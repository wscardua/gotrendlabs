from django import forms
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_datetime

from apps.web.django.accounts.api_client import AuthAPIError, confirm_email, confirm_password_reset, get_markets, get_session, login_user, logout_user, register_user, request_password_reset, resend_email_confirmation
from apps.web.django.accounts.forms import LoginForm, PasswordResetConfirmForm, PasswordResetRequestForm, RegisterForm
from apps.web.django.accounts.session import USER_KEY, auth_token, clear_auth_session, is_authenticated, safe_redirect_url, store_auth_session
from apps.web.django.core.middleware import ReferralCaptureMiddleware
from apps.web.django.core.domain_client import local_markets


SIGNUP_TICKET_STAKE = 80
REMEMBER_ME_SESSION_AGE = 60 * 60 * 24 * 30


def _display_outcome(label):
    return "NÃO" if label == "NAO" else label


def _market_created_at_score(market):
    parsed = parse_datetime(market.get("created_at") or "")
    return parsed.timestamp() if parsed else 0


def _market_view_score(market):
    return int(market.get("view_count") or 0)


def _popular_signup_market():
    try:
        markets = get_markets()
    except AuthAPIError:
        markets = []
    try:
        local_by_slug = {market["slug"]: market for market in local_markets()}
    except Exception:
        local_by_slug = {}
    combined = {market.get("slug"): market for market in markets if market.get("slug")}
    for slug, market in local_by_slug.items():
        combined[slug] = {**market, **combined.get(slug, {})}
    hydrated = []
    for market in combined.values():
        if market.get("status") in {"draft", "canceled"}:
            continue
        local = local_by_slug.get(market.get("slug"), {})
        merged = {**local, **market}
        if not merged.get("sparkline_series"):
            merged["sparkline_series"] = local.get("sparkline_series", [])
        if not merged.get("options"):
            merged["options"] = local.get("options", [])
        if merged.get("view_count") is None:
            merged["view_count"] = local.get("view_count", 0)
        hydrated.append(merged)
    if not hydrated:
        return None
    market = max(hydrated, key=lambda item: (_market_view_score(item), _market_created_at_score(item)))
    primary_label = market.get("primary_outcome") or (market.get("options") or [{}])[0].get("label", "SIM")
    primary_probability = max(float(market.get("primary_probability_exact") or market.get("primary_probability") or 50), 1)
    return {
        **market,
        "display_primary_outcome": _display_outcome(primary_label),
        "estimated_return_gtl": round(SIGNUP_TICKET_STAKE * (100 / primary_probability)),
        "stake_gtl": SIGNUP_TICKET_STAKE,
    }


def login_view(request):
    if is_authenticated(request):
        return redirect("home")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        credentials = {
            "email": form.cleaned_data["email"],
            "password": form.cleaned_data["password"],
        }
        try:
            response = login_user(credentials)
        except AuthAPIError as exc:
            form.add_error(None, str(exc))
        else:
            store_auth_session(request, response)
            if form.cleaned_data.get("remember_me"):
                request.session.set_expiry(REMEMBER_ME_SESSION_AGE)
            else:
                request.session.set_expiry(None)
            return redirect(safe_redirect_url(request, request.GET.get("next"), reverse("home")))
    return render(request, "accounts/login.html", {"form": form})


def register_view(request):
    if is_authenticated(request):
        return redirect("home")
    referral_code = request.session.get(ReferralCaptureMiddleware.SESSION_KEY, "")
    form = RegisterForm(request.POST or None, initial={"referral_code": referral_code})
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
            request.session.pop(ReferralCaptureMiddleware.SESSION_KEY, None)
            store_auth_session(request, response)
            return redirect("home")
    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "recaptcha_enabled": settings.RECAPTCHA_ENABLED,
            "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
            "signup_market": _popular_signup_market(),
            "referral_code": referral_code,
        },
    )


def password_reset_request_view(request):
    if is_authenticated(request):
        return redirect("home")
    form = PasswordResetRequestForm(request.POST or None)
    reset_url = ""
    message = ""
    if request.method == "POST" and form.is_valid():
        try:
            response = request_password_reset(form.cleaned_data["email"])
        except AuthAPIError as exc:
            form.add_error(None, str(exc))
        else:
            message = response.get("message") or "Se o email estiver cadastrado, enviaremos instruções."
            reset_url = response.get("reset_url") or ""
    return render(request, "accounts/password_reset_request.html", {"form": form, "message": message, "reset_url": reset_url})


def password_reset_confirm_view(request, token):
    if is_authenticated(request):
        return redirect("home")
    form = PasswordResetConfirmForm(request.POST or None)
    success = False
    if request.method == "POST" and form.is_valid():
        try:
            confirm_password_reset(token, form.cleaned_data["password"])
        except AuthAPIError as exc:
            form.add_error(None, str(exc))
        else:
            success = True
    return render(request, "accounts/password_reset_confirm.html", {"form": form, "success": success})


def email_confirm_view(request, token):
    message = ""
    success = False
    try:
        response = confirm_email(token)
    except AuthAPIError as exc:
        message = str(exc)
    else:
        success = True
        message = response.get("message") or "Email confirmado com sucesso."
        token_value = auth_token(request)
        if token_value:
            try:
                session = get_session(token_value)
            except AuthAPIError:
                session = None
            if session:
                request.session[USER_KEY] = session["user"]
    return render(request, "accounts/email_confirm.html", {"success": success, "message": message})


def email_confirmation_resend_view(request):
    token = auth_token(request)
    if not token:
        return redirect("login")
    try:
        response = resend_email_confirmation(token)
    except AuthAPIError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, response.get("message") or "Novo link enviado.")
    return redirect(safe_redirect_url(request, request.GET.get("next"), reverse("home")))


def logout_view(request):
    token = auth_token(request)
    if token:
        try:
            logout_user(token)
        except AuthAPIError:
            pass
    clear_auth_session(request)
    return redirect("home")
