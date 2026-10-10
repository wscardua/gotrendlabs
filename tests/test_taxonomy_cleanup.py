import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.db import connection

from apps.api.backend_api.db import get_connection
from apps.web.django.markets.models import AdminEvent, Market, MarketCategory, MarketSubcategory, MarketEvent
from ops.scripts.consolidate_unused_taxonomy import consolidate
from tests.test_cases import AppendOnlyTransactionTestCase


class TaxonomyCleanupTests(AppendOnlyTransactionTestCase):
    def setUp(self):
        super().setUp()
        if connection.vendor != "postgresql":
            self.skipTest("Limpeza usa PostgreSQL")
        environment = patch.dict(os.environ, {f"FASTAPI_POSTGRES_{key}": "" for key in ("DB", "USER", "PASSWORD", "HOST", "PORT")})
        environment.start()
        self.addCleanup(environment.stop)
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.backup = Path(directory.name) / "backup.json"
        self.category = MarketCategory.objects.create(name="Esporte", slug="esporte")
        self.keep = MarketSubcategory.objects.create(category=self.category, name="Geral", slug="esporte-geral")
        self.remove = MarketSubcategory.objects.create(category=self.category, name="Geral", slug="geral")
        self.keep_event = MarketEvent.objects.create(subcategory=self.keep, name="Geral", slug="esporte-geral-geral")
        self.remove_event = MarketEvent.objects.create(subcategory=self.remove, name="Geral", slug="geral")
        self.distinct_event = MarketEvent.objects.create(subcategory=self.remove, name="Mundial2026", slug="mundial2026")

    def run_cleanup(self, execute=False):
        with get_connection() as db:
            return consolidate(db, [(self.remove.pk, self.keep.pk)], execute=execute, backup_path=self.backup)

    def market(self, subcategory, event):
        return Market.objects.create(slug="preservado", title="Preservado?", category=self.category, subcategory=subcategory, event=event)

    def test_dry_run_has_no_side_effects(self):
        report = self.run_cleanup()
        self.assertEqual(report["mode"], "dry-run")
        self.assertEqual(MarketSubcategory.objects.count(), 2)
        self.assertEqual(MarketEvent.objects.count(), 3)
        self.assertFalse(self.backup.exists())
        self.assertFalse(AdminEvent.objects.exists())

    def test_execute_preserves_linked_ids_and_distinct_events_with_backup_and_audit(self):
        market = self.market(self.keep, self.keep_event)
        self.run_cleanup(execute=True)
        market.refresh_from_db()
        self.assertEqual((market.subcategory_id, market.event_id), (self.keep.pk, self.keep_event.pk))
        self.assertFalse(MarketSubcategory.objects.filter(pk=self.remove.pk).exists())
        self.assertFalse(MarketEvent.objects.filter(pk=self.remove_event.pk).exists())
        self.distinct_event.refresh_from_db()
        self.assertEqual(self.distinct_event.subcategory_id, self.keep.pk)
        backup = json.loads(self.backup.read_text())
        self.assertEqual(backup["merges"][0]["remove_id"], self.remove.pk)
        self.assertEqual(self.backup.stat().st_mode & 0o777, 0o600)
        self.assertEqual(AdminEvent.objects.get().action, "taxonomy.deduplicate")

    def test_refuses_source_with_linked_market(self):
        self.market(self.remove, self.remove_event)
        with self.assertRaisesRegex(ValueError, "possui mercado"):
            self.run_cleanup(execute=True)
        self.assertEqual(MarketSubcategory.objects.count(), 2)
        self.assertEqual(MarketEvent.objects.count(), 3)
        self.assertFalse(self.backup.exists())

    def test_refuses_conflicting_notices(self):
        self.remove.notice = "Aviso que deve ser preservado"
        self.remove.save(update_fields=["notice"])
        with self.assertRaisesRegex(ValueError, "Avisos ou bloqueios"):
            self.run_cleanup(execute=True)
        self.assertEqual(MarketSubcategory.objects.count(), 2)
        self.assertFalse(self.backup.exists())

    def test_existing_backup_is_not_overwritten(self):
        self.backup.write_text("backup anterior")
        with self.assertRaises(FileExistsError):
            self.run_cleanup(execute=True)
        self.assertEqual(self.backup.read_text(), "backup anterior")
        self.assertEqual(MarketSubcategory.objects.count(), 2)
        self.assertEqual(MarketEvent.objects.count(), 3)
