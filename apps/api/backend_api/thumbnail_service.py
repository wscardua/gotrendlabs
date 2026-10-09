"""Persistent administrative thumbnail domain. No provider call in HTTP transactions."""

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field
from apps.api.backend_api import thumbnail_settings as config

VERSION = "market-thumbnail-bedrock-v2"
ACTIVE = ("queued", "running")
PROMOTION_LOCK = 73019012


def now():
    return datetime.now(timezone.utc)


def number(name, default):
    return max(1, int(os.environ.get("GTL_THUMB_" + name, default)))


def enabled(cursor, policy=None):
    return (
        os.environ.get("GTL_THUMB_ENABLED", "0").lower() in {"1", "true"}
        and (policy or config.load(cursor)).thumbnail_enabled
    )


def private_root():
    return Path(os.environ.get("GTL_THUMB_PRIVATE_ROOT", ".runtime/thumbnail_private"))


def public_root(kind="market"):
    if kind == "badge":
        return Path(os.environ.get("GTL_BADGE_PUBLIC_ROOT", "media/badge_images"))
    return Path(os.environ.get("GTL_THUMB_PUBLIC_ROOT", "media/market_thumbnails"))


class GeneratePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(min_length=1, max_length=4000)
    category: str = Field(min_length=1, max_length=80)
    subcategory: str = Field(min_length=1, max_length=80)
    event: str = Field(default="", max_length=80)

    def context(self):
        values = self.model_dump(exclude={"request_id"})
        if any(
            not values[k].strip()
            for k in ("title", "summary", "category", "subcategory")
        ):
            raise HTTPException(
                422, "Preencha pergunta, resumo, categoria e subcategoria para gerar."
            )
        return {k: v.strip() for k, v in values.items()}


class JobResponse(BaseModel):
    request_id: UUID
    state: str
    snapshot_hash: str
    snapshot: dict
    candidate_id: UUID | None = None
    expires_at: datetime
    message: str


def event(cursor, actor, action, job):
    from apps.api.backend_api.admin_events import record_admin_event

    kind = job.get("kind", "market")
    entity = str(job["market_id"]) if kind == "market" else str(job.get("badge_id") or job["editor_id"])
    record_admin_event(cursor, actor, action, kind, entity, str(job["id"]))


def market(cursor, slug, lock=False):
    cursor.execute(
        "SELECT id,status,image_url FROM gotrendlabs_markets WHERE slug=%s"
        + (" FOR UPDATE" if lock else ""),
        (slug,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, "Mercado não encontrado.")
    return row


def require_draft(row):
    if row["status"] != "draft":
        raise HTTPException(409, "A geração está disponível apenas em rascunhos.")


def serialize(job):
    messages = {
        "queued": "Gerando thumbnail…",
        "running": "Gerando thumbnail…",
        "succeeded": "Thumbnail pronta para o próximo salvamento.",
        "failed": "Não foi possível gerar. Tente novamente.",
        "uncertain": "Não foi possível confirmar a geração. Uma nova tentativa será uma nova solicitação.",
        "expired": "Esta thumbnail expirou. Gere outra.",
    }
    state = job["state"]
    if state == "succeeded" and job["expires_at"] <= now():
        state = "expired"
    return dict(
        request_id=job["id"],
        state=state,
        snapshot_hash=job["snapshot_hash"],
        snapshot=job["snapshot"],
        candidate_id=job["id"] if state == "succeeded" else None,
        expires_at=job["expires_at"],
        message=messages[state],
    )


def request_job(cursor, slug, payload, staff):
    context = payload.context()
    digest = hashlib.sha256(
        json.dumps(context, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    # Serialize all reservations, including global limit. This lock ends before provider I/O.
    cursor.execute("SELECT pg_advisory_xact_lock(%s)", (73019011,))
    row = market(cursor, slug, lock=True)
    require_draft(row)
    cursor.execute(
        "SELECT * FROM gotrendlabs_thumbnail_jobs WHERE id=%s", (payload.request_id,)
    )
    existing = cursor.fetchone()
    if existing:
        if (
            existing["market_id"] != row["id"]
            or existing["operator_id"] != staff["id"]
            or existing["snapshot_hash"] != digest
        ):
            raise HTTPException(409, "Identidade da solicitação já utilizada.")
        return serialize(existing)
    policy = config.load(cursor)
    if not enabled(cursor, policy):
        raise HTTPException(503, "Geração de thumbnails indisponível no momento.")
    cursor.execute(
        "SELECT id FROM gotrendlabs_thumbnail_jobs WHERE market_id=%s AND state IN ('queued','running')",
        (row["id"],),
    )
    if cursor.fetchone():
        raise HTTPException(409, "Já existe uma geração neste mercado. Aguarde.")
    cursor.execute(
        """SELECT COALESCE(sum(CASE WHEN instructions_version='badge-image-bedrock-pair-v2' THEN 2 ELSE 1 END),0) AS global_count,
        COALESCE(sum(CASE WHEN instructions_version='badge-image-bedrock-pair-v2' THEN 2 ELSE 1 END) FILTER (WHERE operator_id=%s),0) AS operator_count,
        count(*) FILTER (WHERE market_id=%s) AS market_count
        FROM gotrendlabs_thumbnail_jobs WHERE created_at >= %s""",
        (
            staff["id"],
            row["id"],
            now() - timedelta(hours=policy.thumbnail_period_hours),
        ),
    )
    counts = cursor.fetchone()
    if any(
        counts[key] >= min(limit, int(os.environ.get("GTL_THUMB_" + name, limit)))
        for key, name, limit in (
            ("global_count", "GLOBAL_LIMIT", policy.thumbnail_global_limit),
            ("operator_count", "OPERATOR_LIMIT", policy.thumbnail_operator_limit),
            ("market_count", "MARKET_LIMIT", policy.thumbnail_market_limit),
        )
    ):
        raise HTTPException(429, "Limite de geração atingido. Tente mais tarde.")
    cursor.execute(
        """INSERT INTO gotrendlabs_thumbnail_jobs
        (id,market_id,operator_id,session_id,snapshot,snapshot_hash,instructions_version,orchestrator,image_model,provider,provider_config,state,expires_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'queued',%s) RETURNING *""",
        (
            payload.request_id,
            row["id"],
            staff["id"],
            staff["session_id"],
            Jsonb(context),
            digest,
            VERSION,
            "",
            policy.thumbnail_model,
            "bedrock",
            Jsonb(
                {
                    "region": policy.thumbnail_region,
                    "aspect_ratio": policy.thumbnail_aspect_ratio,
                    "timeout_seconds": policy.thumbnail_timeout_seconds,
                    "seed": payload.request_id.int % 4294967294 + 1,
                }
            ),
            now() + timedelta(hours=policy.thumbnail_retention_hours),
        ),
    )
    job = cursor.fetchone()
    event(cursor, staff["id"], "thumbnail.request", job)
    return serialize(job)


def get_job(cursor, slug, request_id):
    row = market(cursor, slug)
    cursor.execute(
        "SELECT * FROM gotrendlabs_thumbnail_jobs WHERE id=%s AND market_id=%s",
        (request_id, row["id"]),
    )
    job = cursor.fetchone()
    if not job:
        raise HTTPException(404, "Solicitação não encontrada.")
    return row, job


def validate_image(raw):
    if not raw or len(raw) > 5 * 1024 * 1024:
        raise ValueError("invalid_image_size")
    try:
        img = Image.open(BytesIO(raw))
        if (
            img.format not in {"PNG", "JPEG", "WEBP"}
            or not 256 <= img.width <= 4096
            or not 256 <= img.height <= 4096
            or img.width * img.height > 20_000_000
        ):
            raise ValueError("invalid_image_dimensions")
        img.verify()
        img = Image.open(BytesIO(raw)).convert("RGB")
        output = BytesIO()
        img.save(output, "PNG")
        result = output.getvalue()
        if len(result) > 5 * 1024 * 1024:
            raise ValueError("invalid_image_size")
        return result
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("invalid_image") from exc


def discard_partial(path):
    # A failed compensation must not hide the storage failure or leave a job running.
    # Persistent orphan cleanup will try again once storage permissions recover.
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def candidate_bytes(job):
    path = private_root() / (str(job["id"]) + ".png")
    try:
        return validate_image(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise HTTPException(409, "Thumbnail indisponível. Gere outra.") from exc


def confirm(cursor, row, payload, staff):
    require_draft(row)
    if (
        payload.thumbnail_expected_image_url is None
        or payload.thumbnail_expected_image_url != (row["image_url"] or "")
    ):
        raise HTTPException(
            409, "A imagem do mercado mudou. Recarregue antes de salvar."
        )
    cursor.execute("SELECT pg_advisory_xact_lock(%s)", (PROMOTION_LOCK,))
    cursor.execute(
        "SELECT * FROM gotrendlabs_thumbnail_jobs WHERE id=%s AND market_id=%s FOR UPDATE",
        (payload.thumbnail_candidate_id, row["id"]),
    )
    job = cursor.fetchone()
    if not job or job["state"] != "succeeded" or job["expires_at"] <= now():
        raise HTTPException(409, "Thumbnail inválida ou expirada. Gere outra.")
    data = candidate_bytes(job)
    name = str(uuid4()) + ".png"
    root = public_root()
    try:
        root.mkdir(parents=True, exist_ok=True)
        with (root / name).open("xb") as target:
            target.write(data)
    except OSError as exc:
        discard_partial(root / name)
        raise HTTPException(
            503, "Não foi possível armazenar a thumbnail. Tente novamente."
        ) from exc
    cursor.execute(
        "UPDATE gotrendlabs_thumbnail_jobs SET applied_at=%s,applied_by_id=%s,public_name=%s WHERE id=%s",
        (now(), staff["id"], name, job["id"]),
    )
    event(cursor, staff["id"], "thumbnail.apply", job)
    return "/media/market_thumbnails/" + name
