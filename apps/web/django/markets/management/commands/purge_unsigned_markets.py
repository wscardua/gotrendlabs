import json

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from psycopg.rows import dict_row

from apps.api.backend_api.badge_engine import BadgeAwardEngine
from apps.api.backend_api.daemon_services import _daemon_lifecycle_engine
from apps.web.django.markets.models import Market


LEGACY_STATES = ("open", "locked", "resolved", "sealed", "canceled")


class Command(BaseCommand):
    help = "Inventory or remove pre-production markets that reached publication states without an integrity definition."

    def add_arguments(self, parser):
        parser.add_argument("--execute", action="store_true", help="Apply the purge. Without this flag the command is read-only.")
        parser.add_argument(
            "--backup-confirmed",
            action="store_true",
            help="Required with --execute to confirm that an external PostgreSQL backup was created.",
        )

    def handle(self, *args, **options):
        execute = bool(options["execute"])
        if execute and not options["backup_confirmed"]:
            raise CommandError("Use --backup-confirmed somente depois de criar e validar um backup PostgreSQL externo.")

        candidates = list(
            Market.objects.filter(status__in=LEGACY_STATES, integrity_definition__isnull=True)
            .order_by("id")
            .values("id", "slug", "status")
        )
        market_ids = [item["id"] for item in candidates]
        inventory = self._inventory(market_ids)
        report = {
            "mode": "execute" if execute else "dry-run",
            "markets": candidates,
            **inventory,
        }
        if not market_ids:
            self.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True))
            return

        protected = self._protected_references(market_ids)
        if protected:
            report["protected_references"] = protected
            self.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True))
            if execute:
                raise CommandError("Limpeza recusada: ao menos um mercado possui registro criptografico protegido.")
            return

        if execute:
            with transaction.atomic():
                self._purge(market_ids)
            report["removed"] = True
        self.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True))

    @staticmethod
    def _inventory(market_ids):
        if not market_ids:
            return {"market_count": 0, "prediction_count": 0, "comment_count": 0, "notification_count": 0}
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM gotrendlabs_predictions WHERE market_id = ANY(%s)", [market_ids])
            predictions = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM gotrendlabs_market_comments WHERE market_id = ANY(%s)", [market_ids])
            comments = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM gotrendlabs_user_notifications WHERE market_id = ANY(%s)", [market_ids])
            notifications = cursor.fetchone()[0]
        return {
            "market_count": len(market_ids),
            "prediction_count": predictions,
            "comment_count": comments,
            "notification_count": notifications,
        }

    @staticmethod
    def _protected_references(market_ids):
        checks = {
            "definitions": "SELECT COUNT(*) FROM market_integrity_definitions WHERE market_id = ANY(%s)",
            "commitments": "SELECT COUNT(*) FROM prediction_commitments WHERE market_id = ANY(%s)",
            "seals": "SELECT COUNT(*) FROM market_seals WHERE market_id = ANY(%s)",
            "merkle_leaves": "SELECT COUNT(*) FROM market_merkle_leaves WHERE market_id = ANY(%s)",
            "ledger_events": "SELECT COUNT(*) FROM integrity_ledger_events WHERE market_id = ANY(%s)",
        }
        protected = {}
        with connection.cursor() as cursor:
            for label, sql in checks.items():
                cursor.execute(sql, [market_ids])
                count = cursor.fetchone()[0]
                if count:
                    protected[label] = count
        return protected

    @staticmethod
    def _purge(market_ids):
        now = timezone.now()
        connection.ensure_connection()
        with connection.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT id,slug FROM gotrendlabs_markets WHERE id = ANY(%s) ORDER BY id", [market_ids])
            removed_markets = cursor.fetchall()
            cursor.execute(
                """SELECT DISTINCT user_id FROM gotrendlabs_predictions WHERE market_id = ANY(%s)
                   UNION SELECT DISTINCT author_id FROM gotrendlabs_market_comments WHERE market_id = ANY(%s)""",
                [market_ids, market_ids],
            )
            affected_users = [row["user_id"] for row in cursor.fetchall() if row["user_id"] is not None]
            cursor.execute("SELECT id::text FROM gotrendlabs_predictions WHERE market_id = ANY(%s)", [market_ids])
            prediction_ids = [row["id"] for row in cursor.fetchall()]
            if prediction_ids:
                cursor.execute(
                    "DELETE FROM gotrendlabs_wallet_ledger WHERE reference_type='prediction' AND reference_id = ANY(%s)",
                    [prediction_ids],
                )
                cursor.execute(
                    "DELETE FROM gotrendlabs_user_activities WHERE reference_type='prediction' AND reference_id = ANY(%s)",
                    [prediction_ids],
                )
            cursor.execute("DELETE FROM gotrendlabs_predictions WHERE market_id = ANY(%s)", [market_ids])
            cursor.execute("SELECT to_regclass('public.gotrendlabs_market_funnel_market_links') AS table_name")
            if cursor.fetchone()["table_name"]:
                cursor.execute("DELETE FROM gotrendlabs_market_funnel_market_links WHERE market_id = ANY(%s)", [market_ids])
            # Use Django's deletion collector for presentation/engagement tables,
            # whose PostgreSQL constraints are intentionally NO ACTION.
            # Integrity alerts are mutable operational findings, not cryptographic
            # proofs. Remove findings scoped to candidates before the PROTECT FK.
            cursor.execute("DELETE FROM gotrendlabs_integrity_alerts WHERE market_id = ANY(%s)", [market_ids])
            Market.objects.filter(id__in=market_ids).delete()
            cursor.execute(
                """INSERT INTO gotrendlabs_admin_events
                   (actor_id,action,entity_type,entity_identifier,note,created_at)
                   VALUES (NULL,'integrity.unsigned_markets_purged','data_cleanup','preproduction-cutover',%s,%s)""",
                (
                    f"Removed {len(removed_markets)} unsigned pre-production markets: "
                    + ", ".join(row["slug"] for row in removed_markets),
                    now,
                ),
            )

            for user_id in affected_users:
                cursor.execute(
                    """SELECT
                         COALESCE(SUM(CASE direction WHEN 'credit' THEN amount WHEN 'debit' THEN -amount
                             WHEN 'lock' THEN -amount WHEN 'release' THEN amount ELSE 0 END),0) available,
                         COALESCE(SUM(CASE direction WHEN 'lock' THEN amount WHEN 'release' THEN -amount
                             WHEN 'settle' THEN -amount ELSE 0 END),0) locked,
                         COALESCE(SUM(CASE WHEN entry_type IN ('prediction_payout','reward_feedback','reward_suggestion') AND direction='credit' THEN amount
                             WHEN entry_type='prediction_payout_reversal' AND direction='debit' THEN -amount ELSE 0 END),0) earned
                       FROM gotrendlabs_wallet_ledger WHERE user_id=%s""",
                    [user_id],
                )
                wallet = cursor.fetchone()
                cursor.execute(
                    """UPDATE gotrendlabs_wallet_balances
                       SET available_gtl=%s,locked_gtl=GREATEST(%s,0),total_earned_gtl=GREATEST(%s,0),updated_at=%s
                       WHERE user_id=%s""",
                    [wallet["available"], wallet["locked"], wallet["earned"], now, user_id],
                )

            if affected_users:
                resolution_reasons = [f"market_resolved:{market_id}" for market_id in market_ids]
                cursor.execute(
                    """SELECT a.id,a.user_id,b.code
                       FROM gotrendlabs_user_badge_awards a
                       JOIN gotrendlabs_badge_definitions b ON b.id=a.badge_id
                       WHERE a.user_id = ANY(%s)
                         AND split_part(a.reason_snapshot, ';', 1) = ANY(%s)""",
                    [affected_users, resolution_reasons],
                )
                removed_awards = cursor.fetchall()
                if removed_awards:
                    cursor.execute(
                        "DELETE FROM gotrendlabs_user_badge_awards WHERE id = ANY(%s)",
                        [[row["id"] for row in removed_awards]],
                    )
                    for award in removed_awards:
                        cursor.execute(
                            """DELETE FROM gotrendlabs_user_notifications
                               WHERE recipient_id=%s AND event_type='badge_awarded' AND source_key=%s""",
                            [award["user_id"], f"badge_awarded:{award['code']}"],
                        )
                engine = _daemon_lifecycle_engine(cursor)
                for user_id in affected_users:
                    engine._recalculate_user_reputation(user_id, now)
                    BadgeAwardEngine.reconcile_user(cursor, user_id)
