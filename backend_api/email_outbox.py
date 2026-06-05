from datetime import datetime, timedelta, timezone
import json
import os

from backend_api.security import hash_token, issue_token


EMAIL_CONFIRMATION_TTL = timedelta(hours=48)
PASSWORD_RESET_TEMPLATE_KEY = "account.password_reset"
EMAIL_CONFIRMATION_TEMPLATE_KEY = "user.email_confirmation"


def public_url(path):
    base_url = os.environ.get("GOTRENDLABS_PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    return f"{base_url}/{path.lstrip('/')}"


def enqueue_email(cursor, *, event_type, user_id, recipient_email, template_key, locale, context, idempotency_key, next_attempt_at=None):
    if not recipient_email:
        return None
    now = datetime.now(timezone.utc)
    cursor.execute(
        """
        INSERT INTO gotrendlabs_email_deliveries
            (event_type, recipient_user_id, recipient_email, template_key, locale, subject, body_text, body_html,
             context, idempotency_key, status, attempt_count, max_attempts, next_attempt_at, last_attempt_at,
             sent_at, last_error, provider_message_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, '', '', '', %s::jsonb, %s, 'queued', 0, 3, %s, NULL, NULL, '', '', %s, %s)
        ON CONFLICT (idempotency_key) DO NOTHING
        RETURNING id
        """,
        (
            event_type,
            user_id,
            recipient_email.lower(),
            template_key,
            locale if locale in {"pt-br", "en"} else "pt-br",
            json.dumps(context or {}),
            idempotency_key,
            next_attempt_at or now,
            now,
            now,
        ),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return row["id"] if isinstance(row, dict) else row[0]


def user_email_context(cursor, user_id):
    cursor.execute(
        """
        SELECT id, email, first_name, username, preferred_language
        FROM gotrendlabs_users
        WHERE id = %s
          AND is_active = true
          AND account_status = 'active'
          AND is_bot = false
        """,
        (user_id,),
    )
    user = cursor.fetchone()
    if not user:
        return None
    def value(key, index):
        return user[key] if isinstance(user, dict) else user[index]

    preferred_language = value("preferred_language", 4)
    return {
        "id": value("id", 0),
        "email": value("email", 1),
        "display_name": value("first_name", 2) or value("username", 3),
        "locale": preferred_language if preferred_language in {"pt-br", "en"} else "pt-br",
    }


def enqueue_user_email(cursor, *, event_type, user_id, template_key, context, idempotency_key):
    user = user_email_context(cursor, user_id)
    if not user:
        return None
    return enqueue_email(
        cursor,
        event_type=event_type,
        user_id=user["id"],
        recipient_email=user["email"],
        template_key=template_key,
        locale=user["locale"],
        context={"display_name": user["display_name"], **(context or {})},
        idempotency_key=idempotency_key,
    )


def issue_email_confirmation(cursor, user, *, ip_address=None, user_agent=""):
    token = issue_token()
    now = datetime.now(timezone.utc)
    cursor.execute(
        """
        UPDATE gotrendlabs_email_confirmation_tokens
        SET used_at = %s
        WHERE user_id = %s AND used_at IS NULL
        """,
        (now, user["id"]),
    )
    cursor.execute(
        """
        INSERT INTO gotrendlabs_email_confirmation_tokens
            (user_id, token_hash, created_at, expires_at, used_at, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, NULL, %s, %s)
        RETURNING id
        """,
        (user["id"], hash_token(token), now, now + EMAIL_CONFIRMATION_TTL, ip_address, user_agent),
    )
    token_id = cursor.fetchone()["id"]
    confirmation_url = public_url(f"email-confirm/confirm/{token}/")
    enqueue_email(
        cursor,
        event_type=EMAIL_CONFIRMATION_TEMPLATE_KEY,
        user_id=user["id"],
        recipient_email=user["email"],
        template_key=EMAIL_CONFIRMATION_TEMPLATE_KEY,
        locale=user["preferred_language"] if user["preferred_language"] in {"pt-br", "en"} else "pt-br",
        context={
            "display_name": user["first_name"] or user["username"],
            "confirmation_url": confirmation_url,
            "expires_hours": int(EMAIL_CONFIRMATION_TTL.total_seconds() // 3600),
        },
        idempotency_key=f"user.email_confirmation:{user['id']}:{token_id}",
    )
    return confirmation_url


def enqueue_password_reset_email(cursor, user, reset_url):
    return enqueue_email(
        cursor,
        event_type=PASSWORD_RESET_TEMPLATE_KEY,
        user_id=user["id"],
        recipient_email=user["email"],
        template_key=PASSWORD_RESET_TEMPLATE_KEY,
        locale=user.get("preferred_language") if user.get("preferred_language") in {"pt-br", "en"} else "pt-br",
        context={
            "display_name": user.get("first_name") or user.get("username") or user["email"],
            "reset_url": reset_url,
            "expires_minutes": 60,
        },
        idempotency_key=f"account.password_reset:{user['id']}:{hash_token(reset_url)[0:24]}",
    )
