from django.db import connection
from django.test import TransactionTestCase

from apps.api.backend_api.db import close_pools
from apps.web.django.system_logs import services as log_services


def drain_technical_logs():
    """Keep best-effort request logs out of the next test's database flush."""
    for slot in (log_services._submit_slot, log_services._log_slot):
        if not slot.acquire(timeout=3):
            raise AssertionError("Technical log did not finish before test database teardown")
        slot.release()
    close_pools()


class AppendOnlyTransactionTestCase(TransactionTestCase):
    """Let Django flush its isolated database without weakening production guards."""

    checkpoint_truncate_trigger = "integrity_ledger_checkpoints_no_truncate"

    def _fixture_teardown(self):
        drain_technical_logs()
        trigger_disabled = False
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT to_regclass('integrity_ledger_checkpoints') IS NOT NULL AS table_exists"
                )
                if cursor.fetchone()[0]:
                    cursor.execute(
                        f"ALTER TABLE integrity_ledger_checkpoints DISABLE TRIGGER {self.checkpoint_truncate_trigger}"
                    )
                    trigger_disabled = True
        try:
            super()._fixture_teardown()
        finally:
            if trigger_disabled:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"ALTER TABLE integrity_ledger_checkpoints ENABLE TRIGGER {self.checkpoint_truncate_trigger}"
                    )
