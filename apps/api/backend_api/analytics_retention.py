"""Observed D1/D7/D30 product retention; no client event is a domain fact."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


ZONE = ZoneInfo("America/Sao_Paulo")
ACTIVE_EVENTS = ("page_viewed", "screen_viewed")
MILESTONES = (1, 7, 30)


def _series(cursor, *, audience, cutoff_at, today):
    if audience == "registered":
        cohorts = """
            SELECT u.id AS actor_id,
                   (u.date_joined AT TIME ZONE 'America/Sao_Paulo')::date AS cohort_day,
                   NULL::uuid AS first_session
            FROM gotrendlabs_users u
            WHERE u.date_joined >= %s AND u.is_bot=false
              AND u.is_staff=false AND u.is_superuser=false
        """
        activity = """
            SELECT e.user_id AS actor_id, e.session_id,
                   (e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date AS activity_day
            FROM gotrendlabs_analytics_events e
            WHERE e.user_id IS NOT NULL AND e.actor_type='user'
              AND e.name IN ('page_viewed', 'screen_viewed')
              AND e.occurred_at >= %s
        """
        extra = ""
    else:
        cohorts = """
            SELECT v.id AS actor_id,
                   (v.first_seen_at AT TIME ZONE 'America/Sao_Paulo')::date AS cohort_day,
                   (SELECT s.id FROM gotrendlabs_analytics_sessions s
                    WHERE s.visitor_id=v.id ORDER BY s.started_at, s.id LIMIT 1) AS first_session
            FROM gotrendlabs_analytics_visitors v
            WHERE v.first_seen_at >= %s
              AND EXISTS (
                  SELECT 1 FROM gotrendlabs_analytics_events e
                  JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
                  WHERE s.visitor_id=v.id AND e.actor_type='visitor'
                    AND e.name IN ('page_viewed', 'screen_viewed')
                    AND (e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date =
                        (v.first_seen_at AT TIME ZONE 'America/Sao_Paulo')::date
              )
        """
        activity = """
            SELECT s.visitor_id AS actor_id, e.session_id,
                   (e.occurred_at AT TIME ZONE 'America/Sao_Paulo')::date AS activity_day
            FROM gotrendlabs_analytics_events e
            JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
            WHERE e.actor_type='visitor'
              AND e.name IN ('page_viewed', 'screen_viewed')
              AND e.occurred_at >= %s
        """
        extra = "AND a.session_id <> c.first_session"

    cursor.execute("""
        WITH cohorts AS (
    """ + cohorts + """
        ), activity AS (
    """ + activity + """
        ), per_actor AS (
            SELECT c.actor_id, c.cohort_day,
                   date_trunc('week', c.cohort_day::timestamp)::date AS cohort_week,
                   bool_or(a.activity_day = c.cohort_day + 1) AS returned_d1,
                   bool_or(a.activity_day = c.cohort_day + 7) AS returned_d7,
                   bool_or(a.activity_day = c.cohort_day + 30) AS returned_d30
            FROM cohorts c LEFT JOIN activity a ON a.actor_id=c.actor_id
              AND a.activity_day BETWEEN c.cohort_day + 1 AND c.cohort_day + 30
    """ + extra + """
            GROUP BY c.actor_id, c.cohort_day
        )
        SELECT cohort_week,
               COUNT(*) FILTER (WHERE cohort_day + 1 < %s) AS eligible_d1,
               COUNT(*) FILTER (WHERE cohort_day + 1 < %s AND returned_d1) AS returned_d1,
               COUNT(*) FILTER (WHERE cohort_day + 7 < %s) AS eligible_d7,
               COUNT(*) FILTER (WHERE cohort_day + 7 < %s AND returned_d7) AS returned_d7,
               COUNT(*) FILTER (WHERE cohort_day + 30 < %s) AS eligible_d30,
               COUNT(*) FILTER (WHERE cohort_day + 30 < %s AND returned_d30) AS returned_d30
        FROM per_actor GROUP BY cohort_week ORDER BY cohort_week DESC LIMIT 14
    """, (cutoff_at, cutoff_at, today, today, today, today, today, today))
    rows = []
    for item in cursor.fetchall():
        row = {"week": item["cohort_week"].isoformat()}
        for day in MILESTONES:
            eligible = item[f"eligible_d{day}"]
            returned = item[f"returned_d{day}"]
            row[f"d{day}"] = {"eligible": eligible, "returned": returned,
                              "rate": round(returned * 100 / eligible) if eligible else None}
        rows.append(row)
    totals = {}
    for day in MILESTONES:
        eligible = sum(row[f"d{day}"]["eligible"] for row in rows)
        returned = sum(row[f"d{day}"]["returned"] for row in rows)
        totals[f"d{day}"] = {"eligible": eligible, "returned": returned,
                             "rate": round(returned * 100 / eligible) if eligible else None}
    return {"totals": totals, "cohorts": rows}


def retention(cursor, *, now=None):
    now = now or datetime.now(ZONE)
    today = now.astimezone(ZONE).date()
    cursor.execute("""
        SELECT MIN(received_at) AS first_at FROM gotrendlabs_analytics_events
        WHERE actor_type IN ('visitor', 'user')
    """)
    first = cursor.fetchone()["first_at"]
    empty = {f"d{day}": {"eligible": 0, "returned": 0, "rate": None} for day in MILESTONES}
    if first is None:
        return {"timezone": "America/Sao_Paulo", "since": None,
                "registered": {"totals": empty, "cohorts": []},
                "visitors": {"totals": empty, "cohorts": []}}
    # The first observed day can be partial; do not present older signups as zero retention.
    first_complete_day = first.astimezone(ZONE).date() + timedelta(days=1)
    cutoff_day = max(today - timedelta(days=90), first_complete_day)
    cutoff_at = datetime.combine(cutoff_day, time.min, ZONE)
    return {"timezone": "America/Sao_Paulo", "since": cutoff_day.isoformat() if cutoff_day <= today else None,
            "registered": _series(cursor, audience="registered", cutoff_at=cutoff_at, today=today),
            "visitors": _series(cursor, audience="visitors", cutoff_at=cutoff_at, today=today)}
