from copy import deepcopy
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from django.template.loader import render_to_string
from django.urls import resolve, reverse

from apps.web.django.accounts.api_client import AuthAPIError, get_performance
from apps.web.django.profiles.views import performance


def performance_payload():
    return {
        "scorecard": {"reputation_score": 237, "ranking_position": 8,
                      "resolved_predictions_count": 42, "accuracy_indicator": "71%",
                      "streak": 3, "strong_category": "Ciência", "last_updated_at": "2026-11-07T12:00:00Z"},
        "history": [{"prediction_id": i, "market_slug": f"mercado-{i}",
                     "market_title": f"Pergunta real {i}", "option_label": "Alternativa A",
                     "result_label": "Acertou" if i % 2 else "Não acertou", "won": bool(i % 2),
                     "reputation_delta": 4 if i % 2 else -6,
                     "educational_result_label": "+45 GT₵" if i % 2 else "-30 GT₵",
                     "resolved_at": "2026-11-07T12:00:00Z", "resolved_at_label": "07/11/2026 09:00"}
                    for i in range(10)],
        "progression": {"earned_badges_count": 7, "latest_awards": [
            {"code": "pioneiro", "name": "Pioneiro", "description": "Participação reconhecida",
             "status": "earned", "image_url": "/static/brand/gtl-constellation-mark-light.svg",
             "image_dark_url": "/static/brand/gtl-constellation-mark-dark.svg"}]},
        "generated_at": "2026-11-07T12:00:00Z",
    }


class PerformanceWebTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = {"id": 1, "display_name": "Pessoa", "handle": "@pessoa", "preferred_language": "pt-br"}
        # Keep real view/template rendering; isolate unrelated global navigation services.
        self.context_patch = patch("apps.web.django.core.context_processors.session_context", side_effect=lambda request: {
            "is_guest": not bool(request.session.get("auth_api_token")),
            "can_access_admin_ops": bool(request.session.get("auth_api_user", {}).get("is_staff") or request.session.get("auth_api_user", {}).get("is_superuser")),
            "viewer": {"name": "Pessoa", "handle": "@pessoa"},
        })
        self.context_patch.start()
        self.addCleanup(self.context_patch.stop)

    def request(self, token="token-a", user=None, path="/desempenho/"):
        request = self.factory.get(path)
        request.session = {"auth_api_token": token, "auth_api_user": user or self.user} if token else {}
        return request

    @patch("apps.web.django.profiles.views.get_performance")
    def test_visitor_redirect_preserves_destination(self, api):
        response = performance(self.request(token=None))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/?next=%2Fdesempenho%2F")
        self.assertIn("no-store", response["Cache-Control"])
        api.assert_not_called()

    @patch("apps.web.django.profiles.views.get_performance", return_value=performance_payload())
    def test_authenticated_data_links_and_menu_order(self, api):
        response = performance(self.request())
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        api.assert_called_once_with("token-a")
        for value in ["237", "#8", "42", "71%", "Ciência", "Alternativa A", "07/11/2026 09:00", "+4", "-6", "+45 GT₵", "-30 GT₵", "Pioneiro", "7 badges conquistadas", 'href="/profile/#badges"', 'href="/rankings/"']:
            self.assertIn(value, html)
        for i in range(10):
            self.assertIn(f'href="/markets/mercado-{i}/"', html)
        menu = html.split('class="user-menu"')[1].split('</div>')[0]
        self.assertLess(menu.index("Perfil e badges"), menu.index("Desempenho"))
        self.assertLess(menu.index("Desempenho"), menu.index("Carteira educativa"))
        self.assertNotIn("Painel Administrativo", menu)
        self.assertIn("Carregar mais", html)
        self.assertIn("private", response["Cache-Control"])
        self.assertIn("no-store", response["Cache-Control"])

    @patch("apps.web.django.profiles.views.get_performance")
    def test_empty_and_absent_metrics_do_not_create_fiction(self, api):
        payload = performance_payload()
        payload["history"] = []
        payload["progression"] = {"earned_badges_count": 0, "latest_awards": []}
        payload["scorecard"].update(ranking_position=0, strong_category="", reputation_score=0)
        api.return_value = payload
        response = performance(self.request())
        for text in ["Sem posição", "Ainda não definida", "Suas resoluções aparecerão aqui", "Explorar mercados", "Você ainda não tem conquistas", "0 badges conquistadas"]:
            self.assertContains(response, text)
        self.assertNotContains(response, "#0")
        self.assertNotContains(response, "Pioneiro")
        self.assertNotContains(response, "Carregar mais")

    @patch("apps.web.django.profiles.views.get_performance", side_effect=AuthAPIError("secret backend detail", 503))
    def test_api_failure_is_explicit_without_zero_scorecard(self, api):
        response = performance(self.request())
        self.assertContains(response, "Não foi possível carregar seu desempenho", status_code=503)
        self.assertContains(response, "Tentar novamente", status_code=503)
        self.assertNotContains(response, "Placar atual", status_code=503)
        self.assertNotContains(response, "secret backend detail", status_code=503)

    @patch("apps.web.django.profiles.views.get_performance", side_effect=AuthAPIError("Sessão inválida", 401))
    def test_expired_session_is_cleared(self, api):
        request = self.request()
        response = performance(request)
        self.assertEqual(response.url, "/login/?next=%2Fdesempenho%2F")
        self.assertEqual(request.session, {})

    @patch("apps.web.django.profiles.views.get_performance", side_effect=AuthAPIError("Denied", 403))
    def test_forbidden_does_not_expose_metrics(self, api):
        response = performance(self.request())
        self.assertContains(response, "Acesso não permitido", status_code=403)
        self.assertNotContains(response, "Placar atual", status_code=403)

    @patch("apps.web.django.profiles.views.get_performance")
    def test_data_is_refetched_and_isolated_by_session_not_query_user(self, api):
        first = performance_payload()
        second = deepcopy(first)
        first["history"][0]["market_title"] = "Privado da pessoa A"
        second["history"][0]["market_title"] = "Privado da pessoa B"
        api.side_effect = [first, second, second]
        a = performance(self.request(path="/desempenho/?user_id=2"))
        b = performance(self.request(token="token-b", user={**self.user, "id": 2}))
        performance(self.request(token="token-b"))
        self.assertContains(a, "Privado da pessoa A")
        self.assertNotContains(b, "Privado da pessoa A")
        self.assertContains(b, "Privado da pessoa B")
        self.assertEqual([c.args for c in api.call_args_list], [("token-a",), ("token-b",), ("token-b",)])

    @patch("apps.web.django.profiles.views.get_performance", return_value=performance_payload())
    def test_operator_and_bot_visibility_preserves_existing_permissions(self, api):
        for role in ["is_staff", "is_superuser", "is_bot"]:
            with self.subTest(role=role):
                payload = performance_payload()
                payload["scorecard"]["ranking_position"] = 0
                api.return_value = payload
                response = performance(self.request(user={**self.user, role: True}))
                self.assertContains(response, "Desempenho")
                if role == "is_bot":
                    self.assertNotContains(response, "Painel Administrativo")
                    self.assertContains(response, "Sem posição")
                else:
                    self.assertContains(response, "Painel Administrativo")
                    self.assertNotContains(response, "Placar atual")

    def test_profile_shortcut_and_badges_anchor(self):
        html = render_to_string("profiles/profile.html", {"is_guest": True, "can_access_admin_ops": True, "viewer": {"name": "Pessoa"}})
        self.assertIn('href="/desempenho/"', html)
        self.assertIn('id="badges"', html)

    @patch("apps.web.django.accounts.api_client._request", return_value=performance_payload())
    def test_api_client_uses_authenticated_existing_contract(self, api):
        self.assertEqual(get_performance("personal-token"), performance_payload())
        api.assert_called_once_with("GET", "/users/me/performance", token="personal-token")

    @patch("apps.web.django.profiles.views.get_performance")
    def test_named_route_and_read_only_method(self, api):
        self.assertEqual(reverse("performance"), "/desempenho/")
        self.assertEqual(resolve("/desempenho/").func, performance)
        request = self.request()
        request.method = "POST"
        self.assertEqual(performance(request).status_code, 405)
        api.assert_not_called()

    @patch("apps.web.django.profiles.views.get_performance")
    def test_backend_text_is_escaped_and_history_has_no_extra_image_fetch(self, api):
        payload = performance_payload()
        payload["history"][0]["market_title"] = "<script>alert(1)</script>"
        api.return_value = payload
        response = performance(self.request())
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")
        html = response.content.decode().split('<table class="performance-table"')[1].split('</table>')[0]
        self.assertNotIn('<img', html)
        api.assert_called_once()

    @patch("apps.web.django.profiles.views.get_performance")
    def test_short_history_has_no_load_more(self, api):
        payload = performance_payload()
        payload["history"] = payload["history"][:3]
        api.return_value = payload
        response = performance(self.request())
        self.assertNotContains(response, "Carregar mais")
        table = response.content.decode().split('<table class="performance-table"')[1].split('</table>')[0]
        self.assertEqual(table.count("Pergunta real"), 3)

    @patch("apps.web.django.profiles.views.get_performance")
    def test_impact_chart_preserves_deltas_and_chronological_order(self, api):
        payload = performance_payload()
        payload["history"] = payload["history"][:3]
        payload["history"][0]["reputation_delta"] = 0
        api.return_value = payload
        html = performance(self.request()).content.decode()
        chart = html.split('<ol class="performance-impact-bars">')[1].split('</ol>')[0]
        self.assertLess(chart.index('/markets/mercado-2/'), chart.index('/markets/mercado-1/'))
        self.assertLess(chart.index('/markets/mercado-1/'), chart.index('/markets/mercado-0/'))
        self.assertIn('negative', chart)
        self.assertIn('neutral', chart)
        self.assertIn('--bar-height: 36px', chart)
        self.assertIn('--bar-height: 24px', chart)
        self.assertIn('--bar-height: 0px', chart)
        self.assertIn('>+4</span>', chart)
        self.assertIn('>-6</span>', chart)

    @patch("apps.web.django.profiles.views.get_performance")
    def test_impact_chart_absent_for_empty_and_admin(self, api):
        payload = performance_payload()
        api.return_value = payload
        self.assertNotContains(performance(self.request(user={**self.user, "is_staff": True})), 'class="performance-impact-bars"')
        payload["history"] = []
        self.assertNotContains(performance(self.request()), 'class="performance-impact-bars"')
