import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from apps.api.backend_api.analytics import AnalyticsBatch, AnalyticsEvent, _safe_properties, _source_ip
from apps.api.backend_api.geolite_loader import install


class AnalyticsContractTests(unittest.TestCase):
    def event(self, name, properties=None):
        return AnalyticsEvent(event_id=uuid4(), name=name, occurred_at=datetime.now(timezone.utc),
                              screen_key="market_detail", properties=properties or {})

    def test_client_cannot_claim_domain_completion(self):
        with self.assertRaises(HTTPException):
            _safe_properties(self.event("prediction_created"))

    def test_unlisted_property_cannot_leak_form_content(self):
        with self.assertRaises(HTTPException):
            _safe_properties(self.event("page_viewed", {"email": "someone@example.com"}))

    def test_scroll_milestone_is_bounded(self):
        self.assertEqual(_safe_properties(self.event("scroll_reached", {"percent": 75})), '{"percent": 75}')
        with self.assertRaises(HTTPException):
            _safe_properties(self.event("scroll_reached", {"percent": 73}))

    def test_batch_is_limited_and_requires_ids(self):
        valid = dict(visitor_id=uuid4(), session_id=uuid4(), events=[self.event("page_viewed")])
        self.assertEqual(len(AnalyticsBatch(**valid).events), 1)
        with self.assertRaises(ValueError):
            AnalyticsBatch(**{**valid, "events": valid["events"] * 21})
        with self.assertRaises(ValueError):
            AnalyticsBatch(**{**valid, "utm_campaign": "person@example.com"})

    def test_unsigned_client_ip_header_is_ignored(self):
        request = SimpleNamespace(headers={"x-analytics-client-ip": "8.8.8.8"},
                                  client=SimpleNamespace(host="127.0.0.1"))
        with patch.dict("os.environ", {"GOTRENDLABS_ANALYTICS_PROXY_SECRET": "secret",
                                       "GOTRENDLABS_ANALYTICS_TRUSTED_PROXY_CIDRS": ""}):
            self.assertEqual(_source_ip(request), "127.0.0.1")

    def test_invalid_geolite_update_preserves_active_database_and_records_failure(self):
        with TemporaryDirectory() as directory:
            active = Path(directory) / "GeoLite2-City.mmdb"
            active.write_bytes(b"existing database")
            source = Path(directory) / "download.mmdb"
            source.write_bytes(b"corrupt database")
            with patch("apps.api.backend_api.geolite_loader._record_run") as record:
                with self.assertRaises(Exception):
                    install(source, active)
            self.assertEqual(active.read_bytes(), b"existing database")
            self.assertEqual(record.call_args.args[1], "failed")
