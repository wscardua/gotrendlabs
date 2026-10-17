from datetime import datetime, timezone as datetime_timezone

from django.test import SimpleTestCase
from django.utils import timezone

from apps.web.django.admin_ops.views import _email_delivery_label


class AdminDeliveryDateLabelTests(SimpleTestCase):
    def test_email_and_push_dates_use_current_timezone_and_existing_format(self):
        instant = datetime(2026, 10, 17, 20, 46, 59, tzinfo=datetime_timezone.utc)
        for zone, expected in (
            ('America/Sao_Paulo', '17/10/2026 17:46'),
            ('UTC', '17/10/2026 20:46'),
        ):
            with self.subTest(zone=zone), timezone.override(zone):
                self.assertEqual(_email_delivery_label(instant), expected)

    def test_absent_delivery_timestamp_keeps_placeholder(self):
        self.assertEqual(_email_delivery_label(None), '-')
