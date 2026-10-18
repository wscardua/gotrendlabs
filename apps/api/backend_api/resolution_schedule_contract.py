"""Pure schedule contract shared by FastAPI and the isolated MCP image."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, model_validator

DATES = ('expected_resolution_at',)

class ScheduleValidationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(code)

def fail(code, message):
    raise ScheduleValidationError(code, message)


def validate_schedule_value(value, *, required=False, publishing=False, now=None):
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



class ScheduleFields(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Null is a deliberate incomplete draft, never a fabricated date.
    expected_resolution_at: datetime | None = None
    schedule_timezone: str = Field(default='', max_length=64)

    @model_validator(mode='after')
    def valid_schedule(self):
        try:
            validate_schedule_value(self.model_dump())
        except ScheduleValidationError as exc:
            raise ValueError(exc.code) from exc
        return self

