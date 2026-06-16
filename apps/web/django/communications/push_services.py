from datetime import timedelta
import base64
import json
import os
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
from django.conf import settings
from django.apps import apps
from django.db import transaction
from django.db.models import F, Q
from django.template import Context, Engine
from django.utils import timezone

if not apps.ready:
    django.setup()

from apps.web.django.communications.models import PushDelivery, PushTemplate
from apps.web.django.markets.models import UserNotification


IMMEDIATE_PUSH_EVENTS = {
    "market_resolved",
    "market_locked",
    "wallet_credit",
    "badge_awarded",
    "market_comment",
    "comment_like",
}
OFF_BY_DEFAULT_PUSH_EVENTS = {"market_prediction", "market_like"}
PUSH_SENDING_STALE_AFTER = timedelta(minutes=15)

DEFAULT_PUSH_TEMPLATES = {
    "market_resolved": {
        "title": "Resultado publicado",
        "body": "{{ market_title|default:\"Um mercado\" }} foi resolvido. Abra o app para ver o resultado.",
        "allowed_variables": ["market_title", "market_slug", "notification_id"],
    },
    "market_locked": {
        "title": "Mercado em apuração",
        "body": "{{ market_title|default:\"Um mercado\" }} fechou para novas previsões",
        "allowed_variables": ["market_title", "market_slug", "notification_id"],
    },
    "wallet_credit": {
        "title": "Carteira atualizada",
        "body": "Sua carteira educativa foi atualizada. Confira no app.",
        "allowed_variables": ["notification_id"],
    },
    "badge_awarded": {
        "title": "Nova badge",
        "body": "Você desbloqueou {{ badge_name|default:\"uma nova badge\" }}.",
        "allowed_variables": ["badge_code", "badge_name", "notification_id"],
    },
    "market_comment": {
        "title": "Novo comentário",
        "body": "{{ actor_handle|default:\"Alguém\" }} comentou em {{ market_title|default:\"um mercado\" }}",
        "allowed_variables": ["actor_handle", "market_title", "market_slug", "comment_id", "notification_id"],
    },
    "comment_like": {
        "title": "Curtida no comentário",
        "body": "{{ actor_handle|default:\"Alguém\" }} curtiu seu comentário.",
        "allowed_variables": ["actor_handle", "market_slug", "comment_id", "notification_id"],
    },
    "market_prediction": {
        "title": "Nova previsão no mercado",
        "body": "{{ actor_handle|default:\"Alguém\" }} fez uma previsão em {{ market_title|default:\"um mercado\" }}",
        "allowed_variables": ["actor_handle", "market_title", "market_slug", "notification_id"],
    },
    "market_like": {
        "title": "Mercado curtido",
        "body": "{{ actor_handle|default:\"Alguém\" }} curtiu {{ market_title|default:\"um mercado\" }}",
        "allowed_variables": ["actor_handle", "market_title", "market_slug", "notification_id"],
    },
}


def push_runtime_config():
    provider = (getattr(settings, "GOTRENDLABS_PUSH_PROVIDER", "none") or "none").strip().lower()
    if provider not in {"none", "fcm"}:
        provider = "none"
    return {
        "enabled": bool(getattr(settings, "GOTRENDLABS_PUSH_ENABLED", False)),
        "provider": provider,
        "dry_run": bool(getattr(settings, "GOTRENDLABS_PUSH_DRY_RUN", True)),
        "fcm_secret_configured": bool(getattr(settings, "GOTRENDLABS_FCM_CREDENTIALS_JSON", "")),
    }


def _fcm_credentials_payload():
    raw_value = (getattr(settings, "GOTRENDLABS_FCM_CREDENTIALS_JSON", "") or "").strip()
    if not raw_value:
        return {}
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        try:
            decoded = base64.b64decode(raw_value).decode("utf-8")
            return json.loads(decoded)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return {}


def _fcm_app():
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError as error:
        raise RuntimeError("firebase-admin dependency is not installed.") from error

    app_name = "gotrendlabs-push"
    try:
        return firebase_admin.get_app(app_name)
    except ValueError:
        payload = _fcm_credentials_payload()
        if not payload:
            raise RuntimeError("FCM credentials JSON is invalid.")
        return firebase_admin.initialize_app(credentials.Certificate(payload), name=app_name)


def _send_fcm_delivery(delivery):
    try:
        from firebase_admin import messaging
    except ImportError as error:
        raise RuntimeError("firebase-admin dependency is not installed.") from error

    app = _fcm_app()
    payload = {str(key): str(value) for key, value in (delivery.payload or {}).items() if value is not None}
    message = messaging.Message(
        token=delivery.device.token,
        notification=messaging.Notification(
            title=(delivery.title or "GoTrendLabs")[:120],
            body=delivery.body or "",
        ),
        data=payload,
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(channel_id="gtl_default"),
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound="default"),
            ),
        ),
    )
    return messaging.send(message, app=app)


def _is_fcm_invalid_token_error(error):
    code = (
        getattr(error, "code", "")
        or getattr(error, "error_code", "")
        or getattr(error, "detail", "")
        or error.__class__.__name__
    )
    text = f"{code} {error}".lower()
    invalid_markers = (
        "registration-token-not-registered",
        "unregistered",
        "invalid-registration-token",
        "sender-id-mismatch",
        "invalid token",
    )
    return any(marker in text for marker in invalid_markers)


def push_dashboard_status(cursor, *, now=None):
    now = now or timezone.now()
    since_24h = now - timedelta(hours=24)
    config = push_runtime_config()
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN is_active = true AND push_enabled = true AND revoked_at IS NULL AND provider_invalidated_at IS NULL THEN 1 ELSE 0 END), 0) AS active,
            COALESCE(SUM(CASE WHEN revoked_at IS NOT NULL THEN 1 ELSE 0 END), 0) AS revoked,
            COALESCE(SUM(CASE WHEN provider_invalidated_at IS NOT NULL THEN 1 ELSE 0 END), 0) AS invalidated
        FROM gotrendlabs_push_devices
        """
    )
    devices = cursor.fetchone()
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END), 0) AS queued,
            COALESCE(SUM(CASE WHEN status = 'queued' AND next_attempt_at <= %s THEN 1 ELSE 0 END), 0) AS due,
            COALESCE(SUM(CASE WHEN status = 'sending' THEN 1 ELSE 0 END), 0) AS sending,
            COALESCE(SUM(CASE WHEN status = 'sent' AND sent_at >= %s THEN 1 ELSE 0 END), 0) AS sent_24h,
            COALESCE(SUM(CASE WHEN status = 'dry_run' AND sent_at >= %s THEN 1 ELSE 0 END), 0) AS dry_run_24h,
            COALESCE(SUM(CASE WHEN status = 'failed' AND updated_at >= %s THEN 1 ELSE 0 END), 0) AS failed_24h,
            COALESCE(SUM(CASE WHEN status = 'invalid_token' AND updated_at >= %s THEN 1 ELSE 0 END), 0) AS invalid_token_24h,
            COALESCE(SUM(CASE WHEN status = 'suppressed' AND updated_at >= %s THEN 1 ELSE 0 END), 0) AS suppressed_24h,
            MAX(COALESCE(last_attempt_at, sent_at, created_at)) AS last_activity_at
        FROM gotrendlabs_push_deliveries
        """,
        (now, since_24h, since_24h, since_24h, since_24h, since_24h),
    )
    deliveries = cursor.fetchone()
    active_devices = int(devices["active"] or 0)
    queued = int(deliveries["queued"] or 0)
    due = int(deliveries["due"] or 0)
    failed_24h = int(deliveries["failed_24h"] or 0)
    invalid_token_24h = int(deliveries["invalid_token_24h"] or 0)
    if not config["enabled"]:
        status = "disabled"
        label = "Desligado"
        status_class = "warn"
    elif config["provider"] == "fcm" and not config["dry_run"] and not config["fcm_secret_configured"]:
        status = "misconfigured"
        label = "FCM sem segredo"
        status_class = "risk"
    elif failed_24h:
        status = "error"
        label = "Falhas recentes"
        status_class = "risk"
    elif due:
        status = "backlog"
        label = "Fila pendente"
        status_class = "warn"
    elif invalid_token_24h:
        status = "attention"
        label = "Tokens inválidos"
        status_class = "warn"
    elif config["dry_run"]:
        status = "dry_run"
        label = "Dry-run"
        status_class = "safe"
    else:
        status = "active"
        label = "Operacional"
        status_class = "safe"
    last_activity_at = deliveries["last_activity_at"]
    return {
        "status": status,
        "status_label": label,
        "status_class": status_class,
        "enabled": config["enabled"],
        "provider": config["provider"],
        "dry_run": config["dry_run"],
        "fcm_secret_configured": config["fcm_secret_configured"],
        "devices_total": int(devices["total"] or 0),
        "active_devices": active_devices,
        "revoked_devices": int(devices["revoked"] or 0),
        "invalidated_devices": int(devices["invalidated"] or 0),
        "deliveries_total": int(deliveries["total"] or 0),
        "queued": queued,
        "due": due,
        "sending": int(deliveries["sending"] or 0),
        "sent_24h": int(deliveries["sent_24h"] or 0),
        "dry_run_24h": int(deliveries["dry_run_24h"] or 0),
        "failed_24h": failed_24h,
        "invalid_token_24h": invalid_token_24h,
        "suppressed_24h": int(deliveries["suppressed_24h"] or 0),
        "last_activity_at": last_activity_at.isoformat() if last_activity_at else "",
    }


def default_policy_for_event(event_type):
    if event_type in IMMEDIATE_PUSH_EVENTS:
        mode = "immediate"
    elif event_type in OFF_BY_DEFAULT_PUSH_EVENTS:
        mode = "off"
    else:
        mode = "off"
    template = DEFAULT_PUSH_TEMPLATES.get(event_type, {"allowed_variables": []})
    return {
        "event_type": event_type,
        "mode": mode,
        "is_active": True,
        "default_user_enabled": True,
        "priority": 100,
        "template_key": event_type,
        "allowed_variables": template["allowed_variables"],
    }


def _json_value(value, fallback):
    if not value:
        return fallback
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def _row(cursor, query, params):
    cursor.execute(query, params)
    return cursor.fetchone()


def _notification_context(row):
    metadata = _json_value(row["metadata"], {})
    market_slug = row["market_slug"] or ""
    route = "/"
    if market_slug:
        route = f"/markets/{market_slug}"
        if row["event_type"] == "market_comment":
            route = f"{route}?tab=community"
    elif row["event_type"] == "wallet_credit":
        route = "/wallet"
    elif row["event_type"] == "badge_awarded":
        route = "/badges"
    context = {
        "notification_id": row["id"],
        "event_type": row["event_type"],
        "actor_handle": row["actor_handle"] or "",
        "market_slug": market_slug,
        "market_title": row["market_title"] or "",
        "comment_id": row["comment_id"],
        "badge_code": metadata.get("badge_code", ""),
        "badge_name": metadata.get("badge_name", ""),
        "route": route,
    }
    payload = {
        "notification_id": str(row["id"]),
        "event_type": row["event_type"],
        "route": route,
    }
    if market_slug:
        payload["market_slug"] = market_slug
    if row["comment_id"]:
        payload["comment_id"] = str(row["comment_id"])
    if context["badge_code"]:
        payload["badge_code"] = context["badge_code"]
    return context, payload


def _render_push(event_type, locale, context):
    locale = locale if locale in {"pt-br", "en"} else "pt-br"
    template = (
        PushTemplate.objects.filter(event_type=event_type, locale=locale, is_active=True).first()
        or PushTemplate.objects.filter(event_type=event_type, locale="pt-br", is_active=True).first()
    )
    default = DEFAULT_PUSH_TEMPLATES.get(event_type, {"title": "GoTrendLabs", "body": ""})
    title_source = template.title if template else default["title"]
    body_source = template.body if template else default["body"]
    engine = Engine(debug=False, string_if_invalid="")
    render_context = Context(context or {}, autoescape=True)
    return {
        "title": engine.from_string(title_source).render(render_context).strip(),
        "body": engine.from_string(body_source).render(render_context).strip(),
    }


def _event_policy(cursor, event_type):
    policy = _row(
        cursor,
        """
        SELECT event_type, mode, is_active, default_user_enabled, priority, template_key, allowed_variables
        FROM gotrendlabs_push_event_policies
        WHERE event_type = %s
        """,
        (event_type,),
    )
    if not policy:
        return default_policy_for_event(event_type)
    return {
        "event_type": policy["event_type"],
        "mode": policy["mode"],
        "is_active": bool(policy["is_active"]),
        "default_user_enabled": bool(policy["default_user_enabled"]),
        "priority": int(policy["priority"] or 100),
        "template_key": policy["template_key"] or policy["event_type"],
        "allowed_variables": _json_value(policy["allowed_variables"], []),
    }


def _push_allowed_for_user(cursor, user_id, event_type, policy):
    if not policy["is_active"] or policy["mode"] != "immediate":
        return False
    cursor.execute(
        """
        SELECT event_type, push_enabled
        FROM gotrendlabs_push_preferences
        WHERE user_id = %s AND event_type IN ('', %s)
        """,
        (user_id, event_type),
    )
    preferences = {row["event_type"]: bool(row["push_enabled"]) for row in cursor.fetchall()}
    if preferences.get("") is False:
        return False
    return preferences.get(event_type, policy["default_user_enabled"])


def enqueue_push_for_notification(cursor, notification_id):
    config = push_runtime_config()
    if not config["enabled"]:
        return {"queued": 0, "skipped": 1, "reason": "disabled"}
    notification = _row(
        cursor,
        """
        SELECT n.id, n.recipient_id, n.event_type, n.title, n.body, n.metadata, n.comment_id, n.created_at,
               u.preferred_language,
               actor.username AS actor_handle,
               m.slug AS market_slug,
               m.title AS market_title
        FROM gotrendlabs_user_notifications n
        JOIN gotrendlabs_users u ON u.id = n.recipient_id
        LEFT JOIN gotrendlabs_users actor ON actor.id = n.actor_id
        LEFT JOIN gotrendlabs_markets m ON m.id = n.market_id
        WHERE n.id = %s
          AND u.is_active = true
          AND u.account_status = 'active'
          AND u.is_bot = false
        """,
        (notification_id,),
    )
    if not notification:
        return {"queued": 0, "skipped": 1, "reason": "notification_not_found"}
    policy = _event_policy(cursor, notification["event_type"])
    if not _push_allowed_for_user(cursor, notification["recipient_id"], notification["event_type"], policy):
        return {"queued": 0, "skipped": 1, "reason": policy["mode"]}
    cursor.execute(
        """
        SELECT id, provider, platform
        FROM gotrendlabs_push_devices
        WHERE user_id = %s
          AND is_active = true
          AND push_enabled = true
          AND revoked_at IS NULL
          AND provider_invalidated_at IS NULL
        ORDER BY last_registered_at DESC, id DESC
        """,
        (notification["recipient_id"],),
    )
    devices = cursor.fetchall()
    if not devices:
        return {"queued": 0, "skipped": 1, "reason": "no_devices"}
    context, payload = _notification_context(notification)
    rendered = _render_push(notification["event_type"], notification["preferred_language"], context)
    now = timezone.now()
    queued = 0
    for device in devices:
        cursor.execute(
            """
            INSERT INTO gotrendlabs_push_deliveries
                (notification_id, device_id, event_type, provider, template_key, title, body, payload, policy_snapshot,
                 idempotency_key, status, attempt_count, max_attempts, next_attempt_at, last_attempt_at, sent_at,
                 last_error, provider_message_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, 'queued', 0, 3, %s, NULL, NULL, '', '', %s, %s)
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING id
            """,
            (
                notification["id"],
                device["id"],
                notification["event_type"],
                device["provider"],
                policy["template_key"],
                rendered["title"],
                rendered["body"],
                json.dumps(payload),
                json.dumps(policy),
                f"push:{notification['id']}:{device['id']}",
                now,
                now,
                now,
            ),
        )
        if cursor.fetchone():
            queued += 1
    return {"queued": queued, "skipped": 0, "reason": ""}


def _mark_delivery(delivery, *, status, now, error="", provider_message_id=""):
    delivery.status = status
    delivery.last_attempt_at = now
    delivery.attempt_count += 1
    delivery.last_error = error
    if provider_message_id:
        delivery.provider_message_id = provider_message_id
    if status in {"sent", "dry_run"}:
        delivery.sent_at = now
    if status == "failed":
        delay_minutes = min(60, 5 * max(1, delivery.attempt_count))
        delivery.next_attempt_at = now + timedelta(minutes=delay_minutes)
    delivery.save()


def create_test_push_delivery(*, device, event_type="admin_push_test", title="Teste de push", body="Mensagem de teste do GoTrendLabs."):
    now = timezone.now()
    notification = UserNotification.objects.create(
        recipient=device.user,
        event_type=event_type,
        source_key=f"admin_push_test:{device.id}:{uuid.uuid4().hex}",
        title=title,
        body=body,
        metadata={"admin_test": True},
        created_at=now,
    )
    payload = {
        "notification_id": str(notification.id),
        "event_type": event_type,
        "route": "/alerts",
    }
    policy_snapshot = {
        "event_type": event_type,
        "mode": "test",
        "is_active": True,
        "default_user_enabled": False,
        "template_key": event_type,
        "allowed_variables": ["notification_id", "event_type", "route"],
        "admin_test": True,
    }
    delivery = PushDelivery.objects.create(
        notification=notification,
        device=device,
        event_type=event_type,
        provider=device.provider,
        template_key=event_type,
        title=title,
        body=body,
        payload=payload,
        policy_snapshot=policy_snapshot,
        idempotency_key=f"push-test:{notification.id}:{device.id}",
        status="queued",
        next_attempt_at=now,
    )
    return delivery


def _invalidate_device(delivery, now, reason):
    delivery.device.is_active = False
    delivery.device.push_enabled = False
    delivery.device.provider_invalidated_at = now
    delivery.device.disabled_reason = reason
    delivery.device.save(update_fields=["is_active", "push_enabled", "provider_invalidated_at", "disabled_reason", "updated_at"])


def _claim_due_push_deliveries(*, limit, now):
    stale_before = now - PUSH_SENDING_STALE_AFTER
    due_filter = (
        Q(status__in=["queued", "failed"], next_attempt_at__lte=now)
        | Q(status="sending", last_attempt_at__lte=stale_before)
        | Q(status="sending", last_attempt_at__isnull=True)
    )
    with transaction.atomic():
        deliveries = list(
            PushDelivery.objects.select_for_update(skip_locked=True)
            .select_related("device")
            .filter(due_filter, attempt_count__lt=F("max_attempts"))
            .order_by("next_attempt_at", "id")[:limit]
        )
        for delivery in deliveries:
            delivery.status = "sending"
            delivery.last_attempt_at = now
            delivery.save(update_fields=["status", "last_attempt_at", "updated_at"])
    return deliveries


def process_due_push_deliveries(*, limit=25, now=None):
    now = now or timezone.now()
    config = push_runtime_config()
    stats = {"sent": 0, "failed": 0, "suppressed": 0, "dry_run": 0, "invalid_token": 0, "skipped": 0}
    deliveries = _claim_due_push_deliveries(limit=limit, now=now)
    for delivery in deliveries:
        if not config["enabled"]:
            _mark_delivery(delivery, status="suppressed", now=now, error="Push disabled by environment.")
            stats["suppressed"] += 1
            continue
        if not delivery.device.is_active or not delivery.device.push_enabled:
            _mark_delivery(delivery, status="suppressed", now=now, error="Push device is inactive.")
            stats["suppressed"] += 1
            continue
        if config["provider"] == "none":
            _mark_delivery(delivery, status="dry_run", now=now, provider_message_id=f"dry-run-{delivery.id}")
            stats["dry_run"] += 1
            continue
        if config["provider"] == "fcm" and config["dry_run"]:
            _mark_delivery(delivery, status="dry_run", now=now, provider_message_id=f"fcm-dry-run-{delivery.id}")
            stats["dry_run"] += 1
            continue
        if delivery.device.token.strip().lower().startswith("invalid"):
            _invalidate_device(delivery, now, "provider_invalid_token")
            _mark_delivery(delivery, status="invalid_token", now=now, error="Provider rejected device token.")
            stats["invalid_token"] += 1
            continue
        if config["provider"] == "fcm" and not config["fcm_secret_configured"]:
            _mark_delivery(delivery, status="failed", now=now, error="FCM credentials are not configured.")
            stats["failed"] += 1
            continue
        try:
            provider_message_id = _send_fcm_delivery(delivery)
        except Exception as error:
            if _is_fcm_invalid_token_error(error):
                _invalidate_device(delivery, now, "provider_invalid_token")
                _mark_delivery(delivery, status="invalid_token", now=now, error="Provider rejected device token.")
                stats["invalid_token"] += 1
            else:
                _mark_delivery(delivery, status="failed", now=now, error=str(error)[:500])
                stats["failed"] += 1
            continue
        _mark_delivery(delivery, status="sent", now=now, provider_message_id=provider_message_id)
        stats["sent"] += 1
    if not deliveries:
        stats["skipped"] += 1
    return stats
