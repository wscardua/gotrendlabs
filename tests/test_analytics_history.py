import os
import json
from datetime import datetime, time, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4
from zoneinfo import ZoneInfo

from django.db import connection
from django.contrib.auth import get_user_model
from apps.web.django.markets.models import MarketCategory, MarketSubcategory, Market, MarketOption, Prediction

from apps.api.backend_api.analytics import prune
from apps.api.backend_api.analytics_history import actor_secret, consolidate_day, consolidate_pending, forget_actor
from apps.api.backend_api.analytics_reports import overview, series, compare, editorial, markets, market, retention, coverage
from apps.api.backend_api.db import get_connection
from tests.test_cases import AppendOnlyTransactionTestCase


ZONE = ZoneInfo("America/Sao_Paulo")


class AnalyticsHistoryTests(AppendOnlyTransactionTestCase):
    def tearDown(self):
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                for table in (
                    "gotrendlabs_analytics_history_funnel", "gotrendlabs_analytics_history_actors",
                    "gotrendlabs_analytics_history_counts", "gotrendlabs_analytics_history_days",
                    "gotrendlabs_analytics_market_publication",
                    "gotrendlabs_analytics_events", "gotrendlabs_analytics_views",
                    "gotrendlabs_analytics_sessions", "gotrendlabs_analytics_visitors",
                ):
                    cursor.execute(f"DELETE FROM {table}")
        super().tearDown()

    def setUp(self):
        super().setUp()
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL required")
        self.env = patch.dict(os.environ, {key: "" for key in (
            "FASTAPI_POSTGRES_DB", "FASTAPI_POSTGRES_USER", "FASTAPI_POSTGRES_PASSWORD",
            "FASTAPI_POSTGRES_HOST", "FASTAPI_POSTGRES_PORT")})
        self.env.start()
        self.addCleanup(self.env.stop)

    def event(self, visitor, session, when, name="page_viewed", properties=None):
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO gotrendlabs_analytics_visitors(id,first_seen_at,first_session_id) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING", (visitor,when,session))
            cursor.execute("""INSERT INTO gotrendlabs_analytics_sessions(id,visitor_id,platform,started_at,last_seen_at)
                VALUES (%s,%s,'web',%s,%s) ON CONFLICT(id) DO UPDATE SET last_seen_at=excluded.last_seen_at""", (session,visitor,when,when))
            cursor.execute("""INSERT INTO gotrendlabs_analytics_events
                (id,session_id,name,platform,actor_type,auth_state,occurred_at,received_at,properties)
                VALUES (%s,%s,%s,'web','visitor','anonymous',%s,%s,%s::jsonb)""",
                (uuid4(),session,name,when,when,json.dumps(properties or {})))

    def test_ten_year_history_exact_distinct_and_guarded_purge(self):
        old=(datetime.now(ZONE)-timedelta(days=3653)).replace(hour=12,minute=0,second=0,microsecond=0)
        recent=datetime.now(ZONE)-timedelta(days=1)
        visitor=uuid4()
        self.event(visitor,uuid4(),old)
        self.event(visitor,uuid4(),recent)
        with get_connection() as db, db.cursor() as cur:
            before=overview(cur,all_history=True)
            self.assertEqual(before["actors"]["visitors"],1)
            self.assertNotIn(str(visitor),json.dumps(before,default=str))
            self.assertEqual(before["counts"]["page_viewed"],2)
            self.assertEqual(consolidate_day(cur,old.date()),1)
            self.assertEqual(consolidate_day(cur,old.date()),1)
            result=prune(cur,retention_days=30)
            self.assertEqual(result["events"],1)
            after=overview(cur,all_history=True)
            self.assertEqual(after["actors"]["visitors"],1)
            self.assertEqual(after["counts"]["page_viewed"],2)
            one_year=overview(cur,start=recent.date()-timedelta(days=365),
                              end=recent.date()+timedelta(days=1))
            self.assertEqual(one_year["counts"]["page_viewed"],1)
            first_page=series(cur,all_history=True,grain="year",limit=2)
            self.assertTrue(first_page["has_more"])
            second_page=series(cur,all_history=True,grain="year",limit=2,
                               after=first_page["next_cursor"],revision=first_page["revision"])
            self.assertGreater(second_page["items"][0]["bucket_start"],
                               first_page["items"][-1]["bucket_start"])
            comparison=compare(cur,start=recent.date(),end=recent.date()+timedelta(days=1),
                               previous_equivalent=True)
            self.assertIsNone(comparison["delta"]["new_signups"]["relative"])

    def test_unconsolidated_old_event_survives_purge(self):
        old=datetime.now(timezone.utc)-timedelta(days=400)
        self.event(uuid4(),uuid4(),old)
        with get_connection() as db, db.cursor() as cur:
            self.assertEqual(prune(cur,retention_days=30)["events"],0)
            cur.execute("SELECT count(*) AS n FROM gotrendlabs_analytics_events")
            self.assertEqual(cur.fetchone()["n"],1)

    def test_production_requires_stable_actor_key(self):
        with patch.dict(os.environ,{"GOTRENDLABS_ENV":"production","GOTRENDLABS_ANALYTICS_ACTOR_KEY":""}):
            with self.assertRaisesRegex(RuntimeError,"analytics_actor_key_not_configured"):
                actor_secret()

    def test_late_event_reopens_checkpoint_before_prune(self):
        old=(datetime.now(ZONE)-timedelta(days=40)).replace(hour=12,minute=0,second=0,microsecond=0)
        with get_connection() as db, db.cursor() as cur:
            self.event(uuid4(),uuid4(),old)
            self.assertEqual(consolidate_day(cur,old.date()),1)
        self.event(uuid4(),uuid4(),old+timedelta(minutes=5))
        result=consolidate_pending(limit_days=1)
        self.assertEqual(result["days"],1)
        with get_connection() as db, db.cursor() as cur:
            cur.execute("SELECT source_events FROM gotrendlabs_analytics_history_days WHERE day=%s",(old.date(),))
            self.assertEqual(cur.fetchone()["source_events"],2)
            self.assertEqual(overview(cur,start=old.date(),end=old.date()+timedelta(days=1))["counts"]["page_viewed"],2)

    def test_window_is_local_and_end_exclusive(self):
        day=datetime.now(ZONE).date()-timedelta(days=2)
        boundary=datetime.combine(day,time(0),ZONE)
        self.event(uuid4(),uuid4(),boundary)
        self.event(uuid4(),uuid4(),boundary+timedelta(days=1),name="screen_viewed")
        with get_connection() as db, db.cursor() as cur:
            self.assertEqual(overview(cur,start=day,end=day+timedelta(days=1))["counts"]["page_viewed"],1)
            self.assertEqual(overview(cur,start=day+timedelta(days=1),end=day+timedelta(days=2))["counts"]["page_viewed"],0)

    def test_editorial_lists_unexposed_market_and_publication_taxonomy(self):
        now=datetime.now(ZONE)-timedelta(days=2)
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO gotrendlabs_analytics_market_publication
                (market_id,published_at,category_id,category_name,subcategory_id,subcategory_name,
                 event_id,event_name,kind,close_at,provenance)
                VALUES (900001,%s,7,'Ciência',8,'Espaço',9,'Missão','binary',%s,'reconstructed_current')""",
                (now,now+timedelta(days=7)))
        with get_connection() as db, db.cursor() as cur:
            listed=markets(cur,start=now.date(),end=now.date()+timedelta(days=1))
            self.assertIsNone(listed["items"][0]["observed"]["market_card_viewed"])
            detail=market(cur,900001,start=now.date(),end=now.date()+timedelta(days=1))
            self.assertIsNone(detail["observed_exposure"]["impressions"])
            grouped=editorial(cur,dimension="category",start=now.date(),
                              end=now.date()+timedelta(days=1))
            self.assertEqual(grouped["items"][0]["markets"],1)
            self.assertEqual(grouped["items"][0]["reconstructed_markets"],1)

    def test_visitor_d1_requires_different_session(self):
        day=datetime.now(ZONE).date()-timedelta(days=4)
        self.event(uuid4(),uuid4(),datetime.combine(day-timedelta(days=1),time(12),ZONE))
        visitor=uuid4()
        self.event(visitor,uuid4(),datetime.combine(day,time(12),ZONE))
        self.event(visitor,uuid4(),datetime.combine(day+timedelta(days=1),time(12),ZONE))
        with get_connection() as db, db.cursor() as cur:
            result=retention(cur,start=day,end=day+timedelta(days=1))
            self.assertEqual(result["cohorts"]["visitor"]["d1"]["eligible"],1)
            self.assertEqual(result["cohorts"]["visitor"]["d1"]["returned"],1)

    def test_funnel_respects_order_before_and_after_consolidation(self):
        day=datetime.now(ZONE).date()-timedelta(days=12)
        start=datetime.combine(day,time(12),ZONE)
        visitor,session=uuid4(),uuid4()
        props={"market_slug":"sample-market"}
        self.event(visitor,session,start,"prediction_started",props)
        self.event(visitor,session,start+timedelta(minutes=1),"prediction_preview_viewed",props)
        self.event(visitor,session,start+timedelta(minutes=2),"prediction_option_selected",props)
        self.event(visitor,session,start+timedelta(minutes=3),"prediction_submit_clicked",props)
        with get_connection() as db, db.cursor() as cur:
            before=overview(cur,start=day,end=day+timedelta(days=1))
            self.assertEqual(before["funnel"]["chosen"],1)
            self.assertEqual(before["funnel"]["previewed"],0)
            self.assertEqual(before["funnel"]["submit_clicked"],1)
            consolidate_day(cur,day)
            after=overview(cur,start=day,end=day+timedelta(days=1))
            self.assertEqual(after["funnel"]["previewed"],0)
            self.assertEqual(after["funnel"]["submit_clicked"],1)

    def test_unobserved_metric_is_null_and_filter_scope_is_explicit(self):
        day=datetime.now(ZONE).date()-timedelta(days=2)
        self.event(uuid4(),uuid4(),datetime.combine(day,time(12),ZONE))
        with get_connection() as db, db.cursor() as cur:
            report=overview(cur,start=day,end=day+timedelta(days=1),platform="mobile")
            self.assertIsNone(report["counts"]["prediction_preview_viewed"])
            self.assertEqual(report["filters"]["observed_events_and_actors"]["platform"],"mobile")
            self.assertEqual(report["filters"]["signups_participation_funnel_stake_social_quality"]["platform"],"all")
            self.assertEqual(coverage(cur)["coverage"]["events"]["prediction_preview_viewed"]["availability"],"no_observations")

    def test_historical_actor_key_is_pseudonymous_and_erasure_reconciles_day(self):
        day=datetime.now(ZONE).date()-timedelta(days=12)
        visitor=uuid4()
        self.event(visitor,uuid4(),datetime.combine(day,time(12),ZONE))
        with get_connection() as db, db.cursor() as cur:
            consolidate_day(cur,day)
            cur.execute("SELECT actor_key FROM gotrendlabs_analytics_history_actors WHERE actor_kind='visitor' LIMIT 1")
            key=cur.fetchone()["actor_key"]
            self.assertEqual(len(key),64)
            self.assertNotIn(str(visitor),key)
            forget_actor(cur,"visitor",visitor)
            cur.execute("SELECT source_events FROM gotrendlabs_analytics_history_days WHERE day=%s",(day,))
            self.assertEqual(cur.fetchone()["source_events"],0)
            self.assertEqual(overview(cur,start=day,end=day+timedelta(days=1))["actors"]["visitors"],0)

    def test_visitor_retention_survives_hmac_consolidation_and_purge(self):
        day=datetime.now(ZONE).date()-timedelta(days=45)
        first=datetime.combine(day,time(12),ZONE)
        self.event(uuid4(),uuid4(),first-timedelta(days=1))
        visitor=uuid4()
        self.event(visitor,uuid4(),first)
        self.event(visitor,uuid4(),first+timedelta(days=1))
        with get_connection() as db, db.cursor() as cur:
            for archived_day in (day-timedelta(days=1),day,day+timedelta(days=1)):
                consolidate_day(cur,archived_day)
            prune(cur,retention_days=30)
            result=retention(cur,start=day,end=day+timedelta(days=1))
            self.assertEqual(result["cohorts"]["visitor"]["d1"]["eligible"],1)
            self.assertEqual(result["cohorts"]["visitor"]["d1"]["returned"],1)
            before=overview(cur,start=day,end=day+timedelta(days=1))
            forget_actor(cur,"visitor",visitor)
            after=overview(cur,start=day,end=day+timedelta(days=1))
            self.assertEqual(after["counts"]["page_viewed"],before["counts"]["page_viewed"])
            self.assertEqual(after["actors"]["visitors"],0)

    def test_small_market_suppresses_related_human_facts_and_keeps_zero_explicit(self):
        now=datetime.now(ZONE)
        category=MarketCategory.objects.create(name="Review Science",slug="review-science")
        subcategory=MarketSubcategory.objects.create(category=category,name="Review Space",slug="review-space")
        market_row=Market.objects.create(category=category,subcategory=subcategory,
            slug="small-review-market",title="Small review market",kind="binary",status="open",
            status_label="Open",published_at=now-timedelta(days=1),close_at=now+timedelta(days=7))
        option=MarketOption.objects.create(market=market_row,label="YES",probability_exact=50)
        user=get_user_model().objects.create_user(username="smallreviewer",email="smallreviewer@example.test",password="local-test-password")
        Prediction.objects.create(user=user,market=market_row,market_option=option,
            action_type="initial",stake_amount=10,probability_at_entry=50,
            weight_at_entry=1000,potential_payout=20)
        with connection.cursor() as cur:
            cur.execute("""INSERT INTO gotrendlabs_analytics_market_publication
                (market_id,published_at,category_id,category_name,subcategory_id,subcategory_name,
                 kind,close_at,provenance) VALUES (%s,%s,%s,%s,%s,%s,'binary',%s,'observed_publication')""",
                (market_row.id,market_row.published_at,category.id,category.name,
                 subcategory.id,subcategory.name,market_row.close_at))
        start=now.date()
        end=start+timedelta(days=1)
        with get_connection() as db, db.cursor() as cur:
            listed=markets(cur,start=start,end=end)["items"][0]["participation"]
            self.assertTrue(listed["small_segment_suppressed"])
            self.assertIsNone(listed["human_participants"])
            self.assertIsNone(listed["first_entries"])
            self.assertIsNone(listed["human_volume_gtc"])
            detailed=market(cur,market_row.id,start=start,end=end)
            self.assertIsNone(detailed["stake"]["humans"]["stake_gtc"])
            grouped=editorial(cur,start=start,end=end)["items"][0]
            self.assertTrue(grouped["small_segment_suppressed"])
            self.assertIsNone(grouped["human_participants"])
            self.assertIsNone(grouped["first_entries"])
