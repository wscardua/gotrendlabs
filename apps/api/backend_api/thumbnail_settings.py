"""Validated, persisted thumbnail policy; credentials never enter this contract."""

import json
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

MODEL_CHOICES = (
    ("stability.stable-image-core-v1:1", "Stable Image Core — econômico"),
    ("stability.sd3-5-large-v1:0", "Stable Diffusion 3.5 Large"),
    ("stability.stable-image-ultra-v1:1", "Stable Image Ultra"),
)


class ThumbnailSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thumbnail_enabled: bool = False
    thumbnail_model: Literal[
        "stability.stable-image-core-v1:1",
        "stability.sd3-5-large-v1:0",
        "stability.stable-image-ultra-v1:1",
    ] = "stability.stable-image-core-v1:1"
    thumbnail_region: Literal["us-west-2"] = "us-west-2"
    thumbnail_aspect_ratio: Literal["3:2", "16:9", "1:1"] = "3:2"
    thumbnail_timeout_seconds: int = Field(default=180, ge=10, le=600)
    thumbnail_operator_limit: int = Field(default=10, ge=1, le=10000)
    thumbnail_market_limit: int = Field(default=5, ge=1, le=1000)
    thumbnail_global_limit: int = Field(default=50, ge=1, le=100000)
    thumbnail_period_hours: int = Field(default=24, ge=1, le=720)
    thumbnail_retention_hours: int = Field(default=24, ge=1, le=720)


FIELDS = tuple(ThumbnailSettings.model_fields)


class ThumbnailSettingsUpdate(ThumbnailSettings):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"required": list(FIELDS)}
    )

    @model_validator(mode="before")
    @classmethod
    def require_complete_payload(cls, values):
        if isinstance(values, dict) and set(FIELDS) - values.keys():
            raise ValueError("Envie todos os parâmetros de thumbnails.")
        return values


def load(cursor):
    cursor.execute(
        "SELECT "
        + ",".join(FIELDS)
        + " FROM gotrendlabs_site_config WHERE singleton_key=1"
    )
    row = cursor.fetchone()
    return ThumbnailSettings.model_validate(row or {})


def save(cursor, payload, staff):
    from apps.api.backend_api.main import _record_admin_event

    cursor.execute(
        "SELECT singleton_key FROM gotrendlabs_site_config WHERE singleton_key=1 FOR UPDATE"
    )
    if not cursor.fetchone():
        raise HTTPException(
            409, "Inicialize as Configurações do Sistema antes de alterar thumbnails."
        )
    previous = load(cursor).model_dump()
    values = payload.model_dump()
    cursor.execute(
        "UPDATE gotrendlabs_site_config SET "
        + ",".join(k + "=%s" for k in FIELDS)
        + ",updated_by_id=%s,updated_at=NOW() WHERE singleton_key=1",
        (*values.values(), staff["id"]),
    )
    changed = [k for k in FIELDS if values[k] != previous[k]]
    _record_admin_event(
        cursor,
        staff["id"],
        "thumbnail.settings_update",
        "site_config",
        "thumbnails",
        json.dumps({k: {"before": previous[k], "after": values[k]} for k in changed}),
    )
    return payload
