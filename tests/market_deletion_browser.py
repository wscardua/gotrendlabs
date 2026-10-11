"""Real confirmation template in desktop/mobile Chrome, without backend mutations."""
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()
from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright, expect

OUT = ROOT / '.runtime/market-deletion-browser'
OUT.mkdir(parents=True, exist_ok=True)
market = {
    'slug': 'mercado-teste', 'title': 'O novo jogo lunar será lançado até dezembro?',
    'status': 'draft', 'editorial_status': 'in_review',
    'editorial_market_id': 7, 'editorial_revision': 4, 'can_delete': True,
}
(OUT / 'confirm.html').write_text(render_to_string('admin_ops/market_delete.html', {
    'market': market, 'csrf_token': 'fixture', 'title': 'Excluir mercado',
}))


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def translate_path(self, path):
        path = path.split('?')[0]
        if path.startswith('/static/'):
            return str(ROOT / 'apps/web/static' / path.removeprefix('/static/'))
        return str(OUT / path.lstrip('/'))


server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        for width in (1440, 390):
            page = browser.new_page(viewport={'width': width, 'height': 900}, java_script_enabled=False)
            page.goto(f'http://127.0.0.1:{server.server_port}/confirm.html')
            expect(page.get_by_role('heading', name='Excluir mercado', exact=True)).to_be_visible()
            expect(page.get_by_role('button', name='Confirmar exclusão')).to_be_visible()
            expect(page.get_by_role('link', name='Voltar sem excluir')).to_be_visible()
            assert page.locator('form').get_attribute('method') == 'post'
            assert page.locator('input[name=expected_revision]').get_attribute('value') == '4'
            assert page.locator('input[name=expected_market_id]').get_attribute('value') == '7'
            assert page.locator('input[name=csrfmiddlewaretoken]').count() == 1
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(OUT / f'confirm-{width}.png'), full_page=True)
            page.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
print('PASS: desktop/mobile confirmation, no JavaScript, revision/CSRF/POST and no overflow')
