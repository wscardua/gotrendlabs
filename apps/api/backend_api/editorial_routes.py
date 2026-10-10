"""Human management, OAuth and restricted editorial API. No staff impersonation."""

import secrets
import uuid
from contextlib import contextmanager
from datetime import timedelta, datetime
from typing import Literal
from urllib.parse import urlencode, parse_qsl
from authlib.oauth2.rfc6749 import OAuth2Error
from fastapi import APIRouter, Header, Request, Response, Query
from fastapi.responses import JSONResponse, RedirectResponse
from psycopg.types.json import Jsonb
from apps.api.backend_api.db import get_connection
from apps.api.backend_api import editorial_auth as a, editorial_service as domain
from apps.api.backend_api.editorial_schemas import (
    HumanEditorialAssessment,
    HumanEditorialRecord,
    ResponsibleOptions,
    PolicyResponse,
    TaxonomyResponse,
    SearchResponse,
    MarketProjection,
    SignalsResponse,
    ValidationResponse,
    MutationResponse,
    ReviewResponse,
    SCOPES,
    Strict,
    IntegrationConfig,
    Transfer,
    RevisionAction,
    OAuthRegistration,
    Delegation,
    ToolEvent,
    Draft,
    CreateDraft,
    UpdateDraft,
    SubmitDraft,
    ReviewDecision,
)
from apps.api.backend_api.editorial_oauth import Server
from apps.api.backend_api.admin_events import record_admin_event
from apps.api.backend_api.editorial_context import request_context
from apps.web.django.system_logs.services import log_system_event

router = APIRouter(tags=["editorial-integrations"])


def staff(cursor, authorization):
    from apps.api.backend_api.main import _current_staff_user

    return _current_staff_user(cursor, authorization)


def admin_event(cursor, user, action, identifier):
    record_admin_event(
        cursor,
        user["id"],
        action,
        "agent_integration",
        str(identifier),
        integration_id=identifier,
    )


def check_version(row, expected):
    if row["revision"] != expected:
        a.fail("version_conflict", 409)


def public_row(row):
    return {
        k: v
        for k, v in row.items()
        if k not in ("secret_hash", "token_hash", "metadata")
    }


def technical(t, tool, result, request_id, execution_id="api", stage="api"):
    if execution_id == "api":
        execution_id = request_context.get().get("execution_id", "")
    # Messages are fixed; never copy model text, HTTP payloads or exception text.
    try:
        log_system_event(
            source="fastapi",
            logger_name="editorial",
            event_type="mcp.tool." + result,
            message="Editorial tool " + result,
            request_id=request_id,
            level="INFO" if result == "completed" else "WARNING",
            context={
                "integration_id": str(t["integration_id"]) if t else None,
                "grant_id": str(t["grant_id"]) if t and t["grant_id"] else None,
                "credential_id": str(t["credential_id"])
                if t and t["credential_id"]
                else None,
                "tool": tool,
                "result": result,
                "execution_id": execution_id,
                "stage": stage,
                "authority": "backend" if stage == "api" else "adapter_reported",
            },
        )
    except Exception:
        pass


@contextmanager
def agent(authorization, workload_secret, scope, tool):
    a.workload(workload_secret)
    value = a.bearer(authorization)
    request_id = request_context.get().get("request_id") or uuid.uuid4().hex
    t = None
    lease = None
    try:
        t, lease = a.reserve_call(value, scope)
        technical(t, tool, "started", request_id)
        with get_connection() as c:
            with c.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout = '15s'")
                cur.execute("SET LOCAL lock_timeout = '5s'")
                current = a.validate(cur, value, a.api_audience(), "internal")
                if scope not in current["scopes"]:
                    a.fail("forbidden_scope")
                yield cur, current, request_id
    except Exception as exc:
        t = t or getattr(exc, "editorial_actor", None)
        result = (
            "denied"
            if getattr(exc, "status_code", 500) in (401, 403, 429)
            else "failed"
        )
        technical(t, tool, result, request_id)
        raise
    else:
        technical(t, tool, "completed", request_id)
    finally:
        if lease:
            try:
                a.release_call(lease)
            except Exception:
                pass  # lease expiry recovers after API/DB failure


@router.get("/admin/agent-integration-responsibles", response_model=ResponsibleOptions)
def integration_responsibles(
    authorization: str = Header(default=""), after: int = Query(0, ge=0)
):
    with get_connection() as c:
        with c.cursor() as cur:
            staff(cur, authorization)
            cur.execute(
                """SELECT u.id, u.username,
                   COALESCE(NULLIF(trim(p.display_name), ''), NULLIF(trim(u.first_name), ''), u.username) AS display_name
                   FROM gotrendlabs_users u
                   LEFT JOIN gotrendlabs_user_profiles p ON p.user_id=u.id
                   WHERE u.id>%s AND u.is_active AND u.account_status='active'
                     AND (u.is_staff OR u.is_superuser) AND NOT u.is_bot
                   ORDER BY u.id LIMIT 101""",
                (after,),
            )
            rows = cur.fetchall()
            return {
                "items": rows[:100],
                "has_more": len(rows) > 100,
                "next_cursor": rows[99]["id"] if len(rows) > 100 else None,
            }


@router.get("/admin/agent-integrations")
def list_integrations(
    authorization: str = Header(default=""), after: int = Query(0, ge=0)
):
    with get_connection() as c:
        with c.cursor() as cur:
            staff(cur, authorization)
            cur.execute(
                "SELECT * FROM gotrendlabs_agent_integrations ORDER BY created_at,id LIMIT 101 OFFSET %s",
                (after,),
            )
            rows = cur.fetchall()
            return {
                "items": rows[:100],
                "has_more": len(rows) > 100,
                "next_cursor": str(after + 100) if len(rows) > 100 else None,
            }


@router.post("/admin/agent-integrations", status_code=201)
def create_integration(
    payload: IntegrationConfig, authorization: str = Header(default="")
):
    with get_connection() as c:
        with c.cursor() as cur:
            user = staff(cur, authorization)
            a.eligible(cur, payload.responsible_id)
            if payload.expires_at <= a.now():
                a.fail("validation_failed", 422)
            identifier = uuid.uuid4()
            cur.execute(
                """INSERT INTO gotrendlabs_agent_integrations(id,name,description,responsible_id,state,expires_at,scopes,drafts_per_day,calls_per_minute,concurrent_calls,revision,created_at,last_used_at)
              VALUES(%s,%s,%s,%s,'paused',%s,%s,%s,%s,%s,1,%s,NULL) RETURNING *""",
                (
                    identifier,
                    payload.name,
                    payload.description,
                    payload.responsible_id,
                    payload.expires_at,
                    Jsonb(payload.scopes),
                    payload.drafts_per_day,
                    payload.calls_per_minute,
                    payload.concurrent_calls,
                    a.now(),
                ),
            )
            row = cur.fetchone()
            admin_event(cur, user, "agent.integration.create", identifier)
            return row


@router.get("/admin/agent-integrations/{identifier}")
def integration_detail(identifier: uuid.UUID, authorization: str = Header(default="")):
    with get_connection() as c:
        with c.cursor() as cur:
            staff(cur, authorization)
            row = a.integration(cur, identifier, False)
            for key, table in [
                ("credentials", "credentials"),
                ("connections", "grants"),
            ]:
                cur.execute(
                    f"SELECT * FROM gotrendlabs_agent_{table} WHERE integration_id=%s ORDER BY created_at DESC LIMIT 101",
                    (identifier,),
                )
                items = cur.fetchall()
                row[key] = [public_row(x) for x in items[:100]]
                row[key + "_has_more"] = len(items) > 100
            row["effective_state"] = (
                "expired"
                if row["state"] != "revoked" and row["expires_at"] <= a.now()
                else row["state"]
            )
            return row


@router.patch("/admin/agent-integrations/{identifier}")
def edit_integration(
    identifier: uuid.UUID,
    payload: IntegrationConfig,
    authorization: str = Header(default=""),
):
    with get_connection() as c:
        with c.cursor() as cur:
            user = staff(cur, authorization)
            i = a.integration(cur, identifier, False)
            check_version(i, payload.expected_revision)
            if i["state"] == "revoked":
                a.fail("integration_inactive")
            if payload.responsible_id != i["responsible_id"]:
                a.fail("validation_failed", 422)
            if payload.expires_at <= a.now():
                a.fail("validation_failed", 422)
            cur.execute(
                """UPDATE gotrendlabs_agent_integrations SET name=%s,description=%s,expires_at=%s,scopes=%s,drafts_per_day=%s,calls_per_minute=%s,concurrent_calls=%s,revision=revision+1 WHERE id=%s RETURNING *""",
                (
                    payload.name,
                    payload.description,
                    payload.expires_at,
                    Jsonb(payload.scopes),
                    payload.drafts_per_day,
                    payload.calls_per_minute,
                    payload.concurrent_calls,
                    identifier,
                ),
            )
            row = cur.fetchone()
            admin_event(cur, user, "agent.integration.configure", identifier)
            return row


@router.post("/admin/agent-integrations/{identifier}/transfer-responsibility")
def transfer(
    identifier: uuid.UUID, payload: Transfer, authorization: str = Header(default="")
):
    with get_connection() as c:
        with c.cursor() as cur:
            user = staff(cur, authorization)
            i = a.integration(cur, identifier, False)
            check_version(i, payload.expected_revision)
            if i["state"] == "revoked":
                a.fail("integration_inactive")
            a.eligible(cur, payload.responsible_id)
            cur.execute(
                "UPDATE gotrendlabs_agent_integrations SET responsible_id=%s,revision=revision+1 WHERE id=%s RETURNING *",
                (payload.responsible_id, identifier),
            )
            row = cur.fetchone()
            admin_event(cur, user, "agent.integration.transfer", identifier)
            return row


@router.post("/admin/agent-integrations/{identifier}/credentials")
def issue_credential(
    identifier: uuid.UUID, response: Response, authorization: str = Header(default="")
):
    with get_connection() as c:
        with c.cursor() as cur:
            user = staff(cur, authorization)
            i = a.integration(cur, identifier, False)
            if i["state"] == "revoked" or i["expires_at"] <= a.now():
                a.fail("integration_inactive")
            a.eligible(cur, i["responsible_id"])
            secret = secrets.token_urlsafe(48)
            cid = uuid.uuid4()
            expires = min(i["expires_at"], a.now() + timedelta(days=90))
            cur.execute(
                "INSERT INTO gotrendlabs_agent_credentials(id,integration_id,secret_hash,created_at,expires_at,revoked_at,last_used_at) VALUES(%s,%s,%s,%s,%s,NULL,NULL)",
                (cid, identifier, a.digest(secret), a.now(), expires),
            )
            admin_event(cur, user, "agent.credential.issue", identifier)
            response.headers["Cache-Control"] = "private, no-store"
            return {
                "credential_id": cid,
                "secret": secret,
                "expires_at": expires,
                "previous_credentials_revoked": False,
            }


@router.get("/admin/agent-integrations/{identifier}/connections")
def connections(identifier: uuid.UUID, authorization: str = Header(default="")):
    return integration_detail(identifier, authorization)["connections"]


@router.post("/admin/agent-integrations/{identifier}/{kind}/{origin_id}/revoke")
def revoke_origin(
    identifier: uuid.UUID,
    kind: Literal["credentials", "connections"],
    origin_id: uuid.UUID,
    authorization: str = Header(default=""),
):
    with get_connection() as c:
        with c.cursor() as cur:
            user = staff(cur, authorization)
            a.integration(cur, identifier, False)
            table = "credentials" if kind == "credentials" else "grants"
            cur.execute(
                f"UPDATE gotrendlabs_agent_{table} SET revoked_at=COALESCE(revoked_at,%s) WHERE id=%s AND integration_id=%s RETURNING id",
                (a.now(), origin_id, identifier),
            )
            if not cur.fetchone():
                a.fail("not_found", 404)
            admin_event(cur, user, "agent." + kind + ".revoke", identifier)
            return {"revoked": True}


@router.post("/admin/agent-integrations/{identifier}/{action}")
def transition(
    identifier: uuid.UUID,
    action: Literal["activate", "pause", "revoke"],
    payload: RevisionAction,
    authorization: str = Header(default=""),
):
    with get_connection() as c:
        with c.cursor() as cur:
            user = staff(cur, authorization)
            i = a.integration(cur, identifier, False)
            check_version(i, payload.expected_revision)
            if i["state"] == "revoked":
                a.fail("integration_inactive")
            if action == "activate":
                a.eligible(cur, i["responsible_id"])
                if i["expires_at"] <= a.now():
                    a.fail("integration_inactive")
            state = {"activate": "active", "pause": "paused", "revoke": "revoked"}[
                action
            ]
            cur.execute(
                "UPDATE gotrendlabs_agent_integrations SET state=%s,revision=revision+1 WHERE id=%s RETURNING *",
                (state, identifier),
            )
            row = cur.fetchone()
            admin_event(cur, user, "agent.integration." + action, identifier)
            return row


@router.get("/.well-known/oauth-authorization-server")
def discovery():
    base = a.issuer()
    return {
        "issuer": base,
        "authorization_endpoint": base + "/oauth/authorize",
        "token_endpoint": base + "/oauth/token",
        "registration_endpoint": base + "/oauth/register",
        "revocation_endpoint": base + "/oauth/revoke",
        "response_types_supported": ["code"],
        "grant_types_supported": [
            "authorization_code",
            "refresh_token",
            "client_credentials",
        ],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "scopes_supported": list(SCOPES),
        "code_challenge_methods_supported": ["S256"],
        "authorization_response_iss_parameter_supported": True,
    }


@router.get("/.well-known/oauth-protected-resource/mcp")
@router.get("/.well-known/oauth-protected-resource")
def protected_resource():
    return {
        "resource": a.resource(),
        "authorization_servers": [a.issuer()],
        "scopes_supported": list(SCOPES),
        "bearer_methods_supported": ["header"],
    }


@router.post("/oauth/register", status_code=201)
def register(payload: OAuthRegistration, request: Request):
    a.public_attempt(request.client.host)
    identifier = uuid.uuid4()
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO gotrendlabs_agent_oauth_clients(id,name,redirect_uris,created_at) VALUES(%s,%s,%s,%s)",
                (
                    identifier,
                    payload.client_name,
                    Jsonb(payload.redirect_uris),
                    a.now(),
                ),
            )
    # Optional RFC 7591 string metadata must be omitted when absent, not null.
    return {"client_id": str(identifier), **payload.model_dump(exclude_none=True)}


class Consent(Strict):
    parameters: dict[str, str]
    integration_id: uuid.UUID


@router.post("/oauth/consent-info")
def consent_info(payload: dict[str, str], authorization: str = Header(default="")):
    with get_connection() as c:
        with c.cursor() as cur:
            staff(cur, authorization)
            server = Server(cur)
            try:
                req = server.consent_info(payload)
            except OAuth2Error as exc:
                from fastapi import HTTPException

                raise HTTPException(
                    422, detail={"code": "validation_failed", "oauth_error": exc.error}
                ) from None
            cur.execute(
                "SELECT id,name,scopes FROM gotrendlabs_agent_integrations WHERE state='active' AND expires_at>%s ORDER BY name LIMIT 100",
                (a.now(),),
            )
            return {
                "client_name": req.client.row["name"],
                "scopes": payload["scope"].split(),
                "redirect_uri": payload["redirect_uri"],
                "integrations": cur.fetchall(),
            }


@router.post("/oauth/consent")
def consent(payload: Consent, authorization: str = Header(default="")):
    with get_connection() as c:
        with c.cursor() as cur:
            user = staff(cur, authorization)
            try:
                (status, body, headers), grant_id = Server(cur).authorize(
                    payload.parameters, user, payload.integration_id
                )
            except OAuth2Error as exc:
                from fastapi import HTTPException

                raise HTTPException(
                    422, detail={"code": "validation_failed", "oauth_error": exc.error}
                ) from None
            if status != 302:
                a.fail("validation_failed", 422)
            admin_event(cur, user, "agent.oauth.consent", payload.integration_id)
            return JSONResponse(
                {"redirect": dict(headers)["Location"]},
                headers={"Cache-Control": "private, no-store"},
            )


@router.get("/oauth/authorize")
def authorize(request: Request):
    # Browser login and CSRF consent live in Django, never a staff token in the URL.
    return RedirectResponse(
        a.issuer()
        + "/admin-ops/integration-consent/?"
        + urlencode(list(request.query_params.multi_items())),
        status_code=302,
        headers={"Cache-Control": "private, no-store"},
    )


async def form_data(request):
    body = await request.body()
    if len(body) > 8192:
        a.fail("validation_failed", 422)
    pairs = parse_qsl(body.decode(), keep_blank_values=True)
    if len({k for k, v in pairs}) != len(pairs):
        a.fail("validation_failed", 422)
    return dict(pairs)


@router.post("/oauth/token")
async def token(request: Request):
    a.public_attempt(request.client.host)
    data = await form_data(request)
    with get_connection() as c:
        with c.cursor() as cur:
            if not a.enabled():
                return JSONResponse(
                    {"error": "temporarily_unavailable"},
                    503,
                    headers={"Cache-Control": "private, no-store"},
                )
            if data.get("grant_type") == "client_credentials":
                try:
                    cid = uuid.UUID(data.get("client_id", ""))
                except ValueError:
                    return JSONResponse(
                        {"error": "invalid_client"},
                        401,
                        headers={"Cache-Control": "private, no-store"},
                    )
                cur.execute(
                    "SELECT * FROM gotrendlabs_agent_credentials WHERE id=%s", (cid,)
                )
                credential = cur.fetchone()
                if (
                    not credential
                    or not secrets.compare_digest(
                        credential["secret_hash"],
                        a.digest(data.get("client_secret", "")),
                    )
                    or credential["revoked_at"]
                    or credential["expires_at"] <= a.now()
                ):
                    return JSONResponse(
                        {"error": "invalid_client"},
                        401,
                        headers={"Cache-Control": "private, no-store"},
                    )
                i = a.integration(cur, credential["integration_id"])
                scopes = data.get("scope", " ".join(i["scopes"])).split()
                if data.get("resource") != a.resource():
                    return JSONResponse(
                        {"error": "invalid_target"},
                        400,
                        headers={"Cache-Control": "private, no-store"},
                    )
                if not set(scopes).issubset(i["scopes"]):
                    return JSONResponse(
                        {"error": "invalid_scope"},
                        400,
                        headers={"Cache-Control": "private, no-store"},
                    )
                origin = {
                    "integration_id": i["id"],
                    "credential_id": cid,
                    "grant_id": None,
                    "scopes": scopes,
                }
                expires = min(
                    a.now() + timedelta(minutes=10),
                    credential["expires_at"],
                    i["expires_at"],
                )
                access, _ = a.insert_token(cur, origin, "access", a.resource(), expires)
                cur.execute(
                    "UPDATE gotrendlabs_agent_credentials SET last_used_at=%s WHERE id=%s",
                    (a.now(), cid),
                )
                result = {
                    "access_token": access,
                    "token_type": "Bearer",
                    "expires_in": int((expires - a.now()).total_seconds()),
                    "scope": " ".join(scopes),
                }
                status = 200
            else:
                status, result, headers = Server(cur).token_response(data)
            return JSONResponse(
                result,
                status,
                headers={"Cache-Control": "private, no-store", "Pragma": "no-cache"},
            )


@router.post("/oauth/revoke")
async def revoke_token(request: Request):
    a.public_attempt(request.client.host)
    data = await form_data(request)
    with get_connection() as c:
        with c.cursor() as cur:
            try:
                t = a.validate(
                    cur, data.get("token", ""), a.resource(), "refresh", True
                )
            except Exception:
                return JSONResponse({}, headers={"Cache-Control": "private, no-store"})
            if str(t["origin"].get("client_id")) == data.get("client_id"):
                cur.execute(
                    "UPDATE gotrendlabs_agent_grants SET revoked_at=%s WHERE id=%s",
                    (a.now(), t["grant_id"]),
                )
    return JSONResponse({}, headers={"Cache-Control": "private, no-store"})


@router.post("/internal/agent-integrations/delegate")
def delegate(
    payload: Delegation, response: Response, x_mcp_workload: str = Header(default="")
):
    a.workload(x_mcp_workload)
    with get_connection() as c:
        with c.cursor() as cur:
            t = a.validate(cur, payload.access_token, a.resource())
            expiry = min(t["expires_at"], a.now() + timedelta(seconds=40))
            value, _ = a.insert_token(
                cur, t, "internal", a.api_audience(), expiry, parent=t["id"]
            )
            response.headers["Cache-Control"] = "private, no-store"
            return {
                "access_token": value,
                "expires_in": max(1, int((expiry - a.now()).total_seconds())),
                "scopes": t["scopes"],
                "integration_id": str(t["integration_id"]),
            }


@router.post("/internal/agent-integrations/events")
def ingest_event(
    payload: ToolEvent,
    authorization: str = Header(default=""),
    x_mcp_workload: str = Header(default=""),
):
    a.workload(x_mcp_workload)
    with get_connection() as c:
        with c.cursor() as cur:
            t = a.validate(cur, a.bearer(authorization), a.api_audience(), "internal")
            cur.execute(
                "INSERT INTO gotrendlabs_agent_ingested_events(id,integration_id,created_at) VALUES(%s,%s,%s) ON CONFLICT(id) DO NOTHING RETURNING id",
                (uuid.UUID(payload.event_id), t["integration_id"], a.now()),
            )
            inserted = bool(cur.fetchone())
    if inserted:
        technical(
            t,
            payload.tool,
            payload.result,
            uuid.uuid4().hex,
            payload.execution_id,
            stage="mcp",
        )
    return {"accepted": True, "duplicate": not inserted}


@router.get(
    "/integrations/editorial/policy",
    response_model=PolicyResponse,
)
def get_policy(
    authorization: str = Header(default=""), x_mcp_workload: str = Header(default="")
):
    with agent(authorization, x_mcp_workload, "editorial:read", "get_editorial_policy"):
        return domain.policy()


@router.get(
    "/integrations/editorial/taxonomy",
    response_model=TaxonomyResponse,
)
def get_taxonomy(
    cursor: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    authorization: str = Header(default=""),
    x_mcp_workload: str = Header(default=""),
):
    with agent(authorization, x_mcp_workload, "catalog:read", "get_taxonomy") as (
        cur,
        t,
        r,
    ):
        return domain.taxonomy(cur, cursor, limit)


@router.get(
    "/integrations/editorial/markets",
    response_model=SearchResponse,
)
def markets(
    q: str = Query("", max_length=240),
    status: str = Query("", max_length=20),
    event_id: int | None = None,
    cursor: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    from_at: datetime | None = None,
    to_at: datetime | None = None,
    authorization: str = Header(default=""),
    x_mcp_workload: str = Header(default=""),
):
    with agent(authorization, x_mcp_workload, "catalog:read", "search_markets") as (
        cur,
        t,
        r,
    ):
        return domain.search(cur, q, status, event_id, cursor, limit, from_at, to_at)


@router.get(
    "/integrations/editorial/markets/{market_id}",
    response_model=MarketProjection,
    response_model_exclude_unset=True,
)
def market(
    market_id: int,
    authorization: str = Header(default=""),
    x_mcp_workload: str = Header(default=""),
):
    with agent(authorization, x_mcp_workload, "catalog:read", "get_market") as (
        cur,
        t,
        r,
    ):
        return domain.get_market(cur, market_id, t["integration_id"])


@router.get(
    "/integrations/editorial/signals",
    response_model=SignalsResponse,
)
def signals(
    days: int = Query(7, ge=1, le=90),
    authorization: str = Header(default=""),
    x_mcp_workload: str = Header(default=""),
):
    with agent(
        authorization, x_mcp_workload, "metrics:read", "get_editorial_signals"
    ) as (cur, t, r):
        start = a.now() - timedelta(days=days)
        cur.execute(
            """SELECT u.is_bot,count(*) AS predictions FROM gotrendlabs_predictions p JOIN gotrendlabs_users u ON u.id=p.user_id WHERE p.created_at>=%s AND NOT u.is_staff AND NOT u.is_superuser GROUP BY u.is_bot""",
            (start,),
        )
        counts = {x["is_bot"]: x["predictions"] for x in cur.fetchall()}
        return {
            "period_start": start,
            "period_end": a.now(),
            "as_of": a.now(),
            "timezone": "UTC",
            "unit": "predictions",
            "availability": "available",
            "humans": counts.get(False, 0),
            "bots": counts.get(True, 0),
            "analytics": {"availability": "unavailable", "value": None},
        }


@router.post(
    "/integrations/editorial/drafts/validate", response_model=ValidationResponse
)
def validate_draft(
    payload: Draft,
    authorization: str = Header(default=""),
    x_mcp_workload: str = Header(default=""),
):
    with agent(
        authorization, x_mcp_workload, "drafts:write", "validate_market_draft"
    ) as (cur, t, r):
        domain.validated(cur, payload)
        return {
            "structurally_valid": True,
            "pending": domain.pending(payload.editorial_record.model_dump(mode="json")),
            "evidence_origin": "agent_reported",
            "similar": domain.search(cur, payload.title[:80]),
        }


@router.post("/integrations/editorial/drafts", response_model=MutationResponse)
def create_draft(
    payload: CreateDraft,
    authorization: str = Header(default=""),
    x_mcp_workload: str = Header(default=""),
):
    with agent(
        authorization, x_mcp_workload, "drafts:write", "create_market_draft"
    ) as (cur, t, r):
        return domain.mutate(cur, t, "create", payload, request_id=r)


@router.patch(
    "/integrations/editorial/drafts/{market_id}", response_model=MutationResponse
)
def update_draft(
    market_id: int,
    payload: UpdateDraft,
    authorization: str = Header(default=""),
    x_mcp_workload: str = Header(default=""),
):
    with agent(
        authorization, x_mcp_workload, "drafts:write", "update_market_draft"
    ) as (cur, t, r):
        return domain.mutate(cur, t, "update", payload, market_id, r)


@router.post(
    "/integrations/editorial/drafts/{market_id}/submit", response_model=MutationResponse
)
def submit_draft(
    market_id: int,
    payload: SubmitDraft,
    authorization: str = Header(default=""),
    x_mcp_workload: str = Header(default=""),
):
    with agent(
        authorization, x_mcp_workload, "drafts:submit", "submit_draft_for_review"
    ) as (cur, t, r):
        return domain.mutate(cur, t, "submit", payload, market_id, r)


@router.get(
    "/integrations/editorial/drafts/{market_id}/review",
    response_model=ReviewResponse,
)
def draft_review(
    market_id: int,
    authorization: str = Header(default=""),
    x_mcp_workload: str = Header(default=""),
):
    with agent(authorization, x_mcp_workload, "editorial:read", "get_draft_review") as (
        cur,
        t,
        r,
    ):
        return domain.lock_draft(cur, market_id, t["integration_id"])[1]


@router.get("/admin/agent-editorial-reviews")
def reviews(authorization: str = Header(default=""), cursor: int = Query(0, ge=0)):
    with get_connection() as c:
        with c.cursor() as cur:
            staff(cur, authorization)
            cur.execute(
                "SELECT d.*,m.title,m.slug,m.status FROM gotrendlabs_agent_editorial_drafts d JOIN gotrendlabs_markets m ON m.id=d.market_id WHERE d.market_id>%s ORDER BY d.market_id LIMIT 101",
                (cursor,),
            )
            rows = cur.fetchall()
            return {
                "items": rows[:100],
                "has_more": len(rows) > 100,
                "next_cursor": str(rows[99]["market_id"]) if len(rows) > 100 else None,
            }


@router.get("/admin/agent-editorial-reviews/{market_id}")
def review_detail(market_id: int, authorization: str = Header(default="")):
    with get_connection() as c:
        with c.cursor() as cur:
            staff(cur, authorization)
            _, d = domain.lock_draft(cur, market_id)
            market = domain.get_market(cur, market_id, None)
            current_policy = domain.policy()
            cur.execute(
                "SELECT revision,snapshot,snapshot_hash,created_at FROM gotrendlabs_agent_editorial_revisions WHERE draft_id=%s ORDER BY revision DESC LIMIT 100",
                (market_id,),
            )
            return {
                "market": market,
                "draft": d,
                "document": domain.editorial_document(d["record"], market),
                "policy_version": current_policy["version"],
                "policy_hash": current_policy["hash"],
                "revisions": cur.fetchall(),
                "pending": domain.pending(d["record"]),
                "criteria": current_policy["criteria"],
                "publication_gate_enforced": True,
                "publication_gate_scope": "all_markets",
            }


@router.post("/admin/agent-editorial-reviews/{market_id}/decision")
def decision(
    market_id: int, payload: ReviewDecision, authorization: str = Header(default="")
):
    with get_connection() as c:
        with c.cursor() as cur:
            return domain.decide(cur, market_id, payload, staff(cur, authorization))


@router.patch("/admin/agent-editorial-reviews/{market_id}/record")
def prepare_record(
    market_id: int,
    payload: HumanEditorialRecord,
    authorization: str = Header(default=""),
):
    with get_connection() as c:
        with c.cursor() as cur:
            return domain.prepare_human_record(
                cur, market_id, payload, staff(cur, authorization)
            )


@router.post("/admin/agent-editorial-reviews/{market_id}/assessment")
def assessment(
    market_id: int,
    payload: HumanEditorialAssessment,
    authorization: str = Header(default=""),
):
    with get_connection() as c:
        with c.cursor() as cur:
            return domain.assess_human_record(
                cur, market_id, payload, staff(cur, authorization)
            )


@router.get("/admin/agent-integrations/{identifier}/activity")
def activity(
    identifier: uuid.UUID,
    authorization: str = Header(default=""),
    cursor: int = Query(0, ge=0),
):
    with get_connection() as c:
        with c.cursor() as cur:
            staff(cur, authorization)
            a.integration(cur, identifier, False)
            cur.execute(
                "SELECT id,created_at,request_id,event_type,context FROM gotrendlabs_system_logs WHERE context->>'integration_id'=%s AND (%s=0 OR id<%s) ORDER BY id DESC LIMIT 101",
                (str(identifier), cursor, cursor),
            )
            rows = cur.fetchall()
            return {
                "items": rows[:100],
                "has_more": len(rows) > 100,
                "next_cursor": str(rows[99]["id"]) if len(rows) > 100 else None,
            }
