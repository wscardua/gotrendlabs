"""Delegated lifecycle operations; caller holds validated integration authorization.

Lock order: integration (agent context), market, receipt/ledger. No network I/O.
"""

from uuid import UUID, uuid5

from . import editorial_auth as auth
from .admin_events import record_admin_event
from .editorial_context import request_context
from .editorial_schemas import MarketActionResponse
from .editorial_service import sha
from . import resolution_requests

# Namespaced keys cannot collide with another integration's identical UUID.
RECEIPT_NAMESPACE = UUID("9d11d8a6-e157-4aa8-af32-281245360c5d")


def _market(cursor, market_id):
    cursor.execute(
        "SELECT * FROM gotrendlabs_markets WHERE id=%s FOR UPDATE", (market_id,)
    )
    market = cursor.fetchone()
    if not market:
        auth.fail("not_found", 404)
    return market


def _projection(market, request_id, replayed):
    return MarketActionResponse(
        market_id=market["id"],
        status=market["status"],
        updated_at=market["updated_at"],
        winning_option_id=market["winning_option_id"],
        resolved_at=market["resolved_at"],
        resolution_timezone=market["resolution_timezone"],
        request_id=request_id,
        replayed=replayed,
    ).model_dump(mode="json")


def mutate(cursor, actor, operation, payload, request_id):
    # agent() has revalidated scopes and locked integration through commit,
    # including replay. Never accept an actor or scope from the tool arguments.
    integration = actor["integration"]
    market = _market(cursor, payload.market_id)
    digest = sha(payload.model_dump(mode="json", exclude={"idempotency_key"}))
    cursor.execute(
        """SELECT * FROM gotrendlabs_agent_market_requests
        WHERE integration_id=%s AND operation=%s AND key=%s""",
        (integration["id"], operation, payload.idempotency_key),
    )
    receipt = cursor.fetchone()
    if receipt:
        if receipt["market_id"] != market["id"] or receipt["payload_hash"] != digest:
            auth.fail("idempotency_conflict", 409)
        if operation == "resolve":
            # A seal preserves the resolution; undo/re-resolution supersedes it.
            if not resolution_requests.confirmed_request(
                cursor, market, receipt["resolution_key"]
            ):
                auth.fail("dependency_unavailable", 503)
        elif market["status"] != "canceled":
            auth.fail("market_state_conflict", 409)
        return _projection(market, receipt["request_id"], True)

    if market["updated_at"] != payload.expected_updated_at:
        auth.fail("version_conflict", 409)
    if operation == "resolve":
        if market["status"] != "locked":
            auth.fail("resolution_state_conflict", 409)
        if payload.resolved_at > auth.now():
            auth.fail("validation_failed", 422)
        cursor.execute(
            "SELECT id FROM gotrendlabs_market_options WHERE id=%s AND market_id=%s",
            (payload.winning_option_id, market["id"]),
        )
        if not cursor.fetchone():
            auth.fail("invalid_winning_option", 422)
    else:
        if (
            market["status"] not in {"draft", "scheduled", "open", "locked"}
            or market["status"] != payload.expected_status
        ):
            auth.fail("market_state_conflict", 409)
        if market["status"] == "draft":
            cursor.execute(
                "SELECT integration_id FROM gotrendlabs_agent_editorial_drafts WHERE market_id=%s FOR UPDATE",
                (market["id"],),
            )
            draft = cursor.fetchone()
            if not draft or draft["integration_id"] != integration["id"]:
                auth.fail("resource_forbidden", 404)

    from . import main

    engine = main._market_lifecycle_engine(cursor, None)

    def audit(cur, actor_id, action, entity_type, identifier, note=""):
        record_admin_event(
            cur,
            None,
            action,
            entity_type,
            identifier,
            note,
            integration_id=integration["id"],
            responsible_id=integration["responsible_id"],
            request_id=request_id,
            execution_id=request_context.get().get("execution_id", ""),
        )

    engine.record_admin_event = audit
    resolution_key = None
    if operation == "resolve":
        # Reuse the same immutable, atomic confirmation contract as Admin Ops.
        resolution_key = uuid5(
            RECEIPT_NAMESPACE, f"{integration['id']}:resolve:{payload.idempotency_key}"
        )
        adapted = main.AdminMarketResolvePayload(
            expected_market_id=market["id"],
            idempotency_key=resolution_key,
            **payload.model_dump(
                exclude={"market_id", "expected_updated_at", "idempotency_key"}
            ),
        )
        resolution_digest = resolution_requests.request_hash(adapted)
        if not resolution_requests.confirmed_request(
            cursor, market, resolution_key, payload_hash=resolution_digest
        ):
            engine.resolve_market(market, market["slug"], adapted)
            market = _market(cursor, market["id"])
            resolution_requests.record_request(
                cursor, market, adapted, resolution_digest
            )
    else:
        # Never pass resolved to cancel_market: that path is human-only undo.
        engine.cancel_market(market, market["slug"], payload.note)
        market = _market(cursor, market["id"])

    cursor.execute(
        """INSERT INTO gotrendlabs_agent_market_requests
        (integration_id, operation, key, market_id, payload_hash, resolution_key, request_id, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            integration["id"],
            operation,
            payload.idempotency_key,
            market["id"],
            digest,
            resolution_key,
            request_id,
            auth.now(),
        ),
    )
    return _projection(market, request_id, False)


def delete_draft(cursor, actor, payload, request_id):
    """Delete only an owned prepublication draft; keep a minimal replay receipt."""
    from fastapi import HTTPException
    from psycopg.types.json import Jsonb
    from .market_deletion import delete_market
    from .editorial_schemas import DeleteMarketDraftResponse

    integration = actor["integration"]
    digest = sha(payload.model_dump(mode="json", exclude={"idempotency_key"}))
    # Integration authorization lock in agent() serializes same-key requests.
    # The receipt cannot have a market FK: the resource is physically removed.
    cursor.execute(
        """SELECT payload_hash,response FROM gotrendlabs_agent_idempotency
        WHERE integration_id=%s AND operation='delete' AND key=%s""",
        (integration["id"], str(payload.idempotency_key)),
    )
    receipt = cursor.fetchone()
    if receipt:
        if receipt["payload_hash"] != digest:
            auth.fail("idempotency_conflict", 409)
        return DeleteMarketDraftResponse(
            **{**receipt["response"], "replayed": True}
        ).model_dump(mode="json")

    market = _market(cursor, payload.market_id)
    cursor.execute(
        "SELECT * FROM gotrendlabs_agent_editorial_drafts WHERE market_id=%s FOR UPDATE",
        (market["id"],),
    )
    draft = cursor.fetchone()
    if not draft or draft["integration_id"] != integration["id"]:
        auth.fail("resource_forbidden", 404)
    if (
        draft["revision"] != payload.expected_revision
        or market["updated_at"] != payload.expected_updated_at
    ):
        auth.fail("version_conflict", 409)
    try:
        delete_market(
            cursor,
            market["slug"],
            payload.expected_revision,
            None,
            market["id"],
            integration_id=integration["id"],
            responsible_id=integration["responsible_id"],
            request_id=request_id,
            execution_id=request_context.get().get("execution_id", ""),
            deletion_note=payload.note,
        )
    except HTTPException as exc:
        # Preserve stable codes instead of exposing administrative free text.
        auth.fail(
            "draft_not_deletable" if exc.status_code == 409 else "not_found",
            exc.status_code,
        )

    result = DeleteMarketDraftResponse(
        market_id=market["id"], deleted=True, request_id=request_id, replayed=False
    ).model_dump(mode="json")
    cursor.execute(
        """INSERT INTO gotrendlabs_agent_idempotency
        (integration_id,operation,key,payload_hash,response,created_at)
        VALUES (%s,'delete',%s,%s,%s,%s)""",
        (
            integration["id"],
            str(payload.idempotency_key),
            digest,
            Jsonb(result),
            auth.now(),
        ),
    )
    return result
