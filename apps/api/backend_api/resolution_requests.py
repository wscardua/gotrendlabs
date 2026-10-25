"""Atomic receipts for administrative resolution; caller holds the market lock."""
from fastapi import HTTPException
from apps.api.backend_api.integrity_service import canonical_json, sha256_hex


def conflict(code, message):
    raise HTTPException(status_code=409, detail={"code": code, "message": message})


def request_hash(payload):
    return sha256_hex(canonical_json(payload.model_dump(mode="json", exclude={"idempotency_key"})))


def confirmed_request(cursor, market, key, *, payload_hash=None):
    cursor.execute("SELECT * FROM gotrendlabs_market_resolution_requests WHERE idempotency_key=%s", (key,))
    receipt = cursor.fetchone()
    if not receipt:
        return False
    if receipt["market_id"] != market["id"] or (payload_hash is not None and receipt["request_hash"] != payload_hash):
        conflict("resolution_request_conflict", "Esta operação já foi utilizada com outro conteúdo. Reabra a página para uma nova operação.")
    if market["status"] not in {"resolved", "sealed"} or market["seal_due_at"] != receipt["seal_due_at"]:
        conflict("resolution_request_superseded", "Esta resolução foi desfeita ou substituída. Atualize a página para consultar o estado atual.")
    return True


def record_request(cursor, market, payload, payload_hash):
    cursor.execute("""INSERT INTO gotrendlabs_market_resolution_requests
        (idempotency_key, market_id, request_hash, seal_due_at, created_at)
        VALUES (%s,%s,%s,%s,CURRENT_TIMESTAMP)
        ON CONFLICT (idempotency_key) DO NOTHING RETURNING id""",
        (payload.idempotency_key, market["id"], payload_hash, market["seal_due_at"]))
    if not cursor.fetchone():
        # Cross-market key reuse can race; raising here rolls back every effect.
        conflict("resolution_request_conflict", "Esta chave de operação já foi utilizada. Atualize a página.")
