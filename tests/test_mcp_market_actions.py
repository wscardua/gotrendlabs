"""MCP lifecycle contracts, authorization, settlement and transactional replay."""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from importlib import import_module
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

import httpx
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection, transaction
from django.test import SimpleTestCase, TestCase
from fastapi.testclient import TestClient
from mcp.server.auth.provider import AccessToken
from pydantic import ValidationError

from apps.api.backend_api import editorial_auth as auth, integrity_service
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.editorial_schemas import (
    SCOPES,
    ResolveMarket,
    CancelMarket,
    DeleteMarketDraft,
)
from apps.api.backend_api.main import app
from apps.mcp import server
from apps.web.django.editorial_integrations.models import (
    Integration,
    MarketActionRequest,
    Token,
)
from apps.web.django.markets.models import (
    AdminEvent,
    IntegrityLedgerEvent,
    Market,
    MarketResolutionRequest,
    Prediction,
    UserNotification,
)
from tests.test_cases import AppendOnlyTransactionTestCase
from tests import test_integrity_ledger as integrity_fixtures
from tests import test_mcp_editorial as mcp_fixtures
from tests import test_resolution_reliability as resolution_fixtures


class McpMarketActionTests(AppendOnlyTransactionTestCase):
    _register = integrity_fixtures.IntegrityLedgerIntegrationTests._register
    service_token = mcp_fixtures.McpEditorialTests.service_token
    delegate = mcp_fixtures.McpEditorialTests.delegate
    prepare = resolution_fixtures.ResolutionReliabilityTests.prepare

    def setUp(self):
        self.env = patch.dict(
            os.environ,
            {
                "GTL_MCP_ENABLED": "1",
                "GTL_MCP_WORKLOAD_SECRET": "test-workload-" + "x" * 40,
                "GTL_MCP_ISSUER": "https://issuer.example",
                "GTL_MCP_RESOURCE": "http://localhost:8002/mcp",
                **{
                    key: ""
                    for key in (
                        "FASTAPI_POSTGRES_DB",
                        "FASTAPI_POSTGRES_USER",
                        "FASTAPI_POSTGRES_PASSWORD",
                        "FASTAPI_POSTGRES_HOST",
                        "FASTAPI_POSTGRES_PORT",
                    )
                },
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)
        integrity_fixtures.IntegrityLedgerIntegrationTests.setUp(self)
        self.addCleanup(
            integrity_fixtures.IntegrityLedgerIntegrationTests.tearDown, self
        )
        self.staff = get_user_model().objects.get(email="integrity-staff@example.com")
        self.config = dict(
            name="Lifecycle",
            responsible_id=self.staff.id,
            scopes=list(SCOPES),
            expires_at=(auth.now() + timedelta(days=30)).isoformat(),
        )
        self.iid, self.agentheaders = self.integration()
        self.prepare()
        self.market.refresh_from_db()
        self.resolution = dict(
            market_id=self.market.id,
            expected_updated_at=self.market.updated_at.isoformat(),
            idempotency_key=str(uuid4()),
            winning_option_id=self.option.id,
            source_url="https://example.org/result",
            note="Resultado público conferido pelo executor",
            resolved_at=auth.now().isoformat(),
            resolution_timezone="UTC",
        )
        self.cancellation = dict(
            market_id=self.market.id,
            expected_updated_at=self.market.updated_at.isoformat(),
            expected_status="locked",
            idempotency_key=str(uuid4()),
            note="Evento cancelado pela organização",
        )

    def integration(self, scopes=None):
        config = {
            **self.config,
            "scopes": scopes if scopes is not None else list(SCOPES),
        }
        result = self.client.post(
            "/admin/agent-integrations", json=config, headers=self.staff_headers
        )
        self.assertEqual(result.status_code, 201, result.text)
        iid = result.json()["id"]
        result = self.client.post(
            f"/admin/agent-integrations/{iid}/activate",
            json={"expected_revision": 1},
            headers=self.staff_headers,
        )
        self.assertEqual(result.status_code, 200, result.text)
        result = self.client.post(
            f"/admin/agent-integrations/{iid}/credentials", headers=self.staff_headers
        )
        self.assertEqual(result.status_code, 200, result.text)
        return iid, self.delegate(self.service_token(result.json()))

    def action(self, operation, payload=None, headers=None):
        return self.client.post(
            "/integrations/editorial/markets/" + operation,
            json=payload
            or (self.resolution if operation == "resolve" else self.cancellation),
            headers=headers or self.agentheaders,
        )

    def test_resolve_replay_settles_once_with_technical_actor_and_minimal_projection(
        self,
    ):
        first = self.action("resolve")
        self.assertEqual(first.status_code, 200, first.text)
        again = self.action("resolve")
        self.assertEqual(again.status_code, 200, again.text)
        self.assertFalse(first.json()["replayed"])
        self.assertTrue(again.json()["replayed"])
        self.assertEqual(first.json()["request_id"], again.json()["request_id"])
        self.assertEqual(
            set(first.json()),
            {
                "market_id",
                "status",
                "updated_at",
                "winning_option_id",
                "resolved_at",
                "resolution_timezone",
                "request_id",
                "replayed",
            },
        )
        self.assertEqual(MarketActionRequest.objects.count(), 1)
        self.assertEqual(MarketResolutionRequest.objects.count(), 1)
        self.assertEqual(Prediction.objects.get(market=self.market).status, "resolved")
        self.assertEqual(
            IntegrityLedgerEvent.objects.filter(
                market=self.market, event_type="market_resolved"
            ).count(),
            1,
        )
        self.assertEqual(
            UserNotification.objects.filter(
                market=self.market, event_type="market_resolved"
            ).count(),
            1,
        )
        event = AdminEvent.objects.get(
            action="market.resolve", entity_identifier=self.market.slug
        )
        self.assertIsNone(event.actor_id)
        self.assertEqual(str(event.integration_id), self.iid)
        self.assertEqual(event.responsible_id, self.staff.id)
        self.assertEqual(event.request_id, first.json()["request_id"])
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT entry_type,count(*) n FROM gotrendlabs_wallet_ledger WHERE reference_type='prediction' AND reference_id IN (SELECT id::text FROM gotrendlabs_predictions WHERE market_id=%s) GROUP BY entry_type",
                (self.market.id,),
            )
            self.assertEqual(
                {r["entry_type"]: r["n"] for r in cursor.fetchall()},
                {
                    "prediction_stake_lock": 1,
                    "prediction_refund": 1,
                    "prediction_payout": 1,
                },
            )
        self.market.refresh_from_db()
        from apps.api.backend_api.daemon_services import seal_due_markets

        seal_due_markets(now=self.market.seal_due_at + timedelta(seconds=1))
        self.assertEqual(self.action("resolve").json()["status"], "sealed")
        self.assertEqual(
            self.action(
                "cancel",
                {
                    **self.cancellation,
                    "expected_updated_at": Market.objects.get(
                        pk=self.market.id
                    ).updated_at.isoformat(),
                },
            ).status_code,
            409,
        )

    def test_cancel_refunds_once_without_reputation_change(self):
        user = get_user_model().objects.get(email="integrity-user@example.com")
        before = user.reputation.reputation_score
        first = self.action("cancel")
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()["status"], "canceled")
        self.assertTrue(self.action("cancel").json()["replayed"])
        self.assertEqual(Prediction.objects.get(market=self.market).status, "canceled")
        user.refresh_from_db()
        self.assertEqual(user.reputation.reputation_score, before)
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT entry_type,sum(amount) amount,count(*) n FROM gotrendlabs_wallet_ledger WHERE reference_type='prediction' AND reference_id IN (SELECT id::text FROM gotrendlabs_predictions WHERE market_id=%s) GROUP BY entry_type",
                (self.market.id,),
            )
            rows = {r["entry_type"]: (r["amount"], r["n"]) for r in cursor.fetchall()}
            self.assertEqual(rows["prediction_refund"], (25, 1))
            self.assertNotIn("prediction_payout", rows)
        self.assertEqual(
            self.action(
                "cancel",
                {
                    **self.cancellation,
                    "idempotency_key": str(uuid4()),
                    "expected_updated_at": first.json()["updated_at"],
                },
            ).json()["detail"]["code"],
            "market_state_conflict",
        )

    def test_scope_grants_tokens_and_revocation_are_checked_even_on_replay(self):
        _, limited = self.integration(["catalog:read"])
        self.assertEqual(self.action("resolve", headers=limited).status_code, 403)
        self.assertEqual(self.action("cancel", headers=limited).status_code, 403)
        self.assertEqual(
            self.action("resolve", headers=self.staff_headers).status_code, 401
        )
        self.assertEqual(self.action("resolve").status_code, 200)
        Integration.objects.filter(pk=self.iid).update(scopes=["markets:cancel"])
        self.assertEqual(
            self.action("resolve").json()["detail"]["code"], "forbidden_scope"
        )
        Integration.objects.filter(pk=self.iid).update(
            scopes=list(SCOPES), state="paused"
        )
        self.assertEqual(
            self.action("resolve").json()["detail"]["code"], "integration_inactive"
        )
        Integration.objects.filter(pk=self.iid).update(state="revoked")
        self.assertEqual(self.action("resolve").status_code, 403)

    def test_old_access_and_internal_tokens_do_not_gain_new_scopes(self):
        iid, old = self.integration(["catalog:read"])
        Integration.objects.filter(pk=iid).update(scopes=list(SCOPES))
        self.assertEqual(self.action("cancel", headers=old).status_code, 403)
        self.assertFalse(
            Token.objects.filter(
                integration_id=iid, scopes__contains=["markets:cancel"]
            ).exists()
        )

    def test_state_version_option_and_payload_conflicts(self):
        wrong = Market.objects.exclude(pk=self.market.pk).first().options.first()
        self.assertEqual(
            self.action(
                "resolve", {**self.resolution, "winning_option_id": wrong.id}
            ).json()["detail"]["code"],
            "invalid_winning_option",
        )
        stale = (auth.now() - timedelta(days=1)).isoformat()
        self.assertEqual(
            self.action(
                "resolve", {**self.resolution, "expected_updated_at": stale}
            ).json()["detail"]["code"],
            "version_conflict",
        )
        self.assertEqual(
            self.action(
                "cancel", {**self.cancellation, "expected_status": "open"}
            ).json()["detail"]["code"],
            "market_state_conflict",
        )
        self.assertEqual(
            self.action(
                "resolve",
                {
                    **self.resolution,
                    "resolved_at": (auth.now() + timedelta(days=1)).isoformat(),
                },
            ).status_code,
            422,
        )
        self.assertEqual(self.action("resolve").status_code, 200)
        self.assertEqual(
            self.action("resolve", {**self.resolution, "note": "Outro relato"}).json()[
                "detail"
            ]["code"],
            "idempotency_conflict",
        )
        current = Market.objects.get(pk=self.market.id)
        self.assertEqual(
            self.action(
                "cancel",
                {
                    **self.cancellation,
                    "expected_updated_at": current.updated_at.isoformat(),
                },
            ).status_code,
            409,
        )
        self.assertEqual(
            self.action(
                "resolve",
                {
                    **self.resolution,
                    "idempotency_key": str(uuid4()),
                    "expected_updated_at": current.updated_at.isoformat(),
                },
            ).json()["detail"]["code"],
            "resolution_state_conflict",
        )

    def test_human_undo_remains_available_and_supersedes_mcp_receipt(self):
        self.assertEqual(self.action("resolve").status_code, 200)
        response = self.client.post(
            f"/admin/markets/{self.market.slug}/cancel",
            headers=self.staff_headers,
            json={"expected_market_id": self.market.id, "note": "Revisão humana"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "locked")
        self.assertEqual(
            self.action("resolve").json()["detail"]["code"],
            "resolution_request_superseded",
        )
        self.market.refresh_from_db()
        revised = {
            **self.resolution,
            "idempotency_key": str(uuid4()),
            "expected_updated_at": self.market.updated_at.isoformat(),
        }
        self.assertEqual(self.action("resolve", revised).status_code, 200)
        self.assertEqual(
            self.action("resolve").json()["detail"]["code"],
            "resolution_request_superseded",
        )

    def test_signing_failure_rolls_back_every_effect_and_receipt(self):
        for operation in ("resolve", "cancel"):
            with (
                self.subTest(operation=operation),
                patch.object(
                    integrity_service._signer,
                    "sign",
                    side_effect=integrity_service.IntegritySigningError("unavailable"),
                ),
            ):
                response = self.action(operation)
            self.assertEqual(response.status_code, 503, response.text)
            self.market.refresh_from_db()
            self.assertEqual(self.market.status, "locked")
            self.assertEqual(Prediction.objects.get(market=self.market).status, "open")
            self.assertFalse(MarketActionRequest.objects.exists())
            self.assertFalse(MarketResolutionRequest.objects.exists())
            self.assertFalse(
                AdminEvent.objects.filter(
                    action__in=["market.resolve", "market.cancel"]
                ).exists()
            )
        self.assertEqual(self.action("resolve").status_code, 200)

    def test_ids_and_version_read_do_not_mutate_editorial_snapshot(self):
        response = self.client.get(
            f"/integrations/editorial/markets/{self.market.id}",
            headers=self.agentheaders,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            response.json()["updated_at"],
            self.resolution["expected_updated_at"].replace("+00:00", "Z"),
        )
        self.assertIn(
            self.option.id, [option["id"] for option in response.json()["options"]]
        )
        from apps.api.backend_api.editorial_service import get_market

        with get_connection() as conn, conn.cursor() as cursor:
            snapshot = get_market(cursor, self.market.id, None)
            self.assertNotIn("id", snapshot["options"][0])
            self.assertNotIn("updated_at", snapshot)

    def test_drafts_are_only_cancelable_by_their_creator_and_public_markets_are_global(
        self,
    ):
        from apps.web.django.editorial_integrations.models import EditorialDraft

        draft = Market.objects.exclude(pk=self.market.id).first()
        Market.objects.filter(pk=draft.id).update(status="draft", published_at=None)
        draft.refresh_from_db()
        EditorialDraft.objects.create(
            market=draft,
            integration_id=self.iid,
            revision=1,
            state="preparation",
            record={},
            snapshot_hash="",
        )
        payload = dict(
            market_id=draft.id,
            expected_updated_at=draft.updated_at.isoformat(),
            expected_status="draft",
            idempotency_key=str(uuid4()),
            note="Pesquisa abandonada",
        )
        _, other = self.integration()
        self.assertEqual(self.action("cancel", payload, other).status_code, 404)
        self.assertEqual(self.action("cancel", payload).status_code, 200)
        self.assertEqual(self.action("resolve", headers=other).status_code, 200)

    def race(self, jobs):
        barrier = Barrier(len(jobs))

        def send(operation, payload, headers):
            with TestClient(app) as client:
                barrier.wait(timeout=10)
                return client.post(
                    "/integrations/editorial/markets/" + operation,
                    json=payload,
                    headers=headers,
                )

        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            pending = [pool.submit(send, *job) for job in jobs]
            return [future.result(timeout=30) for future in pending]

    def test_concurrent_identical_request_applies_once(self):
        responses = self.race([("resolve", self.resolution, self.agentheaders)] * 2)
        self.assertEqual(
            [r.status_code for r in responses], [200, 200], [r.text for r in responses]
        )
        self.assertEqual(sorted(r.json()["replayed"] for r in responses), [False, True])
        self.assertEqual(MarketActionRequest.objects.count(), 1)
        self.assertEqual(
            IntegrityLedgerEvent.objects.filter(
                market=self.market, event_type="market_resolved"
            ).count(),
            1,
        )

    def test_competing_integrations_resolve_cancel_only_one_commits(self):
        _, other = self.integration()
        responses = self.race(
            [
                ("resolve", self.resolution, self.agentheaders),
                ("cancel", self.cancellation, other),
            ]
        )
        self.assertEqual(
            sorted(r.status_code for r in responses),
            [200, 409],
            [r.text for r in responses],
        )
        self.assertEqual(MarketActionRequest.objects.count(), 1)
        self.market.refresh_from_db()
        self.assertIn(self.market.status, {"resolved", "canceled"})
        self.assertFalse(
            Prediction.objects.filter(market=self.market, status="open").exists()
        )

    def test_revocation_between_admission_and_transaction_blocks_mutation(self):
        reserve = auth.reserve_call

        def pause_after_admission(value, scope):
            result = reserve(value, scope)
            Integration.objects.filter(pk=self.iid).update(state="paused")
            return result

        with patch.object(auth, "reserve_call", side_effect=pause_after_admission):
            response = self.action("cancel")
        self.assertEqual(response.status_code, 403, response.text)
        self.market.refresh_from_db()
        self.assertEqual(self.market.status, "locked")
        self.assertFalse(MarketActionRequest.objects.exists())

    def test_revoked_credential_cannot_replay(self):
        self.assertEqual(self.action("cancel").status_code, 200)
        from apps.web.django.editorial_integrations.models import Credential

        Credential.objects.filter(integration_id=self.iid).update(revoked_at=auth.now())
        self.assertEqual(self.action("cancel").status_code, 403)

    def test_receipt_failure_rolls_back_settlement_and_human_race_has_one_winner(self):
        from apps.api.backend_api import editorial_market_actions

        with patch.object(
            editorial_market_actions,
            "_projection",
            side_effect=RuntimeError("response build failed"),
        ):
            with self.assertRaises(RuntimeError):
                self.action("resolve")
        self.market.refresh_from_db()
        self.assertEqual(self.market.status, "locked")
        self.assertFalse(MarketActionRequest.objects.exists())
        self.assertFalse(MarketResolutionRequest.objects.exists())
        self.assertEqual(Prediction.objects.get(market=self.market).status, "open")
        barrier = Barrier(2)

        def send(human):
            with TestClient(app) as client:
                barrier.wait(timeout=10)
                if human:
                    return client.post(
                        self.url, json=self.payload, headers=self.staff_headers
                    )
                return client.post(
                    "/integrations/editorial/markets/cancel",
                    json=self.cancellation,
                    headers=self.agentheaders,
                )

        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = [pool.submit(send, human) for human in (False, True)]
            responses = [future.result(timeout=30) for future in pending]
        self.assertEqual(
            sorted(r.status_code for r in responses),
            [200, 409],
            [r.text for r in responses],
        )
        self.market.refresh_from_db()
        self.assertIn(self.market.status, {"resolved", "canceled"})
        self.assertFalse(
            Prediction.objects.filter(market=self.market, status="open").exists()
        )

    def test_open_and_scheduled_markets_cancel_but_do_not_resolve(self):
        for status in ("open", "scheduled"):
            with self.subTest(status=status):
                market = (
                    Market.objects.filter(status="open")
                    .exclude(pk=self.market.id)
                    .first()
                )
                Market.objects.filter(pk=market.id).update(status=status)
                market.refresh_from_db()
                resolution = {
                    **self.resolution,
                    "market_id": market.id,
                    "expected_updated_at": market.updated_at.isoformat(),
                    "winning_option_id": market.options.first().id,
                }
                self.assertEqual(
                    self.action("resolve", resolution).json()["detail"]["code"],
                    "resolution_state_conflict",
                )
                cancellation = {
                    **self.cancellation,
                    "market_id": market.id,
                    "expected_updated_at": market.updated_at.isoformat(),
                    "expected_status": status,
                    "idempotency_key": str(uuid4()),
                }
                result = self.action("cancel", cancellation)
                self.assertEqual(result.status_code, 200, result.text)
                self.assertEqual(result.json()["status"], "canceled")

    def test_same_key_is_namespaced_between_integrations_and_conflicts_between_markets(
        self,
    ):
        self.assertEqual(self.action("resolve").status_code, 200)
        other_market = (
            Market.objects.filter(status="open").exclude(pk=self.market.id).first()
        )
        Market.objects.filter(pk=other_market.id).update(status="locked")
        other_market.refresh_from_db()
        payload = {
            **self.resolution,
            "market_id": other_market.id,
            "expected_updated_at": other_market.updated_at.isoformat(),
            "winning_option_id": other_market.options.first().id,
        }
        self.assertEqual(
            self.action("resolve", payload).json()["detail"]["code"],
            "idempotency_conflict",
        )
        _, other_headers = self.integration()
        result = self.action("resolve", payload, other_headers)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(MarketActionRequest.objects.count(), 2)
        keys = set(
            MarketResolutionRequest.objects.values_list("idempotency_key", flat=True)
        )
        self.assertEqual(len(keys), 2)

    def test_receipts_are_immutable(self):
        self.assertEqual(self.action("cancel").status_code, 200)
        for action in ("update", "delete"):
            with self.assertRaises(DatabaseError), transaction.atomic():
                if action == "update":
                    MarketActionRequest.objects.update(payload_hash="0" * 64)
                else:
                    MarketActionRequest.objects.all().delete()


class McpMarketActionContractTests(SimpleTestCase):
    def payload(self):
        return dict(
            market_id=1,
            expected_updated_at=auth.now(),
            idempotency_key=uuid4(),
            note="Conferido",
            winning_option_id=2,
            source_url="https://example.org/result",
            resolved_at=auth.now(),
            resolution_timezone="UTC",
        )

    def test_strict_schema_rejects_missing_fields_dates_urls_and_extra_powers(self):
        payload = self.payload()
        ResolveMarket(**payload)
        for field in payload:
            with self.subTest(missing=field), self.assertRaises(ValidationError):
                ResolveMarket(**{k: v for k, v in payload.items() if k != field})
        for invalid in (
            {"resolved_at": "2026-11-02T10:00:00"},
            {"expected_updated_at": "2026-11-02T10:00:00"},
            {"resolution_timezone": "Invalid/Zone"},
            {"resolved_at": "2026-11-02T10:00:00-03:00"},
            {"source_url": "file:///etc/passwd"},
            {"source_url": "https://user:password@example.org"},
            {"note": "  "},
            {"winning_option_id": 0},
            {"actor_id": 5},
            {"publish": True},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                ResolveMarket(**{**payload, **invalid})
        with self.assertRaises(ValidationError):
            CancelMarket(
                market_id=1,
                expected_updated_at=auth.now(),
                idempotency_key=uuid4(),
                note="Undo",
                expected_status="resolved",
            )

    def test_catalog_scopes_annotations_and_shared_schemas(self):
        tools = {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}
        self.assertEqual(len(tools), 21)
        for name, scope, field, model in [
            ("resolve_market", "markets:resolve", "resolution", ResolveMarket),
            ("cancel_market", "markets:cancel", "cancellation", CancelMarket),
        ]:
            self.assertEqual(server.TOOL_SCOPES[name], scope)
            self.assertTrue(tools[name].annotations.destructiveHint)
            self.assertTrue(tools[name].annotations.idempotentHint)
            self.assertFalse(tools[name].annotations.readOnlyHint)
            schema = tools[name].inputSchema["properties"][field]
            if "$ref" in schema:
                schema = tools[name].inputSchema["$defs"][
                    schema["$ref"].rsplit("/", 1)[1]
                ]
            self.assertEqual(
                set(schema["required"]), set(model.model_json_schema()["required"])
            )
            self.assertFalse(schema["additionalProperties"])
        with patch.object(
            server,
            "get_access_token",
            return_value=AccessToken(
                token="test", client_id="integration", scopes=["markets:cancel"]
            ),
        ):
            self.assertEqual(
                [t.name for t in asyncio.run(server.scoped_tools())], ["cancel_market"]
            )
        from apps.web.django.admin_ops.integration_views import (
            IntegrationForm,
            SCOPE_LABELS,
        )

        self.assertEqual(set(SCOPE_LABELS), set(SCOPES))
        # Both privileged actions must be visible with the correct individual label.
        self.assertIn(
            "markets:resolve", dict(IntegrationForm.base_fields["scopes"].choices)
        )

    def test_delete_draft_contract_is_strict_scoped_and_destructive(self):
        payload = dict(
            market_id=1,
            expected_revision=2,
            expected_updated_at=auth.now(),
            idempotency_key=uuid4(),
            note="Duplicado",
        )
        DeleteMarketDraft(**payload)
        for field in payload:
            with self.subTest(missing=field), self.assertRaises(ValidationError):
                DeleteMarketDraft(**{k: v for k, v in payload.items() if k != field})
        with self.assertRaises(ValidationError):
            DeleteMarketDraft(**payload, actor_id=1)
        tools = {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}
        tool = tools["delete_market_draft"]
        self.assertTrue(tool.annotations.destructiveHint)
        self.assertTrue(tool.annotations.idempotentHint)
        self.assertFalse(tool.annotations.readOnlyHint)
        self.assertEqual(server.TOOL_SCOPES[tool.name], "drafts:delete")
        with patch.object(
            server,
            "get_access_token",
            return_value=AccessToken(
                token="test", client_id="integration", scopes=["drafts:delete"]
            ),
        ):
            self.assertEqual(
                [t.name for t in asyncio.run(server.scoped_tools())],
                ["delete_market_draft"],
            )

    def test_transport_timeout_is_indeterminate_and_never_resends(self):
        original = httpx.AsyncClient
        calls = []

        def timeout(request):
            calls.append(request.url.path)
            raise httpx.ReadTimeout("secret detail", request=request)

        token = AccessToken(
            token="secret", client_id="integration", scopes=["markets:resolve"]
        )
        with (
            patch.object(server, "get_access_token", return_value=token),
            patch.object(server, "event"),
            patch.object(
                server.httpx,
                "AsyncClient",
                side_effect=lambda **kw: original(
                    transport=httpx.MockTransport(timeout), **kw
                ),
            ),
        ):
            with self.assertRaisesRegex(ValueError, "^operation_indeterminate$"):
                asyncio.run(server.resolve_market(ResolveMarket(**self.payload())))
        self.assertEqual(calls, ["/integrations/editorial/markets/resolve"])


class McpMarketActionAclTests(TestCase):
    def test_receipt_roles_have_only_required_privileges(self):
        migration = import_module(
            "apps.web.django.editorial_integrations.migrations.0007_marketactionrequest_and_more"
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT rolcreaterole OR rolsuper FROM pg_roles WHERE rolname=current_user"
            )
            if not cursor.fetchone()[0]:
                self.skipTest("isolated PostgreSQL role administration required")
            cursor.execute("CREATE ROLE gtl_mcp_receipt_writer NOLOGIN")
            cursor.execute("CREATE ROLE gtl_mcp_receipt_reader NOLOGIN")
        # Run install on a fresh trigger, deliberately starting with broad defaults.
        with connection.cursor() as cursor:
            cursor.execute(
                "DROP TRIGGER agent_market_requests_append_only ON gotrendlabs_agent_market_requests"
            )
            cursor.execute(
                "GRANT ALL ON gotrendlabs_agent_market_requests TO gtl_mcp_receipt_writer,gtl_mcp_receipt_reader"
            )
        with (
            patch.dict(
                os.environ,
                {
                    "FASTAPI_POSTGRES_USER": "gtl_mcp_receipt_writer",
                    "DJANGO_POSTGRES_USER": "gtl_mcp_receipt_reader",
                },
            ),
            connection.schema_editor() as editor,
        ):
            migration.install_receipt_guards(None, editor)
        with connection.cursor() as cursor:
            for role, expected in [
                ("gtl_mcp_receipt_writer", (True, True, False, False, True, False)),
                ("gtl_mcp_receipt_reader", (True, False, False, False, False, False)),
            ]:
                cursor.execute(
                    "SELECT has_table_privilege(%s,'gotrendlabs_agent_market_requests','SELECT'),has_table_privilege(%s,'gotrendlabs_agent_market_requests','INSERT'),has_table_privilege(%s,'gotrendlabs_agent_market_requests','UPDATE'),has_table_privilege(%s,'gotrendlabs_agent_market_requests','DELETE'),has_sequence_privilege(%s,'gotrendlabs_agent_market_requests_id_seq','USAGE'),has_sequence_privilege(%s,'gotrendlabs_agent_market_requests_id_seq','UPDATE')",
                    (role,) * 6,
                )
                self.assertEqual(cursor.fetchone(), expected)
