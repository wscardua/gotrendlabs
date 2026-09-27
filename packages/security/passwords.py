"""Password hashing owned by FastAPI; Django uses this only in isolated tests."""

import base64
import binascii
import hashlib
import hmac
import os
import threading

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type


ALGORITHM = "argon2id_pepper_v1"
PREFIX = f"{ALGORITHM}$"
PEPPER_ENV = "GOTRENDLABS_PASSWORD_PEPPER"
HASHER = PasswordHasher(
    time_cost=2,
    memory_cost=19456,  # KiB (19 MiB): OWASP baseline for the current small host
    parallelism=1,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)
_HASH_SLOTS = threading.BoundedSemaphore(2)


def require_password_pepper():
    """Load a distinct 256-bit secret; never fall back to an application key."""
    encoded = os.environ.get(PEPPER_ENV, "")
    try:
        pepper = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError(f"{PEPPER_ENV} must be base64-encoded random bytes") from exc
    if len(pepper) != 32:
        raise RuntimeError(f"{PEPPER_ENV} must contain exactly 32 random bytes")
    return pepper


def _prepared_password(password):
    password_bytes = password.encode("utf-8") if isinstance(password, str) else password
    return hmac.new(require_password_pepper(), password_bytes, hashlib.sha256).digest()


def make_password(password, *, salt=None):
    prepared = _prepared_password(password)
    with _HASH_SLOTS:
        return PREFIX + HASHER.hash(prepared, salt=salt)


def check_password(password, encoded_password):
    if not encoded_password or not encoded_password.startswith(PREFIX):
        return False
    prepared = _prepared_password(password)
    try:
        with _HASH_SLOTS:
            return HASHER.verify(encoded_password[len(PREFIX):], prepared)
    except (InvalidHashError, VerificationError):
        return False


def password_needs_rehash(encoded_password):
    if not encoded_password or not encoded_password.startswith(PREFIX):
        return True
    try:
        return HASHER.check_needs_rehash(encoded_password[len(PREFIX):])
    except (InvalidHashError, VerificationError):
        return True
