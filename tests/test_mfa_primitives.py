import os
import time
import unittest

from cryptography.fernet import Fernet

from apps.api.backend_api.mfa import decrypt_secret, encrypt_secret, new_secret, valid_timestep


class TotpPrimitiveTests(unittest.TestCase):
    def setUp(self):
        self.previous = os.environ.get("GOTRENDLABS_TOTP_ENCRYPTION_KEY")
        os.environ["GOTRENDLABS_TOTP_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("GOTRENDLABS_TOTP_ENCRYPTION_KEY", None)
        else:
            os.environ["GOTRENDLABS_TOTP_ENCRYPTION_KEY"] = self.previous

    def test_secret_is_encrypted_and_round_trips(self):
        secret = new_secret()
        encrypted = encrypt_secret(secret)
        self.assertNotEqual(secret, encrypted)
        self.assertEqual(secret, decrypt_secret(encrypted))

    def test_totp_rejects_malformed_code(self):
        self.assertIsNone(valid_timestep(new_secret(), "not-a-code", now=time.time()))

    def test_totp_accepts_rfc6238_vector_at_six_digits(self):
        secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        self.assertEqual(valid_timestep(secret, "287082", now=59), 1)
