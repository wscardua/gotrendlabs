from unittest.mock import patch
from django.http import HttpResponse
from django.test import SimpleTestCase, RequestFactory
from apps.web.django.admin_ops.integration_views import consent


class ConsentQueryTests(SimpleTestCase):
    def test_browser_query_remains_scalar_through_get_and_post(self):
        params = {
            "client_id": "client",
            "scope": "editorial:read catalog:read",
            "state": "state",
            "redirect_uri": "http://127.0.0.1:8765/callback",
            "code_challenge": "challenge",
            "code_challenge_method": "S256",
            "resource": "http://127.0.0.1:8000/mcp",
            "response_type": "code",
        }
        session = {
            "auth_api_token": "fixture",
            "auth_api_user": {"id": 1, "is_staff": True},
        }
        request = RequestFactory().get("/admin-ops/integration-consent/", params)
        request.session = session
        with (
            patch(
                "apps.web.django.admin_ops.integration_views._request", return_value={}
            ) as api,
            patch(
                "apps.web.django.admin_ops.integration_views.render",
                return_value=HttpResponse(),
            ),
        ):
            self.assertEqual(consent(request).status_code, 200)
            self.assertEqual(api.call_args.args[2], params)
        request = RequestFactory().post(
            "/admin-ops/integration-consent/",
            {"consent": "allow", "integration_id": "integration"},
        )
        request.session = session
        with patch(
            "apps.web.django.admin_ops.integration_views._request",
            side_effect=[{}, {"redirect": "http://127.0.0.1:8765/callback"}],
        ) as api:
            self.assertEqual(consent(request).status_code, 302)
            self.assertEqual(api.call_args.args[2]["parameters"], params)
        self.assertNotIn("mcp_oauth_request", session)
