import json
from unittest.mock import patch
from uuid import uuid4

from django.test import Client, TestCase


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
