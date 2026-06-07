from pathlib import Path
from io import BytesIO
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.web.django.accounts.api_client import (
    AuthAPIError,
    admin_adjust_user_wallet,
    admin_create_ai_agent,
    admin_block_category,
    admin_block_event,
    admin_block_subcategory,
    admin_cancel_market,
    admin_create_badge,
    admin_create_category,
    admin_create_event,
    admin_create_market,
    admin_create_subcategory,
    admin_convert_suggestion,
    admin_get_dashboard_summary,
    admin_get_ai_agent,
    admin_get_ai_agent_action,
    admin_get_ai_agent_actions,
    admin_get_ai_agents,
    admin_deactivate_badge,
    admin_delete_event,
    admin_get_badges,
    admin_get_market,
    admin_get_market_participants,
    admin_get_market_resolution_audit,
    admin_get_markets,
    admin_get_comments,
    admin_get_queues,
    admin_get_system_log,
    admin_get_system_logs,
    admin_get_taxonomy,
    admin_get_user,
    admin_get_users,
    admin_request_user_password_reset,
    get_backend_health,
    admin_lock_market,
    admin_moderate_comment,
    admin_publish_market,
    admin_deactivate_user,
    admin_reactivate_user,
    admin_resolve_market,
    admin_review_queue_item,
    admin_revoke_user_sessions,
    admin_reward_feedback,
    admin_reward_suggestion,
    admin_approve_wallet_recharge,
    admin_reject_wallet_recharge,
    admin_unblock_category,
    admin_unblock_event,
    admin_unblock_subcategory,
    admin_update_user_roles,
    admin_update_user_bot,
    admin_update_ai_agent,
    admin_update_badge,
    admin_update_category,
    admin_update_event,
    admin_update_market,
    admin_update_subcategory,
)
from apps.web.django.accounts.session import USER_KEY, admin_api_required, auth_token
from apps.web.django.admin_ops.forms import (
    AdminBadgeForm,
    AdminCategoryForm,
    AdminEventForm,
    AdminMarketForm,
    AiAgentForm,
    AiConfigForm,
    AdminSubcategoryForm,
    AdminUserNoteForm,
    AdminUserPasswordResetForm,
    AdminUserRoleForm,
    AdminUserBotForm,
    AdminUserWalletAdjustmentForm,
    DaemonConfigForm,
    EconomyConfigForm,
    EmailTemplateForm,
    FeedbackRewardForm,
    MaintenanceConfigForm,
    MarketResolutionForm,
    QueueReviewForm,
    RetentionConfigForm,
    SiteEmailConfigForm,
    WalletRechargeApprovalForm,
    WalletRechargeRejectForm,
)
from apps.web.django.admin_ops.models import SiteConfig
from apps.web.django.communications.models import EmailDelivery, EmailTemplate
from apps.web.django.core.platform_config import load_platform_config, save_platform_config
from PIL import Image, UnidentifiedImageError


THUMB_STORAGE = FileSystemStorage(location=settings.MEDIA_ROOT / "market_thumbnails", base_url=settings.MEDIA_URL + "market_thumbnails/")
BADGE_STORAGE = FileSystemStorage(location=settings.MEDIA_ROOT / "badge_images", base_url=settings.MEDIA_URL + "badge_images/")
LOAD_MORE_STEP = 10
MAX_UPLOAD_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_UPLOAD_FORMATS = {"JPEG", "PNG", "WEBP"}
CONTRACT_TIMELINE_STATUSES = ("draft", "scheduled", "open", "locked")
CONTRACT_TIMELINE_STATUS_LABELS = {
    "draft": "Rascunhos",
    "scheduled": "Agendados",
    "open": "Abertos",
    "locked": "Fechados",
}

EMAIL_DELIVERY_STATUS_LABELS = {
    "queued": "Na fila",
    "sending": "Enviando",
    "sent": "Enviado",
    "failed": "Falhou",
    "suppressed": "Bloqueado",
}

EMAIL_DELIVERY_STATUS_CLASSES = {
    "queued": "warn",
    "sending": "warn",
    "sent": "safe",
    "failed": "risk",
    "suppressed": "warn",
}


EMAIL_TEMPLATE_HELP = {
    "user.email_confirmation": {
        "description": "Boas-vindas e confirmação de email para liberar ações sensíveis da conta.",
        "variables": [
            ("display_name", "Nome exibido do usuário", "{{ display_name }}", "Ana Silva"),
            ("confirmation_url", "Link único de confirmação", "{{ confirmation_url }}", "https://gotrendlabs.com.br/email-confirm/confirm/exemplo/"),
            ("expires_hours", "Validade do link em horas", "{{ expires_hours }}", "48"),
        ],
    },
    "account.password_reset": {
        "description": "Recuperação de senha por link expirável enviado somente por email.",
        "variables": [
            ("display_name", "Nome exibido do usuário", "{{ display_name }}", "Ana Silva"),
            ("reset_url", "Link único de redefinição de senha", "{{ reset_url }}", "https://gotrendlabs.com.br/password-reset/confirm/exemplo/"),
            ("expires_minutes", "Validade do link em minutos", "{{ expires_minutes }}", "60"),
        ],
    },
    "market.locked": {
        "description": "Aviso para participantes quando um mercado fecha para novas previsões.",
        "variables": [
            ("display_name", "Nome exibido do usuário", "{{ display_name }}", "Ana Silva"),
            ("market_title", "Título público do mercado", "{{ market_title }}", "Bitcoin fecha acima de US$ 120 mil em 2026?"),
            ("market_url", "Link para acompanhar o mercado", "{{ market_url }}", "https://gotrendlabs.com.br/markets/bitcoin-120k-2026/"),
        ],
    },
    "market.resolved": {
        "description": "Aviso para participantes quando um mercado é resolvido.",
        "variables": [
            ("display_name", "Nome exibido do usuário", "{{ display_name }}", "Ana Silva"),
            ("market_title", "Título público do mercado", "{{ market_title }}", "Bitcoin fecha acima de US$ 120 mil em 2026?"),
            ("winning_option", "Opção vencedora informada na resolução", "{{ winning_option }}", "SIM"),
            ("market_url", "Link para ver o resultado", "{{ market_url }}", "https://gotrendlabs.com.br/markets/bitcoin-120k-2026/"),
        ],
    },
    "wallet.credited": {
        "description": "Aviso quando créditos são concedidos ao usuário.",
        "variables": [
            ("display_name", "Nome exibido do usuário", "{{ display_name }}", "Ana Silva"),
            ("amount", "Quantidade de GT₵ concedida", "{{ amount }}", "250"),
            ("description", "Motivo do crédito", "{{ description }}", "Recompensa por sugestão aprovada"),
            ("entry_type", "Tipo técnico do lançamento", "{{ entry_type }}", "suggestion_reward"),
            ("reference_type", "Tipo da origem do crédito", "{{ reference_type }}", "market_suggestion"),
            ("reference_id", "ID da origem do crédito", "{{ reference_id }}", "42"),
            ("wallet_url", "Link da carteira", "{{ wallet_url }}", "https://gotrendlabs.com.br/wallet/"),
        ],
    },
}


def _email_template_help(template):
    fallback = {"description": "Template transacional em PT-BR.", "variables": []}
    return EMAIL_TEMPLATE_HELP.get(template.key if template else "", fallback)


def _email_template_sample_context(template):
    return {name: sample for name, _description, _token, sample in _email_template_help(template)["variables"]}


def _email_delivery_datetime(value):
    parsed = _parse_datetime(value)
    if not parsed:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _email_delivery_label(value):
    if not value:
        return "-"
    return timezone.localtime(value).strftime("%d/%m/%Y %H:%M")


def _email_delivery_counts():
    counts = {status: 0 for status in EMAIL_DELIVERY_STATUS_LABELS}
    for row in EmailDelivery.objects.values("status").annotate(total=Count("id")):
        counts[row["status"]] = row["total"]
    counts["total"] = sum(counts.values())
    return counts


def _email_delivery_row(delivery):
    return {
        "id": delivery.id,
        "created_at": _email_delivery_label(delivery.created_at),
        "updated_at": _email_delivery_label(delivery.updated_at),
        "last_attempt_at": _email_delivery_label(delivery.last_attempt_at),
        "next_attempt_at": _email_delivery_label(delivery.next_attempt_at),
        "sent_at": _email_delivery_label(delivery.sent_at),
        "status": delivery.status,
        "status_label": EMAIL_DELIVERY_STATUS_LABELS.get(delivery.status, delivery.status),
        "status_class": EMAIL_DELIVERY_STATUS_CLASSES.get(delivery.status, "warn"),
        "recipient_email": delivery.recipient_email,
        "recipient_label": getattr(delivery.recipient_user, "username", "") or delivery.recipient_email,
        "template_key": delivery.template_key,
        "event_type": delivery.event_type,
        "subject": delivery.subject,
        "attempt_count": delivery.attempt_count,
        "max_attempts": delivery.max_attempts,
        "last_error": delivery.last_error,
        "idempotency_key": delivery.idempotency_key,
    }


def _display_handle(value):
    value = (value or "").strip()
    return value if value.startswith("@") else f"@{value}"


def _normalized_load_more_limit(raw_limit, step=LOAD_MORE_STEP):
    try:
        limit = int(raw_limit or step)
    except (TypeError, ValueError):
        limit = step
    if limit < step:
        limit = step
    if limit % step:
        limit = ((limit // step) + 1) * step
    return limit


def _load_more_query(request, next_limit):
    query = request.GET.copy()
    for key in ("page", "page_size"):
        query.pop(key, None)
    query["limit"] = str(next_limit)
    return f"?{query.urlencode()}"


def _load_more_context(request, total, visible_count, current_limit):
    return {
        "total": total,
        "visible_count": visible_count,
        "has_more": visible_count < total,
        "next_url": _load_more_query(request, current_limit + LOAD_MORE_STEP),
        "show": total > LOAD_MORE_STEP,
    }


def _slice_load_more(request, items):
    total = len(items)
    limit = _normalized_load_more_limit(request.GET.get("limit"))
    visible_items = items[:limit]
    return visible_items, _load_more_context(request, total, len(visible_items), limit)


def _parse_contract_timeline_datetime(value):
    parsed = _parse_datetime(value)
    if not parsed:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, ZoneInfo("UTC"))
    return parsed


def _contract_timeline_label(value):
    if not value:
        return ""
    return timezone.localtime(value).strftime("%d/%m/%Y %H:%M")


def _contract_timeline_position(value, starts_at, span_seconds):
    if not value or span_seconds <= 0:
        return 0
    offset = (value - starts_at).total_seconds()
    return round(max(0, min(100, (offset / span_seconds) * 100)), 1)


def _contract_timeline_marker_context(label, value, today):
    if not value:
        return {"label": label, "time_label": "", "time_class": "future"}
    if timezone.localtime(value).date() == timezone.localtime(today).date():
        time_label = "Agora"
        time_class = "now"
    elif value < today:
        time_label = "Passado"
        time_class = "past"
    else:
        time_label = "Futuro"
        time_class = "future"
    return {
        "label": f"{label}: {time_label.lower()}",
        "time_label": time_label,
        "time_class": time_class,
    }


def _contract_timeline_phase_context(row, today):
    status = row["market"].get("status") or "draft"
    close_at = row["close_at"]
    resolved_at = row["resolved_at"]
    close_is_past = bool(close_at and close_at <= today)
    close_is_soon = bool(close_at and today < close_at <= today + timedelta(days=3))
    labels = {
        "draft": ("Preparação", "Rascunho pronto para revisar"),
        "scheduled": ("Agendado", "Contrato aguardando operação"),
        "open": ("Em operação", "Recebendo previsões até o fechamento"),
        "locked": ("Em apuração", "Fechado, aguardando resolução"),
    }
    current_label, current_note = labels.get(status, ("Operacional", "Acompanhar próximo marco"))
    phases = [
        {
            "label": "Criação",
            "state": "done",
            "date_label": _contract_timeline_label(row["starts_at"]),
            "note": "Contrato criado",
        },
        {
            "label": "Operação",
            "state": "active" if status == "open" and not close_is_past else "done" if status == "locked" or close_is_past else "pending",
            "date_label": "em curso" if status == "open" and not close_is_past else "concluída" if status == "locked" or close_is_past else "aguardando",
            "note": "Janela de previsões",
        },
        {
            "label": "Fechamento",
            "state": "done" if status == "locked" or resolved_at else "active" if close_is_past else "pending",
            "date_label": _contract_timeline_label(close_at) or "sem data",
            "note": "Prazo vencido" if close_is_past and status != "locked" else "Fechamento próximo" if close_is_soon else "Prazo do mercado",
            "urgency": "overdue" if close_is_past and status != "locked" else "soon" if close_is_soon else "",
            "alert_label": "Atrasado" if close_is_past and status != "locked" else "Próximo" if close_is_soon else "",
        },
        {
            "label": "Resolução",
            "state": "done" if resolved_at else "active" if status == "locked" else "pending",
            "date_label": _contract_timeline_label(resolved_at) or "pendente",
            "note": "Resultado auditável",
        },
    ]
    first_pending_index = next((index for index, phase in enumerate(phases) if phase["state"] == "pending"), None)
    for index, phase in enumerate(phases):
        if phase["state"] == "done":
            phase["time_label"] = "Passado"
        elif phase["state"] == "active":
            phase["time_label"] = "Agora"
        elif first_pending_index == index:
            phase["time_label"] = "Próxima"
        else:
            phase["time_label"] = "Futuro"
    return {
        "current_phase_label": current_label,
        "current_phase_note": current_note,
        "current_phase_class": status,
        "phase_steps": phases,
    }


def _build_contract_timeline(markets, *, today=None):
    today = today or timezone.now()
    parsed_rows = []
    for market in markets:
        status = market.get("status") or ""
        if status not in CONTRACT_TIMELINE_STATUSES:
            continue
        starts_at = _parse_contract_timeline_datetime(market.get("created_at"))
        if not starts_at:
            continue
        close_at = _parse_contract_timeline_datetime(market.get("close_at"))
        resolved_at = _parse_contract_timeline_datetime(market.get("resolved_at"))
        ends_at = resolved_at or close_at or starts_at
        parsed_rows.append(
            {
                "market": market,
                "starts_at": starts_at,
                "close_at": close_at,
                "resolved_at": resolved_at,
                "ends_at": ends_at,
            }
        )

    if not parsed_rows:
        return {
            "rows": [],
            "axis_ticks": [],
            "today_position": None,
            "has_today": False,
            "starts_at_label": "",
            "ends_at_label": "",
            "total": 0,
        }

    starts_at = min(row["starts_at"] for row in parsed_rows)
    ends_at = max(row["ends_at"] for row in parsed_rows)
    if ends_at <= starts_at:
        ends_at = starts_at + timedelta(days=1)
    span_seconds = (ends_at - starts_at).total_seconds()

    axis_ticks = []
    for index in range(5):
        tick_at = starts_at + timedelta(seconds=span_seconds * index / 4)
        axis_ticks.append(
            {
                "position": _contract_timeline_position(tick_at, starts_at, span_seconds),
                "label": timezone.localtime(tick_at).strftime("%d/%m"),
            }
        )

    today_position = None
    if starts_at <= today <= ends_at:
        today_position = _contract_timeline_position(today, starts_at, span_seconds)

    rows = []
    for row in parsed_rows:
        market = row["market"]
        starts_at_position = _contract_timeline_position(row["starts_at"], starts_at, span_seconds)
        ends_at_position = _contract_timeline_position(row["ends_at"], starts_at, span_seconds)
        close_at_position = _contract_timeline_position(row["close_at"], starts_at, span_seconds) if row["close_at"] else None
        resolved_at_position = _contract_timeline_position(row["resolved_at"], starts_at, span_seconds) if row["resolved_at"] else None
        phase_context = _contract_timeline_phase_context(row, today)
        if today <= row["starts_at"]:
            progress_end_position = starts_at_position
        elif today >= row["ends_at"]:
            progress_end_position = ends_at_position
        else:
            progress_end_position = _contract_timeline_position(today, starts_at, span_seconds)
        rows.append(
            {
                "market": market,
                "status_class": market.get("status") or "draft",
                **phase_context,
                "starts_at_label": _contract_timeline_label(row["starts_at"]),
                "close_at_label": _contract_timeline_label(row["close_at"]),
                "resolved_at_label": _contract_timeline_label(row["resolved_at"]),
                "bar_left": starts_at_position,
                "bar_width": max(1.4, ends_at_position - starts_at_position),
                "bar_progress_width": max(0, progress_end_position - starts_at_position),
                "markers": [
                    {
                        **_contract_timeline_marker_context("Criação", row["starts_at"], today),
                        "position": starts_at_position,
                        "class": "start",
                    },
                    *(
                        [
                            {
                                **_contract_timeline_marker_context("Fechamento", row["close_at"], today),
                                "position": close_at_position,
                                "class": "close",
                            }
                        ]
                        if close_at_position is not None
                        else []
                    ),
                    *(
                        [
                            {
                                **_contract_timeline_marker_context("Resolução", row["resolved_at"], today),
                                "position": resolved_at_position,
                                "class": "resolved",
                            }
                        ]
                        if resolved_at_position is not None
                        else []
                    ),
                ],
            }
        )

    return {
        "rows": rows,
        "axis_ticks": axis_ticks,
        "today_position": today_position,
        "has_today": today_position is not None,
        "starts_at_label": _contract_timeline_label(starts_at),
        "ends_at_label": _contract_timeline_label(ends_at),
        "total": len(rows),
    }


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _datetime_label(value, timezone_name):
    parsed = _parse_datetime(value)
    if not parsed:
        return ""
    timezone_name = timezone_name or "UTC"
    try:
        target_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        target_timezone = ZoneInfo("UTC")
        timezone_name = "UTC"
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
    localized = parsed.astimezone(target_timezone)
    return f"{localized.strftime('%d/%m/%Y %H:%M')} {timezone_name}"


def _market_resolution_meta(market):
    enriched = {**market}
    resolution_timezone = enriched.get("resolution_timezone") or enriched.get("close_timezone") or "UTC"
    enriched["resolution_timezone"] = resolution_timezone
    enriched["resolved_at_label"] = enriched.get("resolved_at_label") or _datetime_label(enriched.get("resolved_at"), resolution_timezone)
    return enriched


def _safe_image_content(upload, *, prefix):
    if upload.size > MAX_UPLOAD_IMAGE_BYTES:
        raise ValueError("Imagem excede o limite de 5 MB.")
    try:
        raw = upload.read()
        image = Image.open(BytesIO(raw))
        image.verify()
        image = Image.open(BytesIO(raw))
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Arquivo de imagem inválido.") from exc
    if image.format not in ALLOWED_UPLOAD_FORMATS:
        raise ValueError("Formato de imagem não permitido. Use PNG, JPEG ou WebP.")
    if image.width <= 0 or image.height <= 0 or image.width * image.height > 20_000_000:
        raise ValueError("Dimensões da imagem não permitidas.")
    image = image.convert("RGBA") if image.mode not in {"RGB", "RGBA"} else image
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)
    return f"{prefix}.png", ContentFile(output.read())


def _save_thumbnail(upload):
    filename, content = _safe_image_content(upload, prefix="market-thumb")
    return THUMB_STORAGE.save(THUMB_STORAGE.get_available_name(filename), content)


def _save_badge_image(upload):
    filename, content = _safe_image_content(upload, prefix="badge")
    return BADGE_STORAGE.save(BADGE_STORAGE.get_available_name(filename), content)


def _market_initial(market):
    options = market.get("options", [])
    initial = {
        "title": market.get("title", ""),
        "slug": market.get("slug", ""),
        "summary": market.get("summary", ""),
        "kind": market.get("kind", "binary"),
        "status_label": market.get("status_label", ""),
        "primary_outcome": market.get("primary_outcome", ""),
        "primary_probability_exact": market.get("primary_probability_exact", 0),
        "secondary_probability_exact": market.get("secondary_probability_exact", 0),
        "volume_gtl": market.get("volume_gtl", ""),
        "participants": market.get("participants", ""),
        "category": market.get("category", ""),
        "subcategory": market.get("subcategory", ""),
        "event": market.get("event") or "Geral",
        "source": market.get("source", ""),
        "close_label": market.get("close_label", ""),
        "thumb": market.get("thumb", ""),
        "thumb_color": market.get("thumb_color", ""),
        "image_url": market.get("image_url", ""),
        "resolution_criteria": market.get("resolution_criteria", ""),
        "admin_notes": market.get("admin_notes", ""),
        "close_at": (market.get("close_at") or "")[:16],
        "close_timezone": market.get("close_timezone") or "America/Sao_Paulo",
        "auto_close_enabled": market.get("auto_close_enabled", True),
        "is_featured": market.get("is_featured", False),
        "view_count": market.get("view_count", 0),
        "share_count": market.get("share_count", 0),
        "resolution_type": market.get("resolution_type", ""),
        "resolution_note": market.get("resolution_note", ""),
        "options": [
            {
                "label": option.get("label", ""),
                "hint": option.get("hint", ""),
                "probability": option.get("probability", 0),
                "probability_exact": option.get("probability_exact", option.get("probability", 0)),
            }
            for option in options
        ],
    }
    for index, option in enumerate(options[:3], start=1):
        initial[f"option_{index}_label"] = option.get("label", "")
        initial[f"option_{index}_hint"] = option.get("hint", "")
    return initial


def _default_market_initial():
    return {
        "kind": "binary",
        "category": "",
        "subcategory": "",
        "event": "",
        "thumb": "AI",
        "thumb_color": "#d8ece2",
        "close_timezone": "America/Sao_Paulo",
        "auto_close_enabled": True,
        "is_featured": False,
        "option_1_label": "SIM",
        "option_1_hint": "Opção afirmativa",
        "option_2_label": "NAO",
        "option_2_hint": "Opção negativa",
        "options": [
            {"label": "SIM", "hint": "Opção afirmativa"},
            {"label": "NAO", "hint": "Opção negativa"},
        ],
    }


def _empty_market_participants():
    return {
        "market": {},
        "summary": {
            "participants": "0 participantes",
            "human_participants": 0,
            "bot_participants": 0,
            "human_volume_gtl": 0,
            "bot_volume_gtl": 0,
            "total_volume_gtl": 0,
            "participants_total": 0,
            "human_predictions": 0,
            "bot_predictions": 0,
        },
        "participants": [],
    }


def _market_participants_context(token, slug):
    if not slug:
        return _empty_market_participants()
    try:
        return admin_get_market_participants(token, slug)
    except AuthAPIError:
        return _empty_market_participants()


def _market_taxonomy_options(taxonomy_data):
    categories = []
    subcategories = []
    events = []
    for category in taxonomy_data.get("categories", []):
        if category.get("is_blocked"):
            continue
        category_name = category.get("name", "")
        categories.append({"name": category_name, "slug": category.get("slug", "")})
        for subcategory in category.get("subcategories", []):
            if subcategory.get("is_blocked"):
                continue
            subcategories.append(
                {
                    "name": subcategory.get("name", ""),
                    "slug": subcategory.get("slug", ""),
                    "category": category_name,
                }
            )
            for event in subcategory.get("events", []):
                if event.get("is_blocked"):
                    continue
                events.append(
                    {
                        "name": event.get("name", ""),
                        "slug": event.get("slug", ""),
                        "category": category_name,
                        "subcategory": subcategory.get("name", ""),
                    }
                )
    return {"categories": categories, "subcategories": subcategories, "events": events}


def _default_market_initial_for_taxonomy(taxonomy_data):
    return _default_market_initial()


def _age_label(created_at):
    delta = timezone.now() - created_at
    hours = int(delta.total_seconds() // 3600)
    if hours < 1:
        return "agora"
    if hours < 24:
        return f"{hours}h"
    return f"{hours // 24}d"


def _comment_status_label(value):
    return {"visible": "Visível", "hidden": "Oculto"}.get(value, value)


def _comment_queue_item(comment):
    status_value = comment.get("status", "visible") if isinstance(comment, dict) else comment.status
    created_at = comment.get("created_at") if isinstance(comment, dict) else comment.created_at
    if isinstance(created_at, str):
        created_at_label = created_at[:16].replace("T", " ")
        age_label = ""
    else:
        created_at_label = created_at.strftime("%d/%m/%Y %H:%M")
        age_label = _age_label(created_at)
    author_handle = comment.get("author_handle", "") if isinstance(comment, dict) else comment.author.username
    author_id = comment.get("author_id") if isinstance(comment, dict) else comment.author_id
    market_slug = comment.get("market_slug", "") if isinstance(comment, dict) else comment.market.slug
    body = comment.get("body", "") if isinstance(comment, dict) else comment.body
    moderation_note = comment.get("moderation_note", "") if isinstance(comment, dict) else comment.moderation_note
    comment_id = comment.get("id") if isinstance(comment, dict) else comment.id
    return {
        "id": comment_id,
        "kind": "comment",
        "title": body[:90],
        "queue_label": "Comentários",
        "item_type": f"Comentário em {market_slug}",
        "status": status_value,
        "status_label": _comment_status_label(status_value),
        "severity_label": "Média",
        "owner_label": "Moderação",
        "age_label": age_label,
        "author_handle": _display_handle(author_handle) if author_handle else "",
        "author_id": author_id,
        "guest_name": "",
        "guest_email": "",
        "source": market_slug,
        "description": body,
        "admin_note": moderation_note,
        "created_at": comment.get("created_at", "") if isinstance(comment, dict) else comment.created_at.isoformat(),
        "created_at_label": created_at_label,
    }


def _admin_session_user_label(request):
    user = request.session.get(USER_KEY) or {}
    return user.get("handle") or user.get("email") or user.get("display_name") or "staff"


def _admin_model_user(request):
    user = request.session.get(USER_KEY) or {}
    user_id = user.get("id")
    if not user_id:
        return None
    return get_user_model().objects.filter(id=user_id).first()


def _audit_pagination(audit_data):
    pagination = audit_data.get("pagination", {})
    limit = int(pagination.get("limit") or 10)
    offset = int(pagination.get("offset") or 0)
    total = int(pagination.get("total") or 0)
    previous_offset = max(0, offset - limit)
    next_offset = offset + limit
    pagination.update(
        {
            "has_previous": offset > 0,
            "has_next": next_offset < total,
            "previous_offset": previous_offset,
            "next_offset": next_offset,
            "start": offset + 1 if total else 0,
            "end": min(offset + limit, total),
        }
    )
    audit_data["pagination"] = pagination
    return audit_data


AI_ACTION_TYPE_COPY = {
    "comment": ("Comentário", "Tentativa de publicar um comentário oficial identificado como IA."),
    "prediction": ("Previsão bot", "Tentativa de reservar GT₵ por uma conta oficial automatizada."),
    "cycle": ("Ciclo IA", "Registro global do ciclo operacional dos agentes IA."),
}

AI_ACTION_STATUS_COPY = {
    "created": ("Executada", "A ação foi concluída e gerou registro de domínio.", "safe"),
    "skipped": ("Ignorada", "A ação foi pulada por regra operacional, limite ou configuração.", "warn"),
    "failed": ("Falhou", "A ação tentou executar, mas encontrou erro ou validação impeditiva.", "risk"),
}

AI_ACTION_REASON_COPY = {
    "ai_agents_disabled": ("Agentes IA desativados", "O kill switch geral de agentes IA está desligado."),
    "ai_commenting_disabled": ("Comentários IA desativados", "A configuração permite agentes, mas bloqueia criação de comentários."),
    "ai_paused": ("IA pausada", "A operação IA está pausada até o fim da janela configurada."),
    "ai_predictions_disabled": ("Previsões bot desativadas", "A configuração permite agentes, mas bloqueia previsões automatizadas."),
    "agent_daily_comment_limit": ("Limite diário do agente", "Este agente já atingiu o limite diário de comentários."),
    "agent_daily_prediction_limit": ("Limite diário do agente", "Este agente já atingiu o limite diário de previsões bot."),
    "comment_attempt_limit_reached": ("Limite de tentativas", "O ciclo atingiu o máximo de mercados avaliados para comentário."),
    "comment_created": ("Comentário criado", "Um comentário oficial foi publicado e registrado com vínculo ao mercado."),
    "comment_validation_failed": ("Comentário reprovado", "A resposta da IA não passou na validação segura antes da publicação."),
    "cycle_completed": ("Ciclo concluído", "O ciclo IA terminou e registrou seu resumo operacional."),
    "cycle_error": ("Erro no ciclo", "O ciclo IA falhou durante a execução global."),
    "global_daily_comment_limit": ("Limite global de comentários", "A plataforma já atingiu o limite diário global de comentários IA."),
    "global_daily_prediction_limit": ("Limite global de previsões", "A plataforma já atingiu o limite diário global de previsões bot."),
    "llm_error": ("Erro no provedor IA", "A chamada ao provedor de IA falhou ou retornou erro."),
    "llm_error_timeout": ("Timeout no provedor IA", "A chamada ao provedor de IA demorou além do limite operacional."),
    "llm_should_publish_false": ("IA recomendou não publicar", "A IA avaliou o mercado e indicou que o comentário não deveria ser publicado."),
    "no_active_analyst_agent": ("Sem analista ativo", "Não há agente analista ativo elegível para comentar."),
    "no_active_liquidity_agent": ("Sem liquidez ativa", "Não há agente de liquidez ativo elegível para prever."),
    "no_eligible_market": ("Sem mercado elegível", "Nenhum mercado aberto atendeu às regras do ciclo para essa ação."),
    "no_human_participants": ("Sem participantes humanos", "Previsões bot exigem participação humana mínima antes de agir."),
    "prediction_created": ("Previsão bot criada", "Uma previsão automatizada foi criada respeitando limites e saldo."),
}


def _ai_copy(mapping, value, fallback_help):
    label, help_text, *rest = mapping.get(value, (value or "-", fallback_help))
    payload = {"label": label, "help": help_text}
    if rest:
        payload["class"] = rest[0]
    return payload


def _enrich_ai_action(action):
    if not action:
        return action
    action_type = action.get("action_type") or ""
    action_status = action.get("status") or ""
    reason = action.get("reason") or ""
    type_copy = _ai_copy(AI_ACTION_TYPE_COPY, action_type, "Tipo técnico da ação IA.")
    status_copy = _ai_copy(AI_ACTION_STATUS_COPY, action_status, "Status técnico da ação IA.")
    reason_copy = _ai_copy(AI_ACTION_REASON_COPY, reason, "Motivo técnico registrado pelo ciclo IA.")
    return {
        **action,
        "action_type_label": type_copy["label"],
        "action_type_help": type_copy["help"],
        "status_label": status_copy["label"],
        "status_help": status_copy["help"],
        "status_class": status_copy.get("class", "warn"),
        "reason_label": reason_copy["label"],
        "reason_help": reason_copy["help"],
        "reason_code": reason,
    }


def _enrich_ai_actions(actions):
    return [_enrich_ai_action(action) for action in actions]


def _backend_health_context():
    try:
        payload = get_backend_health()
    except AuthAPIError as exc:
        return {"status": "offline", "label": "Offline", "detail": str(exc)}
    if payload.get("status") == "ok":
        return {"status": "online", "label": "Online", "detail": "/health ok"}
    return {"status": "offline", "label": "Offline", "detail": "Resposta inesperada do /health."}


@admin_api_required
def dashboard(request):
    token = auth_token(request)
    backend_health = _backend_health_context()
    try:
        dashboard_summary = admin_get_dashboard_summary(token)
    except AuthAPIError as exc:
        dashboard_summary = {
            "markets": {},
            "queues": {},
            "users": {},
            "engagement": {},
            "wallet": {},
            "badges": {},
            "system": {},
            "top_markets": [],
            "recent_admin_events": [],
        }
        error = str(exc)
    else:
        error = ""
    return render(
        request,
        "admin_ops/dashboard.html",
        {"dashboard_summary": dashboard_summary, "admin_error": error, "backend_health": backend_health},
    )


@admin_api_required
def config(request):
    platform_config = load_platform_config()
    site_config = SiteConfig.get_solo()
    llm_provider = (site_config.ai_llm_provider or "openai").strip().lower()
    llm_secret_name = "AWS_BEARER_TOKEN_BEDROCK" if llm_provider == "bedrock" else "OPENAI_API_KEY"
    maintenance_form = MaintenanceConfigForm(
        request.POST or None,
        initial={
            "maintenance_enabled": platform_config.get("maintenance_enabled", False),
            "maintenance_message": platform_config.get("maintenance_message", ""),
        },
        prefix="maintenance",
    )
    email_form = SiteEmailConfigForm(
        request.POST or None,
        initial={
            "email_enabled": site_config.email_enabled,
            "smtp_host": site_config.smtp_host,
            "smtp_port": site_config.smtp_port,
            "smtp_username": site_config.smtp_username,
            "smtp_use_tls": site_config.smtp_use_tls,
            "smtp_use_ssl": site_config.smtp_use_ssl,
            "smtp_timeout_seconds": site_config.smtp_timeout_seconds,
            "default_from_email": site_config.default_from_email,
            "default_reply_to_email": site_config.default_reply_to_email,
        },
        prefix="email",
    )
    economy_form = EconomyConfigForm(
        request.POST or None,
        initial={
            "wallet_recharge_min_balance_gtl": site_config.wallet_recharge_min_balance_gtl,
            "referral_bonus_gtl": site_config.referral_bonus_gtl,
        },
        prefix="economy",
    )
    daemon_form = DaemonConfigForm(
        request.POST or None,
        initial={
            "daemon_stale_after_minutes": site_config.daemon_stale_after_minutes,
            "daemon_missing_after_minutes": site_config.daemon_missing_after_minutes,
        },
        prefix="daemon",
    )
    retention_form = RetentionConfigForm(
        request.POST or None,
        initial={
            "system_log_retention_days": site_config.system_log_retention_days,
            "ai_audit_retention_days": site_config.ai_audit_retention_days,
        },
        prefix="retention",
    )
    ai_post_data = request.POST if request.method == "POST" and any(key.startswith("ai-") for key in request.POST) else None
    ai_form = AiConfigForm(
        ai_post_data,
        initial={
            field: getattr(site_config, field)
            for field in AiConfigForm.base_fields
            if hasattr(site_config, field)
        },
        prefix="ai",
    )
    ai_form_valid = ai_post_data is None or ai_form.is_valid()
    if request.method == "POST" and request.POST.get("action") == "smtp_test":
        try:
            call_command("send_smtp_test_email")
        except Exception as exc:
            messages.error(request, f"Teste SMTP falhou: {exc}")
        else:
            messages.success(request, "Teste SMTP enviado para o SES mailbox simulator.")
        return redirect("admin-ops-config")
    if (
        request.method == "POST"
        and maintenance_form.is_valid()
        and email_form.is_valid()
        and economy_form.is_valid()
        and daemon_form.is_valid()
        and retention_form.is_valid()
        and ai_form_valid
    ):
        save_platform_config(
            {
                "maintenance_enabled": maintenance_form.cleaned_data["maintenance_enabled"],
                "maintenance_message": maintenance_form.cleaned_data["maintenance_message"],
                "updated_by": _admin_session_user_label(request),
            }
        )
        for field, value in email_form.cleaned_data.items():
            setattr(site_config, field, value)
        site_config.wallet_recharge_min_balance_gtl = economy_form.cleaned_data["wallet_recharge_min_balance_gtl"]
        site_config.referral_bonus_gtl = economy_form.cleaned_data["referral_bonus_gtl"]
        site_config.daemon_stale_after_minutes = daemon_form.cleaned_data["daemon_stale_after_minutes"]
        site_config.daemon_missing_after_minutes = daemon_form.cleaned_data["daemon_missing_after_minutes"]
        site_config.system_log_retention_days = retention_form.cleaned_data["system_log_retention_days"]
        site_config.ai_audit_retention_days = retention_form.cleaned_data["ai_audit_retention_days"]
        if ai_post_data is not None:
            for field, value in ai_form.cleaned_data.items():
                setattr(site_config, field, value)
        site_config.updated_by = _admin_model_user(request)
        site_config.save()
        messages.success(request, "Configurações atualizadas.")
        return redirect("admin-ops-config")
    smtp_secret_configured = bool(settings.GOTRENDLABS_SMTP_PASSWORD or settings.GOTRENDLABS_SMTP_API_KEY)
    openai_secret_configured = bool(getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY"))
    llm_secret_configured = bool(getattr(settings, llm_secret_name, "") or os.environ.get(llm_secret_name, "").strip())
    return render(
        request,
        "admin_ops/config.html",
        {
            "maintenance_form": maintenance_form,
            "email_form": email_form,
            "economy_form": economy_form,
            "daemon_form": daemon_form,
            "retention_form": retention_form,
            "ai_form": ai_form,
            "platform_config": platform_config,
            "site_config": site_config,
            "smtp_secret_configured": smtp_secret_configured,
            "openai_secret_configured": openai_secret_configured,
            "llm_secret_configured": llm_secret_configured,
            "llm_secret_name": llm_secret_name,
            "llm_provider": llm_provider,
        },
    )


@admin_api_required
def email_templates(request, template_id=None):
    templates = EmailTemplate.objects.filter(locale="pt-br").order_by("key")
    selected = templates.filter(id=template_id).first() if template_id else templates.first()
    if template_id and not selected and templates.exists():
        return redirect("admin-ops-email-templates")
    if not selected:
        return render(request, "admin_ops/email_templates.html", {"templates": [], "selected": None, "form": None})
    template_help = _email_template_help(selected)
    form = EmailTemplateForm(
        request.POST or None,
        initial={
            "subject": selected.subject,
            "body_text": selected.body_text,
            "body_html": selected.body_html,
            "is_active": selected.is_active,
        },
    )
    if request.method == "POST" and form.is_valid():
        selected.subject = form.cleaned_data["subject"].strip()
        selected.body_text = form.cleaned_data["body_text"].strip()
        selected.body_html = form.cleaned_data["body_html"].strip()
        selected.is_active = form.cleaned_data["is_active"]
        selected.updated_by = _admin_model_user(request)
        selected.save()
        messages.success(request, "Template atualizado.")
        return redirect("admin-ops-email-template-edit", template_id=selected.id)
    return render(
        request,
        "admin_ops/email_templates.html",
        {
            "templates": templates,
            "selected": selected,
            "form": form,
            "template_description": template_help["description"],
            "template_variables": template_help["variables"],
            "template_sample_context": _email_template_sample_context(selected),
        },
    )


@admin_api_required
def email_delivery_logs(request):
    filters = {
        "q": request.GET.get("q") or "",
        "status": request.GET.get("status") or "",
        "template_key": request.GET.get("template_key") or "",
        "recipient": request.GET.get("recipient") or "",
        "from": request.GET.get("from") or "",
        "to": request.GET.get("to") or "",
    }
    deliveries = EmailDelivery.objects.select_related("recipient_user").order_by("-created_at", "-id")
    if filters["q"]:
        deliveries = deliveries.filter(
            Q(recipient_email__icontains=filters["q"])
            | Q(template_key__icontains=filters["q"])
            | Q(event_type__icontains=filters["q"])
            | Q(subject__icontains=filters["q"])
            | Q(idempotency_key__icontains=filters["q"])
            | Q(last_error__icontains=filters["q"])
        )
    if filters["status"] in EMAIL_DELIVERY_STATUS_LABELS:
        deliveries = deliveries.filter(status=filters["status"])
    if filters["template_key"]:
        deliveries = deliveries.filter(template_key=filters["template_key"])
    if filters["recipient"]:
        deliveries = deliveries.filter(recipient_email__icontains=filters["recipient"])
    start_at = _email_delivery_datetime(filters["from"])
    end_at = _email_delivery_datetime(filters["to"])
    if start_at:
        deliveries = deliveries.filter(created_at__gte=start_at)
    if end_at:
        deliveries = deliveries.filter(created_at__lte=end_at)

    total = deliveries.count()
    limit = _normalized_load_more_limit(request.GET.get("limit"))
    visible_deliveries = list(deliveries[:limit])
    template_keys = list(EmailTemplate.objects.filter(locale="pt-br").order_by("key").values_list("key", flat=True))
    return render(
        request,
        "admin_ops/email_delivery_logs.html",
        {
            "deliveries": [_email_delivery_row(delivery) for delivery in visible_deliveries],
            "filters": filters,
            "counts": _email_delivery_counts(),
            "status_labels": EMAIL_DELIVERY_STATUS_LABELS,
            "template_keys": template_keys,
            "pagination": _load_more_context(request, total, len(visible_deliveries), limit),
            "total_filtered": total,
        },
    )


@admin_api_required
def ai_agents(request):
    token = auth_token(request)
    try:
        agent_data = admin_get_ai_agents(token)
        action_data = admin_get_ai_agent_actions(
            token,
            agent_id=request.GET.get("agent_id") or "",
            market_slug=request.GET.get("market") or "",
            action_type=request.GET.get("action_type") or "",
            status=request.GET.get("status") or "",
            reason=request.GET.get("reason") or "",
        )
    except AuthAPIError as exc:
        agent_data = {"agents": [], "health": {}}
        action_data = {"actions": [], "health": {}}
        error = str(exc)
    else:
        error = ""
    visible_actions, action_pagination = _slice_load_more(request, action_data.get("actions", []))
    visible_actions = _enrich_ai_actions(visible_actions)
    action_data = {**action_data, "actions": visible_actions}
    return render(
        request,
        "admin_ops/ai_agents.html",
        {
            "agent_data": agent_data,
            "action_data": action_data,
            "action_pagination": action_pagination,
            "filters": {
                "agent_id": request.GET.get("agent_id") or "",
                "market": request.GET.get("market") or "",
                "action_type": request.GET.get("action_type") or "",
                "status": request.GET.get("status") or "",
                "reason": request.GET.get("reason") or "",
            },
            "admin_error": error,
        },
    )


def _ai_agent_initial(agent):
    return {
        "name": agent.get("name", ""),
        "agent_type": agent.get("agent_type", "analyst"),
        "user_id": agent.get("user_id", ""),
        "is_active": agent.get("is_active", False),
        "personality_prompt": agent.get("personality_prompt", ""),
        "comment_style": agent.get("comment_style", ""),
        "max_comments_per_day": agent.get("max_comments_per_day"),
        "max_predictions_per_day": agent.get("max_predictions_per_day"),
        "max_stake_gtl": agent.get("max_stake_gtl"),
        "cooldown_hours": agent.get("cooldown_hours"),
        "min_humans_for_prediction": agent.get("min_humans_for_prediction"),
    }


def _ai_agent_bot_choices(token, current_agent=None):
    choices = []
    try:
        payload = admin_get_users(token, bot="yes", status="active", order="created_desc")
    except AuthAPIError:
        payload = {"users": []}
    seen_ids = set()
    for user in payload.get("users", []):
        if not user.get("is_bot") or not user.get("is_active"):
            continue
        user_id = user.get("id")
        seen_ids.add(user_id)
        handle = user.get("handle") or f"@user-{user_id}"
        display_name = user.get("display_name") or handle
        balance = user.get("available_gtl", 0)
        choices.append((str(user_id), f"{display_name} ({handle}) · ID {user_id} · {balance} GT₵"))
    if current_agent and current_agent.get("user_id") and current_agent.get("user_id") not in seen_ids and current_agent.get("user_is_bot"):
        user_id = current_agent["user_id"]
        handle = current_agent.get("user_handle") or f"@user-{user_id}"
        display_name = current_agent.get("user_display_name") or handle
        choices.insert(0, (str(user_id), f"{display_name} ({handle}) · ID {user_id} · agente atual"))
    return choices


@admin_api_required
def ai_agent_form(request, agent_id=None):
    token = auth_token(request)
    agent = None
    error = ""
    if agent_id:
        try:
            agent = admin_get_ai_agent(token, agent_id)
        except AuthAPIError as exc:
            error = str(exc)
    bot_user_choices = _ai_agent_bot_choices(token, agent)
    form = AiAgentForm(request.POST or None, initial=_ai_agent_initial(agent or {}), bot_user_choices=bot_user_choices)
    if request.method == "POST" and form.is_valid():
        try:
            if agent_id:
                agent = admin_update_ai_agent(token, agent_id, form.to_payload())
                messages.success(request, "Agente IA atualizado.")
            else:
                agent = admin_create_ai_agent(token, form.to_payload())
                messages.success(request, "Agente IA criado.")
            return redirect("admin-ops-ai-agent-edit", agent_id=agent["id"])
        except AuthAPIError as exc:
            error = str(exc)
    return render(
        request,
        "admin_ops/ai_agent_form.html",
        {
            "form": form,
            "agent": agent,
            "admin_error": error,
            "title": "Editar agente IA" if agent_id else "Criar agente IA",
            "bot_user_choices": bot_user_choices,
            "site_config": SiteConfig.get_solo(),
        },
    )


@admin_api_required
def ai_agent_action_detail(request, action_id):
    try:
        action = admin_get_ai_agent_action(auth_token(request), action_id)
    except AuthAPIError as exc:
        action = None
        error = str(exc)
    else:
        error = ""
    payload_pretty = ""
    if action:
        action = _enrich_ai_action(action)
        payload_pretty = json.dumps(action.get("payload_summary") or {}, ensure_ascii=False, indent=2)
    return render(request, "admin_ops/ai_agent_action_detail.html", {"action": action, "payload_pretty": payload_pretty, "admin_error": error})


@admin_api_required
def markets(request):
    status_filter = request.GET.get("status") or ""
    active_order = request.GET.get("order") or "display"
    search_query = request.GET.get("q") or ""
    try:
        market_data = admin_get_markets(auth_token(request), status=status_filter, q=search_query, order=active_order)
    except AuthAPIError as exc:
        market_data = {"markets": [], "counts": {}}
        error = str(exc)
    else:
        error = ""
    visible_markets, market_pagination = _slice_load_more(request, market_data.get("markets", []))
    market_data = {**market_data, "markets": visible_markets}
    return render(
        request,
        "admin_ops/markets.html",
        {
            "market_data": market_data,
            "market_pagination": market_pagination,
            "admin_error": error,
            "active_status": status_filter,
            "active_order": active_order,
            "search_query": search_query,
        },
    )


@admin_api_required
def contracts(request):
    requested_status = request.GET.get("status") or ""
    status_filter = requested_status if requested_status in CONTRACT_TIMELINE_STATUSES else ""
    search_query = request.GET.get("q") or ""
    try:
        market_data = admin_get_markets(auth_token(request), status=status_filter, q=search_query, order="created_asc")
    except AuthAPIError as exc:
        market_data = {"markets": [], "counts": {}}
        error = str(exc)
    else:
        error = ""
    timeline = _build_contract_timeline(market_data.get("markets", []))
    visible_rows, contract_pagination = _slice_load_more(request, timeline.get("rows", []))
    timeline = {**timeline, "rows": visible_rows}
    return render(
        request,
        "admin_ops/contracts.html",
        {
            "timeline": timeline,
            "contract_pagination": contract_pagination,
            "market_data": market_data,
            "admin_error": error,
            "active_status": status_filter,
            "search_query": search_query,
            "status_filters": [
                {"value": value, "label": label, "count": market_data.get("counts", {}).get(value, 0)}
                for value, label in CONTRACT_TIMELINE_STATUS_LABELS.items()
            ],
        },
    )


@admin_api_required
def users(request):
    filters = {
        "q": request.GET.get("q") or "",
        "status": request.GET.get("status") or "",
        "role": request.GET.get("role") or "",
        "bot": request.GET.get("bot") or "",
        "order": request.GET.get("order") or "created_desc",
    }
    try:
        user_data = admin_get_users(auth_token(request), **filters)
    except AuthAPIError as exc:
        user_data = {"users": [], "counts": {}}
        error = str(exc)
    else:
        error = ""
    visible_users, user_pagination = _slice_load_more(request, user_data.get("users", []))
    user_data = {**user_data, "users": visible_users}
    return render(
        request,
        "admin_ops/users.html",
        {
            "user_data": user_data,
            "user_pagination": user_pagination,
            "admin_error": error,
            "active_q": filters["q"],
            "active_status": filters["status"],
            "active_role": filters["role"],
            "active_bot": filters["bot"],
            "active_order": filters["order"],
        },
    )


@admin_api_required
def system_logs(request):
    token = auth_token(request)
    filters = {
        "q": request.GET.get("q") or "",
        "level": request.GET.get("level") or "",
        "source": request.GET.get("source") or "",
        "logger": request.GET.get("logger") or "",
        "event_type": request.GET.get("event_type") or "",
        "method": request.GET.get("method") or "",
        "path": request.GET.get("path") or "",
        "status_code": request.GET.get("status_code") or "",
        "user_identifier": request.GET.get("user_identifier") or request.GET.get("user_id") or "",
        "request_id": request.GET.get("request_id") or "",
        "exception_type": request.GET.get("exception_type") or "",
        "from": request.GET.get("from") or "",
        "to": request.GET.get("to") or "",
        "page": "1",
        "page_size": str(_normalized_load_more_limit(request.GET.get("limit") or request.GET.get("page_size"))),
    }
    try:
        log_data = admin_get_system_logs(token, **filters)
    except AuthAPIError as exc:
        log_data = {"logs": [], "counts": {}, "page": 1, "page_size": 50, "total": 0}
        error = str(exc)
    else:
        error = ""
    log_user_options = []
    seen_user_ids = set()
    for user_filters in ({"order": "created_desc"}, {"role": "staff", "order": "created_desc"}, {"role": "superuser", "order": "created_desc"}):
        try:
            users_payload = admin_get_users(token, **user_filters)
        except AuthAPIError:
            continue
        for user in users_payload.get("users", []):
            if user.get("id") in seen_user_ids:
                continue
            seen_user_ids.add(user.get("id"))
            log_user_options.append(user)
    def _safe_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    page_size = _safe_int(log_data.get("page_size") or filters["page_size"], 50)
    total = _safe_int(log_data.get("total"), 0)
    pagination = {
        "page_size": page_size,
        "total": total,
        "visible_count": len(log_data.get("logs", [])),
        "has_more": len(log_data.get("logs", [])) < total,
        "next_url": _load_more_query(request, page_size + LOAD_MORE_STEP),
        "show": total > LOAD_MORE_STEP,
    }
    return render(
        request,
        "admin_ops/system_logs.html",
        {
            "log_data": log_data,
            "admin_error": error,
            "filters": filters,
            "log_user_options": log_user_options,
            "pagination": pagination,
        },
    )


@admin_api_required
def system_log_detail(request, log_id):
    try:
        log = admin_get_system_log(auth_token(request), log_id)
    except AuthAPIError as exc:
        log = None
        context_pretty = "{}"
        error = str(exc)
    else:
        context_pretty = json.dumps(log.get("context") or {}, ensure_ascii=False, indent=2)
        error = ""
    return render(
        request,
        "admin_ops/system_log_detail.html",
        {"log": log, "context_pretty": context_pretty, "admin_error": error},
    )


@admin_api_required
def user_detail(request, user_id):
    token = auth_token(request)
    error = ""
    detail = None
    note_form = AdminUserNoteForm()
    wallet_form = AdminUserWalletAdjustmentForm()
    role_form = AdminUserRoleForm()
    bot_form = AdminUserBotForm()
    password_reset_form = AdminUserPasswordResetForm()
    password_reset_url = ""
    if request.method == "POST":
        action = request.POST.get("action", "")
        try:
            if action == "deactivate":
                note_form = AdminUserNoteForm(request.POST)
                if note_form.is_valid():
                    admin_deactivate_user(token, user_id, note_form.cleaned_data["note"])
                    messages.success(request, "Usuário desativado e sessões revogadas.")
                    return redirect("admin-ops-user-detail", user_id=user_id)
                error = "Informe a nota operacional."
            elif action == "reactivate":
                note_form = AdminUserNoteForm(request.POST)
                if note_form.is_valid():
                    admin_reactivate_user(token, user_id, note_form.cleaned_data["note"])
                    messages.success(request, "Usuário reativado.")
                    return redirect("admin-ops-user-detail", user_id=user_id)
                error = "Informe a nota operacional."
            elif action == "revoke_sessions":
                note_form = AdminUserNoteForm(request.POST)
                if note_form.is_valid():
                    admin_revoke_user_sessions(token, user_id, note_form.cleaned_data["note"])
                    messages.success(request, "Sessões ativas revogadas.")
                    return redirect("admin-ops-user-detail", user_id=user_id)
                error = "Informe a nota operacional."
            elif action == "wallet_adjust":
                wallet_form = AdminUserWalletAdjustmentForm(request.POST)
                if wallet_form.is_valid():
                    admin_adjust_user_wallet(
                        token,
                        user_id,
                        wallet_form.cleaned_data["direction"],
                        wallet_form.cleaned_data["amount_gtl"],
                        wallet_form.cleaned_data["note"],
                    )
                    messages.success(request, "Ajuste manual de wallet registrado.")
                    return redirect("admin-ops-user-detail", user_id=user_id)
                error = "Revise o ajuste de wallet."
            elif action == "roles_update":
                role_form = AdminUserRoleForm(request.POST)
                if role_form.is_valid():
                    flags = role_form.role_flags()
                    admin_update_user_roles(
                        token,
                        user_id,
                        flags["is_staff"],
                        flags["is_superuser"],
                        role_form.cleaned_data["note"],
                    )
                    messages.success(request, "Papel administrativo atualizado.")
                    return redirect("admin-ops-user-detail", user_id=user_id)
                error = "Revise o papel administrativo."
            elif action == "bot_update":
                bot_form = AdminUserBotForm(request.POST)
                if bot_form.is_valid():
                    admin_update_user_bot(
                        token,
                        user_id,
                        bot_form.cleaned_data["is_bot"],
                        bot_form.cleaned_data["note"],
                    )
                    messages.success(request, "Classificação de robô atualizada.")
                    return redirect("admin-ops-user-detail", user_id=user_id)
                error = "Informe a nota operacional."
            elif action == "password_reset":
                password_reset_form = AdminUserPasswordResetForm(request.POST)
                if password_reset_form.is_valid():
                    reset_payload = admin_request_user_password_reset(token, user_id, password_reset_form.cleaned_data["note"])
                    password_reset_url = reset_payload.get("reset_url", "")
                    messages.success(request, "Link de reset de senha gerado.")
                else:
                    error = "Informe a nota operacional."
        except AuthAPIError as exc:
            error = str(exc)
    try:
        detail = admin_get_user(token, user_id)
    except AuthAPIError as exc:
        error = error or str(exc)
    if detail and not request.method == "POST":
        role = "superuser" if detail["user"].get("is_superuser") else "staff" if detail["user"].get("is_staff") else "user"
        role_form = AdminUserRoleForm(initial={"role": role})
        bot_form = AdminUserBotForm(initial={"is_bot": detail["user"].get("is_bot")})
    return render(
        request,
        "admin_ops/user_detail.html",
        {
            "detail": detail,
            "note_form": note_form,
            "wallet_form": wallet_form,
            "role_form": role_form,
            "bot_form": bot_form,
            "password_reset_form": password_reset_form,
            "password_reset_url": password_reset_url,
            "admin_error": error,
        },
    )


def _badge_initial(badge):
    return {
        "code": badge.get("code", ""),
        "name": badge.get("name", ""),
        "description": badge.get("description", ""),
        "rule_description": badge.get("rule_description", ""),
        "badge_type": badge.get("badge_type", "global"),
        "image_url": badge.get("image_url", ""),
        "image_dark_url": badge.get("image_dark_url", ""),
        "is_active": badge.get("is_active", True),
        "rule_type": badge.get("rule_type", "resolved_predictions_count"),
        "threshold_value": badge.get("threshold_value", 1),
        "category": badge.get("category", ""),
        "subcategory": badge.get("subcategory", ""),
        "event": badge.get("event", ""),
    }


@admin_api_required
def badges(request):
    error = ""
    badge_data = {"badges": []}
    try:
        badge_data = admin_get_badges(auth_token(request))
    except AuthAPIError as exc:
        error = str(exc)
    return render(request, "admin_ops/badges.html", {"badge_data": badge_data, "admin_error": error})


@admin_api_required
def badge_form(request, mode="new", code=None):
    token = auth_token(request)
    error = ""
    badge = None
    taxonomy_data = {"categories": []}
    try:
        taxonomy_data = admin_get_taxonomy(token)
    except AuthAPIError as exc:
        error = str(exc)
    if code:
        try:
            badge = next((item for item in admin_get_badges(token).get("badges", []) if item.get("code") == code), None)
        except AuthAPIError as exc:
            error = error or str(exc)
        if code and not badge and not error:
            error = "Badge não encontrada."
    post_data = None
    upload_error = ""
    if request.method == "POST":
        if request.POST.get("action") == "deactivate" and code:
            try:
                admin_deactivate_badge(token, code, request.POST.get("note") or "Desativada pelo Admin Ops.")
                messages.success(request, "Badge desativada.")
                return redirect("admin-ops-badges")
            except AuthAPIError as exc:
                error = str(exc)
        post_data = request.POST.copy()
        try:
            if request.FILES.get("badge_image"):
                saved_name = _save_badge_image(request.FILES["badge_image"])
                post_data["image_url"] = BADGE_STORAGE.url(saved_name)
            if request.FILES.get("badge_dark_image"):
                saved_name = _save_badge_image(request.FILES["badge_dark_image"])
                post_data["image_dark_url"] = BADGE_STORAGE.url(saved_name)
        except ValueError as exc:
            upload_error = str(exc)
    initial = _badge_initial(badge) if badge else {"badge_type": "global", "rule_type": "resolved_predictions_count", "threshold_value": 1, "is_active": True}
    form = AdminBadgeForm(post_data or None, request.FILES or None, initial=initial, taxonomy=taxonomy_data)
    if upload_error:
        form.add_error(None, upload_error)
    if request.method == "POST" and request.POST.get("action") != "deactivate":
        if not upload_error and form.is_valid():
            try:
                if mode == "new":
                    badge = admin_create_badge(token, form.to_payload())
                    messages.success(request, "Badge criada.")
                    return redirect("admin-ops-badge-edit", code=badge["code"])
                badge = admin_update_badge(token, code, form.to_payload())
                messages.success(request, "Badge atualizada.")
                return redirect("admin-ops-badge-edit", code=badge["code"])
            except AuthAPIError as exc:
                error = str(exc)
        else:
            error = "Revise os campos da badge."
    return render(
        request,
        "admin_ops/badge_form.html",
        {
            "title": "Criar badge" if mode == "new" else "Editar badge",
            "mode": mode,
            "code": code,
            "badge": badge,
            "form": form,
            "taxonomy_options": _market_taxonomy_options(taxonomy_data),
            "admin_error": error,
        },
    )


@admin_api_required
def moderation(request):
    token = auth_token(request)
    filters = {
        "kind": request.GET.get("kind") or "",
        "status": request.GET.get("status") or "",
        "severity": request.GET.get("severity") or "",
        "order": request.GET.get("order") or "created_desc",
    }
    queue_data = {"items": [], "counts": {}}
    error = ""
    try:
        if filters["kind"] != "comment":
            queue_filters = {**filters, "kind": filters["kind"] if filters["kind"] in {"suggestion", "feedback", "wallet_recharge"} else ""}
            queue_data = admin_get_queues(token, **queue_filters)
    except AuthAPIError as exc:
        queue_data = {"items": [], "counts": {}}
        error = str(exc)
    if filters["kind"] in {"", "comment"}:
        try:
            comment_filters = {}
            if filters["status"] in {"visible", "hidden"}:
                comment_filters["status"] = filters["status"]
            comments = admin_get_comments(token, **comment_filters).get("comments", [])
            comment_items = [_comment_queue_item(comment) for comment in comments]
            queue_data.setdefault("items", []).extend(comment_items)
            queue_data.setdefault("counts", {}).setdefault("comment", {})
            queue_data["counts"]["comment"]["visible"] = sum(1 for item in comment_items if item.get("status") == "visible")
            queue_data["counts"]["comment"]["hidden"] = sum(1 for item in comment_items if item.get("status") == "hidden")
        except AuthAPIError as exc:
            error = error or str(exc)
    reverse = filters.get("order") != "created_asc"
    queue_data["items"] = sorted(queue_data.get("items", []), key=lambda item: (item.get("created_at", ""), item["id"]), reverse=reverse)
    visible_items, queue_pagination = _slice_load_more(request, queue_data.get("items", []))
    queue_data = {**queue_data, "items": visible_items}
    return render(
        request,
        "admin_ops/moderation.html",
        {
            "queue_data": queue_data,
            "queue_pagination": queue_pagination,
            "active_kind": filters["kind"],
            "active_status": filters["status"],
            "active_severity": filters["severity"],
            "active_order": filters["order"],
            "admin_error": error,
        },
    )


@admin_api_required
def resolution(request):
    token = auth_token(request)
    error = ""
    active_order = request.GET.get("order") or "resolution_desc"
    try:
        locked_data = admin_get_markets(token, status="locked", order=active_order)
        resolved_data = admin_get_markets(token, status="resolved", order=active_order)
        market_data = {
            "markets": [*locked_data.get("markets", []), *resolved_data.get("markets", [])],
            "counts": {**locked_data.get("counts", {}), **resolved_data.get("counts", {})},
        }
    except AuthAPIError as exc:
        market_data = {"markets": [], "counts": {}}
        error = str(exc)
    market_data["markets"] = [_market_resolution_meta(market) for market in market_data.get("markets", [])]
    dated_markets = [market for market in market_data["markets"] if _parse_datetime(market.get("resolved_at"))]
    pending_markets = [market for market in market_data["markets"] if not _parse_datetime(market.get("resolved_at"))]
    dated_markets.sort(key=lambda market: _parse_datetime(market.get("resolved_at")), reverse=active_order != "resolution_asc")
    market_data["markets"] = [*pending_markets, *dated_markets] if active_order == "pending_first" else [*dated_markets, *pending_markets]
    visible_markets, resolution_pagination = _slice_load_more(request, market_data["markets"])
    market_data = {**market_data, "markets": visible_markets}
    return render(
        request,
        "admin_ops/resolution.html",
        {"market_data": market_data, "resolution_pagination": resolution_pagination, "admin_error": error, "active_order": active_order},
    )


@admin_api_required
def taxonomy(request):
    token = auth_token(request)
    message = ""
    error = ""
    if request.method == "POST":
        if request.POST.get("action") == "create_category":
            form = AdminCategoryForm(request.POST)
            if form.is_valid():
                try:
                    admin_create_category(token, form.cleaned_data)
                    message = "Categoria criada."
                except AuthAPIError as exc:
                    error = str(exc)
            else:
                error = "Revise a categoria."
        elif request.POST.get("action") == "update_category":
            form = AdminCategoryForm(request.POST)
            category_slug = request.POST.get("category_slug", "")
            if form.is_valid() and category_slug:
                try:
                    admin_update_category(token, category_slug, form.cleaned_data)
                    message = "Categoria atualizada."
                except AuthAPIError as exc:
                    error = str(exc)
            else:
                error = "Revise a categoria."
        elif request.POST.get("action") == "create_subcategory":
            form = AdminSubcategoryForm(request.POST)
            if form.is_valid():
                try:
                    admin_create_subcategory(
                        token,
                        form.cleaned_data["category_slug"],
                        {
                            "name": form.cleaned_data["name"],
                            "slug": form.cleaned_data.get("slug") or None,
                            "notice": form.cleaned_data.get("notice") or "",
                        },
                    )
                    message = "Subcategoria criada."
                except AuthAPIError as exc:
                    error = str(exc)
            else:
                error = "Revise a subcategoria."
        elif request.POST.get("action") == "update_subcategory":
            form = AdminSubcategoryForm(request.POST)
            category_slug = request.POST.get("category_slug", "")
            subcategory_slug = request.POST.get("subcategory_slug", "")
            if form.is_valid() and category_slug and subcategory_slug:
                try:
                    admin_update_subcategory(
                        token,
                        category_slug,
                        subcategory_slug,
                        {
                            "name": form.cleaned_data["name"],
                            "slug": form.cleaned_data.get("slug") or None,
                            "notice": form.cleaned_data.get("notice") or "",
                        },
                    )
                    message = "Subcategoria atualizada."
                except AuthAPIError as exc:
                    error = str(exc)
            else:
                error = "Revise a subcategoria."
        elif request.POST.get("action") == "create_event":
            form = AdminEventForm(request.POST)
            if form.is_valid():
                try:
                    admin_create_event(
                        token,
                        form.cleaned_data["category_slug"],
                        form.cleaned_data["subcategory_slug"],
                        {
                            "name": form.cleaned_data["name"],
                            "slug": form.cleaned_data.get("slug") or None,
                            "notice": form.cleaned_data.get("notice") or "",
                        },
                    )
                    message = "Evento criado."
                except AuthAPIError as exc:
                    error = str(exc)
            else:
                error = "Revise o evento."
        elif request.POST.get("action") == "update_event":
            form = AdminEventForm(request.POST)
            category_slug = request.POST.get("category_slug", "")
            subcategory_slug = request.POST.get("subcategory_slug", "")
            event_slug = request.POST.get("event_slug", "")
            if form.is_valid() and category_slug and subcategory_slug and event_slug:
                try:
                    admin_update_event(
                        token,
                        category_slug,
                        subcategory_slug,
                        event_slug,
                        {
                            "name": form.cleaned_data["name"],
                            "slug": form.cleaned_data.get("slug") or None,
                            "notice": form.cleaned_data.get("notice") or "",
                        },
                    )
                    message = "Evento atualizado."
                except AuthAPIError as exc:
                    error = str(exc)
            else:
                error = "Revise o evento."
        elif request.POST.get("action") == "block_category":
            category_slug = request.POST.get("category_slug", "")
            try:
                admin_block_category(token, category_slug, request.POST.get("block_note") or "Bloqueada pelo Admin Ops.")
                message = "Categoria bloqueada."
            except AuthAPIError as exc:
                error = str(exc)
        elif request.POST.get("action") == "unblock_category":
            category_slug = request.POST.get("category_slug", "")
            try:
                admin_unblock_category(token, category_slug, request.POST.get("block_note") or "Reativada pelo Admin Ops.")
                message = "Categoria desbloqueada."
            except AuthAPIError as exc:
                error = str(exc)
        elif request.POST.get("action") == "block_subcategory":
            category_slug = request.POST.get("category_slug", "")
            subcategory_slug = request.POST.get("subcategory_slug", "")
            try:
                admin_block_subcategory(token, category_slug, subcategory_slug, request.POST.get("block_note") or "Bloqueada pelo Admin Ops.")
                message = "Subcategoria bloqueada."
            except AuthAPIError as exc:
                error = str(exc)
        elif request.POST.get("action") == "unblock_subcategory":
            category_slug = request.POST.get("category_slug", "")
            subcategory_slug = request.POST.get("subcategory_slug", "")
            try:
                admin_unblock_subcategory(token, category_slug, subcategory_slug, request.POST.get("block_note") or "Reativada pelo Admin Ops.")
                message = "Subcategoria desbloqueada."
            except AuthAPIError as exc:
                error = str(exc)
        elif request.POST.get("action") == "block_event":
            category_slug = request.POST.get("category_slug", "")
            subcategory_slug = request.POST.get("subcategory_slug", "")
            event_slug = request.POST.get("event_slug", "")
            try:
                admin_block_event(token, category_slug, subcategory_slug, event_slug, request.POST.get("block_note") or "Bloqueado pelo Admin Ops.")
                message = "Evento bloqueado."
            except AuthAPIError as exc:
                error = str(exc)
        elif request.POST.get("action") == "unblock_event":
            category_slug = request.POST.get("category_slug", "")
            subcategory_slug = request.POST.get("subcategory_slug", "")
            event_slug = request.POST.get("event_slug", "")
            try:
                admin_unblock_event(token, category_slug, subcategory_slug, event_slug, request.POST.get("block_note") or "Reativado pelo Admin Ops.")
                message = "Evento desbloqueado."
            except AuthAPIError as exc:
                error = str(exc)
        elif request.POST.get("action") == "delete_event":
            category_slug = request.POST.get("category_slug", "")
            subcategory_slug = request.POST.get("subcategory_slug", "")
            event_slug = request.POST.get("event_slug", "")
            try:
                admin_delete_event(token, category_slug, subcategory_slug, event_slug)
                message = "Evento excluído."
            except AuthAPIError as exc:
                error = str(exc)
    try:
        taxonomy_data = admin_get_taxonomy(token)
    except AuthAPIError as exc:
        taxonomy_data = {"categories": []}
        error = error or str(exc)
    categories = taxonomy_data.get("categories", [])
    for category in categories:
        category["events_count"] = sum(len(subcategory.get("events", [])) for subcategory in category.get("subcategories", []))
        category["has_blocked_item"] = bool(category.get("is_blocked")) or any(
            subcategory.get("is_blocked") or any(event.get("is_blocked") for event in subcategory.get("events", []))
            for subcategory in category.get("subcategories", [])
        )
    taxonomy_summary = {
        "categories_count": len(categories),
        "subcategories_count": sum(len(category.get("subcategories", [])) for category in categories),
        "events_count": sum(len(subcategory.get("events", [])) for category in categories for subcategory in category.get("subcategories", [])),
        "markets_count": sum(int(category.get("markets_count") or 0) for category in categories),
        "blocked_count": sum(
            (1 if category.get("is_blocked") else 0)
            + sum(1 for subcategory in category.get("subcategories", []) if subcategory.get("is_blocked"))
            + sum(1 for subcategory in category.get("subcategories", []) for event in subcategory.get("events", []) if event.get("is_blocked"))
            for category in categories
        ),
    }
    return render(
        request,
        "admin_ops/taxonomy.html",
        {
            "taxonomy": taxonomy_data,
            "taxonomy_summary": taxonomy_summary,
            "category_form": AdminCategoryForm(),
            "subcategory_form": AdminSubcategoryForm(),
            "event_form": AdminEventForm(),
            "admin_message": message,
            "admin_error": error,
        },
    )


@admin_api_required
def market_form(request, mode="new", slug=None):
    token = auth_token(request)
    market = None
    taxonomy_data = {"categories": []}
    error = ""
    message = ""
    if slug:
        try:
            market = _market_resolution_meta(admin_get_market(token, slug))
        except AuthAPIError as exc:
            error = str(exc)
    try:
        taxonomy_data = admin_get_taxonomy(token)
    except AuthAPIError as exc:
        error = error or str(exc)
    post_data = None
    upload_error = ""
    if request.method == "POST":
        if request.POST.get("action") == "lock" and mode != "new":
            try:
                market = admin_lock_market(token, slug, request.POST.get("admin_notes") or "Fechado manualmente pelo admin.")
                messages.success(request, "Mercado fechado manualmente com sucesso.")
                return redirect("admin-ops-market-edit", slug=market["slug"])
            except AuthAPIError as exc:
                error = str(exc)
        post_data = request.POST.copy()
        try:
            if request.FILES.get("thumbnail_file"):
                saved_name = _save_thumbnail(request.FILES["thumbnail_file"])
                post_data["image_url"] = THUMB_STORAGE.url(saved_name)
        except ValueError as exc:
            upload_error = str(exc)
    initial = _market_initial(market) if market else _default_market_initial_for_taxonomy(taxonomy_data)
    if post_data is not None and mode != "new" and not post_data.get("event"):
        post_data["event"] = initial.get("event") or "Geral"
    form = AdminMarketForm(post_data or None, request.FILES or None, initial=initial, taxonomy=taxonomy_data)
    if upload_error:
        form.add_error(None, upload_error)
    is_readonly = bool(market and market.get("status") == "resolved")
    if is_readonly:
        for field in form.fields.values():
            field.disabled = True
    if request.method == "POST" and request.POST.get("action") != "lock" and not upload_error and form.is_valid():
        if is_readonly:
            error = "Mercados resolvidos não podem ser alterados. Desfaça a resolução antes de editar."
            return render(
                request,
                "admin_ops/market_form.html",
                {
                    "title": "Editar/visualizar mercado",
                    "mode": mode,
                    "slug": slug,
                    "form": form,
                    "market": market,
                    "preview": market or initial,
                    "option_rows": form.option_rows(),
                    "taxonomy_options": _market_taxonomy_options(taxonomy_data),
                    "can_manual_close": False,
                    "can_publish": False,
                    "is_readonly": is_readonly,
                    "market_participants": _market_participants_context(token, market.get("slug") if market else slug),
                    "admin_error": error,
                    "admin_message": message,
                },
            )
        action = request.POST.get("action", "save")
        try:
            if mode == "new":
                market = admin_create_market(token, form.to_payload())
                slug = market["slug"]
            else:
                market = admin_update_market(token, slug, form.to_payload())
                slug = market["slug"]
            if action == "publish":
                market = admin_publish_market(token, slug, form.cleaned_data.get("admin_notes") or "")
                message = "Mercado publicado."
            elif action == "cancel":
                market = admin_cancel_market(token, slug, form.cleaned_data.get("admin_notes") or "Cancelado pelo admin.")
                message = "Mercado cancelado."
            else:
                message = "Mercado/contrato salvo com sucesso."
            messages.success(request, message)
            return redirect("admin-ops-market-edit", slug=market["slug"])
        except AuthAPIError as exc:
            error = str(exc)
    elif request.method == "POST" and request.POST.get("action") != "lock":
        error = "Revise os campos do mercado."
    title = "Criar mercado" if mode == "new" else "Editar/visualizar mercado"
    preview = market or (form.to_payload() if form.is_valid() else initial)
    option_rows = form.calculated_option_rows() if form.is_bound else form.initial.get("options", [])
    can_manual_close = bool(market and market.get("status") in {"open", "scheduled"} and market.get("auto_close_enabled") is False)
    can_publish = bool(mode == "new" or not market or market.get("status") in {"draft", "scheduled"})
    taxonomy_options = _market_taxonomy_options(taxonomy_data)
    market_participants = _market_participants_context(token, market.get("slug") if market else slug)
    return render(
        request,
        "admin_ops/market_form.html",
        {
            "title": title,
            "mode": mode,
            "slug": slug,
            "form": form,
            "market": market,
            "preview": preview,
            "option_rows": option_rows,
            "taxonomy_options": taxonomy_options,
            "can_manual_close": can_manual_close,
            "can_publish": can_publish,
            "is_readonly": is_readonly,
            "market_participants": market_participants,
            "admin_error": error,
            "admin_message": message,
        },
    )


@admin_api_required
def resolution_action(request, action, slug=None):
    titles = {
        "resolve": "Resolver mercado",
        "cancel-refund": "Desfazer resolução",
        "audit": "Auditoria da resolução",
        "review": "Revisar mercado",
        "request-review": "Pedir revisão",
    }
    token = auth_token(request)
    error = ""
    market = None
    form = None
    if slug:
        try:
            market = admin_get_market(token, slug)
        except AuthAPIError as exc:
            error = str(exc)
    if action == "audit" and market:
        try:
            limit = min(100, max(1, int(request.GET.get("limit") or 10)))
            offset = max(0, int(request.GET.get("offset") or 0))
        except ValueError:
            limit = 10
            offset = 0
        audit_data = None
        if not error:
            try:
                audit_data = _audit_pagination(admin_get_market_resolution_audit(token, market["slug"], limit=limit, offset=offset))
            except AuthAPIError as exc:
                error = str(exc)
        return render(
            request,
            "admin_ops/resolution_audit.html",
            {
                "title": titles[action],
                "action": action,
                "slug": slug,
                "market": _market_resolution_meta(market),
                "audit": audit_data,
                "admin_error": error,
            },
        )
    if action == "resolve" and market:
        form = MarketResolutionForm(request.POST or None, market=market)
        if request.method == "POST" and form.is_valid():
            try:
                resolved = admin_resolve_market(
                    token,
                    market["slug"],
                    int(form.cleaned_data["winning_option_id"]),
                    form.cleaned_data.get("source_url") or "",
                    form.cleaned_data.get("note") or "",
                    form.cleaned_data.get("resolved_at"),
                    form.cleaned_data.get("resolution_timezone") or "",
                )
                messages.success(request, f"Mercado resolvido: {resolved['title']}")
                return redirect("admin-ops-resolution")
            except AuthAPIError as exc:
                error = str(exc)
        elif request.method == "POST":
            error = "Informe resultado e evidência da resolução."
    elif action == "cancel-refund" and market:
        if request.method == "POST":
            note = request.POST.get("note") or "Resolução cancelada pelo Admin Ops com refund operacional."
            try:
                canceled = admin_cancel_market(token, market["slug"], note)
                messages.success(request, f"Resolução desfeita: {canceled['title']}")
                return redirect("admin-ops-resolution")
            except AuthAPIError as exc:
                error = str(exc)
    return render(
        request,
        "admin_ops/resolution_action.html",
        {"title": titles[action], "action": action, "slug": slug, "market": market, "form": form, "admin_error": error},
    )


@admin_api_required
def queue_action(request, action, kind=None, item_id=None):
    titles = {
        "convert-draft": "Converter sugestão em rascunho",
        "reward-feedback": "Aprovar recompensa",
        "approve-recharge": "Aprovar recarga",
        "view-item": "Visualizar item da fila",
        "moderate": "Moderar item",
        "review": "Revisar item",
    }
    token = auth_token(request)
    error = ""
    message = ""
    item = None
    review_form = QueueReviewForm()
    reward_form = FeedbackRewardForm()
    recharge_form = WalletRechargeApprovalForm()
    recharge_reject_form = WalletRechargeRejectForm()
    if kind and item_id:
        try:
            if kind == "comment":
                comments = admin_get_comments(token).get("comments", [])
                item = next((_comment_queue_item(row) for row in comments if int(row.get("id")) == int(item_id)), None)
            else:
                queue_data = admin_get_queues(token, kind=kind)
                item = next((row for row in queue_data.get("items", []) if int(row.get("id")) == int(item_id)), None)
            if not item:
                error = "Item da fila não encontrado."
        except AuthAPIError as exc:
            error = str(exc)
    if item:
        review_form = QueueReviewForm(initial={"status": item.get("status", "pending"), "note": item.get("admin_note", "")})
        if kind == "comment":
            review_form.fields["status"].choices = (("visible", "Visível"), ("hidden", "Oculto"))
        reward_form = FeedbackRewardForm(initial={"amount_gtl": item.get("reward_gtl") or 50, "note": item.get("admin_note", "")})
        recharge_form = WalletRechargeApprovalForm(initial={"amount_gtl": item.get("reward_gtl") or 250, "note": item.get("admin_note", "")})
        recharge_reject_form = WalletRechargeRejectForm(initial={"note": item.get("admin_note", "")})
    if request.method == "POST" and item and not error:
        operation = request.POST.get("operation", "review")
        try:
            if kind == "wallet_recharge" and operation == "approve-recharge":
                recharge_form = WalletRechargeApprovalForm(request.POST)
                if item.get("status") != "pending":
                    error = "Solicitação de recarga já revisada."
                    raise AuthAPIError(error, 422)
                if recharge_form.is_valid():
                    admin_approve_wallet_recharge(
                        token,
                        item_id,
                        recharge_form.cleaned_data["amount_gtl"],
                        recharge_form.cleaned_data.get("note") or "",
                    )
                    messages.success(request, "Recarga educativa aprovada.")
                    return redirect("admin-ops-moderation")
                error = "Revise a recarga."
            elif kind == "wallet_recharge" and operation == "reject-recharge":
                recharge_reject_form = WalletRechargeRejectForm(request.POST)
                if item.get("status") != "pending":
                    error = "Solicitação de recarga já revisada."
                    raise AuthAPIError(error, 422)
                if recharge_reject_form.is_valid():
                    admin_reject_wallet_recharge(token, item_id, recharge_reject_form.cleaned_data["note"])
                    messages.success(request, "Recarga educativa rejeitada.")
                    return redirect("admin-ops-moderation")
                error = "Informe a nota operacional."
            elif kind == "comment":
                review_form = QueueReviewForm(request.POST)
                review_form.fields["status"].choices = (("visible", "Visível"), ("hidden", "Oculto"))
                if review_form.is_valid():
                    admin_moderate_comment(token, item_id, review_form.cleaned_data["status"], review_form.cleaned_data.get("note") or "")
                    messages.success(request, "Comentário moderado.")
                    return redirect("admin-ops-moderation")
                error = "Revise o status."
            elif operation == "convert-draft" and kind == "suggestion":
                if item.get("converted_market_slug"):
                    error = "Esta sugestão já foi convertida em rascunho."
                    raise AuthAPIError(error, 422)
                admin_convert_suggestion(token, item_id, request.POST.get("note") or "Convertida em rascunho pelo Admin Ops.")
                messages.success(request, "Sugestão convertida em rascunho.")
                return redirect("admin-ops-moderation")
            if operation == "reward" and kind == "feedback":
                reward_form = FeedbackRewardForm(request.POST)
                if item.get("reward_gtl"):
                    error = "Créditos já aprovados para este item."
                    raise AuthAPIError(error, 422)
                if reward_form.is_valid():
                    admin_reward_feedback(token, item_id, reward_form.cleaned_data["amount_gtl"], reward_form.cleaned_data.get("note") or "")
                    messages.success(request, "Feedback recompensado.")
                    return redirect("admin-ops-moderation")
                error = "Revise a recompensa."
            elif operation == "reward" and kind == "suggestion":
                reward_form = FeedbackRewardForm(request.POST)
                if item.get("reward_gtl"):
                    error = "Créditos já aprovados para este item."
                    raise AuthAPIError(error, 422)
                if reward_form.is_valid():
                    admin_reward_suggestion(token, item_id, reward_form.cleaned_data["amount_gtl"], reward_form.cleaned_data.get("note") or "")
                    messages.success(request, "Sugestão recompensada.")
                    return redirect("admin-ops-moderation")
                error = "Revise a recompensa."
            elif kind == "wallet_recharge":
                error = "Escolha aprovar ou rejeitar a recarga."
            else:
                review_form = QueueReviewForm(request.POST)
                if review_form.is_valid():
                    admin_review_queue_item(token, kind, item_id, review_form.cleaned_data["status"], review_form.cleaned_data.get("note") or "")
                    messages.success(request, "Item revisado.")
                    return redirect("admin-ops-moderation")
                error = "Revise o status."
        except AuthAPIError as exc:
            error = str(exc)
    return render(
        request,
        "admin_ops/queue_action.html",
        {
            "title": titles[action],
            "action": action,
            "kind": kind,
            "item_id": item_id,
            "item": item,
            "review_form": review_form,
            "reward_form": reward_form,
            "recharge_form": recharge_form,
            "recharge_reject_form": recharge_reject_form,
            "admin_message": message,
            "admin_error": error,
        },
    )


@admin_api_required
def category_action(request, action):
    token = auth_token(request)
    title_map = {
        "new": "Nova categoria",
        "edit": "Alterar categoria",
        "delete": "Excluir categoria",
        "badge-rules": "Regras de badge",
    }
    message = ""
    error = ""
    if request.method == "POST":
        category_slug = request.POST.get("category_slug", "")
        subcategory_slug = request.POST.get("subcategory_slug", "")
        if request.POST.get("kind") == "category":
            form = AdminCategoryForm(request.POST)
            if form.is_valid():
                try:
                    if action == "new":
                        admin_create_category(token, form.cleaned_data)
                    else:
                        admin_update_category(token, category_slug, form.cleaned_data)
                    message = "Taxonomia atualizada."
                except AuthAPIError as exc:
                    error = str(exc)
        elif request.POST.get("kind") == "subcategory":
            form = AdminSubcategoryForm(request.POST)
            if form.is_valid():
                try:
                    admin_update_subcategory(
                        token,
                        category_slug,
                        subcategory_slug,
                        {"name": form.cleaned_data["name"], "slug": form.cleaned_data.get("slug") or None},
                    )
                    message = "Subcategoria atualizada."
                except AuthAPIError as exc:
                    error = str(exc)
    try:
        taxonomy_data = admin_get_taxonomy(token)
    except AuthAPIError as exc:
        taxonomy_data = {"categories": []}
        error = error or str(exc)
    return render(
        request,
        "admin_ops/category_action.html",
        {
            "title": title_map[action],
            "action": action,
            "taxonomy": taxonomy_data,
            "category_form": AdminCategoryForm(),
            "subcategory_form": AdminSubcategoryForm(),
            "admin_message": message,
            "admin_error": error,
        },
    )
