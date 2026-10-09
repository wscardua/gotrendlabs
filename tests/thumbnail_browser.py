"""Local browser acceptance with real template/JS and simulated contract responses. No provider."""

import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.template.loader import render_to_string
from apps.web.django.admin_ops.forms import AdminMarketForm
from apps.web.django.admin_ops.views import _market_initial, _market_taxonomy_options
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright, expect

OUT = ROOT / ".runtime/thumbnail-browser"
OUT.mkdir(parents=True, exist_ok=True)
market = {
    "slug": "fixture",
    "status": "draft",
    "title": "O novo jogo lunar será lançado até dezembro?",
    "summary": "Uma missão lunar em um universo de exploração espacial.",
    "category": "Games",
    "subcategory": "Lançamentos",
    "event": "Missão",
    "kind": "binary",
    "image_url": "/fixture/current.png",
    "thumb": "GM",
    "thumb_color": "#136f4a",
    "options": [],
    "editorial_revision": 1,
    "editorial_market_id": 1,
    "editorial_status": "approved",
    "close_at": "2026-12-01T12:00:00Z",
    "close_timezone": "America/Sao_Paulo",
    "auto_close_enabled": True,
    "source": "Fonte oficial",
    "resolution_criteria": "Lançamento oficial",
}
taxonomy = {
    "categories": [
        {
            "name": "Games",
            "subcategories": [{"name": "Lançamentos", "events": [{"name": "Missão"}]}],
        }
    ]
}
taxonomy["categories"].extend(
    [
        {
            "name": "Tecnologia",
            "subcategories": [
                {"name": "Celulares", "events": [{"name": "Apresentação"}]}
            ],
        },
        {
            "name": "Esportes",
            "subcategories": [{"name": "Futebol", "events": [{"name": "Final"}]}],
        },
    ]
)
form = AdminMarketForm(initial=_market_initial(market), taxonomy=taxonomy)
html = render_to_string(
    "admin_ops/market_form.html",
    {
        "title": "Editar/visualizar mercado",
        "mode": "edit",
        "slug": "fixture",
        "form": form,
        "market": market,
        "preview": market,
        "option_rows": [],
        "taxonomy_options": _market_taxonomy_options(taxonomy),
        "csrf_token": "fixture-csrf",
        "market_participants": {"items": []},
    },
)
(OUT / "editor.html").write_text(html)


from apps.web.django.admin_ops.forms import ThumbnailConfigForm, AiConfigForm
from apps.web.django.admin_ops.models import SiteConfig
from apps.api.backend_api.thumbnail_settings import ThumbnailSettings

settings_html = render_to_string(
    "admin_ops/config.html",
    {
        "thumbnail_form": ThumbnailConfigForm(
            initial=ThumbnailSettings().model_dump(), prefix="thumbnail"
        ),
        "ai_form": AiConfigForm(prefix="ai"),
        "site_config": SiteConfig(),
        "csrf_token": "fixture-csrf",
    },
)
(OUT / "config.html").write_text(settings_html)


def fixture(kind):
    image = Image.new("RGB", (1536, 1024), "#173d52")
    draw = ImageDraw.Draw(image)
    if kind == "games":
        draw.ellipse((460, 150, 1060, 750), fill="#b3c8cf")
        draw.ellipse((560, 240, 660, 340), fill="#647f8b")
        draw.polygon([(768, 250), (945, 620), (780, 570), (590, 630)], fill="#f2bd53")
        draw.ellipse((700, 380, 815, 495), fill="#173d52")
    elif kind == "technology":
        draw.rounded_rectangle((520, 150, 1010, 810), radius=70, fill="#d5e7ea")
        draw.rounded_rectangle((555, 195, 975, 735), radius=30, fill="#467e86")
        draw.polygon([(585, 670), (768, 320), (940, 600)], fill="#efa54b")
    else:
        draw.polygon(
            [
                (450, 220),
                (590, 170),
                (720, 220),
                (675, 380),
                (650, 750),
                (490, 750),
                (475, 380),
            ],
            fill="#ec814e",
        )
        draw.polygon(
            [
                (800, 220),
                (940, 170),
                (1070, 220),
                (1025, 380),
                (1000, 750),
                (840, 750),
                (825, 380),
            ],
            fill="#69aeb1",
        )
        draw.ellipse((688, 640, 848, 800), fill="#e9e1c5")
    out = BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/config/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(settings_html.encode())
            return

        if self.path == "/":
            raw = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(raw)
            return
        if self.path.startswith("/static/"):
            path = (
                ROOT
                / "apps/web/static"
                / self.path.split("?")[0].removeprefix("/static/")
            )
            if path.is_file():
                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/javascript"
                    if path.suffix == ".js"
                    else "text/css"
                    if path.suffix == ".css"
                    else "image/svg+xml",
                )
                self.end_headers()
                self.wfile.write(path.read_bytes())
                return
        if self.path.startswith("/fixture/"):
            raw = fixture("games")
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.end_headers()
            self.wfile.write(raw)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *_):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        headless=True,
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    current = {"job": None, "mode": "running", "calls": 0, "category": "games"}

    def route(request):
        if request.request.url.endswith("/preview/"):
            request.fulfill(body=fixture(current["category"]), content_type="image/png")
            return
        if request.request.method == "POST":
            current["calls"] += 1
            body = request.request.post_data_json
            current["job"] = {
                "request_id": body["request_id"],
                "snapshot": {k: v for k, v in body.items() if k != "request_id"},
                "state": "running",
            }
        if current["job"]:
            job = {**current["job"], "state": current["mode"]}
            if job["state"] == "succeeded":
                job.update(
                    candidate_id=job["request_id"],
                    preview_url=f"{base}/admin-ops/markets/fixture/thumbnails/{job['request_id']}/preview/",
                )
            if job["state"] == "failed":
                job["message"] = "Não foi possível gerar. Tente novamente."
            request.fulfill(json=job)
        else:
            request.fulfill(json=None)

    page.route("**/admin-ops/markets/fixture/thumbnails/**", route)

    def reset():
        current.update(job=None, mode="running", calls=0)
        page.goto(base)
        page.wait_for_function("typeof initThumbnailEditor === 'function'")
        page.evaluate(
            "document.querySelector('form[data-market-form]').noValidate=true"
        )

    # Real configuration template: independent form submission and keyboard selection.
    from urllib.parse import parse_qs

    settings_posts = []

    def settings_route(route):
        settings_posts.append(parse_qs(route.request.post_data))
        route.fulfill(
            status=200,
            body="Configurações de thumbnails atualizadas.",
            content_type="text/html; charset=utf-8",
        )

    page.route("**/admin-ops/config/", settings_route)
    page.goto(base + "/config/")
    panel = page.locator('[aria-labelledby="thumbnail-config-title"]')
    panel.scroll_into_view_if_needed()
    model = page.locator('[name="thumbnail-thumbnail_model"]')
    model.select_option("stability.stable-image-ultra-v1:1")
    expect(model).to_have_value("stability.stable-image-ultra-v1:1")
    assert page.locator('[name="ai-ai_model"]').input_value() == "gpt-5.4-mini"
    panel.screenshot(path=str(OUT / "config-thumbnails.png"))
    page.set_viewport_size({"width": 390, "height": 844})
    panel.screenshot(path=str(OUT / "config-thumbnails-mobile.png"))
    page.set_viewport_size({"width": 1440, "height": 1100})
    button = page.get_by_role("button", name="Salvar thumbnails", exact=True)
    button.focus()
    button.press("Enter")
    expect(
        page.get_by_text("Configurações de thumbnails atualizadas.", exact=True)
    ).to_be_visible()
    assert settings_posts[0]["action"] == ["thumbnail_settings"]
    assert settings_posts[0]["thumbnail-thumbnail_model"] == [
        "stability.stable-image-ultra-v1:1"
    ]
    assert not any(
        key.startswith("ai-") or key.startswith("email-") for key in settings_posts[0]
    )

    generate = page.locator("[data-thumbnail-generate]")
    status = page.locator("[data-thumbnail-status]")
    origin = page.locator("[name=thumbnail_origin]")
    undo = page.locator("[data-thumbnail-undo]")
    thumb = page.locator("[data-preview-thumb] img")
    editor = page.locator("[data-market-form]")
    reset()
    page.screenshot(path=str(OUT / "editor-desktop.png"), full_page=True)
    expect(page.locator(".market-editor-help")).not_to_have_attribute("open", "")
    for width in (1440, 1100, 390):
        page.set_viewport_size({"width": width, "height": 1000})
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        ), f"Editor overflows at {width}px"
        page.screenshot(path=str(OUT / f"editor-{width}.png"), full_page=True)
    page.locator("[data-theme-toggle]").click()
    page.screenshot(path=str(OUT / "editor-dark-mobile.png"), full_page=True)
    page.locator("[data-theme-toggle]").click()
    page.set_viewport_size({"width": 1440, "height": 1100})
    before = thumb.get_attribute("src")
    generate.focus()
    generate.press("Enter")
    expect(generate).to_be_disabled()
    expect(generate).to_have_text("Gerando…")
    expect(page.locator("[data-thumbnail-progress]")).to_be_visible()
    expect(page.locator("[data-thumbnail-progress]")).to_contain_text("Aguarde")
    expect(page.locator("[data-thumbnail-progress]")).to_contain_text("alguns minutos")
    expect(page.locator("[data-thumbnail-progress]")).to_have_attribute("role", "status")
    expect(page.locator("[name=description]" if page.locator("[data-ai-badge-editor]").count() else "[name=summary]")).to_be_enabled()
    expect(page.locator("[data-thumbnail-progress]")).to_contain_text("Gerando thumbnail…")
    page.locator("[name=source]").fill("Fonte ainda em edição")
    expect(thumb).to_have_attribute("src", before)
    page.screenshot(path=str(OUT / "loading.png"), full_page=True)
    current["mode"] = "succeeded"
    expect(origin).to_have_value("generated", timeout=5000)
    expect(page.locator("[data-thumbnail-progress]")).to_be_hidden()
    expect(generate).to_have_text("Gerar outra")
    assert page.locator("[name=source]").input_value() == "Fonte ainda em edição"
    first = page.locator("[name=thumbnail_candidate_id]").input_value()
    page.screenshot(path=str(OUT / "success.png"), full_page=True)
    page.locator("[name=title]").fill("Pergunta alterada enquanto reviso")
    expect(page.locator("[data-thumbnail-stale]")).to_be_visible()
    current["mode"] = "running"
    generate.click()
    second = current["job"]["request_id"]
    assert second != first
    current["mode"] = "succeeded"
    expect(page.locator("[name=thumbnail_candidate_id]")).to_have_value(
        second, timeout=5000
    )
    undo.click()
    expect(page.locator("[name=thumbnail_candidate_id]")).to_have_value(first)
    # Manual file, generate, undo returns the same file. Late result preserves later upload.
    reset()
    page.locator("[name=thumbnail_file]").set_input_files(
        {"name": "manual.png", "mimeType": "image/png", "buffer": fixture("technology")}
    )
    expect(origin).to_have_value("upload")
    generate.click()
    current["mode"] = "succeeded"
    expect(origin).to_have_value("generated", timeout=5000)
    assert (
        page.locator("[name=thumbnail_file]").evaluate("(input)=>input.files.length")
        == 0
    )
    undo.click()
    expect(origin).to_have_value("upload")
    assert (
        page.locator("[name=thumbnail_file]").evaluate("(input)=>input.files[0].name")
        == "manual.png"
    )
    current["mode"] = "running"
    generate.click()
    page.locator("[name=thumbnail_file]").set_input_files(
        {"name": "later.png", "mimeType": "image/png", "buffer": fixture("sports")}
    )
    current["mode"] = "succeeded"
    expect(generate).to_be_enabled(timeout=5000)
    expect(origin).to_have_value("upload")
    expect(status).to_contain_text("manual")
    # Failure retains image, editable context, and retry.
    reset()
    before = thumb.get_attribute("src")
    generate.click()
    current["mode"] = "failed"
    expect(generate).to_be_enabled(timeout=5000)
    expect(status).to_contain_text("Não foi possível")
    expect(thumb).to_have_attribute("src", before)
    page.screenshot(path=str(OUT / "error.png"), full_page=True)
    # Submit choices inline. Capture actual submit while keeping page for late-result proof.
    reset()
    generate.click()
    page.evaluate(
        "document.querySelector('[data-market-form]').addEventListener('submit', e=>{ if(!e.defaultPrevented){ e.preventDefault(); window.acceptedSubmit=(window.acceptedSubmit||0)+1; } });"
    )
    page.locator("button[name=action][value=save]").click()
    expect(page.locator("[data-thumbnail-submit]")).to_be_visible()
    page.locator("[data-thumbnail-continue]").click()
    assert page.evaluate("window.acceptedSubmit") == 1
    current["mode"] = "succeeded"
    page.wait_for_timeout(1800)
    expect(origin).to_have_value("current")
    # Native validation can block Continue without pretending the page was submitted.
    reset()
    page.evaluate("document.querySelector('[data-market-form]').noValidate=false")
    assert editor.evaluate("form=>form.checkValidity()")
    page.evaluate(
        "document.querySelector('[data-market-form]').addEventListener('submit', e=>{ if(!e.defaultPrevented){ e.preventDefault(); window.acceptedSubmit=(window.acceptedSubmit||0)+1; } });"
    )
    generate.click()
    page.locator("button[name=action][value=save]").click()
    expect(page.locator("[data-thumbnail-submit]")).to_be_visible()
    page.locator("[name=title]").fill("")
    page.locator("[data-thumbnail-continue]").click()
    expect(page.locator("[data-thumbnail-submit]")).to_be_visible()
    assert page.evaluate("window.acceptedSubmit||0") == 0
    current["mode"] = "succeeded"
    expect(origin).to_have_value("generated", timeout=5000)
    expect(generate).to_be_enabled()
    page.locator("[name=title]").fill("Pergunta corrigida depois da validação?")
    page.locator("button[name=action][value=save]").click()
    assert page.evaluate("window.acceptedSubmit") == 1

    # After fixing a required field while still generating, Continue submits once.
    reset()
    page.evaluate("document.querySelector('[data-market-form]').noValidate=false")
    page.evaluate(
        "document.querySelector('[data-market-form]').addEventListener('submit', e=>{ if(!e.defaultPrevented){ e.preventDefault(); window.acceptedSubmit=(window.acceptedSubmit||0)+1; } });"
    )
    generate.click()
    page.locator("button[name=action][value=save]").click()
    page.locator("[name=source]").fill("")
    page.locator("[data-thumbnail-continue]").click()
    assert page.evaluate("window.acceptedSubmit||0") == 0
    page.locator("[name=source]").fill("Fonte corrigida")
    page.locator("[data-thumbnail-continue]").click()
    assert page.evaluate("window.acceptedSubmit") == 1
    current["mode"] = "succeeded"
    page.wait_for_timeout(1800)
    expect(origin).to_have_value("current")
    reset()
    generate.click()
    page.evaluate(
        "document.querySelector('[data-market-form]').addEventListener('submit', e=>{ if(!e.defaultPrevented){ e.preventDefault(); window.acceptedSubmit=(window.acceptedSubmit||0)+1; } });"
    )
    page.locator("button[name=action][value=save]").click()
    page.locator("[data-thumbnail-wait]").click()
    current["mode"] = "succeeded"
    expect(origin).to_have_value("generated", timeout=5000)
    assert page.evaluate("window.acceptedSubmit") == 1
    # The existing publication form also gets the inline generation decision.
    reset()
    generate.click()
    page.evaluate(
        "document.querySelector('[data-editorial-publish]').addEventListener('submit', e=>{ if(!e.defaultPrevented){ e.preventDefault(); window.acceptedPublication=(window.acceptedPublication||0)+1; } });"
    )
    page.locator("[data-editorial-publish] button").click()
    expect(page.locator("[data-thumbnail-submit]")).to_be_visible()
    page.locator("[data-thumbnail-continue]").click()
    assert page.evaluate("window.acceptedPublication") == 1
    current["mode"] = "succeeded"
    page.wait_for_timeout(1800)
    expect(origin).to_have_value("current")
    reset()
    generate.click()
    page.locator("[name=title]").fill("Uma pergunta alterada durante a geração?")
    current["mode"] = "succeeded"
    expect(origin).to_have_value("generated", timeout=5000)
    expect(page.locator("[data-thumbnail-stale]")).to_be_visible()
    assert current["calls"] == 1
    page.locator("[data-editorial-publish] button").click()
    expect(status).to_contain_text("revise a versão")
    # Capture real crop at desktop/mobile card sizes for three categories. Fixtures are not model quality evidence.
    for category in ("games", "technology", "sports"):
        reset()
        current["category"] = category
        if category == "technology":
            page.locator("[name=category]").select_option(label="Tecnologia")
            page.locator("[name=subcategory]").select_option(label="Celulares")
            page.locator("[name=event]").select_option(label="Apresentação")
            page.locator("[name=title]").fill(
                "O novo celular será apresentado neste ano?"
            )
            page.locator("[name=summary]").fill(
                "Uma nova geração de celulares está prevista para apresentação pública."
            )
        elif category == "sports":
            page.locator("[name=category]").select_option(label="Esportes")
            page.locator("[name=subcategory]").select_option(label="Futebol")
            page.locator("[name=event]").select_option(label="Final")
            page.locator("[name=title]").fill(
                "A final entre Aurora e Atlântico terá prorrogação?"
            )
            page.locator("[name=summary]").fill(
                "Dois rivais chegam à final sem favorito definido."
            )
        generate.click()
        current["mode"] = "succeeded"
        expect(origin).to_have_value("generated", timeout=5000)
        page.locator("[data-market-preview]").screenshot(
            path=str(OUT / f"card-{category}.png")
        )
        page.set_viewport_size({"width": 390, "height": 844})
        page.locator("[data-market-preview]").screenshot(
            path=str(OUT / f"card-mobile-{category}.png")
        )
        page.set_viewport_size({"width": 1440, "height": 1100})
    # Manual choice during decode cancels a queued save; the next generation never saves.
    reset()
    page.evaluate("document.querySelector('form[data-market-form]').addEventListener('submit',e=>{if(!e.defaultPrevented){e.preventDefault();window.reviewSaves=(window.reviewSaves||0)+1;}})")
    page.evaluate("window.decodeWaiters=[];window.holdDecode=true;const originalDecode=Image.prototype.decode;Image.prototype.decode=function(){return originalDecode.call(this).then(()=>window.holdDecode?new Promise(resolve=>window.decodeWaiters.push(resolve)):undefined);};void 0;")
    generate.click()
    current["mode"] = "succeeded"
    page.wait_for_function("window.decodeWaiters.length === 1")
    page.locator("[name=thumbnail_file]").set_input_files({"name":"manual.png","mimeType":"image/png","buffer":fixture(current["category"])})
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
    assert not errors, errors
    browser.close()
server.shutdown()
print(
    "Browser acceptance passed: configuration model/independent form/keyboard; loading/success/error; context, regeneration, undo/manual, late upload, submit continue/wait with native validation recovery, 3 category crops, desktop/mobile. No provider calls."
)
