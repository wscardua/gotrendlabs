import json
import os
import urllib.error
import urllib.parse
import urllib.request

from config.env import load_env_file


VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
load_env_file()


class RecaptchaError(Exception):
    pass


def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def recaptcha_secret_key():
    return os.environ.get("RECAPTCHA_SECRET_KEY", "").strip()


def recaptcha_site_key():
    return os.environ.get("RECAPTCHA_SITE_KEY", "").strip()


def recaptcha_enabled():
    if "RECAPTCHA_ENABLED" in os.environ:
        return env_flag("RECAPTCHA_ENABLED")
    return bool(recaptcha_secret_key())


def verify_recaptcha_response(token, remote_ip=None):
    if not recaptcha_enabled():
        return True
    token = (token or "").strip()
    secret = recaptcha_secret_key()
    if not token:
        raise RecaptchaError("Confirme que você não é um robô.")
    if not secret:
        raise RecaptchaError("reCAPTCHA não configurado no servidor.")

    payload = {"secret": secret, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip
    request = urllib.request.Request(
        VERIFY_URL,
        data=urllib.parse.urlencode(payload).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RecaptchaError("Não foi possível validar o reCAPTCHA. Tente novamente.") from exc

    if not result.get("success"):
        raise RecaptchaError("reCAPTCHA inválido ou expirado. Tente novamente.")
    return True
