"""Django password policy: credentials belong to the FastAPI runtime."""

import secrets

from django.contrib.auth.hashers import BasePasswordHasher, mask_hash

from packages.security.passwords import ALGORITHM, check_password, make_password, password_needs_rehash


class APIOnlyPasswordHasher(BasePasswordHasher):
    algorithm = "api_credentials_only"

    def salt(self):
        return ""

    def encode(self, password, salt):
        raise RuntimeError("Create and change usable passwords through the FastAPI auth service.")

    def verify(self, password, encoded):
        return False

    def safe_summary(self, encoded):
        return {"algorithm": self.algorithm}


class Argon2PepperHasher(BasePasswordHasher):
    """Used by the isolated test process, never by Django web in runtime."""
    algorithm = ALGORITHM

    def salt(self):
        return secrets.token_bytes(16)

    def encode(self, password, salt):
        return make_password(password, salt=salt)

    def verify(self, password, encoded):
        return check_password(password, encoded)

    def must_update(self, encoded):
        return password_needs_rehash(encoded)

    def harden_runtime(self, password, encoded):
        pass

    def safe_summary(self, encoded):
        return {"algorithm": self.algorithm, "hash": mask_hash(encoded)}
