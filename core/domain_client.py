import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import Http404


class FixtureDomainClient:
    """Read-only client that mimics the future backend-api contract shape."""

    fixture_path = Path(settings.BASE_DIR) / "data" / "fixtures" / "domain.json"

    @classmethod
    @lru_cache(maxsize=1)
    def _payload(cls):
        with cls.fixture_path.open(encoding="utf-8") as fixture:
            return json.load(fixture)

    def viewer(self):
        return self._payload()["viewer"]

    def stats(self):
        return self._payload()["stats"]

    def markets(self):
        return self._payload()["markets"]

    def market(self, slug):
        for market in self.markets():
            if market["slug"] == slug:
                return market
        raise Http404("Mercado nao encontrado")

    def ranking(self):
        return self._payload()["ranking"]

    def ledger(self):
        return self._payload()["ledger"]

    def admin_summary(self):
        return self._payload()["admin"]


def get_domain_client():
    return FixtureDomainClient()
