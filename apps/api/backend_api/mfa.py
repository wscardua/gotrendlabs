"""TOTP primitives. Secrets are only decrypted inside the FastAPI process."""
import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken


def _key():
    value = os.environ.get("GOTRENDLABS_TOTP_ENCRYPTION_KEY", "").encode()
    if not value:
        raise RuntimeError("GOTRENDLABS_TOTP_ENCRYPTION_KEY is required for MFA.")
    try:
        return Fernet(value)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("GOTRENDLABS_TOTP_ENCRYPTION_KEY must be a Fernet key.") from exc


def require_totp_encryption_key():
    _key()


def new_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def encrypt_secret(secret):
    return _key().encrypt(secret.encode()).decode()


def decrypt_secret(value):
    try:
        return _key().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Stored TOTP secret cannot be decrypted.") from exc


def _code(secret, counter):
    raw = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.new(raw, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 15
    number = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7fffffff) % 1_000_000
    return f"{number:06d}"


def valid_timestep(secret, code, now=None):
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        return None
    current = int((time.time() if now is None else now) // 30)
    for timestep in (current - 1, current, current + 1):
        if hmac.compare_digest(_code(secret, timestep), code):
            return timestep
    return None


def recovery_codes(count=10):
    return ["-".join((secrets.token_hex(4), secrets.token_hex(4))).upper() for _ in range(count)]


def otpauth_uri(secret, account_label):
    return "otpauth://totp/{}?secret={}&issuer={}&algorithm=SHA1&digits=6&period=30".format(
        quote("GoTrendLabs:" + account_label), secret, quote("GoTrendLabs")
    )
