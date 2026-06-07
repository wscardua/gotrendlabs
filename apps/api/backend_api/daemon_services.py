from datetime import datetime, timedelta, timezone

from apps.api.backend_api.admin_events import record_admin_event
from apps.api.backend_api.agent_services import run_ai_agent_cycle
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.market_lifecycle_engine import MarketLifecycleEngine
from system_logs.services import DEFAULT_RETENTION_DAYS, log_system_event


AUTO_CLOSE_NOTE = "Fechamento automático pelo daemon."
AUTO_CANCEL_NO_HUMANS_NOTE = "Cancelamento automático pelo daemon: mercado sem participação humana."
DAEMON_LOGGER = "gotrendlabs.daemon"
DAEMON_HEARTBEAT_EVENT = "daemon.heartbeat"
DEFAULT_STALE_AFTER_MINUTES = 5
DEFAULT_MISSING_AFTER_MINUTES = 15
MAX_MARKET_SLUGS_IN_MESSAGE = 10


def _coerce_retention_days(value, default=DEFAULT_RETENTION_DAYS):
    try:
        days = int(value)
    except (TypeError, ValueError):
        return default
    return days if days > 0 else default


def _noop(*args, **kwargs):
    return None


def _record_wallet_entry(cursor, user_id, *, entry_type, amount, direction, description, reference_type="", reference_id="", created_by_id=None):
    now = datetime.now(timezone.utc)
    cursor.execute(
        """
        INSERT INTO gotrendlabs_wallet_ledger
            (user_id, entry_type, amount, direction, description, reference_type, reference_id, created_by_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (user_id, entry_type, amount, direction, description, reference_type, reference_id, created_by_id, now),
    )
    cursor.execute(
        """
        INSERT INTO gotrendlabs_wallet_balances (user_id, available_gtl, locked_gtl, total_earned_gtl, updated_at)
        VALUES (%s, 0, 0, 0, %s)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id, now),
    )
    if direction == "release":
        cursor.execute(
            """
            UPDATE gotrendlabs_wallet_balances
            SET available_gtl = available_gtl + %s,
                locked_gtl = GREATEST(locked_gtl - %s, 0),
                updated_at = %s
            WHERE user_id = %s
            """,
            (amount, amount, now, user_id),
        )


def _daemon_lifecycle_engine(cursor):
    return MarketLifecycleEngine(
        cursor,
        staff_id=None,
        record_wallet_entry=_record_wallet_entry,
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
                FROM gotrendlabs_markets
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
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT p.user_id) AS total
                    FROM gotrendlabs_predictions p
                    JOIN gotrendlabs_users u ON u.id = p.user_id
                    WHERE p.market_id = %s
                      AND p.status = 'open'
                      AND u.is_bot = false
                    """,
                    (market["id"],),
                )
                human_predictions = int(cursor.fetchone()["total"] or 0)
                if human_predictions == 0:
                    engine.cancel_market(market, market["slug"], AUTO_CANCEL_NO_HUMANS_NOTE)
                    continue
                engine.lock_market_automatically(market, market["slug"], AUTO_CLOSE_NOTE, now=now)
                locked.append({"id": market["id"], "slug": market["slug"], "close_at": market["close_at"].isoformat() if market["close_at"] else ""})
    return locked


def prune_expired_system_logs(now=None):
    now = now or datetime.now(timezone.utc)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            retention = _retention_config(cursor)["system_log_retention_days"]
            cursor.execute("DELETE FROM gotrendlabs_system_logs WHERE created_at < %s", (now - timedelta(days=retention),))
            return cursor.rowcount


def _retention_config(cursor):
    try:
        cursor.execute(
            """
            SELECT system_log_retention_days, ai_audit_retention_days
            FROM gotrendlabs_site_config
            WHERE singleton_key = 1
            """
        )
        row = cursor.fetchone()
    except Exception:
        row = None
    return {
        "system_log_retention_days": _coerce_retention_days(row["system_log_retention_days"] if row else None),
        "ai_audit_retention_days": _coerce_retention_days(row["ai_audit_retention_days"] if row else None),
    }


def prune_expired_ai_agent_actions(now=None):
    now = now or datetime.now(timezone.utc)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            retention = _retention_config(cursor)["ai_audit_retention_days"]
            cursor.execute("DELETE FROM gotrendlabs_ai_agent_actions WHERE created_at < %s", (now - timedelta(days=retention),))
            return cursor.rowcount


def prune_expired_operational_records(now=None):
    now = now or datetime.now(timezone.utc)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            retention = _retention_config(cursor)
            cursor.execute("DELETE FROM gotrendlabs_system_logs WHERE created_at < %s", (now - timedelta(days=retention["system_log_retention_days"]),))
            system_logs = cursor.rowcount
            cursor.execute("DELETE FROM gotrendlabs_ai_agent_actions WHERE created_at < %s", (now - timedelta(days=retention["ai_audit_retention_days"]),))
            ai_agent_actions = cursor.rowcount
    return {
        "system_logs": system_logs,
        "ai_agent_actions": ai_agent_actions,
        "total": system_logs + ai_agent_actions,
        **retention,
    }


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
    ai_summary = {
        "enabled": False,
        "comments_created": 0,
        "predictions_created": 0,
        "skipped": 0,
        "errors": 0,
        "reason": "not_run",
    }
    try:
        locked_markets = close_due_auto_markets(now=now)
        pruned_details = prune_expired_operational_records(now=now)
        pruned_logs = pruned_details["total"]
        from communications.services import process_due_email_deliveries

        email_summary = process_due_email_deliveries(now=now)
    except Exception as exc:
        log_daemon_event(
            "daemon.run_failed",
            f"Daemon operacional falhou: {exc.__class__.__name__}",
            level="ERROR",
            context={"error": str(exc), "error_type": exc.__class__.__name__},
        )
        raise
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                ai_summary = run_ai_agent_cycle(cursor, now=now)
    except Exception as exc:
        ai_summary = {
            "enabled": True,
            "comments_created": 0,
            "predictions_created": 0,
            "skipped": 0,
            "errors": 1,
            "reason": "cycle_exception",
        }
        log_daemon_event(
            "daemon.ai_cycle_failed",
            f"Ciclo IA falhou sem interromper daemon: {exc.__class__.__name__}",
            level="ERROR",
            context={"error": str(exc), "error_type": exc.__class__.__name__},
        )

    log_daemon_event(
        DAEMON_HEARTBEAT_EVENT,
        "Daemon operacional ativo.",
        context={
            "locked_markets": len(locked_markets),
            "pruned_logs": pruned_logs,
            "pruned_log_details": pruned_details,
            "ai": ai_summary,
            "email": email_summary,
        },
    )
    if locked_markets:
        log_daemon_event(
            "daemon.markets_locked",
            _locked_markets_message(locked_markets),
            context={"markets": locked_markets},
        )
    log_daemon_event(
        "daemon.logs_pruned",
        f"Daemon removeu {pruned_logs} registro(s) operacional(is) expirado(s).",
        context={"pruned_logs": pruned_logs, "pruned_log_details": pruned_details},
    )
    return {"locked_markets": locked_markets, "pruned_logs": pruned_logs, "pruned_log_details": pruned_details, "ai": ai_summary, "email": email_summary}


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
        FROM gotrendlabs_system_logs
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
        FROM gotrendlabs_system_logs
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
        FROM gotrendlabs_admin_events
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
