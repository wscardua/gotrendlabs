from html.parser import HTMLParser
from pathlib import Path

from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.urls import reverse


class InvitationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.options = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.links.append(attrs["href"])
        if tag == "template":
            self.options.append(attrs["data-market-invite-option"])
        if tag == "img":
            self.images.append(attrs)


class WebGridInvitationTests(SimpleTestCase):
    def test_five_options_use_existing_named_destinations_and_decorative_assets(self):
        html = render_to_string("components/market_grid_invite.html")
        parser = InvitationParser()
        parser.feed(html)
        self.assertEqual(parser.options, ["suggestion", "ranking", "badges", "results", "concepts"])
        self.assertEqual(parser.links, [reverse("suggestion"), reverse("rankings"), reverse("badges"), reverse("home") + "#resolvidos", reverse("concepts")])
        self.assertEqual(len(parser.images), 5)
        for image in parser.images:
            self.assertEqual(image["alt"], "")
            asset = Path(__file__).resolve().parents[1] / "apps/web/static" / image["src"].removeprefix("/static/")
            self.assertTrue(asset.is_file())
            self.assertNotIn("<text", asset.read_text())
        self.assertEqual(html.count('class="market-grid-invite-label"'), 5)
        self.assertNotIn("Publicidade", html)
        self.assertNotIn('>Prever<', html)

    def test_home_has_only_one_invitation_in_main_list_even_when_empty(self):
        html = render_to_string("core/home.html", {"markets": [], "is_guest": True})
        self.assertEqual(html.count('data-market-grid-invite hidden'), 1)
        self.assertEqual(html.count('data-market-invite-grid'), 1)
        self.assertIn('id="resolvidos"', html)
        pending = html.split('data-market-pending open hidden', 1)[1]
        self.assertNotIn('data-market-grid-invite', pending)
        self.assertIn('data-market-empty', html)
