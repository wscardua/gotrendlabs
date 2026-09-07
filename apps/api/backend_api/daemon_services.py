from datetime import datetime, timedelta, timezone
import hashlib

from apps.api.backend_api.admin_events import record_admin_event
from apps.api.backend_api.agent_services import run_ai_agent_cycle
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.market_lifecycle_engine import MarketLifecycleEngine
from apps.api.backend_api.integrity_service import (
    IntegritySigningError,
    audit_integrity_ledger,
    seal_market,
    verify_market_integrity_records,
)
from apps.web.django.system_logs.services import DEFAULT_RETENTION_DAYS, log_system_event


AUTO_CLOSE_NOTE = "Fechamento automático pelo daemon."
AUTO_CANCEL_NO_HUMANS_NOTE = "Cancelamento automático pelo daemon: mercado sem participação humana."
DAEMON_LOGGER = "gotrendlabs.daemon"
DAEMON_HEARTBEAT_EVENT = "daemon.heartbeat"
DEFAULT_STALE_AFTER_MINUTES = 5
DEFAULT_MISSING_AFTER_MINUTES = 15
MAX_MARKET_SLUGS_IN_MESSAGE = 10

INTEGRITY_ISSUE_LABELS = {
    "definition_invalid": ("Assinatura da definição não confere", "A definição registrada falhou na validação de hash ou assinatura."),
    "definition_changed": ("Definição publicada foi alterada", "A definição operacional atual diverge do registro assinado na publicação."),
    "prediction_commitment_invalid": ("Comprovante de previsão não confere", "Um ou mais compromissos de previsão falharam na validação ou no encadeamento."),
    "prediction_commitment_missing": ("Previsão sem comprovante", "Uma ou mais previsões persistidas não possuem compromisso de integridade correspondente."),
    "seal_invalid": ("Seal final não confere", "O Seal armazenado falhou na validação de conteúdo, referência ou assinatura."),
    "result_changed": ("Resultado registrado foi alterado", "O resultado operacional atual diverge do resultado protegido pelo ledger."),
    "merkle_invalid": ("Histórico Merkle não confere", "A raiz ou uma prova Merkle não corresponde aos compromissos registrados."),
    "market_events_invalid": ("Evento do mercado rompeu o ledger", "Um evento associado ao mercado falhou na validação da cadeia assinada."),
    "verification_exception": ("Verificação de integridade falhou", "A auditoria encontrou um registro inválido que não pôde ser interpretado com segurança."),
    "ledger_chain_invalid": ("Cadeia global do ledger não confere", "A sequência, o elo, o conteúdo ou a assinatura de um evento global falhou na validação."),
    "checkpoint_invalid": ("Checkpoint do ledger não confere", "O checkpoint assinado mais recente falhou na validação criptográfica ou no encadeamento."),
    "checkpoint_boundary_invalid": ("Limite do checkpoint não confere", "O evento usado como limite pelo checkpoint não corresponde ao ledger persistido."),
    "ledger_head_changed": ("Cabeça do ledger foi alterada", "O último evento já auditado não corresponde ao checkpoint assinado."),
    "ledger_head_regressed": ("Ledger perdeu eventos auditados", "A sequência atual do ledger é anterior ao checkpoint assinado mais recente."),
}


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


def seal_due_markets(now=None):
    now = now or datetime.now(timezone.utc)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM gotrendlabs_markets WHERE status='resolved' AND seal_due_at IS NOT NULL AND seal_due_at<=%s ORDER BY seal_due_at,id", (now,))
            candidate_ids = [row["id"] for row in cursor.fetchall()]
    sealed, failed = [], []
    for market_id in candidate_ids:
        market_slug = str(market_id)
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM gotrendlabs_markets WHERE id=%s AND status='resolved' FOR UPDATE SKIP LOCKED", (market_id,))
                    market = cursor.fetchone()
                    if not market:
                        continue
                    market_slug = market["slug"]
                    _seal, created = seal_market(cursor, market, sealed_at=now)
                    if created:
                        sealed.append({"id": market["id"], "slug": market["slug"], "sealed_at": now.isoformat()})
        except Exception as exc:
            failed.append({"id": market_id, "error_type": exc.__class__.__name__})
            log_daemon_event("daemon.market_seal_failed", "Selagem de mercado falhou; mercado permaneceu resolvido.", level="ERROR", context={"market_id": market_id, "error_type": exc.__class__.__name__})
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    record_admin_event(cursor, None, "integrity.seal_failed", "market", market_slug, f"Falha segura de selagem: {exc.__class__.__name__}")
    return {"sealed": sealed, "failed": failed}


def _enqueue_integrity_alert(cursor, *, issue_code, market, now):
    scope = market["slug"] if market else "global"
    dedupe_key = hashlib.sha256(f"{scope}:{issue_code}".encode("utf-8")).hexdigest()
    title, description = INTEGRITY_ISSUE_LABELS.get(
        issue_code,
        INTEGRITY_ISSUE_LABELS["verification_exception"],
    )
    cursor.execute(
        """INSERT INTO gotrendlabs_integrity_alerts
           (market_id,dedupe_key,issue_code,title,description,severity,status,occurrences,
            first_detected_at,last_detected_at,admin_note,reviewed_by_id,reviewed_at,created_at,updated_at)
           VALUES (%s,%s,%s,%s,%s,'high','pending',1,%s,%s,'',NULL,NULL,%s,%s)
           ON CONFLICT (dedupe_key) DO NOTHING
           RETURNING id""",
        (market["id"] if market else None, dedupe_key, issue_code, title, description, now, now, now, now),
    )
    created = cursor.fetchone()
    if created:
        record_admin_event(
            cursor,
            None,
            "integrity.alert_created",
            "market" if market else "integrity_ledger",
            scope,
            f"Alerta alto criado pelo daemon: {issue_code}.",
        )
        return True
    cursor.execute(
        """UPDATE gotrendlabs_integrity_alerts
           SET status='pending',severity='high',occurrences=occurrences+1,last_detected_at=%s,
               reviewed_by_id=NULL,reviewed_at=NULL,updated_at=%s
           WHERE dedupe_key=%s""",
        (now, now, dedupe_key),
    )
    return False


def audit_integrity_records(now=None):
    now = now or datetime.now(timezone.utc)
    summary = {
        "available": True,
        "ledger_status": "unavailable",
        "markets_scanned": 0,
        "issues_detected": 0,
        "alerts_created": 0,
        "scan_failures": 0,
    }
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                ledger_audit = audit_integrity_ledger(cursor, now=now)
                summary["ledger_status"] = ledger_audit["status"]
                if ledger_audit["status"] == "failed":
                    issue_code = ledger_audit.get("issue_code") or "ledger_chain_invalid"
                    summary["issues_detected"] += 1
                    summary["alerts_created"] += int(
                        _enqueue_integrity_alert(cursor, issue_code=issue_code, market=None, now=now)
                    )
                cursor.execute(
                    "SELECT m.* FROM gotrendlabs_markets m ORDER BY m.id"
                )
                markets = cursor.fetchall()
                for market in markets:
                    summary["markets_scanned"] += 1
                    try:
                        verification = verify_market_integrity_records(cursor, market, ledger_audit=ledger_audit)
                        issue_codes = verification["errors"]
                    except IntegritySigningError:
                        summary["scan_failures"] += 1
                        continue
                    except (KeyError, TypeError, ValueError):
                        issue_codes = ["verification_exception"]
                    for issue_code in issue_codes:
                        summary["issues_detected"] += 1
                        summary["alerts_created"] += int(
                            _enqueue_integrity_alert(cursor, issue_code=issue_code, market=market, now=now)
                        )
    except Exception as exc:
        summary["available"] = False
        summary["scan_failures"] += 1
        log_daemon_event(
            "daemon.integrity_audit_unavailable",
            "Auditoria de integridade ficou indisponível neste ciclo; nenhum alerta criptográfico foi inferido.",
            level="ERROR",
            context={"error_type": exc.__class__.__name__},
        )
    if summary["scan_failures"] and summary["markets_scanned"]:
        log_daemon_event(
            "daemon.integrity_audit_partial",
            "Auditoria de integridade não conseguiu verificar todos os mercados neste ciclo.",
            level="ERROR",
            context=summary,
        )
    if summary["issues_detected"]:
        log_daemon_event(
            "daemon.integrity_issues_detected",
            f"Auditoria detectou {summary['issues_detected']} problema(s) de integridade.",
            level="ERROR",
            context=summary,
        )
    return summary


def _run_isolated_task(task_name, operation, *, fallback):
    try:
        return operation()
    except Exception as exc:
        log_daemon_event(
            f"daemon.{task_name}_failed",
            f"Tarefa isolada do daemon falhou: {task_name} ({exc.__class__.__name__}).",
            level="ERROR",
            context={"error": str(exc), "error_type": exc.__class__.__name__, "task": task_name},
        )
        return fallback


def _process_due_email(now):
    from apps.web.django.communications.services import process_due_email_deliveries

    return process_due_email_deliveries(now=now)


def _process_due_push(now):
    from apps.web.django.communications.push_services import process_due_push_deliveries

    return process_due_push_deliveries(now=now)


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
    integrity_audit_summary = _run_isolated_task(
        "integrity_audit",
        lambda: audit_integrity_records(now=now),
        fallback={"available": False, "ledger_status": "unavailable", "markets_scanned": 0, "issues_detected": 0, "alerts_created": 0, "scan_failures": 1},
    )
    locked_markets = _run_isolated_task("market_close", lambda: close_due_auto_markets(now=now), fallback=[])
    if integrity_audit_summary.get("available", True) and integrity_audit_summary.get("ledger_status") != "failed":
        seal_summary = _run_isolated_task(
            "market_seal",
            lambda: seal_due_markets(now=now),
            fallback={"sealed": [], "failed": [{"error_type": "TaskFailure"}]},
        )
    else:
        skipped_reason = (
            "integrity_ledger_failed"
            if integrity_audit_summary.get("ledger_status") == "failed"
            else "integrity_audit_unavailable"
        )
        seal_summary = {"sealed": [], "failed": [], "skipped_reason": skipped_reason}
        log_daemon_event(
            "daemon.market_seal_suppressed",
            "Selagem foi adiada porque a auditoria global nao aprovou a cadeia neste ciclo.",
            level="ERROR",
            context={"reason": skipped_reason},
        )
    pruned_details = _run_isolated_task(
        "retention",
        lambda: prune_expired_operational_records(now=now),
        fallback={"system_logs": 0, "ai_agent_actions": 0, "total": 0},
    )
    pruned_logs = pruned_details["total"]
    email_summary = _run_isolated_task("email", lambda: _process_due_email(now), fallback={"sent": 0, "failed": 1})
    push_summary = _run_isolated_task("push", lambda: _process_due_push(now), fallback={"sent": 0, "failed": 1})
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
            "push": push_summary,
            "integrity_seals": seal_summary,
            "integrity_audit": integrity_audit_summary,
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
    return {
        "locked_markets": locked_markets,
        "pruned_logs": pruned_logs,
        "pruned_log_details": pruned_details,
        "ai": ai_summary,
        "email": email_summary,
        "push": push_summary,
        "integrity_seals": seal_summary,
        "integrity_audit": integrity_audit_summary,
    }


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
