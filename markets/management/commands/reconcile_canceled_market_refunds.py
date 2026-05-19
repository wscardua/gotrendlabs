from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from backend_api.db import get_connection
from backend_api.main import _record_admin_event, _refund_market_predictions


class Command(BaseCommand):
    help = "Reconcile canceled markets that still have open predictions by applying refund releases."

    def add_arguments(self, parser):
        parser.add_argument("--slug", help="Restrict reconciliation to a single market slug.")
        parser.add_argument("--dry-run", action="store_true", help="Report affected markets without changing data.")
        parser.add_argument(
            "--note",
            default="reconcile_canceled_market_refunds: refund open predictions for canceled market",
            help="Audit note stored in admin events.",
        )

    def handle(self, *args, **options):
        slug = options.get("slug")
        dry_run = options["dry_run"]
        note = options["note"]

        with get_connection() as connection:
            with connection.cursor() as cursor:
                markets = self._markets_with_open_predictions(cursor, slug)
                if not markets:
                    self.stdout.write("No canceled markets with open predictions found.")
                    return

                total_predictions = sum(int(market["open_predictions"] or 0) for market in markets)
                if dry_run:
                    for market in markets:
                        self.stdout.write(
                            f"DRY-RUN {market['slug']}: {market['open_predictions']} open predictions, "
                            f"stake {market['stake_amount']} OC"
                        )
                    self.stdout.write(f"DRY-RUN total: {len(markets)} markets, {total_predictions} open predictions.")
                    return

                reconciled = []
                now = datetime.now(timezone.utc)
                for market in markets:
                    stats = _refund_market_predictions(cursor, market["id"], None, market["slug"], now)
                    _record_admin_event(
                        cursor,
                        None,
                        "market.cancel_reconcile",
                        "market",
                        market["slug"],
                        note,
                    )
                    reconciled.append((market, stats))

                for market, stats in reconciled:
                    self.stdout.write(
                        f"Reconciled {market['slug']}: "
                        f"{stats['predictions_canceled']} predictions canceled, "
                        f"{stats['refunds_created']} refunds created, "
                        f"{stats['refunds_existing']} refunds already present."
                    )
                self.stdout.write(f"Done: {len(reconciled)} markets, {total_predictions} predictions inspected.")

    def _markets_with_open_predictions(self, cursor, slug):
        params = []
        slug_filter = ""
        if slug:
            slug_filter = " AND m.slug = %s"
            params.append(slug)
        cursor.execute(
            f"""
            SELECT m.id, m.slug, COUNT(p.id) AS open_predictions, COALESCE(SUM(p.stake_amount), 0) AS stake_amount
            FROM orynth_markets m
            JOIN orynth_predictions p ON p.market_id = m.id
            WHERE m.status = 'canceled'
              AND p.status = 'open'
              {slug_filter}
            GROUP BY m.id, m.slug
            ORDER BY m.slug
            """,
            params,
        )
        return cursor.fetchall()
