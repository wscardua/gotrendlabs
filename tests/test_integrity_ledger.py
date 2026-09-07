import json
from io import StringIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest import mock

from django.core.management import call_command, CommandError
from django.db import DatabaseError, transaction
from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone as django_timezone
from fastapi.testclient import TestClient

from apps.api.backend_api import integrity_service
from apps.api.backend_api.daemon_services import audit_integrity_records, run_daemon_cycle, seal_due_markets
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.main import _market_lifecycle_engine, app
from apps.web.django.accounts.models import BadgeDefinition, UserBadgeAward
from apps.web.django.markets.models import AdminEvent, IntegrityAlert, IntegrityLedgerEvent, IntegritySigningKey, Market, MarketComment, MarketIntegrityDefinition, MarketSeal, PredictionCommitment, UserNotification
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

    def test_ledger_signature_binds_all_persisted_event_metadata(self):
        occurred_at = datetime(2026, 9, 7, 15, 30, tzinfo=timezone.utc)
        payload = {
            "causation_id": None,
            "correlation_id": None,
            "entity_identifier": "market-slug",
            "entity_type": "market",
            "event_type": "market_published",
            "market_id": 7,
            "occurred_at": occurred_at,
            "payload_hash": "a" * 64,
            "payload_reference": "market_definition:4",
            "payload_snapshot": None,
            "previous_event_hash": "",
            "protocol_version": integrity_service.PROTOCOL_VERSION,
            "sequence": 12,
        }
        canonical, event_hash, signed = integrity_service.sign_payload(payload)
        event = {
            **payload,
            "canonical_payload": canonical,
            "payload_json": json.loads(canonical),
            "event_hash": event_hash,
            "signature": signed.value,
            "algorithm": signed.algorithm,
            "key_id": signed.key_id,
            "key_fingerprint": signed.key_fingerprint,
            "created_at": occurred_at,
        }
        self.assertTrue(integrity_service._ledger_event_is_valid(event, signed.public_key_der))
        for field, tampered_value in (
            ("protocol_version", "gtl-integrity/v2"),
            ("entity_type", "prediction"),
            ("entity_identifier", "other-market"),
            ("market_id", 8),
            ("occurred_at", occurred_at + timedelta(seconds=1)),
            ("correlation_id", "00000000-0000-0000-0000-000000000001"),
            ("algorithm", "OTHER"),
            ("key_fingerprint", "0" * 64),
            ("created_at", occurred_at + timedelta(seconds=1)),
        ):
            changed = {**event, field: tampered_value}
            self.assertFalse(integrity_service._ledger_event_is_valid(changed, signed.public_key_der), field)

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
        key_migration = (root / "apps/web/django/markets/migrations/0029_integrity_signing_keys.py").read_text()
        self.assertIn("integrity_signing_keys_append_only", key_migration)
        for relative in (
            "apps/web/django/core/templates/core/security.html",
            "apps/mobile/lib/src/features/info/trust_screen.dart",
        ):
            content = (root / relative).read_text()
            self.assertIn("não equivale a uma blockchain pública ou descentralizada", content)

    def test_daemon_audits_integrity_before_market_mutations(self):
        order = []
        audit_summary = {"markets_scanned": 2, "issues_detected": 0}
        connection = mock.MagicMock()

        with (
            mock.patch("apps.api.backend_api.daemon_services.audit_integrity_records", side_effect=lambda **_: order.append("audit") or audit_summary),
            mock.patch("apps.api.backend_api.daemon_services.close_due_auto_markets", side_effect=lambda **_: order.append("close") or []),
            mock.patch("apps.api.backend_api.daemon_services.seal_due_markets", side_effect=lambda **_: order.append("seal") or {"sealed": [], "failed": []}),
            mock.patch("apps.api.backend_api.daemon_services.prune_expired_operational_records", return_value={"total": 0}),
            mock.patch("apps.api.backend_api.daemon_services.get_connection", return_value=connection),
            mock.patch("apps.api.backend_api.daemon_services.run_ai_agent_cycle", return_value={"enabled": False}),
            mock.patch("apps.api.backend_api.daemon_services.log_daemon_event"),
            mock.patch("apps.web.django.communications.services.process_due_email_deliveries", return_value={}),
            mock.patch("apps.web.django.communications.push_services.process_due_push_deliveries", return_value={}),
        ):
            result = run_daemon_cycle(now=datetime(2026, 9, 6, tzinfo=timezone.utc))

        self.assertEqual(order, ["audit", "close", "seal"])
        self.assertEqual(result["integrity_audit"], audit_summary)

    def test_daemon_continues_independent_tasks_when_integrity_audit_crashes(self):
        order = []
        connection = mock.MagicMock()
        with (
            mock.patch("apps.api.backend_api.daemon_services.audit_integrity_records", side_effect=DatabaseError("timeout")),
            mock.patch("apps.api.backend_api.daemon_services.close_due_auto_markets", side_effect=lambda **_: order.append("close") or []),
            mock.patch("apps.api.backend_api.daemon_services.seal_due_markets") as seal,
            mock.patch("apps.api.backend_api.daemon_services.prune_expired_operational_records", side_effect=lambda **_: order.append("prune") or {"total": 0}),
            mock.patch("apps.api.backend_api.daemon_services.get_connection", return_value=connection),
            mock.patch("apps.api.backend_api.daemon_services.run_ai_agent_cycle", side_effect=lambda *_args, **_kwargs: order.append("ai") or {"enabled": False}),
            mock.patch("apps.api.backend_api.daemon_services.log_daemon_event"),
            mock.patch("apps.web.django.communications.services.process_due_email_deliveries", side_effect=lambda **_: order.append("email") or {}),
            mock.patch("apps.web.django.communications.push_services.process_due_push_deliveries", side_effect=lambda **_: order.append("push") or {}),
        ):
            result = run_daemon_cycle(now=datetime(2026, 9, 7, tzinfo=timezone.utc))

        self.assertFalse(result["integrity_audit"]["available"])
        self.assertEqual(result["integrity_seals"]["skipped_reason"], "integrity_audit_unavailable")
        seal.assert_not_called()
        self.assertEqual(order, ["close", "prune", "email", "push", "ai"])


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
        market.refresh_from_db()
        due = market.seal_due_at
        return market, prediction.json()["prediction_id"], due

    def test_registered_public_keys_survive_local_signer_rotation(self):
        first = self.client.get("/markets/openai-gpt6-2026/integrity/verify")
        self.assertTrue(first.json()["valid"], first.json())

        integrity_service._signer = integrity_service._EphemeralSigner()
        after_restart = self.client.get("/markets/openai-gpt6-2026/integrity/verify")
        self.assertTrue(after_restart.json()["valid"], after_restart.json())
        self.assertTrue(after_restart.json()["ledger_chain_valid"], after_restart.json())
        signing_key = IntegritySigningKey.objects.first()
        with self.assertRaises(DatabaseError), transaction.atomic():
            IntegritySigningKey.objects.filter(pk=signing_key.pk).update(key_fingerprint="0" * 64)

    def test_unsigned_market_purge_is_dry_run_protected_and_idempotent(self):
        unsigned_before = Market.objects.filter(
            status__in=("open", "locked", "resolved", "sealed", "canceled"),
            integrity_definition__isnull=True,
        ).count()
        self.assertGreater(unsigned_before, 0)
        output = StringIO()
        call_command("purge_unsigned_markets", stdout=output)
        self.assertEqual(json.loads(output.getvalue())["mode"], "dry-run")
        self.assertEqual(
            Market.objects.filter(
                status__in=("open", "locked", "resolved", "sealed", "canceled"),
                integrity_definition__isnull=True,
            ).count(),
            unsigned_before,
        )
        with self.assertRaises(CommandError):
            call_command("purge_unsigned_markets", execute=True)

        from django.contrib.auth import get_user_model

        user = get_user_model().objects.get(email="integrity-user@example.com")
        unsigned_market = Market.objects.filter(
            status__in=("open", "locked", "resolved", "sealed", "canceled"),
            integrity_definition__isnull=True,
        ).first()
        signed_market = Market.objects.get(slug="openai-gpt6-2026")
        MarketComment.objects.create(market=unsigned_market, author=user, body="Interacao no mercado a remover.")
        unrelated_badge = BadgeDefinition.objects.create(
            code="unrelated-resolution-history",
            name="Historico independente",
            description="Concessao ligada a outro mercado.",
        )
        unrelated_award = UserBadgeAward.objects.create(
            user=user,
            badge=unrelated_badge,
            awarded_at=django_timezone.now(),
            reason_snapshot=f"market_resolved:{signed_market.id}; resolved_predictions_count=1",
        )
        unrelated_notification = UserNotification.objects.create(
            recipient=user,
            event_type="badge_awarded",
            source_key=f"badge_awarded:{unrelated_badge.code}",
            title="Badge recebida",
            body="Historico independente.",
        )

        call_command("purge_unsigned_markets", execute=True, backup_confirmed=True, stdout=StringIO())
        self.assertFalse(
            Market.objects.filter(
                status__in=("open", "locked", "resolved", "sealed", "canceled"),
                integrity_definition__isnull=True,
            ).exists()
        )
        self.assertTrue(Market.objects.filter(slug="openai-gpt6-2026").exists())
        self.assertTrue(UserBadgeAward.objects.filter(pk=unrelated_award.pk).exists())
        self.assertTrue(UserNotification.objects.filter(pk=unrelated_notification.pk).exists())
        second = StringIO()
        call_command("purge_unsigned_markets", execute=True, backup_confirmed=True, stdout=second)
        self.assertEqual(json.loads(second.getvalue())["market_count"], 0)

    def test_open_market_reports_prediction_commitment_validity_before_sealing(self):
        market = Market.objects.get(slug="openai-gpt6-2026")
        option = market.options.order_by("display_order", "id").first()
        prediction = self.client.post(
            f"/markets/{market.slug}/predict",
            headers=self.user_headers,
            json={"option_id": option.id, "stake_amount": 25, "client_locale": "pt-br"},
        )
        self.assertEqual(prediction.status_code, 201, prediction.text)

        verification = self.client.get(f"/markets/{market.slug}/integrity/verify")

        self.assertEqual(verification.status_code, 200, verification.text)
        self.assertTrue(verification.json()["prediction_commitments_valid"])
        self.assertIsNone(verification.json()["seal_valid"])
        self.assertIsNone(verification.json()["merkle_root_valid"])

        forbidden = self.client.get(
            f"/admin/markets/{market.slug}/integrity/verify",
            headers=self.user_headers,
        )
        staff_verification = self.client.get(
            f"/admin/markets/{market.slug}/integrity/verify",
            headers=self.staff_headers,
        )
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(staff_verification.status_code, 200, staff_verification.text)
        self.assertTrue(staff_verification.json()["prediction_commitments_valid"])

    def test_prediction_without_commitment_is_detected_and_cannot_be_sealed(self):
        market = Market.objects.get(slug="openai-gpt6-2026")
        option = market.options.order_by("display_order", "id").first()
        from django.contrib.auth import get_user_model

        user_id = get_user_model().objects.get(email="integrity-user@example.com").id
        now = django_timezone.now()
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO gotrendlabs_predictions
                       (user_id,market_id,market_option_id,action_type,position_sequence,stake_amount,
                        probability_at_entry,weight_at_entry,potential_payout,status,won,created_at,updated_at)
                       VALUES (%s,%s,%s,'initial',1,10,50,1000,20,'open',NULL,%s,%s)""",
                    (user_id, market.id, option.id, now, now),
                )
        verification = self.client.get(f"/markets/{market.slug}/integrity/verify").json()
        self.assertFalse(verification["prediction_commitments_valid"])
        self.assertIn("prediction_commitment_missing", verification["errors"])

        Market.objects.filter(pk=market.pk).update(
            status="resolved",
            resolved_at=now,
            seal_due_at=now - timedelta(seconds=1),
            winning_option=option,
            resolution_timezone="UTC",
        )
        market.refresh_from_db()
        with get_connection() as connection:
            with connection.cursor() as cursor, self.assertRaises(integrity_service.IntegritySigningError):
                integrity_service.seal_market(cursor, dict(cursor.execute("SELECT * FROM gotrendlabs_markets WHERE id=%s", (market.id,)).fetchone()), sealed_at=now)

    def test_global_ledger_failure_invalidates_market_and_blocks_sealing(self):
        market, _prediction_id, due = self._resolve_due_market()
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM gotrendlabs_markets WHERE id=%s", (market.id,))
                verification = integrity_service.verify_market_integrity_records(
                    cursor,
                    cursor.fetchone(),
                    ledger_audit={"valid": False, "invalid_market_ids": set()},
                )
        self.assertFalse(verification["valid"])
        self.assertFalse(verification["ledger_chain_valid"])
        self.assertIn("ledger_chain_invalid", verification["warnings"])

        with mock.patch(
            "apps.api.backend_api.integrity_service.verify_integrity_ledger_chain",
            return_value={"valid": False, "invalid_market_ids": set()},
        ):
            sealed = seal_due_markets(now=due + timedelta(seconds=2))
        self.assertEqual(sealed["sealed"], [])
        self.assertEqual(len(sealed["failed"]), 1)
        market.refresh_from_db()
        self.assertEqual(market.status, "resolved")
        self.assertFalse(MarketSeal.objects.filter(market=market).exists())

    def test_changed_resolution_blocks_sealing(self):
        market, _prediction_id, due = self._resolve_due_market("tiktok-ban-eua-2026")
        Market.objects.filter(pk=market.pk).update(resolution_note="Resultado alterado apos a resolucao")

        sealed = seal_due_markets(now=due + timedelta(seconds=2))

        self.assertEqual(sealed["sealed"], [])
        self.assertEqual(len(sealed["failed"]), 1)
        market.refresh_from_db()
        self.assertEqual(market.status, "resolved")
        self.assertFalse(MarketSeal.objects.filter(market=market).exists())

    def test_prediction_row_tampering_is_detected_against_signed_commitment(self):
        market = Market.objects.get(slug="openai-gpt6-2026")
        option = market.options.order_by("display_order", "id").first()
        created = self.client.post(
            f"/markets/{market.slug}/predict",
            headers=self.user_headers,
            json={"option_id": option.id, "stake_amount": 25, "client_locale": "pt-br"},
        )
        self.assertEqual(created.status_code, 201, created.text)
        prediction_id = created.json()["prediction_id"]
        from apps.web.django.markets.models import Prediction

        Prediction.objects.filter(pk=prediction_id).update(stake_amount=26)
        verification = self.client.get(f"/markets/{market.slug}/integrity/verify").json()
        self.assertFalse(verification["prediction_commitments_valid"])
        self.assertIn("prediction_commitment_invalid", verification["errors"])

    def test_taxonomy_rename_preserves_definition_but_association_change_does_not(self):
        market = Market.objects.get(slug="openai-gpt6-2026")
        original_category_id = market.category_id
        MarketCategory = market.category.__class__
        MarketCategory.objects.filter(pk=original_category_id).update(name="Tecnologia renomeada")
        renamed = self.client.get(f"/markets/{market.slug}/integrity/verify").json()
        self.assertTrue(renamed["definition_matches_current"], renamed)

        replacement = MarketCategory.objects.exclude(pk=original_category_id).first()
        Market.objects.filter(pk=market.pk).update(category=replacement)
        reassociated = self.client.get(f"/markets/{market.slug}/integrity/verify").json()
        self.assertFalse(reassociated["definition_matches_current"])
        self.assertIn("definition_changed", reassociated["errors"])

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
        self.assertTrue(verification.json()["definition_matches_current"])
        self.assertTrue(verification.json()["result_matches_current"])
        self.assertTrue(verification.json()["prediction_commitments_valid"])
        self.assertEqual(verification.json()["errors"], [])
        self.assertEqual(verification.json()["warnings"], [])

        original_title = market.title
        Market.objects.filter(pk=market.pk).update(title="Título adulterado fora do domínio")
        changed_definition = self.client.get(f"/markets/{market.slug}/integrity/verify").json()
        self.assertFalse(changed_definition["valid"])
        self.assertFalse(changed_definition["definition_matches_current"])
        self.assertIn("definition_changed", changed_definition["errors"])
        Market.objects.filter(pk=market.pk).update(title=original_title)

        original_note = market.resolution_note
        Market.objects.filter(pk=market.pk).update(resolution_note="Resultado adulterado fora do domínio")
        changed_result = self.client.get(f"/markets/{market.slug}/integrity/verify").json()
        self.assertFalse(changed_result["valid"])
        self.assertFalse(changed_result["result_matches_current"])
        self.assertIn("result_changed", changed_result["errors"])
        Market.objects.filter(pk=market.pk).update(resolution_note=original_note)

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
        operational_status = self.client.get(f"/markets/{market.slug}/integrity").json()
        self.assertEqual(operational_status["status"], "seal_retry_pending")

        integrity_service._signer = healthy_signer
        retried = seal_due_markets(now=due + timedelta(seconds=3))
        self.assertEqual(len(retried["sealed"]), 1, retried)
        self.assertEqual(MarketSeal.objects.filter(market=market).count(), 1)
        self.assertGreaterEqual(PredictionCommitment.objects.filter(market=market).count(), 1)

    def test_daemon_audit_creates_one_high_alert_and_reopens_it_while_issue_persists(self):
        market = Market.objects.get(slug="openai-gpt6-2026")
        self.assertEqual(market.status, "open")
        unsigned_count = Market.objects.filter(
            status__in=("open", "locked", "resolved", "sealed", "canceled"),
            integrity_definition__isnull=True,
        ).count()
        healthy = audit_integrity_records()
        self.assertGreaterEqual(healthy["issues_detected"], unsigned_count, healthy)
        self.assertEqual(IntegrityAlert.objects.filter(issue_code="definition_missing").count(), unsigned_count)
        self.assertFalse(IntegrityAlert.objects.filter(market=market).exists())

        original_title = market.title
        Market.objects.filter(pk=market.pk).update(title="Definição adulterada para auditoria")
        first = audit_integrity_records()
        self.assertGreaterEqual(first["issues_detected"], 1, first)
        alert = IntegrityAlert.objects.get(market=market, issue_code="definition_changed")
        self.assertEqual(alert.severity, "high")
        self.assertEqual(alert.status, "pending")
        self.assertEqual(alert.occurrences, 1)

        alert.status = "reviewed"
        alert.admin_note = "Em investigação."
        alert.save(update_fields=["status", "admin_note", "updated_at"])
        repeated = audit_integrity_records()
        self.assertEqual(IntegrityAlert.objects.filter(market=market, issue_code="definition_changed").count(), 1)
        alert.refresh_from_db()
        self.assertEqual(alert.status, "pending")
        self.assertEqual(alert.occurrences, 2)
        self.assertEqual(repeated["alerts_created"], 0)
        self.assertEqual(
            AdminEvent.objects.filter(action="integrity.alert_created", entity_identifier=market.slug).count(),
            1,
        )
        Market.objects.filter(pk=market.pk).update(title=original_title)

    def test_pending_integrity_alert_overrides_positive_card_status(self):
        market = Market.objects.get(slug="openai-gpt6-2026")
        Market.objects.filter(pk=market.pk).update(title="Definicao adulterada para o card")
        audit_integrity_records()

        detail = self.client.get(f"/markets/{market.slug}")
        summary = self.client.get(f"/markets/{market.slug}/integrity")

        self.assertEqual(detail.status_code, 200, detail.text)
        self.assertEqual(detail.json()["integrity"]["status"], "verification_failed")
        self.assertEqual(summary.json()["status"], "verification_failed")

    def test_integrity_alert_is_exposed_and_reviewed_only_by_staff(self):
        market = Market.objects.get(slug="openai-gpt6-2026")
        Market.objects.filter(pk=market.pk).update(title="Definição adulterada para fila")
        audit_integrity_records()
        alert = IntegrityAlert.objects.get(market=market, issue_code="definition_changed")

        queue = self.client.get("/admin/queues", headers=self.staff_headers, params={"kind": "integrity_alert"})
        self.assertEqual(queue.status_code, 200, queue.text)
        item = next(item for item in queue.json()["items"] if item["market_slug"] == market.slug and item["issue_code"] == "definition_changed")
        self.assertEqual(item["kind"], "integrity_alert")
        self.assertEqual(item["severity"], "high")
        self.assertEqual(item["market_slug"], market.slug)
        self.assertEqual(item["occurrences"], 1)

        missing_note = self.client.post(
            f"/admin/queues/integrity_alert/{alert.id}/review",
            headers=self.staff_headers,
            json={"status": "reviewed", "note": ""},
        )
        self.assertEqual(missing_note.status_code, 422)
        reviewed = self.client.post(
            f"/admin/queues/integrity_alert/{alert.id}/review",
            headers=self.staff_headers,
            json={"status": "reviewed", "note": "Incidente encaminhado para correção append-only."},
        )
        self.assertEqual(reviewed.status_code, 200, reviewed.text)
        self.assertEqual(reviewed.json()["status"], "reviewed")

    def test_daemon_does_not_classify_verification_infrastructure_failure_as_tampering(self):
        with mock.patch(
            "apps.api.backend_api.daemon_services.verify_integrity_ledger_chain",
            side_effect=integrity_service.IntegritySigningError("public key service unavailable"),
        ):
            summary = audit_integrity_records()
        self.assertEqual(summary["scan_failures"], 1)
        self.assertEqual(summary["issues_detected"], 0)
        self.assertFalse(IntegrityAlert.objects.exists())
