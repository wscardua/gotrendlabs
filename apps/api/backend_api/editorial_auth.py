"""FastAPI-owned identity, current delegation validation and persistent quotas."""

import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from apps.api.backend_api.db import get_connection

UTC = timezone.utc


def now():
    return datetime.now(UTC)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def issuer():
    return os.environ.get("GTL_MCP_ISSUER", "http://localhost:8000").rstrip("/")


def resource():
    return os.environ.get("GTL_MCP_RESOURCE", "http://localhost:8002/mcp")


def api_audience():
    return "gotrendlabs:editorial-api"


def enabled():
    return os.environ.get("GTL_MCP_ENABLED", "0") == "1"


def fail(code, status=403, retry=None):
    raise HTTPException(
        status,
        detail={"code": code, "message": code},
        headers={"Retry-After": str(retry)} if retry else None,
    )


def eligible(cursor, user_id):
    cursor.execute(
        "SELECT id FROM gotrendlabs_users WHERE id=%s AND is_active AND account_status='active' AND (is_staff OR is_superuser) AND NOT is_bot FOR SHARE",
        (user_id,),
    )
    if not cursor.fetchone():
        fail("integration_inactive")


def integration(cursor, identifier, active=True):
    cursor.execute(
        "SELECT * FROM gotrendlabs_agent_integrations WHERE id=%s FOR NO KEY UPDATE",
        (identifier,),
    )
    row = cursor.fetchone()
    if not row:
        fail("not_found", 404)
    if active:
        if not enabled() or row["state"] != "active" or row["expires_at"] <= now():
            fail("integration_inactive")
        eligible(cursor, row["responsible_id"])
    return row


def workload(value):
    expected = os.environ.get("GTL_MCP_WORKLOAD_SECRET", "")
    if len(expected) < 32 or not secrets.compare_digest(value, expected):
        fail("unauthenticated", 401)


def insert_token(
    cursor,
    origin,
    kind,
    audience,
    expires,
    scopes=None,
    parent=None,
    metadata=None,
    value=None,
):
    value = value or secrets.token_urlsafe(48)
    identifier = uuid.uuid4()
    cursor.execute(
        """INSERT INTO gotrendlabs_agent_tokens
      (id,token_hash,integration_id,credential_id,grant_id,parent_id,kind,issuer,audience,scopes,metadata,created_at,expires_at,consumed_at)
      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL)""",
        (
            identifier,
            digest(value),
            origin["integration_id"],
            origin.get("credential_id"),
            origin.get("grant_id"),
            parent,
            kind,
            issuer(),
            audience,
            Jsonb(scopes if scopes is not None else origin["scopes"]),
            Jsonb(metadata or {}),
            now(),
            expires,
        ),
    )
    return value, identifier


def validate(cursor, value, audience, kind="access", allow_consumed=False):
    cursor.execute(
        "SELECT * FROM gotrendlabs_agent_tokens WHERE token_hash=%s", (digest(value),)
    )
    t = cursor.fetchone()
    if (
        not t
        or t["issuer"] != issuer()
        or t["audience"] != audience
        or t["kind"] != kind
        or t["expires_at"] <= now()
    ):
        fail("unauthenticated", 401)
    i = integration(cursor, t["integration_id"])
    # Integration lock serializes all credential/grant revocation and mutating calls.
    cursor.execute(
        "SELECT * FROM gotrendlabs_agent_tokens WHERE id=%s FOR UPDATE", (t["id"],)
    )
    t = cursor.fetchone()
    if t["consumed_at"] and not allow_consumed:
        fail("unauthenticated", 401)
    if t["credential_id"]:
        cursor.execute(
            "SELECT * FROM gotrendlabs_agent_credentials WHERE id=%s AND integration_id=%s",
            (t["credential_id"], i["id"]),
        )
        o = cursor.fetchone()
    else:
        cursor.execute(
            "SELECT * FROM gotrendlabs_agent_grants WHERE id=%s AND integration_id=%s",
            (t["grant_id"], i["id"]),
        )
        o = cursor.fetchone()
        if o:
            eligible(cursor, o["user_id"])
    if not o or o["revoked_at"] or o["expires_at"] <= now():
        fail("integration_inactive")
    if t["parent_id"]:
        cursor.execute(
            "SELECT expires_at,issuer,audience,kind FROM gotrendlabs_agent_tokens WHERE id=%s",
            (t["parent_id"],),
        )
        p = cursor.fetchone()
        if (
            not p
            or p["expires_at"] <= now()
            or p["issuer"] != issuer()
            or p["audience"] != resource()
            or p["kind"] != "access"
        ):
            fail("unauthenticated", 401)
    t["scopes"] = sorted(
        set(t["scopes"])
        & set(i["scopes"])
        & (set(o["scopes"]) if "scopes" in o else set(i["scopes"]))
    )
    t["integration"] = i
    t["origin"] = o
    return t


def bearer(value):
    if not value.startswith("Bearer ") or len(value) > 250:
        fail("unauthenticated", 401)
    return value[7:]


def quota(cursor, bucket, limit, expires, integration_id=None):
    cursor.execute(
        """INSERT INTO gotrendlabs_agent_quotas(integration_id,bucket,count,expires_at) VALUES(%s,%s,0,%s)
       ON CONFLICT(bucket) DO NOTHING""",
        (integration_id, bucket, expires),
    )
    cursor.execute(
        "UPDATE gotrendlabs_agent_quotas SET count=count+1 WHERE bucket=%s AND count<%s RETURNING count",
        (bucket, limit),
    )
    if not cursor.fetchone():
        return False
    return True


def attempt_quota(cursor, bucket, limit, expires, integration_id=None):
    cursor.execute(
        """INSERT INTO gotrendlabs_agent_quotas(integration_id,bucket,count,expires_at) VALUES(%s,%s,1,%s)
      ON CONFLICT(bucket) DO UPDATE SET count=gotrendlabs_agent_quotas.count+1 RETURNING count""",
        (integration_id, bucket, expires),
    )
    return cursor.fetchone()["count"] <= limit


def public_attempt(ip):
    # Commit even denied requests; no user-supplied identity used in the bucket.
    minute = int(now().timestamp() // 60)
    with get_connection() as c:
        with c.cursor() as cur:
            ok = attempt_quota(
                cur, f"auth:{digest(ip)}:{minute}", 30, now() + timedelta(minutes=2)
            )
    if not ok:
        fail("quota_exceeded", 429, 60)


def reserve_call(value, scope):
    denied = None
    lease = uuid.uuid4()
    t = None
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute("SET LOCAL lock_timeout = '5s'")
            t = validate(cur, value, api_audience(), "internal")
            i = t["integration"]
            minute = int(now().timestamp() // 60)
            ok = attempt_quota(
                cur,
                f"call:{i['id']}:{minute}",
                i["calls_per_minute"],
                now() + timedelta(minutes=2),
                i["id"],
            )
            if not ok:
                denied = "quota_exceeded"
            elif scope not in t["scopes"]:
                denied = "forbidden_scope"
            else:
                cur.execute(
                    "DELETE FROM gotrendlabs_agent_leases WHERE integration_id=%s AND expires_at<=%s",
                    (i["id"], now()),
                )
                cur.execute(
                    "SELECT count(*) AS count FROM gotrendlabs_agent_leases WHERE integration_id=%s",
                    (i["id"],),
                )
                if cur.fetchone()["count"] >= i["concurrent_calls"]:
                    denied = "quota_exceeded"
                else:
                    cur.execute(
                        "INSERT INTO gotrendlabs_agent_leases(id,integration_id,expires_at) VALUES(%s,%s,%s)",
                        (lease, i["id"], now() + timedelta(seconds=45)),
                    )
                    cur.execute(
                        "UPDATE gotrendlabs_agent_integrations SET last_used_at=%s WHERE id=%s",
                        (now(), i["id"]),
                    )
    if denied:
        try:
            fail(
                denied,
                429 if denied == "quota_exceeded" else 403,
                60 if denied == "quota_exceeded" else None,
            )
        except HTTPException as exc:
            exc.editorial_actor = t
            raise
    return t, lease


def release_call(lease):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM gotrendlabs_agent_leases WHERE id=%s", (lease,))


def draft_quota(cursor, i):
    date = now().astimezone(ZoneInfo("America/Sao_Paulo")).date()
    tomorrow = datetime.combine(
        date + timedelta(days=1), datetime.min.time(), ZoneInfo("America/Sao_Paulo")
    )
    if not quota(
        cursor, f"draft:{i['id']}:{date}", i["drafts_per_day"], tomorrow, i["id"]
    ):
        fail("quota_exceeded", 429, max(1, int((tomorrow - now()).total_seconds())))
