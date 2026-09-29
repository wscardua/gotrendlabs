"""First-party product analytics. Client events are observations, never domain facts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from ipaddress import ip_address, ip_network
import hmac
import json
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field

from apps.api.backend_api.analytics_retention import retention as calculate_retention


EVENT_PROPERTIES = {
    "page_viewed": set(), "screen_viewed": set(), "navigation_clicked": set(),
    "market_card_viewed": {"market_slug", "placement"},
    "market_card_clicked": {"market_slug", "placement"},
    "market_filter_applied": {"filter"},
    "search_performed": {"result_count"},
    "scroll_reached": {"percent"},
    "signup_started": set(), "login_started": set(),
    "market_detail_viewed": {"market_slug"},
    "prediction_started": {"market_slug"},
    "prediction_option_selected": {"market_slug"},
    "prediction_preview_viewed": {"market_slug"},
    "prediction_submit_clicked": {"market_slug"},
    "position_action_started": {"market_slug", "action"},
    "position_preview_viewed": {"market_slug", "action"},
    "share_started": {"market_slug", "kind"},
    "link_copied": {"kind"},
    "notification_opened": {"kind"},
    "integrity_opened": {"market_slug"},
    "contribution_started": {"kind"},
    "wallet_opened": set(),
    "market_like_clicked": {"market_slug"},
    "market_favorite_clicked": {"market_slug"},
    "comment_submit_clicked": {"market_slug"},
    "comment_reaction_clicked": {"market_slug"},
    "position_submit_clicked": {"market_slug", "action"},
    "suggestion_submit_clicked": set(),
    "feedback_submit_clicked": set(),
    "recharge_submit_clicked": set(),
    "profile_update_clicked": set(),
    "badge_share_clicked": set(),
    "referral_share_clicked": set(),
}


class AnalyticsEvent(BaseModel):
    event_id: UUID
    view_id: Optional[UUID] = None
    name: str = Field(min_length=1, max_length=60)
    occurred_at: datetime
    screen_key: str = Field(default="", max_length=120, pattern=r"^[a-zA-Z0-9_:/{}.-]*$")
    target_key: str = Field(default="", max_length=120, pattern=r"^[a-zA-Z0-9_:/{}.-]*$")
    properties: dict = Field(default_factory=dict)


class AnalyticsBatch(BaseModel):
    visitor_id: UUID
    session_id: UUID
    entry_screen: str = Field(default="", max_length=120, pattern=r"^[a-zA-Z0-9_:/{}.-]*$")
    referrer_host: str = Field(default="", max_length=255)
    utm_source: str = Field(default="", max_length=120, pattern=r"^[a-zA-Z0-9_.-]*$")
    utm_medium: str = Field(default="", max_length=120, pattern=r"^[a-zA-Z0-9_.-]*$")
    utm_campaign: str = Field(default="", max_length=120, pattern=r"^[a-zA-Z0-9_.-]*$")
    events: list[AnalyticsEvent] = Field(min_length=1, max_length=20)


def _safe_properties(event):
    allowed = EVENT_PROPERTIES.get(event.name)
    if allowed is None or set(event.properties) - allowed:
        raise HTTPException(422, detail="Evento ou propriedades não permitidos.")
    if len(json.dumps(event.properties)) > 512:
        raise HTTPException(422, detail="Propriedades muito grandes.")
    for value in event.properties.values():
        if not isinstance(value, (str, int, bool)) or isinstance(value, str) and not re.fullmatch(r"[a-zA-Z0-9_:/{}.-]{1,80}", value):
            raise HTTPException(422, detail="Propriedade inválida.")
    if event.name == "scroll_reached" and event.properties.get("percent") not in {25, 50, 75, 100}:
        raise HTTPException(422, detail="Marco de rolagem inválido.")
    if event.name == "search_performed" and not isinstance(event.properties.get("result_count"), int):
        raise HTTPException(422, detail="Contagem de busca obrigatória.")
    return json.dumps(event.properties)


def _geo(ip):
    path = os.environ.get("GOTRENDLABS_GEOLITE_CITY_PATH", "")
    if not path or not Path(path).is_file():
        return None
    try:
        address = ip_address(ip)
        if not address.is_global:
            return None
        import geoip2.database
        import geoip2.errors
        with geoip2.database.Reader(path) as reader:
            try:
                result = reader.city(str(address))
            except geoip2.errors.AddressNotFoundError:
                return None
            return {
                "country": result.country.iso_code,
                "region": result.subdivisions.most_specific.iso_code,
                "city": result.city.name,
                "radius": result.location.accuracy_radius,
                "version": str(reader.metadata().build_epoch),
            }
    except Exception:
        # Um arquivo GeoLite ausente/corrompido não pode interromper a coleta.
        return None


def _source_ip(request):
    secret = os.environ.get("GOTRENDLABS_ANALYTICS_PROXY_SECRET", "")
    supplied = request.headers.get("x-analytics-proxy-secret", "")
    forwarded = request.headers.get("x-analytics-client-ip", "")
    if secret and forwarded and hmac.compare_digest(secret, supplied or ""):
        return forwarded
    peer = request.client.host if request.client else ""
    trusted = os.environ.get("GOTRENDLABS_ANALYTICS_TRUSTED_PROXY_CIDRS", "")
    try:
        if any(ip_address(peer) in ip_network(part.strip()) for part in trusted.split(",") if part.strip()):
            candidate = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            if candidate:
                return str(ip_address(candidate))
    except ValueError:
        pass
    return peer


def geolite_file_status():
    path = os.environ.get("GOTRENDLABS_GEOLITE_CITY_PATH", "")
    if not path:
        return {"state": "not_configured"}
    source = Path(path)
    if not source.is_file():
        return {"state": "missing"}
    try:
        import geoip2.database
        with geoip2.database.Reader(str(source)) as reader:
            metadata = reader.metadata()
            if "City" not in metadata.database_type:
                return {"state": "invalid"}
            return {"state": "ready", "database_type": metadata.database_type,
                    "database_build_at": datetime.fromtimestamp(metadata.build_epoch, timezone.utc).isoformat(),
                    "file_size_bytes": source.stat().st_size, "node_count": metadata.node_count,
                    "file_modified_at": datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat()}
    except Exception:
        return {"state": "invalid"}


def ingest(cursor, batch, *, request, user):
    now = datetime.now(timezone.utc)
    platform = "mobile" if request.headers.get("x-gotrendlabs-client") == "mobile" else "web"
    actor = "bot" if user and user.get("is_bot") else "staff" if user and (user.get("is_staff") or user.get("is_superuser")) else "user" if user else "visitor"
    if any(event.occurred_at.tzinfo is None or not now - timedelta(days=7) <= event.occurred_at <= now + timedelta(minutes=5) for event in batch.events):
        raise HTTPException(422, detail="Horário de evento inválido.")
    encoded = [_safe_properties(event) for event in batch.events]
    if any(value and (urlsplit("//" + value).hostname or "") != value.lower() for value in [batch.referrer_host]):
        raise HTTPException(422, detail="Origem inválida.")
    cursor.execute("INSERT INTO gotrendlabs_analytics_visitors(id) VALUES (%s) ON CONFLICT (id) DO UPDATE SET last_seen_at=now()", (batch.visitor_id,))
    cursor.execute("SELECT visitor_id, platform FROM gotrendlabs_analytics_sessions WHERE id=%s", (batch.session_id,))
    session = cursor.fetchone()
    new_session = False
    if session is None:
        geo = _geo(_source_ip(request))
        cursor.execute("""
            INSERT INTO gotrendlabs_analytics_sessions
              (id, visitor_id, platform, entry_screen, referrer_host, utm_source, utm_medium, utm_campaign,
               country_code, region_code, city_name, geo_accuracy_radius_km, geo_database_version)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING
        """, (batch.session_id, batch.visitor_id, platform, batch.entry_screen, batch.referrer_host,
              batch.utm_source, batch.utm_medium, batch.utm_campaign,
              (geo or {}).get("country"), (geo or {}).get("region"), (geo or {}).get("city"),
              (geo or {}).get("radius"), (geo or {}).get("version")))
        new_session = cursor.rowcount == 1
        cursor.execute("SELECT visitor_id, platform FROM gotrendlabs_analytics_sessions WHERE id=%s", (batch.session_id,))
        session = cursor.fetchone()
    if str(session["visitor_id"]) != str(batch.visitor_id) or session["platform"] != platform:
        raise HTTPException(409, detail="Sessão vinculada a outro visitante.")
    cursor.execute("UPDATE gotrendlabs_analytics_sessions SET last_seen_at=now() WHERE id=%s", (batch.session_id,))
    accepted = 0
    for event, props in zip(batch.events, encoded):
        if event.view_id:
            cursor.execute("""
                INSERT INTO gotrendlabs_analytics_views (id, session_id, screen_key)
                VALUES (%s,%s,%s) ON CONFLICT (id) DO NOTHING
            """, (event.view_id, batch.session_id, event.screen_key))
            cursor.execute("SELECT session_id FROM gotrendlabs_analytics_views WHERE id=%s", (event.view_id,))
            if str(cursor.fetchone()["session_id"]) != str(batch.session_id):
                raise HTTPException(409, detail="Visualização vinculada a outra sessão.")
        cursor.execute("""
            INSERT INTO gotrendlabs_analytics_events
              (id, session_id, view_id, user_id, name, platform, actor_type, auth_state,
               screen_key, target_key, occurred_at, properties)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
            ON CONFLICT (id) DO NOTHING
        """, (event.event_id, batch.session_id, event.view_id, user["id"] if user else None,
              event.name, platform, actor, "authenticated" if user else "anonymous",
              event.screen_key, event.target_key, event.occurred_at, props))
        accepted += cursor.rowcount
    cursor.execute("""
        INSERT INTO gotrendlabs_analytics_ingestion_status
          (id, completed_at, platform, received, accepted, new_session)
        VALUES (1, clock_timestamp(), %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
          completed_at=EXCLUDED.completed_at, platform=EXCLUDED.platform,
          received=EXCLUDED.received, accepted=EXCLUDED.accepted,
          new_session=EXCLUDED.new_session
        WHERE gotrendlabs_analytics_ingestion_status.completed_at <= EXCLUDED.completed_at
    """, (platform, len(batch.events), accepted, new_session))
    return {"accepted": accepted}


def summary(cursor, *, days=7, platform="all", audience="all", region="", city=""):
    if days not in {1, 7, 30, 90} or platform not in {"all", "web", "mobile"} or audience not in {"all", "anonymous", "authenticated"}:
        raise HTTPException(422, detail="Filtro inválido.")
    if len(region) > 20 or len(city) > 120:
        raise HTTPException(422, detail="Região inválida.")
    since = datetime.now(timezone.utc) - timedelta(days=days)
    where = ["e.received_at >= %s", "e.actor_type IN ('visitor', 'user')"]
    args = [since]
    if platform != "all":
        where.append("e.platform = %s")
        args.append(platform)
    if audience != "all":
        where.append("e.auth_state = %s")
        args.append(audience)
    if region:
        where.append("s.region_code = %s")
        args.append(region)
    if city:
        where.append("s.city_name = %s")
        args.append(city)
    filtered = " FROM gotrendlabs_analytics_events e JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id WHERE " + " AND ".join(where)
    cursor.execute("""
        SELECT COUNT(DISTINCT s.visitor_id) AS visitors,
               COUNT(DISTINCT e.session_id) AS sessions,
               COUNT(DISTINCT e.user_id) AS users,
               COUNT(*) FILTER (WHERE e.name IN ('page_viewed','screen_viewed')) AS views,
               COUNT(DISTINCT e.session_id) FILTER (WHERE e.received_at >= now() - interval '5 minutes') AS recent_sessions,
               COUNT(DISTINCT e.session_id) FILTER (WHERE s.country_code IS NOT NULL) AS located_sessions
    """ + filtered, args)
    totals = dict(cursor.fetchone())
    cursor.execute("""
        SELECT date_trunc('day', e.received_at)::date AS day,
               COUNT(DISTINCT e.session_id) AS sessions,
               COUNT(*) FILTER (WHERE e.name IN ('page_viewed','screen_viewed')) AS views
    """ + filtered + " GROUP BY 1 ORDER BY 1", args)
    daily = [{"day": row["day"].isoformat(), "sessions": row["sessions"], "views": row["views"]} for row in cursor.fetchall()]
    peak = max((row["views"] for row in daily), default=0)
    for row in daily:
        row["percent"] = round(row["views"] * 100 / peak) if peak else 0
    cursor.execute("""
        SELECT e.screen_key AS key, COUNT(*) AS views,
               COUNT(DISTINCT e.session_id) AS sessions
    """ + filtered + " AND e.name IN ('page_viewed','screen_viewed') GROUP BY 1 ORDER BY views DESC LIMIT 10", args)
    screens = [dict(row) for row in cursor.fetchall()]
    cursor.execute("""
        SELECT s.country_code, s.region_code, s.city_name,
               COUNT(DISTINCT e.session_id) AS sessions,
               COUNT(DISTINCT e.user_id) AS users
    """ + filtered + " GROUP BY 1,2,3 ORDER BY sessions DESC LIMIT 30", args)
    geography = [dict(row) for row in cursor.fetchall()]
    cursor.execute("""
        SELECT s.country_code, s.region_code,
               COUNT(DISTINCT e.session_id) AS sessions,
               COUNT(DISTINCT e.user_id) AS users
    """ + filtered + " AND s.country_code = 'BR' AND s.region_code IS NOT NULL GROUP BY 1,2 ORDER BY sessions DESC, 1, 2 LIMIT 27", args)
    regions = [dict(row) for row in cursor.fetchall()]
    region_peak = max((row["sessions"] for row in regions), default=0)
    for row in regions:
        row["percent"] = round(row["sessions"] * 100 / region_peak) if region_peak else 0
    cursor.execute("""
        SELECT s.country_code, s.region_code, s.city_name,
               COUNT(DISTINCT e.session_id) AS sessions,
               COUNT(DISTINCT e.user_id) AS users
    """ + filtered + " AND s.country_code = 'BR' AND s.city_name IS NOT NULL GROUP BY 1,2,3 ORDER BY sessions DESC, 1, 2, 3 LIMIT 20", args)
    cities = [dict(row) for row in cursor.fetchall()]
    cursor.execute("""
        SELECT date_trunc('day', e.received_at)::date AS day,
               COUNT(DISTINCT e.session_id) FILTER (WHERE s.country_code IS NOT NULL) AS located_sessions,
               COUNT(DISTINCT e.session_id) FILTER (WHERE s.region_code IS NOT NULL) AS regional_sessions,
               COUNT(DISTINCT e.session_id) AS sessions
    """ + filtered + " GROUP BY 1 ORDER BY 1", args)
    geo_daily = [{"day": row["day"].isoformat(), "located_sessions": row["located_sessions"],
                  "regional_sessions": row["regional_sessions"], "sessions": row["sessions"]}
                 for row in cursor.fetchall()]
    for row in geo_daily:
        row["percent"] = round(row["regional_sessions"] * 100 / row["sessions"]) if row["sessions"] else 0
    trend_region = region or (regions[0]["region_code"] if regions else "")
    region_daily = []
    if trend_region:
        cursor.execute("""
            SELECT date_trunc('day', e.received_at)::date AS day,
                   COUNT(DISTINCT e.session_id) AS sessions
        """ + filtered + " AND s.country_code='BR' AND s.region_code=%s GROUP BY 1 ORDER BY 1",
                       args + [trend_region])
        region_daily = [{"day": row["day"].isoformat(), "sessions": row["sessions"]}
                        for row in cursor.fetchall()]
        trend_peak = max((row["sessions"] for row in region_daily), default=0)
        for row in region_daily:
            row["percent"] = round(row["sessions"] * 100 / trend_peak) if trend_peak else 0
    cursor.execute("""
        SELECT COALESCE(NULLIF(s.utm_source, ''), NULLIF(s.referrer_host, ''), 'Direto/desconhecido') AS source,
               COUNT(DISTINCT e.session_id) AS sessions
    """ + filtered + " GROUP BY 1 ORDER BY sessions DESC LIMIT 10", args)
    sources = [dict(row) for row in cursor.fetchall()]
    cursor.execute("""
        SELECT e.properties->>'market_slug' AS slug,
               COUNT(*) FILTER (WHERE e.name='market_card_viewed') AS impressions,
               COUNT(*) FILTER (WHERE e.name='market_card_clicked') AS clicks,
               COUNT(*) FILTER (WHERE e.name='prediction_started') AS tickets
    """ + filtered + " AND e.name IN ('market_card_viewed','market_card_clicked','prediction_started')"
          " AND e.properties ? 'market_slug' GROUP BY 1 ORDER BY impressions DESC, clicks DESC LIMIT 10", args)
    markets = [dict(row) for row in cursor.fetchall()]
    cursor.execute("""
        WITH steps AS (
            SELECT e.session_id,
                   MIN(e.occurred_at) FILTER (WHERE e.name IN ('page_viewed','screen_viewed')) AS visited_at,
                   MIN(e.occurred_at) FILTER (WHERE e.name='market_detail_viewed') AS market_at,
                   MIN(e.occurred_at) FILTER (WHERE e.name='prediction_started') AS ticket_at,
                   MIN(e.occurred_at) FILTER (WHERE e.name='prediction_submit_clicked') AS submit_at
    """ + filtered + """ GROUP BY e.session_id
        )
        SELECT COUNT(*) FILTER (WHERE visited_at IS NOT NULL) AS visited,
               COUNT(*) FILTER (WHERE market_at >= visited_at) AS market_opened,
               COUNT(*) FILTER (WHERE ticket_at >= market_at AND market_at >= visited_at) AS ticket_started,
               COUNT(*) FILTER (WHERE submit_at >= ticket_at AND ticket_at >= market_at AND market_at >= visited_at) AS submit_clicked
        FROM steps
    """, args)
    funnel = dict(cursor.fetchone())
    cursor.execute("""
        WITH starts AS (
            SELECT e.session_id, e.properties->>'market_slug' AS slug,
                   MIN(e.occurred_at) AS started_at, MAX(s.last_seen_at) AS last_seen_at
    """ + filtered + """ AND e.name='prediction_started'
                          AND NULLIF(e.properties->>'market_slug', '') IS NOT NULL
            GROUP BY e.session_id, e.properties->>'market_slug'
        ), progress AS (
            SELECT st.session_id, st.slug, st.started_at, st.last_seen_at,
                   MIN(e.occurred_at) FILTER (WHERE e.name IN ('prediction_option_selected',
                       'prediction_preview_viewed') AND e.occurred_at >= st.started_at) AS engaged_at,
                   MIN(e.occurred_at) FILTER (WHERE e.name='prediction_submit_clicked'
                       AND e.occurred_at >= st.started_at) AS submit_at
            FROM starts st LEFT JOIN gotrendlabs_analytics_events e
              ON e.session_id=st.session_id AND e.properties->>'market_slug'=st.slug
              AND e.received_at >= %s AND e.actor_type IN ('visitor','user')
              AND e.name IN ('prediction_option_selected','prediction_preview_viewed',
                             'prediction_submit_clicked')
            GROUP BY st.session_id, st.slug, st.started_at, st.last_seen_at
        )
        SELECT COUNT(*) AS started,
               COUNT(*) FILTER (WHERE engaged_at IS NOT NULL) AS engaged,
               COUNT(*) FILTER (WHERE submit_at IS NOT NULL AND
                   (engaged_at IS NULL OR submit_at >= engaged_at)) AS submit_clicked,
               COUNT(*) FILTER (WHERE last_seen_at < now() - interval '30 minutes') AS eligible,
               COUNT(*) FILTER (WHERE last_seen_at < now() - interval '30 minutes'
                   AND engaged_at IS NULL AND submit_at IS NULL) AS abandoned_before_choice,
               COUNT(*) FILTER (WHERE last_seen_at < now() - interval '30 minutes'
                   AND engaged_at IS NOT NULL AND submit_at IS NULL) AS abandoned_after_choice
        FROM progress
    """, args + [since])
    abandonment = dict(cursor.fetchone())
    cursor.execute("""
        SELECT COUNT(DISTINCT e.user_id) AS started_users,
               COUNT(DISTINCT p.user_id) AS confirmed_users
        FROM gotrendlabs_analytics_events e
        JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
        LEFT JOIN gotrendlabs_markets m ON m.slug=e.properties->>'market_slug'
        LEFT JOIN gotrendlabs_predictions p ON p.market_id=m.id AND p.user_id=e.user_id
          AND p.action_type='initial' AND p.created_at >= e.occurred_at
          AND p.created_at <= e.occurred_at + interval '7 days'
        WHERE """ + " AND ".join(where) + " AND e.name='prediction_started' AND e.user_id IS NOT NULL", args)
    authenticated_funnel = dict(cursor.fetchone())
    insights = []
    previous_where = ["e.received_at >= %s", "e.received_at < %s"] + where[1:]
    cursor.execute("SELECT COUNT(DISTINCT e.session_id) AS sessions FROM gotrendlabs_analytics_events e JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id WHERE " + " AND ".join(previous_where),
                   [since - timedelta(days=days), since] + args[1:])
    previous_sessions = cursor.fetchone()["sessions"]
    if previous_sessions >= 20:
        change = round((totals["sessions"] - previous_sessions) * 100 / previous_sessions)
        if abs(change) >= 25:
            direction = "cresceram" if change > 0 else "caíram"
            insights.append({"kind": "traffic_change", "title": f"Sessões {direction} {abs(change)}%",
                             "detail": f"{totals['sessions']} sessões neste período, ante {previous_sessions} no período equivalente anterior.",
                             "sample": totals["sessions"] + previous_sessions})
    if funnel["ticket_started"] >= 20 and funnel["submit_clicked"] / funnel["ticket_started"] < 0.4:
        insights.append({"kind": "funnel_drop", "title": "Poucos tickets avançam até confirmar",
                         "detail": f"{funnel['submit_clicked']} de {funnel['ticket_started']} sessões com ticket registraram clique em confirmar.",
                         "sample": funnel["ticket_started"]})
    if abandonment["eligible"] >= 20:
        abandoned = abandonment["abandoned_before_choice"] + abandonment["abandoned_after_choice"]
        if abandoned / abandonment["eligible"] >= 0.5:
            insights.append({"kind": "ticket_abandonment", "title": "Muitos tickets param antes do envio",
                             "detail": f"{abandoned} de {abandonment['eligible']} jornadas de sessão/mercado ficaram sem clique em confirmar após 30 minutos de inatividade.",
                             "sample": abandonment["eligible"]})
    for item in markets:
        if item["impressions"] >= 50 and item["clicks"] / item["impressions"] < 0.02:
            insights.append({"kind": "market_low_click", "title": "Mercado com poucas aberturas",
                             "detail": f"{item['slug']}: {item['clicks']} cliques em {item['impressions']} impressões.",
                             "sample": item["impressions"]})
            break
    if (geography and geography[0]["region_code"] and totals["sessions"] >= 30
            and geography[0]["sessions"] / totals["sessions"] >= 0.4):
        top = geography[0]
        insights.append({"kind": "regional_concentration", "title": "Acesso concentrado em uma região",
                         "detail": f"{top['region_code'] or top['country_code'] or 'Local desconhecido'} reúne {top['sessions']} de {totals['sessions']} sessões observadas.",
                         "sample": totals["sessions"]})
    cursor.execute("""
        SELECT COUNT(*) AS signups FROM gotrendlabs_users
        WHERE date_joined >= %s AND is_bot=false AND is_staff=false AND is_superuser=false
    """, (since,))
    signups = cursor.fetchone()["signups"]
    cursor.execute("""
        SELECT COUNT(*) AS predictions, COUNT(DISTINCT p.user_id) AS participants
        FROM gotrendlabs_predictions p JOIN gotrendlabs_users u ON u.id=p.user_id
        WHERE p.created_at >= %s AND u.is_bot=false AND u.is_staff=false AND u.is_superuser=false
    """, (since,))
    prediction_counts = dict(cursor.fetchone())
    cursor.execute("SELECT completed_at, platform, received, accepted, new_session FROM gotrendlabs_analytics_ingestion_status WHERE id=1")
    ingestion_row = cursor.fetchone()
    ingestion = dict(ingestion_row) if ingestion_row else None
    if ingestion:
        ingestion["completed_at"] = ingestion["completed_at"].isoformat()
        ingestion["duplicates"] = ingestion["received"] - ingestion["accepted"]
    cursor.execute("""
        SELECT COUNT(*) AS events, COUNT(DISTINCT e.session_id) AS sessions,
               COUNT(DISTINCT s.visitor_id) AS visitors
        FROM gotrendlabs_analytics_events e
        JOIN gotrendlabs_analytics_sessions s ON s.id=e.session_id
        WHERE e.received_at >= now() - interval '24 hours'
          AND e.actor_type IN ('visitor', 'user')
    """)
    collection_24h = dict(cursor.fetchone())
    cursor.execute("SELECT received_at FROM gotrendlabs_analytics_events WHERE actor_type IN ('visitor','user') ORDER BY received_at DESC LIMIT 1")
    latest_event = cursor.fetchone()
    collection_24h["last_event_at"] = latest_event["received_at"].isoformat() if latest_event else None
    cursor.execute("""
        SELECT started_at, completed_at, status, database_build_at, database_type,
               file_size_bytes, node_count, error_code
        FROM gotrendlabs_geolite_load_runs ORDER BY completed_at DESC, id DESC LIMIT 1
    """)
    geolite_row = cursor.fetchone()
    geolite_run = dict(geolite_row) if geolite_row else None
    if geolite_run:
        for key in ("started_at", "completed_at", "database_build_at"):
            if geolite_run[key]:
                geolite_run[key] = geolite_run[key].isoformat()
    retention = calculate_retention(cursor)
    return {"period_days": days, "generated_at": datetime.now(timezone.utc).isoformat(),
            "totals": totals, "daily": daily, "screens": screens, "geography": geography,
            "regions": regions, "cities": cities, "geo_daily": geo_daily,
            "trend_region": trend_region, "region_daily": region_daily,
            "sources": sources, "markets": markets, "funnel": funnel,
            "abandonment": abandonment, "authenticated_funnel": authenticated_funnel, "insights": insights[:5],
            "last_ingestion": ingestion, "collection_24h": collection_24h,
            "last_geolite_run": geolite_run, "geolite_file": geolite_file_status(),
            "retention": retention,
            "domain_totals": {"signups": signups, **prediction_counts},
            "coverage": "Navegação observada desde a ativação da coleta. Cadastros e previsões vêm do banco de domínio e são globais: filtros de plataforma, público e região não se aplicam a esses totais."}


def prune(cursor, *, now=None, retention_days=90):
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max(30, min(retention_days, 365)))
    cursor.execute("DELETE FROM gotrendlabs_analytics_events WHERE received_at < %s", (cutoff,))
    events = cursor.rowcount
    cursor.execute("DELETE FROM gotrendlabs_analytics_views WHERE session_id IN (SELECT id FROM gotrendlabs_analytics_sessions WHERE last_seen_at < %s)", (cutoff,))
    cursor.execute("DELETE FROM gotrendlabs_analytics_sessions WHERE last_seen_at < %s", (cutoff,))
    sessions = cursor.rowcount
    cursor.execute("DELETE FROM gotrendlabs_analytics_visitors v WHERE NOT EXISTS (SELECT 1 FROM gotrendlabs_analytics_sessions s WHERE s.visitor_id=v.id)")
    return {"events": events, "sessions": sessions}
