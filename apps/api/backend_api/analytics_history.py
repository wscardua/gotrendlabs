"""Lossless daily observation history; the MCP adapter never touches these tables."""

from datetime import datetime, time, timedelta
import hashlib
import hmac
import os
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from apps.api.backend_api.db import get_connection


ZONE = ZoneInfo("America/Sao_Paulo")
ACTIVE = ("page_viewed", "screen_viewed")


def actor_secret():
    secret=os.environ.get("GOTRENDLABS_ANALYTICS_ACTOR_KEY")
    if secret:
        return secret
    if (os.environ.get("GOTRENDLABS_ENV", "").strip().lower() in ("prod", "production")
            or os.environ.get("DJANGO_DEBUG", "").strip().lower() in ("0", "false", "no", "off")):
        raise RuntimeError("analytics_actor_key_not_configured")
    return "gotrendlabs-local-analytics-actor-key"


def prepare_actor_key(cursor):
    cursor.execute("SELECT set_config('gotrendlabs.analytics_actor_key',%s,true)", (actor_secret(),))


def actor_key(kind, source_id):
    prefix="v:" if kind=="visitor" else "u:"
    return hmac.new(actor_secret().encode(),f"{prefix}{source_id}".encode(),hashlib.sha256).hexdigest()


def forget_actor(cursor, kind, source_id):
    """Remove identifying presence and raw observations; anonymous aggregates remain."""
    if kind not in ("visitor", "registered"):
        raise ValueError("invalid_actor_kind")
    cursor.execute("SELECT pg_advisory_xact_lock(7140027)")
    if kind=="registered":
        cursor.execute("""SELECT DISTINCT (e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date AS day
            FROM gotrendlabs_analytics_events e JOIN gotrendlabs_analytics_history_days h
              ON h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date
            WHERE e.user_id=%s AND NOT h.raw_pruned""", (source_id,))
        affected=[r["day"] for r in cursor.fetchall()]
        cursor.execute("DELETE FROM gotrendlabs_analytics_events WHERE user_id=%s", (source_id,))
    else:
        cursor.execute("""SELECT DISTINCT (e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date AS day
            FROM gotrendlabs_analytics_events e JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
            JOIN gotrendlabs_analytics_history_days h
              ON h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date
            WHERE s.visitor_id=%s AND NOT h.raw_pruned""", (source_id,))
        affected=[r["day"] for r in cursor.fetchall()]
        cursor.execute("""DELETE FROM gotrendlabs_analytics_events e USING gotrendlabs_analytics_sessions s
            WHERE e.session_id=s.id AND s.visitor_id=%s""", (source_id,))
    for day in affected:
        consolidate_day(cursor,day)
    cursor.execute("DELETE FROM gotrendlabs_analytics_history_actors WHERE actor_kind=%s AND actor_key=%s",
                   (kind,actor_key(kind,source_id)))


def bounds(day):
    """A business day is [local midnight, next local midnight), including DST."""
    return (datetime.combine(day, time.min, ZONE),
            datetime.combine(day + timedelta(days=1), time.min, ZONE))


def consolidate_day(cursor, day, *, today=None):
    today = today or datetime.now(ZONE).date()
    if day > today - timedelta(days=9):
        raise ValueError("day_not_mature")
    start, end = bounds(day)
    cursor.execute("SELECT pg_advisory_xact_lock(7140027)")
    prepare_actor_key(cursor)
    cursor.execute("SELECT raw_pruned FROM gotrendlabs_analytics_history_days WHERE day=%s FOR UPDATE", (day,))
    prior = cursor.fetchone()
    if prior and prior["raw_pruned"]:
        raise ValueError("raw_events_already_pruned")
    cursor.execute("""
        INSERT INTO gotrendlabs_analytics_history_days(day,source_events)
        VALUES (%s,0) ON CONFLICT(day) DO NOTHING
    """, (day,))
    cursor.execute("DELETE FROM gotrendlabs_analytics_history_counts WHERE day=%s", (day,))
    cursor.execute("DELETE FROM gotrendlabs_analytics_history_actors WHERE day=%s", (day,))
    cursor.execute("DELETE FROM gotrendlabs_analytics_history_funnel WHERE day=%s", (day,))
    # market_id=0 is the platform total. Event market attribution uses the
    # observed slug, never the current featured flag or a fabricated view.
    cursor.execute("""
        WITH source AS (
            SELECT e.*
            FROM gotrendlabs_analytics_events e
            WHERE e.occurred_at >= %s AND e.occurred_at < %s
        ), dimensions AS (
            SELECT 0::bigint AS market_id, platform,actor_type,name FROM source
            UNION ALL
            SELECT market_id,platform,actor_type,name FROM source WHERE market_id IS NOT NULL
        )
        INSERT INTO gotrendlabs_analytics_history_counts
            (day,market_id,platform,actor_type,event_name,events)
        SELECT %s,market_id,platform,actor_type,name,count(*)
        FROM dimensions GROUP BY 1,2,3,4,5
    """, (start, end, day))
    cursor.execute("""
        WITH starts AS (
            SELECT e.session_id,e.properties->>'market_slug' AS slug,
                   min(e.occurred_at) AS started_at,max(s.last_seen_at) AS last_seen_at,
                   min(e.market_id) AS market_id
            FROM gotrendlabs_analytics_events e
            JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
            WHERE e.name='prediction_started' AND e.actor_type IN ('visitor','user')
              AND e.occurred_at >= %s AND e.occurred_at < %s
              AND nullif(e.properties->>'market_slug','') IS NOT NULL
            GROUP BY e.session_id,e.properties->>'market_slug'
        ), progress AS (
            SELECT st.session_id,st.slug,st.started_at,st.last_seen_at,st.market_id,
                   choice.chosen_at,preview.preview_at,submitted.submit_at
            FROM starts st
            LEFT JOIN LATERAL (
                SELECT min(e.occurred_at) AS chosen_at FROM gotrendlabs_analytics_events e
                WHERE e.session_id=st.session_id AND e.properties->>'market_slug'=st.slug
                  AND e.name='prediction_option_selected' AND e.occurred_at>=st.started_at
            ) choice ON true
            LEFT JOIN LATERAL (
                SELECT min(e.occurred_at) AS preview_at FROM gotrendlabs_analytics_events e
                WHERE e.session_id=st.session_id AND e.properties->>'market_slug'=st.slug
                  AND e.name='prediction_preview_viewed' AND e.occurred_at>=choice.chosen_at
            ) preview ON true
            LEFT JOIN LATERAL (
                SELECT min(e.occurred_at) AS submit_at FROM gotrendlabs_analytics_events e
                WHERE e.session_id=st.session_id AND e.properties->>'market_slug'=st.slug
                  AND e.name='prediction_submit_clicked'
                  AND e.occurred_at>=coalesce(preview.preview_at,choice.chosen_at)
            ) submitted ON true
        ), dimensions AS (
            SELECT 0::bigint AS market_id,chosen_at,preview_at,submit_at,last_seen_at FROM progress
            UNION ALL
            SELECT market_id,chosen_at,preview_at,submit_at,last_seen_at FROM progress
            WHERE market_id IS NOT NULL
        )
        INSERT INTO gotrendlabs_analytics_history_funnel
            (day,market_id,started,chosen,previewed,submit_clicked,eligible,
             abandoned_before_choice,abandoned_after_choice)
        SELECT %s,market_id,count(*),count(*) FILTER (WHERE chosen_at IS NOT NULL),
               count(*) FILTER (WHERE preview_at IS NOT NULL),
               count(*) FILTER (WHERE submit_at IS NOT NULL),
               count(*) FILTER (WHERE last_seen_at < now()-interval '30 minutes'),
               count(*) FILTER (WHERE last_seen_at < now()-interval '30 minutes'
                                      AND chosen_at IS NULL AND submit_at IS NULL),
               count(*) FILTER (WHERE last_seen_at < now()-interval '30 minutes'
                                      AND chosen_at IS NOT NULL AND submit_at IS NULL)
        FROM dimensions GROUP BY 1,2
    """, (start, end, day))
    cursor.execute("""
        WITH source AS (
            SELECT e.session_id,e.user_id,e.actor_type,e.platform,e.name,
                   s.visitor_id,e.market_id,
                   (u.date_joined AT TIME ZONE 'America/Sao_Paulo')::date AS user_cohort,
                   (v.first_seen_at AT TIME ZONE 'America/Sao_Paulo')::date AS visitor_cohort,
                   v.first_session_id AS first_session
            FROM gotrendlabs_analytics_events e
            JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
            JOIN gotrendlabs_analytics_visitors v ON v.id=s.visitor_id
            LEFT JOIN gotrendlabs_users u ON u.id=e.user_id
            WHERE e.occurred_at >= %s AND e.occurred_at < %s
              AND e.actor_type IN ('visitor','user')
        ), dimensions AS (
            SELECT 0::bigint AS market_id,session_id,user_id,actor_type,platform,name,
                   visitor_id,user_cohort,visitor_cohort,first_session FROM source
            UNION ALL
            SELECT market_id,session_id,user_id,actor_type,platform,name,
                   visitor_id,user_cohort,visitor_cohort,first_session FROM source
            WHERE market_id IS NOT NULL
        )
        INSERT INTO gotrendlabs_analytics_history_actors
            (day,actor_kind,actor_key,market_id,platform,cohort_day,active_view,different_session)
        SELECT %s,
               CASE WHEN actor_type='visitor' THEN 'visitor' ELSE 'registered' END,
               encode(hmac((CASE WHEN actor_type='visitor' THEN 'v:'||visitor_id::text
                                 ELSE 'u:'||user_id::text END)::bytea,
                           current_setting('gotrendlabs.analytics_actor_key')::bytea,'sha256'),'hex'),
               market_id,platform,
               CASE WHEN actor_type='visitor' THEN visitor_cohort ELSE user_cohort END,
               bool_or(name IN ('page_viewed','screen_viewed')),
               bool_or(session_id <> first_session)
        FROM dimensions GROUP BY 1,2,3,4,5,6
    """, (start, end, day))
    cursor.execute("""
        UPDATE gotrendlabs_analytics_history_days
        SET source_events=(SELECT count(*) FROM gotrendlabs_analytics_events
                           WHERE occurred_at >= %s AND occurred_at < %s),
            source_max_received_at=(SELECT max(received_at) FROM gotrendlabs_analytics_events
                                    WHERE occurred_at >= %s AND occurred_at < %s),
            consolidated_at=now() WHERE day=%s
    """, (start, end, start, end, day))
    cursor.execute("""
        SELECT h.source_events,
               coalesce((SELECT sum(c.events) FROM gotrendlabs_analytics_history_counts c
                         WHERE c.day=h.day AND c.market_id=0),0) AS preserved_events
        FROM gotrendlabs_analytics_history_days h WHERE h.day=%s
    """, (day,))
    checked=cursor.fetchone()
    if checked["source_events"] != checked["preserved_events"]:
        raise ValueError("history_count_verification_failed")
    return checked["source_events"]


def consolidate_pending(*, limit_days=30, through=None):
    """One committed day per transaction is a resumable checkpoint."""
    through = min(through or datetime.now(ZONE).date() - timedelta(days=9),
                  datetime.now(ZONE).date() - timedelta(days=9))
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT h.day
                FROM gotrendlabs_analytics_history_days h
                LEFT JOIN LATERAL (
                    SELECT count(*) AS events,max(e.received_at) AS last_received
                    FROM gotrendlabs_analytics_events e
                    WHERE e.occurred_at >= (h.day::timestamp AT TIME ZONE 'America/Sao_Paulo')
                      AND e.occurred_at < ((h.day+1)::timestamp AT TIME ZONE 'America/Sao_Paulo')
                ) raw ON true
                WHERE h.raw_pruned=false AND h.day<=%s
                  AND (h.source_events IS DISTINCT FROM raw.events
                       OR h.source_max_received_at IS DISTINCT FROM raw.last_received)
                ORDER BY h.day LIMIT %s
            """, (through, limit_days+1))
            stale = [row["day"] for row in cursor.fetchall()]
            cursor.execute("""
                SELECT min((occurred_at AT TIME ZONE 'America/Sao_Paulo')::date) AS day
                FROM gotrendlabs_analytics_events
            """)
            first = cursor.fetchone()["day"]
            cursor.execute("SELECT max(day) AS day FROM gotrendlabs_analytics_history_days")
            last = cursor.fetchone()["day"]
    if first is None:
        return {"days": 0, "events": 0, "remaining": 0}
    day = max(first, last + timedelta(days=1)) if last else first
    done = events = 0
    for stale_day in stale[:limit_days]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                events += consolidate_day(cursor, stale_day)
        done += 1
    while day <= through and done < limit_days:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                events += consolidate_day(cursor, day)
        done += 1
        day += timedelta(days=1)
    return {"days": done, "events": events,
            "remaining": max(0, (through - day).days + 1) + max(0, len(stale)-done)}


def reject_unsupported(*, platform="all", market_id=None):
    if platform not in ("all", "web", "mobile") or (market_id is not None and market_id <= 0):
        raise HTTPException(422, detail={"code": "validation_failed"})
