from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from functools import lru_cache
import hashlib
from ipaddress import ip_address as parse_ip_address
import os
import json
import re
import secrets
import string
import sys
import time
from typing import Optional
import unicodedata
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, Header, HTTPException, Query, Request, status

from apps.api.backend_api.admin_events import record_admin_event
from apps.api.backend_api.agent_services import ai_health_summary, market_public_metrics, refresh_market_public_metrics
from apps.api.backend_api.badge_engine import BadgeAwardEngine
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.daemon_services import daemon_dashboard_status
from apps.api.backend_api.email_outbox import enqueue_password_reset_email, enqueue_user_email, issue_email_confirmation, public_url
from apps.api.backend_api.market_lifecycle_engine import MarketLifecycleEngine
from apps.api.backend_api.schemas import (
    AdminCategoryPayload,
    AdminBadgeListResponse,
    AdminBadgePayload,
    AdminBadgeResponse,
    AdminDashboardSummaryResponse,
    AdminAiAgentActionListResponse,
    AdminAiAgentActionResponse,
    AdminAiAgentListResponse,
    AdminAiAgentPayload,
    AdminAiAgentResponse,
    AdminUserDetailResponse,
    AdminUserBotPayload,
    AdminUserListResponse,
    AdminUserPasswordResetPayload,
    AdminUserPasswordResetResponse,
    AdminUserRolePayload,
    AdminUserWalletAdjustmentPayload,
    FeedbackRewardPayload,
    AdminMarketActionPayload,
    AdminMarketListResponse,
    AdminMarketParticipantListResponse,
    AdminMarketPayload,
    AdminMarketResolutionAuditResponse,
    AdminMarketResolvePayload,
    AdminEventPayload,
    AdminSubcategoryPayload,
    AdminTaxonomyResponse,
    AuthResponse,
    BadgeListResponse,
    BadgeResponse,
    CommentCreatePayload,
    CommentListResponse,
    CommentModerationPayload,
    CommentResponse,
    EmailConfirmationConfirmPayload,
    EmailConfirmationResponse,
    LedgerResponse,
    LoginPayload,
    MarketListResponse,
    MarketResponse,
    MarketSuggestionPayload,
    NotificationListResponse,
    PasswordResetConfirmPayload,
    PasswordResetConfirmResponse,
    PasswordResetRequestPayload,
    PasswordResetRequestResponse,
    PredictionCreatePayload,
    PredictionCreateResponse,
    PredictionPreviewResponse,
    ProfileUpdatePayload,
    ProductFeedbackPayload,
    QueueItemResponse,
    PublicUserProfileResponse,
    QueueListResponse,
    QueueReviewPayload,
    RankingResponse,
    RegisterPayload,
    ReferralResponse,
    SessionContextResponse,
    SuggestionRewardPayload,
    SystemLogListResponse,
    SystemLogResponse,
    UserProfileResponse,
    WalletRechargeApprovalPayload,
    WalletRechargeRejectPayload,
    WalletRechargeRequestListResponse,
    WalletRechargeRequestResponse,
)
from apps.api.backend_api.security import check_password, hash_token, issue_token, make_password
from config.recaptcha import RecaptchaError, verify_recaptcha_response
from apps.web.django.system_logs.services import exception_payload, log_system_event, new_request_id, request_headers

SESSION_TTL = timedelta(days=14)
PASSWORD_RESET_TTL = timedelta(hours=1)
PASSWORD_RESET_MESSAGE = "Se o email estiver cadastrado, enviaremos instruções para recuperar a senha."
INITIAL_GRANT_GTL = 2000
INITIAL_REPUTATION = 100
BASE_PREDICTION_WEIGHT = 10_000
PROBABILITY_QUANT = Decimal("0.0001")
REPUTATION_K_FACTOR = Decimal("10")
TERMS_VERSION = "2026-05-17"
BADGE_RULE_TYPES = {
    "founding_member",
    "resolved_predictions_count",
    "correct_predictions_count",
    "streak_count",
    "ranking_position",
    "comments_count",
    "approved_suggestions_count",
    "rewarded_feedback_count",
}
BADGE_TYPES = {"global", "category", "performance", "engagement"}
PUBLIC_WEB_BASE_URL = os.environ.get("GOTRENDLABS_PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

app = FastAPI(title="GoTrendLabs Backend API", version="0.1.0")

_RATE_LIMIT_BUCKETS = {}


def _rate_limits_enabled():
    configured = os.environ.get("GOTRENDLABS_RATE_LIMITS_ENABLED")
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes", "on"}
    return "test" not in sys.argv


def _rate_limit_identity(request, *parts):
    ip_address, _ = _client_meta(request)
    clean_parts = [str(part or "").strip().lower()[:256] for part in parts if str(part or "").strip()]
    raw_identity = "|".join([ip_address or "unknown", *clean_parts])
    return hashlib.sha256(raw_identity.encode()).hexdigest()


def _enforce_rate_limit(bucket, identity, *, limit, window_seconds):
    if not _rate_limits_enabled():
        return
    now = time.monotonic()
    key = (bucket, identity)
    hits = [hit for hit in _RATE_LIMIT_BUCKETS.get(key, []) if now - hit < window_seconds]
    if len(hits) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Aguarde alguns minutos antes de tentar novamente.",
        )
    hits.append(now)
    _RATE_LIMIT_BUCKETS[key] = hits


def _clear_rate_limits():
    _RATE_LIMIT_BUCKETS.clear()


@lru_cache(maxsize=512)
def _local_media_url_exists(url):
    if not url or not url.startswith("/media/"):
        return True
    relative_path = url.split("?", 1)[0].removeprefix("/media/").lstrip("/")
    if not relative_path:
        return False
    return os.path.isfile(os.path.join(os.getcwd(), "media", relative_path))


def _public_image_url(url):
    url = (url or "").strip()
    return url if _local_media_url_exists(url) else ""


def _runtime_config_path():
    return os.environ.get("GOTRENDLABS_RUNTIME_CONFIG_PATH") or os.path.join(os.getcwd(), ".runtime", "platform_config.json")


def _maintenance_mode_active():
    try:
        with open(_runtime_config_path(), encoding="utf-8") as config_file:
            data = json.load(config_file)
    except (OSError, json.JSONDecodeError):
        return False
    return bool(data.get("maintenance_enabled"))


@app.middleware("http")
async def system_log_middleware(request: Request, call_next):
    started_at = time.perf_counter()
    request_id = request.headers.get("x-request-id") or new_request_id()
    ip_address, user_agent = _client_meta(request)
    user_id = _request_user_id(request.headers.get("authorization", ""))
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        exception_type, stack_trace = exception_payload(exc)
        log_system_event(
            level="ERROR",
            source="fastapi",
            logger_name="fastapi.request",
            event_type="request_exception",
            message=f"{request.method} {request.url.path} raised {exception_type}",
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            status_code=500,
            duration_ms=duration_ms,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            exception_type=exception_type,
            stack_trace=stack_trace,
            context={"headers": request_headers(request.headers), "query": dict(request.query_params)},
        )
        raise
    duration_ms = int((time.perf_counter() - started_at) * 1000)
    response.headers["X-Request-ID"] = request_id
    status_code = response.status_code
    level = "ERROR" if status_code >= 500 else "WARNING" if status_code >= 400 else "INFO"
    log_system_event(
        level=level,
        source="fastapi",
        logger_name="fastapi.request",
        event_type="request",
        message=f"{request.method} {request.url.path} -> {status_code}",
        request_id=request_id,
        method=request.method,
        path=str(request.url.path),
        status_code=status_code,
        duration_ms=duration_ms,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        context={"headers": request_headers(request.headers), "query": dict(request.query_params)},
    )
    return response


def _row_value(row, key, index):
    if isinstance(row, dict):
        return row[key]
    return row[index]


def _decimal_probability(value):
    return Decimal(str(value or 0)).quantize(PROBABILITY_QUANT)


def _display_probability(value):
    return int(_decimal_probability(value).to_integral_value(rounding=ROUND_DOWN))


def _even_probability_exact(total):
    if total <= 0:
        return Decimal("0.0000")
    return (Decimal("100") / Decimal(total)).quantize(PROBABILITY_QUANT)


def _client_meta(request):
    forwarded_for = request.headers.get("x-forwarded-for", "")
    ip_address = forwarded_for.split(",")[0].strip() or (request.client.host if request.client else None)
    try:
        parse_ip_address(ip_address)
    except ValueError:
        ip_address = None
    user_agent = request.headers.get("user-agent", "")[:255]
    return ip_address, user_agent


def _request_user_id(authorization):
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id
                    FROM gotrendlabs_auth_sessions
                    WHERE token_hash = %s
                      AND revoked_at IS NULL
                      AND expires_at > %s
                    """,
                    (hash_token(token), datetime.now(timezone.utc)),
                )
                row = cursor.fetchone()
                return row["user_id"] if row else None
    except Exception:
        return None


def _ensure_recaptcha(token, request):
    ip_address, _ = _client_meta(request)
    try:
        verify_recaptcha_response(token, remote_ip=ip_address)
    except RecaptchaError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


def _clean_handle(handle):
    return _handle_seed(handle)


def _handle_seed(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    seed = re.sub(r"[^a-z0-9]+", "", ascii_value.lower())
    if len(seed) < 2:
        seed = "user"
    return f"@{seed[:149]}"


def _slug_seed(value, *, max_length=160):
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    seed = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return (seed or "item")[:max_length]


def _unique_slug(cursor, table_name, value, *, max_length=160):
    base = _slug_seed(value, max_length=max_length)
    slug = base
    suffix = 2
    while True:
        cursor.execute(f"SELECT id FROM {table_name} WHERE slug = %s", (slug,))
        if not cursor.fetchone():
            return slug
        suffix_text = f"-{suffix}"
        slug = f"{base[:max_length - len(suffix_text)]}{suffix_text}"
        suffix += 1


def _unique_handle(cursor, value):
    base = _handle_seed(value)
    handle = base
    suffix = 2
    while True:
        cursor.execute("SELECT id FROM gotrendlabs_users WHERE lower(username) = lower(%s)", (handle,))
        if not cursor.fetchone():
            return handle
        suffix_text = str(suffix)
        handle = f"{base[:150 - len(suffix_text)]}{suffix_text}"
        suffix += 1


def _user_response(row, *, display_name=None):
    email_confirmed_at = row.get("email_confirmed_at") if hasattr(row, "get") else None
    return {
        "id": row["id"],
        "handle": _handle_seed(row["username"]),
        "email": row["email"],
        "display_name": display_name or row["first_name"] or _handle_seed(row["username"]),
        "preferred_language": row["preferred_language"],
        "created_at": row["date_joined"].isoformat(),
        "last_login": row["last_login"].isoformat() if row["last_login"] else None,
        "account_status": row["account_status"],
        "is_staff": bool(row["is_staff"]) if "is_staff" in row else False,
        "email_confirmed": bool(email_confirmed_at),
        "email_confirmed_at": email_confirmed_at.isoformat() if email_confirmed_at else None,
    }


def _admin_user_response(row):
    return {
        "id": row["id"],
        "handle": _handle_seed(row["username"]),
        "email": row["email"],
        "display_name": row.get("profile_display_name") or row["first_name"] or _handle_seed(row["username"]),
        "preferred_language": row["preferred_language"],
        "account_status": row["account_status"],
        "is_active": bool(row["is_active"]),
        "is_staff": bool(row["is_staff"]),
        "is_superuser": bool(row["is_superuser"]),
        "is_bot": bool(row.get("is_bot", False)),
        "created_at": row["date_joined"].isoformat(),
        "last_login": row["last_login"].isoformat() if row["last_login"] else None,
        "deactivated_at": row["deactivated_at"].isoformat() if row["deactivated_at"] else None,
        "available_gtl": int(row.get("available_gtl") or 0),
        "locked_gtl": int(row.get("locked_gtl") or 0),
        "reputation_score": int(row.get("reputation_score") or 0),
    }


def _public_user_response(row, *, display_name=None):
    return {
        "id": row["id"],
        "handle": _handle_seed(row["username"]),
        "display_name": display_name or row["first_name"] or _handle_seed(row["username"]),
    }


def _ensure_user_core(cursor, user_id, *, display_name=None):
    now = datetime.now(timezone.utc)
    cursor.execute("SELECT id, username, first_name, is_staff, is_superuser, is_bot FROM gotrendlabs_users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    is_operator = user["is_staff"] or user["is_superuser"] or user["is_bot"]
    profile_name = display_name or user["first_name"] or user["username"]
    cursor.execute(
        """
        INSERT INTO gotrendlabs_user_profiles (user_id, display_name, bio, strong_category, birth_date, sex, is_public, created_at, updated_at)
        VALUES (%s, %s, '', '', NULL, '', true, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id, profile_name, now, now),
    )
    if is_operator:
        _ensure_wallet_balance(cursor, user_id)
        return
    cursor.execute(
        """
        INSERT INTO gotrendlabs_user_reputations
            (user_id, reputation_score, resolved_predictions_count, accuracy_indicator, streak, strong_category, last_updated_at)
        VALUES (%s, %s, 0, '0%%', 0, '', %s)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id, INITIAL_REPUTATION, now),
    )
    cursor.execute("SELECT 1 FROM gotrendlabs_wallet_ledger WHERE user_id = %s AND entry_type = 'grant_initial'", (user_id,))
    has_initial_grant = cursor.fetchone()
    if not has_initial_grant and not is_operator:
        _record_wallet_entry(
            cursor,
            user_id,
            entry_type="grant_initial",
            amount=INITIAL_GRANT_GTL,
            direction="credit",
            description="Saldo inicial do GoTrendLabs",
            reference_type="auth_register",
            reference_id=str(user_id),
        )
    else:
        _ensure_wallet_balance(cursor, user_id)
    cursor.execute(
        """
        INSERT INTO gotrendlabs_user_badges (user_id, code, name, description, status, earned_at)
        VALUES (%s, 'founding_member', 'Membro fundador', 'Entrou no GoTrendLabs durante a fase inicial.', 'earned', %s)
        ON CONFLICT (user_id, code) DO NOTHING
        """,
        (user_id, now),
    )
    cursor.execute(
        """
        INSERT INTO gotrendlabs_user_badges (user_id, code, name, description, status, earned_at)
        VALUES
            (%s, 'calibrated', 'Calibrado', 'Desbloqueado ao demonstrar consistência preditiva.', 'locked', NULL),
            (%s, 'early_signal', 'Early signal', 'Desbloqueado ao acertar antes do consenso virar.', 'locked', NULL),
            (%s, 'top_1_percent', 'Top 1%%', 'Desbloqueado ao alcançar elite do ranking.', 'locked', NULL)
        ON CONFLICT (user_id, code) DO NOTHING
        """,
        (user_id, user_id, user_id),
    )
    BadgeAwardEngine.on_user_registered(cursor, user_id)
    cursor.execute(
        """
        INSERT INTO gotrendlabs_user_activities (user_id, activity_type, title, description, reference_type, reference_id, occurred_at)
        SELECT %s, 'register', 'Conta criada', 'Perfil, carteira e reputação inicial ativados.', 'user', %s, %s
        WHERE NOT EXISTS (
            SELECT 1 FROM gotrendlabs_user_activities
            WHERE user_id = %s AND activity_type = 'register'
        )
        """,
        (user_id, str(user_id), now, user_id),
    )


def _ranking_positions(cursor):
    cursor.execute(
        """
        SELECT u.id
        FROM gotrendlabs_user_reputations r
        JOIN gotrendlabs_users u ON u.id = r.user_id
        WHERE u.is_active = true
          AND u.is_staff = false
          AND u.is_superuser = false
          AND u.is_bot = false
          AND lower(COALESCE(u.username, '')) NOT LIKE '@dev%%'
          AND lower(COALESCE(u.username, '')) NOT LIKE 'dev%%'
        ORDER BY r.reputation_score DESC, u.date_joined ASC, u.id ASC
        """
    )
    return {row["id"]: index + 1 for index, row in enumerate(cursor.fetchall())}


PUBLIC_BADGE_FILTERS = [
    "b.code NOT LIKE 'dev_%%'",
    "lower(COALESCE(b.name, '')) NOT LIKE '%% dev'",
    "lower(COALESCE(b.description, '')) NOT LIKE '%%simulação dev%%'",
    "lower(COALESCE(b.rule_description, '')) NOT LIKE '%%preview local%%'",
]


PUBLIC_USER_FILTERS = [
    "lower(COALESCE(u.username, '')) NOT LIKE '@dev%%'",
    "lower(COALESCE(u.username, '')) NOT LIKE 'dev%%'",
]


def _badge_response(row):
    rule_description = row["rule_description"] or ""
    if "futebool" in rule_description.lower():
        rule_description = rule_description.replace("futebool", "Futebol").replace("Futebool", "Futebol")
    return {
        "code": row["code"],
        "name": row["name"],
        "description": row["description"],
        "rule_description": rule_description,
        "badge_type": row["badge_type"] or "global",
        "image_url": row["image_url"] or "",
        "image_dark_url": row["image_dark_url"] or "",
        "status": "earned" if row["awarded_at"] else "locked",
        "earned_at": row["awarded_at"].isoformat() if row["awarded_at"] else None,
        "reason_snapshot": row["reason_snapshot"] or "",
    }


def _badge_rows(cursor, user_id=None, include_inactive=False):
    where_parts = []
    if not include_inactive:
        where_parts.append("b.is_active = true")
    where_parts.extend(PUBLIC_BADGE_FILTERS)
    active_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    params = []
    if user_id:
        award_select = "a.awarded_at, a.reason_snapshot"
        award_join = "LEFT JOIN gotrendlabs_user_badge_awards a ON a.badge_id = b.id AND a.user_id = %s"
        params.append(user_id)
    else:
        award_select = "NULL AS awarded_at, '' AS reason_snapshot"
        award_join = ""
    cursor.execute(
        f"""
        SELECT b.code, b.name, b.description, b.rule_description, b.badge_type, b.image_url, b.image_dark_url,
               {award_select}
        FROM gotrendlabs_badge_definitions b
        {award_join}
        {active_sql}
        ORDER BY (CASE WHEN a.awarded_at IS NULL THEN 1 ELSE 0 END) ASC, a.awarded_at ASC NULLS LAST, b.name ASC, b.code ASC
        """ if user_id else
        f"""
        SELECT b.code, b.name, b.description, b.rule_description, b.badge_type, b.image_url, b.image_dark_url,
               {award_select}
        FROM gotrendlabs_badge_definitions b
        {active_sql}
        ORDER BY b.name ASC, b.code ASC
        """,
        params,
    )
    return [_badge_response(row) for row in cursor.fetchall()]


def _admin_badge_response(row):
    return {
        "code": row["code"],
        "name": row["name"],
        "description": row["description"],
        "rule_description": row["rule_description"] or "",
        "badge_type": row["badge_type"] or "global",
        "image_url": row["image_url"] or "",
        "image_dark_url": row["image_dark_url"] or "",
        "is_active": bool(row["is_active"]),
        "rule_type": row["rule_type"],
        "threshold_value": float(row["threshold_value"] or 0),
        "category": row["category"] or "",
        "subcategory": row["subcategory"] or "",
        "event": row["event"] or "",
        "rule_active": bool(row["rule_active"]),
        "awards_count": int(row["awards_count"] or 0),
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def _admin_badge_rows(cursor, where_sql="", params=None):
    cursor.execute(
        f"""
        SELECT b.code, b.name, b.description, b.rule_description, b.badge_type, b.image_url, b.image_dark_url,
               b.is_active, b.created_at, b.updated_at,
               r.rule_type, r.threshold_value, r.category, r.subcategory, r.event, r.is_active AS rule_active,
               COUNT(a.id) AS awards_count
        FROM gotrendlabs_badge_definitions b
        JOIN gotrendlabs_badge_rules r ON r.badge_id = b.id
        LEFT JOIN gotrendlabs_user_badge_awards a ON a.badge_id = b.id
        {where_sql}
        GROUP BY b.id, r.id
        ORDER BY b.is_active DESC, b.name ASC, b.code ASC
        """,
        params or [],
    )
    return [_admin_badge_response(row) for row in cursor.fetchall()]


def _validate_badge_payload(payload):
    badge_type = payload.badge_type if payload.badge_type in BADGE_TYPES else "global"
    rule_type = payload.rule_type
    if rule_type not in BADGE_RULE_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Tipo de regra de badge inválido.")
    return badge_type, rule_type


def _validate_badge_taxonomy(cursor, payload):
    category = payload.category.strip()
    subcategory = payload.subcategory.strip()
    event = payload.event.strip()
    if event and not subcategory:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Escolha uma subcategoria antes do evento da badge.")
    if subcategory and not category:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Escolha uma categoria antes da subcategoria da badge.")
    if not category:
        return
    cursor.execute(
        "SELECT id FROM gotrendlabs_market_categories WHERE lower(name) = lower(%s) OR lower(slug) = lower(%s)",
        (category, category),
    )
    category_row = cursor.fetchone()
    if not category_row:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Categoria de badge não encontrada.")
    if not subcategory:
        return
    cursor.execute(
        """
        SELECT id
        FROM gotrendlabs_market_subcategories
        WHERE category_id = %s
          AND (lower(name) = lower(%s) OR lower(slug) = lower(%s))
        """,
        (category_row["id"], subcategory, subcategory),
    )
    subcategory_row = cursor.fetchone()
    if not subcategory_row:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Subcategoria de badge não pertence à categoria.")
    if not event:
        return
    cursor.execute(
        """
        SELECT id
        FROM gotrendlabs_market_events
        WHERE subcategory_id = %s
          AND (lower(name) = lower(%s) OR lower(slug) = lower(%s))
        """,
        (subcategory_row["id"], event, event),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Evento de badge não pertence à subcategoria.")


def _ledger_wallet_totals(cursor, user_id):
    cursor.execute(
        """
        SELECT
            COALESCE(SUM(CASE
                WHEN direction = 'credit' THEN amount
                WHEN direction = 'debit' THEN -amount
                WHEN direction = 'lock' THEN -amount
                WHEN direction = 'release' THEN amount
                ELSE 0
            END), 0) AS available_gtl,
            COALESCE(SUM(CASE WHEN direction = 'lock' THEN amount WHEN direction IN ('release', 'settle') THEN -amount ELSE 0 END), 0) AS locked_gtl,
            COALESCE(SUM(CASE
                WHEN direction = 'credit' AND entry_type IN ('prediction_payout', 'reward_feedback', 'reward_suggestion') THEN amount
                WHEN direction = 'debit' AND entry_type = 'prediction_payout_reversal' THEN -amount
                ELSE 0
            END), 0) AS total_earned_gtl
        FROM gotrendlabs_wallet_ledger
        WHERE user_id = %s
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    return {
        "available_gtl": int(_row_value(row, "available_gtl", 0) or 0),
        "locked_gtl": int(_row_value(row, "locked_gtl", 1) or 0),
        "total_earned_gtl": int(_row_value(row, "total_earned_gtl", 2) or 0),
    }


def _ensure_wallet_balance(cursor, user_id):
    cursor.execute("SELECT user_id FROM gotrendlabs_wallet_balances WHERE user_id = %s", (user_id,))
    if cursor.fetchone():
        return
    totals = _ledger_wallet_totals(cursor, user_id)
    cursor.execute(
        """
        INSERT INTO gotrendlabs_wallet_balances (user_id, available_gtl, locked_gtl, total_earned_gtl, updated_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (
            user_id,
            totals["available_gtl"],
            totals["locked_gtl"],
            totals["total_earned_gtl"],
            datetime.now(timezone.utc),
        ),
    )


def _wallet_summary(cursor, user_id):
    _ensure_wallet_balance(cursor, user_id)
    cursor.execute(
        """
        SELECT available_gtl, locked_gtl, total_earned_gtl
        FROM gotrendlabs_wallet_balances
        WHERE user_id = %s
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    return {
        "available_gtl": int(row["available_gtl"] or 0),
        "locked_gtl": int(row["locked_gtl"] or 0),
        "total_earned_gtl": int(row["total_earned_gtl"] or 0),
    }


def _record_wallet_entry(
    cursor,
    user_id,
    *,
    entry_type,
    amount,
    direction,
    description,
    reference_type="",
    reference_id="",
    created_by_id=None,
):
    _ensure_wallet_balance(cursor, user_id)
    cursor.execute(
        """
        INSERT INTO gotrendlabs_wallet_ledger
            (user_id, entry_type, amount, direction, description, reference_type, reference_id, created_by_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            user_id,
            entry_type,
            amount,
            direction,
            description,
            reference_type,
            reference_id,
            created_by_id,
            datetime.now(timezone.utc),
        ),
    )
    entry_id = _row_value(cursor.fetchone(), "id", 0)
    available_delta = 0
    locked_delta = 0
    earned_delta = 0
    if direction == "credit":
        available_delta = amount
        if entry_type in ("prediction_payout", "reward_feedback", "reward_suggestion"):
            earned_delta = amount
    elif direction == "debit":
        available_delta = -amount
        if entry_type == "prediction_payout_reversal":
            earned_delta = -amount
    elif direction == "lock":
        available_delta = -amount
        locked_delta = amount
    elif direction == "release":
        available_delta = amount
        locked_delta = -amount
    elif direction == "settle":
        locked_delta = -amount

    cursor.execute(
        """
        UPDATE gotrendlabs_wallet_balances
        SET available_gtl = available_gtl + %s,
            locked_gtl = locked_gtl + %s,
            total_earned_gtl = total_earned_gtl + %s,
            updated_at = %s
        WHERE user_id = %s
        """,
        (available_delta, locked_delta, earned_delta, datetime.now(timezone.utc), user_id),
    )
    if direction == "credit":
        _create_notification(
            cursor,
            recipient_id=user_id,
            actor_id=created_by_id,
            event_type="wallet_credit",
            source_key=f"wallet_credit:{entry_id}",
            title="Créditos recebidos",
            body=f"Você recebeu {int(amount)} créditos.",
            metadata={
                "ledger_entry_id": entry_id,
                "entry_type": entry_type,
                "amount": int(amount),
                "direction": direction,
                "reference_type": reference_type,
                "reference_id": reference_id,
            },
            suppress_self=False,
        )
        if entry_type != "grant_initial":
            enqueue_user_email(
                cursor,
                event_type="wallet.credited",
                user_id=user_id,
                template_key="wallet.credited",
                context={
                    "amount": int(amount),
                    "description": description,
                    "entry_type": entry_type,
                    "reference_type": reference_type,
                    "reference_id": reference_id,
                    "wallet_url": public_url("/wallet/"),
                },
                idempotency_key=f"wallet.credited:{user_id}:{entry_id}",
            )
    return entry_id


REFERRAL_CODE_ALPHABET = string.ascii_uppercase + string.digits

LEDGER_ENTRY_TYPE_LABELS = {
    "grant_initial": "Crédito inicial",
    "prediction_stake_lock": "Crédito reservado",
    "prediction_refund": "Crédito devolvido",
    "prediction_payout": "Ganho por acerto",
    "prediction_loss": "Previsão encerrada",
    "prediction_payout_reversal": "Estorno de ganho",
    "prediction_resolution_relock": "Crédito reservado novamente",
    "manual_adjustment": "Ajuste administrativo",
    "reward_feedback": "Recompensa por feedback",
    "reward_suggestion": "Recompensa por sugestão",
    "reward_referral": "Bônus por indicação",
    "educational_recharge": "Recarga educativa",
}

LEDGER_DIRECTION_LABELS = {
    "credit": "Entrada",
    "debit": "Saída",
    "lock": "Reserva",
    "release": "Liberação",
    "settle": "Baixa",
}


def _humanize_code(value):
    return " ".join(part for part in (value or "").replace("_", " ").split()).capitalize()


def _ledger_entry_response(row):
    entry_type = row["entry_type"]
    direction = row["direction"]
    return {
        "entry_id": row["id"],
        "entry_type": entry_type,
        "entry_type_label": LEDGER_ENTRY_TYPE_LABELS.get(entry_type, _humanize_code(entry_type)),
        "amount": row["amount"],
        "direction": direction,
        "direction_label": LEDGER_DIRECTION_LABELS.get(direction, _humanize_code(direction)),
        "description": row["description"],
        "reference_type": row["reference_type"],
        "reference_id": row["reference_id"],
        "created_at": row["created_at"].isoformat(),
        "created_by": row["created_by_id"],
    }


def _normalize_referral_code(value):
    return re.sub(r"[^A-Z0-9]", "", (value or "").strip().upper())[:32]


def _new_referral_code():
    return "".join(secrets.choice(REFERRAL_CODE_ALPHABET) for _ in range(10))


def _site_referral_bonus(cursor):
    cursor.execute("SELECT referral_bonus_gtl FROM gotrendlabs_site_config WHERE singleton_key = 1")
    row = cursor.fetchone()
    return int(row["referral_bonus_gtl"] if row and row["referral_bonus_gtl"] is not None else 200)


def _is_referral_eligible_user(user):
    return bool(
        user
        and user.get("account_status") == "active"
        and not user.get("is_bot")
    )


def _ensure_referral_code(cursor, user):
    if not _is_referral_eligible_user(user):
        return ""
    cursor.execute("SELECT code FROM gotrendlabs_referral_codes WHERE referrer_id = %s", (user["id"],))
    row = cursor.fetchone()
    if row:
        return row["code"]
    for _attempt in range(20):
        code = _new_referral_code()
        cursor.execute(
            """
            INSERT INTO gotrendlabs_referral_codes (referrer_id, code, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING code
            """,
            (user["id"], code, datetime.now(timezone.utc), datetime.now(timezone.utc)),
        )
        row = cursor.fetchone()
        if row:
            return row["code"]
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível criar código de indicação.")


def _referral_response(cursor, user):
    bonus_gtl = _site_referral_bonus(cursor)
    if not _is_referral_eligible_user(user):
        return {"code": "", "bonus_gtl": bonus_gtl, "enabled": False, "reason": "Indicação bonificada disponível apenas para usuários ativos."}
    if bonus_gtl <= 0:
        return {"code": "", "bonus_gtl": 0, "enabled": False, "reason": "Bônus de indicação desativado no Admin Ops."}
    code = _ensure_referral_code(cursor, user)
    return {"code": code, "bonus_gtl": bonus_gtl, "enabled": True, "reason": "Compartilhe seu link para receber GT₵ quando a pessoa criar conta."}


def _award_referral_bonus(cursor, referral_code, invitee_id):
    code = _normalize_referral_code(referral_code)
    if not code:
        return None
    reward_gtl = _site_referral_bonus(cursor)
    if reward_gtl <= 0:
        return None
    cursor.execute(
        """
        SELECT u.id, u.username, u.first_name, u.email, u.preferred_language, u.date_joined, u.last_login,
               u.account_status, u.is_staff, u.is_superuser, u.is_bot, u.email_confirmed_at
        FROM gotrendlabs_referral_codes c
        JOIN gotrendlabs_users u ON u.id = c.referrer_id
        WHERE upper(c.code) = %s
          AND u.is_active = true
          AND u.account_status = 'active'
        """,
        (code,),
    )
    referrer = cursor.fetchone()
    if not _is_referral_eligible_user(referrer) or referrer["id"] == invitee_id:
        return None
    cursor.execute(
        """
        INSERT INTO gotrendlabs_referral_rewards (referrer_id, invitee_id, reward_gtl, ledger_entry_id, rewarded_at, created_at)
        VALUES (%s, %s, %s, NULL, NULL, %s)
        ON CONFLICT (invitee_id) DO NOTHING
        RETURNING id
        """,
        (referrer["id"], invitee_id, reward_gtl, datetime.now(timezone.utc)),
    )
    reward = cursor.fetchone()
    if not reward:
        return None
    entry_id = _record_wallet_entry(
        cursor,
        referrer["id"],
        entry_type="reward_referral",
        amount=reward_gtl,
        direction="credit",
        description="Bônus por indicação validada",
        reference_type="referral_reward",
        reference_id=str(reward["id"]),
    )
    cursor.execute(
        """
        UPDATE gotrendlabs_referral_rewards
        SET ledger_entry_id = %s, rewarded_at = %s
        WHERE id = %s
        """,
        (entry_id, datetime.now(timezone.utc), reward["id"]),
    )
    return entry_id


def _current_user(cursor, authorization):
    token = _bearer_token(authorization)
    cursor.execute(
        """
        SELECT u.id, u.username, u.email, u.first_name, u.preferred_language,
               u.date_joined, u.last_login, u.account_status, u.is_staff, u.is_superuser, u.is_bot,
               u.email_confirmed_at
        FROM gotrendlabs_auth_sessions s
        JOIN gotrendlabs_users u ON u.id = s.user_id
        WHERE s.token_hash = %s
          AND s.revoked_at IS NULL
          AND s.expires_at > %s
          AND u.is_active = true
          AND u.account_status = 'active'
        """,
        (hash_token(token), datetime.now(timezone.utc)),
    )
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida.")
    cursor.execute(
        "UPDATE gotrendlabs_auth_sessions SET last_seen_at = %s WHERE token_hash = %s",
        (datetime.now(timezone.utc), hash_token(token)),
    )
    _ensure_user_core(cursor, user["id"])
    return user


def _require_email_confirmed(user):
    if user.get("is_staff") or user.get("is_superuser") or user.get("is_bot"):
        return
    if not user.get("email_confirmed_at"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirme seu email para liberar esta ação.",
        )


def _current_staff_user(cursor, authorization):
    user = _current_user(cursor, authorization)
    if not user["is_staff"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso administrativo restrito.")
    return user


def _optional_current_user(cursor, authorization):
    if not authorization:
        return None
    try:
        return _current_user(cursor, authorization)
    except HTTPException:
        return None


def _system_log_response(row):
    handle = _handle_seed(row["username"]) if row.get("username") else ""
    user_identifier = handle or row.get("user_email") or (str(row["user_id"]) if row.get("user_id") else "")
    display_name = row.get("user_display_name") or ""
    if display_name and handle:
        user_identifier = f"{handle} · {display_name}"
    return {
        "id": row["id"],
        "created_at": row["created_at"].isoformat(),
        "expires_at": row["expires_at"].isoformat(),
        "level": row["level"],
        "source": row["source"],
        "logger_name": row["logger_name"] or "",
        "event_type": row["event_type"],
        "message": row["message"],
        "request_id": row["request_id"] or "",
        "method": row["method"] or "",
        "path": row["path"] or "",
        "status_code": row["status_code"],
        "duration_ms": row["duration_ms"],
        "user_id": row["user_id"],
        "user_identifier": user_identifier,
        "ip_address": str(row["ip_address"] or ""),
        "user_agent": row["user_agent"] or "",
        "exception_type": row["exception_type"] or "",
        "stack_trace": row["stack_trace"] or "",
        "context": row["context"] or {},
    }


def _profile_response(cursor, user):
    _ensure_user_core(cursor, user["id"])
    positions = _ranking_positions(cursor)
    cursor.execute(
        """
        SELECT p.id AS profile_id, p.display_name, p.bio, p.strong_category AS profile_category,
               p.birth_date, p.sex, p.is_public, p.created_at AS profile_created_at,
               p.updated_at AS profile_updated_at,
               r.reputation_score, r.resolved_predictions_count, r.accuracy_indicator,
               r.streak, r.strong_category AS reputation_category, r.last_updated_at
        FROM gotrendlabs_user_profiles p
        LEFT JOIN gotrendlabs_user_reputations r ON r.user_id = p.user_id
        WHERE p.user_id = %s
        """,
        (user["id"],),
    )
    profile = cursor.fetchone()
    return {
        "user": _user_response(user, display_name=profile["display_name"]),
        "profile_id": profile["profile_id"],
        "bio": profile["bio"],
        "strong_category": profile["profile_category"] or profile["reputation_category"] or "",
        "birth_date": profile["birth_date"].isoformat() if profile["birth_date"] else None,
        "sex": profile["sex"] or "",
        "profile_created_at": profile["profile_created_at"].isoformat(),
        "profile_updated_at": profile["profile_updated_at"].isoformat(),
        "is_public": profile["is_public"],
        "reputation": {
            "reputation_score": int(profile["reputation_score"] or 0),
            "ranking_position": positions.get(user["id"], 0),
            "resolved_predictions_count": int(profile["resolved_predictions_count"] or 0),
            "accuracy_indicator": profile["accuracy_indicator"] or "0%",
            "streak": int(profile["streak"] or 0),
            "strong_category": profile["reputation_category"] or "",
            "last_updated_at": profile["last_updated_at"].isoformat() if profile["last_updated_at"] else profile["profile_updated_at"].isoformat(),
        },
    }


def _public_profile_response(cursor, user):
    profile = _profile_response(cursor, user)
    profile["user"] = _public_user_response(user, display_name=profile["user"]["display_name"])
    profile.pop("birth_date", None)
    profile.pop("sex", None)
    profile.pop("profile_id", None)
    profile.pop("profile_created_at", None)
    profile.pop("profile_updated_at", None)
    return profile


def _resolution_timezone(row):
    if "resolution_timezone" in row and row["resolution_timezone"]:
        return row["resolution_timezone"]
    return row["close_timezone"] or "UTC"


def _datetime_label(value, timezone_name):
    if not value:
        return ""
    try:
        target_timezone = ZoneInfo(timezone_name or "UTC")
    except ZoneInfoNotFoundError:
        target_timezone = timezone.utc
        timezone_name = "UTC"
    localized = value.astimezone(target_timezone) if value.tzinfo else value.replace(tzinfo=timezone.utc).astimezone(target_timezone)
    return f"{localized.strftime('%d/%m/%Y %H:%M')} {timezone_name or 'UTC'}"


def _timezone_short_label(timezone_name):
    return "BRT" if timezone_name == "America/Sao_Paulo" else (timezone_name or "UTC")


def _public_close_label(close_at, timezone_name, close_label, status_value):
    label = (close_label or "").strip()
    if label and "T" not in label:
        return label
    if close_at:
        try:
            target_timezone = ZoneInfo(timezone_name or "UTC")
        except ZoneInfoNotFoundError:
            target_timezone = timezone.utc
            timezone_name = "UTC"
        localized = close_at.astimezone(target_timezone) if close_at.tzinfo else close_at.replace(tzinfo=timezone.utc).astimezone(target_timezone)
        return f"Fecha em {localized.strftime('%d/%m/%Y %H:%M')} {_timezone_short_label(timezone_name)}"
    return _market_status_label(status_value)


def _market_rows(cursor, where_sql="", params=None, order_sql="m.display_order ASC, m.id ASC"):
    cursor.execute(
        f"""
        SELECT m.id, m.slug, m.title, m.summary, m.kind, m.status, m.status_label,
               m.primary_outcome, m.primary_probability_exact, m.secondary_probability_exact,
               m.volume_gtl, m.participants, m.source, m.closes_in, m.close_label,
               m.thumb, m.thumb_color, m.image_url, m.resolution_criteria,
               m.resolution_type, m.resolved_at, m.resolution_timezone, m.winning_option_id, m.resolution_note,
               m.close_at, m.close_timezone, m.auto_close_enabled, m.is_featured, m.view_count, m.share_count, m.created_at,
               COALESCE(COUNT(DISTINCT ml.id), 0) AS market_like_count,
               COALESCE(COUNT(DISTINCT visible_comments.id), 0) AS comment_count,
               c.name AS category, c.notice AS category_notice,
               sc.name AS subcategory, sc.notice AS subcategory_notice,
               ev.name AS event, ev.notice AS event_notice
        FROM gotrendlabs_markets m
        JOIN gotrendlabs_market_categories c ON c.id = m.category_id
        JOIN gotrendlabs_market_subcategories sc ON sc.id = m.subcategory_id
        LEFT JOIN gotrendlabs_market_events ev ON ev.id = m.event_id
        LEFT JOIN gotrendlabs_market_likes ml ON ml.market_id = m.id
        LEFT JOIN gotrendlabs_market_comments visible_comments ON visible_comments.market_id = m.id AND visible_comments.status = 'visible'
        {where_sql}
        GROUP BY m.id, c.name, c.notice, sc.name, sc.notice, ev.name, ev.notice
        ORDER BY {order_sql}
        """,
        params or [],
    )
    return cursor.fetchall()


def _market_status_label(status_value):
    return {
        "draft": "Rascunho",
        "scheduled": "Agendado",
        "open": "Aberto",
        "locked": "Fechado",
        "resolved": "Resolvido",
        "canceled": "Cancelado",
    }.get(status_value, status_value)


def _short_close_label(close_at):
    if not close_at:
        return ""
    now = datetime.now(timezone.utc)
    target = close_at if close_at.tzinfo else close_at.replace(tzinfo=timezone.utc)
    delta = target - now
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return "fim"
    days = seconds // 86400
    if days >= 1:
        return f"{days}d"
    hours = max(1, seconds // 3600)
    return f"{hours}h"


def _sparkline_paths(points, *, width=220, height=44, pad=4):
    if not points:
        points = [50]
    if len(points) == 1:
        points = [points[0], points[0]]
    step = (width - (pad * 2)) / max(len(points) - 1, 1)
    coords = []
    for index, value in enumerate(points):
        probability = max(Decimal("0"), min(Decimal("100"), _decimal_probability(value)))
        x = Decimal(str(pad)) + (Decimal(str(index)) * Decimal(str(step)))
        y = Decimal(str(pad)) + ((Decimal("100") - probability) / Decimal("100")) * Decimal(str(height - (pad * 2)))
        coords.append((round(x, 2), round(y, 2)))
    path = " ".join(f"{'M' if index == 0 else 'L'} {x:g} {y:g}" for index, (x, y) in enumerate(coords))
    area = f"M {coords[0][0]:g} {height - pad:g} " + " ".join(f"L {x:g} {y:g}" for x, y in coords) + f" L {coords[-1][0]:g} {height - pad:g} Z"
    return {"sparkline_path": path, "sparkline_area_path": area}


def _market_sparklines(cursor, market_id, options):
    option_ids = [option["id"] for option in options]
    if not option_ids:
        fallback = _sparkline_paths([50])
        return {**fallback, "series": []}
    weights = {option_id: BASE_PREDICTION_WEIGHT for option_id in option_ids}
    points_by_option = {option_id: [] for option_id in option_ids}

    def append_points():
        total = sum(weights.values())
        for option_id in option_ids:
            points_by_option[option_id].append((Decimal(weights[option_id]) * Decimal("100") / Decimal(total)).quantize(PROBABILITY_QUANT))

    append_points()
    cursor.execute(
        """
        SELECT market_option_id, weight_at_entry
        FROM gotrendlabs_predictions
        WHERE market_id = %s AND status IN ('open', 'resolved')
        ORDER BY created_at ASC, id ASC
        """,
        (market_id,),
    )
    for prediction in cursor.fetchall():
        option_id = prediction["market_option_id"]
        if option_id not in weights:
            continue
        weights[option_id] += int(prediction["weight_at_entry"] or 0)
        append_points()
    primary = _sparkline_paths(points_by_option[option_ids[0]])
    series = []
    for option in options:
        series.append(
            {
                "id": option["id"],
                "label": option["label"],
                "path": _sparkline_paths(points_by_option[option["id"]])["sparkline_path"],
            }
        )
    return {**primary, "series": series}


def _comment_status_label(value):
    return {"visible": "Visível", "hidden": "Oculto"}.get(value, value)


def _comment_response(row):
    return {
        "id": row["id"],
        "market_slug": row["market_slug"],
        "author_id": row["author_id"],
        "author_handle": _handle_seed(row["author_handle"]),
        "author_display_name": row["author_display_name"] or _handle_seed(row["author_handle"]),
        "author_is_bot": bool(row.get("author_is_bot", False)),
        "author_badge_label": "IA oficial" if row.get("author_is_bot", False) else "",
        "body": row["body"],
        "status": row["status"],
        "like_count": int(row["like_count"] or 0),
        "dislike_count": int(row["dislike_count"] or 0),
        "viewer_reaction": row.get("viewer_reaction"),
        "moderation_note": row["moderation_note"] or "",
        "moderated_by": row["moderated_by_id"],
        "moderated_at": row["moderated_at"].isoformat() if row["moderated_at"] else None,
        "created_at": row["created_at"].isoformat(),
        "created_at_label": _age_label(row["created_at"]),
    }


def _market_comments(cursor, market_id=None, *, slug=None, visible_only=True, viewer_id=None):
    where = []
    params = []
    if market_id is not None:
        where.append("mc.market_id = %s")
        params.append(market_id)
    if slug is not None:
        where.append("m.slug = %s")
        params.append(slug)
    if visible_only:
        where.append("mc.status = 'visible'")
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    viewer_join = ""
    viewer_select = "NULL AS viewer_reaction"
    viewer_group = ""
    if viewer_id:
        viewer_join = "LEFT JOIN gotrendlabs_comment_reactions vr ON vr.comment_id = mc.id AND vr.user_id = %s"
        viewer_select = "vr.reaction AS viewer_reaction"
        viewer_group = ", vr.reaction"
        params = [viewer_id, *params]
    cursor.execute(
        f"""
        SELECT mc.id, mc.body, mc.status, mc.moderation_note, mc.moderated_by_id,
               mc.moderated_at, mc.created_at, mc.updated_at,
               m.slug AS market_slug,
               u.id AS author_id, u.username AS author_handle, u.first_name AS author_display_name,
               u.is_bot AS author_is_bot,
               COALESCE(SUM(CASE WHEN cr.reaction = 'like' THEN 1 ELSE 0 END), 0) AS like_count,
               COALESCE(SUM(CASE WHEN cr.reaction = 'dislike' THEN 1 ELSE 0 END), 0) AS dislike_count,
               {viewer_select}
        FROM gotrendlabs_market_comments mc
        JOIN gotrendlabs_markets m ON m.id = mc.market_id
        JOIN gotrendlabs_users u ON u.id = mc.author_id
        LEFT JOIN gotrendlabs_comment_reactions cr ON cr.comment_id = mc.id
        {viewer_join}
        {where_sql}
        GROUP BY mc.id, mc.body, mc.status, mc.moderation_note, mc.moderated_by_id,
                 mc.moderated_at, mc.created_at, mc.updated_at,
                 m.slug, u.id, u.username, u.first_name, u.is_bot{viewer_group}
        ORDER BY mc.created_at DESC, mc.id DESC
        """,
        params,
    )
    return [_comment_response(row) for row in cursor.fetchall()]


def _market_response(cursor, row, *, viewer_id=None, include_comments=True, filter_public_image=True):
    cursor.execute(
        """
        SELECT id, label, probability_exact, hint
        FROM gotrendlabs_market_options
        WHERE market_id = %s
        ORDER BY display_order ASC, id ASC
        """,
        (row["id"],),
    )
    options = [
        {
            "id": option["id"],
            "label": option["label"],
            "probability": _display_probability(option["probability_exact"]),
            "probability_exact": float(_decimal_probability(option["probability_exact"])),
            "hint": option["hint"],
        }
        for option in cursor.fetchall()
    ]
    sparkline = _market_sparklines(cursor, row["id"], options)
    options = [
        {**option, "sparkline_path": next((item["path"] for item in sparkline["series"] if item["id"] == option["id"]), "")}
        for option in options
    ]
    viewer_has_prediction = False
    viewer_has_favorite = False
    viewer_has_like = False
    if viewer_id:
        cursor.execute(
            """
            SELECT 1
            FROM gotrendlabs_predictions
            WHERE market_id = %s AND user_id = %s
            LIMIT 1
            """,
            (row["id"], viewer_id),
        )
        viewer_has_prediction = bool(cursor.fetchone())
        cursor.execute(
            """
            SELECT 1
            FROM gotrendlabs_market_favorites
            WHERE market_id = %s AND user_id = %s
            LIMIT 1
            """,
            (row["id"], viewer_id),
        )
        viewer_has_favorite = bool(cursor.fetchone())
        cursor.execute(
            """
            SELECT 1
            FROM gotrendlabs_market_likes
            WHERE market_id = %s AND user_id = %s
            LIMIT 1
            """,
            (row["id"], viewer_id),
        )
        viewer_has_like = bool(cursor.fetchone())
    public_metrics = market_public_metrics(cursor, row["id"])
    return {
        "slug": row["slug"],
        "title": row["title"],
        "category": row["category"],
        "category_notice": row["category_notice"] or "",
        "subcategory": row["subcategory"],
        "subcategory_notice": row["subcategory_notice"] or "",
        "event": row["event"] or "Geral",
        "event_notice": row["event_notice"] or "",
        "kind": row["kind"],
        "status": row["status"],
        "status_label": _market_status_label(row["status"]),
        "primary_outcome": row["primary_outcome"],
        "primary_probability": _display_probability(row["primary_probability_exact"]),
        "primary_probability_exact": float(_decimal_probability(row["primary_probability_exact"])),
        "secondary_probability": _display_probability(row["secondary_probability_exact"]),
        "secondary_probability_exact": float(_decimal_probability(row["secondary_probability_exact"])),
        "volume_gtl": _currency_label(public_metrics["volume_gtl"]),
        "participants": public_metrics["participants"],
        "human_participants": public_metrics["human_participants"],
        "bot_participants": public_metrics["bot_participants"],
        "human_volume_gtl": public_metrics["human_volume_gtl"],
        "bot_volume_gtl": public_metrics["bot_volume_gtl"],
        "total_volume_gtl": public_metrics["total_volume_gtl"],
        "source": row["source"],
        "closes_in": _short_close_label(row["close_at"]) or row["closes_in"],
        "close_label": _public_close_label(row["close_at"], row["close_timezone"], row["close_label"], row["status"]),
        "thumb": row["thumb"],
        "thumb_color": row["thumb_color"],
        "image_url": _public_image_url(row["image_url"]) if filter_public_image else (row["image_url"] or ""),
        "summary": row["summary"],
        "resolution_criteria": row["resolution_criteria"],
        "close_at": row["close_at"].isoformat() if row["close_at"] else None,
        "close_timezone": row["close_timezone"],
        "auto_close_enabled": row["auto_close_enabled"],
        "is_featured": bool(row["is_featured"]) if "is_featured" in row else False,
        "resolved_at": row["resolved_at"].isoformat() if "resolved_at" in row and row["resolved_at"] else None,
        "resolved_at_label": _datetime_label(row["resolved_at"], _resolution_timezone(row)) if "resolved_at" in row and row["resolved_at"] else "",
        "resolution_timezone": _resolution_timezone(row),
        "winning_option_id": row["winning_option_id"] if "winning_option_id" in row else None,
        "resolution_note": (row["resolution_note"] or "") if "resolution_note" in row else "",
        "resolution_type": (row["resolution_type"] or "") if "resolution_type" in row else "",
        "market_like_count": int(row["market_like_count"] or 0) if "market_like_count" in row else 0,
        "comment_count": int(row["comment_count"] or 0) if "comment_count" in row else 0,
        "view_count": int(row["view_count"] or 0) if "view_count" in row else 0,
        "share_count": int(row["share_count"] or 0) if "share_count" in row else 0,
        "viewer_has_prediction": viewer_has_prediction,
        "viewer_has_favorite": viewer_has_favorite,
        "viewer_has_like": viewer_has_like,
        "created_at": row["created_at"].isoformat() if "created_at" in row and row["created_at"] else "",
        "sparkline_path": sparkline["sparkline_path"],
        "sparkline_area_path": sparkline["sparkline_area_path"],
        "sparkline_series": sparkline["series"],
        "options": options,
        "comments": _market_comments(cursor, row["id"], viewer_id=viewer_id) if include_comments else [],
    }


def _participants_label(count):
    if count == 1:
        return "1 participante"
    return f"{count} participantes"


def _currency_label(value):
    return str(value or "0 GT₵").replace(" GTL", " GT₵")


def _format_gtl_amount(value):
    return f"{int(value or 0):,}".replace(",", ".")


def _volume_label(amount):
    return _currency_label(f"{amount} GT₵")


@app.get("/stats")
def get_public_stats():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM gotrendlabs_markets WHERE status = 'open') AS open_markets,
                    (
                        SELECT COUNT(*)
                        FROM gotrendlabs_predictions p
                        JOIN gotrendlabs_users u ON u.id = p.user_id
                        WHERE u.is_bot = false
                    ) AS total_predictions,
                    (
                        SELECT COALESCE(SUM(l.amount), 0)
                        FROM gotrendlabs_wallet_ledger l
                        INNER JOIN gotrendlabs_users u ON u.id = l.user_id
                        WHERE l.direction = 'credit'
                          AND u.is_staff = false
                          AND u.is_superuser = false
                    ) AS distributed_gtl,
                    (
                        SELECT COALESCE(SUM(p.stake_amount), 0)
                        FROM gotrendlabs_predictions p
                        JOIN gotrendlabs_users u ON u.id = p.user_id
                        WHERE u.is_bot = false
                    ) AS moved_gtl
                """
            )
            row = cursor.fetchone()
    return {
        "open_markets": int(row["open_markets"] or 0),
        "total_predictions": int(row["total_predictions"] or 0),
        "distributed_gtl": _format_gtl_amount(row["distributed_gtl"]),
        "moved_gtl": _format_gtl_amount(row["moved_gtl"]),
        "resolution_sla": "pendente",
        "real_money": "R$0",
    }


def _market_probability_snapshot(cursor, market_id):
    cursor.execute(
        """
        SELECT o.id, o.label, o.hint, o.display_order,
               %s + COALESCE(SUM(p.weight_at_entry), 0) AS total_weight
        FROM gotrendlabs_market_options o
        LEFT JOIN gotrendlabs_predictions p
          ON p.market_option_id = o.id
         AND p.status = 'open'
        WHERE o.market_id = %s
        GROUP BY o.id, o.label, o.hint, o.display_order
        ORDER BY o.display_order ASC, o.id ASC
        """,
        (BASE_PREDICTION_WEIGHT, market_id),
    )
    rows = cursor.fetchall()
    total_weight = sum(int(row["total_weight"] or 0) for row in rows)
    if not rows or total_weight <= 0:
        return []

    probability_by_id = {}
    for row in rows:
        value = (Decimal(int(row["total_weight"] or 0)) * Decimal("100") / Decimal(total_weight)).quantize(PROBABILITY_QUANT)
        probability_by_id[row["id"]] = value

    snapshot = []
    for row in rows:
        probability_exact = probability_by_id[row["id"]]
        cursor.execute(
            "UPDATE gotrendlabs_market_options SET probability_exact = %s, updated_at = %s WHERE id = %s",
            (probability_exact, datetime.now(timezone.utc), row["id"]),
        )
        probability = _display_probability(probability_exact)
        snapshot.append({"id": row["id"], "label": row["label"], "probability": probability, "probability_exact": float(probability_exact), "hint": row["hint"]})

    primary_probability_exact = _decimal_probability(snapshot[0]["probability_exact"]) if snapshot else Decimal("0")
    secondary_probability_exact = _decimal_probability(snapshot[1]["probability_exact"]) if len(snapshot) > 1 else Decimal("0")
    public_metrics = market_public_metrics(cursor, market_id)
    cursor.execute(
        """
        UPDATE gotrendlabs_markets
        SET primary_probability_exact = %s,
            secondary_probability_exact = %s,
            volume_gtl = %s,
            participants = %s,
            updated_at = %s
        WHERE id = %s
        """,
        (
            primary_probability_exact,
            secondary_probability_exact,
            public_metrics["volume_gtl"],
            public_metrics["participants"],
            datetime.now(timezone.utc),
            market_id,
        ),
    )
    return snapshot


def _prediction_preview(cursor, slug, payload):
    cursor.execute(
        """
        SELECT id, status
        FROM gotrendlabs_markets
        WHERE slug = %s
        """,
        (slug,),
    )
    market = cursor.fetchone()
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mercado não encontrado.")
    if market["status"] != "open":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Mercado fechado para novas previsões.")

    cursor.execute(
        """
        SELECT id, probability_exact
        FROM gotrendlabs_market_options
        WHERE id = %s AND market_id = %s
        """,
        (payload.option_id, market["id"]),
    )
    option = cursor.fetchone()
    if not option:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Opção inválida para este mercado.")

    probability_exact = max(_decimal_probability(option["probability_exact"]), PROBABILITY_QUANT)
    estimated_return = int((Decimal(payload.stake_amount) * Decimal("100") / probability_exact).to_integral_value())
    return {
        "market_id": market["id"],
        "option_id": option["id"],
        "stake_amount": payload.stake_amount,
        "probability_exact": float(probability_exact),
        "estimated_return": estimated_return,
    }


def _sync_featured_market(cursor, market_id, is_featured):
    if not is_featured:
        return
    if market_id is None:
        cursor.execute(
            """
            SELECT id
            FROM gotrendlabs_markets
            WHERE is_featured = true
            ORDER BY updated_at DESC, display_order ASC, id ASC
            """
        )
    else:
        cursor.execute(
            """
            SELECT id
            FROM gotrendlabs_markets
            WHERE is_featured = true
              AND id <> %s
            ORDER BY updated_at DESC, display_order ASC, id ASC
            """,
            (market_id,),
        )
    keep_ids = [row["id"] for row in cursor.fetchall()[:1]]
    if keep_ids:
        if market_id is None:
            cursor.execute(
                """
                UPDATE gotrendlabs_markets
                SET is_featured = false,
                    updated_at = %s
                WHERE is_featured = true
                  AND id <> ALL(%s)
                """,
                (datetime.now(timezone.utc), keep_ids),
            )
        else:
            cursor.execute(
                """
                UPDATE gotrendlabs_markets
                SET is_featured = false,
                    updated_at = %s
                WHERE is_featured = true
                  AND id <> %s
                  AND id <> ALL(%s)
                """,
                (datetime.now(timezone.utc), market_id, keep_ids),
            )
        return


def _ensure_featured_allowed(market_status, is_featured):
    if is_featured and market_status == "canceled":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Mercados cancelados não podem ficar em destaque.")


def _record_admin_event(cursor, actor_id, action, entity_type, entity_identifier, note=""):
    record_admin_event(cursor, actor_id, action, entity_type, entity_identifier, note)


def _market_lifecycle_engine(cursor, staff_id):
    return MarketLifecycleEngine(
        cursor,
        staff_id=staff_id,
        record_wallet_entry=_record_wallet_entry,
        record_admin_event=_record_admin_event,
        ensure_user_core=_ensure_user_core,
        validate_publishable=_validate_publishable,
    )


def _admin_user_row(cursor, user_id):
    cursor.execute(
        """
        SELECT u.id, u.username, u.email, u.first_name, u.preferred_language,
               u.date_joined, u.last_login, u.account_status, u.is_active,
               u.is_staff, u.is_superuser, u.is_bot, u.deactivated_at,
               p.display_name AS profile_display_name,
               COALESCE(w.available_gtl, 0) AS available_gtl,
               COALESCE(w.locked_gtl, 0) AS locked_gtl,
               COALESCE(r.reputation_score, 0) AS reputation_score
        FROM gotrendlabs_users u
        LEFT JOIN gotrendlabs_user_profiles p ON p.user_id = u.id
        LEFT JOIN gotrendlabs_wallet_balances w ON w.user_id = u.id
        LEFT JOIN gotrendlabs_user_reputations r ON r.user_id = u.id
        WHERE u.id = %s
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    _ensure_user_core(cursor, user_id)
    cursor.execute(
        """
        SELECT u.id, u.username, u.email, u.first_name, u.preferred_language,
               u.date_joined, u.last_login, u.account_status, u.is_active,
               u.is_staff, u.is_superuser, u.is_bot, u.deactivated_at,
               p.display_name AS profile_display_name,
               COALESCE(w.available_gtl, 0) AS available_gtl,
               COALESCE(w.locked_gtl, 0) AS locked_gtl,
               COALESCE(r.reputation_score, 0) AS reputation_score
        FROM gotrendlabs_users u
        LEFT JOIN gotrendlabs_user_profiles p ON p.user_id = u.id
        LEFT JOIN gotrendlabs_wallet_balances w ON w.user_id = u.id
        LEFT JOIN gotrendlabs_user_reputations r ON r.user_id = u.id
        WHERE u.id = %s
        """,
        (user_id,),
    )
    return cursor.fetchone()


def _require_admin_target(staff, target, *, allow_superuser=False, allow_self=False):
    if int(staff["id"]) == int(target["id"]) and not allow_self:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Operador não pode executar esta ação sobre a própria conta.")
    if target["is_superuser"] and not allow_superuser:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Ação não permitida para superusuário.")


def _require_superuser(staff):
    if not staff["is_superuser"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas superusuários podem alterar privilégios administrativos.")


def _issue_password_reset(cursor, user, *, ip_address=None, user_agent=""):
    token = issue_token()
    now = datetime.now(timezone.utc)
    cursor.execute(
        """
        INSERT INTO gotrendlabs_password_reset_tokens
            (user_id, token_hash, created_at, expires_at, used_at, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, NULL, %s, %s)
        """,
        (user["id"], hash_token(token), now, now + PASSWORD_RESET_TTL, ip_address, user_agent),
    )
    reset_url = f"{PUBLIC_WEB_BASE_URL}/password-reset/confirm/{token}/"
    enqueue_password_reset_email(cursor, user, reset_url)
    return reset_url


def _ledger_entries(cursor, user_id, limit=10):
    cursor.execute(
        """
        SELECT id, entry_type, amount, direction, description, reference_type, reference_id, created_by_id, created_at
        FROM gotrendlabs_wallet_ledger
        WHERE user_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT %s
        """,
        (user_id, limit),
    )
    return [_ledger_entry_response(row) for row in cursor.fetchall()]


def _admin_user_detail(cursor, user_id):
    user = _admin_user_row(cursor, user_id)
    wallet = _wallet_summary(cursor, user_id)
    profile = _profile_response(cursor, user)

    cursor.execute(
        """
        SELECT p.id, p.status, p.stake_amount, p.won, p.created_at,
               m.slug AS market_slug, m.title AS market_title, mo.label AS option_label
        FROM gotrendlabs_predictions p
        JOIN gotrendlabs_markets m ON m.id = p.market_id
        JOIN gotrendlabs_market_options mo ON mo.id = p.market_option_id
        WHERE p.user_id = %s
        ORDER BY p.created_at DESC, p.id DESC
        LIMIT 10
        """,
        (user_id,),
    )
    predictions = [
        {
            "id": row["id"],
            "status": row["status"],
            "stake_amount": row["stake_amount"],
            "won": row["won"],
            "market_slug": row["market_slug"],
            "market_title": row["market_title"],
            "option_label": row["option_label"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in cursor.fetchall()
    ]
    cursor.execute("SELECT status, COUNT(*) AS total FROM gotrendlabs_predictions WHERE user_id = %s GROUP BY status", (user_id,))
    prediction_counts = {row["status"]: int(row["total"] or 0) for row in cursor.fetchall()}

    cursor.execute(
        """
        SELECT mc.id, mc.status, mc.body, mc.created_at, m.slug AS market_slug, m.title AS market_title
        FROM gotrendlabs_market_comments mc
        JOIN gotrendlabs_markets m ON m.id = mc.market_id
        WHERE mc.author_id = %s
        ORDER BY mc.created_at DESC, mc.id DESC
        LIMIT 10
        """,
        (user_id,),
    )
    comments = [
        {
            "id": row["id"],
            "status": row["status"],
            "body": row["body"],
            "market_slug": row["market_slug"],
            "market_title": row["market_title"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in cursor.fetchall()
    ]
    cursor.execute("SELECT status, COUNT(*) AS total FROM gotrendlabs_market_comments WHERE author_id = %s GROUP BY status", (user_id,))
    comment_counts = {row["status"]: int(row["total"] or 0) for row in cursor.fetchall()}

    cursor.execute(
        """
        SELECT b.code, b.name, b.description, b.badge_type, b.image_url, b.image_dark_url,
               a.awarded_at, a.reason_snapshot
        FROM gotrendlabs_user_badge_awards a
        JOIN gotrendlabs_badge_definitions b ON b.id = a.badge_id
        WHERE a.user_id = %s
        ORDER BY a.awarded_at DESC, b.name ASC
        LIMIT 20
        """,
        (user_id,),
    )
    badges = [
        {
            "code": row["code"],
            "name": row["name"],
            "description": row["description"],
            "badge_type": row["badge_type"],
            "image_url": row["image_url"] or "",
            "image_dark_url": row["image_dark_url"] or "",
            "awarded_at": row["awarded_at"].isoformat() if row["awarded_at"] else None,
            "reason_snapshot": row["reason_snapshot"] or "",
        }
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT id, question, status, reward_gtl, created_at
        FROM gotrendlabs_market_suggestions
        WHERE author_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 10
        """,
        (user_id,),
    )
    suggestions = [
        {
            "id": row["id"],
            "title": row["question"],
            "status": row["status"],
            "reward_gtl": row["reward_gtl"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT id, feedback_type, severity, status, reward_gtl, created_at
        FROM gotrendlabs_product_feedback
        WHERE author_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 10
        """,
        (user_id,),
    )
    feedback = [
        {
            "id": row["id"],
            "title": row["feedback_type"],
            "severity": row["severity"],
            "status": row["status"],
            "reward_gtl": row["reward_gtl"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT id, created_at, last_seen_at, expires_at, revoked_at, ip_address, user_agent
        FROM gotrendlabs_auth_sessions
        WHERE user_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 10
        """,
        (user_id,),
    )
    sessions = [
        {
            "id": row["id"],
            "created_at": row["created_at"].isoformat(),
            "last_seen_at": row["last_seen_at"].isoformat() if row["last_seen_at"] else None,
            "expires_at": row["expires_at"].isoformat(),
            "revoked_at": row["revoked_at"].isoformat() if row["revoked_at"] else None,
            "ip_address": str(row["ip_address"] or ""),
            "user_agent": row["user_agent"] or "",
        }
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT event_type, email, provider, ip_address, user_agent, created_at
        FROM gotrendlabs_auth_events
        WHERE user_id = %s OR lower(email) = lower(%s)
        ORDER BY created_at DESC, id DESC
        LIMIT 10
        """,
        (user_id, user["email"]),
    )
    auth_events = [
        {
            "event_type": row["event_type"],
            "email": row["email"],
            "provider": row["provider"],
            "ip_address": str(row["ip_address"] or ""),
            "user_agent": row["user_agent"] or "",
            "created_at": row["created_at"].isoformat(),
        }
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT action, entity_type, entity_identifier, note, created_at, actor_id
        FROM gotrendlabs_admin_events
        WHERE (entity_type = 'user' AND entity_identifier = %s) OR actor_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 10
        """,
        (str(user_id), user_id),
    )
    admin_events = [
        {
            "action": row["action"],
            "entity_type": row["entity_type"],
            "entity_identifier": row["entity_identifier"],
            "note": row["note"],
            "actor_id": row["actor_id"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in cursor.fetchall()
    ]
    return {
        "user": _admin_user_response(user),
        "profile": {
            "bio": profile["bio"],
            "strong_category": profile["strong_category"],
            "birth_date": profile["birth_date"],
            "sex": profile["sex"],
            "is_public": profile["is_public"],
            "profile_created_at": profile["profile_created_at"],
            "profile_updated_at": profile["profile_updated_at"],
        },
        "wallet": wallet,
        "ledger": _ledger_entries(cursor, user_id),
        "reputation": profile["reputation"],
        "prediction_counts": prediction_counts,
        "predictions": predictions,
        "comment_counts": comment_counts,
        "comments": comments,
        "badges": badges,
        "suggestions": suggestions,
        "feedback": feedback,
        "sessions": sessions,
        "auth_events": auth_events,
        "admin_events": admin_events,
    }


def _age_label(created_at):
    created = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - created
    hours = int(delta.total_seconds() // 3600)
    if hours < 1:
        return "agora"
    if hours < 24:
        return f"{hours}h"
    return f"{hours // 24}d"


def _actor_display_name(row):
    if not row:
        return ""
    return row.get("actor_display_name") or _handle_seed(row.get("actor_handle") or "")


def _notification_response(row):
    metadata = row["metadata"] or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}
    return {
        "id": row["id"],
        "event_type": row["event_type"],
        "title": row["title"],
        "body": row["body"] or "",
        "is_read": bool(row["is_read"]),
        "actor_handle": _handle_seed(row["actor_handle"]) if row.get("actor_handle") else "",
        "actor_display_name": _actor_display_name(row),
        "market_slug": row["market_slug"] or "",
        "market_title": row["market_title"] or "",
        "comment_id": row["comment_id"],
        "metadata": metadata,
        "created_at": row["created_at"].isoformat(),
        "created_at_label": _age_label(row["created_at"]),
    }


def _notification_rows(cursor, recipient_id, *, limit=10):
    cursor.execute(
        """
        SELECT n.id, n.event_type, n.title, n.body, n.is_read, n.metadata, n.created_at,
               n.comment_id,
               actor.username AS actor_handle, actor.first_name AS actor_display_name,
               m.slug AS market_slug, m.title AS market_title
        FROM gotrendlabs_user_notifications n
        LEFT JOIN gotrendlabs_users actor ON actor.id = n.actor_id
        LEFT JOIN gotrendlabs_markets m ON m.id = n.market_id
        WHERE n.recipient_id = %s
        ORDER BY n.created_at DESC, n.id DESC
        LIMIT %s
        """,
        (recipient_id, limit),
    )
    notifications = [_notification_response(row) for row in cursor.fetchall()]
    cursor.execute(
        "SELECT COUNT(*) AS total FROM gotrendlabs_user_notifications WHERE recipient_id = %s AND is_read = false",
        (recipient_id,),
    )
    unread = cursor.fetchone()
    return {"unread_count": int(unread["total"] or 0), "notifications": notifications}


def _market_participant_recipient_ids(cursor, market_id, actor_id):
    cursor.execute(
        """
        SELECT DISTINCT p.user_id
        FROM gotrendlabs_predictions p
        JOIN gotrendlabs_users u ON u.id = p.user_id
        WHERE p.market_id = %s
          AND p.user_id <> %s
          AND u.is_bot = false
        """,
        (market_id, actor_id),
    )
    return [row["user_id"] for row in cursor.fetchall()]


def _create_notification(
    cursor,
    *,
    recipient_id,
    actor=None,
    actor_id=None,
    market_id=None,
    comment_id=None,
    event_type,
    source_key,
    title,
    body,
    metadata=None,
    suppress_self=True,
):
    actor = actor or {}
    notification_actor_id = actor.get("id") or actor_id
    if actor.get("is_bot") or (suppress_self and notification_actor_id and recipient_id == notification_actor_id):
        return
    cursor.execute("SELECT is_bot FROM gotrendlabs_users WHERE id = %s", (recipient_id,))
    recipient = cursor.fetchone()
    recipient_is_bot = recipient["is_bot"] if isinstance(recipient, dict) else recipient[0] if recipient else False
    if not recipient or recipient_is_bot:
        return
    cursor.execute(
        """
        INSERT INTO gotrendlabs_user_notifications
            (recipient_id, actor_id, market_id, comment_id, event_type, source_key, title, body, is_read, read_at, metadata, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, false, NULL, %s::jsonb, %s)
        ON CONFLICT (recipient_id, source_key) DO NOTHING
        """,
        (
            recipient_id,
            notification_actor_id,
            market_id,
            comment_id,
            event_type,
            source_key,
            title,
            body,
            json.dumps(metadata or {}),
            datetime.now(timezone.utc),
        ),
    )


def _notify_market_participants(cursor, *, actor, market_id, comment_id=None, event_type, source_key, title, body, metadata=None):
    if actor.get("is_bot"):
        return
    for recipient_id in _market_participant_recipient_ids(cursor, market_id, actor["id"]):
        _create_notification(
            cursor,
            recipient_id=recipient_id,
            actor=actor,
            market_id=market_id,
            comment_id=comment_id,
            event_type=event_type,
            source_key=source_key,
            title=title,
            body=body,
            metadata=metadata,
        )


def _notify_comment_author(cursor, *, actor, comment_id, event_type, source_key, title, body, metadata=None):
    if actor.get("is_bot"):
        return
    cursor.execute(
        """
        SELECT mc.author_id, mc.market_id
        FROM gotrendlabs_market_comments mc
        WHERE mc.id = %s AND mc.status = 'visible'
        """,
        (comment_id,),
    )
    comment = cursor.fetchone()
    if not comment:
        return
    _create_notification(
        cursor,
        recipient_id=comment["author_id"],
        actor=actor,
        market_id=comment["market_id"],
        comment_id=comment_id,
        event_type=event_type,
        source_key=source_key,
        title=title,
        body=body,
        metadata=metadata,
    )


def _queue_status_label(value):
    return {
        "pending": "Pendente",
        "converted": "Convertida",
        "reviewed": "Revisado",
        "rewarded": "Recompensado",
        "approved": "Aprovada",
        "rejected": "Rejeitado",
    }.get(value, value)


def _queue_severity_label(value):
    return {"low": "Baixa", "medium": "Média", "high": "Alta"}.get(value, value)


def _date_label(value):
    return value.strftime("%d/%m/%Y %H:%M") if value else ""


def _suggestion_response(row):
    return {
        "id": row["id"],
        "kind": "suggestion",
        "title": row["question"],
        "category": row["category"],
        "queue_label": "Mercado",
        "item_type": "Sugestão de mercado",
        "status": row["status"],
        "status_label": _queue_status_label(row["status"]),
        "severity": "medium",
        "severity_label": "Média",
        "owner_label": "Editorial",
        "age_label": _age_label(row["created_at"]),
        "author_handle": _handle_seed(row["author_handle"]) if row["author_handle"] else None,
        "author_id": row["author_id"],
        "guest_name": row["guest_name"] or "",
        "guest_email": row["guest_email"] or "",
        "source": row["suggested_source"],
        "description": row["rationale"],
        "admin_note": row["admin_note"] or "",
        "reward_gtl": row["reward_gtl"],
        "converted_market_slug": row["converted_market_slug"],
        "created_at": row["created_at"].isoformat(),
        "created_at_label": _date_label(row["created_at"]),
        "reviewed_at": row["reviewed_at"].isoformat() if row["reviewed_at"] else None,
    }


def _feedback_response(row):
    return {
        "id": row["id"],
        "kind": "feedback",
        "title": row["feedback_type"],
        "category": "Feedback",
        "queue_label": "Feedback",
        "item_type": row["feedback_type"],
        "status": row["status"],
        "status_label": _queue_status_label(row["status"]),
        "severity": row["severity"],
        "severity_label": _queue_severity_label(row["severity"]),
        "owner_label": "Operação",
        "age_label": _age_label(row["created_at"]),
        "author_handle": _handle_seed(row["author_handle"]) if row["author_handle"] else None,
        "author_id": row["author_id"],
        "guest_name": row["guest_name"] or "",
        "guest_email": row["guest_email"] or "",
        "source": "",
        "description": row["description"],
        "admin_note": row["admin_note"] or "",
        "reward_gtl": row["reward_gtl"],
        "converted_market_slug": None,
        "created_at": row["created_at"].isoformat(),
        "created_at_label": _date_label(row["created_at"]),
        "reviewed_at": row["reviewed_at"].isoformat() if row["reviewed_at"] else None,
    }


def _wallet_recharge_response(row):
    title = "Solicitação de recarga educativa"
    amount_gtl = row["amount_gtl"]
    if amount_gtl:
        title = f"{title} · {amount_gtl} GT₵"
    return {
        "id": row["id"],
        "kind": "wallet_recharge",
        "title": title,
        "category": "Wallet",
        "queue_label": "Recarga",
        "item_type": "Recarga educativa",
        "status": row["status"],
        "status_label": _queue_status_label(row["status"]),
        "severity": "medium",
        "severity_label": "Média",
        "owner_label": "Operação",
        "age_label": _age_label(row["created_at"]),
        "author_handle": _handle_seed(row["author_handle"]) if row["author_handle"] else None,
        "author_id": row["user_id"],
        "guest_name": "",
        "guest_email": "",
        "source": "",
        "description": "Pedido de crédito educativo para voltar a participar dos mercados.",
        "admin_note": row["admin_note"] or "",
        "reward_gtl": amount_gtl,
        "converted_market_slug": None,
        "created_at": row["created_at"].isoformat(),
        "created_at_label": _date_label(row["created_at"]),
        "reviewed_at": row["reviewed_at"].isoformat() if row["reviewed_at"] else None,
    }


def _wallet_recharge_public_response(row):
    return {
        "id": row["id"],
        "status": row["status"],
        "status_label": _queue_status_label(row["status"]),
        "amount_gtl": row["amount_gtl"],
        "admin_note": row["admin_note"] or "",
        "created_at": row["created_at"].isoformat(),
        "created_at_label": _date_label(row["created_at"]),
        "reviewed_at": row["reviewed_at"].isoformat() if row["reviewed_at"] else None,
    }


def _get_wallet_recharge_request(cursor, request_id):
    cursor.execute(
        """
        SELECT r.*, u.username AS author_handle
        FROM gotrendlabs_wallet_recharge_requests r
        JOIN gotrendlabs_users u ON u.id = r.user_id
        WHERE r.id = %s
        """,
        (request_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação de recarga não encontrada.")
    return row


def _get_suggestion(cursor, suggestion_id):
    cursor.execute(
        """
        SELECT s.*, u.username AS author_handle, m.slug AS converted_market_slug
        FROM gotrendlabs_market_suggestions s
        LEFT JOIN gotrendlabs_users u ON u.id = s.author_id
        LEFT JOIN gotrendlabs_markets m ON m.id = s.converted_market_id
        WHERE s.id = %s
        """,
        (suggestion_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sugestão não encontrada.")
    return row


def _get_feedback(cursor, feedback_id):
    cursor.execute(
        """
        SELECT f.*, u.username AS author_handle
        FROM gotrendlabs_product_feedback f
        LEFT JOIN gotrendlabs_users u ON u.id = f.author_id
        WHERE f.id = %s
        """,
        (feedback_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback não encontrado.")
    return row


def _upsert_category(cursor, name, slug=None, notice=None):
    cleaned_slug = _slug_seed(slug or name, max_length=100)
    notice_value = (notice or "").strip() if notice is not None else ""
    should_update_notice = notice is not None
    cursor.execute(
        """
        INSERT INTO gotrendlabs_market_categories (name, slug, notice, is_blocked, blocked_reason, created_at)
        VALUES (%s, %s, %s, false, '', %s)
        ON CONFLICT (slug) DO UPDATE
        SET name = EXCLUDED.name,
            notice = CASE WHEN %s THEN EXCLUDED.notice ELSE gotrendlabs_market_categories.notice END
        RETURNING id, name, slug, notice, is_blocked
        """,
        (name.strip(), cleaned_slug, notice_value, datetime.now(timezone.utc), should_update_notice),
    )
    return cursor.fetchone()


def _upsert_subcategory(cursor, category_id, name, slug=None, notice=None):
    cleaned_slug = _slug_seed(slug or name, max_length=100)
    notice_value = (notice or "").strip() if notice is not None else ""
    should_update_notice = notice is not None
    cursor.execute(
        """
        INSERT INTO gotrendlabs_market_subcategories (category_id, name, slug, notice, is_blocked, blocked_reason, created_at)
        VALUES (%s, %s, %s, %s, false, '', %s)
        ON CONFLICT (category_id, slug) DO UPDATE
        SET name = EXCLUDED.name,
            notice = CASE WHEN %s THEN EXCLUDED.notice ELSE gotrendlabs_market_subcategories.notice END
        RETURNING id, name, slug, notice, is_blocked
        """,
        (category_id, name.strip(), cleaned_slug, notice_value, datetime.now(timezone.utc), should_update_notice),
    )
    return cursor.fetchone()


def _upsert_event(cursor, subcategory_id, name, slug=None, notice=None):
    cleaned_slug = _slug_seed(slug or name, max_length=100)
    notice_value = (notice or "").strip() if notice is not None else ""
    should_update_notice = notice is not None
    cursor.execute(
        """
        INSERT INTO gotrendlabs_market_events (subcategory_id, name, slug, notice, is_blocked, blocked_reason, created_at)
        VALUES (%s, %s, %s, %s, false, '', %s)
        ON CONFLICT (subcategory_id, slug) DO UPDATE
        SET name = EXCLUDED.name,
            notice = CASE WHEN %s THEN EXCLUDED.notice ELSE gotrendlabs_market_events.notice END
        RETURNING id, name, slug, notice, is_blocked
        """,
        (subcategory_id, name.strip(), cleaned_slug, notice_value, datetime.now(timezone.utc), should_update_notice),
    )
    return cursor.fetchone()


def _ensure_taxonomy_available(category, subcategory, event=None):
    if category["is_blocked"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Categoria bloqueada para novos mercados.")
    if subcategory["is_blocked"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Subcategoria bloqueada para novos mercados.")
    if event and event["is_blocked"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Evento bloqueado para novos mercados.")


def _admin_market_by_slug(cursor, slug):
    rows = _market_rows(cursor, "WHERE m.slug = %s", [slug])
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mercado não encontrado.")
    return rows[0]


def _option_dict(option):
    if isinstance(option, dict):
        return option
    if hasattr(option, "model_dump"):
        return option.model_dump()
    return option.dict()


def _even_probabilities(total):
    exact = _even_probability_exact(total)
    return [{"probability": _display_probability(exact), "probability_exact": exact} for _ in range(total)]


def _normalize_market_options(payload):
    if payload.kind not in {"binary", "multiple"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Tipo de mercado inválido.")

    if payload.kind == "binary":
        return [
            {"label": "SIM", "probability": 50, "probability_exact": Decimal("50.0000"), "hint": "Opção afirmativa"},
            {"label": "NAO", "probability": 50, "probability_exact": Decimal("50.0000"), "hint": "Opção negativa"},
        ]

    raw_options = [_option_dict(option) for option in payload.options]
    normalized = []
    seen = set()
    for option in raw_options:
        label = (option.get("label") or "").strip()
        if not label:
            continue
        label_key = label.casefold()
        if label_key in seen:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Opções duplicadas não são permitidas.")
        seen.add(label_key)
        normalized.append(
            {
                "label": label,
                "probability": 0,
                "probability_exact": Decimal("0.0000"),
                "hint": (option.get("hint") or "").strip(),
            }
        )

    if len(normalized) < 2:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Mercado de múltipla escolha exige pelo menos duas opções.")

    for option, probability in zip(normalized, _even_probabilities(len(normalized))):
        option.update(probability)
    return normalized


def _validate_admin_market_payload(payload):
    missing = []
    required_text = {
        "summary": payload.summary,
        "source": payload.source,
        "resolution_criteria": payload.resolution_criteria,
        "close_timezone": payload.close_timezone,
        "thumb_color": payload.thumb_color,
    }
    for field, value in required_text.items():
        if not (value or "").strip():
            missing.append(field)
    if not payload.close_at:
        missing.append("close_at")
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Campos obrigatórios ausentes: " + ", ".join(missing),
        )


def _payload_closes_in(payload):
    return _short_close_label(payload.close_at)


def _save_market_options(cursor, market_id, options, *, preserve_existing_probability=False):
    cursor.execute(
        """
        SELECT id, label, probability_exact
        FROM gotrendlabs_market_options
        WHERE market_id = %s
        """,
        (market_id,),
    )
    existing_options = cursor.fetchall()
    existing_by_label = {row["label"]: row for row in existing_options}
    desired_labels = {option["label"].strip() for option in options}

    for index, option in enumerate(options, start=1):
        label = option["label"].strip()
        existing = existing_by_label.get(label)
        if existing:
            probability_exact = existing["probability_exact"] if preserve_existing_probability else _decimal_probability(option["probability_exact"])
            cursor.execute(
                """
                UPDATE gotrendlabs_market_options
                SET probability_exact = %s,
                    hint = %s,
                    display_order = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (
                    _decimal_probability(probability_exact),
                    option.get("hint", "").strip(),
                    index,
                    datetime.now(timezone.utc),
                    existing["id"],
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO gotrendlabs_market_options (market_id, label, probability_exact, hint, display_order, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    market_id,
                    label,
                    _decimal_probability(option["probability_exact"]),
                    option.get("hint", "").strip(),
                    index,
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                ),
            )

    removed_ids = [row["id"] for row in existing_options if row["label"] not in desired_labels]
    if not removed_ids:
        return
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM gotrendlabs_predictions
        WHERE market_option_id = ANY(%s)
        """,
        (removed_ids,),
    )
    if cursor.fetchone()["total"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Não é possível remover opções que já possuem previsões vinculadas.",
        )
    cursor.execute("DELETE FROM gotrendlabs_market_options WHERE id = ANY(%s)", (removed_ids,))


def _validate_publishable(cursor, market_id):
    cursor.execute(
        """
        SELECT title, summary, source, resolution_criteria, close_at, close_timezone, thumb_color,
               kind, category_id, subcategory_id, event_id
        FROM gotrendlabs_markets
        WHERE id = %s
        """,
        (market_id,),
    )
    market = cursor.fetchone()
    missing = []
    for field in ("title", "summary", "source", "resolution_criteria", "close_at", "close_timezone", "thumb_color", "event_id"):
        if not market[field]:
            missing.append(field)
    cursor.execute(
        """
                SELECT label, probability_exact
        FROM gotrendlabs_market_options
        WHERE market_id = %s
        ORDER BY display_order ASC, id ASC
        """,
        (market_id,),
    )
    options = cursor.fetchall()
    option_count = len(options)
    if market["kind"] == "binary":
        if option_count != 2 or [option["label"] for option in options] != ["SIM", "NAO"] or [_display_probability(option["probability_exact"]) for option in options] != [50, 50]:
            missing.append("duas opções binárias fixas 50/50")
    if market["kind"] == "multiple" and option_count < 2:
        missing.append("duas ou mais opções")
    if market["kind"] == "multiple" and option_count >= 2:
        expected = _even_probability_exact(option_count)
        if any(_decimal_probability(option["probability_exact"]) != expected for option in options):
            missing.append("probabilidades iniciais iguais")
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mercado não publicável: " + ", ".join(missing),
        )


def _taxonomy_response(cursor):
    cursor.execute(
        """
        SELECT c.id, c.name, c.slug, c.notice, c.is_blocked, c.blocked_reason, c.blocked_at, COUNT(m.id) AS markets_count
        FROM gotrendlabs_market_categories c
        LEFT JOIN gotrendlabs_markets m ON m.category_id = c.id
        GROUP BY c.id, c.name, c.slug, c.notice, c.is_blocked, c.blocked_reason, c.blocked_at
        ORDER BY c.name ASC
        """
    )
    categories = []
    for category in cursor.fetchall():
        cursor.execute(
            """
            SELECT sc.id, sc.name, sc.slug, sc.notice, sc.is_blocked, sc.blocked_reason, sc.blocked_at, COUNT(m.id) AS markets_count
            FROM gotrendlabs_market_subcategories sc
            LEFT JOIN gotrendlabs_markets m ON m.subcategory_id = sc.id
            WHERE sc.category_id = %s
            GROUP BY sc.id, sc.name, sc.slug, sc.notice, sc.is_blocked, sc.blocked_reason, sc.blocked_at
            ORDER BY sc.name ASC
            """,
            (category["id"],),
        )
        subcategories = []
        for subcategory in cursor.fetchall():
            cursor.execute(
                """
                SELECT ev.name, ev.slug, ev.notice, ev.is_blocked, ev.blocked_reason, ev.blocked_at, COUNT(m.id) AS markets_count
                FROM gotrendlabs_market_events ev
                LEFT JOIN gotrendlabs_markets m ON m.event_id = ev.id
                WHERE ev.subcategory_id = %s
                GROUP BY ev.id, ev.name, ev.slug, ev.notice, ev.is_blocked, ev.blocked_reason, ev.blocked_at
                ORDER BY ev.name ASC
                """,
                (subcategory["id"],),
            )
            subcategories.append(
                {
                    "name": subcategory["name"],
                    "slug": subcategory["slug"],
                    "notice": subcategory["notice"] or "",
                    "markets_count": subcategory["markets_count"],
                    "is_blocked": subcategory["is_blocked"],
                    "blocked_reason": subcategory["blocked_reason"] or "",
                    "blocked_at": subcategory["blocked_at"].isoformat() if subcategory["blocked_at"] else None,
                    "events": [
                        {
                            "name": row["name"],
                            "slug": row["slug"],
                            "notice": row["notice"] or "",
                            "markets_count": row["markets_count"],
                            "is_blocked": row["is_blocked"],
                            "blocked_reason": row["blocked_reason"] or "",
                            "blocked_at": row["blocked_at"].isoformat() if row["blocked_at"] else None,
                        }
                        for row in cursor.fetchall()
                    ],
                }
            )
        categories.append(
            {
                "name": category["name"],
                "slug": category["slug"],
                "notice": category["notice"] or "",
                "markets_count": category["markets_count"],
                "is_blocked": category["is_blocked"],
                "blocked_reason": category["blocked_reason"] or "",
                "blocked_at": category["blocked_at"].isoformat() if category["blocked_at"] else None,
                "subcategories": subcategories,
            }
        )
    return {"categories": categories}


def _public_taxonomy_response(cursor):
    taxonomy = _taxonomy_response(cursor)
    categories = []
    for category in taxonomy["categories"]:
        if category.get("is_blocked"):
            continue
        categories.append(
            {
                **category,
                "subcategories": [
                    {
                        **subcategory,
                        "events": [event for event in subcategory.get("events", []) if not event.get("is_blocked")],
                    }
                    for subcategory in category.get("subcategories", [])
                    if not subcategory.get("is_blocked")
                ],
            }
        )
    return {"categories": categories}


def _suggestion_category_name(cursor, category_value):
    value = (category_value or "").strip()
    if not value:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Categoria é obrigatória.")
    cursor.execute(
        """
        SELECT name
        FROM gotrendlabs_market_categories
        WHERE is_blocked = false
          AND (lower(name) = lower(%s) OR lower(slug) = lower(%s))
        """,
        (value, value),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Selecione uma categoria ativa cadastrada.")
    return row["name"]


def _ranking_categories(cursor):
    cursor.execute(
        """
        SELECT c.id, c.name, c.slug
        FROM gotrendlabs_market_categories c
        ORDER BY c.name ASC
        """
    )
    categories = []
    for category in cursor.fetchall():
        cursor.execute(
            """
            SELECT id, name, slug
            FROM gotrendlabs_market_subcategories
            WHERE category_id = %s
            ORDER BY name ASC
            """,
            (category["id"],),
        )
        subcategories = []
        for subcategory in cursor.fetchall():
            cursor.execute(
                """
                SELECT name, slug
                FROM gotrendlabs_market_events
                WHERE subcategory_id = %s
                ORDER BY name ASC
                """,
                (subcategory["id"],),
            )
            subcategories.append(
                {
                    "name": subcategory["name"],
                    "slug": subcategory["slug"],
                    "events": [{"name": row["name"], "slug": row["slug"]} for row in cursor.fetchall()],
                }
            )
        categories.append(
            {
                "name": category["name"],
                "slug": category["slug"],
                "subcategories": subcategories,
            }
        )
    return categories


def _ranking_badges_by_user(cursor, user_ids, visible_limit=3):
    badges_by_user = {user_id: {"badges": [], "badges_total": 0} for user_id in user_ids}
    if not user_ids:
        return badges_by_user
    cursor.execute(
        """
        SELECT user_id, code, name, badge_type, image_url, image_dark_url, awarded_at, badge_rank, badges_total
        FROM (
            SELECT a.user_id, b.code, b.name, b.badge_type, b.image_url, b.image_dark_url, a.awarded_at,
                   ROW_NUMBER() OVER (PARTITION BY a.user_id ORDER BY a.awarded_at DESC, b.code ASC) AS badge_rank,
                   COUNT(*) OVER (PARTITION BY a.user_id) AS badges_total
            FROM gotrendlabs_user_badge_awards a
            JOIN gotrendlabs_badge_definitions b ON b.id = a.badge_id
            WHERE b.is_active = true
              AND a.user_id = ANY(%s)
              AND b.code NOT LIKE 'dev_%%'
              AND lower(COALESCE(b.name, '')) NOT LIKE '%% dev'
              AND lower(COALESCE(b.description, '')) NOT LIKE '%%simulação dev%%'
              AND lower(COALESCE(b.rule_description, '')) NOT LIKE '%%preview local%%'
        ) ranked_badges
        WHERE badge_rank <= %s
        ORDER BY user_id ASC, badge_rank ASC
        """,
        (user_ids, visible_limit),
    )
    for badge in cursor.fetchall():
        user_badges = badges_by_user.setdefault(badge["user_id"], {"badges": [], "badges_total": 0})
        user_badges["badges_total"] = int(badge["badges_total"] or 0)
        user_badges["badges"].append(
            {
                "code": badge["code"],
                "name": badge["name"],
                "image_url": badge["image_url"] or "",
                "image_dark_url": badge["image_dark_url"] or "",
                "badge_type": badge["badge_type"] or "global",
                "awarded_at": badge["awarded_at"].isoformat(),
            }
        )
    return badges_by_user


def _attach_ranking_badges(cursor, rows):
    badges_by_user = _ranking_badges_by_user(cursor, [row["user_id"] for row in rows])
    enriched_rows = []
    for row in rows:
        badge_summary = badges_by_user.get(row["user_id"], {"badges": [], "badges_total": 0})
        enriched_rows.append(
            {
                **row,
                "badges": badge_summary["badges"],
                "badges_total": badge_summary["badges_total"],
            }
        )
    return enriched_rows


def _ranking_theme_rows(cursor, category, subcategory, event, limit=50):
    where = [
        "u.is_active = true",
        "u.is_staff = false",
        "u.is_superuser = false",
        "u.is_bot = false",
        *PUBLIC_USER_FILTERS,
        "p.status = 'resolved'",
        "c.slug = %s",
    ]
    params = [category]
    if subcategory:
        where.append("sc.slug = %s")
        params.append(subcategory)
    if event:
        where.append("ev.slug = %s")
        params.append(event)
    cursor.execute(
        f"""
        SELECT u.id, u.username, u.first_name, u.date_joined,
               p.probability_at_entry, p.won, p.updated_at, p.id AS prediction_id,
               c.name AS category_name, sc.name AS subcategory_name, ev.name AS event_name
        FROM gotrendlabs_predictions p
        JOIN gotrendlabs_users u ON u.id = p.user_id
        JOIN gotrendlabs_markets m ON m.id = p.market_id
        JOIN gotrendlabs_market_categories c ON c.id = m.category_id
        JOIN gotrendlabs_market_subcategories sc ON sc.id = m.subcategory_id
        LEFT JOIN gotrendlabs_market_events ev ON ev.id = m.event_id
        WHERE {" AND ".join(where)}
        ORDER BY u.id ASC, p.updated_at ASC, p.id ASC
        """,
        params,
    )
    users = {}
    for row in cursor.fetchall():
        user = users.setdefault(
            row["id"],
            {
                "user_id": row["id"],
                "username": row["username"],
                "first_name": row["first_name"],
                "date_joined": row["date_joined"],
                "score": INITIAL_REPUTATION,
                "total": 0,
                "wins": 0,
                "strong_category": row["event_name"] if event else row["subcategory_name"] if subcategory else row["category_name"],
            },
        )
        probability = max(Decimal("0"), min(Decimal("1"), _decimal_probability(row["probability_at_entry"]) / Decimal("100")))
        delta = REPUTATION_K_FACTOR * (Decimal("1") - probability) if row["won"] else -(REPUTATION_K_FACTOR * probability)
        user["score"] = max(0, user["score"] + int(delta.to_integral_value(rounding=ROUND_HALF_UP)))
        user["total"] += 1
        if row["won"]:
            user["wins"] += 1

    ranked = sorted(users.values(), key=lambda row: (-row["score"], row["date_joined"], row["user_id"]))[:limit]
    rows = []
    for index, row in enumerate(ranked, start=1):
        accuracy = "0%"
        if row["total"] > 0:
            accuracy = f"{int((Decimal(row['wins']) * Decimal('100') / Decimal(row['total'])).to_integral_value(rounding=ROUND_HALF_UP))}%"
        rows.append(
            {
                "position": index,
                "user_id": row["user_id"],
                "handle": _handle_seed(row["username"]),
                "display_name": row["first_name"] or _handle_seed(row["username"]),
                "reputation_score": row["score"],
                "accuracy_indicator": accuracy,
                "strong_category": row["strong_category"] or "Geral",
            }
        )
    return _attach_ranking_badges(cursor, rows)


def _record_event(cursor, event_type, *, user_id=None, email="", provider="", ip_address=None, user_agent=""):
    cursor.execute(
        """
        INSERT INTO gotrendlabs_auth_events (user_id, event_type, email, provider, ip_address, user_agent, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, event_type, email or "", provider or "", ip_address, user_agent, datetime.now(timezone.utc)),
    )


def _create_session(cursor, user_id, request):
    token = issue_token()
    expires_at = datetime.now(timezone.utc) + SESSION_TTL
    ip_address, user_agent = _client_meta(request)
    cursor.execute(
        """
        INSERT INTO gotrendlabs_auth_sessions
            (user_id, token_hash, created_at, last_seen_at, expires_at, revoked_at, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s, NULL, %s, %s)
        """,
        (user_id, hash_token(token), datetime.now(timezone.utc), datetime.now(timezone.utc), expires_at, ip_address, user_agent),
    )
    return {"token": token, "expires_at": expires_at.isoformat()}


def _bearer_token(authorization):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão ausente.")
    return authorization.split(" ", 1)[1].strip()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"name": "GoTrendLabs Backend API", "status": "ok"}


@app.get("/markets", response_model=MarketListResponse)
def list_markets(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    authorization: str = Header(default=""),
):
    where = ["m.status NOT IN ('draft', 'canceled')"]
    params = []
    if status_filter:
        where.append("lower(m.status) = lower(%s)")
        params.append(status_filter)
    if category:
        where.append("(lower(c.name) = lower(%s) OR lower(c.slug) = lower(%s))")
        params.extend([category, category])
    if subcategory:
        where.append("(lower(sc.name) = lower(%s) OR lower(sc.slug) = lower(%s))")
        params.extend([subcategory, subcategory])
    where_sql = "WHERE " + " AND ".join(where)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            viewer = _optional_current_user(cursor, authorization)
            rows = _market_rows(cursor, where_sql, params)
            return {"markets": [_market_response(cursor, row, viewer_id=viewer["id"] if viewer else None, include_comments=False) for row in rows]}


@app.get("/markets/{slug}", response_model=MarketResponse)
def get_market(slug: str, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            viewer = _optional_current_user(cursor, authorization)
            rows = _market_rows(cursor, "WHERE m.slug = %s AND m.status <> 'draft'", [slug])
            if not rows:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mercado não encontrado.")
            return _market_response(cursor, rows[0], viewer_id=viewer["id"] if viewer else None)


def _public_market_row_or_404(cursor, slug):
    rows = _market_rows(cursor, "WHERE m.slug = %s AND m.status NOT IN ('draft', 'canceled')", [slug])
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mercado não encontrado.")
    return rows[0]


@app.post("/markets/{slug}/favorite", response_model=MarketResponse)
def favorite_market(slug: str, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            row = _public_market_row_or_404(cursor, slug)
            cursor.execute(
                """
                INSERT INTO gotrendlabs_market_favorites (user_id, market_id, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, market_id) DO NOTHING
                """,
                (user["id"], row["id"], datetime.now(timezone.utc)),
            )
            return _market_response(cursor, row, viewer_id=user["id"], include_comments=False)


@app.delete("/markets/{slug}/favorite", response_model=MarketResponse)
def unfavorite_market(slug: str, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            row = _public_market_row_or_404(cursor, slug)
            cursor.execute(
                """
                DELETE FROM gotrendlabs_market_favorites
                WHERE user_id = %s AND market_id = %s
                """,
                (user["id"], row["id"]),
            )
            return _market_response(cursor, row, viewer_id=user["id"], include_comments=False)


@app.post("/markets/{slug}/like", response_model=MarketResponse)
def like_market(slug: str, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            row = _public_market_row_or_404(cursor, slug)
            cursor.execute(
                """
                INSERT INTO gotrendlabs_market_likes (user_id, market_id, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, market_id) DO NOTHING
                RETURNING id
                """,
                (user["id"], row["id"], datetime.now(timezone.utc)),
            )
            created_like = bool(cursor.fetchone())
            if created_like:
                _notify_market_participants(
                    cursor,
                    actor=user,
                    market_id=row["id"],
                    event_type="market_like",
                    source_key=f"market_like:{row['id']}:{user['id']}",
                    title="Seu mercado recebeu uma curtida",
                    body=f"{_handle_seed(user['username'])} curtiu um mercado em que você fez previsão.",
                )
            rows = _market_rows(cursor, "WHERE m.slug = %s AND m.status NOT IN ('draft', 'canceled')", [slug])
            return _market_response(cursor, rows[0], viewer_id=user["id"], include_comments=False)


@app.delete("/markets/{slug}/like", response_model=MarketResponse)
def unlike_market(slug: str, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            row = _public_market_row_or_404(cursor, slug)
            cursor.execute(
                """
                DELETE FROM gotrendlabs_market_likes
                WHERE user_id = %s AND market_id = %s
                """,
                (user["id"], row["id"]),
            )
            rows = _market_rows(cursor, "WHERE m.slug = %s AND m.status NOT IN ('draft', 'canceled')", [slug])
            return _market_response(cursor, rows[0], viewer_id=user["id"], include_comments=False)


def _increment_market_counter(cursor, slug, field_name):
    cursor.execute(
        f"""
        UPDATE gotrendlabs_markets
        SET {field_name} = {field_name} + 1, updated_at = %s
        WHERE slug = %s AND status <> 'draft'
        RETURNING view_count, share_count
        """,
        (datetime.now(timezone.utc), slug),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mercado não encontrado.")
    return {"view_count": int(row["view_count"] or 0), "share_count": int(row["share_count"] or 0)}


@app.post("/markets/{slug}/view")
def track_market_view(slug: str, request: Request):
    _enforce_rate_limit("market-view", _rate_limit_identity(request, slug), limit=120, window_seconds=60)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            return _increment_market_counter(cursor, slug, "view_count")


@app.post("/markets/{slug}/share")
def track_market_share(slug: str, request: Request):
    _enforce_rate_limit("market-share", _rate_limit_identity(request, slug), limit=60, window_seconds=60)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            return _increment_market_counter(cursor, slug, "share_count")


@app.get("/markets/{slug}/comments", response_model=CommentListResponse)
def list_market_comments(slug: str, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            viewer = _optional_current_user(cursor, authorization)
            cursor.execute("SELECT id, status FROM gotrendlabs_markets WHERE slug = %s AND status <> 'draft'", (slug,))
            market = cursor.fetchone()
            if not market:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mercado não encontrado.")
            return {"comments": _market_comments(cursor, market["id"], viewer_id=viewer["id"] if viewer else None)}


@app.get("/badges", response_model=BadgeListResponse)
def list_badges(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            viewer = _optional_current_user(cursor, authorization)
            if viewer:
                BadgeAwardEngine.reconcile_user(cursor, viewer["id"], ensure_user_core=_ensure_user_core)
            return {"badges": _badge_rows(cursor, user_id=viewer["id"] if viewer else None)}


@app.get("/taxonomy", response_model=AdminTaxonomyResponse)
def get_public_taxonomy():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            return _public_taxonomy_response(cursor)


@app.post("/markets/{slug}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(slug: str, payload: CommentCreatePayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            _require_email_confirmed(user)
            body = payload.body.strip()
            if not body:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Comentário não pode ficar vazio.")
            cursor.execute("SELECT id, status FROM gotrendlabs_markets WHERE slug = %s", (slug,))
            market = cursor.fetchone()
            if not market:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mercado não encontrado.")
            if market["status"] in {"draft", "canceled"}:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Este mercado não aceita comentários.")
            cursor.execute(
                """
                INSERT INTO gotrendlabs_market_comments
                    (market_id, author_id, body, status, moderation_note, moderated_by_id, moderated_at, created_at, updated_at)
                VALUES (%s, %s, %s, 'visible', '', NULL, NULL, %s, %s)
                RETURNING id
                """,
                (market["id"], user["id"], body, datetime.now(timezone.utc), datetime.now(timezone.utc)),
            )
            comment_id = cursor.fetchone()["id"]
            if not user.get("is_bot"):
                BadgeAwardEngine.on_comment_created(cursor, user["id"], market_id=market["id"])
                _notify_market_participants(
                    cursor,
                    actor=user,
                    market_id=market["id"],
                    comment_id=comment_id,
                    event_type="market_comment",
                    source_key=f"market_comment:{comment_id}",
                    title="Novo comentário em um mercado seu",
                    body=f"{_handle_seed(user['username'])} comentou em um mercado em que você fez previsão.",
                )
            return next(comment for comment in _market_comments(cursor, market["id"], viewer_id=user["id"]) if comment["id"] == comment_id)


def _set_comment_reaction(cursor, comment_id, user, reaction):
    _require_email_confirmed(user)
    user_id = user["id"]
    cursor.execute("SELECT mc.id FROM gotrendlabs_market_comments mc WHERE mc.id = %s AND mc.status = 'visible'", (comment_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado.")
    cursor.execute(
        """
        INSERT INTO gotrendlabs_comment_reactions (comment_id, user_id, reaction, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (comment_id, user_id)
        DO UPDATE SET reaction = EXCLUDED.reaction, updated_at = EXCLUDED.updated_at
        RETURNING (xmax = 0) AS inserted
        """,
        (comment_id, user_id, reaction, datetime.now(timezone.utc), datetime.now(timezone.utc)),
    )
    reaction_row = cursor.fetchone()
    if reaction == "like" and reaction_row:
        _notify_comment_author(
            cursor,
            actor=user,
            comment_id=comment_id,
            event_type="comment_like",
            source_key=f"comment_like:{comment_id}:{user_id}",
            title="Seu comentário recebeu uma curtida",
            body=f"{_handle_seed(user['username'])} curtiu seu comentário.",
        )
    cursor.execute("SELECT market_id FROM gotrendlabs_market_comments WHERE id = %s", (comment_id,))
    market_id = cursor.fetchone()["market_id"]
    return next(comment for comment in _market_comments(cursor, market_id, viewer_id=user_id) if comment["id"] == comment_id)


def _clear_comment_reaction(cursor, comment_id, user_id, reaction):
    cursor.execute("SELECT market_id FROM gotrendlabs_market_comments WHERE id = %s AND status = 'visible'", (comment_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado.")
    cursor.execute(
        "DELETE FROM gotrendlabs_comment_reactions WHERE comment_id = %s AND user_id = %s AND reaction = %s",
        (comment_id, user_id, reaction),
    )
    return next(comment for comment in _market_comments(cursor, row["market_id"], viewer_id=user_id) if comment["id"] == comment_id)


@app.post("/comments/{comment_id}/like", response_model=CommentResponse)
def like_comment(comment_id: int, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            return _set_comment_reaction(cursor, comment_id, user, "like")


@app.delete("/comments/{comment_id}/like", response_model=CommentResponse)
def unlike_comment(comment_id: int, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            return _clear_comment_reaction(cursor, comment_id, user["id"], "like")


@app.post("/comments/{comment_id}/dislike", response_model=CommentResponse)
def dislike_comment(comment_id: int, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            return _set_comment_reaction(cursor, comment_id, user, "dislike")


@app.delete("/comments/{comment_id}/dislike", response_model=CommentResponse)
def undislike_comment(comment_id: int, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            return _clear_comment_reaction(cursor, comment_id, user["id"], "dislike")


@app.post("/markets/{slug}/prediction-preview", response_model=PredictionPreviewResponse)
def preview_prediction(slug: str, payload: PredictionCreatePayload):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            return _prediction_preview(cursor, slug, payload)


@app.post("/markets/{slug}/predict", response_model=PredictionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(slug: str, payload: PredictionCreatePayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            _require_email_confirmed(user)
            cursor.execute(
                """
                SELECT id, slug, status
                FROM gotrendlabs_markets
                WHERE slug = %s
                """,
                (slug,),
            )
            market = cursor.fetchone()
            if not market:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mercado não encontrado.")
            if market["status"] != "open":
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Mercado fechado para novas previsões.")

            cursor.execute(
                """
                SELECT id, label, probability_exact, hint
                FROM gotrendlabs_market_options
                WHERE id = %s AND market_id = %s
                """,
                (payload.option_id, market["id"]),
            )
            option = cursor.fetchone()
            if not option:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Opção inválida para este mercado.")

            cursor.execute(
                """
                SELECT id
                FROM gotrendlabs_predictions
                WHERE user_id = %s AND market_id = %s
                """,
                (user["id"], market["id"]),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Você já registrou uma previsão neste mercado.")

            cursor.execute(
                """
                SELECT available_gtl, locked_gtl, total_earned_gtl
                FROM gotrendlabs_wallet_balances
                WHERE user_id = %s
                FOR UPDATE
                """,
                (user["id"],),
            )
            balance = cursor.fetchone()
            if not balance:
                _ensure_wallet_balance(cursor, user["id"])
                cursor.execute(
                    """
                    SELECT available_gtl, locked_gtl, total_earned_gtl
                    FROM gotrendlabs_wallet_balances
                    WHERE user_id = %s
                    FOR UPDATE
                    """,
                    (user["id"],),
                )
                balance = cursor.fetchone()
            if int(balance["available_gtl"] or 0) < payload.stake_amount:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Saldo insuficiente para esta previsão.")

            cursor.execute(
                """
                SELECT reputation_score
                FROM gotrendlabs_user_reputations
                WHERE user_id = %s
                """,
                (user["id"],),
            )
            reputation = cursor.fetchone()
            reputation_score = int(reputation["reputation_score"] if reputation else INITIAL_REPUTATION)
            probability_at_entry = max(_decimal_probability(option["probability_exact"]), PROBABILITY_QUANT)
            weight_at_entry = reputation_score * payload.stake_amount
            potential_payout = int((Decimal(payload.stake_amount) * Decimal("100") / probability_at_entry).to_integral_value())
            accepted_at = datetime.now(timezone.utc)

            cursor.execute(
                """
                INSERT INTO gotrendlabs_predictions
                    (user_id, market_id, market_option_id, stake_amount, probability_at_entry,
                     weight_at_entry, potential_payout, status, won, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'open', NULL, %s, %s)
                RETURNING id, created_at
                """,
                (
                    user["id"],
                    market["id"],
                    option["id"],
                    payload.stake_amount,
                    probability_at_entry,
                    weight_at_entry,
                    potential_payout,
                    accepted_at,
                    accepted_at,
                ),
            )
            prediction = cursor.fetchone()
            _record_wallet_entry(
                cursor,
                user["id"],
                entry_type="prediction_stake_lock",
                amount=payload.stake_amount,
                direction="lock",
                description=f"Stake bloqueado em previsão: {slug}",
                reference_type="prediction",
                reference_id=str(prediction["id"]),
            )
            _notify_market_participants(
                cursor,
                actor=user,
                market_id=market["id"],
                event_type="market_prediction",
                source_key=f"market_prediction:{prediction['id']}",
                title="Nova previsão em um mercado seu",
                body=f"{_handle_seed(user['username'])} fez uma previsão em um mercado em que você também participou.",
                metadata={"prediction_id": prediction["id"], "stake_amount": payload.stake_amount},
            )
            snapshot = _market_probability_snapshot(cursor, market["id"])
            wallet_after = _wallet_summary(cursor, user["id"])
            return {
                "prediction_id": prediction["id"],
                "market_id": market["id"],
                "option_id": option["id"],
                "stake_amount": payload.stake_amount,
                "accepted_at": prediction["created_at"].isoformat(),
                "wallet_balance_after": wallet_after,
                "market_probability_snapshot": snapshot,
                "potential_payout": potential_payout,
            }


@app.post("/suggestions/", response_model=QueueItemResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/suggestions", response_model=QueueItemResponse, status_code=status.HTTP_201_CREATED)
def create_suggestion(payload: MarketSuggestionPayload, request: Request, authorization: str = Header(default="")):
    _enforce_rate_limit("suggestion", _rate_limit_identity(request, payload.guest_email or authorization), limit=20, window_seconds=3600)
    if payload.kind not in {"binary", "multiple"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Tipo de mercado inválido.")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _optional_current_user(cursor, authorization)
            if user:
                _require_email_confirmed(user)
            if not user and (not payload.guest_name.strip() or not payload.guest_email):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nome e email são obrigatórios para visitantes.")
            if not user:
                _ensure_recaptcha(payload.recaptcha_token, request)
            category_name = _suggestion_category_name(cursor, payload.category)
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                INSERT INTO gotrendlabs_market_suggestions
                    (author_id, guest_name, guest_email, question, category, subcategory, kind, suggested_source, rationale,
                     status, admin_note, reward_gtl, converted_market_id, reviewed_by_id, reviewed_at, rewarded_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', '', NULL, NULL, NULL, NULL, NULL, %s, %s)
                RETURNING id
                """,
                (
                    user["id"] if user else None,
                    "" if user else payload.guest_name.strip(),
                    "" if user else str(payload.guest_email or "").lower(),
                    payload.question.strip(),
                    category_name,
                    payload.subcategory.strip(),
                    payload.kind,
                    payload.suggested_source.strip(),
                    payload.rationale.strip(),
                    now,
                    now,
                ),
            )
            suggestion_id = cursor.fetchone()["id"]
            return _suggestion_response(_get_suggestion(cursor, suggestion_id))


@app.post("/feedback/", response_model=QueueItemResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/feedback", response_model=QueueItemResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(payload: ProductFeedbackPayload, request: Request, authorization: str = Header(default="")):
    _enforce_rate_limit("feedback", _rate_limit_identity(request, payload.guest_email or authorization), limit=20, window_seconds=3600)
    if payload.severity not in {"low", "medium", "high"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Severidade inválida.")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _optional_current_user(cursor, authorization)
            if user:
                _require_email_confirmed(user)
            if not user and (not payload.guest_name.strip() or not payload.guest_email):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nome e email são obrigatórios para visitantes.")
            if not user:
                _ensure_recaptcha(payload.recaptcha_token, request)
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                INSERT INTO gotrendlabs_product_feedback
                    (author_id, guest_name, guest_email, feedback_type, severity, description, status, admin_note, reward_gtl,
                     reviewed_by_id, reviewed_at, rewarded_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, 'pending', '', NULL, NULL, NULL, NULL, %s, %s)
                RETURNING id
                """,
                (
                    user["id"] if user else None,
                    "" if user else payload.guest_name.strip(),
                    "" if user else str(payload.guest_email or "").lower(),
                    payload.feedback_type.strip(),
                    payload.severity,
                    payload.description.strip(),
                    now,
                    now,
                ),
            )
            feedback_id = cursor.fetchone()["id"]
            return _feedback_response(_get_feedback(cursor, feedback_id))


@app.get("/admin/system-logs", response_model=SystemLogListResponse)
def admin_list_system_logs(
    q: str = Query(default=""),
    level: str = Query(default=""),
    source: str = Query(default=""),
    logger: str = Query(default=""),
    event_type: str = Query(default=""),
    method: str = Query(default=""),
    path: str = Query(default=""),
    status_code: Optional[int] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    user_identifier: str = Query(default=""),
    request_id: str = Query(default=""),
    exception_type: str = Query(default=""),
    from_date: Optional[datetime] = Query(default=None, alias="from"),
    to_date: Optional[datetime] = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    authorization: str = Header(default=""),
):
    where = []
    params = []
    search = (q or "").strip()
    if search:
        where.append("(l.message ILIKE %s OR l.path ILIKE %s OR l.logger_name ILIKE %s OR l.request_id ILIKE %s OR l.exception_type ILIKE %s)")
        like = f"%{search}%"
        params.extend([like, like, like, like, like])
    if level:
        where.append("l.level = %s")
        params.append(level.upper())
    if source:
        where.append("l.source = %s")
        params.append(source)
    if logger:
        where.append("l.logger_name ILIKE %s")
        params.append(f"%{logger}%")
    if event_type:
        where.append("l.event_type = %s")
        params.append(event_type)
    if method:
        where.append("l.method = %s")
        params.append(method.upper())
    if path:
        where.append("l.path ILIKE %s")
        params.append(f"%{path}%")
    if status_code is not None:
        where.append("l.status_code = %s")
        params.append(status_code)
    if user_id is not None:
        where.append("l.user_id = %s")
        params.append(user_id)
    user_identifier_search = (user_identifier or "").strip()
    if " · " in user_identifier_search and user_identifier_search.startswith("@"):
        user_identifier_search = user_identifier_search.split(" · ", 1)[0].strip()
    if user_identifier_search:
        if user_identifier_search.isdigit():
            where.append("(l.user_id = %s OR u.username ILIKE %s OR u.email ILIKE %s OR u.first_name ILIKE %s)")
            like = f"%{user_identifier_search}%"
            params.extend([int(user_identifier_search), like, like, like])
        else:
            like = f"%{user_identifier_search}%"
            where.append("(u.username ILIKE %s OR u.email ILIKE %s OR u.first_name ILIKE %s)")
            params.extend([like, like, like])
    if request_id:
        where.append("l.request_id = %s")
        params.append(request_id)
    if exception_type:
        where.append("l.exception_type ILIKE %s")
        params.append(f"%{exception_type}%")
    if from_date:
        where.append("l.created_at >= %s")
        params.append(from_date)
    if to_date:
        where.append("l.created_at <= %s")
        params.append(to_date)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    offset = (page - 1) * page_size
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            cursor.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM gotrendlabs_system_logs l
                LEFT JOIN gotrendlabs_users u ON u.id = l.user_id
                {where_sql}
                """,
                params,
            )
            total = int(cursor.fetchone()["total"] or 0)
            cursor.execute(
                f"""
                SELECT l.id, l.created_at, l.expires_at, l.level, l.source, l.logger_name, l.event_type, l.message,
                       l.request_id, l.method, l.path, l.status_code, l.duration_ms, l.user_id, l.ip_address,
                       l.user_agent, l.exception_type, l.stack_trace, l.context,
                       u.username, u.email AS user_email, u.first_name AS user_display_name
                FROM gotrendlabs_system_logs l
                LEFT JOIN gotrendlabs_users u ON u.id = l.user_id
                {where_sql}
                ORDER BY l.created_at DESC, l.id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, page_size, offset],
            )
            logs = [_system_log_response(row) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(CASE WHEN level = 'DEBUG' THEN 1 ELSE 0 END), 0) AS debug,
                    COALESCE(SUM(CASE WHEN level = 'INFO' THEN 1 ELSE 0 END), 0) AS info,
                    COALESCE(SUM(CASE WHEN level = 'WARNING' THEN 1 ELSE 0 END), 0) AS warning,
                    COALESCE(SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END), 0) AS error,
                    COALESCE(SUM(CASE WHEN level = 'CRITICAL' THEN 1 ELSE 0 END), 0) AS critical
                FROM gotrendlabs_system_logs
                """
            )
            counts = cursor.fetchone()
            return {
                "logs": logs,
                "counts": {
                    "total": int(counts["total"] or 0),
                    "debug": int(counts["debug"] or 0),
                    "info": int(counts["info"] or 0),
                    "warning": int(counts["warning"] or 0),
                    "error": int(counts["error"] or 0),
                    "critical": int(counts["critical"] or 0),
                },
                "page": page,
                "page_size": page_size,
                "total": total,
            }


@app.get("/admin/system-logs/{log_id}", response_model=SystemLogResponse)
def admin_get_system_log(log_id: int, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            cursor.execute(
                """
                SELECT l.id, l.created_at, l.expires_at, l.level, l.source, l.logger_name, l.event_type, l.message,
                       l.request_id, l.method, l.path, l.status_code, l.duration_ms, l.user_id, l.ip_address,
                       l.user_agent, l.exception_type, l.stack_trace, l.context,
                       u.username, u.email AS user_email, u.first_name AS user_display_name
                FROM gotrendlabs_system_logs l
                LEFT JOIN gotrendlabs_users u ON u.id = l.user_id
                WHERE l.id = %s
                """,
                (log_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log não encontrado.")
            return _system_log_response(row)


@app.get("/admin/dashboard-summary", response_model=AdminDashboardSummaryResponse)
def admin_dashboard_summary(authorization: str = Header(default="")):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=7)
    next_24h = now + timedelta(hours=24)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            cursor.execute("SELECT status, COUNT(*) AS total FROM gotrendlabs_markets GROUP BY status")
            market_counts = {row["status"]: int(row["total"] or 0) for row in cursor.fetchall()}
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(view_count), 0) AS total_views,
                    COALESCE(SUM(share_count), 0) AS total_shares,
                    COALESCE(SUM(CASE WHEN status IN ('open', 'scheduled') AND close_at >= %s AND close_at <= %s THEN 1 ELSE 0 END), 0) AS closing_24h
                FROM gotrendlabs_markets
                """,
                (now, next_24h),
            )
            market_totals = cursor.fetchone()
            cursor.execute(
                """
                SELECT m.slug, m.title, m.status, m.status_label, c.name AS category,
                       s.name AS subcategory, ev.name AS event, m.view_count, m.share_count
                FROM gotrendlabs_markets m
                LEFT JOIN gotrendlabs_market_categories c ON c.id = m.category_id
                LEFT JOIN gotrendlabs_market_subcategories s ON s.id = m.subcategory_id
                LEFT JOIN gotrendlabs_market_events ev ON ev.id = m.event_id
                ORDER BY m.view_count DESC, m.share_count DESC, m.created_at DESC
                LIMIT 5
                """
            )
            top_markets = [
                {
                    "slug": row["slug"],
                    "title": row["title"],
                    "status": row["status"],
                    "status_label": row["status_label"],
                    "category": row["category"] or "",
                    "subcategory": row["subcategory"] or "",
                    "event": row["event"] or "",
                    "view_count": int(row["view_count"] or 0),
                    "share_count": int(row["share_count"] or 0),
                }
                for row in cursor.fetchall()
            ]
            cursor.execute("SELECT status, COUNT(*) AS total FROM gotrendlabs_market_suggestions GROUP BY status")
            suggestion_counts = {row["status"]: int(row["total"] or 0) for row in cursor.fetchall()}
            cursor.execute("SELECT status, COUNT(*) AS total FROM gotrendlabs_product_feedback GROUP BY status")
            feedback_counts = {row["status"]: int(row["total"] or 0) for row in cursor.fetchall()}
            cursor.execute(
                """
                SELECT severity, COUNT(*) AS total
                FROM gotrendlabs_product_feedback
                WHERE status = 'pending'
                GROUP BY severity
                """
            )
            feedback_severity_counts = {row["severity"]: int(row["total"] or 0) for row in cursor.fetchall()}
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(CASE WHEN account_status = 'active' THEN 1 ELSE 0 END), 0) AS active,
                    COALESCE(SUM(CASE WHEN account_status = 'deactivated' THEN 1 ELSE 0 END), 0) AS deactivated,
                    COALESCE(SUM(CASE WHEN is_staff = true AND is_superuser = false THEN 1 ELSE 0 END), 0) AS staff,
                    COALESCE(SUM(CASE WHEN is_superuser = true THEN 1 ELSE 0 END), 0) AS superuser,
                    COALESCE(SUM(CASE WHEN date_joined >= %s THEN 1 ELSE 0 END), 0) AS new_7d
                FROM gotrendlabs_users
                """,
                (since,),
            )
            user_counts = cursor.fetchone()
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END), 0) AS open,
                    COALESCE(SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END), 0) AS resolved,
                    COALESCE(SUM(CASE WHEN status = 'canceled' THEN 1 ELSE 0 END), 0) AS canceled,
                    COALESCE(SUM(CASE WHEN created_at >= %s THEN 1 ELSE 0 END), 0) AS created_7d
                FROM gotrendlabs_predictions
                """,
                (since,),
            )
            prediction_counts = cursor.fetchone()
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(CASE WHEN status = 'visible' THEN 1 ELSE 0 END), 0) AS visible,
                    COALESCE(SUM(CASE WHEN status = 'hidden' THEN 1 ELSE 0 END), 0) AS hidden
                FROM gotrendlabs_market_comments
                """
            )
            comment_counts = cursor.fetchone()
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(available_gtl), 0) AS available_gtl,
                    COALESCE(SUM(locked_gtl), 0) AS locked_gtl
                FROM gotrendlabs_wallet_balances
                """
            )
            wallet_counts = cursor.fetchone()
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM gotrendlabs_badge_definitions WHERE is_active = true) AS active_catalog,
                    (SELECT COUNT(*) FROM gotrendlabs_user_badge_awards) AS awarded
                """
            )
            badge_counts = cursor.fetchone()
            cursor.execute(
                """
                SELECT level, COUNT(*) AS total
                FROM gotrendlabs_system_logs
                WHERE created_at >= %s
                GROUP BY level
                """,
                (since,),
            )
            log_counts = {row["level"].lower(): int(row["total"] or 0) for row in cursor.fetchall()}
            cursor.execute("SELECT COUNT(*) AS total FROM gotrendlabs_admin_events WHERE created_at >= %s", (since,))
            admin_events_7d = int(cursor.fetchone()["total"] or 0)
            cursor.execute(
                """
                SELECT e.action, e.entity_type, e.entity_identifier, e.note, e.created_at,
                       u.username AS actor_handle, u.first_name AS actor_name
                FROM gotrendlabs_admin_events e
                LEFT JOIN gotrendlabs_users u ON u.id = e.actor_id
                ORDER BY e.created_at DESC, e.id DESC
                LIMIT 6
                """
            )
            recent_admin_events = [
                {
                    "action": row["action"],
                    "entity_type": row["entity_type"],
                    "entity_identifier": row["entity_identifier"],
                    "note": row["note"] or "",
                    "created_at": row["created_at"].isoformat() if row["created_at"] else "",
                    "actor": row["actor_handle"] or row["actor_name"] or "sistema",
                }
                for row in cursor.fetchall()
            ]
            cursor.execute(
                """
                SELECT email_enabled, smtp_host, smtp_port, default_from_email,
                       daemon_stale_after_minutes, daemon_missing_after_minutes,
                       ai_agents_enabled, ai_commenting_enabled, ai_predictions_enabled,
                       ai_llm_provider, ai_llm_base_url, ai_model, ai_max_comments_per_cycle,
                       ai_max_predictions_per_cycle, ai_min_humans_for_prediction, ai_max_stake_gtl
                FROM gotrendlabs_site_config
                WHERE singleton_key = 1
                """
            )
            site_config = cursor.fetchone()
            smtp_secret_configured = bool(os.environ.get("GOTRENDLABS_SMTP_PASSWORD") or os.environ.get("GOTRENDLABS_SMTP_API_KEY"))
            smtp_ready = bool(
                site_config
                and site_config["email_enabled"]
                and site_config["smtp_host"]
                and site_config["smtp_port"]
                and site_config["default_from_email"]
                and smtp_secret_configured
            )
            smtp_status = "ready" if smtp_ready else "pending" if site_config and site_config["email_enabled"] else "inactive"
            daemon_status = daemon_dashboard_status(
                cursor,
                now=now,
                stale_after_minutes=int(site_config["daemon_stale_after_minutes"] or 7) if site_config else 7,
                missing_after_minutes=int(site_config["daemon_missing_after_minutes"] or 21) if site_config else 21,
            )
            ai_health = ai_health_summary(cursor, now=now)
            return {
                "markets": {
                    **market_counts,
                    "total": sum(market_counts.values()),
                    "closing_24h": int(market_totals["closing_24h"] or 0),
                    "total_views": int(market_totals["total_views"] or 0),
                    "total_shares": int(market_totals["total_shares"] or 0),
                },
                "queues": {
                    "suggestions_pending": suggestion_counts.get("pending", 0),
                    "feedback_pending": feedback_counts.get("pending", 0),
                    "feedback_high_pending": feedback_severity_counts.get("high", 0),
                    "comments_hidden": int(comment_counts["hidden"] or 0),
                    "action_total": market_counts.get("locked", 0)
                    + suggestion_counts.get("pending", 0)
                    + feedback_counts.get("pending", 0)
                    + feedback_severity_counts.get("high", 0)
                    + int(comment_counts["hidden"] or 0),
                },
                "users": {
                    "total": int(user_counts["total"] or 0),
                    "active": int(user_counts["active"] or 0),
                    "deactivated": int(user_counts["deactivated"] or 0),
                    "staff": int(user_counts["staff"] or 0),
                    "superuser": int(user_counts["superuser"] or 0),
                    "new_7d": int(user_counts["new_7d"] or 0),
                },
                "engagement": {
                    "predictions_total": int(prediction_counts["total"] or 0),
                    "predictions_open": int(prediction_counts["open"] or 0),
                    "predictions_resolved": int(prediction_counts["resolved"] or 0),
                    "predictions_canceled": int(prediction_counts["canceled"] or 0),
                    "predictions_7d": int(prediction_counts["created_7d"] or 0),
                    "comments_total": int(comment_counts["total"] or 0),
                    "comments_visible": int(comment_counts["visible"] or 0),
                    "comments_hidden": int(comment_counts["hidden"] or 0),
                },
                "wallet": {
                    "available_gtl": int(wallet_counts["available_gtl"] or 0),
                    "locked_gtl": int(wallet_counts["locked_gtl"] or 0),
                },
                "badges": {
                    "active_catalog": int(badge_counts["active_catalog"] or 0),
                    "awarded": int(badge_counts["awarded"] or 0),
                },
                "system": {
                    "logs_error_7d": log_counts.get("error", 0),
                    "logs_warning_7d": log_counts.get("warning", 0),
                    "logs_critical_7d": log_counts.get("critical", 0),
                    "admin_events_7d": admin_events_7d,
                    "maintenance_enabled": _maintenance_mode_active(),
                    "smtp_status": smtp_status,
                    "recaptcha_enabled": os.environ.get("RECAPTCHA_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"},
                    **daemon_status,
                    "ai": ai_health,
                },
                "top_markets": top_markets,
                "recent_admin_events": recent_admin_events,
            }


def _admin_ai_agent_response(cursor, row, now=None):
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(hours=24)
    cursor.execute(
        """
        SELECT action_type, status, COUNT(*) AS total
        FROM gotrendlabs_ai_agent_actions
        WHERE agent_id = %s
          AND created_at >= %s
        GROUP BY action_type, status
        """,
        (row["id"], since),
    )
    counts = {(item["action_type"], item["status"]): int(item["total"] or 0) for item in cursor.fetchall()}
    return {
        "id": row["id"],
        "name": row["name"],
        "agent_type": row["agent_type"],
        "is_active": bool(row["is_active"]),
        "user_id": row["user_id"],
        "user_handle": _handle_seed(row["username"]),
        "user_display_name": row["first_name"] or _handle_seed(row["username"]),
        "user_is_bot": bool(row["is_bot"]),
        "personality_prompt": row["personality_prompt"] or "",
        "comment_style": row["comment_style"] or "",
        "max_comments_per_day": row["max_comments_per_day"],
        "max_predictions_per_day": row["max_predictions_per_day"],
        "max_stake_gtl": row["max_stake_gtl"],
        "cooldown_hours": row["cooldown_hours"],
        "min_humans_for_prediction": row["min_humans_for_prediction"],
        "last_action_at": row["last_action_at"].isoformat() if row["last_action_at"] else None,
        "last_error": row["last_error"] or "",
        "actions_24h": sum(counts.values()),
        "comments_24h": counts.get(("comment", "created"), 0),
        "predictions_24h": counts.get(("prediction", "created"), 0),
        "skipped_24h": counts.get(("comment", "skipped"), 0) + counts.get(("prediction", "skipped"), 0) + counts.get(("cycle", "skipped"), 0),
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def _admin_ai_agent_rows(cursor):
    cursor.execute(
        """
        SELECT a.*, u.username, u.first_name, u.is_bot
        FROM gotrendlabs_ai_agents a
        JOIN gotrendlabs_users u ON u.id = a.user_id
        ORDER BY a.agent_type ASC, a.name ASC, a.id ASC
        """
    )
    return [_admin_ai_agent_response(cursor, row) for row in cursor.fetchall()]


def _validate_ai_agent_payload(cursor, payload, agent_id=None):
    if payload.agent_type not in {"analyst", "liquidity", "contrarian"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Tipo de agente inválido.")
    cursor.execute("SELECT id, is_bot FROM gotrendlabs_users WHERE id = %s AND is_active = true", (payload.user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Usuário bot não encontrado.")
    if not user["is_bot"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Agente IA deve usar usuário marcado como bot.")
    cursor.execute("SELECT id FROM gotrendlabs_ai_agents WHERE user_id = %s", (payload.user_id,))
    existing = cursor.fetchone()
    if existing and existing["id"] != agent_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este usuário bot já está vinculado a outro agente IA.")


@app.get("/admin/ai-agents", response_model=AdminAiAgentListResponse)
def admin_list_ai_agents(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            return {"agents": _admin_ai_agent_rows(cursor), "health": ai_health_summary(cursor)}


@app.post("/admin/ai-agents", response_model=AdminAiAgentResponse, status_code=status.HTTP_201_CREATED)
def admin_create_ai_agent(payload: AdminAiAgentPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            _validate_ai_agent_payload(cursor, payload)
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                INSERT INTO gotrendlabs_ai_agents
                    (name, agent_type, user_id, is_active, personality_prompt, comment_style,
                     max_comments_per_day, max_predictions_per_day, max_stake_gtl, cooldown_hours,
                     min_humans_for_prediction, last_error, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '', %s, %s)
                RETURNING id
                """,
                (
                    payload.name.strip(),
                    payload.agent_type,
                    payload.user_id,
                    payload.is_active,
                    payload.personality_prompt.strip(),
                    payload.comment_style.strip(),
                    payload.max_comments_per_day,
                    payload.max_predictions_per_day,
                    payload.max_stake_gtl,
                    payload.cooldown_hours,
                    payload.min_humans_for_prediction,
                    now,
                    now,
                ),
            )
            agent_id = cursor.fetchone()["id"]
            _record_admin_event(cursor, staff["id"], "ai_agent.create", "ai_agent", str(agent_id), f"Agente IA criado: {payload.name.strip()}")
            cursor.execute(
                """
                SELECT a.*, u.username, u.first_name, u.is_bot
                FROM gotrendlabs_ai_agents a
                JOIN gotrendlabs_users u ON u.id = a.user_id
                WHERE a.id = %s
                """,
                (agent_id,),
            )
            return _admin_ai_agent_response(cursor, cursor.fetchone())


@app.get("/admin/ai-agents/{agent_id}", response_model=AdminAiAgentResponse)
def admin_get_ai_agent(agent_id: int, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            cursor.execute(
                """
                SELECT a.*, u.username, u.first_name, u.is_bot
                FROM gotrendlabs_ai_agents a
                JOIN gotrendlabs_users u ON u.id = a.user_id
                WHERE a.id = %s
                """,
                (agent_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agente IA não encontrado.")
            return _admin_ai_agent_response(cursor, row)


@app.patch("/admin/ai-agents/{agent_id}", response_model=AdminAiAgentResponse)
def admin_update_ai_agent(agent_id: int, payload: AdminAiAgentPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            _validate_ai_agent_payload(cursor, payload, agent_id=agent_id)
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                UPDATE gotrendlabs_ai_agents
                SET name = %s,
                    agent_type = %s,
                    user_id = %s,
                    is_active = %s,
                    personality_prompt = %s,
                    comment_style = %s,
                    max_comments_per_day = %s,
                    max_predictions_per_day = %s,
                    max_stake_gtl = %s,
                    cooldown_hours = %s,
                    min_humans_for_prediction = %s,
                    updated_at = %s
                WHERE id = %s
                RETURNING id
                """,
                (
                    payload.name.strip(),
                    payload.agent_type,
                    payload.user_id,
                    payload.is_active,
                    payload.personality_prompt.strip(),
                    payload.comment_style.strip(),
                    payload.max_comments_per_day,
                    payload.max_predictions_per_day,
                    payload.max_stake_gtl,
                    payload.cooldown_hours,
                    payload.min_humans_for_prediction,
                    now,
                    agent_id,
                ),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agente IA não encontrado.")
            _record_admin_event(cursor, staff["id"], "ai_agent.update", "ai_agent", str(agent_id), f"Agente IA atualizado: {payload.name.strip()}")
            cursor.execute(
                """
                SELECT a.*, u.username, u.first_name, u.is_bot
                FROM gotrendlabs_ai_agents a
                JOIN gotrendlabs_users u ON u.id = a.user_id
                WHERE a.id = %s
                """,
                (agent_id,),
            )
            return _admin_ai_agent_response(cursor, cursor.fetchone())


def _admin_ai_action_response(row):
    return {
        "id": row["id"],
        "agent_id": row["agent_id"],
        "agent_name": row["agent_name"] or "",
        "market_id": row["market_id"],
        "market_slug": row["market_slug"] or "",
        "market_title": row["market_title"] or "",
        "action_type": row["action_type"],
        "status": row["status"],
        "reason": row["reason"] or "",
        "payload_summary": row["payload_summary"] or {},
        "prompt_template_version": row["prompt_template_version"] or "",
        "prompt_hash": row["prompt_hash"] or "",
        "comment_id": row["comment_id"],
        "prediction_id": row["prediction_id"],
        "created_at": row["created_at"].isoformat(),
    }


@app.get("/admin/ai-agent-actions", response_model=AdminAiAgentActionListResponse)
def admin_list_ai_agent_actions(
    agent_id: Optional[int] = Query(default=None),
    market_slug: str = Query(default=""),
    action_type: str = Query(default=""),
    action_status: str = Query(default="", alias="status"),
    reason: str = Query(default=""),
    authorization: str = Header(default=""),
):
    where = []
    params = []
    if agent_id:
        where.append("act.agent_id = %s")
        params.append(agent_id)
    if market_slug:
        where.append("m.slug = %s")
        params.append(market_slug)
    if action_type:
        where.append("act.action_type = %s")
        params.append(action_type)
    if action_status:
        where.append("act.status = %s")
        params.append(action_status)
    if reason:
        where.append("act.reason ILIKE %s")
        params.append(f"%{reason}%")
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            cursor.execute(
                f"""
                SELECT act.*, a.name AS agent_name, m.slug AS market_slug, m.title AS market_title
                FROM gotrendlabs_ai_agent_actions act
                LEFT JOIN gotrendlabs_ai_agents a ON a.id = act.agent_id
                LEFT JOIN gotrendlabs_markets m ON m.id = act.market_id
                {where_sql}
                ORDER BY act.created_at DESC, act.id DESC
                LIMIT 100
                """,
                params,
            )
            return {"actions": [_admin_ai_action_response(row) for row in cursor.fetchall()], "health": ai_health_summary(cursor)}


@app.get("/admin/ai-agent-actions/{action_id}", response_model=AdminAiAgentActionResponse)
def admin_get_ai_agent_action(action_id: int, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            cursor.execute(
                """
                SELECT act.*, a.name AS agent_name, m.slug AS market_slug, m.title AS market_title
                FROM gotrendlabs_ai_agent_actions act
                LEFT JOIN gotrendlabs_ai_agents a ON a.id = act.agent_id
                LEFT JOIN gotrendlabs_markets m ON m.id = act.market_id
                WHERE act.id = %s
                """,
                (action_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ação IA não encontrada.")
            return _admin_ai_action_response(row)


@app.get("/admin/users", response_model=AdminUserListResponse)
def admin_list_users(
    q: str = Query(default=""),
    status_filter: str = Query(default="", alias="status"),
    role: str = Query(default=""),
    bot: str = Query(default=""),
    order: str = Query(default="created_desc"),
    authorization: str = Header(default=""),
):
    order_map = {
        "created_desc": "u.date_joined DESC, u.id DESC",
        "created_asc": "u.date_joined ASC, u.id ASC",
        "last_login_desc": "u.last_login DESC NULLS LAST, u.id DESC",
        "last_login_asc": "u.last_login ASC NULLS LAST, u.id ASC",
        "wallet_desc": "COALESCE(w.available_gtl, 0) DESC, u.id DESC",
        "reputation_desc": "COALESCE(r.reputation_score, 0) DESC, u.id DESC",
    }
    where = []
    params = []
    search = (q or "").strip()
    if search:
        where.append("(lower(u.email) LIKE lower(%s) OR lower(u.username) LIKE lower(%s) OR lower(u.first_name) LIKE lower(%s) OR lower(p.display_name) LIKE lower(%s))")
        like = f"%{search}%"
        params.extend([like, like, like, like])
    if status_filter in {"active", "deactivated"}:
        where.append("u.account_status = %s")
        params.append(status_filter)
    if role == "staff":
        where.append("u.is_staff = true AND u.is_superuser = false")
    elif role == "superuser":
        where.append("u.is_superuser = true")
    elif role == "user":
        where.append("u.is_staff = false AND u.is_superuser = false")
    if bot == "yes":
        where.append("u.is_bot = true")
    elif bot == "no":
        where.append("u.is_bot = false")
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            cursor.execute(
                f"""
                SELECT u.id, u.username, u.email, u.first_name, u.preferred_language,
                       u.date_joined, u.last_login, u.account_status, u.is_active,
                       u.is_staff, u.is_superuser, u.is_bot, u.deactivated_at,
                       p.display_name AS profile_display_name,
                       COALESCE(w.available_gtl, 0) AS available_gtl,
                       COALESCE(w.locked_gtl, 0) AS locked_gtl,
                       COALESCE(r.reputation_score, 0) AS reputation_score
                FROM gotrendlabs_users u
                LEFT JOIN gotrendlabs_user_profiles p ON p.user_id = u.id
                LEFT JOIN gotrendlabs_wallet_balances w ON w.user_id = u.id
                LEFT JOIN gotrendlabs_user_reputations r ON r.user_id = u.id
                {where_sql}
                ORDER BY {order_map.get(order, order_map['created_desc'])}
                LIMIT 100
                """,
                params,
            )
            users = [_admin_user_response(row) for row in cursor.fetchall()]
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(CASE WHEN account_status = 'active' THEN 1 ELSE 0 END), 0) AS active,
                    COALESCE(SUM(CASE WHEN account_status = 'deactivated' THEN 1 ELSE 0 END), 0) AS deactivated,
                    COALESCE(SUM(CASE WHEN is_staff = true AND is_superuser = false THEN 1 ELSE 0 END), 0) AS staff,
                    COALESCE(SUM(CASE WHEN is_superuser = true THEN 1 ELSE 0 END), 0) AS superuser,
                    COALESCE(SUM(CASE WHEN is_bot = true THEN 1 ELSE 0 END), 0) AS bots,
                    COALESCE(SUM(CASE WHEN is_staff = false AND is_superuser = false THEN 1 ELSE 0 END), 0) AS users
                FROM gotrendlabs_users
                """
            )
            counts = cursor.fetchone()
            return {
                "users": users,
                "counts": {
                    "total": int(counts["total"] or 0),
                    "active": int(counts["active"] or 0),
                    "deactivated": int(counts["deactivated"] or 0),
                    "staff": int(counts["staff"] or 0),
                    "superuser": int(counts["superuser"] or 0),
                    "bots": int(counts["bots"] or 0),
                    "users": int(counts["users"] or 0),
                },
            }


@app.get("/admin/users/{user_id}", response_model=AdminUserDetailResponse)
def admin_get_user(user_id: int, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            return _admin_user_detail(cursor, user_id)


@app.post("/admin/users/{user_id}/deactivate", response_model=AdminUserDetailResponse)
def admin_deactivate_user(user_id: int, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    note = (payload.note or "").strip()
    if not note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nota operacional é obrigatória.")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            target = _admin_user_row(cursor, user_id)
            _require_admin_target(staff, target)
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                UPDATE gotrendlabs_users
                SET account_status = 'deactivated',
                    is_active = false,
                    deactivated_at = %s
                WHERE id = %s
                """,
                (now, user_id),
            )
            cursor.execute(
                """
                UPDATE gotrendlabs_auth_sessions
                SET revoked_at = %s
                WHERE user_id = %s AND revoked_at IS NULL
                """,
                (now, user_id),
            )
            _record_admin_event(cursor, staff["id"], "user.deactivate", "user", str(user_id), note)
            return _admin_user_detail(cursor, user_id)


@app.post("/admin/users/{user_id}/reactivate", response_model=AdminUserDetailResponse)
def admin_reactivate_user(user_id: int, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    note = (payload.note or "").strip()
    if not note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nota operacional é obrigatória.")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            target = _admin_user_row(cursor, user_id)
            _require_admin_target(staff, target, allow_superuser=True)
            cursor.execute(
                """
                UPDATE gotrendlabs_users
                SET account_status = 'active',
                    is_active = true,
                    deactivated_at = NULL
                WHERE id = %s
                """,
                (user_id,),
            )
            _record_admin_event(cursor, staff["id"], "user.reactivate", "user", str(user_id), note)
            return _admin_user_detail(cursor, user_id)


@app.post("/admin/users/{user_id}/sessions/revoke", response_model=AdminUserDetailResponse)
def admin_revoke_user_sessions(user_id: int, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    note = (payload.note or "").strip()
    if not note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nota operacional é obrigatória.")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            target = _admin_user_row(cursor, user_id)
            _require_admin_target(staff, target, allow_superuser=True)
            cursor.execute(
                """
                UPDATE gotrendlabs_auth_sessions
                SET revoked_at = %s
                WHERE user_id = %s AND revoked_at IS NULL
                """,
                (datetime.now(timezone.utc), user_id),
            )
            _record_admin_event(cursor, staff["id"], "user.sessions_revoke", "user", str(user_id), note)
            return _admin_user_detail(cursor, user_id)


@app.post("/admin/users/{user_id}/wallet/adjust", response_model=AdminUserDetailResponse)
def admin_adjust_user_wallet(user_id: int, payload: AdminUserWalletAdjustmentPayload, authorization: str = Header(default="")):
    note = payload.note.strip()
    if not note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nota operacional é obrigatória.")
    if payload.direction not in {"credit", "debit"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Direção de ajuste inválida.")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            target = _admin_user_row(cursor, user_id)
            _require_admin_target(staff, target, allow_superuser=True, allow_self=True)
            wallet = _wallet_summary(cursor, user_id)
            if payload.direction == "debit" and wallet["available_gtl"] < payload.amount_gtl:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Saldo disponível insuficiente para débito manual.")
            _record_wallet_entry(
                cursor,
                user_id,
                entry_type="manual_adjustment",
                amount=payload.amount_gtl,
                direction=payload.direction,
                description=note,
                reference_type="admin_user_adjustment",
                reference_id=str(user_id),
                created_by_id=staff["id"],
            )
            _record_admin_event(cursor, staff["id"], "user.wallet_adjust", "user", str(user_id), note)
            return _admin_user_detail(cursor, user_id)


@app.post("/admin/users/{user_id}/roles", response_model=AdminUserDetailResponse)
def admin_update_user_roles(user_id: int, payload: AdminUserRolePayload, authorization: str = Header(default="")):
    note = payload.note.strip()
    if not note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nota operacional é obrigatória.")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            _require_superuser(staff)
            target = _admin_user_row(cursor, user_id)
            _require_admin_target(staff, target, allow_superuser=True)
            is_superuser = bool(payload.is_superuser)
            is_staff = bool(payload.is_staff) or is_superuser
            if target["is_superuser"] and not is_superuser:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM gotrendlabs_users
                    WHERE is_superuser = true
                      AND is_active = true
                      AND account_status = 'active'
                      AND id <> %s
                    """,
                    (user_id,),
                )
                if int(cursor.fetchone()["total"] or 0) == 0:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Não é possível remover o último superusuário ativo.")
            cursor.execute(
                """
                UPDATE gotrendlabs_users
                SET is_staff = %s,
                    is_superuser = %s
                WHERE id = %s
                """,
                (is_staff, is_superuser, user_id),
            )
            role_label = "superuser" if is_superuser else "staff" if is_staff else "user"
            _record_admin_event(cursor, staff["id"], "user.roles_update", "user", str(user_id), f"{note} | role={role_label}")
            return _admin_user_detail(cursor, user_id)


@app.post("/admin/users/{user_id}/bot", response_model=AdminUserDetailResponse)
def admin_update_user_bot(user_id: int, payload: AdminUserBotPayload, authorization: str = Header(default="")):
    note = payload.note.strip()
    if not note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nota operacional é obrigatória.")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            target = _admin_user_row(cursor, user_id)
            _require_admin_target(staff, target, allow_superuser=True)
            cursor.execute("UPDATE gotrendlabs_users SET is_bot = %s WHERE id = %s", (bool(payload.is_bot), user_id))
            label = "bot" if payload.is_bot else "human"
            _record_admin_event(cursor, staff["id"], "user.bot_update", "user", str(user_id), f"{note} | bot={label}")
            return _admin_user_detail(cursor, user_id)


@app.post("/admin/users/{user_id}/password-reset", response_model=AdminUserPasswordResetResponse)
def admin_request_user_password_reset(user_id: int, payload: AdminUserPasswordResetPayload, request: Request, authorization: str = Header(default="")):
    note = payload.note.strip()
    if not note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nota operacional é obrigatória.")
    ip_address, user_agent = _client_meta(request)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            target = _admin_user_row(cursor, user_id)
            _require_admin_target(staff, target, allow_superuser=True)
            if (target["is_staff"] or target["is_superuser"]) and not staff["is_superuser"]:
                _require_superuser(staff)
            if not target["is_active"] or target["account_status"] != "active":
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Reset de senha exige conta ativa.")
            reset_url = _issue_password_reset(cursor, target, ip_address=ip_address, user_agent=user_agent)
            _record_event(cursor, "password_reset_requested", user_id=target["id"], email=target["email"], ip_address=ip_address, user_agent=user_agent)
            _record_admin_event(cursor, staff["id"], "user.password_reset_request", "user", str(user_id), note)
            return {"message": PASSWORD_RESET_MESSAGE, "reset_url": reset_url}


@app.get("/admin/comments", response_model=CommentListResponse)
def admin_list_comments(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    market_slug: Optional[str] = Query(default=None, alias="market"),
    authorization: str = Header(default=""),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            if status_filter and status_filter not in {"visible", "hidden"}:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Status de comentário inválido.")
            comments = _market_comments(cursor, slug=market_slug, visible_only=False)
            if status_filter:
                comments = [comment for comment in comments if comment["status"] == status_filter]
            return {"comments": comments}


@app.patch("/admin/comments/{comment_id}/moderation", response_model=CommentResponse)
def admin_moderate_comment(comment_id: int, payload: CommentModerationPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            if payload.status not in {"visible", "hidden"}:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Status de comentário inválido.")
            cursor.execute(
                """
                SELECT mc.id, mc.market_id
                FROM gotrendlabs_market_comments mc
                WHERE mc.id = %s
                """,
                (comment_id,),
            )
            comment = cursor.fetchone()
            if not comment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado.")
            note = payload.note.strip() or ("Oculto pelo Admin Ops." if payload.status == "hidden" else "Restaurado pelo Admin Ops.")
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                UPDATE gotrendlabs_market_comments
                SET status = %s,
                    moderation_note = %s,
                    moderated_by_id = %s,
                    moderated_at = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (payload.status, note, staff["id"], now, now, comment_id),
            )
            _record_admin_event(
                cursor,
                staff["id"],
                "comment.hide" if payload.status == "hidden" else "comment.restore",
                "market_comment",
                str(comment_id),
                note,
            )
            return next(
                item
                for item in _market_comments(cursor, comment["market_id"], visible_only=False)
                if item["id"] == comment_id
            )


@app.get("/admin/markets", response_model=AdminMarketListResponse)
def admin_list_markets(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    q: str = Query(default=""),
    order: str = "display",
    authorization: str = Header(default=""),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            params = []
            where = []
            if status_filter:
                where.append("lower(m.status) = lower(%s)")
                params.append(status_filter)
            if q:
                where.append("(m.title ILIKE %s OR m.slug ILIKE %s OR m.summary ILIKE %s)")
                pattern = f"%{q.strip()}%"
                params.extend([pattern, pattern, pattern])
            where_sql = f"WHERE {' AND '.join(where)}" if where else ""
            order_sql = {
                "resolution_asc": "m.resolved_at ASC NULLS LAST, m.display_order ASC, m.id ASC",
                "resolution_desc": "m.resolved_at DESC NULLS LAST, m.display_order ASC, m.id ASC",
                "created_asc": "m.created_at ASC, m.id ASC",
                "created_desc": "m.created_at DESC, m.id DESC",
                "views_desc": "m.view_count DESC, m.share_count DESC, m.display_order ASC, m.id ASC",
                "shares_desc": "m.share_count DESC, m.view_count DESC, m.display_order ASC, m.id ASC",
            }.get(order, "m.display_order ASC, m.id ASC")
            rows = _market_rows(cursor, where_sql, params, order_sql)
            cursor.execute("SELECT status, COUNT(*) AS total FROM gotrendlabs_markets GROUP BY status")
            counts = {row["status"]: row["total"] for row in cursor.fetchall()}
            return {
                "markets": [_market_response(cursor, row, include_comments=False, filter_public_image=False) for row in rows],
                "counts": counts,
            }


@app.get("/admin/markets/{slug}/participants", response_model=AdminMarketParticipantListResponse)
def admin_get_market_participants(slug: str, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            market = _admin_market_by_slug(cursor, slug)
            public_metrics = market_public_metrics(cursor, market["id"])
            cursor.execute(
                """
                SELECT p.id AS prediction_id, p.user_id, u.username AS handle, u.first_name AS display_name,
                       u.is_bot, o.label AS option_label, p.stake_amount, p.probability_at_entry,
                       p.potential_payout, p.status, p.won, p.created_at
                FROM gotrendlabs_predictions p
                JOIN gotrendlabs_users u ON u.id = p.user_id
                JOIN gotrendlabs_market_options o ON o.id = p.market_option_id
                WHERE p.market_id = %s
                ORDER BY u.is_bot ASC, p.created_at ASC, p.id ASC
                """,
                (market["id"],),
            )
            participants = [
                {
                    "prediction_id": row["prediction_id"],
                    "user_id": row["user_id"],
                    "handle": _handle_seed(row["handle"]),
                    "display_name": row["display_name"] or _handle_seed(row["handle"]),
                    "is_bot": bool(row["is_bot"]),
                    "badge_label": "IA oficial" if row["is_bot"] else "",
                    "option_label": row["option_label"],
                    "stake_amount": int(row["stake_amount"] or 0),
                    "probability_at_entry": float(row["probability_at_entry"] or 0),
                    "potential_payout": int(row["potential_payout"] or 0),
                    "status": row["status"],
                    "won": row["won"],
                    "created_at": row["created_at"].isoformat(),
                }
                for row in cursor.fetchall()
            ]
            return {
                "market": {"slug": market["slug"], "title": market["title"], "status": market["status"]},
                "summary": {
                    **public_metrics,
                    "participants_total": len(participants),
                    "human_predictions": sum(1 for row in participants if not row["is_bot"]),
                    "bot_predictions": sum(1 for row in participants if row["is_bot"]),
                },
                "participants": participants,
            }


@app.post("/admin/markets", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
def admin_create_market(payload: AdminMarketPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            category = _upsert_category(cursor, payload.category)
            subcategory = _upsert_subcategory(cursor, category["id"], payload.subcategory)
            event = _upsert_event(cursor, subcategory["id"], payload.event)
            _ensure_taxonomy_available(category, subcategory, event)
            slug = _slug_seed(payload.slug or payload.title)
            cursor.execute("SELECT id FROM gotrendlabs_markets WHERE slug = %s", (slug,))
            if cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug de mercado já está em uso.")
            options = _normalize_market_options(payload)
            _validate_admin_market_payload(payload)
            _ensure_featured_allowed("draft", payload.is_featured)
            primary = payload.primary_outcome or (options[0]["label"] if options else "")
            primary_probability_exact = _decimal_probability(payload.primary_probability_exact or (options[0]["probability_exact"] if options else 0))
            secondary_probability_exact = _decimal_probability(payload.secondary_probability_exact or (options[1]["probability_exact"] if len(options) > 1 else 0))
            _sync_featured_market(cursor, None, payload.is_featured)
            cursor.execute(
                """
                INSERT INTO gotrendlabs_markets
                    (category_id, subcategory_id, event_id, slug, title, summary, kind, status, status_label,
                     primary_outcome, primary_probability_exact, secondary_probability_exact, volume_gtl, participants,
                     source, closes_in, close_label, thumb, thumb_color, image_url, resolution_criteria,
                     close_at, close_timezone, auto_close_enabled, is_featured,
                     resolution_type, resolution_timezone, resolution_note, admin_notes, created_by_id, updated_by_id,
                     view_count, share_count, display_order, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        0, 0, (SELECT COALESCE(MAX(display_order), 0) + 1 FROM gotrendlabs_markets), %s, %s)
                RETURNING id
                """,
                (
                    category["id"],
                    subcategory["id"],
                    event["id"],
                    slug,
                    payload.title.strip(),
                    payload.summary.strip(),
                    payload.kind,
                    payload.status_label or "Rascunho",
                    primary,
                    primary_probability_exact,
                    secondary_probability_exact,
                    payload.volume_gtl,
                    payload.participants,
                    payload.source.strip(),
                    _payload_closes_in(payload),
                    payload.close_label,
                    payload.thumb,
                    payload.thumb_color,
                    payload.image_url,
                    payload.resolution_criteria.strip(),
                    payload.close_at,
                    payload.close_timezone,
                    payload.auto_close_enabled,
                    payload.is_featured,
                    payload.resolution_type,
                    "",
                    payload.resolution_note,
                    payload.admin_notes,
                    staff["id"],
                    staff["id"],
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                ),
            )
            market_id = cursor.fetchone()["id"]
            _save_market_options(cursor, market_id, options)
            _record_admin_event(cursor, staff["id"], "market.create", "market", slug, payload.admin_notes)
            return _market_response(cursor, _admin_market_by_slug(cursor, slug), filter_public_image=False)


@app.get("/admin/markets/{slug}", response_model=MarketResponse)
def admin_get_market(slug: str, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            return _market_response(cursor, _admin_market_by_slug(cursor, slug), filter_public_image=False)


@app.patch("/admin/markets/{slug}", response_model=MarketResponse)
def admin_update_market(slug: str, payload: AdminMarketPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            row = _admin_market_by_slug(cursor, slug)
            if row["status"] == "resolved":
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Mercados resolvidos não podem ser alterados. Desfaça a resolução antes de editar.")
            category = _upsert_category(cursor, payload.category)
            subcategory = _upsert_subcategory(cursor, category["id"], payload.subcategory)
            event = _upsert_event(cursor, subcategory["id"], payload.event)
            _ensure_taxonomy_available(category, subcategory, event)
            new_slug = _slug_seed(payload.slug or slug)
            if new_slug != slug:
                cursor.execute("SELECT id FROM gotrendlabs_markets WHERE slug = %s AND id <> %s", (new_slug, row["id"]))
                if cursor.fetchone():
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug de mercado já está em uso.")
            options = _normalize_market_options(payload)
            _validate_admin_market_payload(payload)
            _ensure_featured_allowed(row["status"], payload.is_featured)
            cursor.execute("SELECT COUNT(*) AS total FROM gotrendlabs_predictions WHERE market_id = %s", (row["id"],))
            has_predictions = bool(cursor.fetchone()["total"])
            preserve_operational_fields = row["status"] != "draft" or has_predictions
            if preserve_operational_fields:
                status_label = row["status_label"]
                primary = row["primary_outcome"]
                primary_probability_exact = _decimal_probability(row["primary_probability_exact"])
                secondary_probability_exact = _decimal_probability(row["secondary_probability_exact"])
                volume_gtl = row["volume_gtl"]
                participants = row["participants"]
                resolution_type = row["resolution_type"] or ""
                resolution_note = row["resolution_note"] or ""
            else:
                status_label = payload.status_label or row["status_label"]
                primary = payload.primary_outcome or (options[0]["label"] if options else "")
                primary_probability_exact = _decimal_probability(payload.primary_probability_exact or (options[0]["probability_exact"] if options else 0))
                secondary_probability_exact = _decimal_probability(payload.secondary_probability_exact or (options[1]["probability_exact"] if len(options) > 1 else 0))
                volume_gtl = payload.volume_gtl
                participants = payload.participants
                resolution_type = payload.resolution_type
                resolution_note = payload.resolution_note
            _sync_featured_market(cursor, row["id"], payload.is_featured)
            cursor.execute(
                """
                UPDATE gotrendlabs_markets
                SET category_id = %s,
                    subcategory_id = %s,
                    event_id = %s,
                    slug = %s,
                    title = %s,
                    summary = %s,
                    kind = %s,
                    status_label = %s,
                    primary_outcome = %s,
                    primary_probability_exact = %s,
                    secondary_probability_exact = %s,
                    volume_gtl = %s,
                    participants = %s,
                    source = %s,
                    closes_in = %s,
                    close_label = %s,
                    thumb = %s,
                    thumb_color = %s,
                    image_url = %s,
                    resolution_criteria = %s,
                    close_at = %s,
                    close_timezone = %s,
                    auto_close_enabled = %s,
                    is_featured = %s,
                    resolution_type = %s,
                    resolution_note = %s,
                    admin_notes = %s,
                    updated_by_id = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (
                    category["id"],
                    subcategory["id"],
                    event["id"],
                    new_slug,
                    payload.title.strip(),
                    payload.summary.strip(),
                    payload.kind,
                    status_label,
                    primary,
                    primary_probability_exact,
                    secondary_probability_exact,
                    volume_gtl,
                    participants,
                    payload.source.strip(),
                    _payload_closes_in(payload),
                    payload.close_label,
                    payload.thumb,
                    payload.thumb_color,
                    payload.image_url,
                    payload.resolution_criteria.strip(),
                    payload.close_at,
                    payload.close_timezone,
                    payload.auto_close_enabled,
                    payload.is_featured,
                    resolution_type,
                    resolution_note,
                    payload.admin_notes,
                    staff["id"],
                    datetime.now(timezone.utc),
                    row["id"],
                ),
            )
            _save_market_options(cursor, row["id"], options, preserve_existing_probability=preserve_operational_fields)
            _record_admin_event(cursor, staff["id"], "market.update", "market", new_slug, payload.admin_notes)
            return _market_response(cursor, _admin_market_by_slug(cursor, new_slug), filter_public_image=False)


@app.post("/admin/markets/{slug}/publish", response_model=MarketResponse)
def admin_publish_market(slug: str, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            row = _admin_market_by_slug(cursor, slug)
            _market_lifecycle_engine(cursor, staff["id"]).publish_market(row, slug, payload.note)
            return _market_response(cursor, _admin_market_by_slug(cursor, slug), filter_public_image=False)


@app.post("/admin/markets/{slug}/cancel", response_model=MarketResponse)
def admin_cancel_market(slug: str, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            row = _admin_market_by_slug(cursor, slug)
            _market_lifecycle_engine(cursor, staff["id"]).cancel_market(row, slug, payload.note)
            return _market_response(cursor, _admin_market_by_slug(cursor, slug), filter_public_image=False)


@app.post("/admin/markets/{slug}/resolve", response_model=MarketResponse)
def admin_resolve_market(slug: str, payload: AdminMarketResolvePayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            row = _admin_market_by_slug(cursor, slug)
            _market_lifecycle_engine(cursor, staff["id"]).resolve_market(row, slug, payload)
            return _market_response(cursor, _admin_market_by_slug(cursor, slug), filter_public_image=False)


@app.get("/admin/markets/{slug}/resolution-audit", response_model=AdminMarketResolutionAuditResponse)
def admin_get_market_resolution_audit(
    slug: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    authorization: str = Header(default=""),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            cursor.execute(
                """
                SELECT m.id, m.slug, m.title, m.status, m.winning_option_id, m.resolved_at,
                       m.resolution_timezone, m.resolution_note, m.source,
                       o.label AS winning_option_label
                FROM gotrendlabs_markets m
                LEFT JOIN gotrendlabs_market_options o ON o.id = m.winning_option_id
                WHERE m.slug = %s
                """,
                (slug,),
            )
            market = cursor.fetchone()
            if not market:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mercado não encontrado.")
            if market["status"] != "resolved":
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Auditoria disponível apenas para mercados resolvidos.")

            reason_pattern = f"%market_resolved:{market['id']}%"
            cursor.execute(
                """
                SELECT COUNT(*) AS predictions_total,
                       COALESCE(SUM(CASE WHEN won IS TRUE THEN 1 ELSE 0 END), 0) AS winners_total,
                       COALESCE(SUM(CASE WHEN won IS FALSE THEN 1 ELSE 0 END), 0) AS losers_total,
                       COALESCE(SUM(stake_amount), 0) AS stake_total
                FROM gotrendlabs_predictions
                WHERE market_id = %s
                """,
                (market["id"],),
            )
            prediction_totals = cursor.fetchone()
            cursor.execute(
                """
                SELECT COALESCE(SUM(CASE WHEN l.entry_type = 'prediction_refund' THEN l.amount ELSE 0 END), 0) AS refund_total,
                       COALESCE(SUM(CASE WHEN l.entry_type = 'prediction_payout' THEN l.amount ELSE 0 END), 0) AS payout_total,
                       COALESCE(SUM(CASE WHEN l.entry_type = 'prediction_loss' THEN l.amount ELSE 0 END), 0) AS loss_total
                FROM gotrendlabs_predictions p
                LEFT JOIN gotrendlabs_wallet_ledger l
                  ON l.reference_type = 'prediction'
                 AND l.reference_id = p.id::text
                 AND l.entry_type IN ('prediction_refund', 'prediction_payout', 'prediction_loss')
                WHERE p.market_id = %s
                """,
                (market["id"],),
            )
            ledger_totals = cursor.fetchone()
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM gotrendlabs_user_badge_awards a
                WHERE a.reason_snapshot LIKE %s
                  AND a.user_id IN (SELECT user_id FROM gotrendlabs_predictions WHERE market_id = %s)
                """,
                (reason_pattern, market["id"]),
            )
            badge_total = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS total FROM gotrendlabs_predictions WHERE market_id = %s", (market["id"],))
            participant_total = int(cursor.fetchone()["total"] or 0)
            cursor.execute(
                """
                WITH ledger_totals AS (
                    SELECT reference_id::bigint AS prediction_id,
                           COALESCE(SUM(CASE WHEN entry_type = 'prediction_refund' THEN amount ELSE 0 END), 0) AS prediction_refund,
                           COALESCE(SUM(CASE WHEN entry_type = 'prediction_payout' THEN amount ELSE 0 END), 0) AS prediction_payout,
                           COALESCE(SUM(CASE WHEN entry_type = 'prediction_loss' THEN amount ELSE 0 END), 0) AS prediction_loss
                    FROM gotrendlabs_wallet_ledger
                    WHERE reference_type = 'prediction'
                      AND reference_id ~ '^[0-9]+$'
                      AND entry_type IN ('prediction_refund', 'prediction_payout', 'prediction_loss')
                    GROUP BY reference_id::bigint
                )
                SELECT p.id AS prediction_id, p.user_id, u.username AS handle, u.first_name AS display_name,
                       o.label AS option_label, p.stake_amount, p.probability_at_entry,
                       p.potential_payout, p.won,
                       COALESCE(lt.prediction_refund, 0) AS prediction_refund,
                       COALESCE(lt.prediction_payout, 0) AS prediction_payout,
                       COALESCE(lt.prediction_loss, 0) AS prediction_loss
                FROM gotrendlabs_predictions p
                JOIN gotrendlabs_users u ON u.id = p.user_id
                JOIN gotrendlabs_market_options o ON o.id = p.market_option_id
                LEFT JOIN ledger_totals lt ON lt.prediction_id = p.id
                WHERE p.market_id = %s
                ORDER BY p.id ASC
                LIMIT %s OFFSET %s
                """,
                (market["id"], limit, offset),
            )
            participant_rows = cursor.fetchall()
            participant_user_ids = [row["user_id"] for row in participant_rows]
            badges_by_user = {user_id: [] for user_id in participant_user_ids}
            if participant_user_ids:
                cursor.execute(
                    """
                    SELECT a.user_id, b.code, b.name, a.awarded_at, a.reason_snapshot
                    FROM gotrendlabs_user_badge_awards a
                    JOIN gotrendlabs_badge_definitions b ON b.id = a.badge_id
                    WHERE a.reason_snapshot LIKE %s
                      AND a.user_id = ANY(%s)
                    ORDER BY a.awarded_at ASC, b.code ASC
                    """,
                    (reason_pattern, participant_user_ids),
                )
                for badge in cursor.fetchall():
                    badges_by_user.setdefault(badge["user_id"], []).append(
                        {
                            "code": badge["code"],
                            "name": badge["name"],
                            "awarded_at": badge["awarded_at"].isoformat(),
                            "reason_snapshot": badge["reason_snapshot"] or "",
                        }
                    )

            return {
                "market": {
                    "slug": market["slug"],
                    "title": market["title"],
                    "status": market["status"],
                    "winning_option_id": market["winning_option_id"],
                    "winning_option_label": market["winning_option_label"] or "",
                    "resolved_at": market["resolved_at"].isoformat() if market["resolved_at"] else None,
                    "resolved_at_label": _datetime_label(market["resolved_at"], market["resolution_timezone"]) if market["resolved_at"] else "",
                    "resolution_timezone": market["resolution_timezone"] or "",
                    "resolution_note": market["resolution_note"] or "",
                    "source": market["source"] or "",
                },
                "summary": {
                    "predictions_total": int(prediction_totals["predictions_total"] or 0),
                    "winners_total": int(prediction_totals["winners_total"] or 0),
                    "losers_total": int(prediction_totals["losers_total"] or 0),
                    "stake_total": int(prediction_totals["stake_total"] or 0),
                    "refund_total": int(ledger_totals["refund_total"] or 0),
                    "payout_total": int(ledger_totals["payout_total"] or 0),
                    "loss_total": int(ledger_totals["loss_total"] or 0),
                    "badge_awards_total": int(badge_total or 0),
                },
                "participants": [
                    {
                        "user_id": row["user_id"],
                        "handle": _handle_seed(row["handle"]),
                        "display_name": row["display_name"] or _handle_seed(row["handle"]),
                        "prediction_id": row["prediction_id"],
                        "option_label": row["option_label"],
                        "stake_amount": int(row["stake_amount"] or 0),
                        "probability_at_entry": float(row["probability_at_entry"] or 0),
                        "potential_payout": int(row["potential_payout"] or 0),
                        "won": row["won"],
                        "ledger": {
                            "prediction_refund": int(row["prediction_refund"] or 0),
                            "prediction_payout": int(row["prediction_payout"] or 0),
                            "prediction_loss": int(row["prediction_loss"] or 0),
                        },
                        "badges": badges_by_user.get(row["user_id"], []),
                    }
                    for row in participant_rows
                ],
                "pagination": {"limit": limit, "offset": offset, "total": participant_total},
            }


@app.post("/admin/markets/{slug}/lock", response_model=MarketResponse)
def admin_lock_market(slug: str, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            row = _admin_market_by_slug(cursor, slug)
            _market_lifecycle_engine(cursor, staff["id"]).lock_market(row, slug, payload.note)
            return _market_response(cursor, _admin_market_by_slug(cursor, slug), filter_public_image=False)


@app.get("/admin/queues", response_model=QueueListResponse)
def admin_list_queues(
    kind: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    severity: Optional[str] = None,
    order: str = "created_desc",
    authorization: str = Header(default=""),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            items = []
            if kind in {None, "", "suggestion"}:
                where = []
                params = []
                if status_filter:
                    where.append("s.status = %s")
                    params.append(status_filter)
                where_sql = "WHERE " + " AND ".join(where) if where else ""
                cursor.execute(
                    f"""
                    SELECT s.*, u.username AS author_handle, m.slug AS converted_market_slug
                    FROM gotrendlabs_market_suggestions s
                    LEFT JOIN gotrendlabs_users u ON u.id = s.author_id
                    LEFT JOIN gotrendlabs_markets m ON m.id = s.converted_market_id
                    {where_sql}
                    ORDER BY s.created_at ASC, s.id ASC
                    """,
                    params,
                )
                items.extend(_suggestion_response(row) for row in cursor.fetchall())
            if kind in {None, "", "feedback"}:
                where = []
                params = []
                if status_filter:
                    where.append("f.status = %s")
                    params.append(status_filter)
                if severity:
                    where.append("f.severity = %s")
                    params.append(severity)
                where_sql = "WHERE " + " AND ".join(where) if where else ""
                cursor.execute(
                    f"""
                    SELECT f.*, u.username AS author_handle
                    FROM gotrendlabs_product_feedback f
                    LEFT JOIN gotrendlabs_users u ON u.id = f.author_id
                    {where_sql}
                    ORDER BY f.created_at ASC, f.id ASC
                    """,
                    params,
                )
                items.extend(_feedback_response(row) for row in cursor.fetchall())
            if kind in {None, "", "wallet_recharge"}:
                where = []
                params = []
                if status_filter:
                    where.append("r.status = %s")
                    params.append(status_filter)
                where_sql = "WHERE " + " AND ".join(where) if where else ""
                cursor.execute(
                    f"""
                    SELECT r.*, u.username AS author_handle
                    FROM gotrendlabs_wallet_recharge_requests r
                    JOIN gotrendlabs_users u ON u.id = r.user_id
                    {where_sql}
                    ORDER BY r.created_at ASC, r.id ASC
                    """,
                    params,
                )
                items.extend(_wallet_recharge_response(row) for row in cursor.fetchall())
            reverse = order != "created_asc"
            items = sorted(items, key=lambda item: item["created_at"], reverse=reverse)
            cursor.execute("SELECT status, COUNT(*) AS total FROM gotrendlabs_market_suggestions GROUP BY status")
            suggestion_counts = {row["status"]: row["total"] for row in cursor.fetchall()}
            cursor.execute("SELECT status, COUNT(*) AS total FROM gotrendlabs_product_feedback GROUP BY status")
            feedback_counts = {row["status"]: row["total"] for row in cursor.fetchall()}
            cursor.execute("SELECT status, COUNT(*) AS total FROM gotrendlabs_wallet_recharge_requests GROUP BY status")
            recharge_counts = {row["status"]: row["total"] for row in cursor.fetchall()}
            return {"items": items, "counts": {"suggestion": suggestion_counts, "feedback": feedback_counts, "wallet_recharge": recharge_counts}}


@app.post("/admin/queues/{kind}/{item_id}/review", response_model=QueueItemResponse)
def admin_review_queue_item(kind: str, item_id: int, payload: QueueReviewPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            now = datetime.now(timezone.utc)
            if kind == "suggestion":
                if payload.status not in {"pending", "reviewed", "rejected"}:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Status inválido para sugestão.")
                _get_suggestion(cursor, item_id)
                cursor.execute(
                    """
                    UPDATE gotrendlabs_market_suggestions
                    SET status = %s, admin_note = %s, reviewed_by_id = %s, reviewed_at = %s, updated_at = %s
                    WHERE id = %s
                    """,
                    (payload.status, payload.note, staff["id"], now, now, item_id),
                )
                _record_admin_event(cursor, staff["id"], "suggestion.review", "market_suggestion", str(item_id), payload.note)
                suggestion = _get_suggestion(cursor, item_id)
                if suggestion["author_id"] and payload.status == "reviewed":
                    BadgeAwardEngine.on_suggestion_approved(cursor, suggestion["author_id"], suggestion_id=item_id)
                return _suggestion_response(suggestion)
            if kind == "feedback":
                if payload.status not in {"pending", "reviewed", "rejected"}:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Status inválido para feedback.")
                _get_feedback(cursor, item_id)
                cursor.execute(
                    """
                    UPDATE gotrendlabs_product_feedback
                    SET status = %s, admin_note = %s, reviewed_by_id = %s, reviewed_at = %s, updated_at = %s
                    WHERE id = %s
                    """,
                    (payload.status, payload.note, staff["id"], now, now, item_id),
                )
                _record_admin_event(cursor, staff["id"], "feedback.review", "product_feedback", str(item_id), payload.note)
                return _feedback_response(_get_feedback(cursor, item_id))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fila não encontrada.")


@app.post("/admin/queues/suggestions/{suggestion_id}/convert-draft", response_model=QueueItemResponse)
def admin_convert_suggestion_to_draft(suggestion_id: int, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            suggestion = _get_suggestion(cursor, suggestion_id)
            if suggestion["status"] == "converted":
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Sugestão já convertida.")
            category = _upsert_category(cursor, suggestion["category"])
            subcategory = _upsert_subcategory(cursor, category["id"], suggestion["subcategory"] or "Geral")
            event = _upsert_event(cursor, subcategory["id"], "Geral")
            _ensure_taxonomy_available(category, subcategory, event)
            now = datetime.now(timezone.utc)
            close_at = now + timedelta(days=30)
            slug = _unique_slug(cursor, "gotrendlabs_markets", suggestion["question"])
            options = _normalize_market_options(
                AdminMarketPayload(
                    title=suggestion["question"],
                    kind=suggestion["kind"],
                    category=suggestion["category"],
                    subcategory=suggestion["subcategory"] or "Geral",
                    event="Geral",
                    summary=suggestion["rationale"] or "Sugestão enviada por usuário para curadoria editorial.",
                    source=suggestion["suggested_source"],
                    resolution_criteria="A definir pela curadoria antes da publicação.",
                    close_at=close_at,
                    close_timezone="America/Sao_Paulo",
                    thumb_color="#d8ece2",
                    options=[{"label": "Opção A"}, {"label": "Opção B"}] if suggestion["kind"] == "multiple" else [],
                )
            )
            primary = options[0]["label"] if options else ""
            primary_probability_exact = _decimal_probability(options[0]["probability_exact"] if options else 0)
            secondary_probability_exact = _decimal_probability(options[1]["probability_exact"] if len(options) > 1 else 0)
            cursor.execute(
                """
                INSERT INTO gotrendlabs_markets
                    (category_id, subcategory_id, event_id, slug, title, summary, kind, status, status_label,
                     primary_outcome, primary_probability_exact, secondary_probability_exact, volume_gtl, participants,
                     source, closes_in, close_label, thumb, thumb_color, image_url, resolution_criteria,
                     close_at, close_timezone, auto_close_enabled, is_featured,
                     resolution_type, resolution_timezone, resolution_note, admin_notes, created_by_id, updated_by_id,
                     view_count, share_count, display_order, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft', 'Rascunho', %s, %s, %s, '0 GT₵', '0 usuários',
                        %s, %s, '', '', '#d8ece2', '', 'A definir pela curadoria antes da publicação.',
                        %s, 'America/Sao_Paulo', true, false, '', '', '', %s, %s, %s,
                        0, 0, (SELECT COALESCE(MAX(display_order), 0) + 1 FROM gotrendlabs_markets), %s, %s)
                RETURNING id
                """,
                (
                    category["id"],
                    subcategory["id"],
                    event["id"],
                    slug,
                    suggestion["question"],
                    suggestion["rationale"] or "Sugestão enviada por usuário para curadoria editorial.",
                    suggestion["kind"],
                    primary,
                    primary_probability_exact,
                    secondary_probability_exact,
                    suggestion["suggested_source"],
                    _short_close_label(close_at),
                    close_at,
                    payload.note,
                    staff["id"],
                    staff["id"],
                    now,
                    now,
                ),
            )
            market_id = cursor.fetchone()["id"]
            _save_market_options(cursor, market_id, options)
            cursor.execute(
                """
                UPDATE gotrendlabs_market_suggestions
                SET status = 'converted',
                    admin_note = %s,
                    converted_market_id = %s,
                    reviewed_by_id = %s,
                    reviewed_at = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (payload.note, market_id, staff["id"], now, now, suggestion_id),
            )
            _record_admin_event(cursor, staff["id"], "suggestion.convert_draft", "market_suggestion", str(suggestion_id), payload.note)
            _record_admin_event(cursor, staff["id"], "market.create", "market", slug, f"Rascunho criado a partir da sugestão {suggestion_id}.")
            return _suggestion_response(_get_suggestion(cursor, suggestion_id))


@app.post("/admin/queues/suggestions/{suggestion_id}/reward", response_model=QueueItemResponse)
def admin_reward_suggestion(suggestion_id: int, payload: SuggestionRewardPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            suggestion = _get_suggestion(cursor, suggestion_id)
            if not suggestion["author_id"]:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Sugestão sem usuário cadastrado não pode receber créditos.")
            if suggestion["reward_gtl"]:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Sugestão já recebeu créditos.")
            now = datetime.now(timezone.utc)
            _record_wallet_entry(
                cursor,
                suggestion["author_id"],
                entry_type="reward_suggestion",
                amount=payload.amount_gtl,
                direction="credit",
                description="Crédito por sugestão validada",
                reference_type="suggestion",
                reference_id=str(suggestion_id),
                created_by_id=staff["id"],
            )
            cursor.execute(
                """
                UPDATE gotrendlabs_market_suggestions
                SET status = 'rewarded',
                    admin_note = %s,
                    reward_gtl = %s,
                    reviewed_by_id = %s,
                    reviewed_at = %s,
                    rewarded_at = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (payload.note, payload.amount_gtl, staff["id"], now, now, now, suggestion_id),
            )
            _record_admin_event(cursor, staff["id"], "suggestion.reward", "market_suggestion", str(suggestion_id), payload.note)
            BadgeAwardEngine.on_suggestion_rewarded(cursor, suggestion["author_id"], suggestion_id=suggestion_id)
            return _suggestion_response(_get_suggestion(cursor, suggestion_id))


@app.post("/admin/queues/feedback/{feedback_id}/reward", response_model=QueueItemResponse)
def admin_reward_feedback(feedback_id: int, payload: FeedbackRewardPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            feedback = _get_feedback(cursor, feedback_id)
            if not feedback["author_id"]:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Feedback sem usuário não pode receber recompensa.")
            if feedback["status"] == "rewarded" or feedback["reward_gtl"]:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Feedback já recompensado.")
            now = datetime.now(timezone.utc)
            _record_wallet_entry(
                cursor,
                feedback["author_id"],
                entry_type="reward_feedback",
                amount=payload.amount_gtl,
                direction="credit",
                description="Recompensa por feedback validado",
                reference_type="feedback",
                reference_id=str(feedback_id),
                created_by_id=staff["id"],
            )
            cursor.execute(
                """
                UPDATE gotrendlabs_product_feedback
                SET status = 'rewarded',
                    admin_note = %s,
                    reward_gtl = %s,
                    reviewed_by_id = %s,
                    reviewed_at = %s,
                    rewarded_at = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (payload.note, payload.amount_gtl, staff["id"], now, now, now, feedback_id),
            )
            _record_admin_event(cursor, staff["id"], "feedback.reward", "product_feedback", str(feedback_id), payload.note)
            BadgeAwardEngine.on_feedback_rewarded(cursor, feedback["author_id"], feedback_id=feedback_id)
            return _feedback_response(_get_feedback(cursor, feedback_id))


@app.post("/admin/queues/wallet-recharges/{request_id}/approve", response_model=QueueItemResponse)
def admin_approve_wallet_recharge(request_id: int, payload: WalletRechargeApprovalPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            recharge = _get_wallet_recharge_request(cursor, request_id)
            if recharge["status"] != "pending":
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Solicitação de recarga já revisada.")
            now = datetime.now(timezone.utc)
            note = payload.note.strip() or "Recarga educativa aprovada pelo Admin Ops."
            _record_wallet_entry(
                cursor,
                recharge["user_id"],
                entry_type="educational_recharge",
                amount=payload.amount_gtl,
                direction="credit",
                description=note,
                reference_type="wallet_recharge_request",
                reference_id=str(request_id),
                created_by_id=staff["id"],
            )
            cursor.execute(
                """
                UPDATE gotrendlabs_wallet_recharge_requests
                SET status = 'approved',
                    amount_gtl = %s,
                    admin_note = %s,
                    reviewed_by_id = %s,
                    reviewed_at = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (payload.amount_gtl, note, staff["id"], now, now, request_id),
            )
            _record_admin_event(cursor, staff["id"], "wallet_recharge.approve", "wallet_recharge_request", str(request_id), note)
            return _wallet_recharge_response(_get_wallet_recharge_request(cursor, request_id))


@app.post("/admin/queues/wallet-recharges/{request_id}/reject", response_model=QueueItemResponse)
def admin_reject_wallet_recharge(request_id: int, payload: WalletRechargeRejectPayload, authorization: str = Header(default="")):
    note = payload.note.strip()
    if not note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nota operacional é obrigatória.")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            recharge = _get_wallet_recharge_request(cursor, request_id)
            if recharge["status"] != "pending":
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Solicitação de recarga já revisada.")
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                UPDATE gotrendlabs_wallet_recharge_requests
                SET status = 'rejected',
                    admin_note = %s,
                    reviewed_by_id = %s,
                    reviewed_at = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (note, staff["id"], now, now, request_id),
            )
            _record_admin_event(cursor, staff["id"], "wallet_recharge.reject", "wallet_recharge_request", str(request_id), note)
            return _wallet_recharge_response(_get_wallet_recharge_request(cursor, request_id))


@app.get("/admin/badges", response_model=AdminBadgeListResponse)
def admin_get_badges(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            return {"badges": _admin_badge_rows(cursor)}


@app.post("/admin/badges", response_model=AdminBadgeResponse, status_code=status.HTTP_201_CREATED)
def admin_create_badge(payload: AdminBadgePayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            badge_type, rule_type = _validate_badge_payload(payload)
            _validate_badge_taxonomy(cursor, payload)
            code = _slug_seed(payload.code or payload.name, max_length=80)
            cursor.execute("SELECT id FROM gotrendlabs_badge_definitions WHERE code = %s", (code,))
            if cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe badge com este código.")
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                INSERT INTO gotrendlabs_badge_definitions
                    (code, name, description, rule_description, badge_type, image_url, image_dark_url, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    code,
                    payload.name.strip(),
                    payload.description.strip(),
                    (payload.rule_description or payload.description).strip(),
                    badge_type,
                    payload.image_url.strip(),
                    payload.image_dark_url.strip(),
                    payload.is_active,
                    now,
                    now,
                ),
            )
            badge_id = cursor.fetchone()["id"]
            cursor.execute(
                """
                INSERT INTO gotrendlabs_badge_rules
                    (badge_id, rule_type, threshold_value, category, subcategory, event, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, true, %s, %s)
                """,
                (
                    badge_id,
                    rule_type,
                    _decimal_probability(payload.threshold_value),
                    payload.category.strip(),
                    payload.subcategory.strip(),
                    payload.event.strip(),
                    now,
                    now,
                ),
            )
            _record_admin_event(cursor, staff["id"], "badge.create", "badge", code, payload.rule_description)
            return _admin_badge_rows(cursor, "WHERE b.code = %s", [code])[0]


@app.patch("/admin/badges/{code}", response_model=AdminBadgeResponse)
def admin_update_badge(code: str, payload: AdminBadgePayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            badge_type, rule_type = _validate_badge_payload(payload)
            _validate_badge_taxonomy(cursor, payload)
            cursor.execute("SELECT id FROM gotrendlabs_badge_definitions WHERE code = %s", (code,))
            badge = cursor.fetchone()
            if not badge:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Badge não encontrada.")
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                UPDATE gotrendlabs_badge_definitions
                SET name = %s,
                    description = %s,
                    rule_description = %s,
                    badge_type = %s,
                    image_url = %s,
                    image_dark_url = %s,
                    is_active = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (
                    payload.name.strip(),
                    payload.description.strip(),
                    (payload.rule_description or payload.description).strip(),
                    badge_type,
                    payload.image_url.strip(),
                    payload.image_dark_url.strip(),
                    payload.is_active,
                    now,
                    badge["id"],
                ),
            )
            cursor.execute(
                """
                UPDATE gotrendlabs_badge_rules
                SET rule_type = %s,
                    threshold_value = %s,
                    category = %s,
                    subcategory = %s,
                    event = %s,
                    is_active = true,
                    updated_at = %s
                WHERE badge_id = %s
                """,
                (
                    rule_type,
                    _decimal_probability(payload.threshold_value),
                    payload.category.strip(),
                    payload.subcategory.strip(),
                    payload.event.strip(),
                    now,
                    badge["id"],
                ),
            )
            _record_admin_event(cursor, staff["id"], "badge.update", "badge", code, payload.rule_description)
            return _admin_badge_rows(cursor, "WHERE b.code = %s", [code])[0]


@app.post("/admin/badges/{code}/deactivate", response_model=AdminBadgeResponse)
def admin_deactivate_badge(code: str, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            cursor.execute("SELECT id FROM gotrendlabs_badge_definitions WHERE code = %s", (code,))
            badge = cursor.fetchone()
            if not badge:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Badge não encontrada.")
            now = datetime.now(timezone.utc)
            cursor.execute("UPDATE gotrendlabs_badge_definitions SET is_active = false, updated_at = %s WHERE id = %s", (now, badge["id"]))
            cursor.execute("UPDATE gotrendlabs_badge_rules SET is_active = false, updated_at = %s WHERE badge_id = %s", (now, badge["id"]))
            _record_admin_event(cursor, staff["id"], "badge.deactivate", "badge", code, payload.note)
            return _admin_badge_rows(cursor, "WHERE b.code = %s", [code])[0]


@app.get("/admin/taxonomy", response_model=AdminTaxonomyResponse)
def admin_get_taxonomy(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _current_staff_user(cursor, authorization)
            return _taxonomy_response(cursor)


@app.post("/admin/categories", response_model=AdminTaxonomyResponse, status_code=status.HTTP_201_CREATED)
def admin_create_category(payload: AdminCategoryPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            category = _upsert_category(cursor, payload.name, payload.slug, payload.notice)
            _record_admin_event(cursor, staff["id"], "category.create", "category", category["slug"])
            return _taxonomy_response(cursor)


@app.patch("/admin/categories/{slug}", response_model=AdminTaxonomyResponse)
def admin_update_category(slug: str, payload: AdminCategoryPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            new_slug = _slug_seed(payload.slug or payload.name, max_length=100)
            cursor.execute("SELECT id FROM gotrendlabs_market_categories WHERE slug = %s", (slug,))
            category = cursor.fetchone()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
            cursor.execute("SELECT id FROM gotrendlabs_market_categories WHERE slug = %s AND id <> %s", (new_slug, category["id"]))
            if cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug de categoria já está em uso.")
            cursor.execute(
                "UPDATE gotrendlabs_market_categories SET name = %s, slug = %s, notice = %s WHERE id = %s",
                (payload.name.strip(), new_slug, payload.notice.strip(), category["id"]),
            )
            _record_admin_event(cursor, staff["id"], "category.update", "category", new_slug)
            return _taxonomy_response(cursor)


@app.post("/admin/categories/{slug}/block", response_model=AdminTaxonomyResponse)
def admin_block_category(slug: str, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            cursor.execute("SELECT id FROM gotrendlabs_market_categories WHERE slug = %s", (slug,))
            category = cursor.fetchone()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                UPDATE gotrendlabs_market_categories
                SET is_blocked = true, blocked_at = %s, blocked_reason = %s
                WHERE id = %s
                """,
                (now, payload.note or "Bloqueada pelo Admin Ops.", category["id"]),
            )
            _record_admin_event(cursor, staff["id"], "category.block", "category", slug, payload.note)
            return _taxonomy_response(cursor)


@app.post("/admin/categories/{slug}/unblock", response_model=AdminTaxonomyResponse)
def admin_unblock_category(slug: str, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            cursor.execute("SELECT id FROM gotrendlabs_market_categories WHERE slug = %s", (slug,))
            category = cursor.fetchone()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
            cursor.execute(
                """
                UPDATE gotrendlabs_market_categories
                SET is_blocked = false, blocked_at = NULL, blocked_reason = ''
                WHERE id = %s
                """,
                (category["id"],),
            )
            _record_admin_event(cursor, staff["id"], "category.unblock", "category", slug, payload.note)
            return _taxonomy_response(cursor)


@app.post("/admin/categories/{slug}/subcategories", response_model=AdminTaxonomyResponse, status_code=status.HTTP_201_CREATED)
def admin_create_subcategory(slug: str, payload: AdminSubcategoryPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            cursor.execute("SELECT id FROM gotrendlabs_market_categories WHERE slug = %s", (slug,))
            category = cursor.fetchone()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
            subcategory = _upsert_subcategory(cursor, category["id"], payload.name, payload.slug, payload.notice)
            _record_admin_event(cursor, staff["id"], "subcategory.create", "subcategory", subcategory["slug"])
            return _taxonomy_response(cursor)


@app.patch("/admin/categories/{slug}/subcategories/{subcategory_slug}", response_model=AdminTaxonomyResponse)
def admin_update_subcategory(slug: str, subcategory_slug: str, payload: AdminSubcategoryPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            cursor.execute("SELECT id FROM gotrendlabs_market_categories WHERE slug = %s", (slug,))
            category = cursor.fetchone()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
            cursor.execute(
                "SELECT id FROM gotrendlabs_market_subcategories WHERE category_id = %s AND slug = %s",
                (category["id"], subcategory_slug),
            )
            subcategory = cursor.fetchone()
            if not subcategory:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategoria não encontrada.")
            new_slug = _slug_seed(payload.slug or payload.name, max_length=100)
            cursor.execute(
                """
                SELECT id FROM gotrendlabs_market_subcategories
                WHERE category_id = %s AND slug = %s AND id <> %s
                """,
                (category["id"], new_slug, subcategory["id"]),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug de subcategoria já está em uso.")
            cursor.execute(
                "UPDATE gotrendlabs_market_subcategories SET name = %s, slug = %s, notice = %s WHERE id = %s",
                (payload.name.strip(), new_slug, payload.notice.strip(), subcategory["id"]),
            )
            _record_admin_event(cursor, staff["id"], "subcategory.update", "subcategory", new_slug)
            return _taxonomy_response(cursor)


@app.post("/admin/categories/{slug}/subcategories/{subcategory_slug}/block", response_model=AdminTaxonomyResponse)
def admin_block_subcategory(slug: str, subcategory_slug: str, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            cursor.execute("SELECT id FROM gotrendlabs_market_categories WHERE slug = %s", (slug,))
            category = cursor.fetchone()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
            cursor.execute(
                "SELECT id FROM gotrendlabs_market_subcategories WHERE category_id = %s AND slug = %s",
                (category["id"], subcategory_slug),
            )
            subcategory = cursor.fetchone()
            if not subcategory:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategoria não encontrada.")
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                UPDATE gotrendlabs_market_subcategories
                SET is_blocked = true, blocked_at = %s, blocked_reason = %s
                WHERE id = %s
                """,
                (now, payload.note or "Bloqueada pelo Admin Ops.", subcategory["id"]),
            )
            _record_admin_event(cursor, staff["id"], "subcategory.block", "subcategory", subcategory_slug, payload.note)
            return _taxonomy_response(cursor)


@app.post("/admin/categories/{slug}/subcategories/{subcategory_slug}/unblock", response_model=AdminTaxonomyResponse)
def admin_unblock_subcategory(slug: str, subcategory_slug: str, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            cursor.execute("SELECT id FROM gotrendlabs_market_categories WHERE slug = %s", (slug,))
            category = cursor.fetchone()
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
            cursor.execute(
                "SELECT id FROM gotrendlabs_market_subcategories WHERE category_id = %s AND slug = %s",
                (category["id"], subcategory_slug),
            )
            subcategory = cursor.fetchone()
            if not subcategory:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategoria não encontrada.")
            cursor.execute(
                """
                UPDATE gotrendlabs_market_subcategories
                SET is_blocked = false, blocked_at = NULL, blocked_reason = ''
                WHERE id = %s
                """,
                (subcategory["id"],),
            )
            _record_admin_event(cursor, staff["id"], "subcategory.unblock", "subcategory", subcategory_slug, payload.note)
            return _taxonomy_response(cursor)


def _taxonomy_category_and_subcategory(cursor, category_slug, subcategory_slug):
    cursor.execute("SELECT id FROM gotrendlabs_market_categories WHERE slug = %s", (category_slug,))
    category = cursor.fetchone()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    cursor.execute(
        "SELECT id FROM gotrendlabs_market_subcategories WHERE category_id = %s AND slug = %s",
        (category["id"], subcategory_slug),
    )
    subcategory = cursor.fetchone()
    if not subcategory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategoria não encontrada.")
    return category, subcategory


@app.post("/admin/categories/{slug}/subcategories/{subcategory_slug}/events", response_model=AdminTaxonomyResponse, status_code=status.HTTP_201_CREATED)
def admin_create_event(slug: str, subcategory_slug: str, payload: AdminEventPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            _, subcategory = _taxonomy_category_and_subcategory(cursor, slug, subcategory_slug)
            event = _upsert_event(cursor, subcategory["id"], payload.name, payload.slug, payload.notice)
            _record_admin_event(cursor, staff["id"], "event.create", "event", event["slug"])
            return _taxonomy_response(cursor)


@app.patch("/admin/categories/{slug}/subcategories/{subcategory_slug}/events/{event_slug}", response_model=AdminTaxonomyResponse)
def admin_update_event(slug: str, subcategory_slug: str, event_slug: str, payload: AdminEventPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            _, subcategory = _taxonomy_category_and_subcategory(cursor, slug, subcategory_slug)
            cursor.execute(
                "SELECT id FROM gotrendlabs_market_events WHERE subcategory_id = %s AND slug = %s",
                (subcategory["id"], event_slug),
            )
            event = cursor.fetchone()
            if not event:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
            new_slug = _slug_seed(payload.slug or payload.name, max_length=100)
            cursor.execute(
                """
                SELECT id FROM gotrendlabs_market_events
                WHERE subcategory_id = %s AND slug = %s AND id <> %s
                """,
                (subcategory["id"], new_slug, event["id"]),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug de evento já está em uso.")
            cursor.execute(
                "UPDATE gotrendlabs_market_events SET name = %s, slug = %s, notice = %s WHERE id = %s",
                (payload.name.strip(), new_slug, payload.notice.strip(), event["id"]),
            )
            _record_admin_event(cursor, staff["id"], "event.update", "event", new_slug)
            return _taxonomy_response(cursor)


@app.post("/admin/categories/{slug}/subcategories/{subcategory_slug}/events/{event_slug}/block", response_model=AdminTaxonomyResponse)
def admin_block_event(slug: str, subcategory_slug: str, event_slug: str, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            _, subcategory = _taxonomy_category_and_subcategory(cursor, slug, subcategory_slug)
            cursor.execute(
                "SELECT id FROM gotrendlabs_market_events WHERE subcategory_id = %s AND slug = %s",
                (subcategory["id"], event_slug),
            )
            event = cursor.fetchone()
            if not event:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                UPDATE gotrendlabs_market_events
                SET is_blocked = true, blocked_at = %s, blocked_reason = %s
                WHERE id = %s
                """,
                (now, payload.note or "Bloqueado pelo Admin Ops.", event["id"]),
            )
            _record_admin_event(cursor, staff["id"], "event.block", "event", event_slug, payload.note)
            return _taxonomy_response(cursor)


@app.post("/admin/categories/{slug}/subcategories/{subcategory_slug}/events/{event_slug}/unblock", response_model=AdminTaxonomyResponse)
def admin_unblock_event(slug: str, subcategory_slug: str, event_slug: str, payload: AdminMarketActionPayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            _, subcategory = _taxonomy_category_and_subcategory(cursor, slug, subcategory_slug)
            cursor.execute(
                "SELECT id FROM gotrendlabs_market_events WHERE subcategory_id = %s AND slug = %s",
                (subcategory["id"], event_slug),
            )
            event = cursor.fetchone()
            if not event:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
            cursor.execute(
                """
                UPDATE gotrendlabs_market_events
                SET is_blocked = false, blocked_at = NULL, blocked_reason = ''
                WHERE id = %s
                """,
                (event["id"],),
            )
            _record_admin_event(cursor, staff["id"], "event.unblock", "event", event_slug, payload.note)
            return _taxonomy_response(cursor)


@app.delete("/admin/categories/{slug}/subcategories/{subcategory_slug}/events/{event_slug}", response_model=AdminTaxonomyResponse)
def admin_delete_event(slug: str, subcategory_slug: str, event_slug: str, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            staff = _current_staff_user(cursor, authorization)
            _, subcategory = _taxonomy_category_and_subcategory(cursor, slug, subcategory_slug)
            cursor.execute(
                "SELECT id FROM gotrendlabs_market_events WHERE subcategory_id = %s AND slug = %s",
                (subcategory["id"], event_slug),
            )
            event = cursor.fetchone()
            if not event:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado.")
            cursor.execute("SELECT COUNT(*) AS total FROM gotrendlabs_markets WHERE event_id = %s", (event["id"],))
            linked_markets = cursor.fetchone()["total"]
            if linked_markets:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Evento possui mercados vinculados.")
            cursor.execute("DELETE FROM gotrendlabs_market_events WHERE id = %s", (event["id"],))
            _record_admin_event(cursor, staff["id"], "event.delete", "event", event_slug)
            return _taxonomy_response(cursor)


@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterPayload, request: Request):
    _enforce_rate_limit("register", _rate_limit_identity(request, payload.email), limit=10, window_seconds=3600)
    if not payload.terms_accepted:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="É preciso aceitar a política de uso para criar conta.")
    _ensure_recaptcha(payload.recaptcha_token, request)

    language = payload.language if payload.language in {"pt-br", "en"} else "pt-br"
    ip_address, user_agent = _client_meta(request)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM gotrendlabs_users WHERE lower(email) = lower(%s)",
                (payload.email,),
            )
            if cursor.fetchone():
                _record_event(cursor, "login_failure", email=payload.email, ip_address=ip_address, user_agent=user_agent)
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já está em uso.")

            now = datetime.now(timezone.utc)
            cursor.execute("SELECT email_enabled, referral_bonus_gtl FROM gotrendlabs_site_config WHERE singleton_key = 1")
            site_config = cursor.fetchone()
            email_confirmation_required = bool(site_config and site_config["email_enabled"])
            handle = _unique_handle(cursor, payload.display_name)
            cursor.execute(
                """
                INSERT INTO gotrendlabs_users
                    (password, last_login, is_superuser, username, first_name, last_name, is_staff, is_active,
                     date_joined, email, preferred_language, external_provider, external_subject,
                     terms_accepted_at, terms_version, account_status, deletion_requested_at, deactivated_at,
                     email_confirmed_at, is_bot)
                VALUES (%s, NULL, false, %s, %s, '', false, true, %s, %s, %s, '', '',
                        %s, %s, 'active', NULL, NULL, %s, false)
                RETURNING id, username, email, first_name, preferred_language, date_joined, last_login, account_status, is_staff, email_confirmed_at
                """,
                (
                    make_password(payload.password),
                    handle,
                    payload.display_name.strip(),
                    now,
                    payload.email.lower(),
                    language,
                    now,
                    TERMS_VERSION,
                    None if email_confirmation_required else now,
                ),
            )
            user = cursor.fetchone()
            _ensure_user_core(cursor, user["id"], display_name=payload.display_name.strip())
            _award_referral_bonus(cursor, payload.referral_code, user["id"])
            session = _create_session(cursor, user["id"], request)
            _record_event(cursor, "register", user_id=user["id"], email=user["email"], ip_address=ip_address, user_agent=user_agent)
            if email_confirmation_required:
                issue_email_confirmation(cursor, user, ip_address=ip_address, user_agent=user_agent)
                _record_event(cursor, "email_confirmation_sent", user_id=user["id"], email=user["email"], ip_address=ip_address, user_agent=user_agent)
            return {"user": _user_response(user), "session": session}


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginPayload, request: Request):
    ip_address, user_agent = _client_meta(request)
    _enforce_rate_limit("login", _rate_limit_identity(request, payload.email), limit=10, window_seconds=300)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, first_name, preferred_language, password, is_active,
                       date_joined, last_login, account_status, is_staff, email_confirmed_at
                FROM gotrendlabs_users
                WHERE lower(email) = lower(%s)
                """,
                (payload.email,),
            )
            user = cursor.fetchone()
            if not user or not user["is_active"] or user["account_status"] != "active" or not check_password(payload.password, user["password"]):
                _record_event(cursor, "login_failure", user_id=user["id"] if user else None, email=payload.email, ip_address=ip_address, user_agent=user_agent)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos.")

            now = datetime.now(timezone.utc)
            cursor.execute("UPDATE gotrendlabs_users SET last_login = %s WHERE id = %s", (now, user["id"]))
            user["last_login"] = now
            session = _create_session(cursor, user["id"], request)
            _record_event(cursor, "login_success", user_id=user["id"], email=user["email"], ip_address=ip_address, user_agent=user_agent)
            return {"user": _user_response(user), "session": session}


@app.post("/auth/password-reset/request", response_model=PasswordResetRequestResponse)
def request_password_reset(payload: PasswordResetRequestPayload, request: Request):
    ip_address, user_agent = _client_meta(request)
    _enforce_rate_limit("password-reset-request", _rate_limit_identity(request, payload.email), limit=5, window_seconds=3600)
    reset_url = ""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, first_name, preferred_language
                FROM gotrendlabs_users
                WHERE lower(email) = lower(%s)
                  AND is_active = true
                  AND account_status = 'active'
                """,
                (payload.email,),
            )
            user = cursor.fetchone()
            if user:
                _issue_password_reset(cursor, user, ip_address=ip_address, user_agent=user_agent)
                _record_event(cursor, "password_reset_requested", user_id=user["id"], email=user["email"], ip_address=ip_address, user_agent=user_agent)
    return {"message": PASSWORD_RESET_MESSAGE, "reset_url": ""}


@app.post("/auth/password-reset/confirm", response_model=PasswordResetConfirmResponse)
def confirm_password_reset(payload: PasswordResetConfirmPayload, request: Request):
    ip_address, user_agent = _client_meta(request)
    _enforce_rate_limit("password-reset-confirm", _rate_limit_identity(request), limit=10, window_seconds=3600)
    now = datetime.now(timezone.utc)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT t.id, t.user_id, u.email
                FROM gotrendlabs_password_reset_tokens t
                JOIN gotrendlabs_users u ON u.id = t.user_id
                WHERE t.token_hash = %s
                  AND t.used_at IS NULL
                  AND t.expires_at > %s
                  AND u.is_active = true
                  AND u.account_status = 'active'
                """,
                (hash_token(payload.token), now),
            )
            token_row = cursor.fetchone()
            if not token_row:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Link de recuperação inválido ou expirado.")
            cursor.execute(
                """
                UPDATE gotrendlabs_users
                SET password = %s
                WHERE id = %s
                """,
                (make_password(payload.password), token_row["user_id"]),
            )
            cursor.execute(
                """
                UPDATE gotrendlabs_auth_sessions
                SET revoked_at = %s
                WHERE user_id = %s AND revoked_at IS NULL
                """,
                (now, token_row["user_id"]),
            )
            cursor.execute(
                """
                UPDATE gotrendlabs_password_reset_tokens
                SET used_at = %s
                WHERE id = %s
                """,
                (now, token_row["id"]),
            )
            _record_event(cursor, "password_reset_confirmed", user_id=token_row["user_id"], email=token_row["email"], ip_address=ip_address, user_agent=user_agent)
    return {"message": "Senha atualizada com sucesso."}


@app.post("/auth/email-confirm/confirm", response_model=EmailConfirmationResponse)
def confirm_email(payload: EmailConfirmationConfirmPayload, request: Request):
    _enforce_rate_limit("email-confirm", _rate_limit_identity(request), limit=10, window_seconds=3600)
    ip_address, user_agent = _client_meta(request)
    now = datetime.now(timezone.utc)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT t.id, t.user_id, u.email
                FROM gotrendlabs_email_confirmation_tokens t
                JOIN gotrendlabs_users u ON u.id = t.user_id
                WHERE t.token_hash = %s
                  AND t.used_at IS NULL
                  AND t.expires_at > %s
                  AND u.is_active = true
                  AND u.account_status = 'active'
                """,
                (hash_token(payload.token), now),
            )
            token_row = cursor.fetchone()
            if not token_row:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Link de confirmação inválido ou expirado.")
            cursor.execute(
                """
                UPDATE gotrendlabs_users
                SET email_confirmed_at = COALESCE(email_confirmed_at, %s)
                WHERE id = %s
                """,
                (now, token_row["user_id"]),
            )
            cursor.execute("UPDATE gotrendlabs_email_confirmation_tokens SET used_at = %s WHERE id = %s", (now, token_row["id"]))
            _record_event(cursor, "email_confirmed", user_id=token_row["user_id"], email=token_row["email"], ip_address=ip_address, user_agent=user_agent)
    return {"message": "Email confirmado com sucesso."}


@app.post("/auth/email-confirm/resend", response_model=EmailConfirmationResponse)
def resend_email_confirmation(request: Request, authorization: str = Header(default="")):
    _enforce_rate_limit("email-confirm-resend", _rate_limit_identity(request, authorization), limit=5, window_seconds=3600)
    ip_address, user_agent = _client_meta(request)
    now = datetime.now(timezone.utc)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            if user.get("email_confirmed_at"):
                return {"message": "Email já confirmado."}
            cursor.execute(
                """
                SELECT created_at
                FROM gotrendlabs_email_confirmation_tokens
                WHERE user_id = %s
                  AND used_at IS NULL
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user["id"],),
            )
            latest = cursor.fetchone()
            if latest and latest["created_at"] > now - timedelta(minutes=10):
                return {"message": "Aguarde alguns minutos antes de reenviar a confirmação."}
            issue_email_confirmation(cursor, user, ip_address=ip_address, user_agent=user_agent)
            _record_event(cursor, "email_confirmation_sent", user_id=user["id"], email=user["email"], ip_address=ip_address, user_agent=user_agent)
    return {"message": "Enviamos um novo link de confirmação."}


@app.get("/auth/session", response_model=SessionContextResponse)
def session_context(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            return {"user": _user_response(user), "authenticated": True}


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, authorization: str = Header(default="")):
    token = _bearer_token(authorization)
    ip_address, user_agent = _client_meta(request)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE gotrendlabs_auth_sessions
                SET revoked_at = %s
                WHERE token_hash = %s AND revoked_at IS NULL
                RETURNING user_id
                """,
                (datetime.now(timezone.utc), hash_token(token)),
            )
            row = cursor.fetchone()
            if row:
                _record_event(cursor, "logout", user_id=row["user_id"], ip_address=ip_address, user_agent=user_agent)
    return None


@app.post("/auth/social/{provider}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def social_login(provider: str):
    if provider not in {"google", "facebook", "x"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provedor não suportado.")
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Login social ainda depende da credencial OAuth do provedor.")


@app.get("/users/me", response_model=UserProfileResponse)
def get_me(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            return _profile_response(cursor, user)


@app.get("/users/me/notifications", response_model=NotificationListResponse)
def get_my_notifications(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            return _notification_rows(cursor, user["id"])


@app.post("/users/me/notifications/read-all", response_model=NotificationListResponse)
def mark_my_notifications_read(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            cursor.execute(
                """
                UPDATE gotrendlabs_user_notifications
                SET is_read = true, read_at = %s
                WHERE recipient_id = %s AND is_read = false
                """,
                (datetime.now(timezone.utc), user["id"]),
            )
            return _notification_rows(cursor, user["id"])


@app.patch("/users/me", response_model=UserProfileResponse)
def update_me(payload: ProfileUpdatePayload, authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            _require_email_confirmed(user)
            updates = []
            values = []
            if payload.display_name is not None:
                updates.append("display_name = %s")
                values.append(payload.display_name.strip())
                cursor.execute("UPDATE gotrendlabs_users SET first_name = %s WHERE id = %s", (payload.display_name.strip(), user["id"]))
                user["first_name"] = payload.display_name.strip()
            if payload.email is not None and payload.email.lower() != user["email"].lower():
                cursor.execute("SELECT id FROM gotrendlabs_users WHERE lower(email) = lower(%s) AND id <> %s", (payload.email, user["id"]))
                if cursor.fetchone():
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe uma conta com este email.")
                cursor.execute("UPDATE gotrendlabs_users SET email = %s, email_confirmed_at = NULL WHERE id = %s", (payload.email.lower(), user["id"]))
                user["email"] = payload.email.lower()
                user["email_confirmed_at"] = None
                issue_email_confirmation(cursor, user, ip_address=None, user_agent="")
                _record_event(cursor, "email_confirmation_sent", user_id=user["id"], email=user["email"])
            if payload.handle is not None:
                handle = _handle_seed(payload.handle)
                if len(handle) < 2:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Identificador inválido.")
                if handle != user["username"]:
                    cursor.execute("SELECT id FROM gotrendlabs_users WHERE lower(username) = lower(%s) AND id <> %s", (handle, user["id"]))
                    if cursor.fetchone():
                        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe uma conta com este identificador.")
                    cursor.execute("UPDATE gotrendlabs_users SET username = %s WHERE id = %s", (handle, user["id"]))
                    user["username"] = handle
            if payload.preferred_language is not None:
                language = payload.preferred_language if payload.preferred_language in {"pt-br", "en"} else "pt-br"
                cursor.execute("UPDATE gotrendlabs_users SET preferred_language = %s WHERE id = %s", (language, user["id"]))
                user["preferred_language"] = language
            if "birth_date" in payload.model_fields_set:
                if payload.birth_date and payload.birth_date > date.today():
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Data de nascimento não pode ser futura.")
                updates.append("birth_date = %s")
                values.append(payload.birth_date)
            if "sex" in payload.model_fields_set:
                sex = (payload.sex or "").strip()
                if sex and sex not in {"male", "female", "other", "prefer_not_to_say"}:
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Sexo inválido.")
                updates.append("sex = %s")
                values.append(sex)
            if payload.bio is not None:
                updates.append("bio = %s")
                values.append(payload.bio.strip())
            if updates:
                updates.append("updated_at = %s")
                values.append(datetime.now(timezone.utc))
                values.append(user["id"])
                cursor.execute(f"UPDATE gotrendlabs_user_profiles SET {', '.join(updates)} WHERE user_id = %s", values)
            return _profile_response(cursor, user)


@app.post("/auth/account-deletion-request", status_code=status.HTTP_204_NO_CONTENT)
def request_account_deletion(request: Request, authorization: str = Header(default="")):
    ip_address, user_agent = _client_meta(request)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            _require_email_confirmed(user)
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                UPDATE gotrendlabs_users
                SET account_status = 'deactivated',
                    is_active = false,
                    deletion_requested_at = %s,
                    deactivated_at = %s
                WHERE id = %s
                """,
                (now, now, user["id"]),
            )
            cursor.execute(
                """
                UPDATE gotrendlabs_auth_sessions
                SET revoked_at = %s
                WHERE user_id = %s AND revoked_at IS NULL
                """,
                (now, user["id"]),
            )
            _record_event(
                cursor,
                "account_deletion_requested",
                user_id=user["id"],
                email=user["email"],
                ip_address=ip_address,
                user_agent=user_agent,
            )
    return None


@app.get("/users/me/wallet")
def get_my_wallet(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            return _wallet_summary(cursor, user["id"])


@app.get("/users/me/wallet/recharge-requests", response_model=WalletRechargeRequestListResponse)
def get_my_wallet_recharge_requests(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            cursor.execute(
                """
                SELECT id, status, amount_gtl, admin_note, created_at, reviewed_at
                FROM gotrendlabs_wallet_recharge_requests
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT 10
                """,
                (user["id"],),
            )
            return {"requests": [_wallet_recharge_public_response(row) for row in cursor.fetchall()]}


@app.post("/users/me/wallet/recharge-requests", response_model=WalletRechargeRequestResponse, status_code=status.HTTP_201_CREATED)
def create_my_wallet_recharge_request(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            _require_email_confirmed(user)
            wallet = _wallet_summary(cursor, user["id"])
            cursor.execute(
                """
                SELECT wallet_recharge_min_balance_gtl
                FROM gotrendlabs_site_config
                WHERE singleton_key = 1
                """
            )
            site_config = cursor.fetchone()
            min_balance = int(site_config["wallet_recharge_min_balance_gtl"] if site_config else 100)
            if wallet["available_gtl"] > min_balance:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Recarga disponível apenas para saldo disponível de até {min_balance} GT₵.",
                )
            cursor.execute(
                """
                SELECT id
                FROM gotrendlabs_wallet_recharge_requests
                WHERE user_id = %s AND status = 'pending'
                """,
                (user["id"],),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Você já possui uma solicitação de recarga pendente.")
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                INSERT INTO gotrendlabs_wallet_recharge_requests
                    (user_id, status, amount_gtl, admin_note, reviewed_by_id, reviewed_at, created_at, updated_at)
                VALUES (%s, 'pending', NULL, '', NULL, NULL, %s, %s)
                RETURNING id, status, amount_gtl, admin_note, created_at, reviewed_at
                """,
                (user["id"], now, now),
            )
            return _wallet_recharge_public_response(cursor.fetchone())


@app.get("/users/me/ledger", response_model=LedgerResponse)
def get_my_ledger(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            wallet = _wallet_summary(cursor, user["id"])
            cursor.execute(
                """
                SELECT id, entry_type, amount, direction, description, reference_type, reference_id, created_by_id, created_at
                FROM gotrendlabs_wallet_ledger
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                """,
                (user["id"],),
            )
            entries = [_ledger_entry_response(row) for row in cursor.fetchall()]
            return {"wallet": wallet, "entries": entries}


@app.get("/users/me/referral", response_model=ReferralResponse)
def get_my_referral(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            return _referral_response(cursor, user)


@app.get("/users/me/badges", response_model=list[BadgeResponse])
def get_my_badges(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            BadgeAwardEngine.reconcile_user(cursor, user["id"], ensure_user_core=_ensure_user_core)
            return _badge_rows(cursor, user_id=user["id"])


@app.get("/users/me/activity")
def get_my_activity(authorization: str = Header(default="")):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            user = _current_user(cursor, authorization)
            cursor.execute(
                """
                SELECT activity_type, title, description, reference_type, reference_id, occurred_at
                FROM gotrendlabs_user_activities
                WHERE user_id = %s
                ORDER BY occurred_at DESC, id DESC
                LIMIT 20
                """,
                (user["id"],),
            )
            return [
                {
                    "activity_type": row["activity_type"],
                    "title": row["title"],
                    "description": row["description"],
                    "reference_type": row["reference_type"],
                    "reference_id": row["reference_id"],
                    "occurred_at": row["occurred_at"].isoformat(),
                }
                for row in cursor.fetchall()
            ]


@app.get("/users/{handle}", response_model=PublicUserProfileResponse)
def get_public_profile(handle: str):
    cleaned = _clean_handle(handle)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, first_name, preferred_language, date_joined, last_login, account_status, is_staff
                FROM gotrendlabs_users
                WHERE lower(username) = lower(%s) AND is_active = true AND account_status = 'active'
                """,
                (cleaned,),
            )
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")
            _ensure_user_core(cursor, user["id"])
            cursor.execute("SELECT is_public FROM gotrendlabs_user_profiles WHERE user_id = %s", (user["id"],))
            if not cursor.fetchone()["is_public"]:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")
            return _public_profile_response(cursor, user)


@app.get("/rankings", response_model=RankingResponse)
def get_rankings(
    category: Optional[str] = Query(default=None),
    subcategory: Optional[str] = Query(default=None),
    event: Optional[str] = Query(default=None),
):
    selected_category = (category or "").strip()
    selected_subcategory = (subcategory or "").strip() if selected_category else ""
    selected_event = (event or "").strip() if selected_category and selected_subcategory else ""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            categories = _ranking_categories(cursor)
            cursor.execute("SELECT id FROM gotrendlabs_users WHERE is_active = true")
            for row in cursor.fetchall():
                _ensure_user_core(cursor, row["id"])
            if selected_category:
                return {
                    "rows": _ranking_theme_rows(cursor, selected_category, selected_subcategory, selected_event),
                    "categories": categories,
                    "selected_category": selected_category,
                    "selected_subcategory": selected_subcategory,
                    "selected_event": selected_event,
                }
            cursor.execute(
                """
                SELECT u.id, u.username, u.first_name, r.reputation_score, r.accuracy_indicator, r.strong_category
                FROM gotrendlabs_user_reputations r
                JOIN gotrendlabs_users u ON u.id = r.user_id
                WHERE u.is_active = true
                  AND u.is_staff = false
                  AND u.is_superuser = false
                  AND u.is_bot = false
                  AND lower(COALESCE(u.username, '')) NOT LIKE '@dev%%'
                  AND lower(COALESCE(u.username, '')) NOT LIKE 'dev%%'
                  AND lower(COALESCE(r.strong_category, '')) <> 'dev ranking'
                ORDER BY r.reputation_score DESC, u.date_joined ASC, u.id ASC
                LIMIT 50
                """
            )
            rows = []
            for index, row in enumerate(cursor.fetchall(), start=1):
                rows.append(
                    {
                        "position": index,
                        "user_id": row["id"],
                        "handle": _handle_seed(row["username"]),
                        "display_name": row["first_name"] or _handle_seed(row["username"]),
                        "reputation_score": row["reputation_score"],
                        "accuracy_indicator": row["accuracy_indicator"],
                        "strong_category": row["strong_category"] or "Geral",
                    }
                )
            rows = _attach_ranking_badges(cursor, rows)
            return {
                "rows": rows,
                "categories": categories,
                "selected_category": selected_category,
                "selected_subcategory": selected_subcategory,
                "selected_event": selected_event,
            }
