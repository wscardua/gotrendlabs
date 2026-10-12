import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from django.db import connection
from django.contrib.auth import get_user_model
from fastapi.testclient import TestClient

from apps.api.backend_api.main import app
from apps.api.backend_api.analytics import summary
from apps.api.backend_api.analytics_retention import retention
from apps.api.backend_api.db import get_connection
from tests.test_cases import AppendOnlyTransactionTestCase


class AnalyticsIntegrationTests(AppendOnlyTransactionTestCase):
    def tearDown(self):
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM gotrendlabs_analytics_ingestion_status")
                cursor.execute("DELETE FROM gotrendlabs_geolite_load_runs")
                for table in ("gotrendlabs_analytics_events", "gotrendlabs_analytics_views",
                              "gotrendlabs_analytics_sessions", "gotrendlabs_analytics_visitors"):
                    cursor.execute(f"DELETE FROM {table}")
        super().tearDown()

    def setUp(self):
        super().setUp()
        if connection.vendor != "postgresql":
            self.skipTest("Analytics usa PostgreSQL")
        self.environment = patch.dict(os.environ, {key: "" for key in (
            "FASTAPI_POSTGRES_DB", "FASTAPI_POSTGRES_USER", "FASTAPI_POSTGRES_PASSWORD",
            "FASTAPI_POSTGRES_HOST", "FASTAPI_POSTGRES_PORT")})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.api = TestClient(app)

    def test_anonymous_ingestion_deduplication_and_admin_guard(self):
        visitor, session, view, event = [str(uuid4()) for _ in range(4)]
        payload = {"visitor_id": visitor, "session_id": session, "events": [{
            "event_id": event, "view_id": view, "name": "page_viewed",
            "occurred_at": datetime.now(timezone.utc).isoformat(), "screen_key": "home",
        }]}
        first = self.api.post("/analytics/events", json=payload)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()["accepted"], 1)
        replay = self.api.post("/analytics/events", json=payload)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["accepted"], 0)
        with connection.cursor() as cursor:
            cursor.execute("SELECT auth_state, user_id FROM gotrendlabs_analytics_events WHERE id=%s", [event])
            self.assertEqual(cursor.fetchone(), ("anonymous", None))
        with get_connection() as api_connection:
            with api_connection.cursor() as cursor:
                report = summary(cursor)
            self.assertEqual(report["totals"]["visitors"], 1)
            self.assertEqual(report["funnel"]["visited"], 1)
            self.assertEqual(report["authenticated_funnel"]["confirmed_users"], 0)
            self.assertEqual(report["last_ingestion"]["received"], 1)
            self.assertEqual(report["last_ingestion"]["accepted"], 0)
            self.assertEqual(report["last_ingestion"]["duplicates"], 1)
            self.assertGreaterEqual(report["collection_24h"]["events"], 1)
        self.assertEqual(self.api.get("/admin/analytics/summary").status_code, 401)

    def test_platform_comparison_counts_distincts_and_respects_filters(self):
        now = datetime.now(timezone.utc)
        visitor = str(uuid4())
        user_id = 42  # Analytics stores a logical bigint user ID without a foreign key.
        sessions = []
        for platform, visitor_id in (("web", visitor), ("web", visitor),
                                     ("mobile", str(uuid4())), ("web", str(uuid4())),
                                     ("mobile", str(uuid4())), ("web", str(uuid4()))):
            session_id = str(uuid4())
            payload = {"visitor_id": visitor_id, "session_id": session_id, "events": [
                {"event_id": str(uuid4()), "view_id": str(uuid4()),
                 "name": "screen_viewed" if platform == "mobile" else "page_viewed",
                 "screen_key": "today", "occurred_at": now.isoformat()}
                for _ in range(2)
            ]}
            response = self.api.post("/analytics/events", json=payload,
                                     headers={"X-GoTrendLabs-Client": platform})
            self.assertEqual(response.status_code, 200, response.text)
            sessions.append(session_id)
            replay = self.api.post("/analytics/events", json=payload,
                                   headers={"X-GoTrendLabs-Client": platform})
            self.assertEqual(replay.json()["accepted"], 0)
        with connection.cursor() as cursor:
            for session in (sessions[0], sessions[2]):
                cursor.execute("UPDATE gotrendlabs_analytics_sessions SET country_code='BR', "
                               "region_code='SP', city_name='São Paulo' WHERE id=%s", [session])
            for session in (sessions[1], sessions[2]):
                cursor.execute("UPDATE gotrendlabs_analytics_events SET user_id=%s, "
                               "auth_state='authenticated', actor_type='user' WHERE session_id=%s",
                               [user_id, session])
            for session, actor in ((sessions[3], "staff"), (sessions[4], "bot")):
                cursor.execute("UPDATE gotrendlabs_analytics_events SET actor_type=%s "
                               "WHERE session_id=%s", [actor, session])
            cursor.execute("UPDATE gotrendlabs_analytics_events SET received_at=%s WHERE session_id=%s",
                           [now - timedelta(days=8), sessions[5]])
            cursor.execute("UPDATE gotrendlabs_analytics_events SET received_at=%s WHERE id="
                           "(SELECT id FROM gotrendlabs_analytics_events WHERE session_id=%s LIMIT 1)",
                           [now - timedelta(days=2), sessions[0]])
        with get_connection() as api_connection, api_connection.cursor() as cursor:
            with patch("apps.api.backend_api.analytics.datetime", wraps=datetime) as clock:
                clock.now.return_value = now
                report = summary(cursor)
                web, mobile = report["platforms"]
                self.assertEqual(web, {"platform": "web", "visitors": 1, "sessions": 2,
                                       "users": 1, "views": 4, "session_share": 66.7})
                self.assertEqual(mobile, {"platform": "mobile", "visitors": 1, "sessions": 1,
                                          "users": 1, "views": 2, "session_share": 33.3})
                self.assertEqual(report["totals"]["users"], 1)
                self.assertEqual(report["totals"]["sessions"], 3)
                self.assertEqual(len(report["platform_daily"]), 8)
                daily = {row["day"]: row for row in report["platform_daily"]}
                self.assertEqual(daily[now.date().isoformat()]["web_sessions"], 2)
                self.assertEqual(daily[(now - timedelta(days=2)).date().isoformat()]["web_sessions"], 1)
                self.assertEqual(daily[(now - timedelta(days=1)).date().isoformat()]["web_sessions"], 0)
                selected = summary(cursor, platform="mobile")
                self.assertEqual(len(selected["platforms"]), 1)
                self.assertEqual(selected["platforms"][0]["session_share"], 100.0)
                self.assertTrue(all(row["web_sessions"] == 0 for row in selected["platform_daily"]))
                regional = summary(cursor, region="SP", city="São Paulo")
                self.assertEqual([row["sessions"] for row in regional["platforms"]], [1, 1])
                self.assertEqual([row["session_share"] for row in regional["platforms"]], [50.0, 50.0])
                authenticated = summary(cursor, audience="authenticated")
                self.assertEqual([row["sessions"] for row in authenticated["platforms"]], [1, 1])
                anonymous = summary(cursor, audience="anonymous")
                self.assertEqual([row["sessions"] for row in anonymous["platforms"]], [1, 0])
                self.assertEqual([row["views"] for row in summary(cursor, days=1)["platforms"]], [3, 2])
                empty = summary(cursor, region="XX")
                self.assertTrue(all(row["sessions"] == 0 and row["session_share"] is None
                                    for row in empty["platforms"]))
                self.assertTrue(all(row["web_sessions"] == row["mobile_sessions"] == 0
                                    for row in empty["platform_daily"]))

    def test_collection_by_platform_is_global_human_and_reports_absent_history(self):
        now = datetime.now(timezone.utc)
        ids = []
        for platform in ("web", "mobile", "mobile"):
            event_id = str(uuid4())
            ids.append(event_id)
            response = self.api.post("/analytics/events", json={
                "visitor_id": str(uuid4()), "session_id": str(uuid4()), "events": [{
                    "event_id": event_id, "name": "screen_viewed", "view_id": str(uuid4()),
                    "screen_key": "today", "occurred_at": now.isoformat(),
                }]}, headers={"X-GoTrendLabs-Client": platform})
            self.assertEqual(response.status_code, 200, response.text)
        older = now - timedelta(days=2)
        with connection.cursor() as cursor:
            cursor.execute("UPDATE gotrendlabs_analytics_events SET received_at=%s WHERE id=%s", [older, ids[1]])
            cursor.execute("UPDATE gotrendlabs_analytics_events SET actor_type='bot' WHERE id=%s", [ids[2]])
        with get_connection() as api_connection, api_connection.cursor() as cursor:
            report = summary(cursor, days=1, platform="web", audience="authenticated", region="XX")
            self.assertEqual(report["totals"]["sessions"], 0)
            web, mobile = report["collection_platforms"]
            self.assertEqual(sum(row["events_24h"] for row in report["collection_platforms"]),
                             report["collection_24h"]["events"])
            self.assertEqual(web["platform"], "web")
            self.assertEqual(web["events_24h"], 1)
            self.assertIsNotNone(web["last_event_at"])
            self.assertEqual(mobile, {"platform": "mobile", "events_24h": 0, "last_event_at": older.isoformat()})
        with connection.cursor() as cursor:
            cursor.execute("UPDATE gotrendlabs_analytics_events SET actor_type='staff' WHERE id=%s", [ids[1]])
        with get_connection() as api_connection, api_connection.cursor() as cursor:
            self.assertEqual(summary(cursor)["collection_platforms"][1],
                             {"platform": "mobile", "events_24h": 0, "last_event_at": None})

    def test_platform_comparison_is_consistent_during_concurrent_ingestion(self):
        def visit(platform):
            payload = {"visitor_id": str(uuid4()), "session_id": str(uuid4()), "events": [{
                "event_id": str(uuid4()), "view_id": str(uuid4()), "name": "screen_viewed",
                "screen_key": "today", "occurred_at": datetime.now(timezone.utc).isoformat(),
            }]}
            response = self.api.post("/analytics/events", json=payload,
                                     headers={"X-GoTrendLabs-Client": platform})
            self.assertEqual(response.status_code, 200, response.text)

        visit("web")
        class ConcurrentIngestionCursor:
            inserted = False

            def __init__(self, cursor):
                self.cursor = cursor

            def execute(self, query, args=None):
                result = self.cursor.execute(query, args)
                if not self.inserted and "COUNT(DISTINCT s.visitor_id) AS visitors" in query:
                    # A second connection commits after the aggregate query's snapshot.
                    self.inserted = True
                    visit("mobile")
                return result

            def __getattr__(self, name):
                return getattr(self.cursor, name)

        with get_connection() as api_connection, api_connection.cursor() as cursor:
            concurrent = ConcurrentIngestionCursor(cursor)
            report = summary(concurrent)
            self.assertTrue(concurrent.inserted)
            self.assertEqual(sum(row["sessions"] for row in report["platforms"]),
                             report["totals"]["sessions"])
            self.assertEqual([row["sessions"] for row in report["platforms"]], [1, 0])
            self.assertEqual([row["session_share"] for row in report["platforms"]], [100.0, 0.0])
            fresh = summary(cursor)
            self.assertEqual(fresh["totals"]["sessions"], 2)
            self.assertEqual([row["session_share"] for row in fresh["platforms"]], [50.0, 50.0])

    def test_client_cannot_submit_confirmed_domain_event(self):
        payload = {"visitor_id": str(uuid4()), "session_id": str(uuid4()), "events": [{
            "event_id": str(uuid4()), "name": "prediction_created",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        }]}
        response = self.api.post("/analytics/events", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_collection_limit_identity_does_not_depend_on_client_visitor_id(self):
        identities = []
        with patch("apps.api.backend_api.main._enforce_rate_limit",
                   side_effect=lambda bucket, identity, **_: identities.append((bucket, identity))):
            for _ in range(2):
                payload = {"visitor_id": str(uuid4()), "session_id": str(uuid4()), "events": [{
                    "event_id": str(uuid4()), "name": "page_viewed",
                    "occurred_at": datetime.now(timezone.utc).isoformat(), "screen_key": "home",
                }]}
                self.assertEqual(self.api.post("/analytics/events", json=payload).status_code, 200)
        self.assertEqual(len(identities), 2)
        self.assertEqual(identities[0], identities[1])

    def test_session_funnel_requires_ordered_steps(self):
        when = datetime.now(timezone.utc)
        events = [
            {"event_id": str(uuid4()), "name": name,
             "occurred_at": (when + timedelta(seconds=index)).isoformat(),
             "screen_key": "market_detail" if index else "home",
             "properties": {"market_slug": "example"} if index else {}}
            for index, name in enumerate(("page_viewed", "market_detail_viewed",
                                          "prediction_started", "prediction_submit_clicked"))
        ]
        payload = {"visitor_id": str(uuid4()), "session_id": str(uuid4()), "events": events}
        response = self.api.post("/analytics/events", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        with get_connection() as api_connection:
            with api_connection.cursor() as cursor:
                funnel = summary(cursor)["funnel"]
        self.assertEqual(funnel, {"visited": 1, "market_opened": 1,
                                  "ticket_started": 1, "submit_clicked": 1})

    def test_geography_and_matured_ticket_abandonment(self):
        when = datetime.now(timezone.utc) - timedelta(hours=2)
        visitor, session = str(uuid4()), str(uuid4())
        payload = {"visitor_id": visitor, "session_id": session, "events": [
            {"event_id": str(uuid4()), "name": name,
             "occurred_at": (when + timedelta(seconds=index)).isoformat(),
             "properties": {"market_slug": "example"}}
            for index, name in enumerate(("prediction_started", "prediction_option_selected"))
        ]}
        self.assertEqual(self.api.post("/analytics/events", json=payload).status_code, 200)
        with connection.cursor() as cursor:
            cursor.execute("""UPDATE gotrendlabs_analytics_sessions
                           SET country_code='BR', region_code='SP', city_name='São Paulo',
                               last_seen_at=now() - interval '1 hour' WHERE id=%s""", [session])
        with get_connection() as api_connection:
            with api_connection.cursor() as cursor:
                report = summary(cursor)
                regional = summary(cursor, region="SP", city="São Paulo")
        self.assertEqual(report["regions"][0]["region_code"], "SP")
        self.assertEqual(report["cities"][0]["city_name"], "São Paulo")
        self.assertEqual(report["geo_daily"][0]["regional_sessions"], 1)
        self.assertEqual(report["trend_region"], "SP")
        self.assertEqual(report["region_daily"][0]["sessions"], 1)
        self.assertEqual(report["abandonment"]["eligible"], 1)
        self.assertEqual(report["abandonment"]["abandoned_after_choice"], 1)
        self.assertEqual(regional["totals"]["sessions"], 1)

    def test_retention_counts_new_sessions_and_matured_registered_cohorts(self):
        now = datetime(2026, 9, 29, 15, tzinfo=timezone.utc)
        cohort = datetime(2026, 9, 10, 15, tzinfo=timezone.utc)
        user = get_user_model().objects.create(username="retention_user", email="retention@example.test",
                                               date_joined=cohort)

        def observed(cursor, *, visitor, session, at, actor="visitor", user_id=None, first=False):
            if first:
                cursor.execute("INSERT INTO gotrendlabs_analytics_visitors(id, first_seen_at) VALUES (%s,%s)",
                               [visitor, at])
            cursor.execute("""INSERT INTO gotrendlabs_analytics_sessions
                           (id, visitor_id, platform, started_at, last_seen_at)
                           VALUES (%s,%s,'web',%s,%s)""", [session, visitor, at, at])
            cursor.execute("""INSERT INTO gotrendlabs_analytics_events
                           (id, session_id, user_id, name, platform, actor_type, auth_state,
                            occurred_at, received_at)
                           VALUES (%s,%s,%s,'page_viewed','web',%s,%s,%s,%s)""",
                           [str(uuid4()), session, user_id, actor,
                            "authenticated" if user_id else "anonymous", at, at])

        with connection.cursor() as cursor:
            seed = str(uuid4())
            observed(cursor, visitor=seed, session=str(uuid4()), at=cohort - timedelta(days=2), first=True)
            visitor = str(uuid4())
            observed(cursor, visitor=visitor, session=str(uuid4()), at=cohort, first=True)
            observed(cursor, visitor=visitor, session=str(uuid4()), at=cohort + timedelta(days=1))
            registered_visitor = str(uuid4())
            observed(cursor, visitor=registered_visitor, session=str(uuid4()), at=cohort,
                     actor="user", user_id=user.id, first=True)
            observed(cursor, visitor=registered_visitor, session=str(uuid4()), at=cohort + timedelta(days=7),
                     actor="user", user_id=user.id)
        with get_connection() as api_connection:
            with api_connection.cursor() as cursor:
                result = retention(cursor, now=now)
        self.assertEqual(result["visitors"]["totals"]["d1"],
                         {"eligible": 1, "returned": 1, "rate": 100})
        self.assertEqual(result["visitors"]["totals"]["d7"],
                         {"eligible": 1, "returned": 0, "rate": 0})
        self.assertEqual(result["registered"]["totals"]["d7"],
                         {"eligible": 1, "returned": 1, "rate": 100})
        self.assertIsNone(result["registered"]["totals"]["d30"]["rate"])
