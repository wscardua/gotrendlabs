import base64
import hashlib
import hmac
import secrets


PBKDF2_ITERATIONS = 720000


def make_password(raw_password):
    salt = secrets.token_urlsafe(12)
    digest = hashlib.pbkdf2_hmac("sha256", raw_password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    encoded = base64.b64encode(digest).decode().strip()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${encoded}"


def check_password(raw_password, encoded_password):
    try:
        algorithm, iterations, salt, encoded = encoded_password.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac("sha256", raw_password.encode(), salt.encode(), int(iterations))
    candidate = base64.b64encode(digest).decode().strip()
    return hmac.compare_digest(candidate, encoded)


def issue_token():
    return secrets.token_urlsafe(48)


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()
