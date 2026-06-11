from django import forms
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_datetime
import secrets

from apps.web.django.accounts.api_client import AuthAPIError, confirm_email, confirm_password_reset, get_markets, get_session, login_user, logout_user, register_user, request_password_reset, resend_email_confirmation, social_auth_callback, social_auth_complete_email, social_auth_start
from apps.web.django.accounts.forms import LoginForm, PasswordResetConfirmForm, PasswordResetRequestForm, RegisterForm, SocialEmailForm
from apps.web.django.accounts.session import USER_KEY, auth_token, clear_auth_session, is_authenticated, safe_redirect_url, store_auth_session
from apps.web.django.core.middleware import ReferralCaptureMiddleware
from apps.web.django.core.domain_client import local_markets


SIGNUP_TICKET_STAKE = 80
REMEMBER_ME_SESSION_AGE = 60 * 60 * 24 * 30
SOCIAL_AUTH_SESSION_KEY = "social_auth_state"
SOCIAL_EMAIL_SESSION_KEY = "social_email_state"
SOCIAL_PROVIDERS = {"google", "facebook", "x"}


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


def social_auth_start_view(request, provider):
    provider = provider.lower()
    if provider not in SOCIAL_PROVIDERS:
        messages.error(request, "Provedor social não suportado.")
        return redirect("login")
    state = secrets.token_urlsafe(24)
    next_url = safe_redirect_url(request, request.GET.get("next"), reverse("home"))
    redirect_uri = request.build_absolute_uri(reverse("social-auth-callback", kwargs={"provider": provider}))
    try:
        response = social_auth_start(provider, {"redirect_uri": redirect_uri, "state": state})
    except AuthAPIError as exc:
        messages.error(request, str(exc))
        return redirect("login")
    request.session[SOCIAL_AUTH_SESSION_KEY] = {
        "provider": provider,
        "state": response.get("state") or state,
        "next": next_url,
        "referral_code": request.session.get(ReferralCaptureMiddleware.SESSION_KEY, ""),
        "oauth_token_secret": response.get("oauth_token_secret", ""),
    }
    return redirect(response["authorization_url"])


def social_auth_callback_view(request, provider):
    provider = provider.lower()
    session_state = request.session.get(SOCIAL_AUTH_SESSION_KEY) or {}
    fallback = reverse("login")
    if provider not in SOCIAL_PROVIDERS or session_state.get("provider") != provider:
        messages.error(request, "Não foi possível validar o início do login social.")
        return redirect(fallback)
    if request.GET.get("error"):
        messages.error(request, "Login social cancelado ou recusado pelo provedor.")
        request.session.pop(SOCIAL_AUTH_SESSION_KEY, None)
        return redirect(fallback)
    if provider != "x" and request.GET.get("state") != session_state.get("state"):
        messages.error(request, "Não foi possível validar a segurança do login social.")
        request.session.pop(SOCIAL_AUTH_SESSION_KEY, None)
        return redirect(fallback)
    payload = {
        "redirect_uri": request.build_absolute_uri(reverse("social-auth-callback", kwargs={"provider": provider})),
        "code": request.GET.get("code", ""),
        "state": request.GET.get("state", ""),
        "oauth_token": request.GET.get("oauth_token", ""),
        "oauth_verifier": request.GET.get("oauth_verifier", ""),
        "oauth_token_secret": session_state.get("oauth_token_secret", ""),
        "referral_code": session_state.get("referral_code", ""),
    }
    try:
        response = social_auth_callback(provider, payload)
    except AuthAPIError as exc:
        if isinstance(exc.detail, dict) and exc.detail.get("code") == "social_email_required":
            request.session[SOCIAL_EMAIL_SESSION_KEY] = {
                "provider": provider,
                "subject": exc.detail.get("subject", ""),
                "display_name": exc.detail.get("display_name", ""),
                "preferred_language": exc.detail.get("preferred_language", "pt-br"),
                "referral_code": session_state.get("referral_code", ""),
                "next": session_state.get("next", reverse("home")),
            }
            request.session.pop(SOCIAL_AUTH_SESSION_KEY, None)
            return redirect("social-auth-email")
        messages.error(request, str(exc))
        request.session.pop(SOCIAL_AUTH_SESSION_KEY, None)
        return redirect(fallback)
    request.session.pop(SOCIAL_AUTH_SESSION_KEY, None)
    request.session.pop(ReferralCaptureMiddleware.SESSION_KEY, None)
    store_auth_session(request, response)
    return redirect(safe_redirect_url(request, session_state.get("next"), reverse("home")))


def social_auth_email_view(request):
    pending = request.session.get(SOCIAL_EMAIL_SESSION_KEY) or {}
    if not pending.get("provider") or not pending.get("subject"):
        messages.error(request, "Não foi possível encontrar o login social pendente.")
        return redirect("login")
    form = SocialEmailForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        payload = {
            "provider": pending["provider"],
            "subject": pending["subject"],
            "email": form.cleaned_data["email"],
            "display_name": pending.get("display_name", ""),
            "preferred_language": pending.get("preferred_language", "pt-br"),
            "referral_code": pending.get("referral_code", ""),
        }
        try:
            response = social_auth_complete_email(pending["provider"], payload)
        except AuthAPIError as exc:
            if exc.status_code == 409:
                form.add_error(None, "Email já está em uso. Entre com email e senha antes de vincular este provedor social.")
            else:
                form.add_error(None, str(exc))
        else:
            request.session.pop(SOCIAL_EMAIL_SESSION_KEY, None)
            request.session.pop(ReferralCaptureMiddleware.SESSION_KEY, None)
            store_auth_session(request, response)
            messages.success(request, "Enviamos um email para confirmar sua conta.")
            return redirect(safe_redirect_url(request, pending.get("next"), reverse("home")))
    return render(request, "accounts/social_email.html", {"form": form, "provider": pending.get("provider", "social")})


def logout_view(request):
    token = auth_token(request)
    if token:
        try:
            logout_user(token)
        except AuthAPIError:
            pass
    clear_auth_session(request)
    return redirect("home")
