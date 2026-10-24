"""Bounded, read-only analytics projections shared by HTTP and MCP."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from apps.api.backend_api.analytics_history import bounds, prepare_actor_key


ZONE = ZoneInfo("America/Sao_Paulo")
EVENTS = (
    "page_viewed", "screen_viewed", "market_card_viewed", "market_card_clicked",
    "market_detail_viewed", "prediction_started", "prediction_option_selected",
    "prediction_preview_viewed", "prediction_submit_clicked", "share_started",
)
GRAINS = {"day": "day", "week": "week", "month": "month", "year": "year"}
DEFINITIONS = {
    "observed_visitors": "Distinct anonymous browser or installation IDs with an observed event; not people.",
    "active_accounts": "Distinct non-staff, non-bot accounts with page_viewed or screen_viewed.",
    "new_signups": "Human non-staff accounts by date_joined.",
    "human_participants": "Distinct human non-staff accounts with any persisted prediction action in the interval.",
    "bot_participants": "Distinct bot accounts with any persisted prediction action in the interval.",
    "event_counts": "Accepted observed client events; each event_id contributes once.",
    "card_ctr": "market_card_clicked / market_card_viewed; null when impressions are zero.",
    "prediction_funnel": "Observed steps are event counts, not attributed attempts; initial prediction is a persisted domain fact.",
    "volume_gtc": "Initial and reinforcement stake_amount only; revision reuses existing stake and is not new volume.",
    "retention": "Exact calendar D1/D7/D30 activity; visitors require a different anonymous session.",
}


def _fail(code="validation_failed", status=422):
    raise HTTPException(status, detail={"code": code})


def _revision(cursor, supplied, *, continuation=False):
    cursor.execute("""
        SELECT md5(concat_ws('|',
            (SELECT max(consolidated_at)::text FROM gotrendlabs_analytics_history_days),
            (SELECT max(received_at)::text FROM gotrendlabs_analytics_events),
            (SELECT max(updated_at)::text FROM gotrendlabs_predictions),
            (SELECT max(updated_at)::text FROM gotrendlabs_markets),
            (SELECT max(captured_at)::text FROM gotrendlabs_analytics_market_publication),
            (SELECT max(date_joined)::text FROM gotrendlabs_users))) AS revision
    """)
    current=cursor.fetchone()["revision"]
    if continuation and not supplied:
        _fail("revision_required",409)
    if supplied and supplied != current:
        _fail("snapshot_changed",409)
    return current


def _coverage(cursor):
    cursor.execute("""
        SELECT (SELECT min(day) FROM gotrendlabs_analytics_history_days) AS history_first,
               (SELECT max(day) FROM gotrendlabs_analytics_history_days) AS history_last,
               (SELECT min((occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
                FROM gotrendlabs_analytics_events) AS raw_first,
               (SELECT max((occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
                FROM gotrendlabs_analytics_events) AS raw_last,
               (SELECT max(consolidated_at) FROM gotrendlabs_analytics_history_days) AS consolidated_at,
               (SELECT min((published_at AT TIME ZONE 'America/Sao_Paulo')::date)
                FROM gotrendlabs_markets WHERE published_at IS NOT NULL) AS published_first,
               (SELECT min((date_joined AT TIME ZONE 'America/Sao_Paulo')::date)
                FROM gotrendlabs_users WHERE is_bot=false AND is_staff=false AND is_superuser=false) AS signup_first,
               (SELECT min((created_at AT TIME ZONE 'America/Sao_Paulo')::date)
                FROM gotrendlabs_predictions) AS prediction_first
    """)
    row = cursor.fetchone()
    observed = min((x for x in (row["history_first"], row["raw_first"]) if x), default=None)
    latest = max((x for x in (row["raw_last"], row["history_last"]) if x), default=None)
    return {"observed_first": observed, "observed_last": latest,
            "consolidated_through": row["history_last"], "consolidated_at": row["consolidated_at"],
            "published_first": row["published_first"], "signup_first": row["signup_first"],
            "prediction_first": row["prediction_first"]}


def coverage(cursor):
    c = _coverage(cursor)
    return {"contract_version": "analytics-mcp.v1", "generated_at": datetime.now(ZONE),
            "timezone": str(ZONE), "coverage": {**c, "events": _event_coverage(cursor)},
            "definitions": DEFINITIONS,
            "limits": {"page_size_max": 100, "period_end": "exclusive", "period_start": "inclusive",
                       "calendar": "America/Sao_Paulo; week starts Monday",
                       "partial_day": "current day is partial",
                       "privacy": "No actor, visitor, session, or event identifiers are returned."}}


def _event_coverage(cursor):
    """First/last actual observations, never a fabricated instrumentation date."""
    cursor.execute("""
        SELECT event_name,min(day) AS first_day,max(day) AS last_day FROM (
            SELECT event_name,day FROM gotrendlabs_analytics_history_counts
            WHERE market_id=0 AND actor_type IN ('visitor','user')
            UNION ALL
            SELECT name AS event_name,(occurred_at AT TIME ZONE 'America/Sao_Paulo')::date AS day
            FROM gotrendlabs_analytics_events WHERE actor_type IN ('visitor','user')
        ) observations GROUP BY event_name
    """)
    found={r["event_name"]:r for r in cursor.fetchall()}
    return {name:{"first_observed_day":found[name]["first_day"] if name in found else None,
                  "last_observed_day":found[name]["last_day"] if name in found else None,
                  "availability":"observed" if name in found else "no_observations"}
            for name in EVENTS}


def _visible_events(counts, coverage, start, end, observed_last):
    return {name:(counts[name] if metadata["first_observed_day"] is not None
                  and end>metadata["first_observed_day"]
                  and observed_last is not None and start<=observed_last else None)
            for name,metadata in coverage.items()}


def _block_filters(platform):
    return {"observed_events_and_actors":{"platform":platform},
            "signups_participation_funnel_stake_social_quality":{"platform":"all"},
            "note":"A plataforma dos fatos de domínio e do funil não é atribuível; esses blocos são globais."}


def _suppress_market_humans(participation):
    """Keep zero explicit while withholding exact facts about 1–4 people."""
    sample=participation["human_participants"]
    participation["small_segment_suppressed"]=0<sample<5
    if participation["small_segment_suppressed"]:
        for key in ("human_participants","first_entries","reinforcements","revisions",
                    "human_volume_gtc","first_platform_participants"):
            if key in participation:
                participation[key]=None
    return participation


def period(cursor, *, start=None, end=None, all_history=False):
    c = _coverage(cursor)
    today = datetime.now(ZONE).date()
    if all_history and (start is not None or end is not None):
        _fail()
    if (start is None) != (end is None):
        _fail()
    if all_history:
        first = min((d for d in (c["observed_first"], c["published_first"], c["signup_first"], c["prediction_first"]) if d), default=today)
        start, end = first, today + timedelta(days=1)
    elif start is None:
        end = today + timedelta(days=1)
        start = end - timedelta(days=7)
    if start >= end or end > today + timedelta(days=1):
        _fail()
    return start, end, c


def _observed_counts(cursor, start, end, *, market_id=0, platform="all"):
    if platform not in ("all", "web", "mobile"):
        _fail()
    start_at, _ = bounds(start)
    end_at, _ = bounds(end)
    cursor.execute("""
        WITH preserved AS (
            SELECT event_name, sum(events)::bigint AS n
            FROM gotrendlabs_analytics_history_counts
            WHERE day >= %s AND day < %s AND market_id=%s
              AND actor_type IN ('visitor','user') AND (%s='all' OR platform=%s)
            GROUP BY event_name
        ), live AS (
            SELECT e.name AS event_name,count(*)::bigint AS n
            FROM gotrendlabs_analytics_events e
            WHERE e.occurred_at >= %s AND e.occurred_at < %s
              AND NOT EXISTS (SELECT 1 FROM gotrendlabs_analytics_history_days h
                              WHERE h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
              AND (%s=0 OR e.market_id=%s) AND e.actor_type IN ('visitor','user')
              AND (%s='all' OR e.platform=%s)
            GROUP BY e.name
        )
        SELECT event_name,sum(n)::bigint AS n FROM (
            SELECT * FROM preserved UNION ALL SELECT * FROM live
        ) combined GROUP BY event_name
    """, (start,end,market_id,platform,platform,start_at,end_at,market_id,market_id,platform,platform))
    found = {row["event_name"]: row["n"] for row in cursor.fetchall()}
    return {name: found.get(name, 0) for name in EVENTS}


def _actors(cursor, start, end, *, market_id=0, platform="all"):
    start_at, _ = bounds(start)
    end_at, _ = bounds(end)
    prepare_actor_key(cursor)
    cursor.execute("""
        WITH actors AS (
            SELECT actor_kind,actor_key,active_view
            FROM gotrendlabs_analytics_history_actors
            WHERE day >= %s AND day < %s AND market_id=%s
              AND (%s='all' OR platform=%s)
            UNION ALL
            SELECT CASE WHEN e.actor_type='visitor' THEN 'visitor' ELSE 'registered' END,
                   encode(hmac((CASE WHEN e.actor_type='visitor' THEN 'v:'||s.visitor_id::text
                                     ELSE 'u:'||e.user_id::text END)::bytea,
                               current_setting('gotrendlabs.analytics_actor_key')::bytea,'sha256'),'hex'),
                   e.name IN ('page_viewed','screen_viewed')
            FROM gotrendlabs_analytics_events e
            JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
            WHERE e.occurred_at >= %s AND e.occurred_at < %s
              AND NOT EXISTS (SELECT 1 FROM gotrendlabs_analytics_history_days h
                              WHERE h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
              AND (%s=0 OR e.market_id=%s) AND (%s='all' OR e.platform=%s)
              AND e.actor_type IN ('visitor','user')
        )
        SELECT count(DISTINCT actor_key) FILTER (WHERE actor_kind='visitor') AS visitors,
               count(DISTINCT actor_key) FILTER (WHERE actor_kind='registered' AND active_view) AS active_accounts
        FROM actors
    """, (start,end,market_id,platform,platform,start_at,end_at,market_id,market_id,platform,platform))
    return dict(cursor.fetchone())


def _domain(cursor, start, end, *, market_id=0):
    start_at, _ = bounds(start)
    end_at, _ = bounds(end)
    cursor.execute("""
        SELECT count(*) FILTER (WHERE action_type='initial' AND NOT is_bot) AS first_entries,
               count(*) FILTER (WHERE action_type='reinforcement' AND NOT is_bot) AS reinforcements,
               count(*) FILTER (WHERE action_type='revision' AND NOT is_bot) AS revisions,
               count(DISTINCT user_id) FILTER (WHERE NOT is_bot) AS human_participants,
               count(DISTINCT user_id) FILTER (WHERE is_bot) AS bot_participants,
               coalesce(sum(stake_amount) FILTER (WHERE action_type IN ('initial','reinforcement') AND NOT is_bot),0) AS human_volume_gtc,
               coalesce(sum(stake_amount) FILTER (WHERE action_type IN ('initial','reinforcement') AND is_bot),0) AS bot_volume_gtc
        FROM (SELECT p.*,u.is_bot FROM gotrendlabs_predictions p
              JOIN gotrendlabs_users u ON u.id=p.user_id
              WHERE p.created_at >= %s AND p.created_at < %s
                AND (%s=0 OR p.market_id=%s)
                AND NOT u.is_staff AND NOT u.is_superuser) p
    """, (start_at,end_at,market_id,market_id))
    result=dict(cursor.fetchone())
    cursor.execute("""
        SELECT count(DISTINCT p.user_id) AS first_platform_participants
        FROM gotrendlabs_predictions p JOIN gotrendlabs_users u ON u.id=p.user_id
        WHERE p.action_type='initial' AND p.created_at >= %s AND p.created_at < %s
          AND (%s=0 OR p.market_id=%s)
          AND NOT u.is_bot AND NOT u.is_staff AND NOT u.is_superuser
          AND NOT EXISTS (
            SELECT 1 FROM gotrendlabs_predictions earlier
            WHERE earlier.user_id=p.user_id AND earlier.action_type='initial'
              AND (earlier.created_at,earlier.id)<(p.created_at,p.id))
    """,(start_at,end_at,market_id,market_id))
    result.update(cursor.fetchone())
    return result


def _stake(cursor, end, *, market_id=0):
    reference=min(bounds(end)[0],datetime.now(ZONE))
    cursor.execute("""
        WITH per_actor AS (
            SELECT p.user_id,u.is_bot,sum(p.stake_amount)::bigint AS stake
            FROM gotrendlabs_predictions p
            JOIN gotrendlabs_users u ON u.id=p.user_id
            JOIN gotrendlabs_markets m ON m.id=p.market_id
            WHERE p.created_at < %s
              AND (p.superseded_at IS NULL OR p.superseded_at >= %s)
              AND (m.resolved_at IS NULL OR m.resolved_at >= %s)
              AND (m.canceled_at IS NULL OR m.canceled_at >= %s)
              AND (%s=0 OR p.market_id=%s)
              AND NOT u.is_staff AND NOT u.is_superuser
            GROUP BY p.user_id,u.is_bot
        ), ranked AS (
            SELECT *,row_number() OVER(PARTITION BY is_bot ORDER BY stake DESC,user_id) AS rank
            FROM per_actor
        )
        SELECT is_bot,count(*) AS participants,sum(stake)::bigint AS stake_gtc,
               coalesce(sum(stake) FILTER (WHERE rank<=10),0)::bigint AS top_ten_stake_gtc
        FROM ranked GROUP BY is_bot
    """,(reference,reference,reference,reference,market_id,market_id))
    by_actor={r["is_bot"]:r for r in cursor.fetchall()}
    output={}
    for label,flag in (("humans",False),("bots",True)):
        row=by_actor.get(flag)
        sample=row["participants"] if row else 0
        total=row["stake_gtc"] if row else 0
        output[label]={"participants":sample,"stake_gtc":total,
                       "top_ten_share":round(row["top_ten_stake_gtc"]/total,4)
                       if row and total and sample>=10 else None,
                       "concentration_suppressed":sample<10}
    return {"as_of":reference,"unit":"GT₵ educational credits","precision":"limited_reconstruction",**output,
            "definition":"Sum of unsuperseded prediction rows before the reference, excluding markets resolved or canceled by then."}


def _social(cursor,start,end,*,market_id=0):
    start_at,_=bounds(start)
    end_at,_=bounds(end)
    cursor.execute("""
        SELECT
          (SELECT count(*) FROM gotrendlabs_market_likes l JOIN gotrendlabs_users u ON u.id=l.user_id
           WHERE l.created_at >= %s AND l.created_at < %s AND (%s=0 OR l.market_id=%s)
             AND NOT u.is_bot AND NOT u.is_staff AND NOT u.is_superuser) AS likes,
          (SELECT count(*) FROM gotrendlabs_market_favorites f JOIN gotrendlabs_users u ON u.id=f.user_id
           WHERE f.created_at >= %s AND f.created_at < %s AND (%s=0 OR f.market_id=%s)
             AND NOT u.is_bot AND NOT u.is_staff AND NOT u.is_superuser) AS favorites,
          (SELECT count(*) FROM gotrendlabs_market_comments c JOIN gotrendlabs_users u ON u.id=c.author_id
           WHERE c.created_at >= %s AND c.created_at < %s AND (%s=0 OR c.market_id=%s)
             AND c.status='visible' AND NOT u.is_bot AND NOT u.is_staff AND NOT u.is_superuser) AS visible_comments
    """,(start_at,end_at,market_id,market_id,start_at,end_at,market_id,market_id,
         start_at,end_at,market_id,market_id))
    return {**dict(cursor.fetchone()),"basis":"current surviving state; removals and moderation history unavailable",
            "share_actions":"share_started events in observed counts; external sharing is unverified"}


def _quality(cursor,start,end):
    start_at,_=bounds(start)
    end_at,_=bounds(end)
    cursor.execute("""
        SELECT count(*) FILTER (WHERE canceled_at >= %s AND canceled_at < %s) AS cancellations,
               count(*) FILTER (WHERE (canceled_at >= %s AND canceled_at < %s)
                                  OR (resolved_at >= %s AND resolved_at < %s)) AS terminal_markets,
               avg(extract(epoch FROM resolved_at-close_at)/3600)
                   FILTER (WHERE resolved_at >= %s AND resolved_at < %s AND close_at IS NOT NULL) AS close_to_resolution_hours
        FROM gotrendlabs_markets WHERE published_at IS NOT NULL
    """,(start_at,end_at,start_at,end_at,start_at,end_at,start_at,end_at))
    row=dict(cursor.fetchone())
    denominator=row["terminal_markets"]
    cursor.execute("""SELECT count(*) AS delayed FROM gotrendlabs_markets
        WHERE status='locked' AND expected_resolution_at IS NOT NULL
          AND expected_resolution_at < now() AND published_at IS NOT NULL""")
    return {**row,"cancellation_rate":round(row["cancellations"]/denominator,4) if denominator else None,
            "delayed_in_resolution_current":cursor.fetchone()["delayed"],
            "delay_basis":"current locked state past expected_resolution_at; no historical status inferred"}


def _funnel(cursor,start,end,*,market_id=0):
    start_at,_=bounds(start)
    end_at,_=bounds(end)
    cursor.execute("""
        WITH preserved AS (
            SELECT coalesce(sum(started),0) AS started,coalesce(sum(chosen),0) AS chosen,
                   coalesce(sum(previewed),0) AS previewed,
                   coalesce(sum(submit_clicked),0) AS submit_clicked,
                   coalesce(sum(eligible),0) AS eligible,
                   coalesce(sum(abandoned_before_choice),0) AS abandoned_before_choice,
                   coalesce(sum(abandoned_after_choice),0) AS abandoned_after_choice
            FROM gotrendlabs_analytics_history_funnel
            WHERE day >= %s AND day < %s AND market_id=%s
        ), starts AS (
            SELECT e.session_id,e.properties->>'market_slug' AS slug,
                   min(e.occurred_at) AS started_at,max(s.last_seen_at) AS last_seen_at
            FROM gotrendlabs_analytics_events e
            JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
            WHERE e.name='prediction_started' AND e.actor_type IN ('visitor','user')
              AND e.occurred_at >= %s AND e.occurred_at < %s
              AND NOT EXISTS (SELECT 1 FROM gotrendlabs_analytics_history_days h
                  WHERE h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
              AND (%s=0 OR e.market_id=%s)
              AND nullif(e.properties->>'market_slug','') IS NOT NULL
            GROUP BY e.session_id,e.properties->>'market_slug'
        ), progress AS (
            SELECT st.session_id,st.slug,st.last_seen_at,
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
        ), live AS (
            SELECT count(*) AS started,count(*) FILTER (WHERE chosen_at IS NOT NULL) AS chosen,
                   count(*) FILTER (WHERE preview_at IS NOT NULL) AS previewed,
                   count(*) FILTER (WHERE submit_at IS NOT NULL) AS submit_clicked,
                   count(*) FILTER (WHERE last_seen_at < now()-interval '30 minutes') AS eligible,
                   count(*) FILTER (WHERE last_seen_at < now()-interval '30 minutes'
                     AND chosen_at IS NULL AND submit_at IS NULL) AS abandoned_before_choice,
                   count(*) FILTER (WHERE last_seen_at < now()-interval '30 minutes'
                     AND chosen_at IS NOT NULL AND submit_at IS NULL) AS abandoned_after_choice
            FROM progress
        )
        SELECT p.started+l.started AS started,p.chosen+l.chosen AS chosen,
               p.previewed+l.previewed AS previewed,
               p.submit_clicked+l.submit_clicked AS submit_clicked,
               p.eligible+l.eligible AS eligible,
               p.abandoned_before_choice+l.abandoned_before_choice AS abandoned_before_choice,
               p.abandoned_after_choice+l.abandoned_after_choice AS abandoned_after_choice
        FROM preserved p CROSS JOIN live l
    """,(start,end,market_id,start_at,end_at,market_id,market_id))
    return dict(cursor.fetchone())


def overview(cursor, *, start=None, end=None, all_history=False, platform="all"):
    start,end,c = period(cursor,start=start,end=end,all_history=all_history)
    if platform not in ("all","web","mobile"):
        _fail()
    counts = _observed_counts(cursor,start,end,platform=platform)
    actors = _actors(cursor,start,end,platform=platform)
    domain = _domain(cursor,start,end)
    funnel = _funnel(cursor,start,end)
    stake = _stake(cursor,end)
    social = _social(cursor,start,end)
    quality = _quality(cursor,start,end)
    start_at,_ = bounds(start)
    end_at,_ = bounds(end)
    cursor.execute("""SELECT count(*) AS new_signups FROM gotrendlabs_users
        WHERE date_joined >= %s AND date_joined < %s AND is_bot=false
          AND is_staff=false AND is_superuser=false""", (start_at,end_at))
    signups = cursor.fetchone()["new_signups"]
    first = c["observed_first"]
    observed_start = max(start,first) if first else None
    observed_end = min(end,c["observed_last"]+timedelta(days=1)) if c["observed_last"] else None
    observed_available=first is not None and end>first and start<=c["observed_last"]
    metric_coverage=_event_coverage(cursor)
    visible_counts=_visible_events(counts,metric_coverage,start,end,c["observed_last"])
    visible_actors=actors if observed_available else {"visitors":None,"active_accounts":None}
    visible_funnel=funnel if visible_counts["prediction_started"] is not None else {name:None for name in funnel}
    if visible_funnel["previewed"] is not None and visible_counts["prediction_preview_viewed"] is None:
        visible_funnel["previewed"]=None
    return {"contract_version":"analytics-mcp.v1", "generated_at":datetime.now(ZONE),
            "timezone":str(ZONE),"requested":{"start":start,"end_exclusive":end,"all_history":all_history},
            "observed_coverage":{"start":observed_start,"end_exclusive":observed_end,
                                 "before_instrumentation":bool(first and start<first),
                                 "available":observed_available},
            "partial_period":end>datetime.now(ZONE).date(),
            "filters":_block_filters(platform),"metric_coverage":metric_coverage,
            "consolidated_at":c["consolidated_at"],"counts":visible_counts,
            "card_ctr":{"numerator":visible_counts["market_card_clicked"],
                        "denominator":visible_counts["market_card_viewed"],
                        "value":round(counts["market_card_clicked"]/counts["market_card_viewed"],4)
                        if visible_counts["market_card_clicked"] is not None
                        and visible_counts["market_card_viewed"] is not None
                        and counts["market_card_viewed"] else None},
            "actors":visible_actors,"new_signups":signups,"participation":domain,"funnel":visible_funnel,
            "stake":stake,"social":social,"quality":quality,
            "precision":"mixed: exact observed/domain counts; limited historical stake reconstruction and current-state social/quality",
            "availability":"available" if observed_available else "not_instrumented"}


def retention(cursor, *, start=None, end=None, all_history=False):
    start,end,c = period(cursor,start=start,end=end,all_history=all_history)
    prepare_actor_key(cursor)
    today = datetime.now(ZONE).date()
    # Cohort members and return activity are retained per actor/day. Do not sum
    # daily distinct counts or use today's account state as historical activity.
    result = {}
    for kind in ("registered","visitor"):
        cohort_start=max(start,c["observed_first"]+timedelta(days=1)) if c["observed_first"] else end
        if kind=="registered":
            cohort_sql="""SELECT encode(hmac(('u:'||id::text)::bytea,
                current_setting('gotrendlabs.analytics_actor_key')::bytea,'sha256'),'hex') AS actor_key,
                (date_joined AT TIME ZONE 'America/Sao_Paulo')::date AS cohort_day
                FROM gotrendlabs_users WHERE date_joined >= %s AND date_joined < %s
                  AND is_bot=false AND is_staff=false AND is_superuser=false"""
            cohort_args=(bounds(cohort_start)[0],bounds(end)[0])
        else:
            cohort_sql="""SELECT actor_key,cohort_day FROM presence
                WHERE day=cohort_day AND active_view AND cohort_day >= %s AND cohort_day < %s
                GROUP BY actor_key,cohort_day"""
            cohort_args=(cohort_start,end)
        cursor.execute("""
            WITH presence AS (
                SELECT actor_key,cohort_day,day,active_view,different_session
                FROM gotrendlabs_analytics_history_actors
                WHERE actor_kind=%s AND market_id=0 AND day >= %s AND day < %s
                UNION ALL
                SELECT encode(hmac((CASE WHEN e.actor_type='visitor' THEN 'v:'||s.visitor_id::text
                                          ELSE 'u:'||e.user_id::text END)::bytea,
                                    current_setting('gotrendlabs.analytics_actor_key')::bytea,'sha256'),'hex'),
                       CASE WHEN e.actor_type='visitor' THEN (v.first_seen_at AT TIME ZONE 'America/Sao_Paulo')::date
                            ELSE (u.date_joined AT TIME ZONE 'America/Sao_Paulo')::date END,
                       (e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date,
                       e.name IN ('page_viewed','screen_viewed'),
                       e.session_id <> v.first_session_id
                FROM gotrendlabs_analytics_events e
                JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
                JOIN gotrendlabs_analytics_visitors v ON v.id=s.visitor_id
                LEFT JOIN gotrendlabs_users u ON u.id=e.user_id
                WHERE e.occurred_at >= %s AND e.occurred_at < %s
                  AND NOT EXISTS (SELECT 1 FROM gotrendlabs_analytics_history_days h
                                  WHERE h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
                  AND ((%s='visitor' AND e.actor_type='visitor') OR
                       (%s='registered' AND e.actor_type='user' AND u.is_bot=false
                        AND u.is_staff=false AND u.is_superuser=false))
            ), cohorts AS (
        """+cohort_sql+"""
            )
            SELECT n,
                   count(*) AS cohort_size,
                   count(*) FILTER (WHERE cohort_day+n >= %s) AS immature,
                   count(*) FILTER (WHERE cohort_day+n < %s) AS eligible,
                   count(*) FILTER (WHERE cohort_day+n < %s AND EXISTS (
                       SELECT 1 FROM presence p WHERE p.actor_key=c.actor_key
                         AND p.day=c.cohort_day+n AND p.active_view
                         AND (%s='registered' OR p.different_session))) AS returned
            FROM cohorts c CROSS JOIN (VALUES (1),(7),(30)) milestones(n)
            GROUP BY n ORDER BY n
        """, (kind,start,end+timedelta(days=30),bounds(start)[0],
              bounds(end+timedelta(days=30))[0],kind,kind,*cohort_args,today,today,today,kind))
        result[kind] = {f"d{r['n']}":{"cohort_size":r["cohort_size"],"immature":r["immature"],
                                       "eligible":r["eligible"],"returned":r["returned"],
                                       "rate":round(r["returned"]/r["eligible"],4) if r["eligible"] else None}
                        for r in cursor.fetchall()}
    return {"contract_version":"analytics-mcp.v1","generated_at":datetime.now(ZONE),
            "requested":{"start":start,"end_exclusive":end},"timezone":str(ZONE),
            "observed_first":c["observed_first"],"cohorts":result,
            "precision":"exact","partial_period":end>today,
            "availability":"available" if c["observed_first"] else "not_instrumented"}


def markets(cursor, *, start=None, end=None, all_history=False, after=0, limit=25,
            revision=None):
    start,end,c = period(cursor,start=start,end=end,all_history=all_history)
    if not 1 <= limit <= 50 or after < 0:
        _fail()
    revision=_revision(cursor,revision,continuation=after>0)
    cursor.execute("""
        SELECT p.market_id AS id,m.slug,m.status,p.kind,p.published_at,p.close_at,
               m.expected_resolution_at,m.resolved_at,m.canceled_at,
               p.category_id,p.subcategory_id,p.event_id,
               p.category_name AS category,p.subcategory_name AS subcategory,
               p.event_name AS event,p.provenance AS taxonomy_basis
        FROM gotrendlabs_analytics_market_publication p
        LEFT JOIN gotrendlabs_markets m ON m.id=p.market_id
        WHERE p.market_id>%s AND p.published_at < %s
          AND (p.close_at IS NULL OR p.close_at >= %s)
        ORDER BY p.market_id LIMIT %s
    """, (after,bounds(end)[0],bounds(start)[0],limit+1))
    rows = cursor.fetchall()
    has_more = len(rows)>limit
    rows = rows[:limit]
    ids = [r["id"] for r in rows]
    if not ids:
        stats = {}
    else:
        start_at,_ = bounds(start)
        end_at,_ = bounds(end)
        cursor.execute("""
            WITH observed AS (
                SELECT market_id,event_name,sum(events)::bigint AS n
                FROM gotrendlabs_analytics_history_counts
                WHERE day >= %s AND day < %s AND market_id=ANY(%s)
                  AND actor_type IN ('visitor','user')
                GROUP BY market_id,event_name
                UNION ALL
                SELECT e.market_id,e.name,count(*)::bigint
                FROM gotrendlabs_analytics_events e
                WHERE e.market_id=ANY(%s) AND e.occurred_at >= %s AND e.occurred_at < %s
                  AND e.actor_type IN ('visitor','user')
                  AND NOT EXISTS (SELECT 1 FROM gotrendlabs_analytics_history_days h
                        WHERE h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
                GROUP BY e.market_id,e.name
            )
            SELECT market_id,event_name,sum(n)::bigint AS n FROM observed
            GROUP BY market_id,event_name
        """, (start,end,ids,ids,start_at,end_at))
        stats = {mid:{} for mid in ids}
        for r in cursor.fetchall():
            stats[r["market_id"]][r["event_name"]] = r["n"]
        cursor.execute("""
            SELECT p.market_id,
                   count(DISTINCT p.user_id) FILTER (WHERE NOT u.is_bot) AS human_participants,
                   count(DISTINCT p.user_id) FILTER (WHERE u.is_bot) AS bot_participants,
                   count(*) FILTER (WHERE NOT u.is_bot AND p.action_type='initial') AS first_entries,
                   count(*) FILTER (WHERE NOT u.is_bot AND p.action_type='reinforcement') AS reinforcements,
                   count(*) FILTER (WHERE NOT u.is_bot AND p.action_type='revision') AS revisions,
                   coalesce(sum(p.stake_amount) FILTER (WHERE NOT u.is_bot AND p.action_type IN ('initial','reinforcement')),0) AS human_volume_gtc
            FROM gotrendlabs_predictions p JOIN gotrendlabs_users u ON u.id=p.user_id
            WHERE p.market_id=ANY(%s) AND p.created_at >= %s AND p.created_at < %s
              AND NOT u.is_staff AND NOT u.is_superuser
            GROUP BY p.market_id
        """, (ids,start_at,end_at))
        for r in cursor.fetchall():
            stats[r["market_id"]]["participation"] = {k:v for k,v in r.items() if k!="market_id"}
    items=[]
    observed_available=c["observed_first"] is not None and end>c["observed_first"] and start<=c["observed_last"]
    metric_coverage=_event_coverage(cursor)
    for row in rows:
        r=dict(row)
        metric=stats.get(row["id"],{})
        counts={name:metric.get(name,0) for name in EVENTS}
        visible_counts=_visible_events(counts,metric_coverage,start,end,c["observed_last"])
        r["observed"] = visible_counts
        r["observed_availability"] = "available" if observed_available else "not_instrumented"
        r["participation"] = _suppress_market_humans(metric.get("participation",{"human_participants":0,"bot_participants":0,
            "first_entries":0,"reinforcements":0,"revisions":0,"human_volume_gtc":0}))
        r["card_ctr"]={"numerator":visible_counts["market_card_clicked"],
                        "denominator":visible_counts["market_card_viewed"],
                        "value":round(counts["market_card_clicked"]/counts["market_card_viewed"],4)
                        if visible_counts["market_card_clicked"] is not None
                        and visible_counts["market_card_viewed"] is not None
                        and counts["market_card_viewed"] else None}
        items.append(r)
    return {"contract_version":"analytics-mcp.v1","generated_at":datetime.now(ZONE),
            "timezone":str(ZONE),"requested":{"start":start,"end_exclusive":end,"all_history":all_history},
            "observed_first":c["observed_first"],"consolidated_at":c["consolidated_at"],
            "items":items,"has_more":has_more,"next_cursor":rows[-1]["id"] if has_more else None,
            "order":"market_id_ascending","revision":revision,"precision":"exact",
            "partial_period":end>datetime.now(ZONE).date()}


def market(cursor, market_id, *, start=None, end=None, all_history=False):
    start,end,c = period(cursor,start=start,end=end,all_history=all_history)
    if market_id <= 0:
        _fail()
    cursor.execute("""SELECT p.market_id AS id,m.slug,m.status,p.kind,p.published_at,p.close_at,
        m.expected_resolution_at,m.resolved_at,m.canceled_at,p.category_id,p.subcategory_id,p.event_id,
        p.category_name,p.subcategory_name,p.event_name,p.provenance AS taxonomy_basis
        FROM gotrendlabs_analytics_market_publication p
        LEFT JOIN gotrendlabs_markets m ON m.id=p.market_id WHERE p.market_id=%s""", (market_id,))
    row=cursor.fetchone()
    if not row:
        _fail("not_found",404)
    counts=_observed_counts(cursor,start,end,market_id=market_id)
    actors=_actors(cursor,start,end,market_id=market_id)
    domain=_domain(cursor,start,end,market_id=market_id)
    funnel=_funnel(cursor,start,end,market_id=market_id)
    stake=_stake(cursor,end,market_id=market_id)
    social=_social(cursor,start,end,market_id=market_id)
    observed_available=c["observed_first"] is not None and end>c["observed_first"] and start<=c["observed_last"]
    visible_counts=_visible_events(counts,_event_coverage(cursor),start,end,c["observed_last"])
    cursor.execute("""
        SELECT min(day) AS first_day,max(day) AS last_day FROM (
          SELECT h.day FROM gotrendlabs_analytics_history_counts h
          WHERE h.market_id=%s AND h.day >= %s AND h.day < %s
            AND h.event_name='market_card_viewed' AND h.actor_type IN ('visitor','user')
          UNION ALL
          SELECT (e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date
          FROM gotrendlabs_analytics_events e
          WHERE e.market_id=%s AND e.occurred_at >= %s AND e.occurred_at < %s
            AND e.name='market_card_viewed' AND e.actor_type IN ('visitor','user')
            AND NOT EXISTS (SELECT 1 FROM gotrendlabs_analytics_history_days h
              WHERE h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
        ) exposure
    """,(market_id,start,end,market_id,bounds(start)[0],bounds(end)[0]))
    exposure=dict(cursor.fetchone())
    exposure.update({"impressions":visible_counts["market_card_viewed"],
                     "basis":"recorded card impressions; day precision; no inferred publication exposure"})
    domain=_suppress_market_humans(domain)
    if domain["small_segment_suppressed"]:
        stake["humans"]={"participants":None,"stake_gtc":None,"top_ten_share":None,
                         "concentration_suppressed":True}
        for key in ("likes","favorites","visible_comments"):
            social[key]=None
    if observed_available:
        actors={key:(None if value is not None and 0<value<5 else value)
                for key,value in actors.items()}
    if visible_counts["prediction_preview_viewed"] is None:
        funnel["previewed"]=None
    return {"contract_version":"analytics-mcp.v1","generated_at":datetime.now(ZONE),
            "timezone":str(ZONE),"requested":{"start":start,"end_exclusive":end,"all_history":all_history},
            "observed_first":c["observed_first"],"consolidated_at":c["consolidated_at"],
            "market":dict(row),"observed":visible_counts,
            "actors":actors if observed_available else {"visitors":None,"active_accounts":None},
            "participation":domain,"funnel":funnel if observed_available else {name:None for name in funnel},
            "stake":stake,"social":social,"observed_exposure":exposure,
            "card_ctr":{"numerator":visible_counts["market_card_clicked"],
                        "denominator":visible_counts["market_card_viewed"],
                        "value":round(counts["market_card_clicked"]/counts["market_card_viewed"],4)
                        if visible_counts["market_card_clicked"] is not None
                        and visible_counts["market_card_viewed"] is not None
                        and counts["market_card_viewed"] else None},
            "precision":"mixed: exact observed/domain counts; limited historical stake reconstruction and current-state social",
            "partial_period":end>datetime.now(ZONE).date()}


def _bucket(day, grain):
    if grain == "day":
        return day
    if grain == "week":
        return day-timedelta(days=day.weekday())
    if grain == "month":
        return day.replace(day=1)
    if grain == "year":
        return day.replace(month=1,day=1)
    _fail()


def _next_bucket(day, grain):
    if grain == "day":
        return day+timedelta(days=1)
    if grain == "week":
        return day+timedelta(days=7)
    if grain == "month":
        return date(day.year+1,1,1) if day.month==12 else date(day.year,day.month+1,1)
    if grain == "year":
        return date(day.year+1,1,1)
    _fail()


def series(cursor, *, start=None, end=None, all_history=False, grain="month",
           after=None, limit=50, platform="all", revision=None):
    start,end,c=period(cursor,start=start,end=end,all_history=all_history)
    prepare_actor_key(cursor)
    metric_coverage=_event_coverage(cursor)
    if grain not in GRAINS or platform not in ("all","web","mobile") or not 1<=limit<=100:
        _fail()
    first=_bucket(start,grain)
    if after is not None and (after<first or _bucket(after,grain)!=after):
        _fail()
    revision=_revision(cursor,revision,continuation=after is not None)
    current=_next_bucket(after,grain) if after else first
    buckets=[]
    while current<end and len(buckets)<=limit:
        buckets.append(current)
        current=_next_bucket(current,grain)
    has_more=len(buckets)>limit
    buckets=buckets[:limit]
    if not buckets:
        return {"contract_version":"analytics-mcp.v1","generated_at":datetime.now(ZONE),
                "timezone":str(ZONE),"grain":grain,
                "requested":{"start":start,"end_exclusive":end},"filters":_block_filters(platform),
                "observed_first":c["observed_first"],"metric_coverage":metric_coverage,
                "items":[],"has_more":False,
                "next_cursor":None,"revision":revision,"precision":"exact"}
    page_start=max(start,buckets[0])
    page_end=min(end,_next_bucket(buckets[-1],grain))
    start_at,_=bounds(page_start)
    end_at,_=bounds(page_end)
    cursor.execute(f"""
        WITH observed AS (
            SELECT date_trunc('{grain}',day::timestamp)::date AS bucket,event_name,sum(events)::bigint AS n
            FROM gotrendlabs_analytics_history_counts
            WHERE day >= %s AND day < %s AND market_id=0
              AND actor_type IN ('visitor','user') AND (%s='all' OR platform=%s)
            GROUP BY 1,2
            UNION ALL
            SELECT date_trunc('{grain}',e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date,
                   e.name,count(*)::bigint
            FROM gotrendlabs_analytics_events e
            WHERE e.occurred_at >= %s AND e.occurred_at < %s
              AND e.actor_type IN ('visitor','user') AND (%s='all' OR e.platform=%s)
              AND NOT EXISTS (SELECT 1 FROM gotrendlabs_analytics_history_days h
                              WHERE h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
            GROUP BY 1,2
        ) SELECT bucket,event_name,sum(n)::bigint AS n FROM observed GROUP BY 1,2
    """,(page_start,page_end,platform,platform,start_at,end_at,platform,platform))
    observed={b:{} for b in buckets}
    for r in cursor.fetchall():
        if r["bucket"] in observed:
            observed[r["bucket"]][r["event_name"]]=r["n"]
    cursor.execute(f"""
        WITH actors AS (
            SELECT date_trunc('{grain}',day::timestamp)::date AS bucket,actor_kind,actor_key,active_view
            FROM gotrendlabs_analytics_history_actors
            WHERE day >= %s AND day < %s AND market_id=0 AND (%s='all' OR platform=%s)
            UNION ALL
            SELECT date_trunc('{grain}',e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date,
                   CASE WHEN e.actor_type='visitor' THEN 'visitor' ELSE 'registered' END,
                   encode(hmac((CASE WHEN e.actor_type='visitor' THEN 'v:'||s.visitor_id::text
                                     ELSE 'u:'||e.user_id::text END)::bytea,
                               current_setting('gotrendlabs.analytics_actor_key')::bytea,'sha256'),'hex'),
                   e.name IN ('page_viewed','screen_viewed')
            FROM gotrendlabs_analytics_events e
            JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
            WHERE e.occurred_at >= %s AND e.occurred_at < %s
              AND (%s='all' OR e.platform=%s)
              AND NOT EXISTS (SELECT 1 FROM gotrendlabs_analytics_history_days h
                              WHERE h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
              AND e.actor_type IN ('visitor','user')
        ) SELECT bucket,count(DISTINCT actor_key) FILTER (WHERE actor_kind='visitor') AS visitors,
                 count(DISTINCT actor_key) FILTER (WHERE actor_kind='registered' AND active_view) AS active_accounts
          FROM actors GROUP BY bucket
    """,(page_start,page_end,platform,platform,start_at,end_at,platform,platform))
    actors={r["bucket"]:dict(r) for r in cursor.fetchall()}
    cursor.execute(f"""
        SELECT date_trunc('{grain}',p.created_at AT TIME ZONE 'America/Sao_Paulo')::date AS bucket,
               count(DISTINCT p.user_id) FILTER (WHERE NOT u.is_bot) AS human_participants,
               count(*) FILTER (WHERE NOT u.is_bot AND p.action_type='initial') AS first_entries
        FROM gotrendlabs_predictions p JOIN gotrendlabs_users u ON u.id=p.user_id
        WHERE p.created_at >= %s AND p.created_at < %s AND NOT u.is_staff AND NOT u.is_superuser
        GROUP BY 1
    """,(start_at,end_at))
    domain={r["bucket"]:dict(r) for r in cursor.fetchall()}
    items=[]
    for b in buckets:
        counts={name:observed[b].get(name,0) for name in EVENTS}
        bucket_start=max(start,b)
        bucket_end=min(end,_next_bucket(b,grain))
        available=c["observed_first"] is not None and bucket_end>c["observed_first"] and bucket_start<=c["observed_last"]
        items.append({"bucket_start":b,"covered_start":max(start,b),
                      "covered_end_exclusive":min(end,_next_bucket(b,grain)),
                      "partial_bucket":start>b or end<_next_bucket(b,grain),
                      "counts":_visible_events(counts,metric_coverage,bucket_start,bucket_end,c["observed_last"]),
                      "observed_availability":"available" if available else "not_instrumented",
                      "visitors":actors.get(b,{}).get("visitors",0) if available else None,
                      "active_accounts":actors.get(b,{}).get("active_accounts",0) if available else None,
                      "human_participants":domain.get(b,{}).get("human_participants",0),
                      "first_entries":domain.get(b,{}).get("first_entries",0)})
    return {"contract_version":"analytics-mcp.v1","generated_at":datetime.now(ZONE),
            "timezone":str(ZONE),"grain":grain,"requested":{"start":start,"end_exclusive":end},
            "filters":_block_filters(platform),"observed_first":c["observed_first"],
            "metric_coverage":metric_coverage,
            "items":items,"has_more":has_more,"next_cursor":buckets[-1] if has_more else None,
            "revision":revision,"precision":"exact"}


def compare(cursor, *, start, end, baseline_start=None, baseline_end=None,
            previous_equivalent=False, platform="all"):
    if previous_equivalent == (baseline_start is not None or baseline_end is not None):
        _fail()
    if previous_equivalent:
        baseline_end=start
        baseline_start=start-(end-start)
    if baseline_start is None or baseline_end is None or end-start != baseline_end-baseline_start:
        _fail()
    current=overview(cursor,start=start,end=end,platform=platform)
    baseline=overview(cursor,start=baseline_start,end=baseline_end,platform=platform)
    keys=("new_signups",)
    delta={}
    for key in keys:
        a=current[key]
        b=baseline[key]
        delta[key]={"absolute":a-b,"relative":round((a-b)/b,4) if b else None,
                    "baseline_zero":b==0}
    for key in ("human_participants","human_volume_gtc"):
        a=current["participation"][key]
        b=baseline["participation"][key]
        delta[key]={"absolute":a-b,"relative":round((a-b)/b,4) if b else None,
                    "baseline_zero":b==0}
    return {"contract_version":"analytics-mcp.v1","generated_at":datetime.now(ZONE),
            "timezone":str(ZONE),"current":current,"baseline":baseline,"delta":delta,
            "periods_equivalent_days":(end-start).days,"causal_claim":False}


SEGMENTS = {
    "category": ("lpad(p.category_id::text,12,'0')", "p.category_name"),
    "subcategory": ("lpad(p.subcategory_id::text,12,'0')", "p.subcategory_name"),
    "event": ("lpad(coalesce(p.event_id,0)::text,12,'0')", "coalesce(p.event_name,'Sem evento')"),
    "format": ("p.kind", "p.kind"),
    "duration": ("CASE WHEN p.close_at IS NULL THEN 'unknown' "
                 "WHEN p.close_at-p.published_at < interval '1 day' THEN 'under_1d' "
                 "WHEN p.close_at-p.published_at < interval '8 days' THEN '1_to_7d' "
                 "WHEN p.close_at-p.published_at < interval '31 days' THEN '8_to_30d' "
                 "ELSE 'over_30d' END", "''"),
}


def editorial(cursor, *, dimension="category", start=None, end=None,
              all_history=False, after="", limit=50, revision=None):
    start,end,c=period(cursor,start=start,end=end,all_history=all_history)
    if dimension not in SEGMENTS or not 1<=limit<=100 or len(after)>100:
        _fail()
    revision=_revision(cursor,revision,continuation=bool(after))
    key,label=SEGMENTS[dimension]
    if dimension == "duration":
        label = key
    start_at,_=bounds(start)
    end_at,_=bounds(end)
    cursor.execute(f"""
        WITH candidate AS (
            SELECT p.market_id,{key} AS group_key,{label} AS label,p.provenance
            FROM gotrendlabs_analytics_market_publication p
            WHERE p.published_at < %s AND (p.close_at IS NULL OR p.close_at >= %s)
        ), groups AS (
            SELECT group_key,min(label) AS label,count(*) AS markets,
                   count(DISTINCT label)>1 AS mixed_labels,
                   count(*) FILTER (WHERE provenance='reconstructed_current') AS reconstructed_markets
            FROM candidate WHERE group_key>%s GROUP BY group_key ORDER BY group_key LIMIT %s
        ), selected AS (
            SELECT candidate.* FROM candidate JOIN groups USING (group_key)
        ), observed AS (
            SELECT s.group_key,c.event_name,sum(c.events)::bigint AS n
            FROM selected s JOIN gotrendlabs_analytics_history_counts c ON c.market_id=s.market_id
            WHERE c.day >= %s AND c.day < %s AND c.actor_type IN ('visitor','user')
            GROUP BY s.group_key,c.event_name
            UNION ALL
            SELECT s.group_key,e.name,count(*)::bigint
            FROM selected s JOIN gotrendlabs_analytics_events e ON e.market_id=s.market_id
            WHERE e.occurred_at >= %s AND e.occurred_at < %s
              AND e.actor_type IN ('visitor','user')
              AND NOT EXISTS (SELECT 1 FROM gotrendlabs_analytics_history_days h
                    WHERE h.day=(e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date)
            GROUP BY s.group_key,e.name
        ), facts AS (
            SELECT s.group_key,count(DISTINCT p.user_id) FILTER (WHERE NOT u.is_bot) AS human_participants,
                   count(*) FILTER (WHERE NOT u.is_bot AND p.action_type='initial') AS first_entries
            FROM selected s JOIN gotrendlabs_predictions p ON p.market_id=s.market_id
            JOIN gotrendlabs_users u ON u.id=p.user_id
            WHERE p.created_at >= %s AND p.created_at < %s
              AND NOT u.is_staff AND NOT u.is_superuser
            GROUP BY s.group_key
        )
        SELECT g.group_key,g.label,g.markets,g.mixed_labels,g.reconstructed_markets,
               coalesce(sum(o.n) FILTER (WHERE o.event_name='market_card_viewed'),0)::bigint AS impressions,
               coalesce(sum(o.n) FILTER (WHERE o.event_name='market_card_clicked'),0)::bigint AS clicks,
               coalesce(sum(o.n) FILTER (WHERE o.event_name='market_detail_viewed'),0)::bigint AS detail_views,
               coalesce(max(f.human_participants),0) AS human_participants,
               coalesce(max(f.first_entries),0) AS first_entries
        FROM groups g LEFT JOIN observed o ON o.group_key=g.group_key
        LEFT JOIN facts f ON f.group_key=g.group_key
        GROUP BY g.group_key,g.label,g.markets,g.mixed_labels,g.reconstructed_markets
        ORDER BY g.group_key
    """,(end_at,start_at,after,limit+1,start,end,start_at,end_at,start_at,end_at))
    rows=cursor.fetchall()
    has_more=len(rows)>limit
    rows=rows[:limit]
    items=[]
    observed_available=c["observed_first"] is not None and end>c["observed_first"] and start<=c["observed_last"]
    metric_coverage=_event_coverage(cursor)
    for row in rows:
        r=dict(row)
        impressions=r["impressions"]
        clicks=r["clicks"]
        visible=_visible_events({name:({"market_card_viewed":impressions,
                                      "market_card_clicked":clicks,
                                      "market_detail_viewed":r["detail_views"]}.get(name,0))
                                 for name in EVENTS},metric_coverage,start,end,c["observed_last"])
        r["card_ctr"]={"numerator":visible["market_card_clicked"],
                       "denominator":visible["market_card_viewed"],
                       "value":round(r["clicks"]/r["impressions"],4)
                       if visible["market_card_clicked"] is not None
                       and visible["market_card_viewed"] is not None and r["impressions"] else None}
        r.update({"impressions":visible["market_card_viewed"],
                  "clicks":visible["market_card_clicked"],
                  "detail_views":visible["market_detail_viewed"]})
        r["observed_availability"]="available" if observed_available else "not_instrumented"
        if 0<r["human_participants"]<5:
            r["human_participants"]=None
            r["first_entries"]=None
            r["small_segment_suppressed"]=True
        else:
            r["small_segment_suppressed"]=False
        items.append(r)
    return {"contract_version":"analytics-mcp.v1","generated_at":datetime.now(ZONE),
            "timezone":str(ZONE),"requested":{"start":start,"end_exclusive":end},
            "dimension":dimension,"items":items,"has_more":has_more,
            "next_cursor":rows[-1]["group_key"] if has_more else None,
            "order":"group_key_ascending","revision":revision,"observed_first":c["observed_first"],
            "taxonomy_basis":"publication_snapshot; reconstructed_current flagged per group",
            "precision":"exact for observed events/domain facts; reconstructed taxonomy may differ from original"}
