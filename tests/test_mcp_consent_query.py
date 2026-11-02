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
        consent_info = {
            "scopes": ["editorial:read", "catalog:read"],
            "integrations": [{"scopes": ["editorial:read", "catalog:read"]}],
        }
        request = RequestFactory().get("/admin-ops/integration-consent/", params)
        request.session = session
        with (
            patch(
                "apps.web.django.admin_ops.integration_views._request",
                return_value=consent_info,
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
            side_effect=[consent_info, {"redirect": "http://127.0.0.1:8765/callback"}],
        ) as api:
            self.assertEqual(consent(request).status_code, 302)
            self.assertEqual(api.call_args.args[2]["parameters"], params)
        self.assertNotIn("mcp_oauth_request", session)

    def test_revoked_session_reauthenticates_and_preserves_oauth_on_get_and_post(self):
        from urllib.parse import parse_qs, urlsplit
        from apps.web.django.accounts.api_client import AuthAPIError

        params = {
            "client_id": "client",
            "scope": "catalog:read drafts:delete",
            "state": "state-with+special&characters",
            "redirect_uri": "http://127.0.0.1:33389/mcp-oauth-callback",
            "code_challenge": "challenge",
            "code_challenge_method": "S256",
            "resource": "http://127.0.0.1:8000/mcp",
            "response_type": "code",
        }
        info = {"scopes": ["catalog:read"], "integrations": []}
        for method, fail_at_consent in (
            ("get", False),
            ("post", False),
            ("post", True),
        ):
            with self.subTest(method=method, fail_at_consent=fail_at_consent):
                request = (
                    RequestFactory().get("/admin-ops/integration-consent/", params)
                    if method == "get"
                    else RequestFactory().post(
                        "/admin-ops/integration-consent/",
                        {"consent": "allow", "integration_id": "integration"},
                    )
                )
                request.session = {
                    "auth_api_token": "revoked",
                    "auth_api_user": {"id": 1, "is_staff": True},
                    "mcp_oauth_request": params.copy(),
                }
                responses = ([info] if fail_at_consent else []) + [
                    AuthAPIError("Sessão inválida.", 401)
                ]
                with patch(
                    "apps.web.django.admin_ops.integration_views._request",
                    side_effect=responses,
                ):
                    response = consent(request)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(urlsplit(response["Location"]).path, "/login/")
                target = parse_qs(urlsplit(response["Location"]).query)["next"][0]
                self.assertEqual(
                    urlsplit(target).path, "/admin-ops/integration-consent/"
                )
                self.assertEqual(
                    {k: v[0] for k, v in parse_qs(urlsplit(target).query).items()},
                    params,
                )
                self.assertNotIn("auth_api_token", request.session)
                self.assertNotIn("auth_api_user", request.session)
                self.assertEqual(request.session["mcp_oauth_request"], params)
                self.assertIn("no-store", response["Cache-Control"])
                # A fresh authenticated return must resume the same request.
                resumed = RequestFactory().get(target)
                resumed.session = {
                    **request.session,
                    "auth_api_token": "fresh",
                    "auth_api_user": {"id": 1, "is_staff": True},
                }
                with (
                    patch(
                        "apps.web.django.admin_ops.integration_views._request",
                        return_value=info,
                    ) as api,
                    patch(
                        "apps.web.django.admin_ops.integration_views.render",
                        return_value=HttpResponse(),
                    ),
                ):
                    self.assertEqual(consent(resumed).status_code, 200)
                self.assertEqual(api.call_args.args[2], params)
                self.assertEqual(api.call_args.args[3], "fresh")

    def test_non_auth_errors_preserve_session_and_do_not_force_login(self):
        from apps.web.django.accounts.api_client import AuthAPIError

        for code in (403, 422, 503):
            with self.subTest(code=code):
                request = RequestFactory().get(
                    "/admin-ops/integration-consent/", {"client_id": "client"}
                )
                request.session = {
                    "auth_api_token": "valid",
                    "auth_api_user": {"id": 1, "is_staff": True},
                }
                with (
                    patch(
                        "apps.web.django.admin_ops.integration_views._request",
                        side_effect=AuthAPIError("API error", code),
                    ),
                    patch(
                        "apps.web.django.admin_ops.integration_views.render",
                        return_value=HttpResponse(),
                    ) as render,
                ):
                    self.assertEqual(consent(request).status_code, 200)
                self.assertEqual(request.session["auth_api_token"], "valid")
                self.assertEqual(render.call_args.args[2]["admin_error"], "API error")
