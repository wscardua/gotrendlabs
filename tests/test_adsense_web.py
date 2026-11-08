from copy import deepcopy
from html.parser import HTMLParser

from django.conf import settings
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_head = False
        self.accounts = []
        self.ads = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'head':
            self.in_head = True
        if tag == 'meta' and attrs.get('name') == 'google-adsense-account':
            self.accounts.append((self.in_head, attrs.get('content')))
        if 'adsbygoogle' in attrs.get('class', '') or 'data-ad-slot' in attrs or 'googlesyndication.com' in attrs.get('src', ''):
            self.ads.append(attrs)

    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False


@override_settings(SECURE_SSL_REDIRECT=False)
class AdSenseWebTests(SimpleTestCase):
    def setUp(self):
        # Reset cached template context processors when mocks are removed.
        self.enterContext(override_settings(TEMPLATES=deepcopy(settings.TEMPLATES)))

    def test_anonymous_ads_txt_exact_response_in_both_environments(self):
        for production in (False, True):
            with self.subTest(production=production), override_settings(PRODUCTION_MODE=production):
                response = self.client.get(reverse('ads-txt'))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'], 'text/plain')
                self.assertEqual(response.content, b'google.com, pub-4771800155732970, DIRECT, f08c47fec0942fa0\n')
                self.assertNotIn('sessionid', response.cookies)

    @patch('apps.web.django.core.middleware.maintenance_enabled', return_value=True)
    def test_ads_txt_remains_public_during_maintenance_without_exempting_other_paths(self, maintenance):
        self.assertEqual(self.client.get('/ads.txt').status_code, 200)
        maintenance.assert_not_called()
        for path in ('/', '/ads.txt/extra'):
            self.assertRedirects(self.client.get(path), '/maintenance/', fetch_redirect_response=False)

    def test_head_and_unsupported_method(self):
        response = self.client.head('/ads.txt', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertEqual(response.content, b'')
        self.assertEqual(self.client.post('/ads.txt').status_code, 405)

    @patch('apps.web.django.core.views.local_markets', return_value=[])
    @patch('apps.web.django.core.views.get_markets', return_value=[])
    @patch('apps.web.django.core.context_processors.session_context', return_value={'is_guest': True})
    @patch('apps.web.django.core.middleware.maintenance_enabled', return_value=False)
    def test_public_pages_render_environment_specific_head_without_ads(self, *_mocks):
        for production in (False, True):
            with override_settings(PRODUCTION_MODE=production):
                for path in ('/', '/concepts/', '/security/', '/use-policy/', '/login/'):
                    with self.subTest(production=production, path=path):
                        response = self.client.get(path, secure=True)
                        self.assertEqual(response.status_code, 200)
                        parser = HeadParser()
                        parser.feed(response.content.decode())
                        self.assertEqual(parser.accounts, [(True, 'ca-pub-4771800155732970')] if production and path != '/login/' else [])
                        self.assertEqual(parser.ads, [])
                        self.assertNotContains(response, 'adsbygoogle')
