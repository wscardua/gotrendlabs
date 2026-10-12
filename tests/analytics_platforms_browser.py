"""Browser acceptance of the real analytics template/assets with synthetic report data."""

import os
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright


def main():
    output = ROOT / ".runtime/analytics-platform-browser"
    output.mkdir(parents=True, exist_ok=True)
    platforms = [
        {"platform": "web", "sessions": 28, "visitors": 20, "users": 12,
         "views": 96, "session_share": 70.0},
        {"platform": "mobile", "sessions": 12, "visitors": 9, "users": 7,
         "views": 45, "session_share": 30.0},
    ]
    daily = [{"day": (date(2026, 10, 5) + timedelta(days=index)).isoformat(),
              "web_sessions": web, "mobile_sessions": mobile}
             for index, (web, mobile) in enumerate(
                 [(0, 0), (4, 1), (7, 3), (2, 2), (5, 1), (8, 4), (3, 0), (1, 1)])]
    styles = (ROOT / "apps/web/static/css/gotrendlabs.css").read_text()
    styles += (ROOT / "apps/web/static/css/analytics.css").read_text()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=os.environ.get(
            "CHROME_BIN", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        for variant in ("all", "mobile", "empty"):
            selected = platforms if variant != "mobile" else [platforms[1]]
            series = daily
            if variant == "empty":
                selected = [dict(row, sessions=0, visitors=0, users=0, views=0, session_share=None)
                            for row in platforms]
                series = [dict(row, web_sessions=0, mobile_sessions=0) for row in daily]
            fragment = render_to_string("admin_ops/analytics_platforms.html", {
                "report": {"platforms": selected, "platform_daily": series},
                "filters": {"platform": "all" if variant == "empty" else variant},
            })
            html = ('<!doctype html><html lang="pt-BR"><meta name="viewport" '
                    'content="width=device-width,initial-scale=1"><style>' + styles +
                    '</style><main class="shell analytics-page">' + fragment + '</main></html>')
            for width in (1280, 390):
                page.set_viewport_size({"width": width, "height": 1000})
                page.set_content(html)
                assert page.locator(".analytics-platform-daily").evaluate("e => e.open")
                assert page.locator("[data-platform-chart]").is_hidden()
                page.add_script_tag(path=str(ROOT / "apps/web/static/js/analytics-platforms.js"))
                assert page.locator("[data-platform-chart]").is_visible()
                assert page.locator("polyline").count() == len(selected)
                assert page.locator("[data-platform]").count() == len(selected)
                assert not page.locator("polyline").evaluate_all(
                    "lines => lines.some(l => /NaN|Infinity/.test(l.getAttribute('points')))")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.locator(".analytics-platform-daily summary").focus()
                page.keyboard.press("Enter")
                assert page.locator(".analytics-platform-daily").evaluate("e => e.open")
                assert page.locator("tbody tr").count() == len(daily)
                page.screenshot(path=str(output / f"{variant}-{width}.png"), full_page=True)
        assert not errors, errors
        browser.close()
    print("PASS: desktop/mobile, both/single/empty platforms, no-JS table, keyboard and graph.")


if __name__ == "__main__":
    main()
