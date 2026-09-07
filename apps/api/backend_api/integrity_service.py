"""Cryptographic integrity protocol for GoTrendLabs markets.

Private key material is never persisted. Production signing is delegated to AWS KMS;
the in-memory signer exists only for development and deterministic test injection.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import threading
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


PROTOCOL_VERSION = "gtl-integrity/v1"
SIGNING_ALGORITHM = "ED25519_SHA_512"
LEDGER_LOCK_ID = 0x47544C49
CHECKPOINT_VERIFIER_VERSION = "gtl-ledger-verifier/v1"
FULL_AUDIT_INTERVAL = timedelta(hours=24)


class IntegritySigningError(RuntimeError):
    pass


def _json_default(value: Any):
    if isinstance(value, datetime):
        aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return aware.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    raise TypeError(f"Unsupported canonical value: {type(value).__name__}")


def canonical_json(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_json_default).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class Signature:
    value: bytes
    algorithm: str
    key_id: str
    key_fingerprint: str
    public_key_der: bytes


class _EphemeralSigner:
    def __init__(self):
        self._private_key = Ed25519PrivateKey.generate()
        self.key_id = f"local-ephemeral-ed25519:{sha256_hex(self.public_key())[:16]}"

    def sign(self, digest_hex: str) -> Signature:
        public_der = self.public_key()
        return Signature(
            value=self._private_key.sign(digest_hex.encode("ascii")),
            algorithm=SIGNING_ALGORITHM,
            key_id=self.key_id,
            key_fingerprint=sha256_hex(public_der),
            public_key_der=public_der,
        )

    def public_key(self) -> bytes:
        return self._private_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )


class _KMSSigner:
    def __init__(self, key_id: str):
        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:
            raise IntegritySigningError("Dependencia AWS KMS indisponivel.") from exc
        self.key_id = key_id
        self._client = boto3.client("kms", config=Config(connect_timeout=2, read_timeout=5, retries={"max_attempts": 2, "mode": "standard"}))
        self._public_key_der = None

    def _public_key(self) -> bytes:
        if self._public_key_der is None:
            self._public_key_der = bytes(self._client.get_public_key(KeyId=self.key_id)["PublicKey"])
        return self._public_key_der

    def public_key(self) -> bytes:
        return self._public_key()

    def sign(self, digest_hex: str) -> Signature:
        try:
            response = self._client.sign(KeyId=self.key_id, Message=digest_hex.encode("ascii"), MessageType="RAW", SigningAlgorithm=SIGNING_ALGORITHM)
            public_der = self._public_key()
            return Signature(bytes(response["Signature"]), SIGNING_ALGORITHM, response.get("KeyId", self.key_id), sha256_hex(public_der), public_der)
        except Exception as exc:
            raise IntegritySigningError(f"AWS KMS recusou a assinatura ({exc.__class__.__name__}).") from exc


_signer = None
_signer_lock = threading.Lock()


def get_signer():
    global _signer
    if _signer is not None:
        return _signer
    with _signer_lock:
        if _signer is not None:
            return _signer
        environment = os.environ.get("GOTRENDLABS_ENV", "").strip().lower()
        key_id = os.environ.get("GOTRENDLABS_INTEGRITY_KMS_KEY_ID", "").strip()
        if key_id:
            _signer = _KMSSigner(key_id)
        elif environment in {"prod", "production"}:
            raise IntegritySigningError("GOTRENDLABS_INTEGRITY_KMS_KEY_ID e obrigatoria em producao.")
        else:
            _signer = _EphemeralSigner()
        return _signer


def sign_payload(payload: dict) -> tuple[bytes, str, Signature]:
    canonical = canonical_json(payload)
    digest = sha256_hex(canonical)
    return canonical, digest, get_signer().sign(digest)


def remember_public_key(cursor, signed: Signature, *, created_at: datetime | None = None):
    created_at = created_at or datetime.now(timezone.utc)
    cursor.execute(
        """INSERT INTO integrity_signing_keys
           (key_id,algorithm,key_fingerprint,public_key_der,created_at)
           VALUES (%s,%s,%s,%s,%s)
           ON CONFLICT (key_id) DO NOTHING""",
        (signed.key_id, signed.algorithm, signed.key_fingerprint, signed.public_key_der, created_at),
    )
    cursor.execute("SELECT key_fingerprint FROM integrity_signing_keys WHERE key_id=%s", (signed.key_id,))
    existing = cursor.fetchone()
    if not existing or not hmac.compare_digest(existing["key_fingerprint"], signed.key_fingerprint):
        raise IntegritySigningError("O identificador da chave nao corresponde a chave publica registrada.")


def verify_signed_hash(digest_hex: str, signature: bytes, public_key_der: bytes) -> bool:
    try:
        key = serialization.load_der_public_key(public_key_der)
        if not isinstance(key, Ed25519PublicKey):
            return False
        key.verify(bytes(signature), digest_hex.encode("ascii"))
        return True
    except Exception:
        return False


def _user_commitment(user_id: int) -> str:
    secret = os.environ.get("GOTRENDLABS_USER_COMMITMENT_SECRET", "").encode()
    environment = os.environ.get("GOTRENDLABS_ENV", "").strip().lower()
    if not secret and environment in {"prod", "production"}:
        raise IntegritySigningError("GOTRENDLABS_USER_COMMITMENT_SECRET e obrigatoria em producao.")
    if not secret:
        secret = b"dev-only-user-commitment-secret"
    return hmac.new(secret, f"gtl-user:{user_id}".encode(), hashlib.sha256).hexdigest()


def append_ledger_event(cursor, *, event_type: str, entity_type: str, entity_identifier: str, market_id: int | None, payload_reference: str, payload_hash: str, occurred_at: datetime | None = None, correlation_id=None, causation_id=None, payload_snapshot: dict | None = None):
    occurred_at = occurred_at or datetime.now(timezone.utc)
    cursor.execute("SELECT pg_advisory_xact_lock(%s)", (LEDGER_LOCK_ID,))
    cursor.execute("SELECT sequence, event_hash FROM integrity_ledger_events ORDER BY sequence DESC LIMIT 1")
    previous = cursor.fetchone()
    sequence = int(previous["sequence"]) + 1 if previous else 1
    previous_hash = previous["event_hash"] if previous else ""
    event_payload = {
        "causation_id": str(causation_id) if causation_id else None,
        "correlation_id": str(correlation_id) if correlation_id else None,
        "entity_identifier": str(entity_identifier),
        "entity_type": entity_type,
        "event_type": event_type,
        "market_id": market_id,
        "occurred_at": occurred_at,
        "payload_hash": payload_hash,
        "payload_reference": payload_reference,
        "payload_snapshot": payload_snapshot,
        "previous_event_hash": previous_hash,
        "protocol_version": PROTOCOL_VERSION,
        "sequence": sequence,
    }
    canonical, event_hash, signed = sign_payload(event_payload)
    remember_public_key(cursor, signed, created_at=occurred_at)
    cursor.execute(
        """INSERT INTO integrity_ledger_events
        (sequence,protocol_version,event_type,entity_type,entity_identifier,market_id,payload_reference,payload_hash,canonical_payload,payload_json,previous_event_hash,event_hash,signature,algorithm,key_id,key_fingerprint,correlation_id,causation_id,occurred_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
        (sequence,PROTOCOL_VERSION,event_type,entity_type,str(entity_identifier),market_id,payload_reference,payload_hash,canonical,json.dumps(event_payload,default=_json_default),previous_hash,event_hash,signed.value,signed.algorithm,signed.key_id,signed.key_fingerprint,correlation_id,causation_id,occurred_at,occurred_at),
    )
    return cursor.fetchone()


def market_definition_payload(
    cursor,
    market_id: int,
    *,
    published_at: datetime,
    definition_version: int = 1,
    signed_snapshot: dict | None = None,
):
    cursor.execute("""SELECT m.*, c.name category_name, sc.name subcategory_name, ev.name event_name
                    FROM gotrendlabs_markets m JOIN gotrendlabs_market_categories c ON c.id=m.category_id
                    JOIN gotrendlabs_market_subcategories sc ON sc.id=m.subcategory_id
                    LEFT JOIN gotrendlabs_market_events ev ON ev.id=m.event_id WHERE m.id=%s""", (market_id,))
    market = cursor.fetchone()
    if not market:
        raise IntegritySigningError("Mercado inexistente para definicao de integridade.")
    cursor.execute("SELECT id,label,hint,display_order FROM gotrendlabs_market_options WHERE market_id=%s ORDER BY display_order,id", (market_id,))
    options = cursor.fetchall()
    payload = {
        "auto_close_enabled": bool(market["auto_close_enabled"]),
        "category": (signed_snapshot or {}).get("category", market["category_name"]),
        "close_at": market["close_at"], "close_timezone": market["close_timezone"] or "UTC",
        "definition_version": definition_version,
        "event": (signed_snapshot or {}).get("event", market["event_name"] or ""),
        "kind": market["kind"],
        "market_id": market_id, "market_slug": market["slug"],
        "options": [{"id": row["id"], "label": row["label"], "hint": row["hint"] or "", "order": row["display_order"]} for row in options],
        "protocol_version": PROTOCOL_VERSION, "published_at": published_at,
        "resolution_criteria": market["resolution_criteria"] or "", "resolution_source": market["source"] or "",
        "subcategory": (signed_snapshot or {}).get("subcategory", market["subcategory_name"]),
        "summary": market["summary"] or "", "title": market["title"],
    }
    # Stable associations are always protected; names remain editorial snapshots.
    payload["category_id"] = market["category_id"]
    payload["subcategory_id"] = market["subcategory_id"]
    payload["event_id"] = market["event_id"]
    return payload


def market_result_payload(market: dict):
    return {
        "evidence": market["resolution_note"] or "", "resolved_at": market["resolved_at"],
        "resolution_timezone": market["resolution_timezone"] or "UTC", "winning_option_id": market["winning_option_id"],
    }


def register_market_definition(cursor, market_id: int, *, occurred_at: datetime | None = None):
    occurred_at = occurred_at or datetime.now(timezone.utc)
    cursor.execute("SELECT * FROM market_integrity_definitions WHERE market_id=%s", (market_id,))
    existing = cursor.fetchone()
    if existing:
        return existing
    cursor.execute("SELECT id,slug FROM gotrendlabs_markets WHERE id=%s FOR UPDATE", (market_id,))
    market = cursor.fetchone()
    payload = market_definition_payload(cursor, market_id, published_at=occurred_at)
    canonical, digest, signed = sign_payload(payload)
    remember_public_key(cursor, signed, created_at=occurred_at)
    cursor.execute("""INSERT INTO market_integrity_definitions
        (market_id,definition_version,protocol_version,canonical_payload,payload_json,payload_hash,signature,algorithm,key_id,key_fingerprint,signed_at)
        VALUES (%s,1,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s) RETURNING *""",
        (market_id,PROTOCOL_VERSION,canonical,json.dumps(payload,default=_json_default),digest,signed.value,signed.algorithm,signed.key_id,signed.key_fingerprint,occurred_at))
    definition = cursor.fetchone()
    append_ledger_event(cursor,event_type="market_published",entity_type="market",entity_identifier=market["slug"],market_id=market_id,payload_reference=f"market_definition:{definition['id']}",payload_hash=digest,occurred_at=occurred_at)
    return definition


def commit_prediction(cursor, *, prediction_id: int, user_id: int, occurred_at: datetime | None = None):
    occurred_at = occurred_at or datetime.now(timezone.utc)
    cursor.execute("SELECT * FROM prediction_commitments WHERE prediction_id=%s", (prediction_id,))
    existing = cursor.fetchone()
    if existing:
        return existing
    cursor.execute("""SELECT p.*, m.slug market_slug, d.id definition_id, d.definition_version
        FROM gotrendlabs_predictions p JOIN gotrendlabs_markets m ON m.id=p.market_id
        JOIN market_integrity_definitions d ON d.market_id=p.market_id WHERE p.id=%s""", (prediction_id,))
    prediction = cursor.fetchone()
    if not prediction:
        raise IntegritySigningError("Mercado sem definicao assinada nao aceita previsao.")
    cursor.execute("""SELECT pc.id,pc.commitment_hash FROM prediction_commitments pc
        JOIN gotrendlabs_predictions p ON p.id=pc.prediction_id
        WHERE p.user_id=%s AND p.market_id=%s ORDER BY p.position_sequence DESC,pc.id DESC LIMIT 1""", (user_id,prediction["market_id"]))
    previous = cursor.fetchone()
    payload = {
        "action_id": f"prediction:{prediction_id}", "action_type": prediction["action_type"],
        "definition_version": prediction["definition_version"], "market_id": prediction["market_id"],
        "market_slug": prediction["market_slug"], "option_id": prediction["market_option_id"],
        "position_sequence": prediction["position_sequence"], "previous_commitment_hash": previous["commitment_hash"] if previous else None,
        "protocol_version": PROTOCOL_VERSION, "server_timestamp": occurred_at, "stake": int(prediction["stake_amount"]),
        "user_commitment": _user_commitment(user_id),
    }
    canonical,digest,signed=sign_payload(payload)
    remember_public_key(cursor, signed, created_at=occurred_at)
    cursor.execute("""INSERT INTO prediction_commitments
        (prediction_id,market_id,definition_id,previous_commitment_id,protocol_version,canonical_payload,payload_json,commitment_hash,signature,algorithm,key_id,key_fingerprint,signed_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s) RETURNING *""",
        (prediction_id,prediction["market_id"],prediction["definition_id"],previous["id"] if previous else None,PROTOCOL_VERSION,canonical,json.dumps(payload,default=_json_default),digest,signed.value,signed.algorithm,signed.key_id,signed.key_fingerprint,occurred_at))
    commitment=cursor.fetchone()
    append_ledger_event(cursor,event_type="prediction_committed",entity_type="prediction",entity_identifier=prediction_id,market_id=prediction["market_id"],payload_reference=f"prediction_commitment:{commitment['id']}",payload_hash=digest,occurred_at=occurred_at)
    return commitment


def build_merkle(commitment_hashes: list[str]):
    if not commitment_hashes:
        return sha256_hex(b""), []
    levels = [commitment_hashes]
    while len(levels[-1]) > 1:
        level = levels[-1]
        levels.append([sha256_hex(bytes.fromhex(level[i]) + bytes.fromhex(level[i + 1] if i + 1 < len(level) else level[i])) for i in range(0, len(level), 2)])
    proofs = []
    for original_index in range(len(commitment_hashes)):
        index = original_index
        proof = []
        for level in levels[:-1]:
            sibling_index = index - 1 if index % 2 else index + 1
            sibling = level[sibling_index] if sibling_index < len(level) else level[index]
            proof.append({"position": "left" if index % 2 else "right", "hash": sibling})
            index //= 2
        proofs.append(proof)
    return levels[-1][0], proofs


def verify_merkle_proof(leaf_hash: str, proof: list[dict], root: str) -> bool:
    value = leaf_hash
    for item in proof:
        sibling = item["hash"]
        value = sha256_hex(bytes.fromhex(sibling) + bytes.fromhex(value)) if item["position"] == "left" else sha256_hex(bytes.fromhex(value) + bytes.fromhex(sibling))
    return hmac.compare_digest(value, root)


def _json_object(value):
    return json.loads(value) if isinstance(value, str) else (value or {})


def _ledger_event_is_valid(event: dict, public_key_der: bytes) -> bool:
    """Validate the signed snapshot and every persisted event metadata field."""
    event_payload = _json_object(event["payload_json"])
    expected_correlation_id = str(event["correlation_id"]) if event["correlation_id"] else None
    expected_causation_id = str(event["causation_id"]) if event["causation_id"] else None
    return (
        hmac.compare_digest(event["previous_event_hash"], event_payload.get("previous_event_hash", ""))
        and hmac.compare_digest(event["event_hash"], sha256_hex(bytes(event["canonical_payload"])))
        and hmac.compare_digest(sha256_hex(canonical_json(event_payload)), event["event_hash"])
        and event_payload.get("sequence") == event["sequence"]
        and event_payload.get("protocol_version") == event["protocol_version"] == PROTOCOL_VERSION
        and event_payload.get("event_type") == event["event_type"]
        and event_payload.get("entity_type") == event["entity_type"]
        and event_payload.get("entity_identifier") == event["entity_identifier"]
        and event_payload.get("market_id") == event["market_id"]
        and event_payload.get("payload_hash") == event["payload_hash"]
        and event_payload.get("payload_reference") == event["payload_reference"]
        and event_payload.get("occurred_at") == _json_default(event["occurred_at"])
        and event_payload.get("correlation_id") == expected_correlation_id
        and event_payload.get("causation_id") == expected_causation_id
        and event["created_at"] == event["occurred_at"]
        and event["algorithm"] == SIGNING_ALGORITHM
        and hmac.compare_digest(sha256_hex(public_key_der), event["key_fingerprint"])
        and verify_signed_hash(event["event_hash"], bytes(event["signature"]), public_key_der)
    )


def _verify_integrity_ledger_segment(
    cursor,
    *,
    start_sequence: int,
    through_sequence: int,
    expected_previous_hash: str,
):
    cursor.execute(
        """SELECT * FROM integrity_ledger_events
           WHERE sequence >= %s AND sequence <= %s ORDER BY sequence""",
        (start_sequence, through_sequence),
    )
    previous_hash = expected_previous_hash
    expected_sequence = start_sequence
    valid = True
    invalid_market_ids = set()
    first_invalid_sequence = None
    last_verified_sequence = start_sequence - 1
    last_verified_hash = expected_previous_hash
    verified_event_count = 0
    public_keys = {}
    for event in cursor.fetchall():
        try:
            public_key_der = public_keys.get(event["key_id"])
            if public_key_der is None:
                public_key_der = public_key_der_for(event["key_id"], cursor=cursor)
                public_keys[event["key_id"]] = public_key_der
            valid_event = (
                event["sequence"] == expected_sequence
                and hmac.compare_digest(event["previous_event_hash"], previous_hash)
                and _ledger_event_is_valid(event, public_key_der)
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            valid_event = False
        if not valid_event:
            valid = False
            if first_invalid_sequence is None:
                first_invalid_sequence = expected_sequence
            if event["market_id"] is not None:
                invalid_market_ids.add(event["market_id"])
        elif first_invalid_sequence is None:
            last_verified_sequence = event["sequence"]
            last_verified_hash = event["event_hash"]
            verified_event_count += 1
        previous_hash = event["event_hash"]
        expected_sequence = event["sequence"] + 1
    if expected_sequence <= through_sequence:
        valid = False
        if first_invalid_sequence is None:
            first_invalid_sequence = expected_sequence
    return {
        "valid": valid,
        "invalid_market_ids": invalid_market_ids,
        "first_invalid_sequence": first_invalid_sequence,
        "last_verified_sequence": last_verified_sequence,
        "last_verified_hash": last_verified_hash,
        "verified_event_count": verified_event_count,
    }


def _ledger_head(cursor):
    cursor.execute("SELECT sequence,event_hash FROM integrity_ledger_events ORDER BY sequence DESC LIMIT 1")
    row = cursor.fetchone()
    return {
        "sequence": int(row["sequence"]) if row else 0,
        "event_hash": row["event_hash"] if row else "",
    }


def verify_integrity_ledger_chain(cursor):
    head = _ledger_head(cursor)
    verification = _verify_integrity_ledger_segment(
        cursor,
        start_sequence=1,
        through_sequence=head["sequence"],
        expected_previous_hash="",
    )
    verification.update(
        {
            "status": "verified" if verification["valid"] else "failed",
            "current_sequence": head["sequence"],
            "current_event_hash": head["event_hash"],
            "verified_through_sequence": verification["last_verified_sequence"],
            "verified_at": None,
            "audit_type": "full",
            "pending_events": 0,
            "issue_code": "" if verification["valid"] else "ledger_chain_invalid",
        }
    )
    return verification


def _checkpoint_is_valid(checkpoint: dict, public_key_der: bytes) -> bool:
    payload = _json_object(checkpoint["payload_json"])
    return (
        hmac.compare_digest(sha256_hex(bytes(checkpoint["canonical_payload"])), checkpoint["checkpoint_hash"])
        and hmac.compare_digest(sha256_hex(canonical_json(payload)), checkpoint["checkpoint_hash"])
        and verify_signed_hash(checkpoint["checkpoint_hash"], bytes(checkpoint["signature"]), public_key_der)
        and checkpoint["algorithm"] == SIGNING_ALGORITHM
        and hmac.compare_digest(sha256_hex(public_key_der), checkpoint["key_fingerprint"])
        and payload.get("checkpoint_sequence") == checkpoint["checkpoint_sequence"]
        and payload.get("audit_type") == checkpoint["audit_type"]
        and payload.get("status") == checkpoint["status"]
        and payload.get("first_event_sequence") == checkpoint["first_event_sequence"]
        and payload.get("last_event_sequence") == checkpoint["last_event_sequence"]
        and payload.get("last_event_hash") == checkpoint["last_event_hash"]
        and payload.get("observed_head_sequence") == checkpoint["observed_head_sequence"]
        and payload.get("observed_head_hash") == checkpoint["observed_head_hash"]
        and payload.get("verified_event_count") == checkpoint["verified_event_count"]
        and payload.get("previous_checkpoint_hash") == checkpoint["previous_checkpoint_hash"]
        and payload.get("failure_sequence") == checkpoint["failure_sequence"]
        and payload.get("issue_code") == checkpoint["issue_code"]
        and payload.get("protocol_version") == checkpoint["protocol_version"] == PROTOCOL_VERSION
        and payload.get("verifier_version") == checkpoint["verifier_version"] == CHECKPOINT_VERIFIER_VERSION
        and payload.get("verified_at") == _json_default(checkpoint["verified_at"])
        and checkpoint["created_at"] == checkpoint["verified_at"]
        and checkpoint["status"] in {"valid", "invalid"}
        and checkpoint["audit_type"] in {"full", "incremental"}
    )


def _latest_checkpoint(cursor):
    cursor.execute("SELECT * FROM integrity_ledger_checkpoints ORDER BY checkpoint_sequence DESC LIMIT 1")
    return cursor.fetchone()


def ledger_checkpoint_status(cursor):
    checkpoint = _latest_checkpoint(cursor)
    # Read the checkpoint first: a concurrent append can then only turn the result
    # into pending, never into a false head-regression failure.
    head = _ledger_head(cursor)
    base = {
        "invalid_market_ids": set(),
        "current_sequence": head["sequence"],
        "current_event_hash": head["event_hash"],
        "verified_through_sequence": 0,
        "verified_at": None,
        "audit_type": None,
        "pending_events": head["sequence"],
        "checkpoint": checkpoint,
        "issue_code": "checkpoint_unavailable",
    }
    if not checkpoint:
        return {**base, "status": "unavailable", "valid": None}
    checkpoint_payload = {}
    try:
        checkpoint_payload = _json_object(checkpoint["payload_json"])
        public_key = public_key_der_for(checkpoint["key_id"], cursor=cursor)
        checkpoint_valid = _checkpoint_is_valid(checkpoint, public_key)
        if checkpoint["checkpoint_sequence"] > 1:
            cursor.execute(
                "SELECT checkpoint_hash FROM integrity_ledger_checkpoints WHERE checkpoint_sequence=%s",
                (checkpoint["checkpoint_sequence"] - 1,),
            )
            previous = cursor.fetchone()
            checkpoint_valid = checkpoint_valid and bool(previous) and hmac.compare_digest(
                checkpoint["previous_checkpoint_hash"], previous["checkpoint_hash"]
            )
        else:
            checkpoint_valid = checkpoint_valid and checkpoint["previous_checkpoint_hash"] == ""
    except IntegritySigningError:
        return {**base, "status": "unavailable", "valid": None, "issue_code": "checkpoint_key_unavailable"}
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        checkpoint_valid = False
    details = {
        **base,
        "invalid_market_ids": set(checkpoint_payload.get("invalid_market_ids") or []),
        "verified_through_sequence": int(checkpoint["last_event_sequence"]),
        "verified_at": checkpoint["verified_at"],
        "audit_type": checkpoint["audit_type"],
    }
    if not checkpoint_valid:
        return {**details, "status": "failed", "valid": False, "issue_code": "checkpoint_invalid"}
    if checkpoint["status"] == "invalid":
        return {**details, "status": "failed", "valid": False, "issue_code": checkpoint["issue_code"] or "ledger_chain_invalid"}
    if checkpoint["last_event_sequence"] != checkpoint["observed_head_sequence"] or not hmac.compare_digest(
        checkpoint["last_event_hash"], checkpoint["observed_head_hash"]
    ):
        return {**details, "status": "failed", "valid": False, "issue_code": "checkpoint_invalid"}
    if head["sequence"] < checkpoint["observed_head_sequence"]:
        return {**details, "status": "failed", "valid": False, "issue_code": "ledger_head_regressed"}
    if head["sequence"] == checkpoint["observed_head_sequence"]:
        if not hmac.compare_digest(head["event_hash"], checkpoint["observed_head_hash"]):
            return {**details, "status": "failed", "valid": False, "issue_code": "ledger_head_changed"}
        return {**details, "status": "verified", "valid": True, "pending_events": 0, "issue_code": ""}
    cursor.execute(
        "SELECT event_hash FROM integrity_ledger_events WHERE sequence=%s",
        (checkpoint["last_event_sequence"],),
    )
    boundary = cursor.fetchone() if checkpoint["last_event_sequence"] else {"event_hash": ""}
    if not boundary or not hmac.compare_digest(boundary["event_hash"], checkpoint["last_event_hash"]):
        return {**details, "status": "failed", "valid": False, "issue_code": "checkpoint_boundary_invalid"}
    return {
        **details,
        "status": "pending",
        "valid": None,
        "pending_events": head["sequence"] - checkpoint["last_event_sequence"],
        "issue_code": "ledger_verification_pending",
    }


def _create_ledger_checkpoint(cursor, verification: dict, *, audit_type: str, verified_at: datetime):
    latest = _latest_checkpoint(cursor)
    checkpoint_sequence = int(latest["checkpoint_sequence"]) + 1 if latest else 1
    previous_checkpoint_hash = latest["checkpoint_hash"] if latest else ""
    payload = {
        "audit_type": audit_type,
        "checkpoint_sequence": checkpoint_sequence,
        "failure_sequence": verification.get("first_invalid_sequence"),
        "first_event_sequence": verification.get("first_event_sequence"),
        "issue_code": "" if verification["valid"] else "ledger_chain_invalid",
        "invalid_market_ids": sorted(verification["invalid_market_ids"]),
        "last_event_hash": verification["last_verified_hash"],
        "last_event_sequence": verification["last_verified_sequence"],
        "observed_head_hash": verification["current_event_hash"],
        "observed_head_sequence": verification["current_sequence"],
        "previous_checkpoint_hash": previous_checkpoint_hash,
        "protocol_version": PROTOCOL_VERSION,
        "status": "valid" if verification["valid"] else "invalid",
        "verified_at": verified_at,
        "verified_event_count": verification["verified_event_count"],
        "verifier_version": CHECKPOINT_VERIFIER_VERSION,
    }
    canonical, checkpoint_hash, signed = sign_payload(payload)
    remember_public_key(cursor, signed, created_at=verified_at)
    cursor.execute(
        """INSERT INTO integrity_ledger_checkpoints
           (checkpoint_sequence,audit_type,status,first_event_sequence,last_event_sequence,last_event_hash,
            observed_head_sequence,observed_head_hash,verified_event_count,previous_checkpoint_hash,
            failure_sequence,issue_code,protocol_version,verifier_version,canonical_payload,payload_json,
            checkpoint_hash,signature,algorithm,key_id,key_fingerprint,verified_at,created_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s)
           RETURNING *""",
        (
            checkpoint_sequence, audit_type, payload["status"], payload["first_event_sequence"],
            payload["last_event_sequence"], payload["last_event_hash"], payload["observed_head_sequence"],
            payload["observed_head_hash"], payload["verified_event_count"], previous_checkpoint_hash,
            payload["failure_sequence"], payload["issue_code"], PROTOCOL_VERSION, CHECKPOINT_VERIFIER_VERSION,
            canonical, json.dumps(payload, default=_json_default), checkpoint_hash, signed.value, signed.algorithm,
            signed.key_id, signed.key_fingerprint, verified_at, verified_at,
        ),
    )
    return cursor.fetchone()


def audit_integrity_ledger(cursor, *, now: datetime | None = None, force_full: bool = False):
    now = now or datetime.now(timezone.utc)
    cursor.execute("SELECT pg_advisory_xact_lock(%s)", (LEDGER_LOCK_ID,))
    head = _ledger_head(cursor)
    latest = _latest_checkpoint(cursor)
    checkpoint_status = ledger_checkpoint_status(cursor) if latest else None
    if latest and checkpoint_status["status"] == "unavailable":
        raise IntegritySigningError("O checkpoint anterior não pôde ser validado com segurança.")
    if latest and checkpoint_status["status"] == "failed" and latest["status"] == "valid":
        return checkpoint_status
    cursor.execute(
        """SELECT verified_at FROM integrity_ledger_checkpoints
           WHERE audit_type='full' AND status='valid'
           ORDER BY checkpoint_sequence DESC LIMIT 1"""
    )
    last_full = cursor.fetchone()
    full_due = not last_full or last_full["verified_at"] <= now - FULL_AUDIT_INTERVAL
    audit_type = "full" if force_full or not latest or latest["status"] == "invalid" or full_due else "incremental"
    if (
        audit_type == "incremental"
        and checkpoint_status
        and checkpoint_status["status"] == "verified"
    ):
        return checkpoint_status
    if audit_type == "full":
        start_sequence = 1
        expected_previous_hash = ""
    else:
        start_sequence = int(latest["last_event_sequence"]) + 1
        expected_previous_hash = latest["last_event_hash"]
    verification = _verify_integrity_ledger_segment(
        cursor,
        start_sequence=start_sequence,
        through_sequence=head["sequence"],
        expected_previous_hash=expected_previous_hash,
    )
    verification.update(
        {
            "first_event_sequence": start_sequence if start_sequence <= head["sequence"] else None,
            "current_sequence": head["sequence"],
            "current_event_hash": head["event_hash"],
        }
    )
    checkpoint = _create_ledger_checkpoint(cursor, verification, audit_type=audit_type, verified_at=now)
    return {
        "status": "verified" if verification["valid"] else "failed",
        "valid": bool(verification["valid"]),
        "invalid_market_ids": verification["invalid_market_ids"],
        "current_sequence": head["sequence"],
        "current_event_hash": head["event_hash"],
        "verified_through_sequence": checkpoint["last_event_sequence"],
        "verified_at": checkpoint["verified_at"],
        "audit_type": checkpoint["audit_type"],
        "pending_events": 0,
        "issue_code": checkpoint["issue_code"],
        "checkpoint": checkpoint,
    }


def verify_market_integrity_records(cursor, market: dict, *, ledger_audit=None):
    errors = []
    warnings = []
    ledger_audit = ledger_audit or ledger_checkpoint_status(cursor)

    cursor.execute("SELECT * FROM market_integrity_definitions WHERE market_id=%s", (market["id"],))
    definition = cursor.fetchone()
    definition_valid = definition_matches_current = None
    if definition:
        try:
            definition_payload = _json_object(definition["payload_json"])
            definition_valid = (
                hmac.compare_digest(sha256_hex(bytes(definition["canonical_payload"])), definition["payload_hash"])
                and hmac.compare_digest(sha256_hex(canonical_json(definition_payload)), definition["payload_hash"])
                and verify_signed_hash(
                    definition["payload_hash"],
                    bytes(definition["signature"]),
                    public_key_der_for(definition["key_id"], cursor=cursor),
                )
            )
            current_definition = market_definition_payload(
                cursor,
                market["id"],
                published_at=market["published_at"],
                definition_version=definition["definition_version"],
                signed_snapshot=definition_payload,
            )
            definition_matches_current = hmac.compare_digest(
                sha256_hex(canonical_json(current_definition)), definition["payload_hash"]
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            definition_valid = False
            definition_matches_current = False
        if not definition_valid:
            errors.append("definition_invalid")
        if not definition_matches_current:
            errors.append("definition_changed")
    elif market["status"] not in {"draft", "scheduled"}:
        errors.append("definition_missing")

    cursor.execute(
        """SELECT pc.id,pc.market_id commitment_market_id,pc.definition_id,pc.previous_commitment_id,pc.protocol_version,
                  pc.canonical_payload,pc.payload_json,pc.commitment_hash,pc.signature,
                  pc.algorithm,pc.key_id,pc.key_fingerprint,pc.signed_at,
                  p.id prediction_id,p.user_id,p.market_id prediction_market_id,
                  p.market_option_id,p.action_type,p.position_sequence,p.stake_amount,p.created_at prediction_created_at
           FROM gotrendlabs_predictions p
           LEFT JOIN prediction_commitments pc ON pc.prediction_id=p.id
           WHERE p.market_id=%s
           ORDER BY p.user_id,p.position_sequence,p.id,pc.id""",
        (market["id"],),
    )
    commitments = cursor.fetchall()
    previous_by_user = {}
    commitments_valid = True
    missing_commitment = False
    for commitment in commitments:
        previous = previous_by_user.get(commitment["user_id"])
        if commitment["id"] is None:
            missing_commitment = True
            commitments_valid = False
            continue
        payload = _json_object(commitment["payload_json"])
        expected_previous_id = previous["id"] if previous else None
        expected_previous_hash = previous["commitment_hash"] if previous else None
        try:
            commitment_public_key = public_key_der_for(commitment["key_id"], cursor=cursor)
            valid_commitment = (
                hmac.compare_digest(sha256_hex(bytes(commitment["canonical_payload"])), commitment["commitment_hash"])
                and hmac.compare_digest(sha256_hex(canonical_json(payload)), commitment["commitment_hash"])
                and verify_signed_hash(
                    commitment["commitment_hash"],
                    bytes(commitment["signature"]),
                    commitment_public_key,
                )
                and hmac.compare_digest(sha256_hex(commitment_public_key), commitment["key_fingerprint"])
                and commitment["protocol_version"] == PROTOCOL_VERSION
                and payload.get("protocol_version") == commitment["protocol_version"]
                and commitment["previous_commitment_id"] == expected_previous_id
                and payload.get("previous_commitment_hash") == expected_previous_hash
                and payload.get("position_sequence") == commitment["position_sequence"]
                and payload.get("action_id") == f"prediction:{commitment['prediction_id']}"
                and payload.get("action_type") == commitment["action_type"]
                and payload.get("market_id") == commitment["prediction_market_id"]
                and commitment["commitment_market_id"] == commitment["prediction_market_id"]
                and payload.get("option_id") == commitment["market_option_id"]
                and payload.get("stake") == int(commitment["stake_amount"])
                and payload.get("server_timestamp") == _json_default(commitment["prediction_created_at"])
                and payload.get("user_commitment") == _user_commitment(commitment["user_id"])
                and bool(definition)
                and commitment["definition_id"] == definition["id"]
                and payload.get("definition_version") == definition["definition_version"]
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            valid_commitment = False
        commitments_valid = commitments_valid and valid_commitment
        previous_by_user[commitment["user_id"]] = commitment
    if missing_commitment:
        errors.append("prediction_commitment_missing")
    if not commitments_valid and not missing_commitment:
        errors.append("prediction_commitment_invalid")

    cursor.execute("SELECT * FROM market_seals WHERE market_id=%s", (market["id"],))
    seal = cursor.fetchone()
    seal_valid = merkle_valid = result_matches_current = None
    if seal:
        try:
            seal_payload = _json_object(seal["payload_json"])
            signed_result = seal_payload.get("result") or {}
            signed_result_hash = sha256_hex(canonical_json(signed_result))
            seal_valid = (
                hmac.compare_digest(sha256_hex(bytes(seal["canonical_payload"])), seal["seal_hash"])
                and hmac.compare_digest(sha256_hex(canonical_json(seal_payload)), seal["seal_hash"])
                and verify_signed_hash(
                    seal["seal_hash"],
                    bytes(seal["signature"]),
                    public_key_der_for(seal["key_id"], cursor=cursor),
                )
                and hmac.compare_digest(seal_payload.get("result_hash", ""), seal["result_hash"])
                and hmac.compare_digest(signed_result_hash, seal["result_hash"])
                and hmac.compare_digest(seal_payload.get("predictions_root", ""), seal["predictions_root"])
                and bool(definition)
                and hmac.compare_digest(seal_payload.get("definition_hash", ""), definition["payload_hash"])
            )
            result_matches_current = hmac.compare_digest(
                sha256_hex(canonical_json(market_result_payload(market))), seal["result_hash"]
            )
            cursor.execute(
                """SELECT ml.commitment_id,ml.leaf_hash,ml.proof
                   FROM market_merkle_leaves ml
                   WHERE ml.seal_id=%s ORDER BY ml.leaf_index""",
                (seal["id"],),
            )
            leaves = cursor.fetchall()
            commitment_by_id = {row["id"]: row for row in commitments}
            leaves_match = len(leaves) == len(commitments) and all(
                row["commitment_id"] in commitment_by_id
                and hmac.compare_digest(row["leaf_hash"], commitment_by_id[row["commitment_id"]]["commitment_hash"])
                for row in leaves
            )
            calculated_root, _ = build_merkle([row["leaf_hash"] for row in leaves])
            merkle_valid = (
                leaves_match
                and hmac.compare_digest(calculated_root, seal["predictions_root"])
                and all(
                    verify_merkle_proof(row["leaf_hash"], _json_object(row["proof"]), seal["predictions_root"])
                    for row in leaves
                )
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            seal_valid = False
            result_matches_current = False
            merkle_valid = False
        if not seal_valid:
            errors.append("seal_invalid")
        if not result_matches_current:
            errors.append("result_changed")
        if not merkle_valid:
            errors.append("merkle_invalid")
    elif market["status"] == "resolved":
        cursor.execute(
            """SELECT payload_hash FROM integrity_ledger_events
               WHERE market_id=%s AND event_type='market_resolved'
               ORDER BY sequence DESC LIMIT 1""",
            (market["id"],),
        )
        resolution_event = cursor.fetchone()
        current_resolution = {
            "winning_option_id": market["winning_option_id"],
            "resolved_at": market["resolved_at"],
            "seal_due_at": market["seal_due_at"],
            "resolution_note": market["resolution_note"] or "",
        }
        result_matches_current = bool(resolution_event) and hmac.compare_digest(
            sha256_hex(canonical_json(current_resolution)), resolution_event["payload_hash"]
        )
        if not result_matches_current:
            errors.append("result_changed")

    ledger_valid = ledger_audit.get("valid")
    market_events_valid = market["id"] not in ledger_audit["invalid_market_ids"]
    if ledger_audit["status"] == "failed":
        warnings.append("ledger_chain_invalid")
    elif ledger_audit["status"] == "pending":
        warnings.append("ledger_verification_pending")
    elif ledger_audit["status"] == "unavailable":
        warnings.append("ledger_verification_unavailable")
    if not market_events_valid:
        errors.append("market_events_invalid")
    definition_applicable = market["status"] not in {"draft", "scheduled"}
    market_valid = None if not definition_applicable and not definition else (
        bool(definition_valid and definition_matches_current)
        and commitments_valid
        and market_events_valid
        and (market["status"] != "resolved" or bool(result_matches_current))
        and (market["status"] != "sealed" or bool(seal_valid and result_matches_current and merkle_valid))
    )
    if market_valid is False or ledger_valid is False:
        overall_valid = False
    elif market_valid is None or ledger_valid is None:
        overall_valid = None
    else:
        overall_valid = True
    if overall_valid is False:
        verification_status = "failed"
    elif ledger_audit["status"] == "unavailable":
        verification_status = "unavailable"
    elif overall_valid is None:
        verification_status = "pending"
    else:
        verification_status = "verified"
    return {
        "verification_status": verification_status,
        "market_valid": market_valid,
        "overall_valid": overall_valid,
        "definition_valid": definition_valid,
        "definition_matches_current": definition_matches_current,
        "seal_valid": seal_valid,
        "result_matches_current": result_matches_current,
        "prediction_commitments_valid": commitments_valid if definition else None,
        "merkle_root_valid": merkle_valid,
        "market_events_valid": market_events_valid,
        "ledger_chain_valid": ledger_valid,
        "ledger_verified_through_sequence": ledger_audit["verified_through_sequence"],
        "ledger_current_sequence": ledger_audit["current_sequence"],
        "ledger_pending_events": ledger_audit["pending_events"],
        "ledger_verified_at": _json_default(ledger_audit["verified_at"]) if ledger_audit["verified_at"] else None,
        "ledger_audit_type": ledger_audit["audit_type"],
        "errors": list(dict.fromkeys(errors)),
        "warnings": warnings,
    }


def seal_market(cursor, market: dict, *, sealed_at: datetime | None = None):
    sealed_at = sealed_at or datetime.now(timezone.utc)
    cursor.execute("SELECT * FROM market_seals WHERE market_id=%s", (market["id"],))
    existing = cursor.fetchone()
    if existing:
        return existing, False
    if market["status"] != "resolved" or not market["seal_due_at"] or market["seal_due_at"] > sealed_at:
        return None, False
    cursor.execute("SELECT * FROM market_integrity_definitions WHERE market_id=%s", (market["id"],))
    definition = cursor.fetchone()
    if not definition:
        raise IntegritySigningError("Mercado legado sem definicao original nao pode ser selado como prova nativa.")
    ledger_audit = audit_integrity_ledger(cursor, now=sealed_at)
    verification = verify_market_integrity_records(cursor, market, ledger_audit=ledger_audit)
    if verification["overall_valid"] is not True:
        issue_codes = verification["errors"] + verification["warnings"]
        details = ", ".join(issue_codes) if issue_codes else "verification_failed"
        raise IntegritySigningError(f"Mercado nao pode ser selado porque sua integridade falhou: {details}.")
    cursor.execute("""SELECT pc.*,p.position_sequence,p.id prediction_id FROM prediction_commitments pc
        JOIN gotrendlabs_predictions p ON p.id=pc.prediction_id
        WHERE pc.market_id=%s ORDER BY p.position_sequence,p.id,pc.id""", (market["id"],))
    commitments = cursor.fetchall()
    commitment_hashes = [row["commitment_hash"] for row in commitments]
    predictions_root, proofs = build_merkle(commitment_hashes)
    check_root, _ = build_merkle(commitment_hashes)
    if not hmac.compare_digest(predictions_root, check_root):
        raise IntegritySigningError("A raiz Merkle nao passou pela validacao independente.")
    result_payload = market_result_payload(market)
    result_hash = sha256_hex(canonical_json(result_payload))
    cursor.execute("SELECT event_hash FROM integrity_ledger_events ORDER BY sequence DESC LIMIT 1")
    previous = cursor.fetchone()
    previous_hash = previous["event_hash"] if previous else ""
    payload = {
        "definition_hash": definition["payload_hash"], "definition_version": definition["definition_version"],
        "market_id": market["id"], "market_slug": market["slug"], "predictions_root": predictions_root,
        "previous_event_hash": previous_hash, "protocol_version": PROTOCOL_VERSION,
        "result": result_payload, "result_hash": result_hash, "sealed_at": sealed_at,
    }
    canonical,digest,signed=sign_payload(payload)
    remember_public_key(cursor, signed, created_at=sealed_at)
    cursor.execute("""INSERT INTO market_seals
        (market_id,definition_id,protocol_version,predictions_root,result_hash,previous_event_hash,canonical_payload,payload_json,seal_hash,signature,algorithm,key_id,key_fingerprint,sealed_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s) RETURNING *""",
        (market["id"],definition["id"],PROTOCOL_VERSION,predictions_root,result_hash,previous_hash,canonical,json.dumps(payload,default=_json_default),digest,signed.value,signed.algorithm,signed.key_id,signed.key_fingerprint,sealed_at))
    seal = cursor.fetchone()
    for index, commitment in enumerate(commitments):
        cursor.execute("""INSERT INTO market_merkle_leaves (market_id,seal_id,commitment_id,leaf_index,leaf_hash,proof)
            VALUES (%s,%s,%s,%s,%s,%s::jsonb)""", (market["id"],seal["id"],commitment["id"],index,commitment["commitment_hash"],json.dumps(proofs[index])))
    append_ledger_event(cursor,event_type="market_sealed",entity_type="market",entity_identifier=market["slug"],market_id=market["id"],payload_reference=f"market_seal:{seal['id']}",payload_hash=digest,occurred_at=sealed_at)
    cursor.execute("UPDATE gotrendlabs_markets SET status='sealed',status_label='Selado',sealed_at=%s,updated_at=%s WHERE id=%s AND status='resolved'", (sealed_at,sealed_at,market["id"]))
    if cursor.rowcount != 1:
        raise IntegritySigningError("O estado do mercado mudou durante a selagem.")
    _notify_sealed(cursor, market, sealed_at)
    return seal, True


def _notify_sealed(cursor, market, sealed_at):
    from apps.api.backend_api.email_outbox import enqueue_user_email, public_url
    from apps.web.django.communications.push_services import enqueue_push_for_notification
    cursor.execute("""SELECT DISTINCT p.user_id FROM gotrendlabs_predictions p JOIN gotrendlabs_users u ON u.id=p.user_id
                      WHERE p.market_id=%s AND u.is_bot=false ORDER BY p.user_id""", (market["id"],))
    for row in cursor.fetchall():
        recipient_id = row["user_id"]
        cursor.execute("""INSERT INTO gotrendlabs_user_notifications
            (recipient_id,actor_id,market_id,comment_id,event_type,source_key,title,body,is_read,read_at,metadata,created_at)
            VALUES (%s,NULL,%s,NULL,'market_sealed',%s,'Histórico finalizado e verificável',%s,false,NULL,%s::jsonb,%s)
            ON CONFLICT (recipient_id,source_key) DO NOTHING RETURNING id""",
            (recipient_id,market["id"],f"market_sealed:{market['id']}","O registro deste mercado está disponível para conferência.",json.dumps({"sealed_at": _json_default(sealed_at),"route": f"/markets/{market['slug']}"}),sealed_at))
        created=cursor.fetchone()
        if created:
            enqueue_push_for_notification(cursor, created["id"])
        enqueue_user_email(cursor,event_type="market.sealed",user_id=recipient_id,template_key="market.sealed",context={"market_title":market["title"],"market_url":public_url(f"/markets/{market['slug']}/")},idempotency_key=f"market.sealed:{recipient_id}:{market['id']}")


def public_key_payload(key_id: str | None = None, *, cursor=None):
    signer = get_signer()
    resolved_key_id = key_id or signer.key_id
    public_der = public_key_der_for(resolved_key_id, cursor=cursor)
    pem = serialization.load_der_public_key(public_der).public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return {
        "protocol_version": PROTOCOL_VERSION,
        "algorithm": SIGNING_ALGORITHM,
        "key_id": resolved_key_id,
        "fingerprint": sha256_hex(public_der),
        "public_key_pem": pem,
    }


def public_key_der_for(key_id: str, *, cursor=None) -> bytes:
    if cursor is not None:
        cursor.execute("SELECT public_key_der FROM integrity_signing_keys WHERE key_id=%s", (key_id,))
        registered = cursor.fetchone()
        if registered:
            return bytes(registered["public_key_der"])
    signer = get_signer()
    if getattr(signer, "key_id", "") == key_id:
        return signer.public_key()
    if key_id.startswith("local-ephemeral-ed25519"):
        return b""
    try:
        return _KMSSigner(key_id)._public_key()
    except IntegritySigningError:
        raise
    except Exception as exc:
        raise IntegritySigningError(
            f"A chave publica historica ficou indisponivel ({exc.__class__.__name__})."
        ) from exc


def encode_signature(value: bytes) -> str:
    return base64.b64encode(bytes(value)).decode("ascii")
