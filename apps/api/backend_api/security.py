import hashlib
import secrets

from packages.security.passwords import check_password, make_password


def issue_token():
    return secrets.token_urlsafe(48)


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()
