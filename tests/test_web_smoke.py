from django.test import TestCase
from django.urls import reverse

from core.domain_client import get_domain_client


class FixtureDomainClientTests(TestCase):
    def test_market_fixture_contract_has_expected_fields(self):
        market = get_domain_client().market("openai-gpt6-2026")

        self.assertEqual(market["status"], "open")
        self.assertIn("options", market)
        self.assertIn("resolution_criteria", market)
        self.assertGreaterEqual(len(market["options"]), 2)


class WebSmokeTests(TestCase):
    def test_main_pages_render(self):
        routes = [
            reverse("home"),
            reverse("market-detail", args=["openai-gpt6-2026"]),
            reverse("login"),
            reverse("register"),
            reverse("wallet"),
            reverse("profile"),
            reverse("rankings"),
            reverse("admin-ops-dashboard"),
            reverse("concepts"),
            reverse("categories"),
            reverse("security"),
            reverse("suggestion"),
            reverse("feedback"),
        ]

        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)

    def test_login_page_has_focused_auth_layout(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, "Acessar conta")
        self.assertContains(response, "Google")
        self.assertContains(response, "Facebook")
        self.assertContains(response, "Modo guest")
        self.assertNotContains(response, "backend-api")
        self.assertNotContains(response, "Continuar com Apple")

    def test_prediction_preview_partial_renders(self):
        response = self.client.post(
            reverse("prediction-preview", args=["openai-gpt6-2026"]),
            {"choice": "SIM", "amount": "120"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SIM")
        self.assertContains(response, "120 OC")
