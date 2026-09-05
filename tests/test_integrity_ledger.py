import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest import mock

from django.db import DatabaseError, transaction
from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone as django_timezone
from fastapi.testclient import TestClient

from apps.api.backend_api import integrity_service
from apps.api.backend_api.daemon_services import seal_due_markets
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.main import _market_lifecycle_engine, app
from apps.web.django.markets.models import AdminEvent, IntegrityLedgerEvent, Market, MarketIntegrityDefinition, MarketSeal, PredictionCommitment, UserNotification
from tests.test_web_smoke import _seed_test_badges, _seed_test_email_templates, _seed_test_markets


class IntegrityProtocolTests(SimpleTestCase):
    def setUp(self):
        self.previous_signer = integrity_service._signer
        integrity_service._signer = integrity_service._EphemeralSigner()

    def tearDown(self):
        integrity_service._signer = self.previous_signer

    def test_canonical_payload_is_deterministic_utf8(self):
        instant = datetime(2026, 9, 5, 12, 30, tzinfo=timezone.utc)
        first = integrity_service.canonical_json({"z": "ação", "a": instant})
        second = integrity_service.canonical_json({"a": instant, "z": "ação"})
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), {"a": "2026-09-05T12:30:00Z", "z": "ação"})

    def test_signature_detects_payload_tampering(self):
        canonical, digest, signature = integrity_service.sign_payload({"market_id": 7, "result": "SIM"})
        self.assertTrue(integrity_service.verify_signed_hash(digest, signature.value, signature.public_key_der))
        tampered = integrity_service.sha256_hex(canonical.replace(b"SIM", b"NAO"))
        self.assertFalse(integrity_service.verify_signed_hash(tampered, signature.value, signature.public_key_der))

    def test_merkle_proof_validates_each_leaf_and_rejects_tampering(self):
        leaves = [integrity_service.sha256_hex(f"prediction:{index}".encode()) for index in range(5)]
        root, proofs = integrity_service.build_merkle(leaves)
        for index, leaf in enumerate(leaves):
            self.assertTrue(integrity_service.verify_merkle_proof(leaf, proofs[index], root))
        self.assertFalse(integrity_service.verify_merkle_proof("0" * 64, proofs[0], root))

    def test_user_commitment_is_pseudonymous_and_secret_bound(self):
        with mock.patch.dict("os.environ", {"GOTRENDLABS_USER_COMMITMENT_SECRET": "secret-a"}, clear=False):
            first = integrity_service._user_commitment(123)
        with mock.patch.dict("os.environ", {"GOTRENDLABS_USER_COMMITMENT_SECRET": "secret-b"}, clear=False):
            second = integrity_service._user_commitment(123)
        self.assertNotEqual(first, second)
        self.assertNotIn("123", first)
        self.assertEqual(len(first), 64)

    def test_public_key_lookup_does_not_issue_signature(self):
        signer = integrity_service._signer
        with mock.patch.object(signer, "sign", wraps=signer.sign) as sign:
            payload = integrity_service.public_key_payload()
        sign.assert_not_called()
        self.assertEqual(payload["fingerprint"], integrity_service.sha256_hex(signer.public_key()))

    def test_production_requires_managed_key(self):
        integrity_service._signer = None
        with mock.patch.dict("os.environ", {"GOTRENDLABS_ENV": "production", "GOTRENDLABS_INTEGRITY_KMS_KEY_ID": ""}, clear=False):
            with self.assertRaises(integrity_service.IntegritySigningError):
                integrity_service.get_signer()

    def test_kms_signer_uses_ed25519_raw_without_exporting_private_key(self):
        public_der = integrity_service._signer.public_key()
        client = mock.Mock()
        client.sign.return_value = {"Signature": b"signature", "KeyId": "key-arn"}
        client.get_public_key.return_value = {"PublicKey": public_der}
        boto3 = mock.Mock()
        boto3.client.return_value = client
        botocore_config = mock.Mock()
        with mock.patch.dict("sys.modules", {"boto3": boto3, "botocore.config": botocore_config}):
            signer = integrity_service._KMSSigner("alias/gotrendlabs-integrity")
            signed = signer.sign("a" * 64)
        client.sign.assert_called_once_with(
            KeyId="alias/gotrendlabs-integrity",
            Message=b"a" * 64,
            MessageType="RAW",
            SigningAlgorithm="ED25519_SHA_512",
        )
        self.assertEqual(signed.key_fingerprint, integrity_service.sha256_hex(public_der))

    def test_append_only_guards_and_institutional_disclaimer_are_versioned(self):
        root = Path(__file__).resolve().parents[1]
        migration = (root / "apps/web/django/markets/migrations/0027_market_integrity_ledger.py").read_text()
        self.assertIn("BEFORE UPDATE OR DELETE", migration)
        self.assertIn("REVOKE UPDATE, DELETE", migration)
        for relative in (
            "apps/web/django/core/templates/core/security.html",
            "apps/mobile/lib/src/features/info/trust_screen.dart",
        ):
            content = (root / relative).read_text()
            self.assertIn("não equivale a uma blockchain pública ou descentralizada", content)


class IntegrityLedgerIntegrationTests(TransactionTestCase):
    def setUp(self):
        self.previous_signer = integrity_service._signer
        integrity_service._signer = integrity_service._EphemeralSigner()
        _seed_test_badges()
        _seed_test_markets()
        _seed_test_email_templates()
        self.client = TestClient(app)
        self.staff_headers = self._register("Integrity Staff", "integrity-staff@example.com")
        self.user_headers = self._register("Integrity User", "integrity-user@example.com")
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff=true WHERE email=%s", ("integrity-staff@example.com",))

    def tearDown(self):
        integrity_service._signer = self.previous_signer

    def _register(self, display_name, email):
        response = self.client.post(
            "/auth/register",
            json={"display_name": display_name, "email": email, "language": "pt-br", "password": "testpass123", "terms_accepted": True},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return {"Authorization": f"Bearer {response.json()['session']['token']}"}

    def _resolve_due_market(self, slug="openai-gpt6-2026"):
        market = Market.objects.get(slug=slug)
        option = market.options.order_by("display_order", "id").first()
        prediction = self.client.post(
            f"/markets/{slug}/predict",
            headers=self.user_headers,
            json={"option_id": option.id, "stake_amount": 25, "client_locale": "pt-br"},
        )
        self.assertEqual(prediction.status_code, 201, prediction.text)
        if market.auto_close_enabled:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM gotrendlabs_markets WHERE id=%s FOR UPDATE", (market.id,))
                    market_row = cursor.fetchone()
                    cursor.execute("SELECT id FROM gotrendlabs_users WHERE email=%s", ("integrity-staff@example.com",))
                    staff_id = cursor.fetchone()["id"]
                    _market_lifecycle_engine(cursor, staff_id).lock_market_automatically(
                        market_row,
                        slug,
                        note="Fechamento automático de teste",
                        now=django_timezone.now(),
                    )
        else:
            locked = self.client.post(f"/admin/markets/{slug}/lock", headers=self.staff_headers, json={"note": "Fechamento de teste"})
            self.assertEqual(locked.status_code, 200, locked.text)
        resolved = self.client.post(
            f"/admin/markets/{slug}/resolve",
            headers=self.staff_headers,
            json={"winning_option_id": option.id, "source_url": "https://example.com/evidence", "note": "Evidência conferida"},
        )
        self.assertEqual(resolved.status_code, 200, resolved.text)
        due = django_timezone.now() - timedelta(seconds=1)
        Market.objects.filter(pk=market.pk).update(seal_due_at=due)
        market.refresh_from_db()
        return market, prediction.json()["prediction_id"], due

    def test_due_sealing_is_concurrent_safe_idempotent_and_publicly_verifiable(self):
        market, prediction_id, due = self._resolve_due_market()
        receipt = self.client.get(
            f"/markets/{market.slug}/predictions/{prediction_id}/receipt",
            headers=self.user_headers,
        )
        self.assertEqual(receipt.status_code, 200)
        self.assertNotIn("integrity-user@example.com", json.dumps(receipt.json()))

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _index: seal_due_markets(now=due + timedelta(seconds=2)), range(2)))
        self.assertEqual(sum(len(item["sealed"]) for item in outcomes), 1, outcomes)
        self.assertEqual(MarketSeal.objects.filter(market=market).count(), 1)
        market.refresh_from_db()
        self.assertEqual(market.status, "sealed")

        proof = self.client.get(
            f"/markets/{market.slug}/predictions/{prediction_id}/merkle-proof",
            headers=self.user_headers,
        )
        self.assertEqual(proof.status_code, 200, proof.text)
        merkle = proof.json()["merkle_proof"]
        self.assertTrue(integrity_service.verify_merkle_proof(merkle["leaf_hash"], merkle["proof"], merkle["predictions_root"]))
        verification = self.client.get(f"/markets/{market.slug}/integrity/verify")
        self.assertEqual(verification.status_code, 200)
        self.assertTrue(verification.json()["valid"], verification.json())

        repeated = seal_due_markets(now=due + timedelta(seconds=3))
        self.assertEqual(repeated, {"sealed": [], "failed": []})
        self.assertEqual(UserNotification.objects.filter(market=market, event_type="market_sealed").count(), 1)
        self.assertTrue(IntegrityLedgerEvent.objects.filter(market=market, event_type="market_sealed").exists())

        definition = MarketIntegrityDefinition.objects.get(market=market)
        with self.assertRaises(DatabaseError), transaction.atomic():
            MarketIntegrityDefinition.objects.filter(pk=definition.pk).update(payload_hash="0" * 64)

    def test_signing_failure_keeps_market_resolved_and_retry_seals_once(self):
        market, _prediction_id, due = self._resolve_due_market("tiktok-ban-eua-2026")
        healthy_signer = integrity_service._signer
        failing_signer = mock.Mock()
        failing_signer.sign.side_effect = integrity_service.IntegritySigningError("kms unavailable")
        integrity_service._signer = failing_signer
        failed = seal_due_markets(now=due + timedelta(seconds=2))
        self.assertEqual(len(failed["failed"]), 1)
        market.refresh_from_db()
        self.assertEqual(market.status, "resolved")
        self.assertFalse(MarketSeal.objects.filter(market=market).exists())
        self.assertTrue(AdminEvent.objects.filter(action="integrity.seal_failed", entity_identifier=market.slug).exists())

        integrity_service._signer = healthy_signer
        retried = seal_due_markets(now=due + timedelta(seconds=3))
        self.assertEqual(len(retried["sealed"]), 1, retried)
        self.assertEqual(MarketSeal.objects.filter(market=market).count(), 1)
        self.assertGreaterEqual(PredictionCommitment.objects.filter(market=market).count(), 1)
