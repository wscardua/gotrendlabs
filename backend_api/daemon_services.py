from datetime import datetime, timedelta, timezone

from backend_api.admin_events import record_admin_event
from backend_api.db import get_connection
from backend_api.market_lifecycle_engine import MarketLifecycleEngine
from system_logs.services import log_system_event


AUTO_CLOSE_NOTE = "Fechamento automático pelo daemon."
DAEMON_LOGGER = "orynth.daemon"
DAEMON_HEARTBEAT_EVENT = "daemon.heartbeat"
DEFAULT_STALE_AFTER_MINUTES = 5
DEFAULT_MISSING_AFTER_MINUTES = 15
MAX_MARKET_SLUGS_IN_MESSAGE = 10


def _noop(*args, **kwargs):
    return None


def _daemon_lifecycle_engine(cursor):
    return MarketLifecycleEngine(
        cursor,
        staff_id=None,
        record_wallet_entry=_noop,
        record_admin_event=record_admin_event,
        ensure_user_core=_noop,
        validate_publishable=_noop,
    )


def close_due_auto_markets(now=None):
    now = now or datetime.now(timezone.utc)
    locked = []
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM orynth_markets
                WHERE status IN ('open', 'scheduled')
                  AND auto_close_enabled = true
                  AND close_at IS NOT NULL
                  AND close_at <= %s
                ORDER BY close_at ASC, id ASC
                FOR UPDATE SKIP LOCKED
                """,
                (now,),
            )
            markets = cursor.fetchall()
            engine = _daemon_lifecycle_engine(cursor)
            for market in markets:
                engine.lock_market_automatically(market, market["slug"], AUTO_CLOSE_NOTE, now=now)
                locked.append({"id": market["id"], "slug": market["slug"], "close_at": market["close_at"].isoformat() if market["close_at"] else ""})
    return locked


def prune_expired_system_logs(now=None):
    now = now or datetime.now(timezone.utc)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM orynth_system_logs WHERE expires_at < %s", (now,))
            return cursor.rowcount


def log_daemon_event(event_type, message, *, level="INFO", context=None, created_at=None):
    return log_system_event(
        level=level,
        source="python",
        logger_name=DAEMON_LOGGER,
        event_type=event_type,
        message=message,
        context=context or {},
        created_at=created_at,
    )


def _locked_markets_message(locked_markets):
    slugs = [market["slug"] for market in locked_markets]
    preview = ", ".join(slugs[:MAX_MARKET_SLUGS_IN_MESSAGE])
    if len(slugs) <= MAX_MARKET_SLUGS_IN_MESSAGE:
        return f"Daemon fechou {len(slugs)} mercado(s) automaticamente: {preview}."
    remaining = len(slugs) - MAX_MARKET_SLUGS_IN_MESSAGE
    return f"Daemon fechou {len(slugs)} mercado(s) automaticamente. Primeiros: {preview}. Mais {remaining} no detalhe do log."


def run_daemon_cycle(now=None):
    now = now or datetime.now(timezone.utc)
    log_daemon_event("daemon.run_started", "Daemon operacional iniciou ciclo.", context={"started_at": now.isoformat()}, created_at=now)
    try:
        locked_markets = close_due_auto_markets(now=now)
        pruned_logs = prune_expired_system_logs(now=now)
    except Exception as exc:
        log_daemon_event(
            "daemon.run_failed",
            f"Daemon operacional falhou: {exc.__class__.__name__}",
            level="ERROR",
            context={"error": str(exc), "error_type": exc.__class__.__name__},
        )
        raise

    log_daemon_event(
        DAEMON_HEARTBEAT_EVENT,
        "Daemon operacional ativo.",
        context={"locked_markets": len(locked_markets), "pruned_logs": pruned_logs},
    )
    if locked_markets:
        log_daemon_event(
            "daemon.markets_locked",
            _locked_markets_message(locked_markets),
            context={"markets": locked_markets},
        )
    log_daemon_event("daemon.logs_pruned", f"Daemon removeu {pruned_logs} log(s) expirado(s).", context={"pruned_logs": pruned_logs})
    return {"locked_markets": locked_markets, "pruned_logs": pruned_logs}


def daemon_dashboard_status(
    cursor,
    *,
    now=None,
    stale_after_minutes=DEFAULT_STALE_AFTER_MINUTES,
    missing_after_minutes=DEFAULT_MISSING_AFTER_MINUTES,
):
    now = now or datetime.now(timezone.utc)
    stale_after = now - timedelta(minutes=stale_after_minutes)
    missing_after = now - timedelta(minutes=missing_after_minutes)
    cursor.execute(
        """
        SELECT created_at, context
        FROM orynth_system_logs
        WHERE logger_name = %s
          AND event_type = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (DAEMON_LOGGER, DAEMON_HEARTBEAT_EVENT),
    )
    heartbeat = cursor.fetchone()
    cursor.execute(
        """
        SELECT created_at
        FROM orynth_system_logs
        WHERE logger_name = %s
          AND event_type = 'daemon.run_failed'
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (DAEMON_LOGGER,),
    )
    error = cursor.fetchone()
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM orynth_admin_events
        WHERE action = 'market.lock'
          AND actor_id IS NULL
          AND note = %s
          AND created_at >= %s
        """,
        (AUTO_CLOSE_NOTE, now - timedelta(hours=24)),
    )
    locked_24h = int(cursor.fetchone()["total"] or 0)
    if not heartbeat:
        status = "missing"
        label = "Sem sinal"
        last_seen_at = ""
        last_success_at = ""
    else:
        last_seen = heartbeat["created_at"]
        if last_seen >= stale_after:
            status = "active"
            label = "Ativo"
        elif last_seen >= missing_after:
            status = "stale"
            label = "Atrasado"
        else:
            status = "missing"
            label = "Sem sinal"
        last_seen_at = last_seen.isoformat()
        last_success_at = last_seen.isoformat()
    return {
        "daemon_status": status,
        "daemon_status_label": label,
        "daemon_last_seen_at": last_seen_at,
        "daemon_last_success_at": last_success_at,
        "daemon_last_error_at": error["created_at"].isoformat() if error and error["created_at"] else "",
        "daemon_locked_markets_24h": locked_24h,
        "daemon_stale_after_minutes": stale_after_minutes,
        "daemon_missing_after_minutes": missing_after_minutes,
    }
