import base64
import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode

import httpx


SUPPORTED_SOCIAL_PROVIDERS = {"google", "facebook", "x"}


class SocialOAuthError(Exception):
    def __init__(self, message, *, status_code=400):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class SocialAuthorization:
    authorization_url: str
    state: str
    oauth_token_secret: str = ""


@dataclass
class SocialProfile:
    provider: str
    subject: str
    email: str
    email_verified: bool
    display_name: str
    preferred_language: str = "pt-br"


def _env(name):
    return os.environ.get(name, "").strip()


def _require_provider(provider):
    provider = (provider or "").strip().lower()
    if provider not in SUPPORTED_SOCIAL_PROVIDERS:
        raise SocialOAuthError("Provedor não suportado.", status_code=404)
    return provider


def _require(value, label):
    if not value:
        raise SocialOAuthError(f"{label} não configurado.", status_code=503)
    return value


def _oauth2_credentials(provider):
    if provider == "google":
        return (
            _require(_env("GOTRENDLABS_GOOGLE_CLIENT_ID"), "Google Client ID"),
            _require(_env("GOTRENDLABS_GOOGLE_CLIENT_SECRET"), "Google Client Secret"),
        )
    if provider == "facebook":
        return (
            _require(_env("GOTRENDLABS_FACEBOOK_CLIENT_ID"), "Facebook Client ID"),
            _require(_env("GOTRENDLABS_FACEBOOK_CLIENT_SECRET"), "Facebook Client Secret"),
        )
    raise SocialOAuthError("Provedor OAuth2 inválido.", status_code=404)


def _x_credentials():
    return (
        _require(_env("GOTRENDLABS_X_CONSUMER_KEY"), "X Consumer Key"),
        _require(_env("GOTRENDLABS_X_CONSUMER_SECRET"), "X Consumer Secret"),
    )


def _x_oauth2_credentials():
    client_id = _env("GOTRENDLABS_X_CLIENT_ID")
    client_secret = _env("GOTRENDLABS_X_CLIENT_SECRET")
    if not client_id:
        return None
    return client_id, client_secret


def build_social_authorization(provider, *, redirect_uri, state=""):
    provider = _require_provider(provider)
    state = state or secrets.token_urlsafe(24)
    if provider == "google":
        client_id, _ = _oauth2_credentials(provider)
        return SocialAuthorization(
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth?"
            + urlencode(
                {
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": "openid email profile",
                    "state": state,
                    "access_type": "online",
                    "prompt": "select_account",
                }
            ),
            state=state,
        )
    if provider == "facebook":
        client_id, _ = _oauth2_credentials(provider)
        return SocialAuthorization(
            authorization_url="https://www.facebook.com/v19.0/dialog/oauth?"
            + urlencode(
                {
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": "email,public_profile",
                    "state": state,
                }
            ),
            state=state,
        )
    return _build_x_authorization(redirect_uri=redirect_uri, state=state)


def fetch_social_profile(provider, payload):
    provider = _require_provider(provider)
    if provider == "google":
        return _fetch_google_profile(payload)
    if provider == "facebook":
        return _fetch_facebook_profile(payload)
    return _fetch_x_profile(payload)


def _fetch_google_profile(payload):
    client_id, client_secret = _oauth2_credentials("google")
    token = _post_json(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": _require(payload.code, "Código OAuth"),
            "grant_type": "authorization_code",
            "redirect_uri": payload.redirect_uri,
        },
    )
    access_token = _require(token.get("access_token"), "Access token Google")
    profile = _get_json(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return SocialProfile(
        provider="google",
        subject=str(profile.get("sub") or ""),
        email=str(profile.get("email") or "").lower(),
        email_verified=bool(profile.get("email_verified")),
        display_name=str(profile.get("name") or profile.get("email") or "Usuário GoTrendLabs"),
        preferred_language=_normalize_locale(profile.get("locale")),
    )


def _fetch_facebook_profile(payload):
    client_id, client_secret = _oauth2_credentials("facebook")
    token = _get_json(
        "https://graph.facebook.com/v19.0/oauth/access_token",
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": payload.redirect_uri,
            "code": _require(payload.code, "Código OAuth"),
        },
    )
    access_token = _require(token.get("access_token"), "Access token Facebook")
    profile = _get_json(
        "https://graph.facebook.com/v19.0/me",
        params={"fields": "id,name,email,verified", "access_token": access_token},
    )
    return SocialProfile(
        provider="facebook",
        subject=str(profile.get("id") or ""),
        email=str(profile.get("email") or "").lower(),
        email_verified=False,
        display_name=str(profile.get("name") or profile.get("email") or "Usuário GoTrendLabs"),
    )


def _fetch_x_profile(payload):
    if payload.code:
        return _fetch_x_oauth2_profile(payload)
    consumer_key, consumer_secret = _x_credentials()
    oauth_token = _require(payload.oauth_token, "OAuth token X")
    oauth_verifier = _require(payload.oauth_verifier, "OAuth verifier X")
    token_secret = _require(payload.oauth_token_secret, "OAuth token secret X")
    access = _post_oauth1(
        "https://api.twitter.com/oauth/access_token",
        consumer_key,
        consumer_secret,
        token=oauth_token,
        token_secret=token_secret,
        extra={"oauth_verifier": oauth_verifier},
    )
    access_token = _require(access.get("oauth_token"), "Access token X")
    access_secret = _require(access.get("oauth_token_secret"), "Access token secret X")
    profile = _get_oauth1_json(
        "https://api.twitter.com/1.1/account/verify_credentials.json",
        consumer_key,
        consumer_secret,
        token=access_token,
        token_secret=access_secret,
        params={"include_email": "true", "skip_status": "true", "include_entities": "false"},
    )
    return SocialProfile(
        provider="x",
        subject=str(profile.get("id_str") or profile.get("id") or ""),
        email=str(profile.get("email") or "").lower(),
        email_verified=bool(profile.get("email")),
        display_name=str(profile.get("name") or profile.get("screen_name") or "Usuário GoTrendLabs"),
    )


def _build_x_authorization(*, redirect_uri, state):
    oauth2_credentials = _x_oauth2_credentials()
    if oauth2_credentials:
        client_id, _ = oauth2_credentials
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")
        return SocialAuthorization(
            authorization_url="https://x.com/i/oauth2/authorize?"
            + urlencode(
                {
                    "response_type": "code",
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "scope": "users.read tweet.read",
                    "state": state,
                    "code_challenge": code_challenge,
                    "code_challenge_method": "S256",
                }
            ),
            state=state,
            oauth_token_secret=code_verifier,
        )
    consumer_key, consumer_secret = _x_credentials()
    data = _post_oauth1(
        "https://api.twitter.com/oauth/request_token",
        consumer_key,
        consumer_secret,
        extra={"oauth_callback": redirect_uri},
    )
    oauth_token = _require(data.get("oauth_token"), "OAuth token X")
    oauth_token_secret = _require(data.get("oauth_token_secret"), "OAuth token secret X")
    return SocialAuthorization(
        authorization_url="https://api.twitter.com/oauth/authenticate?" + urlencode({"oauth_token": oauth_token, "state": state}),
        state=state,
        oauth_token_secret=oauth_token_secret,
    )


def _fetch_x_oauth2_profile(payload):
    credentials = _x_oauth2_credentials()
    if not credentials:
        raise SocialOAuthError("X OAuth2 Client ID não configurado.", status_code=503)
    client_id, client_secret = credentials
    headers = {}
    if client_secret:
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers["Authorization"] = f"Basic {basic}"
    token = _post_json(
        "https://api.x.com/2/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": _require(payload.code, "Código OAuth X"),
            "redirect_uri": payload.redirect_uri,
            "code_verifier": _require(payload.oauth_token_secret, "Code verifier X"),
        },
        headers=headers,
    )
    access_token = _require(token.get("access_token"), "Access token X")
    profile = _get_json(
        "https://api.x.com/2/users/me",
        params={"user.fields": "id,name,username"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = profile.get("data") or {}
    return SocialProfile(
        provider="x",
        subject=str(data.get("id") or ""),
        email="",
        email_verified=False,
        display_name=str(data.get("name") or data.get("username") or "Usuário GoTrendLabs"),
    )


def _post_json(url, *, data, headers=None):
    try:
        response = httpx.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise SocialOAuthError("Não foi possível validar o login social.") from exc


def _get_json(url, *, params=None, headers=None):
    try:
        response = httpx.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise SocialOAuthError("Não foi possível obter o perfil do provedor social.") from exc


def _post_oauth1(url, consumer_key, consumer_secret, *, token="", token_secret="", extra=None):
    params = extra or {}
    headers = {"Authorization": _oauth1_header("POST", url, consumer_key, consumer_secret, token=token, token_secret=token_secret, extra=params)}
    try:
        response = httpx.post(url, data=params, headers=headers, timeout=10)
        response.raise_for_status()
        return dict(parse_qsl(response.text))
    except httpx.HTTPError as exc:
        raise SocialOAuthError("Não foi possível validar o login com X.") from exc


def _get_oauth1_json(url, consumer_key, consumer_secret, *, token, token_secret, params):
    headers = {"Authorization": _oauth1_header("GET", url, consumer_key, consumer_secret, token=token, token_secret=token_secret, extra=params)}
    try:
        response = httpx.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise SocialOAuthError("Não foi possível obter o perfil do X.") from exc


def _oauth1_header(method, url, consumer_key, consumer_secret, *, token="", token_secret="", extra=None):
    oauth = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": secrets.token_urlsafe(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
    }
    if token:
        oauth["oauth_token"] = token
    signature_params = {**oauth, **(extra or {})}
    base = "&".join(
        [
            method.upper(),
            _quote(url),
            _quote("&".join(f"{_quote(k)}={_quote(v)}" for k, v in sorted((str(k), str(v)) for k, v in signature_params.items()))),
        ]
    )
    signing_key = f"{_quote(consumer_secret)}&{_quote(token_secret)}"
    oauth["oauth_signature"] = base64.b64encode(hmac.new(signing_key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{_quote(k)}="{_quote(v)}"' for k, v in oauth.items())


def _quote(value):
    return quote(str(value), safe="~")


def _normalize_locale(locale):
    locale = (locale or "").lower().replace("_", "-")
    return locale if locale in {"pt-br", "en"} else "pt-br"
