"""Authoritative operational schedule; no lifecycle or financial side effects."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastapi import HTTPException
from pydantic import BaseModel, Field, ConfigDict, model_validator

DATES = ('expected_resolution_at',)
FIELDS = (*DATES, 'schedule_timezone')
PROJECTION = (*FIELDS, 'original_expected_resolution_at', 'schedule_version')
TERMINAL = {'resolved', 'sealed', 'canceled'}
LABELS = {
    'terminal': 'Decisão publicada ou mercado encerrado',
    'closure_inconsistent': 'Fechamento pendente de operação',
    'schedule_pending': 'Agenda pendente de revisão',
    'resolution_scheduled': 'Apuração prevista',
    'resolution_overdue': 'Previsão vencida',
}

def fail(code, message, status=422):
    raise HTTPException(status, {'code': code, 'message': message})


def validate_schedule(value, *, required=False, publishing=False, now=None):
    now = now or datetime.now(timezone.utc)
    present = [value.get(k) for k in DATES]
    zone = value.get('schedule_timezone')
    if not all(present) or not zone:
        if required:
            fail('schedule_incomplete', 'Informe a resolução prevista e seu fuso.')
    try:
        if zone:
            ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        fail('schedule_timezone_invalid', 'Informe fuso IANA válido.')
    for stamp in present:
        if stamp is not None and (stamp.tzinfo is None or stamp.utcoffset() is None):
            fail('schedule_offset_required', 'Cada instante exige offset explícito.')
    expected = present[0]
    close = value.get('close_at')
    if close and close.tzinfo is None and expected:
        fail('schedule_offset_required', 'Fechamento exige offset explícito.')
    if close and expected and expected <= close:
        fail('schedule_order_invalid', 'A resolução prevista deve ser posterior ao fechamento.')
    if publishing and any(stamp <= now for stamp in present if stamp):
        fail('schedule_expired', 'Publicação exige agenda futura.')


def preparation_pending(value):
    return ["schedule_incomplete"] if not all(value.get(k) for k in FIELDS) else []


class ScheduleFields(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Null is a deliberate incomplete draft, never a fabricated date.
    expected_resolution_at: datetime | None = None
    schedule_timezone: str = Field(default='', max_length=64)

    @model_validator(mode='after')
    def valid_schedule(self):
        try:
            validate_schedule(self.model_dump())
        except HTTPException as exc:
            raise ValueError(exc.detail['code']) from exc
        return self


class Reschedule(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_market_id: int = Field(gt=0)
    expected_version: int = Field(ge=1)
    expected_resolution_at: datetime
    reason: str = Field(min_length=1, max_length=2000)


def classification(market, *, now=None):
    now = now or datetime.now(timezone.utc)
    status = market['status']
    if status in TERMINAL:
        code = 'terminal'
    elif status in {'open', 'scheduled'} and market.get('close_at') and now >= market['close_at']:
        code = 'closure_inconsistent'
    elif not all(market.get(k) for k in FIELDS) or (status != 'draft' and not market.get('schedule_version')):
        code = 'schedule_pending'
    elif now > market['expected_resolution_at']:
        code = 'resolution_overdue'
    else:
        code = 'resolution_scheduled'
    return {'code': code, 'label': LABELS[code], 'as_of': now.isoformat(),
            'can_reschedule': status in {'open', 'locked'} and bool(market.get('schedule_version')),
            'can_resolve': status == 'locked' and code in {'resolution_scheduled', 'resolution_overdue'}}


def save_draft(cursor, market_id, payload):
    value = payload.model_dump() if hasattr(payload, 'model_dump') else payload
    validate_schedule(value)
    cursor.execute('SELECT status,schedule_version FROM gotrendlabs_markets WHERE id=%s FOR UPDATE', (market_id,))
    current = cursor.fetchone()
    if current['schedule_version'] or current['status'] not in {'draft', 'scheduled'}:
        cursor.execute('SELECT '+','.join(FIELDS)+' FROM gotrendlabs_markets WHERE id=%s', (market_id,))
        if dict(cursor.fetchone()) != {k:value.get(k) for k in FIELDS}:
            fail('schedule_protected', 'Use o reagendamento auditável para agenda publicada.')
        return
    cursor.execute('UPDATE gotrendlabs_markets SET '+','.join(k+'=%s' for k in FIELDS)+' WHERE id=%s',
                   (*[value.get(k) for k in FIELDS], market_id))


def history(cursor, market_id):
    cursor.execute("SELECT * FROM integrity_ledger_events WHERE market_id=%s AND event_type IN ('market_schedule_registered','market_schedule_rescheduled','market_evidence_recovery_updated') ORDER BY sequence", (market_id,))
    return cursor.fetchall()


def snapshot(market):
    return {k: market.get(k) for k in PROJECTION}


def record(cursor, market, *, actor_id, reason, provenance, before=None, event_type=None):
    from .integrity_service import append_ledger_event, canonical_json, sha256_hex
    cursor.execute('SELECT payload_hash FROM market_integrity_definitions WHERE market_id=%s', (market['id'],))
    definition = cursor.fetchone()
    if not definition:
        fail('schedule_definition_missing', 'Agenda assinada exige definição registrada.')
    data = {'definition_hash': definition['payload_hash'], 'before': before, 'after': snapshot(market),
            'actor_id': actor_id, 'reason': reason, 'provenance': provenance}
    append_ledger_event(cursor, event_type=event_type or ('market_schedule_registered' if before is None else 'market_schedule_rescheduled'),
        entity_type='market', entity_identifier=market['slug'], market_id=market['id'],
        payload_reference=f"market_schedule:{market['id']}:{market['schedule_version']}",
        payload_hash=sha256_hex(canonical_json(data)), payload_snapshot=data)


def register(cursor, market_id, *, actor_id, reason='Agenda inicial revisada', provenance=None):
    cursor.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s FOR UPDATE', (market_id,))
    market = cursor.fetchone()
    if market['schedule_version']:
        return
    validate_schedule(market, required=True)
    if market['status'] in TERMINAL:
        fail('schedule_terminal', 'Não fabricar agenda histórica em mercado terminal.')
    market.update(schedule_version=1, original_expected_resolution_at=market['expected_resolution_at'])
    record(cursor, market, actor_id=actor_id, reason=reason, provenance=provenance or {'origin':'publication'})
    cursor.execute('UPDATE gotrendlabs_markets SET schedule_version=1,original_expected_resolution_at=expected_resolution_at WHERE id=%s', (market_id,))


def reschedule(cursor, market_id, payload, *, actor_id):
    cursor.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s FOR UPDATE', (market_id,))
    market = cursor.fetchone()
    if not market or market['id'] != payload.expected_market_id:
        fail('market_identity_conflict', 'Mercado não corresponde ao alvo.', 409)
    if market['schedule_version'] != payload.expected_version:
        fail('schedule_version_conflict', 'Agenda alterada; atualize a página.', 409)
    if market['status'] not in {'open', 'locked'}:
        fail('schedule_terminal', 'Este estado não permite reagendamento.')
    if not payload.reason.strip():
        fail('schedule_reason_required', 'Informe motivo.')
    if verify(cursor, market):
        fail('schedule_integrity_failed', 'Agenda divergente do histórico; encaminhe para auditoria.', 409)
    if payload.expected_resolution_at.tzinfo is None:
        fail('schedule_offset_required', 'Cada instante exige offset explícito.')
    from .integrity_service import _json_object
    before = _json_object(history(cursor, market_id)[-1]['payload_json'])['payload_snapshot']['after']
    market.update(expected_resolution_at=payload.expected_resolution_at, schedule_version=market['schedule_version']+1)
    validate_schedule(market, required=True)
    if market['expected_resolution_at'] <= datetime.now(timezone.utc):
        fail('schedule_expired', 'Nova previsão deve estar no futuro.')
    record(cursor, market, actor_id=actor_id, reason=payload.reason.strip(), provenance={'origin':'staff_reschedule'}, before=before)
    cursor.execute('UPDATE gotrendlabs_markets SET expected_resolution_at=%s,schedule_version=%s,updated_by_id=%s,updated_at=%s WHERE id=%s',
        (market['expected_resolution_at'],market['schedule_version'],actor_id,datetime.now(timezone.utc),market_id))


def require_resolution(cursor, market_id):
    """Require a reviewed projection, never treat an operational forecast as a gate."""
    cursor.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s FOR UPDATE', (market_id,))
    market = cursor.fetchone()
    validate_schedule(market, required=True)
    if not market['schedule_version']:
        fail('schedule_pending', 'Agenda publicada exige revisão e complemento assinado.')
    if verify(cursor, market):
        fail('schedule_integrity_failed', 'Agenda divergente do histórico; encaminhe para auditoria.', 409)


def verify(cursor, market):
    from .integrity_service import _json_object, _ledger_event_is_valid, public_key_der_for, canonical_json, sha256_hex
    cursor.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s', (market['id'],))
    current = cursor.fetchone()
    events = history(cursor, market['id'])
    if not events:
        return ['schedule_history_missing'] if current['schedule_version'] else []
    cursor.execute('SELECT payload_hash FROM market_integrity_definitions WHERE market_id=%s', (market['id'],))
    definition = cursor.fetchone()
    previous = None
    for version, event in enumerate(events, 1):
        data = _json_object(event['payload_json']).get('payload_snapshot', {})
        after = data.get('after', {})
        if (not _ledger_event_is_valid(event, public_key_der_for(event['key_id'], cursor=cursor))
            or not definition or data.get('definition_hash') != definition['payload_hash']
            or sha256_hex(canonical_json(data)) != event['payload_hash']
            or data.get('before') != previous or after.get('schedule_version') != version
            or (previous is None and (event['event_type'] != 'market_schedule_registered' or after.get('original_expected_resolution_at') != after.get('expected_resolution_at')))
            or (previous and any(after.get(k) != previous.get(k) for k in ('schedule_timezone','original_expected_resolution_at')))):
            return ['schedule_history_invalid']
        previous = after
    import json
    from .integrity_service import _json_default
    # Retired columns exist only to verify the exact shape of previously signed snapshots.
    return [] if previous == json.loads(json.dumps({k:current.get(k) for k in previous},default=_json_default)) else ['schedule_projection_changed']
