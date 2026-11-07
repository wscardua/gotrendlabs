"""Local visual QA using actual templates and test-only data; no API or database writes."""
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.template.loader import render_to_string
from tests.test_performance_web import performance_payload


class PreviewHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/static/"):
            self.path = "/" + parsed.path.removeprefix("/static/")
            return super().do_GET()
        state = parse_qs(parsed.query).get("state", ["data"])[0]
        payload = performance_payload()
        payload["history"][0]["market_title"] = "Uma pergunta extensa para verificar a leitura confortável de resoluções e escolhas em telas pequenas?"
        if state == "empty":
            payload["history"] = []
            payload["progression"] = {"earned_badges_count": 0, "latest_awards": []}
            payload["scorecard"].update(ranking_position=0, strong_category="")
        html = render_to_string("profiles/performance.html", {
            "performance": payload, "performance_error": state == "error", "show_performance_scorecard": True,
            # Fixed fixtures: -6 is 36 px, +4 is 24 px in the presentation scale.
            "reputation_chart": [
                {**item, "bar_height": 24 if item["reputation_delta"] > 0 else 36}
                for item in reversed(payload["history"])
            ] if state != "error" else [],
            "is_guest": False, "viewer": {"name": "Pessoa de teste", "handle": "@teste", "balance_gtl": 100},
        })
        data = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8768), partial(PreviewHandler, directory=ROOT / "apps/web/static"))
    print("Read-only performance QA: http://127.0.0.1:8768", flush=True)
    server.serve_forever()
