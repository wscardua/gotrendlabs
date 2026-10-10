import asyncio
import base64
import hashlib
import os
import secrets
import socket
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import connection
from fastapi.testclient import TestClient
from apps.api.backend_api.main import app
from apps.api.backend_api import editorial_auth as a, editorial_service as domain
from apps.api.backend_api.db import get_connection
from apps.web.django.accounts.models import AuthSession
from apps.web.django.markets.models import (
    Market,
    MarketCategory,
    MarketSubcategory,
    MarketEvent,
    AdminEvent,
)
from apps.web.django.editorial_integrations.models import (
    Integration,
    Credential,
    Token,
    Quota,
    Lease,
    EditorialDraft,
    EditorialRevision,
)
from apps.web.django.system_logs.models import SystemLog
from tests.test_cases import AppendOnlyTransactionTestCase


class McpEditorialTests(AppendOnlyTransactionTestCase):
    def setUp(self):
        super().setUp()
        self.env = patch.dict(
            os.environ,
            {
                "GTL_MCP_ENABLED": "1",
                "GTL_MCP_WORKLOAD_SECRET": "test-workload-" + ("x" * 40),
                "GTL_MCP_ISSUER": "https://issuer.example",
                "GTL_MCP_RESOURCE": "http://localhost:8002/mcp",
                **{
                    k: ""
                    for k in (
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
        U = get_user_model()
        self.staff = U.objects.create(
            username="@editor",
            email="editor@example.test",
            is_staff=True,
            is_active=True,
            account_status="active",
        )
        self.super = U.objects.create(
            username="@super",
            email="super@example.test",
            is_superuser=True,
            is_active=True,
            account_status="active",
        )
        self.member = U.objects.create(
            username="@member",
            email="member@example.test",
            is_active=True,
            account_status="active",
        )
        self.human = self.session(self.staff, True)
        self.superheaders = self.session(self.super, True)
        self.memberheaders = self.session(self.member, False)
        self.client = TestClient(app)
        c = MarketCategory.objects.create(name="Science", slug="science")
        s = MarketSubcategory.objects.create(category=c, name="Space", slug="space")
        e = MarketEvent.objects.create(subcategory=s, name="Mission", slug="mission")
        self.ids = (c.id, s.id, e.id)
        self.config = {
            "name": "Pilot",
            "description": "test",
            "responsible_id": self.staff.id,
            "expires_at": (a.now() + timedelta(days=89)).isoformat(),
            "scopes": list(
                __import__(
                    "apps.api.backend_api.editorial_schemas", fromlist=["SCOPES"]
                ).SCOPES
            ),
        }
        r = self.client.post(
            "/admin/agent-integrations", json=self.config, headers=self.human
        )
        self.assertEqual(r.status_code, 201, r.text)
        self.integration = r.json()
        self.iid = self.integration["id"]
        r = self.client.post(
            f"/admin/agent-integrations/{self.iid}/activate",
            json={"expected_revision": 1},
            headers=self.human,
        )
        self.assertEqual(r.status_code, 200, r.text)
        r = self.client.post(
            f"/admin/agent-integrations/{self.iid}/credentials", headers=self.human
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.credential = r.json()
        self.external = self.service_token()
        self.agentheaders = self.delegate(self.external)
        policy = domain.policy()
        self.payload = {
            "title": "Will the next mission launch?",
            "summary": "Future uncertain launch. Educational prediction.",
            "kind": "binary",
            "category_id": c.id,
            "subcategory_id": s.id,
            "event_id": e.id,
            "options": [],
            "source": "https://example.org/mission",
            "resolution_criteria": "Official announcement of launch before deadline",
            "close_at": (a.now() + timedelta(days=3))
            .astimezone(__import__("zoneinfo").ZoneInfo("America/Sao_Paulo"))
            .isoformat(),
            "close_timezone": "America/Sao_Paulo",
            "editorial_record": {
                "policy_version": policy["version"],
                "policy_hash": policy["hash"],
                "document": (
                    "CONTEXTO E DUPLICIDADE\nUncertain future event. Catalog checked.\n\n"
                    "PERGUNTA, REGRAS E PRAZOS\nOfficial launch announcement before deadline.\n\n"
                    "FONTES E EVIDÊNCIAS\nhttps://example.org/mission consulted by agent at "
                    + a.now().isoformat()
                    + ". Launch schedule pending; human verification required.\n\n"
                    "CONTINGÊNCIAS E RESPONSÁVEL\nHuman operator must monitor.\n\n"
                    "PENDÊNCIAS E CONCLUSÃO\nHuman must verify before approval."
                ),
            },
            "idempotency_key": "draft-test-key",
        }

    def session(self, user, mfa):
        value = secrets.token_urlsafe(40)
        AuthSession.objects.create(
            user=user,
            token_hash=a.digest(value),
            expires_at=a.now() + timedelta(days=1),
            mfa_verified_at=a.now() if mfa else None,
        )
        return {"Authorization": "Bearer " + value}

    def service_token(self, credential=None):
        c = credential or self.credential
        r = self.client.post(
            "/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": c["credential_id"],
                "client_secret": c["secret"],
                "resource": a.resource(),
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()["access_token"]

    def delegate(self, value):
        r = self.client.post(
            "/internal/agent-integrations/delegate",
            json={"access_token": value},
            headers={"X-MCP-Workload": os.environ["GTL_MCP_WORKLOAD_SECRET"]},
        )
        self.assertEqual(r.status_code, 200, r.text)
        return {
            "Authorization": "Bearer " + r.json()["access_token"],
            "X-MCP-Workload": os.environ["GTL_MCP_WORKLOAD_SECRET"],
        }

    def create(self, payload=None, headers=None):
        return self.client.post(
            "/integrations/editorial/drafts",
            json=payload or self.payload,
            headers=headers or self.agentheaders,
        )

    def assess(self, market_id, revision, snapshot_hash, decision="approved", document=None, headers=None):
        return self.client.post(
            f"/admin/agent-editorial-reviews/{market_id}/assessment",
            json={
                "expected_revision": revision,
                "snapshot_hash": snapshot_hash,
                "editorial_record": {
                    **self.payload["editorial_record"],
                    **({"document": document} if document is not None else {}),
                },
                "decision": decision,
                "confirmed": decision == "approved",
            },
            headers=headers or self.human,
        )

    def test_codex_registration_ignores_unknown_metadata_without_granting_permissions(
        self,
    ):
        payload = {
            "client_name": "Codex",
            "redirect_uris": ["http://127.0.0.1:51702/callback/local-client"],
            "grant_types": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_method": "none",
            "response_types": ["code"],
            "application_type": "native",
            "unknown_extension": {"scopes": ["admin:*"], "integration_id": "forged"},
        }
        r = self.client.post("/oauth/register", json=payload)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertNotIn("application_type", r.json())
        self.assertNotIn("unknown_extension", r.json())
        self.assertNotIn("access_token", r.json())
        cid = r.json()["client_id"]
        with get_connection() as c, c.cursor() as cur:
            cur.execute(
                "SELECT redirect_uris FROM gotrendlabs_agent_oauth_clients WHERE id=%s",
                (cid,),
            )
            self.assertEqual(cur.fetchone()["redirect_uris"], payload["redirect_uris"])
        for invalid in (
            {"redirect_uris": ["http://evil.example/callback"]},
            {"redirect_uris": ["https://client.example/callback#fragment"]},
            {"grant_types": ["client_credentials"]},
            {"token_endpoint_auth_method": "client_secret_post"},
            {"response_types": ["token"]},
        ):
            with self.subTest(invalid=invalid):
                denied = self.client.post(
                    "/oauth/register", json={**payload, **invalid}
                )
                self.assertEqual(denied.status_code, 422)

    def test_chatgpt_registration_omits_absent_scope_and_accepts_https_consent(self):
        callback = "https://chatgpt.com/connector_platform_oauth_redirect"
        for metadata in ({}, {"scope": "editorial:read"}):
            with self.subTest(metadata=metadata):
                r = self.client.post(
                    "/oauth/register",
                    json={
                        "client_name": "ChatGPT",
                        "redirect_uris": [callback],
                        **metadata,
                    },
                )
                self.assertEqual(r.status_code, 201, r.text)
                registered = r.json()
                self.assertNotIn(None, registered.values())
                self.assertNotIn("client_secret", registered)
                self.assertEqual(registered["token_endpoint_auth_method"], "none")
                if metadata:
                    self.assertEqual(registered["scope"], "editorial:read")
                else:
                    self.assertNotIn("scope", registered)
                params = {
                    "response_type": "code",
                    "client_id": registered["client_id"],
                    "redirect_uri": callback,
                    "scope": "editorial:read",
                    "resource": a.resource(),
                    "state": "test-chatgpt-state",
                    "code_challenge": "a" * 43,
                    "code_challenge_method": "S256",
                    "ui_locales": "pt-BR",
                }
                consent = self.client.post(
                    "/oauth/consent-info", json=params, headers=self.human
                )
                self.assertEqual(consent.status_code, 200, consent.text)
                self.assertEqual(consent.json()["redirect_uri"], callback)
                # Registration alone does not create a delegation or access token.
                self.assertNotIn("access_token", registered)

    def oauth(self):
        r = self.client.post(
            "/oauth/register",
            json={
                "client_name": "Real client",
                "application_type": "native",
                "redirect_uris": ["https://client.example/callback"],
            },
        )
        self.assertEqual(r.status_code, 201, r.text)
        cid = r.json()["client_id"]
        verifier = "z" * 64
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        params = {
            "client_id": cid,
            "redirect_uri": "https://client.example/callback",
            "response_type": "code",
            "scope": " ".join(self.config["scopes"]),
            "state": "client-state",
            "resource": a.resource(),
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        r = self.client.post("/oauth/consent-info", json=params, headers=self.human)
        self.assertEqual(r.status_code, 200, r.text)
        r = self.client.post(
            "/oauth/consent",
            json={"parameters": params, "integration_id": self.iid},
            headers=self.human,
        )
        self.assertEqual(r.status_code, 200, r.text)
        from urllib.parse import urlsplit, parse_qs

        query = parse_qs(urlsplit(r.json()["redirect"]).query)
        self.assertEqual(query["state"], ["client-state"])
        self.assertEqual(query["iss"], [a.issuer()])
        data = {
            "grant_type": "authorization_code",
            "client_id": cid,
            "redirect_uri": params["redirect_uri"],
            "code": query["code"][0],
            "code_verifier": verifier,
            "resource": a.resource(),
        }
        return cid, params, data

    def test_staff_superuser_mfa_equivalent_and_member_denied(self):
        for h in (self.human, self.superheaders):
            self.assertEqual(
                self.client.get("/admin/agent-integrations", headers=h).status_code, 200
            )
        for h in ({}, self.memberheaders, self.session(self.staff, False)):
            self.assertIn(
                self.client.get("/admin/agent-integrations", headers=h).status_code,
                (401, 403),
            )
        self.assertEqual(
            len(
                self.client.get(
                    "/admin/agent-integrations", headers=self.superheaders
                ).json()["items"]
            ),
            1,
        )

    def test_secret_once_rotation_origin_revoke_and_no_log_leak(self):
        self.assertNotEqual(
            Credential.objects.get(id=self.credential["credential_id"]).secret_hash,
            self.credential["secret"],
        )
        detail = self.client.get(
            "/admin/agent-integrations/" + self.iid, headers=self.human
        ).text
        self.assertNotIn("secret_hash", detail)
        self.assertNotIn(self.credential["secret"], detail)
        second = self.client.post(
            "/admin/agent-integrations/" + self.iid + "/credentials",
            headers=self.superheaders,
        )
        self.assertEqual(second.headers["cache-control"], "private, no-store")
        self.service_token()
        self.client.post(
            f"/admin/agent-integrations/{self.iid}/credentials/{self.credential['credential_id']}/revoke",
            headers=self.human,
        )
        self.assertEqual(
            self.client.get(
                "/integrations/editorial/policy", headers=self.agentheaders
            ).status_code,
            403,
        )
        self.assertNotIn(
            self.credential["secret"],
            " ".join(
                str(x.context) + x.message + x.stack_trace
                for x in SystemLog.objects.all()
            ),
        )

    def test_oauth_pkce_redirect_single_use_refresh_reuse(self):
        cid, params, data = self.oauth()
        bad = self.client.post("/oauth/token", data={**data, "code_verifier": "q" * 64})
        self.assertEqual(bad.status_code, 400, bad.text)
        bad = self.client.post(
            "/oauth/token",
            data={**data, "redirect_uri": "https://client.example/other"},
        )
        self.assertEqual(bad.status_code, 400, bad.text)
        r = self.client.post("/oauth/token", data=data)
        self.assertEqual(r.status_code, 200, r.text)
        tokens = r.json()
        self.assertEqual(
            self.client.get(
                "/integrations/editorial/policy",
                headers=self.delegate(tokens["access_token"]),
            ).status_code,
            200,
        )
        self.assertEqual(self.client.post("/oauth/token", data=data).status_code, 400)
        # Reusing a code revokes its family; start a fresh consent for refresh rotation.
        cid, params, data = self.oauth()
        r = self.client.post("/oauth/token", data=data)
        self.assertEqual(r.status_code, 200, r.text)
        tokens = r.json()
        refresh = {
            "grant_type": "refresh_token",
            "client_id": cid,
            "refresh_token": tokens["refresh_token"],
            "resource": a.resource(),
        }
        rotated = self.client.post("/oauth/token", data=refresh)
        self.assertEqual(rotated.status_code, 200, rotated.text)
        self.assertNotEqual(rotated.json()["refresh_token"], tokens["refresh_token"])
        self.assertEqual(
            self.client.post("/oauth/token", data=refresh).status_code, 400
        )
        r = self.client.post(
            "/internal/agent-integrations/delegate",
            json={"access_token": rotated.json()["access_token"]},
            headers={"X-MCP-Workload": os.environ["GTL_MCP_WORKLOAD_SECRET"]},
        )
        self.assertEqual(r.status_code, 403)

    def test_oauth_invalid_redirect_pkce_and_nonstaff_consent(self):
        cid, params, data = self.oauth()
        for extra in (
            {"redirect_uri": "https://evil.example"},
            {"code_challenge_method": "plain"},
            {"resource": "https://other.example/mcp"},
            {"code_challenge": ""},
        ):
            r = self.client.post(
                "/oauth/consent-info", json={**params, **extra}, headers=self.human
            )
            self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(
            self.client.post(
                "/oauth/consent-info", json=params, headers=self.memberheaders
            ).status_code,
            403,
        )

    def test_workload_without_delegation_audience_issuer_forgery(self):
        self.assertEqual(
            self.create(
                headers={"X-MCP-Workload": os.environ["GTL_MCP_WORKLOAD_SECRET"]}
            ).status_code,
            401,
        )
        self.assertEqual(
            self.create(
                headers={
                    **self.agentheaders,
                    "Authorization": "Bearer " + self.external,
                }
            ).status_code,
            401,
        )
        self.assertEqual(
            self.create(
                headers={**self.agentheaders, "X-MCP-Workload": "forged"}
            ).status_code,
            401,
        )
        Token.objects.filter(token_hash=a.digest(self.external)).update(
            issuer="https://evil.example"
        )
        self.assertEqual(
            self.client.post(
                "/internal/agent-integrations/delegate",
                json={"access_token": self.external},
                headers={"X-MCP-Workload": os.environ["GTL_MCP_WORKLOAD_SECRET"]},
            ).status_code,
            401,
        )

    def test_pause_resume_terminal_revoke_role_loss_and_transfer(self):
        self.client.post(
            f"/admin/agent-integrations/{self.iid}/pause",
            json={"expected_revision": 2},
            headers=self.human,
        )
        self.assertEqual(self.create().status_code, 403)
        self.client.post(
            f"/admin/agent-integrations/{self.iid}/activate",
            json={"expected_revision": 3},
            headers=self.human,
        )
        self.staff.is_staff = False
        self.staff.save(update_fields=["is_staff"])
        self.assertEqual(self.create().status_code, 403)
        r = self.client.post(
            f"/admin/agent-integrations/{self.iid}/transfer-responsibility",
            json={"expected_revision": 4, "responsible_id": self.super.id},
            headers=self.superheaders,
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.create().status_code, 200)
        self.client.post(
            f"/admin/agent-integrations/{self.iid}/revoke",
            json={"expected_revision": 5},
            headers=self.superheaders,
        )
        self.assertEqual(
            self.client.post(
                f"/admin/agent-integrations/{self.iid}/activate",
                json={"expected_revision": 6},
                headers=self.superheaders,
            ).status_code,
            403,
        )

    def test_create_retry_conflict_and_revoked_retry(self):
        first = self.create()
        self.assertEqual(first.status_code, 200, first.text)
        second = self.create()
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(first.json()["market_id"], second.json()["market_id"])
        self.assertTrue(second.json()["replayed"])
        self.assertEqual(Market.objects.count(), 1)
        self.assertEqual(
            AdminEvent.objects.filter(action="agent.draft.create").count(), 1
        )
        self.assertEqual(Quota.objects.get(bucket__startswith="draft:").count, 1)
        self.assertEqual(
            self.create({**self.payload, "title": "Different"}).status_code, 409
        )
        self.client.post(
            f"/admin/agent-integrations/{self.iid}/pause",
            json={"expected_revision": 2},
            headers=self.human,
        )
        self.assertEqual(self.create().status_code, 403)

    def test_invalid_taxonomy_extras_dates_options_rollback(self):
        for extra in (
            {"category_id": 999999},
            {"is_featured": True},
            {"close_at": "2026-10-08T12:00:00"},
            {"close_timezone": "Mars/Planet"},
            {"kind": "multiple", "options": [{"label": "one"}, {"label": "ONE"}]},
        ):
            r = self.create({**self.payload, **extra})
            self.assertEqual(r.status_code, 422, r.text)
        self.assertFalse(Market.objects.exists())
        self.assertFalse(Quota.objects.filter(bucket__startswith="draft:").exists())

    def test_submission_return_approval_human_edit_and_stale_versions(self):
        r = self.create()
        self.assertEqual(r.status_code, 200, r.text)
        d = r.json()
        mid = d["market_id"]
        r = self.client.post(
            f"/integrations/editorial/drafts/{mid}/submit",
            json={"expected_revision": 1, "idempotency_key": "submit-001"},
            headers=self.agentheaders,
        )
        self.assertEqual(r.status_code, 200, r.text)
        submitted = r.json()
        edit = {**self.payload, "expected_revision": 2, "idempotency_key": "update-001"}
        self.assertEqual(
            self.client.patch(
                f"/integrations/editorial/drafts/{mid}",
                json=edit,
                headers=self.agentheaders,
            ).status_code,
            409,
        )
        r = self.assess(mid, 2, submitted["snapshot_hash"])
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(
            self.client.patch(
                f"/integrations/editorial/drafts/{mid}",
                json={**edit, "expected_revision": 3},
                headers=self.agentheaders,
            ).status_code,
            409,
        )
        # Existing human editor requires the version and invalidates approval.
        human = {
            "title": "Human revised title",
            "summary": self.payload["summary"],
            "kind": "binary",
            "category": "Science",
            "subcategory": "Space",
            "event": "Mission",
            "source": self.payload["source"],
            "resolution_criteria": self.payload["resolution_criteria"],
            "close_at": self.payload["close_at"],
            "close_timezone": "America/Sao_Paulo",
            "thumb_color": "#334155",
            "options": [],
        }
        r = self.client.patch(
            "/admin/markets/" + d["slug"], json=human, headers=self.human
        )
        self.assertEqual(r.status_code, 409, r.text)
        r = self.client.patch(
            "/admin/markets/" + d["slug"],
            json={**human, "expected_revision": 4},
            headers=self.human,
        )
        self.assertEqual(r.status_code, 200, r.text)
        draft = EditorialDraft.objects.get(market_id=mid)
        self.assertEqual(draft.revision, 5)
        self.assertEqual(draft.state, "preparation")
        self.assertEqual(draft.decision, {})
        self.assertEqual(EditorialRevision.objects.filter(draft_id=mid).count(), 5)
        self.assertEqual(
            self.client.patch(
                f"/integrations/editorial/drafts/{mid}",
                json=edit,
                headers=self.agentheaders,
            ).status_code,
            409,
        )

    def test_market_projection_preserves_required_nulls(self):
        from apps.api.backend_api.editorial_schemas import MarketProjection

        mid = self.create().json()["market_id"]
        Market.objects.filter(id=mid).update(close_at=None, event_id=None)
        result = self.client.get(
            f"/integrations/editorial/markets/{mid}", headers=self.agentheaders
        )
        self.assertEqual(result.status_code, 200)
        self.assertIn("close_at", result.json())
        self.assertIn("event_id", result.json())
        projection = MarketProjection.model_validate(result.json())
        self.assertIsNone(projection.close_at)
        self.assertIsNone(projection.event_id)

    def approve_for_publication(self, created):
        mid = created["market_id"]
        submitted = self.client.post(
            f"/integrations/editorial/drafts/{mid}/submit",
            json={
                "expected_revision": created["revision"],
                "idempotency_key": f"approve-submit-{mid}",
            },
            headers=self.agentheaders,
        )
        self.assertEqual(submitted.status_code, 200, submitted.text)
        data = submitted.json()
        approved = self.assess(mid, data["revision"], data["snapshot_hash"])
        self.assertEqual(approved.status_code, 200, approved.text)
        return approved.json()

    def test_readable_slug_replay_and_title_collision(self):
        self.payload["title"] = "A missão lançará em 2026?"
        first = self.create().json()
        self.assertEqual(first["slug"], "a-missao-lancara-em-2026")
        self.assertEqual(self.create().json()["slug"], first["slug"])
        other = self.create(
            {**self.payload, "idempotency_key": "second-same-title"}
        ).json()
        self.assertEqual(other["slug"], first["slug"] + "-2")
        changed = self.client.patch(
            f"/integrations/editorial/drafts/{first['market_id']}",
            json={
                **self.payload,
                "title": "Updated title",
                "expected_revision": 1,
                "idempotency_key": "stable-slug-edit",
            },
            headers=self.agentheaders,
        )
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json()["slug"], first["slug"])

    def test_agent_publication_requires_favorable_current_review(self):
        for state in ("preparation", "in_review", "returned", "rejected"):
            with self.subTest(state=state):
                d = self.create(
                    {**self.payload, "idempotency_key": "gate-" + state}
                ).json()
                mid = d["market_id"]
                if state != "preparation":
                    submitted = self.client.post(
                        f"/integrations/editorial/drafts/{mid}/submit",
                        json={
                            "expected_revision": 1,
                            "idempotency_key": "submit-" + state,
                        },
                        headers=self.agentheaders,
                    ).json()
                    if state in ("returned", "rejected"):
                        decision = self.assess(mid, 2, submitted["snapshot_hash"], state)
                        self.assertEqual(decision.status_code, 200, decision.text)
                blocked = self.client.post(
                    "/admin/markets/" + d["slug"] + "/publish",
                    json={"note": "Must not open"},
                    headers=self.human,
                )
                self.assertEqual(blocked.status_code, 409, blocked.text)
                self.assertEqual(
                    blocked.json()["detail"]["code"], "editorial_approval_required"
                )
                self.assertEqual(Market.objects.get(id=mid).status, "draft")
                with get_connection() as c:
                    with c.cursor() as cur:
                        cur.execute(
                            "SELECT 1 FROM market_integrity_definitions WHERE market_id=%s",
                            (mid,),
                        )
                        self.assertIsNone(cur.fetchone())

    def test_stale_approval_or_content_cannot_publish(self):
        d = self.create().json()
        mid = d["market_id"]
        self.approve_for_publication(d)
        original = EditorialDraft.objects.get(market_id=mid)
        for field, value in [("snapshot_hash", "0" * 64), ("revision", 99)]:
            EditorialDraft.objects.filter(market_id=mid).update(**{field: value})
            response = self.client.post(
                "/admin/markets/" + d["slug"] + "/publish", json={}, headers=self.human
            )
            self.assertEqual(response.status_code, 409, response.text)
            EditorialDraft.objects.filter(market_id=mid).update(
                snapshot_hash=original.snapshot_hash, revision=original.revision
            )
        Market.objects.filter(id=mid).update(summary="Unreviewed content")
        self.assertEqual(
            self.client.post(
                "/admin/markets/" + d["slug"] + "/publish", json={}, headers=self.human
            ).status_code,
            409,
        )
        Market.objects.filter(id=mid).update(summary=self.payload["summary"])
        record = dict(original.record)
        record["policy_hash"] = "0" * 64
        EditorialDraft.objects.filter(market_id=mid).update(record=record)
        self.assertEqual(
            self.client.post(
                "/admin/markets/" + d["slug"] + "/publish", json={}, headers=self.human
            ).status_code,
            409,
        )

    def test_human_edit_invalidates_approval_and_blocks_publication(self):
        d = self.create().json()
        mid = d["market_id"]
        self.approve_for_publication(d)
        changed = self.client.patch(
            "/admin/markets/" + d["slug"],
            json={
                "title": self.payload["title"],
                "category": "Science",
                "subcategory": "Space",
                "event": "Mission",
                "summary": "Edited by human after review",
                "source": self.payload["source"],
                "resolution_criteria": self.payload["resolution_criteria"],
                "close_at": self.payload["close_at"],
                "close_timezone": "America/Sao_Paulo",
                "thumb_color": "#334155",
                "expected_revision": 4,
            },
            headers=self.human,
        )
        self.assertEqual(changed.status_code, 200, changed.text)
        draft = EditorialDraft.objects.get(market_id=mid)
        self.assertEqual(draft.state, "preparation")
        self.assertEqual(draft.revision, 5)
        self.assertEqual(draft.decision, {})
        blocked = self.client.post(
            "/admin/markets/" + d["slug"] + "/publish", json={}, headers=self.human
        )
        self.assertEqual(blocked.status_code, 409, blocked.text)

    def test_scheduled_agent_market_rechecks_approval_before_opening(self):
        d = self.create().json()
        Market.objects.filter(id=d["market_id"]).update(status="scheduled")
        blocked = self.client.post(
            "/admin/markets/" + d["slug"] + "/publish", json={}, headers=self.human
        )
        self.assertEqual(blocked.status_code, 409, blocked.text)
        Market.objects.filter(id=d["market_id"]).update(status="draft")
        self.approve_for_publication(d)
        Market.objects.filter(id=d["market_id"]).update(status="scheduled")
        from apps.api.backend_api.integrity_service import _EphemeralSigner

        with patch(
            "apps.api.backend_api.integrity_service.get_signer",
            return_value=_EphemeralSigner(),
        ):
            published = self.client.post(
                "/admin/markets/" + d["slug"] + "/publish", json={}, headers=self.human
            )
        self.assertEqual(published.status_code, 200, published.text)
        self.assertEqual(Market.objects.get(id=d["market_id"]).status, "open")

    def test_human_web_submission_and_stale_version(self):
        from django.test import Client
        from apps.web.django.accounts.api_client import AuthAPIError

        created = self.create().json()
        mid = created["market_id"]
        web = Client(enforce_csrf_checks=True)
        session = web.session
        session["auth_api_token"] = self.human["Authorization"][7:]
        session["auth_api_user"] = {"id": self.staff.id, "is_staff": True, "display_name": "Editor", "handle": "@editor", "preferred_language": "pt-br"}
        session.save()

        def bridge(method, path, payload=None, token=None, **kwargs):
            response = self.client.request(method, path, json=payload, headers={"Authorization": "Bearer " + token})
            if response.status_code >= 400:
                raise AuthAPIError("API error", response.status_code)
            return response.json()

        url = f"/admin-ops/agent-reviews/{mid}/"
        data = {"action": "assessment", "expected_revision": 1, "snapshot_hash": created["snapshot_hash"], "decision": "returned", "document": "PENDÊNCIAS E CONCLUSÃO\nFonte ainda não conferida. Devolver para ajustes."}
        with patch("apps.web.django.admin_ops.integration_views._request", side_effect=bridge):
            before = web.get(url)
            self.assertContains(before, "Registrar parecer humano")
            self.assertEqual(web.post(url, data).status_code, 403)
            data["csrfmiddlewaretoken"] = web.cookies["csrftoken"].value
            self.assertEqual(web.post(url, data).status_code, 302)
            saved = EditorialDraft.objects.get(market_id=mid)
            self.assertEqual(saved.state, "returned")
            self.assertEqual(saved.record["document"], data["document"])
            stale = web.post(url, data)
            self.assertContains(stale, "API error")
            self.assertContains(stale, data["document"])

    def test_single_human_assessment_direct_decision_and_atomic_rollback(self):
        import copy
        from apps.api.backend_api.integrity_service import _EphemeralSigner

        for outcome in ("approved", "returned", "rejected"):
            with self.subTest(outcome=outcome):
                created = self.create(
                    {**self.payload, "idempotency_key": "single-" + outcome}
                ).json()
                mid = created["market_id"]
                endpoint = f"/admin/agent-editorial-reviews/{mid}/assessment"
                payload = {
                    "expected_revision": 1,
                    "snapshot_hash": created["snapshot_hash"],
                    "editorial_record": self.payload["editorial_record"],
                    "decision": outcome,
                    "confirmed": outcome == "approved",
                }
                for headers in (
                    {},
                    self.memberheaders,
                    self.agentheaders,
                    self.session(self.staff, False),
                ):
                    self.assertIn(
                        self.client.post(
                            endpoint, json=payload, headers=headers
                        ).status_code,
                        (401, 403),
                    )
                result = self.client.post(endpoint, json=payload, headers=self.human)
                self.assertEqual(result.status_code, 200, result.text)
                self.assertEqual(result.json()["state"], outcome)
                self.assertEqual(result.json()["revision"], 3)
                self.assertEqual(
                    result.json()["decision"]["reviewer_id"], self.staff.id
                )
                self.assertEqual(
                    self.client.post(
                        endpoint, json=payload, headers=self.human
                    ).status_code,
                    409,
                )
                with patch(
                    "apps.api.backend_api.integrity_service.get_signer",
                    return_value=_EphemeralSigner(),
                ):
                    published = self.client.post(
                        "/admin/markets/" + created["slug"] + "/publish",
                        json={},
                        headers=self.human,
                    )
                self.assertEqual(
                    published.status_code,
                    200 if outcome == "approved" else 409,
                    published.text,
                )
        d = self.create({**self.payload, "idempotency_key": "atomic-failure"}).json()
        mid = d["market_id"]
        endpoint = f"/admin/agent-editorial-reviews/{mid}/assessment"
        record = copy.deepcopy(self.payload["editorial_record"])
        payload = {
            "expected_revision": 1,
            "snapshot_hash": d["snapshot_hash"],
            "editorial_record": record,
            "decision": "approved",
            "confirmed": True,
        }
        original_record = EditorialDraft.objects.get(market_id=mid).record
        events_before = AdminEvent.objects.count()
        for problem in ("stale_hash", "empty_document", "unconfirmed"):
            invalid = copy.deepcopy(payload)
            if problem == "stale_hash":
                invalid["snapshot_hash"] = "0" * 64
            if problem == "empty_document":
                invalid["editorial_record"]["document"] = ""
            if problem == "unconfirmed":
                invalid["confirmed"] = False
            failed = self.client.post(endpoint, json=invalid, headers=self.human)
            self.assertEqual(
                failed.status_code, 409 if problem == "stale_hash" else 422, failed.text
            )
            draft = EditorialDraft.objects.get(market_id=mid)
            self.assertEqual(draft.revision, 1)
            self.assertEqual(draft.state, "preparation")
            self.assertEqual(draft.record, original_record)
            self.assertEqual(EditorialRevision.objects.filter(draft_id=mid).count(), 1)
            self.assertEqual(AdminEvent.objects.count(), events_before)

    def test_single_review_form_no_double_attestation_or_prior_submit(self):
        from django.test import Client
        from apps.web.django.accounts.api_client import AuthAPIError

        created = self.create().json()
        mid = created["market_id"]
        web = Client(enforce_csrf_checks=True)
        session = web.session
        session["auth_api_token"] = self.human["Authorization"][7:]
        session["auth_api_user"] = {"id": self.staff.id, "is_staff": True, "display_name": "Editor", "handle": "@editor", "preferred_language": "pt-br"}
        session.save()
        calls = []

        def bridge(method, path, payload=None, token=None, **kwargs):
            calls.append((method, path))
            response = self.client.request(method, path, json=payload, headers={"Authorization": "Bearer " + token})
            if response.status_code >= 400:
                raise AuthAPIError(response.json()["detail"].get("message", "API error"), response.status_code, detail=response.json()["detail"])
            return response.json()

        url = f"/admin-ops/agent-reviews/{mid}/"
        with patch("apps.web.django.admin_ops.integration_views._request", side_effect=bridge):
            html = web.get(url).content.decode()
            self.assertEqual(html.count('name="document"'), 1)
            self.assertEqual(html.count('name="confirmed"'), 1)
            self.assertNotIn('name="verified_criteria"', html)
            self.assertNotIn('name="verified_source_indexes"', html)
            data = {"action": "assessment", "expected_revision": 1, "snapshot_hash": created["snapshot_hash"], "decision": "approved", "document": "Fontes e evidências: https://example.org/mission. Conclusão: aprovado."}
            self.assertEqual(web.post(url, data).status_code, 403)
            data["csrfmiddlewaretoken"] = web.cookies["csrftoken"].value
            failed = web.post(url, data)
            self.assertEqual(failed.status_code, 200)
            self.assertContains(failed, data["document"])
            self.assertEqual(EditorialDraft.objects.get(market_id=mid).revision, 1)
            data["confirmed"] = "yes"
            self.assertEqual(web.post(url, data).status_code, 302)
        self.assertIn(("POST", f"/admin/agent-editorial-reviews/{mid}/assessment"), calls)
        self.assertFalse(any(path.endswith("/record") or path.endswith("/decision") for _, path in calls))
        self.assertEqual(EditorialDraft.objects.get(market_id=mid).state, "approved")
        self.assertEqual(Market.objects.get(id=mid).status, "draft")

    def test_scopes_ownership_private_record_and_no_admin_authority(self):
        r = self.create()
        mid = r.json()["market_id"]
        Integration.objects.filter(id=self.iid).update(scopes=["catalog:read"])
        self.assertEqual(self.create().status_code, 403)
        self.assertEqual(
            self.client.post(
                "/admin/markets", json={}, headers=self.agentheaders
            ).status_code,
            422,
        )
        other = Integration.objects.create(
            name="Other",
            responsible=self.staff,
            expires_at=a.now() + timedelta(days=1),
            state="active",
            scopes=["catalog:read", "drafts:write"],
        )
        c = Credential.objects.create(
            integration=other,
            secret_hash=a.digest("y" * 48),
            expires_at=a.now() + timedelta(days=1),
        )
        h = self.delegate(
            self.service_token({"credential_id": str(c.id), "secret": "y" * 48})
        )
        result = self.client.get(f"/integrations/editorial/markets/{mid}", headers=h)
        self.assertEqual(result.status_code, 200)
        self.assertNotIn("editorial", result.json())
        self.assertEqual(
            self.client.patch(
                f"/integrations/editorial/drafts/{mid}",
                json={**self.payload, "expected_revision": 1},
                headers=h,
            ).status_code,
            404,
        )

    def test_persistent_quota_concurrent_last_unit_and_expired_lease(self):
        Integration.objects.filter(id=self.iid).update(drafts_per_day=1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(
                pool.map(
                    lambda n: self.create(
                        {**self.payload, "idempotency_key": "parallel-" + str(n)}
                    ),
                    [1, 2],
                )
            )
        self.assertEqual(sorted(r.status_code for r in results), [200, 429])
        self.assertEqual(Market.objects.count(), 1)
        Lease.objects.create(
            integration_id=self.iid, expires_at=a.now() - timedelta(seconds=1)
        )
        self.assertEqual(
            self.client.get(
                "/integrations/editorial/policy", headers=self.agentheaders
            ).status_code,
            200,
        )
        self.assertFalse(Lease.objects.exists())
        self.assertEqual(
            self.create(
                {**self.payload, "idempotency_key": "after-restart"}
            ).status_code,
            429,
        )

    def test_calls_scope_denials_and_reduction_remain_persistent(self):
        Integration.objects.filter(id=self.iid).update(calls_per_minute=1)
        self.assertEqual(
            self.client.get(
                "/integrations/editorial/policy", headers=self.agentheaders
            ).status_code,
            200,
        )
        r = self.client.get("/integrations/editorial/policy", headers=self.agentheaders)
        self.assertEqual(r.status_code, 429)
        self.assertIn("retry-after", r.headers)
        self.assertEqual(Quota.objects.get(bucket__startswith="call:").count, 2)

    def test_audit_failure_aborts_technical_failure_does_not(self):
        with patch(
            "apps.api.backend_api.editorial_routes.log_system_event",
            side_effect=RuntimeError("sensitive text"),
        ):
            r = self.create()
            self.assertEqual(r.status_code, 200, r.text)
        with patch(
            "apps.api.backend_api.editorial_service.record_admin_event",
            side_effect=RuntimeError("audit unavailable"),
        ):
            with self.assertRaises(RuntimeError):
                self.create({**self.payload, "idempotency_key": "audit-failure"})
        self.assertEqual(Market.objects.count(), 1)
        self.assertEqual(Quota.objects.get(bucket__startswith="draft:").count, 1)

    def test_pagination_metrics_null_filters_and_no_backend_fetch(self):
        r = self.create()
        self.assertEqual(r.status_code, 200, r.text)
        self.create({**self.payload, "idempotency_key": "second-market"})
        search = self.client.get(
            "/integrations/editorial/markets?limit=1", headers=self.agentheaders
        ).json()
        self.assertTrue(search["has_more"])
        self.assertEqual(search["coverage"], "partial")
        next_page = self.client.get(
            "/integrations/editorial/markets?limit=1&cursor=" + search["next_cursor"],
            headers=self.agentheaders,
        ).json()
        self.assertFalse(next_page["has_more"])
        signals = self.client.get(
            "/integrations/editorial/signals", headers=self.agentheaders
        )
        self.assertEqual(signals.status_code, 200, signals.text)
        self.assertIsNone(signals.json()["analytics"]["value"])
        logs = self.client.get(
            "/admin/system-logs",
            params={
                "integration_id": self.iid,
                "tool": "create_market_draft",
                "result": "completed",
            },
            headers=self.human,
        )
        self.assertEqual(logs.status_code, 200, logs.text)
        self.assertTrue(logs.json()["logs"])
        self.assertTrue(
            all(x["context"]["integration_id"] == self.iid for x in logs.json()["logs"])
        )

    def test_grants_runtime_roles_and_revision_immutability_permissions(self):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM pg_roles WHERE rolname IN ('gotrendlabs_django','gotrendlabs_fastapi')"
            )
            if cur.fetchone()[0] != 2:
                self.skipTest(
                    "dedicated runtime roles absent in this isolated database"
                )
            cur.execute(
                "SELECT has_table_privilege('gotrendlabs_django','gotrendlabs_agent_credentials','SELECT'),has_table_privilege('gotrendlabs_fastapi','gotrendlabs_agent_credentials','INSERT'),has_table_privilege('gotrendlabs_fastapi','gotrendlabs_agent_editorial_revisions','UPDATE')"
            )
            self.assertEqual(cur.fetchone(), (False, True, False))

    def test_real_streamable_mcp_client_tools_auth_and_draft(self):
        import uvicorn
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
        from apps.mcp import server as adapter

        servers = []
        threads = []

        def serve(asgi):
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
            s = uvicorn.Server(
                uvicorn.Config(asgi, log_level="critical", access_log=False)
            )
            thread = threading.Thread(target=lambda: s.run(sockets=[sock]), daemon=True)
            thread.start()
            servers.append(s)
            threads.append(thread)
            for _ in range(100):
                if s.started:
                    return port
                time.sleep(0.02)
            raise AssertionError("Server did not start")

        api_port = serve(app)
        with (
            patch.object(adapter, "API", f"http://127.0.0.1:{api_port}"),
            patch.object(adapter, "WORKLOAD", os.environ["GTL_MCP_WORKLOAD_SECRET"]),
        ):
            mcp_port = serve(adapter.app)

            async def exercise():
                expected_tools = {
                    "get_editorial_policy",
                    "get_taxonomy",
                    "search_markets",
                    "get_market",
                    "get_editorial_signals",
                    "validate_market_draft",
                    "create_market_draft",
                    "update_market_draft",
                    "submit_draft_for_review",
                    "get_draft_review",
                }
                for mode, access in [
                    ("service", self.external),
                    ("oauth", self.oauth_access()),
                ]:
                    async with streamablehttp_client(
                        f"http://127.0.0.1:{mcp_port}/mcp",
                        headers={"Authorization": "Bearer " + access},
                    ) as (read, write, _):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            listed = await session.list_tools()
                            self.assertEqual(
                                {t.name for t in listed.tools}, expected_tools
                            )
                            observed = set()

                            async def invoke(name, arguments):
                                result = await session.call_tool(name, arguments)
                                self.assertFalse(
                                    result.isError, f"{mode}/{name}: {result}"
                                )
                                self.assertIsNotNone(result.structuredContent)
                                observed.add(name)
                                print(f"MCP-PILOT {mode} {name}: OK", flush=True)
                                return result.structuredContent

                            policy = await invoke("get_editorial_policy", {})
                            self.assertEqual(
                                policy["hash"],
                                self.payload["editorial_record"]["policy_hash"],
                            )
                            self.assertTrue(policy["manual"])
                            self.assertTrue(policy["checklist"])
                            self.assertTrue(policy["record_template"])
                            self.assertEqual(len(policy["criteria"]), 11)
                            taxonomy = await invoke("get_taxonomy", {"limit": 1})
                            self.assertTrue(taxonomy["items"])
                            signals = await invoke("get_editorial_signals", {"days": 7})
                            self.assertIn("availability", signals)
                            draft = {
                                k: v
                                for k, v in self.payload.items()
                                if k != "idempotency_key"
                            }
                            valid = await invoke(
                                "validate_market_draft", {"draft": draft}
                            )
                            self.assertTrue(valid["structurally_valid"])
                            create_payload = {
                                **draft,
                                "idempotency_key": f"real-client-{mode}-create",
                            }
                            created = await invoke(
                                "create_market_draft", {"draft": create_payload}
                            )
                            replay = await invoke(
                                "create_market_draft", {"draft": create_payload}
                            )
                            self.assertEqual(replay["market_id"], created["market_id"])
                            self.assertTrue(replay["replayed"])
                            mid = created["market_id"]
                            market = await invoke("get_market", {"market_id": mid})
                            self.assertEqual(market["title"], draft["title"])
                            found = await invoke(
                                "search_markets", {"q": draft["title"], "limit": 20}
                            )
                            self.assertIn(mid, [item["id"] for item in found["items"]])
                            updated = await invoke(
                                "update_market_draft",
                                {
                                    "market_id": mid,
                                    "draft": {
                                        **draft,
                                        "title": draft["title"] + " Updated",
                                        "expected_revision": created["revision"],
                                        "idempotency_key": f"real-client-{mode}-update",
                                    },
                                },
                            )
                            self.assertGreater(updated["revision"], created["revision"])
                            submitted = await invoke(
                                "submit_draft_for_review",
                                {
                                    "market_id": mid,
                                    "submission": {
                                        "expected_revision": updated["revision"],
                                        "idempotency_key": f"real-client-{mode}-submit",
                                    },
                                },
                            )
                            self.assertEqual(submitted["editorial_status"], "in_review")
                            review = await invoke(
                                "get_draft_review", {"market_id": mid}
                            )
                            self.assertEqual(review["state"], "in_review")
                            self.assertEqual(observed, expected_tools)
                            blocked = await session.call_tool(
                                "update_market_draft",
                                {
                                    "market_id": mid,
                                    "draft": {
                                        **draft,
                                        "expected_revision": submitted["revision"],
                                        "idempotency_key": f"real-client-{mode}-blocked",
                                    },
                                },
                            )
                            self.assertTrue(blocked.isError)
                            print(
                                f"MCP-PILOT {mode} edit_in_review: DENIED_EXPECTED",
                                flush=True,
                            )
                            missing = await session.call_tool(
                                "get_market", {"market_id": 999999}
                            )
                            self.assertTrue(missing.isError)
                            print(
                                f"MCP-PILOT {mode} missing_market: DENIED_EXPECTED",
                                flush=True,
                            )

            try:
                asyncio.run(exercise())
            finally:
                for s in servers:
                    s.should_exit = True
                for t in threads:
                    t.join(5)
        self.assertEqual(Market.objects.count(), 2)

    def oauth_access(self):
        cid, params, data = self.oauth()
        r = self.client.post("/oauth/token", data=data)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()["access_token"]

    def test_revocation_wins_lock_before_mutation_and_commit_wins_before_pause(self):
        with get_connection() as c:
            with c.cursor() as cur:
                cur.execute(
                    "SELECT id FROM gotrendlabs_agent_integrations WHERE id=%s FOR UPDATE",
                    (self.iid,),
                )
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(self.create)
                    time.sleep(0.1)
                    cur.execute(
                        "UPDATE gotrendlabs_agent_integrations SET state='revoked',revision=3 WHERE id=%s",
                        (self.iid,),
                    )
                    c.commit()
                    r = future.result(10)
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Market.objects.exists())
        # Opposite ordering: a committed draft remains after subsequent pause.
        Integration.objects.filter(id=self.iid).update(state="active")
        self.assertEqual(self.create().status_code, 200)
        self.client.post(
            f"/admin/agent-integrations/{self.iid}/pause",
            json={"expected_revision": 3},
            headers=self.human,
        )
        self.assertEqual(Market.objects.count(), 1)

    def test_human_and_agent_update_same_revision_only_one_wins(self):
        d = self.create().json()
        mid = d["market_id"]
        human = {
            "title": "Human draft",
            "summary": self.payload["summary"],
            "kind": "binary",
            "category": "Science",
            "subcategory": "Space",
            "event": "Mission",
            "source": self.payload["source"],
            "resolution_criteria": self.payload["resolution_criteria"],
            "close_at": self.payload["close_at"],
            "close_timezone": "America/Sao_Paulo",
            "thumb_color": "#334155",
            "options": [],
            "expected_revision": 1,
        }
        with ThreadPoolExecutor(max_workers=2) as pool:
            f = pool.submit(
                self.client.patch,
                "/admin/markets/" + d["slug"],
                json=human,
                headers=self.human,
            )
            g = pool.submit(
                self.client.patch,
                f"/integrations/editorial/drafts/{mid}",
                json={
                    **self.payload,
                    "title": "Agent draft",
                    "expected_revision": 1,
                    "idempotency_key": "parallel-edit",
                },
                headers=self.agentheaders,
            )
            results = [f.result(15), g.result(15)]
        self.assertEqual(sorted(x.status_code for x in results), [200, 409])
        self.assertEqual(EditorialDraft.objects.get(market_id=mid).revision, 2)

    def test_publication_and_agent_edit_are_serialized_signed_definition_preserved(
        self,
    ):
        d = self.create().json()
        mid = d["market_id"]
        from apps.api.backend_api.integrity_service import _EphemeralSigner

        self.approve_for_publication(d)
        signer = _EphemeralSigner()
        with patch(
            "apps.api.backend_api.integrity_service.get_signer", return_value=signer
        ):
            with ThreadPoolExecutor(max_workers=2) as pool:
                f = pool.submit(
                    self.client.post,
                    "/admin/markets/" + d["slug"] + "/publish",
                    json={"note": "Isolated test only"},
                    headers=self.human,
                )
                g = pool.submit(
                    self.client.patch,
                    f"/integrations/editorial/drafts/{mid}",
                    json={
                        **self.payload,
                        "title": "Edited before publication",
                        "expected_revision": 3,
                        "idempotency_key": "publish-race",
                    },
                    headers=self.agentheaders,
                )
                published = f.result(20)
                edited = g.result(20)
            self.assertEqual(published.status_code, 200, published.text)
            self.assertIn(edited.status_code, (200, 409), edited.text)
            after = self.client.patch(
                f"/integrations/editorial/drafts/{mid}",
                json={
                    **self.payload,
                    "expected_revision": EditorialDraft.objects.get(
                        market_id=mid
                    ).revision,
                    "idempotency_key": "after-publication",
                },
                headers=self.agentheaders,
            )
            self.assertEqual(after.status_code, 409)
            from apps.api.backend_api.db import get_connection
            from apps.api.backend_api.integrity_service import audit_integrity_ledger

            with get_connection() as c:
                with c.cursor() as cur:
                    audit_integrity_ledger(cur, force_full=True)
            checked = self.client.get("/markets/" + d["slug"] + "/integrity/verify")
            self.assertEqual(checked.status_code, 200, checked.text)
            self.assertTrue(checked.json()["overall_valid"], checked.text)

    def test_credential_invalid_expired_absolute_grant_and_brute_force_limit(self):
        bad = {
            "grant_type": "client_credentials",
            "client_id": self.credential["credential_id"],
            "client_secret": "wrong",
            "resource": a.resource(),
        }
        self.assertEqual(self.client.post("/oauth/token", data=bad).status_code, 401)
        Credential.objects.filter(id=self.credential["credential_id"]).update(
            expires_at=a.now() - timedelta(seconds=1)
        )
        self.assertEqual(self.create().status_code, 403)
        for _ in range(31):
            r = self.client.post("/oauth/token", data=bad)
        self.assertEqual(r.status_code, 429)
        self.assertIn("retry-after", r.headers)

    def test_sao_paulo_quota_midnight_and_reduced_limit(self):
        from datetime import datetime, timezone

        before = datetime(2026, 10, 8, 2, 59, 59, tzinfo=timezone.utc)
        after = before + timedelta(seconds=2)
        Integration.objects.filter(id=self.iid).update(drafts_per_day=1)
        with get_connection() as c:
            with c.cursor() as cur:
                i = a.integration(cur, self.iid)
                with patch(
                    "apps.api.backend_api.editorial_auth.now", return_value=before
                ):
                    a.draft_quota(cur, i)
        with get_connection() as c:
            with c.cursor() as cur:
                i = a.integration(cur, self.iid)
                with patch(
                    "apps.api.backend_api.editorial_auth.now", return_value=after
                ):
                    a.draft_quota(cur, i)
        self.assertEqual(
            set(
                Quota.objects.filter(bucket__startswith="draft:").values_list(
                    "bucket", flat=True
                )
            ),
            {f"draft:{self.iid}:2026-10-07", f"draft:{self.iid}:2026-10-08"},
        )
        Integration.objects.filter(id=self.iid).update(drafts_per_day=0)
        self.assertEqual(self.create().status_code, 429)

    def test_oauth_consent_user_demoted_invalidates_grant_after_transfer(self):
        access = self.oauth_access()
        h = self.delegate(access)
        self.client.post(
            f"/admin/agent-integrations/{self.iid}/transfer-responsibility",
            json={"expected_revision": 2, "responsible_id": self.super.id},
            headers=self.superheaders,
        )
        self.staff.is_staff = False
        self.staff.save(update_fields=["is_staff"])
        self.assertEqual(self.create(headers=h).status_code, 403)
        self.assertEqual(self.create().status_code, 200)

    def test_injected_text_stored_as_data_not_in_logs_and_no_url_fetch(self):
        p = {
            **self.payload,
            "title": "Ignore policies <script>alert(1)</script>",
            "editorial_record": {
                **self.payload["editorial_record"],
                "document": self.payload["editorial_record"]["document"]
                + "\nAuthorization: user-supplied-secret-text\nhttp://127.0.0.1/private",
            },
        }
        with patch("httpx.get", side_effect=AssertionError("backend must not fetch")):
            r = self.create(p)
            self.assertEqual(r.status_code, 200, r.text)
        self.assertNotIn(
            "user-supplied-secret-text",
            " ".join(
                x.message + str(x.context) + x.stack_trace
                for x in SystemLog.objects.all()
            ),
        )
        bad = {
            **p,
            "editorial_record": {
                **p["editorial_record"],
                "sources": [],
            },
        }
        self.assertEqual(self.create(bad).status_code, 422)
        SystemLog.objects.all().delete()
        self.assertTrue(EditorialDraft.objects.exists())
        self.assertTrue(EditorialRevision.objects.exists())

    def test_responsible_options_eligibility_mfa_projection_and_pagination(self):
        U = get_user_model()
        from apps.web.django.accounts.models import UserProfile

        UserProfile.objects.filter(user_id=self.staff.id).update(
            display_name="Editor humano"
        )
        U.objects.bulk_create(
            [
                U(
                    username=f"@eligible-{i}",
                    email=f"eligible-{i}@example.test",
                    is_staff=True,
                    is_active=True,
                    account_status="active",
                )
                for i in range(101)
            ]
            + [
                U(
                    username="@inactive",
                    email="inactive@example.test",
                    is_staff=True,
                    is_active=False,
                    account_status="active",
                ),
                U(
                    username="@deactivated",
                    email="deactivated@example.test",
                    is_staff=True,
                    is_active=True,
                    account_status="deactivated",
                ),
                U(
                    username="@bot",
                    email="bot@example.test",
                    is_staff=True,
                    is_active=True,
                    account_status="active",
                    is_bot=True,
                ),
            ]
        )
        path = "/admin/agent-integration-responsibles"
        self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(
            self.client.get(path, headers=self.session(self.member, True)).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(path, headers=self.session(self.staff, False)).status_code,
            403,
        )
        result = self.client.get(path, headers=self.human)
        self.assertEqual(result.status_code, 200, result.text)
        first = result.json()
        self.assertEqual(len(first["items"]), 100)
        self.assertTrue(first["has_more"])
        second = self.client.get(
            path, params={"after": first["next_cursor"]}, headers=self.human
        ).json()
        self.assertFalse(second["has_more"])
        people = first["items"] + second["items"]
        self.assertEqual(len(people), 103)
        self.assertEqual(len({p["id"] for p in people}), 103)
        self.assertNotIn(self.member.id, [p["id"] for p in people])
        self.assertEqual(
            next(p for p in people if p["id"] == self.staff.id)["display_name"],
            "Editor humano",
        )
        self.assertTrue(
            all(set(p) == {"id", "display_name", "username"} for p in people)
        )

    def test_django_ui_csrf_secret_once_review_and_escaped_content(self):
        import re
        from django.test import Client

        web = Client(enforce_csrf_checks=True)
        session = web.session
        session["auth_api_token"] = self.human["Authorization"][7:]
        session["auth_api_user"] = {
            "id": self.staff.id,
            "is_staff": True,
            "is_superuser": False,
            "handle": "@editor",
            "display_name": "Editor",
            "preferred_language": "pt-br",
        }
        session.save()

        def bridge(method, path, payload=None, token=None, **kwargs):
            r = self.client.request(
                method,
                path,
                json=payload,
                headers={"Authorization": "Bearer " + token} if token else {},
            )
            if r.status_code >= 400:
                from apps.web.django.accounts.api_client import AuthAPIError

                raise AuthAPIError("API error", r.status_code)
            return r.json()

        with patch(
            "apps.web.django.admin_ops.integration_views._request", side_effect=bridge
        ):
            listing = web.get("/admin-ops/integrations/")
            self.assertEqual(listing.status_code, 200)
            self.assertIn("Auditoria recente", listing.content.decode())
            self.assertIn("/admin-ops/integrations/new/", listing.content.decode())
            self.assertNotIn('id="integration-settings"', listing.content.decode())
            new = web.get("/admin-ops/integrations/new/")
            self.assertEqual(new.status_code, 200)
            self.assertIn('id="integration-settings"', new.content.decode())
            page = web.get("/admin-ops/integrations/" + self.iid + "/")
            self.assertEqual(page.status_code, 200)
            self.assertIn('type="datetime-local"', page.content.decode())
            self.assertIn(
                'aria-describedby="integration-expiry-help"', page.content.decode()
            )
            self.assertNotIn("Validade com fuso", page.content.decode())
            self.assertIn('select name="responsible_id"', page.content.decode())
            self.assertIn('select name="new_responsible_id"', page.content.decode())
            self.assertNotIn("ID do responsável humano", page.content.decode())
            self.assertIn(f'value="{self.staff.id}" selected', page.content.decode())
            denied = web.post(
                "/admin-ops/integrations/" + self.iid + "/", {"action": "credentials"}
            )
            self.assertEqual(denied.status_code, 403)
            csrf = web.cookies["csrftoken"].value
            generated = web.post(
                "/admin-ops/integrations/" + self.iid + "/",
                {"action": "credentials", "csrfmiddlewaretoken": csrf},
            )
            self.assertEqual(generated.status_code, 200)
            body = generated.content.decode()
            self.assertIn("Credencial exibida uma única vez", body)
            self.assertEqual(generated["Cache-Control"], "private, no-store")
            secret = re.search(r"Segredo:?\s*<code>([^<]+)</code>", body)
            self.assertIsNotNone(secret, body[:1000])
            later = web.get("/admin-ops/integrations/" + self.iid + "/")
            self.assertNotIn(secret.group(1), later.content.decode())
            self.payload["editorial_record"]["document"] += "\n<script>alert(1)</script>"
            d = self.create().json()
            submitted = self.client.post(
                f"/integrations/editorial/drafts/{d['market_id']}/submit",
                json={"expected_revision": 1, "idempotency_key": "ui-review-submit"},
                headers=self.agentheaders,
            )
            self.assertEqual(submitted.status_code, 200, submitted.text)
            detail = web.get(f"/admin-ops/agent-reviews/{d['market_id']}/")
            self.assertEqual(detail.status_code, 200)
            review_html = detail.content.decode()
            self.assertIn(
                "só poderá ser publicado com parecer humano aprovado", review_html
            )
            self.assertIn('name="snapshot_hash"', review_html)
            self.assertIn('name="expected_revision"', review_html)
            self.assertIn('name="document"', review_html)
            self.assertIn('for="editorial-review-decision"', review_html)
            self.assertEqual(review_html.count('name="confirmed"'), 1)
            self.assertNotIn('name="verified_criteria"', review_html)
            self.assertIn("&lt;script&gt;", review_html)
            self.assertNotIn("<script>alert(1)</script>", review_html)
            Integration.objects.filter(id=self.iid).update(
                name="<script>alert(1)</script>"
            )
            escaped = web.get(
                "/admin-ops/integrations/" + self.iid + "/"
            ).content.decode()
            self.assertIn("&lt;script&gt;", escaped)
            self.assertNotIn("<script>alert(1)</script>", escaped)
            Integration.objects.filter(id=self.iid).update(name="Pilot")
            revision = Integration.objects.get(id=self.iid).revision
            invalid = web.post(
                "/admin-ops/integrations/" + self.iid + "/",
                {
                    "action": "transfer",
                    "expected_revision": revision,
                    "new_responsible_id": self.member.id,
                    "csrfmiddlewaretoken": csrf,
                },
            )
            self.assertEqual(invalid.status_code, 200)
            self.assertEqual(
                Integration.objects.get(id=self.iid).responsible_id, self.staff.id
            )
            transferred = web.post(
                "/admin-ops/integrations/" + self.iid + "/",
                {
                    "action": "transfer",
                    "expected_revision": revision,
                    "new_responsible_id": self.super.id,
                    "csrfmiddlewaretoken": csrf,
                },
            )
            self.assertEqual(transferred.status_code, 302)
            self.assertEqual(
                Integration.objects.get(id=self.iid).responsible_id, self.super.id
            )

    def test_old_policy_blocks_submission_until_document_updated(self):
        record = {**self.payload["editorial_record"], "policy_hash": "0" * 64}
        created = self.create({**self.payload, "editorial_record": record}).json()
        mid = created["market_id"]
        endpoint = f"/integrations/editorial/drafts/{mid}/submit"
        self.assertEqual(self.client.post(endpoint, json={"expected_revision": 1, "idempotency_key": "submit-outdated"}, headers=self.agentheaders).status_code, 422)
        updated = self.client.patch(
            f"/integrations/editorial/drafts/{mid}",
            json={**self.payload, "expected_revision": 1, "idempotency_key": "policy-updated"},
            headers=self.agentheaders,
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        submitted = self.client.post(endpoint, json={"expected_revision": 2, "idempotency_key": "submit-current"}, headers=self.agentheaders)
        self.assertEqual(submitted.status_code, 200, submitted.text)
        denied = self.client.post(
            f"/admin/agent-editorial-reviews/{mid}/assessment",
            json={"expected_revision": 3, "snapshot_hash": submitted.json()["snapshot_hash"], "editorial_record": self.payload["editorial_record"], "decision": "approved"},
            headers=self.human,
        )
        self.assertEqual(denied.status_code, 422, denied.text)
        self.assertEqual(EditorialDraft.objects.get(market_id=mid).state, "in_review")

    def test_ingest_auth_dedup_identity_and_invalid_uuid(self):
        event = {
            "event_id": str(uuid.uuid4()),
            "execution_id": str(uuid.uuid4()),
            "tool": "get_editorial_policy",
            "result": "completed",
        }
        path = "/internal/agent-integrations/events"
        self.assertEqual(self.client.post(path, json=event).status_code, 401)
        self.assertEqual(
            self.client.post(
                path,
                json={**event, "integration_id": self.iid},
                headers=self.agentheaders,
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                path, json={**event, "event_id": "-" * 36}, headers=self.agentheaders
            ).status_code,
            422,
        )
        first = self.client.post(path, json=event, headers=self.agentheaders)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertFalse(first.json()["duplicate"])
        self.assertTrue(
            self.client.post(path, json=event, headers=self.agentheaders).json()[
                "duplicate"
            ]
        )
        logs = SystemLog.objects.filter(
            context__execution_id=event["execution_id"], context__stage="mcp"
        )
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.get().context["integration_id"], self.iid)
        self.assertEqual(logs.get().context["authority"], "adapter_reported")

    def test_invalid_payload_counts_attempts_and_active_leases_limit(self):
        Integration.objects.filter(id=self.iid).update(calls_per_minute=1)
        self.assertEqual(
            self.create({**self.payload, "is_featured": True}).status_code, 422
        )
        self.assertEqual(
            self.client.get(
                "/integrations/editorial/policy", headers=self.agentheaders
            ).status_code,
            429,
        )
        Integration.objects.filter(id=self.iid).update(calls_per_minute=60)
        for _ in range(2):
            Lease.objects.create(
                integration_id=self.iid, expires_at=a.now() + timedelta(seconds=45)
            )
        self.assertEqual(
            self.client.get(
                "/integrations/editorial/policy", headers=self.agentheaders
            ).status_code,
            429,
        )
        Lease.objects.filter(integration_id=self.iid).update(
            expires_at=a.now() - timedelta(seconds=1)
        )
        self.assertEqual(
            self.client.get(
                "/integrations/editorial/policy", headers=self.agentheaders
            ).status_code,
            200,
        )

    def test_sdk_oauth_discovery_registration_pkce_refresh_and_scoped_tools(self):
        import subprocess
        import sys
        import uvicorn
        import httpx
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
        from mcp.client.auth import OAuthClientProvider
        from mcp.shared.auth import OAuthClientMetadata
        from urllib.parse import urlsplit, parse_qs
        from pathlib import Path

        # Fresh adapter process has no Django configuration, DB URL or DB credentials.
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        api_port = sock.getsockname()[1]
        free = socket.socket()
        free.bind(("127.0.0.1", 0))
        mcp_port = free.getsockname()[1]
        free.close()
        api_url = f"http://127.0.0.1:{api_port}"
        mcp_url = f"http://127.0.0.1:{mcp_port}/mcp"
        api = uvicorn.Server(
            uvicorn.Config(app, log_level="critical", access_log=False)
        )
        thread = threading.Thread(target=lambda: api.run(sockets=[sock]), daemon=True)
        thread.start()

        class Storage:
            tokens = None
            info = None

            async def get_tokens(self):
                return self.tokens

            async def set_tokens(self, value):
                self.tokens = value

            async def get_client_info(self):
                return self.info

            async def set_client_info(self, value):
                self.info = value

        storage = Storage()
        callback = []

        async def authorize(url):
            parameters = {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}
            for field in (
                "resource",
                "state",
                "scope",
                "redirect_uri",
                "code_challenge",
                "code_challenge_method",
            ):
                self.assertTrue(
                    parameters.get(field),
                    f"missing OAuth field: {field}; fields={list(parameters)}",
                )
            response = self.client.post(
                "/oauth/consent",
                json={"parameters": parameters, "integration_id": self.iid},
                headers=self.human,
            )
            self.assertEqual(response.status_code, 200, response.text)
            query = parse_qs(urlsplit(response.json()["redirect"]).query)
            callback[:] = [query["code"][0], query["state"][0]]

        async def receive():
            return tuple(callback)

        metadata = OAuthClientMetadata(
            redirect_uris=["http://127.0.0.1:7777/callback"],
            client_name="SDK real OAuth",
            token_endpoint_auth_method="none",
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope="editorial:read catalog:read",
        )
        auth = OAuthClientProvider(
            server_url=mcp_url,
            client_metadata=metadata,
            storage=storage,
            redirect_handler=authorize,
            callback_handler=receive,
        )
        env = {k: os.environ[k] for k in ("PATH", "HOME") if k in os.environ}
        env.update(
            GTL_MCP_ENABLED="1",
            GTL_MCP_WORKLOAD_SECRET=os.environ["GTL_MCP_WORKLOAD_SECRET"],
            GTL_MCP_RESOURCE=mcp_url,
            GTL_MCP_ISSUER=api_url,
            GTL_MCP_API_URL=api_url,
            GTL_MCP_SPOOL=str(Path(".runtime/mcp-oauth-test-spool").resolve()),
        )
        process = None
        with patch.dict(
            os.environ,
            {
                "GTL_MCP_RESOURCE": mcp_url,
                "GTL_MCP_ISSUER": api_url,
                "AUTHLIB_INSECURE_TRANSPORT": "1",
            },
        ):
            try:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "apps.mcp.server:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(mcp_port),
                        "--log-level",
                        "critical",
                        "--no-access-log",
                    ],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                for _ in range(150):
                    try:
                        if (
                            httpx.get(
                                mcp_url.rsplit("/mcp", 1)[0] + "/health", timeout=0.5
                            ).status_code
                            == 200
                        ):
                            break
                    except httpx.HTTPError:
                        time.sleep(0.02)

                async def exercise():
                    async with streamablehttp_client(mcp_url, auth=auth) as (
                        read,
                        write,
                        _,
                    ):
                        async with ClientSession(read, write) as client:
                            await client.initialize()
                            tools = await client.list_tools()
                            self.assertEqual(len(tools.tools), 10)

                            def reduce_scopes():
                                try:
                                    Integration.objects.filter(id=self.iid).update(
                                        scopes=["editorial:read", "catalog:read"]
                                    )
                                finally:
                                    # Django's thread-local connection outlives this worker.
                                    from django.db import connections

                                    connections.close_all()

                            await asyncio.to_thread(reduce_scopes)
                            tools = await client.list_tools()
                            self.assertEqual(
                                {x.name for x in tools.tools},
                                {
                                    "get_editorial_policy",
                                    "get_taxonomy",
                                    "search_markets",
                                    "get_market",
                                    "get_draft_review",
                                },
                            )
                            result = await client.call_tool("get_editorial_policy", {})
                            self.assertFalse(result.isError, str(result))
                            first = storage.tokens.refresh_token
                            auth.context.token_expiry_time = time.time() - 1
                            result = await client.call_tool("get_editorial_policy", {})
                            self.assertFalse(result.isError, str(result))
                            self.assertNotEqual(first, storage.tokens.refresh_token)

                asyncio.run(exercise())
            finally:
                if process:
                    process.terminate()
                    process.wait(timeout=10)
                api.should_exit = True
                thread.join(5)

    def create_human_market(self, slug="human-editorial", **overrides):
        payload = {
            "title": "Human-origin question",
            "slug": slug,
            "kind": "binary",
            "category": "Science",
            "subcategory": "Space",
            "event": "Mission",
            "summary": self.payload["summary"],
            "source": self.payload["source"],
            "resolution_criteria": self.payload["resolution_criteria"],
            "close_at": self.payload["close_at"],
            "close_timezone": "America/Sao_Paulo",
            "thumb_color": "#334155",
            **overrides,
        }
        r = self.client.post("/admin/markets", json=payload, headers=self.human)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json(), payload

    def assess_human_market(self, market, **overrides):
        d = EditorialDraft.objects.get(market_id=market["editorial_market_id"])
        r = self.client.post(
            f"/admin/agent-editorial-reviews/{d.market_id}/assessment",
            json={
                "expected_revision": d.revision,
                "snapshot_hash": d.snapshot_hash,
                "editorial_record": self.payload["editorial_record"],
                "decision": "approved",
                "confirmed": True,
                **overrides,
            },
            headers=self.human,
        )
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_universal_human_creation_review_gate_origin_and_edit_invalidation(self):
        m, payload = self.create_human_market()
        mid = m["editorial_market_id"]
        self.assertEqual(m["editorial_origin"], "human")
        self.assertIsNone(EditorialDraft.objects.get(market_id=mid).integration_id)
        self.assertEqual(m["editorial_status"], "preparation")
        url = "/admin/markets/" + m["slug"] + "/publish"
        for decision in (None, "returned", "rejected"):
            if decision:
                self.assess_human_market(m, decision=decision)
            blocked = self.client.post(url, json={}, headers=self.human)
            self.assertEqual(blocked.status_code, 409, blocked.text)
            self.assertEqual(
                blocked.json()["detail"]["code"], "editorial_approval_required"
            )
        approved = self.assess_human_market(m)
        decision = EditorialDraft.objects.get(market_id=mid).decision
        self.assertTrue(decision["global_publication_gate"])
        self.assertEqual(decision["publication_gate_scope"], "all_markets")
        stale = self.client.patch(
            "/admin/markets/" + m["slug"],
            json={**payload, "expected_revision": 1},
            headers=self.human,
        )
        self.assertEqual(stale.status_code, 409)
        changed = self.client.patch(
            "/admin/markets/" + m["slug"],
            json={
                **payload,
                "summary": "New human content",
                "expected_revision": approved["revision"],
            },
            headers=self.human,
        )
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(
            self.client.post(url, json={}, headers=self.human).status_code, 409
        )
        self.assess_human_market(m)
        from apps.api.backend_api.integrity_service import _EphemeralSigner

        with patch(
            "apps.api.backend_api.integrity_service.get_signer",
            return_value=_EphemeralSigner(),
        ):
            result = self.client.post(url, json={}, headers=self.human)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["status"], "open")
        # Human legacy/active reviews do not unpublish or mutate market content.
        self.assess_human_market(m)
        self.assertEqual(Market.objects.get(id=mid).status, "open")
        self.assertEqual(
            self.client.get(
                f"/integrations/editorial/drafts/{mid}/review",
                headers=self.agentheaders,
            ).status_code,
            404,
        )

    def test_publication_closure_gate_automatic_manual_future_timezone_and_hash(self):
        from apps.api.backend_api.integrity_service import _EphemeralSigner

        for automatic in (True, False):
            m, payload = self.create_human_market(
                "closure-" + str(automatic), auto_close_enabled=automatic
            )
            mid = m["editorial_market_id"]
            self.assess_human_market(m)
            original = Market.objects.get(id=mid)
            for value in (None, a.now() - timedelta(seconds=1)):
                Market.objects.filter(id=mid).update(close_at=value)
                blocked = self.client.post(
                    "/admin/markets/" + m["slug"] + "/publish",
                    json={},
                    headers=self.human,
                )
                self.assertEqual(blocked.status_code, 422, blocked.text)
                self.assertEqual(
                    blocked.json()["detail"]["code"], "closure_configuration_invalid"
                )
                self.assertEqual(Market.objects.get(id=mid).status, "draft")
                from django.db import connection

                with connection.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM market_integrity_definitions WHERE market_id=%s",
                        [mid],
                    )
                    self.assertIsNone(cur.fetchone())
            Market.objects.filter(id=mid).update(
                close_at=original.close_at, close_timezone="Invalid/Zone"
            )
            self.assertEqual(
                self.client.post(
                    "/admin/markets/" + m["slug"] + "/publish",
                    json={},
                    headers=self.human,
                ).status_code,
                422,
            )
            Market.objects.filter(id=mid).update(close_timezone=original.close_timezone)
            # A closure mode altered outside the reviewed version must also fail.
            Market.objects.filter(id=mid).update(auto_close_enabled=not automatic)
            self.assertEqual(
                self.client.post(
                    "/admin/markets/" + m["slug"] + "/publish",
                    json={},
                    headers=self.human,
                ).status_code,
                409,
            )
            Market.objects.filter(id=mid).update(auto_close_enabled=automatic)
            with patch(
                "apps.api.backend_api.integrity_service.get_signer",
                return_value=_EphemeralSigner(),
            ):
                published = self.client.post(
                    "/admin/markets/" + m["slug"] + "/publish",
                    json={},
                    headers=self.human,
                )
            self.assertEqual(published.status_code, 200, published.text)
            if not automatic:
                locked = self.client.post(
                    "/admin/markets/" + m["slug"] + "/lock",
                    json={"note": "Manual closure in isolated test"},
                    headers=self.human,
                )
                self.assertEqual(locked.status_code, 200, locked.text)
                self.assertEqual(locked.json()["status"], "locked")

    def test_universal_migration_backfills_existing_market_without_faking_approval(
        self,
    ):
        import importlib
        from django.apps import apps
        from django.db import connection

        # Fixtures bypass the creation service: equivalent to pre-migration legacy.
        legacy = Market.objects.create(
            slug="legacy-review",
            title="Legacy published",
            status="open",
            category_id=self.payload["category_id"],
            subcategory_id=self.payload["subcategory_id"],
            event_id=self.payload["event_id"],
        )
        before = Market.objects.get(id=legacy.id)
        migration = importlib.import_module(
            "apps.web.django.editorial_integrations.migrations.0003_universal_editorial"
        )
        with __import__("django.db", fromlist=["transaction"]).transaction.atomic():
            migration.backfill(apps, type("Schema", (), {"connection": connection})())
        record = EditorialDraft.objects.get(market_id=legacy.id)
        self.assertEqual(record.state, "preparation")
        self.assertEqual(record.decision, {})
        self.assertIsNone(record.integration_id)
        self.assertEqual(Market.objects.get(id=legacy.id).status, before.status)
        self.assertEqual(
            EditorialRevision.objects.filter(draft_id=legacy.id).count(), 1
        )
        with __import__("django.db", fromlist=["transaction"]).transaction.atomic():
            migration.backfill(apps, type("Schema", (), {"connection": connection})())
        self.assertEqual(
            EditorialRevision.objects.filter(draft_id=legacy.id).count(), 1
        )
        detail = self.client.get(
            f"/admin/agent-editorial-reviews/{legacy.id}", headers=self.human
        )
        self.assertEqual(detail.status_code, 200, detail.text)
        self.assertEqual(detail.json()["publication_gate_scope"], "all_markets")

    def test_human_web_review_adds_verified_source_and_preserves_failed_input(self):
        from django.test import Client
        from apps.web.django.accounts.api_client import AuthAPIError

        market, _ = self.create_human_market("human-web-document")
        mid = market["editorial_market_id"]
        draft = EditorialDraft.objects.get(market_id=mid)
        web = Client(enforce_csrf_checks=True)
        session = web.session
        session["auth_api_token"] = self.human["Authorization"][7:]
        session["auth_api_user"] = {"id": self.staff.id, "is_staff": True, "display_name": "Editor", "handle": "@editor", "preferred_language": "pt-br"}
        session.save()

        def bridge(method, path, payload=None, token=None, **kwargs):
            response = self.client.request(method, path, json=payload, headers={"Authorization": "Bearer " + token})
            if response.status_code >= 400:
                detail = response.json()["detail"]
                raise AuthAPIError(detail.get("message", "API error") if isinstance(detail, dict) else str(detail), response.status_code, detail=detail)
            return response.json()

        url = f"/admin-ops/agent-reviews/{mid}/"
        data = {"action": "assessment", "expected_revision": 1, "snapshot_hash": draft.snapshot_hash, "decision": "approved", "document": "Fonte consultada: https://example.org/mission em 2026-10-10. Conclusão: aprovado."}
        with patch("apps.web.django.admin_ops.integration_views._request", side_effect=bridge):
            before = web.get(url)
            self.assertContains(before, 'name="document"')
            self.assertContains(before, 'name="confirmed"')
            data["csrfmiddlewaretoken"] = web.cookies["csrftoken"].value
            failed = web.post(url, data)
            self.assertEqual(failed.status_code, 200)
            self.assertContains(failed, data["document"])
            self.assertEqual(EditorialDraft.objects.get(market_id=mid).revision, 1)
            data["confirmed"] = "yes"
            success = web.post(url, data)
            self.assertEqual(success.status_code, 302)
        saved = EditorialDraft.objects.get(market_id=mid)
        self.assertEqual(saved.state, "approved")
        self.assertEqual(saved.record["document"], data["document"])
        self.assertTrue(saved.decision["confirmed"])
        self.assertEqual(Market.objects.get(id=mid).status, "draft")

    def test_document_review_requires_human_confirmation(self):
        from copy import deepcopy

        record = {
            "policy_version": domain.policy()["version"],
            "policy_hash": domain.policy()["hash"],
            "document": "CONTEXTO E DUPLICIDADE\nEvento futuro.\n\nFONTES E EVIDÊNCIAS\nhttps://example.org/mission consultada pelo agente.\n\nPENDÊNCIAS E CONCLUSÃO\nHumano deve conferir.",
        }
        draft = deepcopy(self.payload)
        draft["idempotency_key"] = "document-review-create"
        draft["editorial_record"] = record
        mixed = deepcopy(draft)
        mixed["editorial_record"]["justification"] = "second source of truth"
        self.assertEqual(self.create(mixed).status_code, 422)
        created = self.create(draft)
        self.assertEqual(created.status_code, 200, created.text)
        mid = created.json()["market_id"]
        updated_document = record["document"] + "\nConsulta complementar registrada."
        updated = deepcopy(draft)
        updated["expected_revision"] = 1
        updated["idempotency_key"] = "document-review-update"
        updated["editorial_record"]["document"] = updated_document
        changed = self.client.patch(
            f"/integrations/editorial/drafts/{mid}", json=updated, headers=self.agentheaders
        )
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json()["revision"], 2)
        own_market = self.client.get(
            f"/integrations/editorial/markets/{mid}", headers=self.agentheaders
        )
        self.assertEqual(own_market.status_code, 200, own_market.text)
        self.assertEqual(
            own_market.json()["editorial"]["record"]["document"], updated_document
        )
        record["document"] = updated_document
        submitted = self.client.post(
            f"/integrations/editorial/drafts/{mid}/submit",
            json={"expected_revision": 2, "idempotency_key": "document-review-submit"},
            headers=self.agentheaders,
        )
        self.assertEqual(submitted.status_code, 200, submitted.text)
        current = self.client.get(f"/admin/agent-editorial-reviews/{mid}", headers=self.human).json()
        self.assertEqual(
            self.client.patch(f"/admin/agent-editorial-reviews/{mid}/record", json={}, headers=self.human).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(f"/admin/agent-editorial-reviews/{mid}/decision", json={}, headers=self.human).status_code,
            404,
        )
        assessment = {
            "expected_revision": current["draft"]["revision"],
            "snapshot_hash": current["draft"]["snapshot_hash"],
            "decision": "approved",
            "editorial_record": record,
        }
        url = f"/admin/agent-editorial-reviews/{mid}/assessment"
        denied = self.client.post(url, json=assessment, headers=self.human)
        self.assertEqual(denied.status_code, 422, denied.text)
        self.assertEqual(EditorialDraft.objects.get(market_id=mid).revision, 3)
        assessment["confirmed"] = True
        accepted = self.client.post(url, json=assessment, headers=self.human)
        self.assertEqual(accepted.status_code, 200, accepted.text)
        saved = EditorialDraft.objects.get(market_id=mid)
        self.assertEqual(saved.record["document"], record["document"])
        self.assertTrue(saved.decision["confirmed"])
        self.assertEqual(saved.state, "approved")
        with get_connection() as connection, connection.cursor() as cursor:
            domain.require_publication_approval(cursor, mid)
        self.assertEqual(self.client.post(url, json=assessment, headers=self.human).status_code, 409)

    def test_policy_cannot_be_silently_stamped_on_unchanged_document(self):
        stale_record = {**self.payload["editorial_record"], "policy_hash": "0" * 64}
        created = self.create({**self.payload, "editorial_record": stale_record}).json()
        current_record = self.payload["editorial_record"]
        endpoint = f"/admin/agent-editorial-reviews/{created['market_id']}/assessment"
        payload = {
            "expected_revision": 1,
            "snapshot_hash": created["snapshot_hash"],
            "decision": "approved",
            "confirmed": True,
            "editorial_record": current_record,
        }
        unchanged = self.client.post(endpoint, json=payload, headers=self.human)
        self.assertEqual(unchanged.status_code, 422, unchanged.text)
        self.assertEqual(EditorialDraft.objects.get(market_id=created["market_id"]).revision, 1)
        payload["editorial_record"] = {
            **current_record,
            "document": current_record["document"] + "\nPolítica atual relida pelo revisor.",
        }
        revised = self.client.post(endpoint, json=payload, headers=self.human)
        self.assertEqual(revised.status_code, 200, revised.text)

    def test_one_time_migration_preserves_source_and_declared_gap(self):
        from importlib import import_module
        from types import SimpleNamespace

        migration = import_module(
            "apps.web.django.editorial_integrations.migrations.0004_single_editorial_document"
        )
        old = {
            "justification": "Evento futuro.",
            "search_coverage": "Busca parcial.",
            "sources": [{"url": "https://example.org/original", "purpose": "resolution", "consulted_at": "2026-10-10T10:00:00+00:00", "excerpt": "Trecho original"}],
            "evidence": [{"criterion_id": "E06", "status": "pending", "evidence": "A fonte não abriu.", "source_indexes": [0]}],
            "gaps": "Conferir fonte alternativa antes da aprovação.",
        }
        market = SimpleNamespace(
            title="Pergunta", summary="Resumo", resolution_criteria="Critério",
            close_at="2026-10-11T10:00:00+00:00", close_timezone="UTC",
            source="https://example.org/market",
        )
        document = migration.document_from_record(old, market, [])
        for text in (
            "https://example.org/original", "https://example.org/market",
            "Trecho original", "A fonte não abriu.",
            "Conferir fonte alternativa antes da aprovação.",
        ):
            self.assertIn(text, document)

    def test_document_return_and_reject_do_not_require_approval_confirmation(self):
        from copy import deepcopy

        draft = deepcopy(self.payload)
        draft["idempotency_key"] = "document-return-create"
        draft["editorial_record"] = {
            "policy_version": domain.policy()["version"],
            "policy_hash": domain.policy()["hash"],
            "document": "PENDÊNCIAS E CONCLUSÃO\nFonte indisponível; devolver para nova pesquisa.",
        }
        created = self.create(draft)
        self.assertEqual(created.status_code, 200, created.text)
        mid = created.json()["market_id"]
        url = f"/admin/agent-editorial-reviews/{mid}/assessment"
        returned = self.client.post(url, json={
            "expected_revision": 1,
            "snapshot_hash": created.json()["snapshot_hash"],
            "decision": "returned",
            "editorial_record": draft["editorial_record"],
        }, headers=self.human)
        self.assertEqual(returned.status_code, 200, returned.text)
        self.assertFalse(returned.json()["decision"]["confirmed"])
        self.assertEqual(EditorialDraft.objects.get(market_id=mid).state, "returned")
        changed = deepcopy(draft)
        changed["expected_revision"] = returned.json()["revision"]
        changed["idempotency_key"] = "document-return-update"
        changed["editorial_record"]["document"] = "PENDÊNCIAS E CONCLUSÃO\nEvento impossível de apurar; rejeitar."
        updated = self.client.patch(f"/integrations/editorial/drafts/{mid}", json=changed, headers=self.agentheaders)
        self.assertEqual(updated.status_code, 200, updated.text)
        rejected = self.client.post(url, json={
            "expected_revision": updated.json()["revision"],
            "snapshot_hash": updated.json()["snapshot_hash"],
            "decision": "rejected",
            "editorial_record": changed["editorial_record"],
        }, headers=self.human)
        self.assertEqual(rejected.status_code, 200, rejected.text)
        self.assertEqual(EditorialDraft.objects.get(market_id=mid).state, "rejected")
