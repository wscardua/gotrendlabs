import json
from unittest.mock import patch
from uuid import uuid4

from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.template.loader import render_to_string
from django.utils.translation import get_language, override

from apps.web.django.admin_ops.templatetags.analytics_display import analytics_date, analytics_number, analytics_timestamp


class AnalyticsWebProxyTests(TestCase):
    def test_proxy_requires_csrf_and_forwards_anonymous_batch(self):
        client = Client(enforce_csrf_checks=True)
        payload = {"visitor_id": str(uuid4()), "session_id": str(uuid4()), "events": []}
        with patch("apps.web.django.core.analytics_views.send_analytics_events", return_value={"accepted": 0}) as send:
            rejected = client.post("/analytics/events/", data=json.dumps(payload), content_type="application/json")
            self.assertEqual(rejected.status_code, 403)
            self.assertFalse(send.called)
            client.cookies["csrftoken"] = "a" * 32
            accepted = client.post("/analytics/events/", data=json.dumps(payload),
                                   content_type="application/json", HTTP_X_CSRFTOKEN="a" * 32)
            self.assertEqual(accepted.status_code, 200)
            self.assertEqual(accepted.json(), {"accepted": 0})
            send.assert_called_once()
            self.assertEqual(send.call_args.args[0], payload)
            self.assertIsNone(send.call_args.args[1])


class AnalyticsPlatformPresentationTests(SimpleTestCase):
    def render_comparison(self, platform="all", sessions=3):
        platforms = [{"platform": key, "sessions": sessions, "visitors": 2, "users": 1,
                      "views": 4, "session_share": 50.0 if sessions else None}
                     for key in (("web", "mobile") if platform == "all" else (platform,))]
        return render_to_string("admin_ops/analytics_platforms.html", {
            "filters": {"platform": platform},
            "report": {"platforms": platforms, "platform_daily": [
                {"day": "2026-10-12", "web_sessions": sessions, "mobile_sessions": sessions}]},
        })

    def test_both_origins_and_accessible_daily_values_are_present(self):
        html = self.render_comparison()
        self.assertIn('data-platform="web"', html)
        self.assertIn('data-platform="mobile"', html)
        self.assertIn('App mobile', html)
        self.assertIn('2026-10-12', html)
        self.assertIn('details class="analytics-platform-daily" open', html)
        self.assertIn('navegadores de computador e celular', html)
        self.assertIn('json', html)

    def test_filtered_platform_and_empty_share_are_explicit(self):
        html = self.render_comparison(platform="mobile", sessions=0)
        self.assertNotIn('data-platform="web"', html)
        self.assertIn('data-platform="mobile"', html)
        self.assertIn('Selecione Todas', html)
        self.assertIn('—', html)
        self.assertNotIn('None%', html)

    def test_dates_numbers_and_timestamps_follow_locale_without_changing_utc(self):
        with override("pt-br"):
            self.assertEqual(analytics_date("2026-10-12"), "12/10/2026")
            self.assertEqual(analytics_number(1234), "1.234")
            self.assertEqual(analytics_number(66.7, 1), "66,7")
            self.assertIn("12/10/2026", analytics_timestamp("2026-10-12T21:00:00+00:00"))
            self.assertIn("21:00", analytics_timestamp("2026-10-12T18:00:00-03:00"))
        with override("en"):
            self.assertEqual(analytics_number(1234), "1,234")
            self.assertEqual(analytics_number(66.7, 1), "66.7")
            self.assertEqual(analytics_date("2026-10-12"), "10/12/2026")

    def test_keyboard_control_is_available_and_no_js_table_stays_open(self):
        html = self.render_comparison()
        self.assertIn('type="range"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('12/10/2026', html)
        self.assertIn('details class="analytics-platform-daily" open', html)


class AnalyticsDashboardUsabilityTests(SimpleTestCase):
    def test_view_forwards_explicit_navigation_filters_to_backend(self):
        from apps.web.django.admin_ops.views import analytics

        query = {"days": "30", "platform": "mobile", "audience": "authenticated", "region": "SP", "city": "São Paulo"}
        request = RequestFactory().get("/admin-ops/analytics/", query)
        request.session = {"auth_api_token": "test-token", "auth_api_user": {
            "is_staff": True, "preferred_language": "pt-br"}}
        with patch("apps.web.django.admin_ops.views.admin_get_analytics_summary", return_value={}) as summary, \
                patch("apps.web.django.admin_ops.views.render", return_value=HttpResponse()) as render:
            analytics(request)
        summary.assert_called_once_with("test-token", query)
        self.assertEqual(render.call_args.args[2]["filters"], query)
        self.assertEqual(len(render.call_args.args[2]["region_choices"]), 27)

    def test_operator_language_controls_rendering_and_response_language(self):
        from apps.web.django.admin_ops.views import analytics

        request = RequestFactory().get("/admin-ops/analytics/", HTTP_ACCEPT_LANGUAGE="en")
        request.session = {"auth_api_token": "test-token", "auth_api_user": {
            "is_staff": True, "preferred_language": "pt-br"}}

        def present(request, template, context):
            self.assertEqual(get_language(), "pt-br")
            return HttpResponse(analytics_number(66.7, 1))

        with override("en"), patch("apps.web.django.admin_ops.views.admin_get_analytics_summary", return_value={}), \
                patch("apps.web.django.admin_ops.views.render", side_effect=present):
            response = analytics(request)
            self.assertEqual(get_language(), "en")
        self.assertEqual(response.headers["Content-Language"], "pt-br")
        self.assertEqual(response.content, b"66,7")

    def render_dashboard(self, state="missing"):
        metric = {"eligible": 0, "returned": 0, "rate": None}
        audience = {"totals": {key: metric for key in ("d1", "d7", "d30")}, "cohorts": []}
        report = {
            "generated_at": "2026-10-12T21:00:00+00:00", "period_days": 7,
            "totals": dict.fromkeys(("visitors", "sessions", "views", "users", "recent_sessions", "located_sessions"), 0),
            "platforms": [], "platform_daily": [], "funnel": {}, "abandonment": {},
            "authenticated_funnel": {}, "domain_totals": {}, "collection_24h": {},
            "retention": {"registered": audience, "visitors": audience},
            "geolite_file": {"state": state},
            "last_geolite_run": {"status": "success", "completed_at": "2026-10-01T12:00:00Z"},
            "cities": [{"city_name": "São Paulo", "region_code": "SP", "sessions": 1, "users": 0}],
            "collection_platforms": [{"platform": "mobile", "events_24h": 0, "last_event_at": None}],
        }
        return render_to_string("admin_ops/analytics.html", {
            "report": report, "region_choices": ["SP", "RJ"],
            "filters": {"days": "7", "platform": "mobile", "audience": "all", "region": "SP", "city": "São Paulo"},
        })

    def test_filters_and_scopes_are_explicit_and_current_health_precedes_history(self):
        html = self.render_dashboard()
        self.assertIn('<select name="region">', html)
        self.assertIn('value="SP" selected', html)
        self.assertIn('list="analytics-city-options"', html)
        self.assertIn('Limpar filtros', html)
        self.assertIn('Global · 90 dias · não segue os filtros', html)
        self.assertIn('não seguem filtros de plataforma, público ou localização', html)
        self.assertIn('Nenhum evento humano no histórico retido', html)
        self.assertIn('Isso não comprova ausência de uso', html)
        self.assertLess(html.index('Geolocalização indisponível'), html.index('Carga histórica concluída'))
        self.assertNotIn('is-success', html)
        self.assertLess(html.index('id="atividade"'), html.index('id="retencao"'))
        self.assertLess(html.index('id="retencao"'), html.index('id="geografia"'))

    def test_ready_geolite_does_not_raise_unavailable_notice(self):
        html = self.render_dashboard("ready")
        self.assertIn('Base GeoLite disponível', html)
        self.assertNotIn('Geolocalização indisponível', html)

    def test_error_page_does_not_link_to_missing_report_sections(self):
        html = render_to_string("admin_ops/analytics.html", {
            "report": None, "admin_error": "Serviço indisponível",
            "filters": {"days": "7", "platform": "all", "audience": "all"},
            "region_choices": ["SP"],
        })
        self.assertIn("Analytics indisponível", html)
        self.assertNotIn('href="#retencao"', html)
        self.assertNotIn('data-platform-chart', html)
