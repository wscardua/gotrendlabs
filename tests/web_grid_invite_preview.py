"""Read-only local acceptance server: actual Django templates/assets, synthetic markets, no DB/API.

Run with the existing venv: python tests/web_grid_invite_preview.py
Fixtures are deliberately test-only and never persisted or used by the product.
"""
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.template.loader import render_to_string


def preview(count=5):
    markets = []
    for index in range(count + 3):
        status = "open" if index < count else ("locked" if index < count + 2 else "sealed")
        markets.append({
            "slug": f"acceptance-{index}", "status": status,
            "status_label": {"open": "Aberto", "locked": "Em apuração", "sealed": "Concluído"}[status],
            "title": ["Uma nova missão chegará à Lua até dezembro?", "O próximo encontro terá anúncio oficial?", "O festival divulgará sua programação neste mês?"][index % 3],
            "category": "Tecnologia", "subcategory": "Ciência", "event": "Aceite local",
            "thumb": "GT", "thumb_color": "#136f4a", "primary_outcome": "SIM", "primary_probability": 58,
            "closes_in": "3 semanas", "created_at": "2026-10-01T12:00:00Z", "close_at": "2026-12-01T12:00:00Z",
            "view_count": count - index, "options": [{"label": "SIM", "probability": 58, "probability_exact": 58}, {"label": "NAO", "probability": 42, "probability_exact": 42}],
        })
    return render_to_string("core/home.html", {"markets": markets, "is_guest": True, "csrf_token": "local-acceptance-token"})


class PreviewHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/static/"):
            self.path = "/" + parsed.path.removeprefix("/static/")
            return super().do_GET()
        if parsed.path in {"/", "/fragment", "/categories/"}:
            count = int(parse_qs(parsed.query).get("count", [5])[0])
            html = (render_to_string("core/categories.html", {"markets": [], "is_guest": True})
                    if parsed.path == "/categories/" else preview(count))
            if parsed.path == "/fragment":
                html = html[html.index('<section class="home-market-board"'):html.rindex('</section>') + len('</section>')]
            data = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_error(404)

    def log_message(self, *_args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8767), partial(PreviewHandler, directory=ROOT / "apps/web/static"))
    print("Read-only web acceptance: http://127.0.0.1:8767", flush=True)
    server.serve_forever()
