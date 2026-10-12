"""Generate isolated HTML fixtures for manual browser QA; never writes database events.

Run with the project's existing venv and serve the output with a loopback HTTP server.
Fixtures use real templates/assets and isolate themes on their loopback QA origin.
"""
import os
import re
import sys
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.template.loader import render_to_string
from django.utils.translation import override


def report_fixture(days=7, state="missing", variant="all"):
    zero = variant == "empty"
    metric = {"eligible": 20, "returned": 4, "rate": 20}
    audience = {"totals": {key: deepcopy(metric) for key in ("d1", "d7", "d30")}, "cohorts": []}
    daily = [{"day": (date(2026, 10, 12) - timedelta(days=days-index)).isoformat(),
              "web_sessions": 0 if zero or variant == "mobile" else index % 8,
              "mobile_sessions": 0 if zero or variant == "web" else index % 8}
             for index in range(days+1)]
    platforms = []
    for key in (("web", "mobile") if variant in ("all", "empty") else (variant,)):
        sessions = sum(day[f"{key}_sessions"] for day in daily)
        visitors = (sessions + 1) // 2
        platforms.append({"platform": key, "sessions": sessions, "visitors": visitors,
                          "users": min(12, visitors), "views": sessions * 3,
                          "session_share": None if zero else 50.0 if variant == "all" else 100.0})
    total_sessions = sum(row["sessions"] for row in platforms)
    located = total_sessions // 3
    latest = "2026-08-01T20:00:00Z" if zero else "2026-10-12T20:00:00Z"
    return {
        "generated_at": "2026-10-12T21:00:00Z", "period_days": days,
        "totals": {"visitors": sum(row["visitors"] for row in platforms), "sessions": total_sessions,
                   "views": sum(row["views"] for row in platforms), "users": max(row["users"] for row in platforms),
                   "recent_sessions": 0, "located_sessions": located},
        "platforms": platforms, "platform_daily": daily,
        "daily": [{"day": row["day"], "sessions": row["web_sessions"]+row["mobile_sessions"],
                   "views": (row["web_sessions"]+row["mobile_sessions"])*3, "percent": 100}
                  for row in daily] if not zero else [],
        "screens": [{"key": "today", "views": total_sessions*3, "sessions": total_sessions}] if not zero else [], "sources": [], "markets": [],
        "regions": [{"region_code": "SP", "sessions": located, "users": min(4, located), "percent": 100}] if located else [],
        "cities": [{"city_name": "São Paulo", "region_code": "SP", "sessions": located, "users": min(4, located)}] if located else [],
        "geo_daily": [], "region_daily": [], "insights": [],
        "funnel": {"visited": total_sessions, "market_opened": total_sessions//2,
                   "ticket_started": total_sessions//4, "submit_clicked": total_sessions//7},
        "abandonment": {"eligible": total_sessions//8, "abandoned_before_choice": total_sessions//20,
                        "abandoned_after_choice": total_sessions//30},
        "authenticated_funnel": {"confirmed_users": min(3, total_sessions//7), "started_users": min(7, total_sessions//4)},
        "retention": {"since": "2026-06-30", "registered": audience, "visitors": deepcopy(audience)},
        "domain_totals": {"signups": 3, "predictions": 4, "participants": 3},
        "last_ingestion": {"completed_at": "2026-10-12T20:00:00Z", "platform": "web",
                           "received": 4, "accepted": 3, "duplicates": 1, "new_session": False},
        "collection_24h": {"events": sum(row["web_sessions"]+row["mobile_sessions"] for row in daily[-2:])*3,
                           "sessions": sum(row["web_sessions"]+row["mobile_sessions"] for row in daily[-2:]),
                           "visitors": 0 if zero else 1, "last_event_at": latest},
        "collection_platforms": [{"platform": key, "events_24h": sum(row[f"{key}_sessions"] for row in daily[-2:])*3,
                                  "last_event_at": "2026-10-12T20:00:00Z" if sum(row[f"{key}_sessions"] for row in daily[-2:]) else "2026-08-01T20:00:00Z" if key == "web" else None}
                                 for key in ("web", "mobile")],
        "geolite_file": {"state": state, "file_size_bytes": 120000, "node_count": 1234,
                         "database_type": "GeoLite2-City", "database_build_at": "2026-10-01T00:00:00Z",
                         "file_modified_at": "2026-10-01T12:00:00Z"},
        "last_geolite_run": {"status": "success", "completed_at": "2026-10-01T12:00:00Z"},
        "coverage": "Dados sintéticos para QA, sem gravação no banco.",
    }


def main():
    output = ROOT / ".runtime/analytics-usability-qa"
    output.mkdir(parents=True, exist_ok=True)
    links = []
    for name, days, state, variant, theme, javascript in (
        ("all-7-light", 7, "missing", "all", "light", True),
        ("all-7-dark", 7, "ready", "all", "dark", True),
        ("web-1-light", 1, "ready", "web", "light", True),
        ("mobile-30-dark", 30, "missing", "mobile", "dark", True),
        ("empty-30-light", 30, "missing", "empty", "light", True),
        ("all-90-light", 90, "ready", "all", "light", True),
        ("no-js", 7, "missing", "all", "light", False),
    ):
        with override("pt-br"):
            html = render_to_string("admin_ops/analytics.html", {
                "report": report_fixture(days, state, variant),
                "region_choices": "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(),
                "filters": {"days": str(days), "platform": "all" if variant == "empty" else variant,
                            "audience": "all", "region": "", "city": ""},
            })
        html = html.replace('<body class="admin-shell">', f'<body class="admin-shell" data-theme="{theme}">')
        html = html.replace('<title>GoTrendLabs Admin | Analytics</title>', '<title>Analytics QA · dados sintéticos</title>')
        html = html.replace('<h1>Analytics</h1>', '<h1>Analytics QA</h1><p>Dados sintéticos, sem gravação no banco. Não representam uso real.</p>')
        html = re.sub(r'<link[^>]+rel="stylesheet"[^>]*>', lambda m: '<style>' +
                      (ROOT / "apps/web" / m[0].split('href="/')[1].split('?')[0]).read_text() + '</style>', html)
        def script(match):
            asset = match[1]
            if not javascript:
                return ""
            return '<script>' + (ROOT / "apps/web" / asset).read_text() + '</script>'
        # Inline asset execution must follow JSON data and rendered chart nodes.
        scripts = []
        for match in re.finditer(r'<script src="/(static/[^?]+)\?[^\"]*" defer></script>', html):
            scripts.append(script(match))
        html = re.sub(r'<script src="/static/[^\"]+" defer></script>', '', html)
        html = html.replace('</body>', ''.join(scripts) + '</body>')
        html = html.replace('src="/static/', 'src="http://localhost:8000/static/')
        (output / f"{name}.html").write_text(html)
        (output / f"{name}-390.html").write_text(f'<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>QA viewport 390px</title><body style="margin:0;background:#f7f4ec"><p>QA · viewport de 390px · dados sintéticos</p><iframe title="Analytics 390px" src="{name}.html" style="width:390px;height:850px;border:1px solid #ded7c8"></iframe></body></html>')
        links.append(f'<li><a href="{name}.html">{name}</a> · <a href="{name}-390.html">390px</a></li>')
    (output / 'index.html').write_text('<!doctype html><html lang="pt-BR"><title>Analytics QA</title><h1>Analytics QA · dados sintéticos</h1><ul>' + ''.join(links) + '</ul></html>')
    print(output)


if __name__ == '__main__':
    main()
