"""Editorial domain: drafts, snapshots, human review and minimal projections."""

import hashlib
import json
from pathlib import Path
from psycopg.types.json import Jsonb
from apps.api.backend_api import editorial_auth as a
from apps.api.backend_api.editorial_schemas import (
    Draft,
    ReviewDecision,
)
from apps.api.backend_api.admin_events import record_admin_event
from apps.api.backend_api.editorial_context import request_context

ROOT = Path(__file__).resolve().parents[3]


def canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def policy():
    path = ROOT / "docs/editorial/criteria-v1.2.json"
    raw = path.read_bytes()
    criteria = json.loads(raw)
    if criteria["status"] != "approved":
        a.fail("dependency_unavailable", 503)
    return {
        **criteria,
        "hash": hashlib.sha256(raw).hexdigest(),
        "manual": (ROOT / "docs/editorial/manual-editorial.md").read_text(),
        "checklist": (ROOT / "docs/editorial/checklist-de-publicacao.md").read_text(),
        "record_template": (ROOT / "docs/editorial/ficha-de-mercado.md").read_text(),
        "as_of": a.now().isoformat(),
    }


def audit(cursor, t, action, resource_id, request_id):
    record_admin_event(
        cursor,
        None,
        action,
        "market",
        str(resource_id),
        integration_id=t["integration_id"],
        responsible_id=t["integration"]["responsible_id"],
        request_id=request_id,
        execution_id=request_context.get().get("execution_id", ""),
    )


def taxonomy(cursor, after=0, limit=100):
    cursor.execute(
        """SELECT c.id AS category_id,c.name AS category,s.id AS subcategory_id,s.name AS subcategory,e.id AS event_id,e.name AS event
        FROM gotrendlabs_market_categories c JOIN gotrendlabs_market_subcategories s ON s.category_id=c.id
        JOIN gotrendlabs_market_events e ON e.subcategory_id=s.id WHERE NOT c.is_blocked AND NOT s.is_blocked AND NOT e.is_blocked AND e.id>%s ORDER BY e.id LIMIT %s""",
        (after, limit + 1),
    )
    rows = cursor.fetchall()
    return {
        "items": rows[:limit],
        "has_more": len(rows) > limit,
        "next_cursor": str(rows[limit - 1]["event_id"]) if len(rows) > limit else None,
        "coverage": "partial" if len(rows) > limit else "complete_for_query",
        "as_of": a.now().isoformat(),
    }


def search(
    cursor, q="", status="", event_id=None, after=0, limit=20, from_at=None, to_at=None
):
    cursor.execute(
        """SELECT id,slug,title,summary,kind,status,category_id,subcategory_id,event_id,close_at,close_timezone
       FROM gotrendlabs_markets WHERE id>%s AND (title ILIKE %s OR summary ILIKE %s) AND (%s='' OR status=%s)
       AND (%s::bigint IS NULL OR event_id=%s) AND (%s::timestamptz IS NULL OR close_at>=%s) AND (%s::timestamptz IS NULL OR close_at<=%s) ORDER BY id LIMIT %s""",
        (
            after,
            "%" + q + "%",
            "%" + q + "%",
            status,
            status,
            event_id,
            event_id,
            from_at,
            from_at,
            to_at,
            to_at,
            limit + 1,
        ),
    )
    rows = cursor.fetchall()
    more = len(rows) > limit
    items = rows[:limit]
    return {
        "items": items,
        "next_cursor": str(items[-1]["id"]) if more else None,
        "has_more": more,
        "coverage": "partial" if more else "complete_for_query",
        "as_of": a.now().isoformat(),
    }


def get_market(cursor, market_id, integration_id):
    cursor.execute(
        "SELECT id,slug,title,summary,kind,status,source,resolution_criteria,close_at,close_timezone,category_id,subcategory_id,event_id,auto_close_enabled,thumb_color,image_url,thumb,is_featured FROM gotrendlabs_markets WHERE id=%s",
        (market_id,),
    )
    m = cursor.fetchone()
    if not m:
        a.fail("not_found", 404)
    cursor.execute(
        "SELECT label,hint FROM gotrendlabs_market_options WHERE market_id=%s ORDER BY display_order,id",
        (market_id,),
    )
    m["options"] = cursor.fetchall()
    cursor.execute(
        "SELECT revision,state,record,snapshot_hash,decision FROM gotrendlabs_agent_editorial_drafts WHERE market_id=%s AND integration_id=%s",
        (market_id, integration_id),
    )
    d = cursor.fetchone()
    if d:
        m["editorial"] = d
    return m


def validated(cursor, payload):
    from apps.api.backend_api import main

    if payload.close_at <= a.now():
        a.fail("validation_failed", 422)
    cursor.execute(
        "SELECT id,name,is_blocked FROM gotrendlabs_market_categories WHERE id=%s FOR SHARE",
        (payload.category_id,),
    )
    category = cursor.fetchone()
    cursor.execute(
        "SELECT id,name,is_blocked FROM gotrendlabs_market_subcategories WHERE id=%s AND category_id=%s FOR SHARE",
        (payload.subcategory_id, payload.category_id),
    )
    sub = cursor.fetchone()
    cursor.execute(
        "SELECT id,name,is_blocked FROM gotrendlabs_market_events WHERE id=%s AND subcategory_id=%s FOR SHARE",
        (payload.event_id, payload.subcategory_id),
    )
    event = cursor.fetchone()
    if (
        not category
        or not sub
        or not event
        or any(x["is_blocked"] for x in (category, sub, event))
    ):
        a.fail("validation_failed", 422)
    options = main._normalize_market_options(payload)
    return category, sub, event, options


def pending(record):
    p = policy()
    result = []
    if record["policy_version"] != p["version"] or record["policy_hash"] != p["hash"]:
        result.append("policy_outdated")
    if not (record.get("document") or "").strip():
        result.append("empty_document")
    return result


def lock_draft(cursor, market_id, integration_id=None):
    cursor.execute(
        "SELECT id,status,slug,title FROM gotrendlabs_markets WHERE id=%s FOR UPDATE",
        (market_id,),
    )
    m = cursor.fetchone()
    if not m:
        a.fail("not_found", 404)
    cursor.execute(
        "SELECT * FROM gotrendlabs_agent_editorial_drafts WHERE market_id=%s FOR UPDATE",
        (market_id,),
    )
    d = cursor.fetchone()
    if not d or integration_id and d["integration_id"] != integration_id:
        a.fail("resource_forbidden", 404)
    return m, d


def version(d, expected):
    if expected != d["revision"]:
        a.fail("version_conflict", 409)


def snapshot(cursor, market_id, payload, revision):
    value = (
        payload.model_dump(
            mode="json", exclude={"idempotency_key", "expected_revision"}
        )
        if payload
        else get_market(cursor, market_id, None)
    )
    value.pop("editorial", None)
    if not payload:
        cursor.execute(
            "SELECT record FROM gotrendlabs_agent_editorial_drafts WHERE market_id=%s",
            (market_id,),
        )
        value["editorial_record"] = cursor.fetchone()["record"]
    value = json.loads(canonical(value))
    h = sha(value)
    cursor.execute(
        "INSERT INTO gotrendlabs_agent_editorial_revisions(draft_id,revision,snapshot,snapshot_hash,created_at) VALUES(%s,%s,%s,%s,%s)",
        (market_id, revision, Jsonb(value), h, a.now()),
    )
    return h


def initialize_human_editorial(cursor, market_id):
    """Shared draft creation hook; origin stays human, never a fake integration."""
    cursor.execute(
        "SELECT id FROM gotrendlabs_markets WHERE id=%s FOR UPDATE", (market_id,)
    )
    cursor.execute(
        "SELECT 1 FROM gotrendlabs_agent_editorial_drafts WHERE market_id=%s",
        (market_id,),
    )
    if cursor.fetchone():
        return
    p = policy()
    record = {
        "policy_version": p["version"],
        "policy_hash": p["hash"],
        "document": "",
    }
    cursor.execute(
        "INSERT INTO gotrendlabs_agent_editorial_drafts(market_id,integration_id,revision,state,record,snapshot_hash,decision) VALUES(%s,NULL,1,'preparation',%s,'','{}'::jsonb)",
        (market_id, Jsonb(record)),
    )
    h = snapshot(cursor, market_id, None, 1)
    cursor.execute(
        "UPDATE gotrendlabs_agent_editorial_drafts SET snapshot_hash=%s WHERE market_id=%s",
        (h, market_id),
    )


def human_edit_guard(cursor, market_id, expected):
    # Called with market lock by the existing web/mobile-compatible handler.
    cursor.execute(
        "SELECT * FROM gotrendlabs_agent_editorial_drafts WHERE market_id=%s FOR UPDATE",
        (market_id,),
    )
    d = cursor.fetchone()
    if d:
        version(d, expected)
    return d


def human_edit_done(cursor, market_id, d):
    if not d:
        return
    revision = d["revision"] + 1
    record = d["record"]
    cursor.execute(
        "UPDATE gotrendlabs_agent_editorial_drafts SET record=%s WHERE market_id=%s",
        (Jsonb(record), market_id),
    )
    h = snapshot(cursor, market_id, None, revision)
    cursor.execute(
        "UPDATE gotrendlabs_agent_editorial_drafts SET revision=%s,state='preparation',snapshot_hash=%s,decision='{}'::jsonb WHERE market_id=%s",
        (revision, h, market_id),
    )


def readable_draft_slug(cursor, title):
    from apps.api.backend_api import main

    base = main._slug_seed(title)
    # Shared with human inserts; serialize the same title across integrations.
    cursor.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
        ("market-slug:" + base,),
    )
    return main._unique_slug(cursor, "gotrendlabs_markets", base)


def require_publication_approval(cursor, market_id):
    """Called after the market lock, before signing or opening any market."""
    cursor.execute(
        "SELECT * FROM gotrendlabs_agent_editorial_drafts WHERE market_id=%s FOR UPDATE",
        (market_id,),
    )
    d = cursor.fetchone()
    decision = (d["decision"] or {}) if d else {}
    if not d:
        from fastapi import HTTPException

        raise HTTPException(
            409,
            detail={
                "code": "editorial_approval_required",
                "message": "Publicação exige ficha e parecer humano aprovado da versão atual.",
            },
        )
    valid = (
        d["state"] == "approved"
        and decision.get("decision") == "approved"
        and decision.get("evidence_origin") == "human_attestation"
        and bool(decision.get("reviewer_id"))
        and decision.get("confirmed") is True
        and decision.get("expected_revision") == d["revision"] - 1
        and decision.get("snapshot_hash") == d["snapshot_hash"]
        and not pending(d["record"])
    )
    if valid:
        cursor.execute(
            "SELECT snapshot,snapshot_hash FROM gotrendlabs_agent_editorial_revisions WHERE draft_id=%s AND revision=%s",
            (market_id, decision["expected_revision"]),
        )
        revision = cursor.fetchone()
        current = get_market(cursor, market_id, None)
        current.pop("editorial", None)
        current["editorial_record"] = d["record"]
        expected = dict(revision["snapshot"]) if revision else {}
        valid = bool(
            revision
            and revision["snapshot_hash"] == d["snapshot_hash"]
            and sha(expected) == d["snapshot_hash"]
        )
        # Draft/scheduled transition isn't a change to the reviewed question.
        current.pop("status", None)
        expected.pop("status", None)
        valid = valid and sha(current) == sha(expected)
    if not valid:
        from fastapi import HTTPException

        raise HTTPException(
            409,
            detail={
                "code": "editorial_approval_required",
                "message": "Publicação bloqueada: este mercado de integração precisa de parecer humano aprovado para a versão atual. Confira a ficha editorial.",
            },
        )


def mutate(cursor, t, operation, payload, market_id=None, request_id=""):
    i = t["integration"]
    key = payload.idempotency_key
    payload_hash = sha(payload.model_dump(mode="json"))
    op = operation + (":" + str(market_id) if market_id else "")
    cursor.execute(
        "SELECT * FROM gotrendlabs_agent_idempotency WHERE integration_id=%s AND operation=%s AND key=%s",
        (i["id"], op, key),
    )
    old = cursor.fetchone()
    if old:
        if old["payload_hash"] != payload_hash:
            a.fail("idempotency_conflict", 409)
        return {**old["response"], "replayed": True}
    from apps.api.backend_api import main

    if operation == "create":
        category, sub, event, options = validated(cursor, payload)
        a.draft_quota(cursor, i)
        fixed = main.AdminMarketPayload(
            **payload.model_dump(
                exclude={
                    "category_id",
                    "subcategory_id",
                    "event_id",
                    "editorial_record",
                    "idempotency_key",
                    "expected_revision",
                }
            ),
            category=category["name"],
            subcategory=sub["name"],
            event=event["name"],
            slug=readable_draft_slug(cursor, payload.title),
            thumb_color="#334155",
        )
        result = main._insert_market_draft(
            cursor, fixed, category, sub, event, None, record_event=False
        )
        cursor.execute(
            "SELECT id FROM gotrendlabs_markets WHERE slug=%s", (result["slug"],)
        )
        market_id = cursor.fetchone()["id"]
        revision = 1
        state = "preparation"
        record = payload.editorial_record.model_dump(mode="json")
        cursor.execute(
            "INSERT INTO gotrendlabs_agent_editorial_drafts(market_id,integration_id,revision,state,record,snapshot_hash,decision) VALUES(%s,%s,1,%s,%s,%s,%s)",
            (market_id, i["id"], state, Jsonb(record), "", Jsonb({})),
        )
        h = snapshot(cursor, market_id, payload, revision)
        cursor.execute(
            "UPDATE gotrendlabs_agent_editorial_drafts SET snapshot_hash=%s WHERE market_id=%s",
            (h, market_id),
        )
    else:
        m, d = lock_draft(cursor, market_id, i["id"])
        version(d, payload.expected_revision)
        if m["status"] != "draft" or d["state"] not in ("preparation", "returned"):
            a.fail("draft_not_editable", 409)
        revision = d["revision"] + 1
        if operation == "update":
            _, _, _, options = validated(cursor, payload)
            state = "preparation"
            record = payload.editorial_record.model_dump(mode="json")
            cursor.execute(
                """UPDATE gotrendlabs_markets SET title=%s,summary=%s,kind=%s,category_id=%s,subcategory_id=%s,event_id=%s,source=%s,resolution_criteria=%s,close_at=%s,close_timezone=%s,primary_outcome=%s,updated_by_id=NULL,updated_at=%s WHERE id=%s""",
                (
                    payload.title,
                    payload.summary,
                    payload.kind,
                    payload.category_id,
                    payload.subcategory_id,
                    payload.event_id,
                    payload.source,
                    payload.resolution_criteria,
                    payload.close_at,
                    payload.close_timezone,
                    options[0]["label"],
                    a.now(),
                    market_id,
                ),
            )
            main._save_market_options(cursor, market_id, options)
            h = snapshot(cursor, market_id, payload, revision)
        else:
            current = get_market(cursor, market_id, i["id"])
            current["close_at"] = current["close_at"].astimezone(
                __import__("zoneinfo").ZoneInfo(current["close_timezone"])
            )
            Draft.model_validate(
                {
                    **{
                        k: current[k]
                        for k in Draft.model_fields
                        if k != "editorial_record"
                    },
                    "editorial_record": d["record"],
                }
            )
            if "policy_outdated" in pending(d["record"]):
                a.fail("validation_failed", 422)
            state = "in_review"
            record = d["record"]
            h = snapshot(cursor, market_id, None, revision)
        cursor.execute(
            "UPDATE gotrendlabs_agent_editorial_drafts SET revision=%s,state=%s,record=%s,snapshot_hash=%s,decision='{}'::jsonb WHERE market_id=%s",
            (revision, state, Jsonb(record), h, market_id),
        )
    cursor.execute(
        "SELECT slug,status FROM gotrendlabs_markets WHERE id=%s", (market_id,)
    )
    m = cursor.fetchone()
    response = {
        "market_id": market_id,
        "slug": m["slug"],
        "market_status": m["status"],
        "editorial_status": state,
        "revision": revision,
        "snapshot_hash": h,
        "policy_version": record["policy_version"],
        "admin_url": "/admin-ops/agent-reviews/" + str(market_id) + "/",
        "request_id": request_id,
        "replayed": False,
    }
    audit(cursor, t, "agent.draft." + operation, market_id, request_id)
    cursor.execute(
        "INSERT INTO gotrendlabs_agent_idempotency(integration_id,operation,key,payload_hash,response,created_at) VALUES(%s,%s,%s,%s,%s,%s)",
        (i["id"], op, key, payload_hash, Jsonb(response), a.now()),
    )
    return response


def assess_human_record(cursor, market_id, payload, staff):
    m, d = lock_draft(cursor, market_id)
    version(d, payload.expected_revision)
    if m["status"] not in {"draft", "scheduled", "open", "locked"}:
        a.fail("draft_not_editable", 409)
    if d["snapshot_hash"] != payload.snapshot_hash:
        a.fail("version_conflict", 409)
    if "policy_outdated" in pending(d["record"]) and payload.editorial_record.document == d["record"].get("document", ""):
        from fastapi import HTTPException

        raise HTTPException(
            422,
            detail={
                "code": "validation_failed",
                "message": "A política editorial mudou. Revise e atualize o documento antes de registrar o parecer.",
                "pending": ["policy_outdated"],
            },
        )
    revision = d["revision"] + 1
    cursor.execute(
        "UPDATE gotrendlabs_agent_editorial_drafts SET record=%s WHERE market_id=%s",
        (Jsonb(payload.editorial_record.model_dump(mode="json")), market_id),
    )
    h = snapshot(cursor, market_id, None, revision)
    cursor.execute(
        "UPDATE gotrendlabs_agent_editorial_drafts SET revision=%s,state='in_review',snapshot_hash=%s,decision='{}'::jsonb WHERE market_id=%s",
        (revision, h, market_id),
    )
    decision = ReviewDecision(
        expected_revision=revision,
        snapshot_hash=h,
        decision=payload.decision,
        confirmed=payload.confirmed,
    )
    return decide(cursor, market_id, decision, staff)


def decide(cursor, market_id, payload, staff):
    m, d = lock_draft(cursor, market_id)
    version(d, payload.expected_revision)
    if (
        m["status"] not in {"draft", "scheduled", "open", "locked"}
        or d["state"] != "in_review"
    ):
        a.fail("draft_not_editable", 409)
    if d["snapshot_hash"] != payload.snapshot_hash:
        a.fail("version_conflict", 409)
    record = d["record"]
    if payload.decision == "approved":
        from fastapi import HTTPException

        missing = pending(record)
        if missing or not payload.confirmed:
            raise HTTPException(
                422,
                detail={
                    "code": "validation_failed",
                    "message": "Aprovação exige documento atual e confirmação humana explícita.",
                    "pending": missing,
                },
            )
    decision = {
        **payload.model_dump(mode="json"),
        "confirmed": payload.confirmed if payload.decision == "approved" else False,
        "reviewer_id": staff["id"],
        "reviewed_at": a.now().isoformat(),
        "evidence_origin": "human_attestation",
        "global_publication_gate": True,
        "publication_gate_scope": "all_markets",
    }
    cursor.execute(
        "UPDATE gotrendlabs_agent_editorial_drafts SET state=%s,decision=%s WHERE market_id=%s",
        (payload.decision, Jsonb(decision), market_id),
    )
    record_admin_event(
        cursor,
        staff["id"],
        "agent.review." + payload.decision,
        "market",
        str(market_id),
        "Parecer registrado no documento editorial.",
        integration_id=d["integration_id"],
    )
    # Preserve decisions alongside revisions without overwriting an old snapshot.
    revision = d["revision"] + 1
    cursor.execute(
        "INSERT INTO gotrendlabs_agent_editorial_revisions(draft_id,revision,snapshot,snapshot_hash,created_at) VALUES(%s,%s,%s,%s,%s)",
        (
            market_id,
            revision,
            Jsonb(
                {
                    "decision": decision,
                    "reviewed_revision": d["revision"],
                    "reviewed_hash": d["snapshot_hash"],
                }
            ),
            d["snapshot_hash"],
            a.now(),
        ),
    )
    cursor.execute(
        "UPDATE gotrendlabs_agent_editorial_drafts SET revision=%s WHERE market_id=%s",
        (revision, market_id),
    )
    return {**d, "revision": revision, "state": payload.decision, "decision": decision}
