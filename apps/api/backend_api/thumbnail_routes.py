from uuid import UUID
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response
from apps.api.backend_api.db import get_connection
from apps.api.backend_api import thumbnail_service as s

router = APIRouter()


@router.post(
    "/admin/markets/{slug}/thumbnails", response_model=s.JobResponse, status_code=202
)
def create(
    slug: str, payload: s.GeneratePayload, authorization: str = Header(default="")
):
    from apps.api.backend_api.main import _current_staff_user

    with get_connection() as conn, conn.cursor() as cursor:
        return s.request_job(
            cursor, slug, payload, _current_staff_user(cursor, authorization)
        )


@router.get("/admin/markets/{slug}/thumbnails", response_model=s.JobResponse | None)
def latest(slug: str, authorization: str = Header(default="")):
    from apps.api.backend_api.main import _current_staff_user

    with get_connection() as conn, conn.cursor() as cursor:
        staff = _current_staff_user(cursor, authorization)
        row = s.market(cursor, slug)
        s.require_draft(row)
        cursor.execute(
            """SELECT * FROM gotrendlabs_thumbnail_jobs WHERE market_id=%s
            AND (operator_id=%s OR state IN ('queued','running')) ORDER BY created_at DESC LIMIT 1""",
            (row["id"], staff["id"]),
        )
        job = cursor.fetchone()
        return s.serialize(job) if job else None


@router.get(
    "/admin/markets/{slug}/thumbnails/{request_id}", response_model=s.JobResponse
)
def status(slug: str, request_id: UUID, authorization: str = Header(default="")):
    from apps.api.backend_api.main import _current_staff_user

    with get_connection() as conn, conn.cursor() as cursor:
        _current_staff_user(cursor, authorization)
        row, job = s.get_job(cursor, slug, request_id)
        return s.serialize(job)


@router.get(
    "/admin/markets/{slug}/thumbnails/{request_id}/preview",
    responses={200: {"content": {"image/png": {}}}},
)
def preview(slug: str, request_id: UUID, authorization: str = Header(default="")):
    from apps.api.backend_api.main import _current_staff_user

    with get_connection() as conn, conn.cursor() as cursor:
        _current_staff_user(cursor, authorization)
        row, job = s.get_job(cursor, slug, request_id)
        s.require_draft(row)
        if s.serialize(job)["state"] != "succeeded":
            raise HTTPException(409, "Thumbnail indisponível.")
        return Response(
            s.candidate_bytes(job),
            media_type="image/png",
            headers={
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )


@router.get("/admin/thumbnail-settings", response_model=s.config.ThumbnailSettings)
def settings(authorization: str = Header(default="")):
    from apps.api.backend_api.main import _current_staff_user

    with get_connection() as conn, conn.cursor() as cursor:
        _current_staff_user(cursor, authorization)
        return s.config.load(cursor)


@router.put("/admin/thumbnail-settings", response_model=s.config.ThumbnailSettings)
def update_settings(
    payload: s.config.ThumbnailSettingsUpdate, authorization: str = Header(default="")
):
    from apps.api.backend_api.main import _current_staff_user

    with get_connection() as conn, conn.cursor() as cursor:
        return s.config.save(
            cursor, payload, _current_staff_user(cursor, authorization)
        )
