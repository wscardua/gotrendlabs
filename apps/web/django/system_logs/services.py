import json
import os
import re
import threading
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address as parse_ip_address

from psycopg import errors

from apps.api.backend_api.db import get_connection


DEFAULT_RETENTION_DAYS = 90
MAX_TEXT_LENGTH = 8000
MAX_CONTEXT_LENGTH = 16000
SENSITIVE_KEY_RE = re.compile(
    r"(authorization|cookie|set-cookie|password|passwd|token|secret|csrf|session|api[_-]?key|access[_-]?key)",
    re.IGNORECASE,
)
_state = threading.local()
_retention_lock = threading.Lock()
_retention_cache = {"days": None, "until": 0.0}
_log_slot = threading.BoundedSemaphore(1)
_submit_slot = threading.BoundedSemaphore(1)


def _coerce_retention_days(value, default=DEFAULT_RETENTION_DAYS):
    try:
        days = int(value)
    except (TypeError, ValueError):
        return default
    return days if days > 0 else default


def _fallback_system_log_retention_days():
    try:
        from django.conf import settings

        if settings.configured:
            return _coerce_retention_days(getattr(settings, "SYSTEM_LOG_RETENTION_DAYS", DEFAULT_RETENTION_DAYS))
    except Exception:
        pass
    return _coerce_retention_days(os.environ.get("SYSTEM_LOG_RETENTION_DAYS"), DEFAULT_RETENTION_DAYS)


def get_system_log_retention_days():
    now = time.monotonic()
    if _retention_cache["until"] > now:
        return _retention_cache["days"]
    with _retention_lock:
        now = time.monotonic()
        if _retention_cache["until"] > now:
            return _retention_cache["days"]
        days = _fallback_system_log_retention_days()
        ttl = 5  # Avoid a connection storm if PostgreSQL is unavailable.
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT system_log_retention_days FROM gotrendlabs_site_config WHERE singleton_key = 1")
                    row = cursor.fetchone()
                    if row:
                        days = _coerce_retention_days(row["system_log_retention_days"], days)
                        ttl = 60
        except (errors.UndefinedTable, errors.UndefinedColumn):
            pass
        except Exception:
            pass
        _retention_cache.update(days=days, until=time.monotonic() + ttl)
        return days


def new_request_id():
    return uuid.uuid4().hex


def normalize_level(value):
    value = str(value or "INFO").upper()
    return value if value in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"} else "INFO"


def normalize_ip(value):
    value = (value or "").split(",")[0].strip()
    if not value:
        return None
    try:
        parse_ip_address(value)
    except ValueError:
        return None
    return value


def truncate_text(value, limit=MAX_TEXT_LENGTH):
    if value is None:
        return ""
    value = str(value)
    if len(value) <= limit:
        return value
    return f"{value[:limit]}...[truncated {len(value) - limit} chars]"


def redact_value(key, value):
    if SENSITIVE_KEY_RE.search(str(key or "")):
        return "[REDACTED]"
    if isinstance(value, str):
        return truncate_text(value, 1200)
    return value


def sanitize_context(value, depth=0):
    if depth > 6:
        return "[TRUNCATED_DEPTH]"
    if isinstance(value, dict):
        return {str(key)[:120]: sanitize_context(redact_value(key, item), depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        items = [sanitize_context(item, depth + 1) for item in value[:50]]
        if len(value) > 50:
            items.append(f"[TRUNCATED_LIST {len(value) - 50} items]")
        return items
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return truncate_text(value, 1200) if isinstance(value, str) else value
    return truncate_text(repr(value), 1200)


def compact_context(value):
    sanitized = sanitize_context(value or {})
    encoded = json.dumps(sanitized, ensure_ascii=True, default=str)
    if len(encoded) <= MAX_CONTEXT_LENGTH:
        return sanitized
    return {
        "truncated": True,
        "preview": encoded[:MAX_CONTEXT_LENGTH],
        "original_size": len(encoded),
    }


def exception_payload(exc):
    if not exc:
        return "", ""
    return exc.__class__.__name__[:160], truncate_text("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)), 20000)


def log_system_event(
    *,
    level="INFO",
    source="python",
    logger_name="",
    event_type="event",
    message="",
    request_id="",
    method="",
    path="",
    status_code=None,
    duration_ms=None,
    user_id=None,
    ip_address=None,
    user_agent="",
    exception_type="",
    stack_trace="",
    context=None,
    created_at=None,
):
    if getattr(_state, "writing", False):
        return None
    if not _log_slot.acquire(blocking=False):
        return None
    try:
        return _write_system_event(
            level=level, source=source, logger_name=logger_name, event_type=event_type,
            message=message, request_id=request_id, method=method, path=path,
            status_code=status_code, duration_ms=duration_ms, user_id=user_id,
            ip_address=ip_address, user_agent=user_agent, exception_type=exception_type,
            stack_trace=stack_trace, context=context, created_at=created_at,
        )
    finally:
        _log_slot.release()


def submit_system_event(**kwargs):
    """Best-effort technical logging without holding an HTTP response open."""
    if not _submit_slot.acquire(blocking=False):
        return None

    def write():
        try:
            log_system_event(**kwargs)
        finally:
            _submit_slot.release()

    try:
        threading.Thread(target=write, name="system-log", daemon=True).start()
    except RuntimeError:
        _submit_slot.release()
    return None


def _write_system_event(
    *, level, source, logger_name, event_type, message, request_id, method, path,
    status_code, duration_ms, user_id, ip_address, user_agent, exception_type,
    stack_trace, context, created_at,
):
    now = created_at or datetime.now(timezone.utc)
    expires_at = now + timedelta(days=get_system_log_retention_days())
    payload = (
        expires_at,
        normalize_level(level),
        str(source or "python")[:32],
        truncate_text(logger_name, 160),
        truncate_text(event_type or "event", 80),
        truncate_text(message, MAX_TEXT_LENGTH),
        truncate_text(request_id, 64),
        truncate_text(method, 12),
        truncate_text(path, 500),
        status_code,
        duration_ms,
        user_id,
        normalize_ip(ip_address),
        truncate_text(user_agent, 255),
        truncate_text(exception_type, 160),
        truncate_text(stack_trace, 20000),
        json.dumps(compact_context(context), ensure_ascii=True, default=str),
    )
    try:
        _state.writing = True
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_system_logs
                        (created_at, expires_at, level, source, logger_name, event_type, message,
                         request_id, method, path, status_code, duration_ms, user_id, ip_address,
                         user_agent, exception_type, stack_trace, context)
                    VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING id
                    """,
                    payload,
                )
                return cursor.fetchone()["id"]
    except (errors.UndefinedTable, errors.UndefinedColumn):
        return None
    except Exception:
        return None
    finally:
        _state.writing = False


def request_headers(headers):
    return {key: redact_value(key, value) for key, value in dict(headers or {}).items()}
