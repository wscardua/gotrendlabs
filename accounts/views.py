from django import forms
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_datetime

from accounts.api_client import AuthAPIError, get_markets, login_user, logout_user, register_user
from accounts.forms import LoginForm, RegisterForm
from accounts.session import auth_token, clear_auth_session, is_authenticated, store_auth_session
from core.domain_client import local_markets


SIGNUP_TICKET_STAKE = 80


def _display_outcome(label):
    return "NÃO" if label == "NAO" else label


def _market_created_at_score(market):
    parsed = parse_datetime(market.get("created_at") or "")
    return parsed.timestamp() if parsed else 0


def _liked_signup_market():
    try:
        markets = get_markets()
    except AuthAPIError:
        markets = local_markets()
    try:
        local_by_slug = {market["slug"]: market for market in local_markets()}
    except Exception:
        local_by_slug = {}
    hydrated = []
    for market in markets:
        if market.get("status") == "canceled":
            continue
        local = local_by_slug.get(market.get("slug"), {})
        merged = {**local, **market}
        if not merged.get("sparkline_series"):
            merged["sparkline_series"] = local.get("sparkline_series", [])
        if not merged.get("options"):
            merged["options"] = local.get("options", [])
        if "market_like_count" not in merged:
            merged["market_like_count"] = local.get("market_like_count", 0)
        hydrated.append(merged)
    if not hydrated:
        return None
    if any(int(market.get("market_like_count") or 0) > 0 for market in hydrated):
        market = max(hydrated, key=lambda item: int(item.get("market_like_count") or 0))
    else:
        market = max(hydrated, key=_market_created_at_score)
    primary_label = market.get("primary_outcome") or (market.get("options") or [{}])[0].get("label", "SIM")
    primary_probability = max(float(market.get("primary_probability_exact") or market.get("primary_probability") or 50), 1)
    return {
        **market,
        "display_primary_outcome": _display_outcome(primary_label),
        "estimated_return_oc": round(SIGNUP_TICKET_STAKE * (100 / primary_probability)),
        "stake_oc": SIGNUP_TICKET_STAKE,
    }


def login_view(request):
    if is_authenticated(request):
        return redirect("home")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            response = login_user(form.cleaned_data)
        except AuthAPIError as exc:
            form.add_error(None, str(exc))
        else:
            store_auth_session(request, response)
            return redirect(request.GET.get("next") or reverse("home"))
    return render(request, "accounts/login.html", {"form": form})


def register_view(request):
    if is_authenticated(request):
        return redirect("home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        payload = form.cleaned_data.copy()
        payload["recaptcha_token"] = request.POST.get("g-recaptcha-response", "")
        try:
            response = register_user(payload)
        except AuthAPIError as exc:
            if exc.status_code == 409:
                form.add_error(None, "Email já está em uso.")
            else:
                form.add_error(None, str(exc))
        except forms.ValidationError as exc:
            form.add_error(None, exc)
        else:
            store_auth_session(request, response)
            return redirect("home")
    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "recaptcha_enabled": settings.RECAPTCHA_ENABLED,
            "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
            "signup_market": _liked_signup_market(),
        },
    )


def logout_view(request):
    token = auth_token(request)
    if token:
        try:
            logout_user(token)
        except AuthAPIError:
            pass
    clear_auth_session(request)
    return redirect("home")
