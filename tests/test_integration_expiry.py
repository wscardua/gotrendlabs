from datetime import datetime, timezone as datetime_timezone
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase
from django.utils import timezone

from apps.web.django.admin_ops.integration_views import IntegrationForm


class IntegrationExpiryTests(SimpleTestCase):
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
