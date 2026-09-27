import base64
import os
import subprocess
import sys
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password as django_check_password
from django.contrib.auth.hashers import make_password as django_make_password
from django.test import SimpleTestCase

from apps.api.backend_api.bootstrap_admin_password import set_admin_password
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.security import check_password, make_password
from apps.web.django.accounts.hashers import APIOnlyPasswordHasher
from apps.web.django.markets.models import AdminEvent
from packages.security.passwords import ALGORITHM, PEPPER_ENV
from tests.test_cases import AppendOnlyTransactionTestCase


class PasswordHashingTests(SimpleTestCase):
    def setUp(self):
        self.pepper = base64.b64encode(b"a" * 32).decode("ascii")

    def test_api_and_django_share_peppered_argon2id_hashes(self):
        with patch.dict(os.environ, {PEPPER_ENV: self.pepper}):
            api_hash = make_password("senha forte")
            other_hash = make_password("senha forte")
            django_hash = django_make_password("senha forte")
            user = get_user_model()(username="hash-test")
            user.set_password("senha forte")

            self.assertTrue(api_hash.startswith(f"{ALGORITHM}$$argon2id$"))
            self.assertIn("m=19456,t=2,p=1", api_hash)
            self.assertNotEqual(api_hash, other_hash)
            self.assertTrue(check_password("senha forte", django_hash))
            self.assertTrue(django_check_password("senha forte", api_hash))
            self.assertTrue(user.check_password("senha forte"))
            self.assertFalse(check_password("senha errada", api_hash))

    def test_wrong_or_missing_pepper_cannot_verify_or_create_password(self):
        with patch.dict(os.environ, {PEPPER_ENV: self.pepper}):
            encoded = make_password("senha forte")

        other_pepper = base64.b64encode(b"b" * 32).decode("ascii")
        with patch.dict(os.environ, {PEPPER_ENV: other_pepper}):
            self.assertFalse(check_password("senha forte", encoded))

        with patch.dict(os.environ, {PEPPER_ENV: ""}):
            with self.assertRaises(RuntimeError):
                check_password("senha forte", encoded)
            with self.assertRaises(RuntimeError):
                make_password("senha forte")

    def test_old_and_malformed_hashes_are_not_accepted(self):
        with patch.dict(os.environ, {PEPPER_ENV: self.pepper}):
            self.assertFalse(check_password("senha", "pbkdf2_sha256$720000$salt$digest"))
            self.assertFalse(check_password("senha", f"{ALGORITHM}$invalid"))
            self.assertFalse(django_check_password("senha", f"{ALGORITHM}$invalid"))

    def test_django_runtime_hasher_rejects_usable_passwords(self):
        hasher = APIOnlyPasswordHasher()
        with self.assertRaises(RuntimeError):
            hasher.encode("senha forte", "")
        self.assertFalse(hasher.verify("senha forte", "anything"))

    def test_only_fastapi_production_startup_requires_pepper(self):
        env = {
            **os.environ,
            "GOTRENDLABS_ENV": "production",
            "DJANGO_DEBUG": "0",
            "DJANGO_SECRET_KEY": "test-only-django-secret-with-more-than-fifty-distinct-characters-1234567890",
            PEPPER_ENV: "",
        }
        for module in ("config.settings", "apps.api.backend_api.main"):
            with self.subTest(module=module):
                result = subprocess.run(
                    [sys.executable, "-c", f"import {module}"],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if module == "config.settings":
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(PEPPER_ENV, result.stderr)


class AdminPasswordBootstrapTests(AppendOnlyTransactionTestCase):
    def test_existing_admin_password_is_set_and_audited_by_api_code(self):
        admin = get_user_model().objects.create_superuser(
            username="bootstrap-admin", email="bootstrap@example.com", password="old-password"
        )
        db_env = {key: "" for key in (
            "FASTAPI_POSTGRES_DB", "FASTAPI_POSTGRES_USER", "FASTAPI_POSTGRES_PASSWORD",
            "FASTAPI_POSTGRES_HOST", "FASTAPI_POSTGRES_PORT",
        )}
        with patch.dict(os.environ, db_env):
            set_admin_password(admin.username, "new-password-123")
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT password FROM gotrendlabs_users WHERE id = %s", (admin.id,))
                    encoded = cursor.fetchone()["password"]
        self.assertTrue(check_password("new-password-123", encoded))
        self.assertTrue(AdminEvent.objects.filter(
            action="user.bootstrap_password_set", entity_identifier=str(admin.id)
        ).exists())
        with self.assertRaises(ValueError):
            with patch.dict(os.environ, db_env):
                set_admin_password("missing-admin", "new-password-123")
