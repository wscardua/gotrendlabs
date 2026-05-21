import json
from decimal import Decimal, ROUND_DOWN
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.utils import timezone


PROBABILITY_QUANT = Decimal("0.0001")


def _decimal_probability(value):
    return Decimal(str(value or 0)).quantize(PROBABILITY_QUANT)


def _display_probability(value):
    return int(_decimal_probability(value).to_integral_value(rounding=ROUND_DOWN))


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


def _market_status_label(status_value):
    return {
        "draft": "Rascunho",
        "scheduled": "Agendado",
        "open": "Aberto",
        "locked": "Fechado",
        "resolved": "Resolvido",
        "canceled": "Cancelado",
    }.get(status_value, status_value)


def _short_close_label(close_at):
    if not close_at:
        return ""
    delta = close_at - timezone.now()
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return "fim"
    days = seconds // 86400
    if days >= 1:
        return f"{days}d"
    return f"{max(1, seconds // 3600)}h"


def _sparkline_paths(points, *, width=220, height=44, pad=4):
    if not points:
        points = [50]
    if len(points) == 1:
        points = [points[0], points[0]]
    step = (width - (pad * 2)) / max(len(points) - 1, 1)
    coords = []
    for index, value in enumerate(points):
        probability = max(Decimal("0"), min(Decimal("100"), _decimal_probability(value)))
        x = pad + (index * step)
        y = Decimal(str(pad)) + ((Decimal("100") - probability) / Decimal("100")) * Decimal(str(height - (pad * 2)))
        coords.append((round(Decimal(str(x)), 2), round(y, 2)))
    path = " ".join(f"{'M' if index == 0 else 'L'} {x:g} {y:g}" for index, (x, y) in enumerate(coords))
    area = f"M {coords[0][0]:g} {height - pad:g} " + " ".join(f"L {x:g} {y:g}" for x, y in coords) + f" L {coords[-1][0]:g} {height - pad:g} Z"
    return {"sparkline_path": path, "sparkline_area_path": area}


def _market_sparklines(market, options):
    if not options:
        fallback = _sparkline_paths([50])
        return {**fallback, "series": []}
    from markets.models import Prediction

    weights = {option["id"]: 10_000 for option in options}
    points_by_option = {option["id"]: [] for option in options}

    def append_points():
        total = sum(weights.values())
        for option in options:
            option_id = option["id"]
            points_by_option[option_id].append((Decimal(weights[option_id]) * Decimal("100") / Decimal(total)).quantize(PROBABILITY_QUANT))

    append_points()
    predictions = (
        Prediction.objects.filter(market=market, status="open")
        .order_by("created_at", "id")
        .values("market_option_id", "weight_at_entry")
    )
    for prediction in predictions:
        option_id = prediction["market_option_id"]
        if option_id not in weights:
            continue
        weights[option_id] += prediction["weight_at_entry"]
        append_points()
    primary = _sparkline_paths(points_by_option[options[0]["id"]])
    series = []
    for option in options:
        series.append(
            {
                "id": option["id"],
                "label": option["label"],
                "path": _sparkline_paths(points_by_option[option["id"]])["sparkline_path"],
            }
        )
    return {**primary, "series": series}


def _local_market_response(market):
    options = [
        {
            "id": option.id,
            "label": option.label,
            "probability": _display_probability(option.probability_exact),
            "probability_exact": float(_decimal_probability(option.probability_exact)),
            "hint": option.hint,
        }
        for option in market.options.all()
    ]
    sparkline = _market_sparklines(market, options)
    options = [
        {**option, "sparkline_path": next((item["path"] for item in sparkline["series"] if item["id"] == option["id"]), "")}
        for option in options
    ]
    return {
        "slug": market.slug,
        "title": market.title,
        "category": market.category.name,
        "subcategory": market.subcategory.name,
        "kind": market.kind,
        "status": market.status,
        "status_label": _market_status_label(market.status),
        "primary_outcome": market.primary_outcome,
        "primary_probability": _display_probability(market.primary_probability_exact),
        "primary_probability_exact": float(_decimal_probability(market.primary_probability_exact)),
        "secondary_probability": _display_probability(market.secondary_probability_exact),
        "secondary_probability_exact": float(_decimal_probability(market.secondary_probability_exact)),
        "volume_oc": _currency_label(market.volume_oc),
        "participants": market.participants,
        "source": market.source,
        "closes_in": _short_close_label(market.close_at) or market.closes_in,
        "close_label": market.close_label or _market_status_label(market.status),
        "thumb": market.thumb,
        "thumb_color": market.thumb_color,
        "image_url": market.image_url,
        "summary": market.summary,
        "resolution_criteria": market.resolution_criteria,
        "close_at": market.close_at.isoformat() if market.close_at else None,
        "close_timezone": market.close_timezone,
        "auto_close_enabled": market.auto_close_enabled,
        "is_featured": market.is_featured,
        "market_like_count": market.likes.count(),
        "view_count": market.view_count,
        "share_count": market.share_count,
        "viewer_has_like": False,
        "created_at": market.created_at.isoformat() if market.created_at else "",
        "sparkline_path": sparkline["sparkline_path"],
        "sparkline_area_path": sparkline["sparkline_area_path"],
        "sparkline_series": sparkline["series"],
        "options": options,
        "comments": [],
    }


def _currency_label(value):
    return str(value or "0 O₵").replace(" OC", " O₵")


def _format_oc_amount(value):
    return f"{int(value or 0):,}".replace(",", ".")


def local_markets(include_canceled=False):
    from markets.models import Market

    excluded_statuses = ["draft"] if include_canceled else ["draft", "canceled"]
    markets = (
        Market.objects.exclude(status__in=excluded_statuses)
        .select_related("category", "subcategory")
        .prefetch_related("options")
        .order_by("display_order", "id")
    )
    return [_local_market_response(market) for market in markets]


def local_market(slug):
    from markets.models import Market

    try:
        market = (
            Market.objects.exclude(status="draft")
            .select_related("category", "subcategory")
            .prefetch_related("options")
            .get(slug=slug)
        )
    except Market.DoesNotExist as exc:
        raise Http404("Mercado nao encontrado") from exc
    return _local_market_response(market)


def local_stats():
    from django.db.models import Sum
    from accounts.models import WalletLedgerEntry
    from markets.models import Market, Prediction

    total_predictions = Prediction.objects.count()
    distributed_oc = (
        WalletLedgerEntry.objects.filter(direction="credit")
        .exclude(user__is_staff=True)
        .exclude(user__is_superuser=True)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    moved_oc = Prediction.objects.aggregate(total=Sum("stake_amount"))["total"] or 0
    return {
        "open_markets": Market.objects.filter(status="open").count(),
        "total_predictions": total_predictions,
        "distributed_oc": _format_oc_amount(distributed_oc),
        "moved_oc": _format_oc_amount(moved_oc),
        "resolution_sla": "pendente",
        "real_money": "R$0",
    }
