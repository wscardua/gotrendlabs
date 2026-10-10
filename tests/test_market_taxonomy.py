import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from fastapi.testclient import TestClient

from apps.api.backend_api.main import app
from apps.web.django.markets.models import Market, MarketCategory, MarketSubcategory, MarketEvent
from tests.test_cases import AppendOnlyTransactionTestCase


class MarketTaxonomyTests(AppendOnlyTransactionTestCase):
    def setUp(self):
        super().setUp()
        if connection.vendor != "postgresql":
            self.skipTest("Taxonomia usa PostgreSQL")
        environment = patch.dict(os.environ, {f"FASTAPI_POSTGRES_{key}": "" for key in (
            "DB", "USER", "PASSWORD", "HOST", "PORT")})
        environment.start()
        self.addCleanup(environment.stop)
        staff = get_user_model().objects.create(username="taxonomy-staff", is_staff=True)
        auth = patch("apps.api.backend_api.main._current_staff_user", return_value={"id": staff.pk})
        auth.start()
        self.addCleanup(auth.stop)
        self.api = TestClient(app)
        self.category = MarketCategory.objects.create(name="Ciência", slug="grupo-original", notice="Aviso grupo")
        self.subcategory = MarketSubcategory.objects.create(category=self.category, name="Espaço", slug="subgrupo-original", notice="Aviso subgrupo")
        self.event = MarketEvent.objects.create(subcategory=self.subcategory, name="Missão Lunar", slug="evento-original", notice="Aviso evento")
        self.payload = {
            "title": "Teste de classificação?", "slug": "teste-taxonomia", "summary": "Resumo",
            "category": self.category.name, "subcategory": self.subcategory.name, "event": self.event.name,
            "source": "https://example.com", "resolution_criteria": "Critério verificável",
            "close_at": "2027-12-31T23:59:00-03:00", "thumb_color": "#123456",
        }

    def edit_market(self, payload):
        detail = self.api.get("/admin/markets/teste-taxonomia")
        self.assertEqual(detail.status_code, 200, detail.text)
        return self.api.patch("/admin/markets/teste-taxonomia", json={
            **payload, "expected_revision": detail.json()["editorial_revision"],
        })

    def counts(self):
        return tuple(model.objects.count() for model in (MarketCategory, MarketSubcategory, MarketEvent))

    def test_edit_reuses_existing_subcategory_and_event_instead_of_duplicating(self):
        created = self.api.post("/admin/markets", json={
            **self.payload, "category": "Original", "subcategory": "Original", "event": "Original",
        })
        self.assertEqual(created.status_code, 201, created.text)
        self.category.slug = "ciencia"
        self.category.save(update_fields=["slug"])
        before = self.counts()
        edited = self.edit_market(self.payload)
        self.assertEqual(edited.status_code, 200, edited.text)
        self.assertEqual(self.counts(), before)
        market = Market.objects.get(slug="teste-taxonomia")
        self.assertEqual((market.category_id, market.subcategory_id, market.event_id),
                         (self.category.pk, self.subcategory.pk, self.event.pk))

    def test_create_and_edit_reuse_custom_slugs_and_preserve_notices(self):
        before = self.counts()
        created = self.api.post("/admin/markets", json=self.payload)
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(self.counts(), before)
        category = MarketCategory.objects.create(name="Tecnologia", slug="tech")
        subcategory = MarketSubcategory.objects.create(category=category, name="Espaço", slug="space-tech")
        event = MarketEvent.objects.create(subcategory=subcategory, name="Missão Lunar", slug="launch")
        before = self.counts()
        payload = {**self.payload, "category": " Tecnologia ", "subcategory": " espaço ", "event": " missão lunar "}
        for _ in range(2):
            edited = self.edit_market(payload)
            self.assertEqual(edited.status_code, 200, edited.text)
            market = Market.objects.get(slug="teste-taxonomia")
            self.assertEqual((market.category_id, market.subcategory_id, market.event_id), (category.pk, subcategory.pk, event.pk))
            self.assertEqual(self.counts(), before)
        for obj, slug, notice in ((self.category, "grupo-original", "Aviso grupo"), (self.subcategory, "subgrupo-original", "Aviso subgrupo"), (self.event, "evento-original", "Aviso evento")):
            obj.refresh_from_db()
            self.assertEqual((obj.slug, obj.notice), (slug, notice))

    def test_blocked_existing_taxonomy_is_not_recreated(self):
        created = self.api.post("/admin/markets", json=self.payload)
        self.assertEqual(created.status_code, 201, created.text)
        for obj in (self.category, self.subcategory, self.event):
            with self.subTest(level=type(obj).__name__):
                obj.is_blocked = True
                obj.save(update_fields=["is_blocked"])
                before = self.counts()
                response = self.api.post("/admin/markets", json=self.payload)
                self.assertEqual(response.status_code, 422, response.text)
                self.assertEqual(self.counts(), before)
                edited = self.edit_market(self.payload)
                self.assertEqual(edited.status_code, 422, edited.text)
                self.assertEqual(self.counts(), before)
                obj.is_blocked = False
                obj.save(update_fields=["is_blocked"])

    def test_existing_duplicate_is_rejected_without_new_records(self):
        MarketEvent.objects.create(subcategory=self.subcategory, name=self.event.name, slug="duplicado")
        before = self.counts()
        response = self.api.post("/admin/markets", json=self.payload)
        self.assertEqual(response.status_code, 409, response.text)
        self.assertIn("duplicidade", response.json()["detail"])
        self.assertEqual(self.counts(), before)
        self.assertFalse(Market.objects.filter(slug="teste-taxonomia").exists())

    def test_new_taxonomy_remains_supported(self):
        before = self.counts()
        response = self.api.post("/admin/markets", json={**self.payload, "category": "Novo", "subcategory": "Nova", "event": "Novidade"})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(self.counts(), tuple(count + 1 for count in before))

    def test_renamed_taxonomy_keeps_its_identity(self):
        created = self.api.post("/admin/markets", json=self.payload)
        self.assertEqual(created.status_code, 201, created.text)
        before = self.counts()
        for obj, field in ((self.category, "category"), (self.subcategory, "subcategory"), (self.event, "event")):
            obj.name += " renomeado"
            obj.save(update_fields=["name"])
            self.payload[field] = obj.name
        response = self.edit_market(self.payload)
        self.assertEqual(response.status_code, 200, response.text)
        market = Market.objects.get(slug="teste-taxonomia")
        self.assertEqual((market.category_id, market.subcategory_id, market.event_id), (self.category.pk, self.subcategory.pk, self.event.pk))
        self.assertEqual(self.counts(), before)
