import os
import time
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from fastapi.testclient import TestClient

from apps.api.backend_api.main import app
from apps.api.backend_api.mfa import _code
from apps.api.backend_api.security import make_password
from tests.test_cases import AppendOnlyTransactionTestCase


class AdministrativeMfaIntegrationTests(AppendOnlyTransactionTestCase):
    """Exercise the API boundary against Django's PostgreSQL test database."""

    def setUp(self):
        super().setUp()
        self.environment = patch.dict(
            os.environ,
            {
                "FASTAPI_POSTGRES_DB": "",
                "FASTAPI_POSTGRES_USER": "",
                "FASTAPI_POSTGRES_PASSWORD": "",
                "FASTAPI_POSTGRES_HOST": "",
                "FASTAPI_POSTGRES_PORT": "",
                "GOTRENDLABS_PASSWORD_PEPPER": "QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUE=",
                "GOTRENDLABS_TOTP_ENCRYPTION_KEY": Fernet.generate_key().decode(),
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        User = get_user_model()
        User.objects.filter(username__in=["@mfa_super", "@mfa_super_only", "@mfa_target", "@mfa_member"]).delete()
        self.superuser = User.objects.create(
            username="@mfa_super",
            email="mfa-super@example.com",
            first_name="MFA Super",
            password=make_password("testpass123"),
            is_staff=True,
            is_superuser=True,
            is_active=True,
            account_status="active",
        )
        self.target = User.objects.create(
            username="@mfa_target",
            email="mfa-target@example.com",
            first_name="MFA Target",
            password=make_password("testpass123"),
            is_staff=True,
            is_active=True,
            account_status="active",
        )
        self.superuser_only = User.objects.create(
            username="@mfa_super_only",
            email="mfa-super-only@example.com",
            first_name="MFA Super Only",
            password=make_password("testpass123"),
            is_staff=False,
            is_superuser=True,
            is_active=True,
            account_status="active",
        )
        self.member = User.objects.create(
            username="@mfa_member",
            email="mfa-member@example.com",
            first_name="MFA Member",
            password=make_password("testpass123"),
            is_active=True,
            account_status="active",
        )
        self.client_api = TestClient(app)

    def _enroll(self, email):
        login = self.client_api.post("/auth/login", json={"email": email, "password": "testpass123"})
        self.assertEqual(login.status_code, 200)
        self.assertTrue(login.json()["mfa_required"])
        challenge = login.json()["challenge_token"]
        enrollment = self.client_api.post("/auth/mfa/enroll", json={"challenge_token": challenge})
        self.assertEqual(enrollment.status_code, 200)
        self.assertEqual(enrollment.headers["cache-control"], "private, no-store")
        verified = self.client_api.post(
            "/auth/mfa/verify",
            json={"challenge_token": challenge, "code": _code(enrollment.json()["manual_key"], int(time.time() // 30))},
        )
        self.assertEqual(verified.status_code, 200)
        self.assertEqual(verified.headers["cache-control"], "private, no-store")
        return verified.json()

    def test_staff_requires_totp_and_superuser_can_recover_target(self):
        authenticated = self._enroll(self.superuser.email)
        token = authenticated["session"]["token"]
        self.assertEqual(self.client_api.get("/admin/users", headers={"Authorization": f"Bearer {token}"}).status_code, 200)

        reset = self.client_api.post(
            f"/admin/users/{self.target.id}/mfa/recover",
            json={"note": "integration test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(reset.status_code, 200)
        target_login = self.client_api.post("/auth/login", json={"email": self.target.email, "password": "testpass123"})
        self.assertEqual(target_login.status_code, 200)
        self.assertTrue(target_login.json()["enrollment_required"])

    def test_superuser_without_staff_flag_receives_mfa_admin_session(self):
        authenticated = self._enroll(self.superuser_only.email)
        token = authenticated["session"]["token"]

        self.assertEqual(self.client_api.get("/admin/users", headers={"Authorization": f"Bearer {token}"}).status_code, 200)

    def test_regular_user_session_has_no_mfa_evidence_but_remains_valid(self):
        login = self.client_api.post("/auth/login", json={"email": self.member.email, "password": "testpass123"})

        self.assertEqual(login.status_code, 200)
        self.assertFalse(login.json().get("mfa_required", False))
        token = login.json()["session"]["token"]
        self.assertEqual(self.client_api.get("/auth/session", headers={"Authorization": f"Bearer {token}"}).status_code, 200)
