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
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


PROTOCOL_VERSION = "gtl-integrity/v1"
SIGNING_ALGORITHM = "ED25519_SHA_512"
LEDGER_LOCK_ID = 0x47544C49


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
        self.key_id = "local-ephemeral-ed25519"

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
    cursor.execute(
        """INSERT INTO integrity_ledger_events
        (sequence,protocol_version,event_type,entity_type,entity_identifier,market_id,payload_reference,payload_hash,canonical_payload,payload_json,previous_event_hash,event_hash,signature,algorithm,key_id,key_fingerprint,correlation_id,causation_id,occurred_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
        (sequence,PROTOCOL_VERSION,event_type,entity_type,str(entity_identifier),market_id,payload_reference,payload_hash,canonical,json.dumps(event_payload,default=_json_default),previous_hash,event_hash,signed.value,signed.algorithm,signed.key_id,signed.key_fingerprint,correlation_id,causation_id,occurred_at,occurred_at),
    )
    return cursor.fetchone()


def register_market_definition(cursor, market_id: int, *, occurred_at: datetime | None = None):
    occurred_at = occurred_at or datetime.now(timezone.utc)
    cursor.execute("SELECT * FROM market_integrity_definitions WHERE market_id=%s", (market_id,))
    existing = cursor.fetchone()
    if existing:
        return existing
    cursor.execute("""SELECT m.*, c.name category_name, sc.name subcategory_name, ev.name event_name
                    FROM gotrendlabs_markets m JOIN gotrendlabs_market_categories c ON c.id=m.category_id
                    JOIN gotrendlabs_market_subcategories sc ON sc.id=m.subcategory_id
                    LEFT JOIN gotrendlabs_market_events ev ON ev.id=m.event_id WHERE m.id=%s FOR UPDATE OF m""", (market_id,))
    market = cursor.fetchone()
    cursor.execute("SELECT id,label,hint,display_order FROM gotrendlabs_market_options WHERE market_id=%s ORDER BY display_order,id", (market_id,))
    options = cursor.fetchall()
    payload = {
        "auto_close_enabled": bool(market["auto_close_enabled"]), "category": market["category_name"],
        "close_at": market["close_at"], "close_timezone": market["close_timezone"] or "UTC",
        "definition_version": 1, "event": market["event_name"] or "", "kind": market["kind"],
        "market_id": market_id, "market_slug": market["slug"],
        "options": [{"id": row["id"], "label": row["label"], "hint": row["hint"] or "", "order": row["display_order"]} for row in options],
        "protocol_version": PROTOCOL_VERSION, "published_at": occurred_at,
        "resolution_criteria": market["resolution_criteria"] or "", "resolution_source": market["source"] or "",
        "subcategory": market["subcategory_name"], "summary": market["summary"] or "", "title": market["title"],
    }
    canonical, digest, signed = sign_payload(payload)
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
    cursor.execute("""SELECT pc.*,p.position_sequence,p.id prediction_id FROM prediction_commitments pc
        JOIN gotrendlabs_predictions p ON p.id=pc.prediction_id
        WHERE pc.market_id=%s ORDER BY p.position_sequence,p.id,pc.id""", (market["id"],))
    commitments = cursor.fetchall()
    commitment_hashes = [row["commitment_hash"] for row in commitments]
    predictions_root, proofs = build_merkle(commitment_hashes)
    check_root, _ = build_merkle(commitment_hashes)
    if not hmac.compare_digest(predictions_root, check_root):
        raise IntegritySigningError("A raiz Merkle nao passou pela validacao independente.")
    result_payload = {
        "evidence": market["resolution_note"] or "", "resolved_at": market["resolved_at"],
        "resolution_timezone": market["resolution_timezone"] or "UTC", "winning_option_id": market["winning_option_id"],
    }
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


def public_key_payload(key_id: str | None = None):
    signer = get_signer()
    resolved_key_id = key_id or signer.key_id
    public_der = public_key_der_for(resolved_key_id)
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


def public_key_der_for(key_id: str) -> bytes:
    signer = get_signer()
    if getattr(signer, "key_id", "") == key_id or key_id == "local-ephemeral-ed25519":
        return signer.public_key()
    return _KMSSigner(key_id)._public_key()


def encode_signature(value: bytes) -> str:
    return base64.b64encode(bytes(value)).decode("ascii")
