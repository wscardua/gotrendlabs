from datetime import datetime, timezone as datetime_timezone
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase
from django.test.client import RequestFactory
from django.template.loader import render_to_string
from django.utils import timezone

from apps.web.django.admin_ops.integration_views import IntegrationForm, mark_scope_eligibility
from apps.api.backend_api.editorial_schemas import SCOPES


class IntegrationExpiryTests(SimpleTestCase):
    def test_all_scopes_have_matching_labels_and_survive_save(self):
        form = IntegrationForm(
            data={
                "name": "Pilot",
                "responsible_id": "1",
                "expires_at": "2027-01-05T22:30",
                "scopes": list(SCOPES),
                "drafts_per_day": "5",
                "calls_per_minute": "60",
                "concurrent_calls": "2",
            },
            responsible_choices=[(1, "Editor")],
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.payload()["scopes"], list(SCOPES))
        choices = dict(form.fields["scopes"].choices)
        self.assertEqual(tuple(choices), SCOPES)
        self.assertIn("analytics", str(choices["analytics:read"]).lower())
        self.assertIn("drafts", str(choices["drafts:write"]).lower())
        self.assertIn("revisão", str(choices["drafts:submit"]).lower())

    def test_consent_marks_missing_analytics_scope_before_submission(self):
        info = mark_scope_eligibility({
            "scopes": ["metrics:read", "analytics:read"],
            "integrations": [
                {"id": "old", "scopes": ["metrics:read"]},
                {"id": "ready", "scopes": ["metrics:read", "analytics:read"]},
            ],
        })
        self.assertEqual(info["integrations"][0]["missing_scopes"], ["analytics:read"])
        self.assertFalse(info["integrations"][0]["eligible"])
        self.assertTrue(info["integrations"][1]["eligible"])
        self.assertTrue(info["has_eligible"])

    def test_consent_with_no_eligible_integration_shows_edit_link_instead_of_empty_select(self):
        identifier = "cf5a19db-e153-4ab2-9ea2-5282fe20f6ae"
        info = mark_scope_eligibility({
            "client_name": "Local client",
            "scopes": ["analytics:read"],
            "redirect_uri": "http://127.0.0.1/callback",
            "integrations": [{"id": identifier, "name": "myintegration", "scopes": ["metrics:read"]}],
        })
        request = RequestFactory().get("/admin-ops/integration-consent/")
        request.session = {}
        html = render_to_string(
            "admin_ops/integration_consent.html",
            {"title": "Autorizar conexão MCP", "info": info},
            request=request,
        )
        self.assertIn("myintegration", html)
        self.assertIn("analytics:read", html)
        self.assertIn(f"/admin-ops/integrations/{identifier}/", html)
        self.assertNotIn("<select", html)

    def test_existing_utc_expiry_displays_local_date_across_day_boundary(self):
        for initial in (
            "2027-01-06T01:30:00+00:00",
            datetime(2027, 1, 6, 1, 30, tzinfo=datetime_timezone.utc),
        ):
            with (
                self.subTest(initial=initial),
                timezone.override(ZoneInfo("Asia/Tokyo")),
            ):
                form = IntegrationForm(initial={"expires_at": initial})
                self.assertIn('value="2027-01-05T22:30"', str(form["expires_at"]))

    def test_picker_posts_offset_aware_expiry_independent_of_active_timezone(self):
        with timezone.override(ZoneInfo("UTC")):
            form = IntegrationForm(
                data={
                    "name": "Pilot",
                    "responsible_id": "1",
                    "expires_at": "2027-01-05T22:30",
                    "drafts_per_day": "5",
                    "calls_per_minute": "60",
                    "concurrent_calls": "2",
                },
                responsible_choices=[(1, "Editor")],
            )
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.payload()["expires_at"], "2027-01-05T22:30:00-03:00")
            self.assertEqual(
                form.cleaned_data["expires_at"].astimezone(datetime_timezone.utc),
                datetime(2027, 1, 6, 1, 30, tzinfo=datetime_timezone.utc),
            )

    def test_invalid_calendar_date_remains_a_field_error(self):
        form = IntegrationForm(data={"expires_at": "2027-02-30T12:00"})
        self.assertFalse(form.is_valid())
        self.assertIn("expires_at", form.errors)
        self.assertIn('type="datetime-local"', str(form["expires_at"]))
