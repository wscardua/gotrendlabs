from django.db import connection
from django.test import TransactionTestCase


class AppendOnlyTransactionTestCase(TransactionTestCase):
    """Let Django flush its isolated database without weakening production guards."""

    checkpoint_truncate_trigger = "integrity_ledger_checkpoints_no_truncate"

    def _fixture_teardown(self):
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
