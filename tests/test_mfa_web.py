from unittest.mock import patch

from django.test import TestCase
from django.template.loader import render_to_string
from django.urls import reverse

from apps.web.django.accounts.forms import MfaCodeForm

class MfaEnrollmentPageTests(TestCase):
    @patch("apps.web.django.accounts.views.mfa_enroll")
    def test_enrollment_page_displays_qr_and_manual_setup_instructions(self, mocked_enrollment):
        mocked_enrollment.return_value = {
            "manual_key": "ABCDEFGHIJKLMNOP",
            "otpauth_uri": "otpauth://totp/GoTrendLabs:test?secret=ABCDEFGHIJKLMNOP&issuer=GoTrendLabs",
        }
        session = self.client.session
        session["mfa_challenge"] = {"token": "opaque-challenge", "enrollment": True, "next": "/admin-ops/"}
        session.save()

        response = self.client.get(reverse("mfa-enroll"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data:image/png;base64,")
        self.assertContains(response, "Ler código QR")
        self.assertContains(response, "Configurar com chave manual")
        self.assertContains(response, "Confirme o código")
        self.assertContains(response, "ABCDEFGHIJKLMNOP")
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_recovery_codes_page_uses_a_readable_one_time_code_grid(self):
        html = render_to_string(
            "accounts/mfa_recovery_codes.html",
            {"recovery_codes": ["AAAA1111-BBBB2222", "CCCC3333-DDDD4444"], "next_url": "/admin-ops/"},
        )

        self.assertIn("Configuração concluída", html)
        self.assertIn("Exibidos uma única vez", html)
        self.assertIn("mfa-recovery-code-grid", html)
        self.assertIn("Quando e como usar", html)
        self.assertIn("Como guardar", html)
        self.assertIn("Guardei os códigos, continuar", html)

    def test_verify_page_prioritizes_totp_and_keeps_recovery_as_an_alternative(self):
        html = render_to_string("accounts/mfa_verify.html", {"form": MfaCodeForm()})

        self.assertIn("mfa-verify-card", html)
        self.assertIn("Código do autenticador", html)
        self.assertIn("Não tem acesso ao autenticador?", html)
        self.assertIn("Confirmar e entrar", html)

    def _set_mfa_challenge(self):
        session = self.client.session
        session["mfa_challenge"] = {"token": "opaque-challenge", "enrollment": False, "next": "/admin-ops/"}
        session.save()

    @patch("apps.web.django.accounts.views.mfa_verify")
    def test_existing_factor_redirects_after_totp_without_recovery_codes_page(self, mocked_verify):
        self._set_mfa_challenge()
        mocked_verify.return_value = {
            "user": {"id": 1, "display_name": "MFA Admin", "handle": "@mfa_admin", "preferred_language": "pt-br", "is_staff": True},
            "session": {"token": "session-token"},
            "recovery_codes": [],
        }

        response = self.client.post(reverse("mfa-verify"), {"code": "123456"})

        self.assertRedirects(response, "/admin-ops/", fetch_redirect_response=False)

    @patch("apps.web.django.accounts.views.mfa_verify")
    def test_initial_enrollment_shows_recovery_codes_once_without_browser_cache(self, mocked_verify):
        self._set_mfa_challenge()
        mocked_verify.return_value = {
            "user": {"id": 1, "display_name": "MFA Admin", "handle": "@mfa_admin", "preferred_language": "pt-br", "is_staff": True},
            "session": {"token": "session-token"},
            "recovery_codes": ["AAAA1111-BBBB2222"],
        }

        response = self.client.post(reverse("mfa-verify"), {"code": "123456"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AAAA1111-BBBB2222")
        self.assertEqual(response["Cache-Control"], "private, no-store")
