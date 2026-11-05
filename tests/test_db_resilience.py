"""Bounded connections and observable outage behavior."""

import os
import asyncio
import json
import threading
import unittest
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from fastapi.testclient import TestClient

from apps.api.backend_api import db
from apps.api.backend_api import main as api_main
from apps.api.backend_api.main import app
from apps.web.django.accounts.api_client import AuthAPIError
from apps.web.django.markets import views
from apps.web.django.core import capacity
from apps.web.django.system_logs import services as log_services


class ConnectionPoolTests(unittest.TestCase):
    """Run against an isolated PostgreSQL using the FASTAPI_POSTGRES_* env."""

    @classmethod
    def setUpClass(cls):
        if not os.environ.get("GTL_RESILIENCE_TEST_DB"):
            raise unittest.SkipTest("isolated PostgreSQL was not configured")
        cls.original = {name: os.environ.get(name) for name in ("GOTRENDLABS_DB_POOL_MAX", "GOTRENDLABS_DB_POOL_WAITING")}
        os.environ["GOTRENDLABS_DB_POOL_MAX"] = "2"
        os.environ["GOTRENDLABS_DB_POOL_WAITING"] = "2"
        db.close_pools()

    @classmethod
    def tearDownClass(cls):
        db.close_pools()
        for name, value in cls.original.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_concurrent_limit_queue_timeout_and_recovery(self):
        with db.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        acquired = threading.Event()
        release = threading.Event()
        lock = threading.Lock()
        count = 0

        def holder():
            nonlocal count
            with db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                with lock:
                    count += 1
                    if count == 2:
                        acquired.set()
                release.wait(5)

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(holder)
            second = executor.submit(holder)
            self.assertTrue(acquired.wait(5))
            try:
                with self.assertRaises(db.DatabaseCapacityError):
                    with db.get_connection():
                        pass
            finally:
                release.set()
            first.result(timeout=5)
            second.result(timeout=5)
        with db.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS healthy")
                self.assertEqual(cursor.fetchone()["healthy"], 1)

    def test_rollback_and_pool_close(self):
        with db.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE TEMP TABLE resilience_rollback (value integer)")
        with self.assertRaises(ValueError):
            with db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("CREATE TABLE resilience_rollback_check (value integer)")
                    cursor.execute("INSERT INTO resilience_rollback_check VALUES (1)")
                raise ValueError("abort")
        with db.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT to_regclass('resilience_rollback_check') AS table_name")
                self.assertIsNone(cursor.fetchone()["table_name"])
        db.close_pools()
        with db.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

    def test_pool_does_not_reuse_a_connection_for_another_role(self):
        reader_role = f"resilience_reader_{uuid4().hex[:8]}"
        original_user = os.environ.get("FASTAPI_POSTGRES_USER")
        original_password = os.environ.get("FASTAPI_POSTGRES_PASSWORD")
        created = False
        try:
            with db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"CREATE ROLE {reader_role} LOGIN PASSWORD 'resilience_test_only'")
            created = True
            os.environ["FASTAPI_POSTGRES_USER"] = reader_role
            os.environ["FASTAPI_POSTGRES_PASSWORD"] = "resilience_test_only"
            with db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT current_user AS role")
                    self.assertEqual(cursor.fetchone()["role"], reader_role)
        finally:
            for name, value in (("FASTAPI_POSTGRES_USER", original_user), ("FASTAPI_POSTGRES_PASSWORD", original_password)):
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
            db.close_pools()
            if created:
                with db.get_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(f"DROP ROLE {reader_role}")


class ApiUnavailableTests(unittest.TestCase):
    def test_read_capacity_returns_safe_503(self):
        with patch("apps.api.backend_api.main.get_connection", side_effect=db.DatabaseCapacityError("private")), patch("apps.api.backend_api.main.submit_system_event"):
            response = TestClient(app).get("/markets")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["code"], "dependency_unavailable")
        self.assertNotIn("private", response.text)

    def test_write_pool_rejection_is_known_to_precede_operation(self):
        with patch("apps.api.backend_api.main.get_connection", side_effect=db.DatabaseCapacityError("private")), patch("apps.api.backend_api.main.submit_system_event"):
            response = TestClient(app).post("/markets/example/view")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["code"], "dependency_unavailable")

    def test_write_connection_loss_does_not_claim_rollback(self):
        from psycopg import OperationalError

        with patch("apps.api.backend_api.main.get_connection", side_effect=OperationalError("private")), patch("apps.api.backend_api.main.submit_system_event"):
            response = TestClient(app).post("/markets/example/view")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["code"], "operation_indeterminate")
        self.assertNotIn("private", response.text)

    def test_admission_rejects_without_entering_domain(self):
        with patch.object(api_main, "_api_capacity", asyncio.Semaphore(0)), patch("apps.api.backend_api.main.get_connection") as connect:
            response = TestClient(app).get("/markets")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["code"], "dependency_unavailable")
        connect.assert_not_called()

    def test_health_keeps_mobile_payload_when_admission_is_full(self):
        with patch.object(api_main, "_api_capacity", asyncio.Semaphore(0)), patch("apps.api.backend_api.main.get_connection", side_effect=db.DatabaseCapacityError("full")), patch("apps.api.backend_api.main.submit_system_event"):
            response = TestClient(app).get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")
        self.assertIn("mobile", response.json())

    def test_health_burst_is_bounded_without_blocking_normal_requests(self):
        def check(_):
            return TestClient(app).get("/health")

        gate = threading.BoundedSemaphore(1)
        gate.acquire()
        with patch.object(api_main, "_health_capacity", gate), patch("apps.api.backend_api.main.get_connection") as connect, patch("apps.api.backend_api.main.submit_system_event"), ThreadPoolExecutor(max_workers=12) as executor:
            try:
                health_responses = list(executor.map(check, range(20)))
                normal = TestClient(app).get("/")
            finally:
                gate.release()
        self.assertTrue(all(response.status_code == 503 for response in health_responses))
        self.assertTrue(all(response.json()["status"] == "degraded" for response in health_responses))
        self.assertTrue(all(response.json()["checks"]["database"] == "not_checked" for response in health_responses))
        self.assertTrue(all("mobile" in response.json() for response in health_responses))
        self.assertEqual(normal.status_code, 200)
        connect.assert_not_called()

    def test_health_allows_two_in_flight_then_recovers(self):
        async def exercise():
            entered = asyncio.Event()
            release = asyncio.Event()
            active = 0
            peak = 0

            async def downstream(_request):
                nonlocal active, peak
                active += 1
                peak = max(peak, active)
                if active == 2:
                    entered.set()
                await release.wait()
                active -= 1
                return api_main.JSONResponse({"status": "ok"})

            def request():
                return api_main.Request({"type": "http", "method": "GET", "path": "/health", "raw_path": b"/health", "query_string": b"", "headers": [], "scheme": "http", "server": ("testserver", 80)})

            first = asyncio.create_task(api_main.admission_middleware(request(), downstream))
            second = asyncio.create_task(api_main.admission_middleware(request(), downstream))
            await asyncio.wait_for(entered.wait(), timeout=2)
            rejected = await api_main.admission_middleware(request(), downstream)
            self.assertEqual(rejected.status_code, 503)
            self.assertEqual(peak, 2)
            release.set()
            self.assertEqual((await first).status_code, 200)
            self.assertEqual((await second).status_code, 200)
            recovered = await api_main.admission_middleware(request(), downstream)
            self.assertEqual(recovered.status_code, 200)

        with patch.object(api_main, "_health_capacity", threading.BoundedSemaphore(2)), patch("apps.api.backend_api.main.get_connection") as connect:
            asyncio.run(exercise())
        connect.assert_not_called()


class MarketUnavailableTests(SimpleTestCase):
    def request(self):
        request = RequestFactory().get("/markets/example/")
        request.session = {}
        return request

    def test_detail_timeout_never_reads_local_market_or_tracks_view(self):
        with patch.object(views, "get_market", side_effect=AuthAPIError("timeout", 503)), patch("apps.web.django.core.domain_client.local_market") as fallback, patch.object(views, "track_market_view") as track:
            response = views.detail(self.request(), "example")
        self.assertEqual(response.status_code, 503)
        self.assertIn(b"temporariamente indispon", response.content)
        fallback.assert_not_called()
        track.assert_not_called()

    def test_integrity_timeout_never_reads_local_market(self):
        with patch.object(views, "get_market", side_effect=AuthAPIError("timeout", 503)), patch("apps.web.django.core.domain_client.local_market") as fallback:
            response = views.integrity(self.request(), "example")
        self.assertEqual(response.status_code, 503)
        fallback.assert_not_called()

    def test_missing_market_stays_404(self):
        with patch.object(views, "get_market", side_effect=AuthAPIError("missing", 404)):
            with self.assertRaises(Exception) as caught:
                views.detail(self.request(), "example")
        self.assertEqual(caught.exception.__class__.__name__, "Http404")

    def test_share_tracking_preserves_missing_and_draft_404(self):
        from apps.web.django.core import views as core_views

        request = RequestFactory().post("/share/market/example/track/")
        for slug in ("missing", "draft"):
            with self.subTest(slug=slug), patch.object(core_views, "track_market_share", side_effect=AuthAPIError("missing", 404)):
                response = core_views.share_market_track(request, slug)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(json.loads(response.content), {"tracked": False})

    def test_share_tracking_unavailable_is_503(self):
        from apps.web.django.core import views as core_views

        request = RequestFactory().post("/share/market/example/track/")
        with patch.object(core_views, "track_market_share", side_effect=AuthAPIError("unavailable", 503)):
            response = core_views.share_market_track(request, "example")
        self.assertEqual(response.status_code, 503)


class RequestAdmissionTests(SimpleTestCase):
    def test_database_exception_page_does_not_render_templates(self):
        from django.db import OperationalError

        middleware = capacity.RequestCapacityMiddleware(lambda _request: None)
        with patch("django.template.loader.get_template", side_effect=AssertionError("template accessed")):
            response = middleware.process_exception(RequestFactory().get("/markets/example/"), OperationalError("private"))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"private", response.content)
        self.assertIn(b'href="/markets/example/"', response.content)

    def test_integrity_error_is_not_misreported_as_capacity(self):
        from django.db import IntegrityError

        middleware = capacity.RequestCapacityMiddleware(lambda _request: None)
        response = middleware.process_exception(RequestFactory().post("/admin/"), IntegrityError("constraint"))
        self.assertIsNone(response)

    def test_database_exception_in_detail_returns_503_through_django_stack(self):
        from django.db import OperationalError
        from django.test import Client

        with patch("apps.web.django.markets.views.get_market", side_effect=OperationalError("private")):
            response = Client().get("/markets/example/")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"private", response.content)

    def test_web_overflow_returns_static_503_and_recovers(self):
        entered = threading.Event()
        release = threading.Event()
        gate = threading.BoundedSemaphore(1)

        def slow_view(_request):
            entered.set()
            release.wait(3)
            return capacity.HttpResponse("ok")

        middleware = capacity.RequestCapacityMiddleware(slow_view)
        with patch.object(capacity, "_available", gate), ThreadPoolExecutor(max_workers=1) as executor:
            first = executor.submit(middleware, RequestFactory().get("/first"))
            self.assertTrue(entered.wait(2))
            try:
                rejected = middleware(RequestFactory().get("/second"))
                self.assertEqual(rejected.status_code, 503)
                self.assertIn(b"temporariamente indispon", rejected.content)
                self.assertIn(b'href="/second"', rejected.content)
            finally:
                release.set()
            self.assertEqual(first.result(timeout=3).status_code, 200)
            self.assertEqual(middleware(RequestFactory().get("/third")).status_code, 200)

    def test_capacity_page_never_offers_post_replay(self):
        middleware = capacity.RequestCapacityMiddleware(lambda _request: capacity.HttpResponse("ok"))
        with patch.object(capacity, "_available", threading.BoundedSemaphore(1)):
            self.assertTrue(capacity._available.acquire(blocking=False))
            try:
                response = middleware(RequestFactory().post("/markets/example/predict/"))
            finally:
                capacity._available.release()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"Tentar novamente</a>", response.content)
        self.assertIn(b'href="/"', response.content)

    def test_short_web_burst_waits_without_extra_database_slots(self):
        barrier = threading.Barrier(20)
        lock = threading.Lock()
        active = 0
        peak = 0

        def short_view(_request):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            try:
                import time

                time.sleep(0.1)
                return capacity.HttpResponse("ok")
            finally:
                with lock:
                    active -= 1

        middleware = capacity.RequestCapacityMiddleware(short_view)

        def request(_):
            barrier.wait()
            return middleware(RequestFactory().get("/markets/")).status_code

        with ThreadPoolExecutor(max_workers=20) as executor:
            statuses = list(executor.map(request, range(20)))
        self.assertEqual(statuses.count(200), 20)
        self.assertLessEqual(peak, 5)

    def test_web_waiting_queue_is_bounded_and_releases_slot(self):
        entered = threading.Event()
        release = threading.Event()
        waiting = threading.Event()

        class TrackedWaiting:
            def __init__(self):
                self.slot = threading.BoundedSemaphore(1)

            def acquire(self, blocking=False):
                result = self.slot.acquire(blocking=blocking)
                if result:
                    waiting.set()
                return result

            def release(self):
                self.slot.release()

        def slow_view(_request):
            entered.set()
            release.wait(3)
            return capacity.HttpResponse("ok")

        middleware = capacity.RequestCapacityMiddleware(slow_view)
        with patch.object(capacity, "_available", threading.BoundedSemaphore(1)), patch.object(capacity, "_waiting", TrackedWaiting()):
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(middleware, RequestFactory().get("/first"))
                self.assertTrue(entered.wait(2))
                second = executor.submit(middleware, RequestFactory().get("/second"))
                self.assertTrue(waiting.wait(2))
                self.assertEqual(middleware(RequestFactory().get("/overflow")).status_code, 503)
                release.set()
                self.assertEqual(first.result(timeout=3).status_code, 200)
                self.assertEqual(second.result(timeout=3).status_code, 200)


class TechnicalLogCapacityTests(SimpleTestCase):
    def test_background_technical_log_is_bounded_and_never_delays_response(self):
        import time

        entered = threading.Event()
        release = threading.Event()
        finished = threading.Event()

        def stalled_write(**_kwargs):
            entered.set()
            release.wait(3)
            finished.set()

        with patch.object(log_services, "log_system_event", side_effect=stalled_write) as writer:
            started = time.monotonic()
            self.assertIsNone(log_services.submit_system_event(message="first"))
            self.assertLess(time.monotonic() - started, 0.2)
            self.assertTrue(entered.wait(2))
            started = time.monotonic()
            self.assertIsNone(log_services.submit_system_event(message="dropped"))
            self.assertLess(time.monotonic() - started, 0.2)
            self.assertEqual(writer.call_count, 1)
            release.set()
            self.assertTrue(finished.wait(2))
            for _ in range(100):
                if log_services._submit_slot.acquire(blocking=False):
                    log_services._submit_slot.release()
                    break
                time.sleep(0.001)
            else:
                self.fail("background logging slot was not released")

    def test_root_logging_handler_never_writes_synchronously_on_event_loop(self):
        import logging
        from apps.web.django.system_logs.logging import DatabaseLogHandler

        async def emit():
            with patch("apps.web.django.system_logs.logging.submit_system_event") as writer:
                DatabaseLogHandler().emit(logging.LogRecord("test", logging.INFO, __file__, 1, "event", (), None))
                writer.assert_not_called()

        asyncio.run(emit())

    def test_logger_drops_concurrent_technical_entry_without_waiting(self):
        entered = threading.Event()
        release = threading.Event()

        def slow_write(**_kwargs):
            entered.set()
            release.wait(3)
            return 1

        with patch.object(log_services, "_write_system_event", side_effect=slow_write) as writer:
            with ThreadPoolExecutor(max_workers=1) as executor:
                first = executor.submit(log_services.log_system_event, message="first")
                self.assertTrue(entered.wait(2))
                try:
                    self.assertIsNone(log_services.log_system_event(message="second"))
                finally:
                    release.set()
                self.assertEqual(first.result(timeout=3), 1)
            self.assertEqual(writer.call_count, 1)

    def test_failed_retention_lookup_is_cached_briefly_and_logging_does_not_raise(self):
        log_services._retention_cache.update(days=None, until=0)
        with patch.object(log_services, "get_connection", side_effect=db.DatabaseCapacityError("full")) as connect:
            self.assertIsNone(log_services.log_system_event(message="one"))
            self.assertIsNone(log_services.log_system_event(message="two"))
        self.assertEqual(connect.call_count, 3)  # one retention lookup, two best-effort writes
        log_services._retention_cache.update(days=None, until=0)
