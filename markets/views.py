from django.shortcuts import render

from core.domain_client import get_domain_client


def detail(request, slug):
    market = get_domain_client().market(slug)
    return render(request, "markets/detail.html", {"market": market})


def prediction_preview(request, slug):
    market = get_domain_client().market(slug)
    amount = int(request.POST.get("amount", "80") or 80)
    choice = request.POST.get("choice", market["options"][0]["label"])
    estimated_return = round(amount * (100 / max(market["primary_probability"], 1)))
    return render(
        request,
        "markets/partials/prediction_preview.html",
        {"market": market, "amount": amount, "choice": choice, "estimated_return": estimated_return},
    )
