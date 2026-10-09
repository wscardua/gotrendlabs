"""Real badge template/CSS/JS, simulated HTTP only. Never invokes a model."""

import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.template.loader import render_to_string
from apps.web.django.admin_ops.forms import AdminBadgeForm
from apps.web.django.admin_ops.views import _market_taxonomy_options
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright, expect

OUT = ROOT / ".runtime/badge-browser"
OUT.mkdir(parents=True, exist_ok=True)
editor = str(uuid4())
badge = {
    "code": "first-resolution",
    "name": "Primeira resolução",
    "description": "Participou de uma previsão resolvida.",
    "rule_description": "Uma previsão concluída.",
    "badge_type": "global",
    "rule_type": "resolved_predictions_count",
    "threshold_value": 1,
    "is_active": True,
    "rule_active": True,
    "image_url": "/fixture/current.png",
    "image_dark_url": "/fixture/dark.png",
    "requirements": [],
}
form = AdminBadgeForm(
    initial={**badge, "badge_image_editor_id": editor, "badge_image_origin": "current"},
    taxonomy={"categories": []},
)
html = render_to_string(
    "admin_ops/badge_form.html",
    {
        "title": "Editar badge",
        "mode": "edit",
        "badge": badge,
        "form": form,
        "badge_editor_id": editor,
        "taxonomy_options": _market_taxonomy_options({"categories": []}),
        "csrf_token": "fixture-csrf",
    },
)
(OUT / "editor.html").write_text(html)


def image(theme="light"):
    im = Image.new("RGB", (512, 512), "#102d23" if theme == "dark" else "#eee6cf")
    d = ImageDraw.Draw(im)
    d.ellipse((70, 70, 442, 442), fill="#136f4a", outline="#c8a645", width=15)
    d.line((155, 270, 230, 340, 365, 180), fill="#eee6cf", width=28)
    out = BytesIO()
    im.save(out, "PNG")
    return out.getvalue()


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            raw = html.encode()
            mime = "text/html"
        elif path.startswith("/fixture/"):
            raw = image()
            mime = "image/png"
        elif path.startswith("/static/"):
            file = ROOT / "apps/web/static" / path.removeprefix("/static/")
            if not file.is_file():
                self.send_error(404)
                return
            raw = file.read_bytes()
            mime = (
                "text/javascript"
                if file.suffix == ".js"
                else "text/css"
                if file.suffix == ".css"
                else "image/svg+xml"
            )
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        current = {"job": None, "mode": "running", "calls": [], "fail": False}

        def route(r):
            if "/preview/" in r.request.url:
                if current.get("dark_fail") and "theme=dark" in r.request.url:
                    r.fulfill(status=503, body="unavailable")
                else:
                    r.fulfill(body=image("dark" if "theme=dark" in r.request.url else "light"), content_type="image/png")
                return
            if r.request.method == "POST":
                body = r.request.post_data_json
                current["calls"].append(body)
                current["job"] = {
                    "request_id": body["request_id"],
                    "snapshot": {
                        k: v
                        for k, v in body.items()
                        if k not in ("request_id", "badge_code")
                    },
                }
            job = current["job"]
            if job:
                job = {**job, "state": current["mode"]}
                if job["state"] == "succeeded":
                    job.update(
                        candidate_id=job["request_id"],
                        preview_url=base
                        + f"/admin-ops/badge-images/{editor}/{job['request_id']}/preview/",
                    )
                    job["preview_dark_url"] = job["preview_url"] + "?theme=dark"
                if job["state"] == "failed":
                    job["message"] = "Não foi possível gerar. Tente novamente."
            r.fulfill(json=job)

        page.route("**/admin-ops/badge-images/**", route)

        def reset():
            current.update(job=None, mode="running", calls=[], dark_fail=False)
            page.goto(base)
            page.wait_for_timeout(150)

        generate = page.locator("[data-thumbnail-generate]")
        origin = page.locator("[name=badge_image_origin]")
        light = page.locator("[data-preview-badge-image-light]")
        dark = page.locator("[data-preview-badge-image-dark]")

        def complete():
            current["mode"] = "succeeded"
            expect(origin).to_have_value("generated", timeout=6000)
            expect(page.locator("[data-thumbnail-progress]")).to_be_hidden()

        reset()
        page.locator("[name=name]").fill("Título editado ainda não salvo")
        generate.focus()
        page.keyboard.press("Enter")
        expect(generate).to_be_disabled()
        expect(generate).to_have_text("Gerando…")
        expect(page.locator("[data-thumbnail-progress]")).to_be_visible()
        expect(page.locator("[data-thumbnail-progress]")).to_contain_text("Aguarde")
        expect(page.locator("[data-thumbnail-progress]")).to_contain_text("alguns minutos")
        expect(page.locator("[data-thumbnail-progress]")).to_have_attribute("role", "status")
        expect(page.locator("[name=description]" if page.locator("[data-ai-badge-editor]").count() else "[name=summary]")).to_be_enabled()
        expect(light).to_have_attribute("src", "/fixture/current.png")
        assert current["calls"][0]["name"] == "Título editado ainda não salvo"
        assert current["calls"][0]["badge_code"] == badge["code"]
        page.screenshot(path=str(OUT / "loading.png"), full_page=True)
        complete()
        expect(light).to_be_visible()
        expect(dark).to_have_attribute("src", current["job"] and light.get_attribute("src") + "?theme=dark")
        page.evaluate("document.body.dataset.theme='dark'")
        expect(dark).to_be_visible()
        expect(light).to_be_hidden()
        page.locator("[name=description]").fill("Descrição alterada depois")
        expect(page.locator("[data-thumbnail-stale]")).to_be_visible()
        assert len(current["calls"]) == 1
        page.screenshot(path=str(OUT / "generated-dark.png"), full_page=True)
        first = current["calls"][0]["request_id"]
        generate.click()
        expect(page.locator("[name=badge_image_candidate_id]")).not_to_have_value(first, timeout=6000)
        expect(generate).to_be_enabled()
        expect(origin).to_have_value("generated", timeout=6000)
        assert len(current["calls"]) == 2 and first != current["calls"][1]["request_id"]
        # Reload an in-progress editor: status resumes, no extra generation request.
        reset()
        generate.click()
        page.reload()
        expect(generate).to_be_disabled()
        expect(page.locator("[data-thumbnail-progress]")).to_be_visible()
        assert len(current["calls"]) == 1
        complete()
        assert len(current["calls"]) == 1
        # Restore an upload pair after generation; no old upload can override selection.
        reset()
        page.locator("[name=badge_image]").set_input_files(
            {"name": "light.png", "mimeType": "image/png", "buffer": image()}
        )
        page.locator("[name=badge_dark_image]").set_input_files(
            {"name": "dark.png", "mimeType": "image/png", "buffer": image()}
        )
        generate.click()
        complete()
        assert page.locator("[name=badge_image]").evaluate("e=>e.files.length") == 0
        assert (
            page.locator("[name=badge_dark_image]").evaluate("e=>e.files.length") == 0
        )
        page.locator("[data-thumbnail-undo]").click()
        expect(origin).to_have_value("upload")
        assert (
            page.locator("[name=badge_image]").evaluate("e=>e.files[0].name")
            == "light.png"
        )
        assert (
            page.locator("[name=badge_dark_image]").evaluate("e=>e.files[0].name")
            == "dark.png"
        )
        # A late image must not replace a newer manual dark upload.
        reset()
        generate.click()
        page.locator("[name=badge_dark_image]").set_input_files(
            {"name": "manual.png", "mimeType": "image/png", "buffer": image()}
        )
        expect(page.locator("[data-thumbnail-progress]")).to_be_visible()
        current["mode"] = "succeeded"
        page.wait_for_timeout(2000)
        expect(origin).to_have_value("upload")
        expect(page.locator("[data-thumbnail-progress]")).to_be_hidden()
        # Failure preserves previous image and allows retry.
        reset()
        generate.click()
        current["mode"] = "failed"
        expect(generate).to_be_enabled(timeout=6000)
        expect(page.locator("[data-thumbnail-progress]")).to_be_hidden()
        expect(light).to_have_attribute("src", "/fixture/current.png")
        expect(page.locator("[data-thumbnail-status]")).to_contain_text(
            "Não foi possível"
        )
        # A missing/unavailable dark preview must preserve the complete previous pair.
        reset()
        current["dark_fail"] = True
        generate.click()
        current["mode"] = "succeeded"
        expect(page.locator("[data-thumbnail-status]")).to_have_attribute("role", "alert", timeout=6000)
        expect(origin).to_have_value("current")
        expect(light).to_have_attribute("src", "/fixture/current.png")
        expect(dark).to_have_attribute("src", "/fixture/dark.png")
        # Native validation does not stop polling or discard the pending decision.
        reset()
        page.evaluate(
            "document.querySelector('[data-badge-form]').addEventListener('submit',e=>{if(!e.defaultPrevented){e.preventDefault();window.accepted=(window.accepted||0)+1;}})"
        )
        generate.click()
        page.locator("button[value=save]").click()
        expect(page.locator("[data-thumbnail-submit]")).to_be_visible()
        page.locator("[name=name]").fill("")
        page.locator("[data-thumbnail-continue]").click()
        assert page.evaluate("window.accepted||0") == 0
        complete()
        page.locator("[name=name]").fill("Nome corrigido")
        page.locator("button[value=save]").click()
        assert page.evaluate("window.accepted") == 1
        # Continue saves current selection; late result is ignored.
        reset()
        page.evaluate(
            "document.querySelector('[data-badge-form]').addEventListener('submit',e=>{if(!e.defaultPrevented){e.preventDefault();window.accepted=(window.accepted||0)+1;}})"
        )
        generate.click()
        page.locator("button[value=save]").click()
        page.locator("[data-thumbnail-continue]").click()
        assert page.evaluate("window.accepted") == 1
        current["mode"] = "succeeded"
        page.wait_for_timeout(2000)
        expect(origin).to_have_value("current")
        reset()
        page.evaluate(
            "document.querySelector('[data-badge-form]').addEventListener('submit',e=>{if(!e.defaultPrevented){e.preventDefault();window.accepted=(window.accepted||0)+1;}})"
        )
        generate.click()
        page.locator("button[value=save]").click()
        page.locator("[data-thumbnail-wait]").click()
        complete()
        assert page.evaluate("window.accepted") == 1
        # Manual choice during decode cancels a queued save; the next generation never saves.
        reset()
        page.evaluate("document.querySelector('form[data-badge-form]').addEventListener('submit',e=>{if(!e.defaultPrevented){e.preventDefault();window.reviewSaves=(window.reviewSaves||0)+1;}})")
        page.evaluate("window.decodeWaiters=[];window.holdDecode=true;const originalDecode=Image.prototype.decode;Image.prototype.decode=function(){return originalDecode.call(this).then(()=>window.holdDecode?new Promise(resolve=>window.decodeWaiters.push(resolve)):undefined);};void 0;")
        generate.click()
        current["mode"] = "succeeded"
        page.wait_for_function("window.decodeWaiters.length === 2")
        page.locator("[name=badge_dark_image]").set_input_files({"name":"manual.png","mimeType":"image/png","buffer":image()})
        page.locator("button[value=save]").click()
        page.locator("[data-thumbnail-wait]").click()
        page.evaluate("window.holdDecode=false;window.decodeWaiters.forEach(resolve=>resolve())")
        expect(generate).to_be_enabled()
        expect(origin).to_have_value("upload")
        expect(page.locator("[data-thumbnail-status]")).to_contain_text("Clique em Salvar")
        assert page.evaluate("window.reviewSaves||0") == 0
        generate.click()
        expect(origin).to_have_value("generated", timeout=6000)
        assert page.evaluate("window.reviewSaves||0") == 0
        page.locator("button[value=save]").click()
        assert page.evaluate("window.reviewSaves") == 1
        for width in (1440, 390):
            reset()
            page.set_viewport_size({"width": width, "height": 1000})
            assert page.evaluate("document.documentElement.scrollWidth") <= width
            page.screenshot(path=str(OUT / f"editor-{width}.png"), full_page=True)
        assert not errors, errors
        browser.close()
finally:
    server.shutdown()
print(
    "Badge browser passed: current context, keyboard, loading/error, generation/regeneration, themes, upload pair/undo, late manual response, native validation, continue/wait. No provider calls."
)
