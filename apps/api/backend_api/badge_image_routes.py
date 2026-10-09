from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response
from apps.api.backend_api.db import get_connection
from apps.api.backend_api import badge_image_service as s

router = APIRouter()


def staff(cursor, authorization):
    from apps.api.backend_api.main import _current_staff_user

    return _current_staff_user(cursor, authorization)


@router.post(
    "/admin/badge-images/{editor_id}",
    response_model=s.common.JobResponse,
    status_code=202,
)
def create(
    editor_id: UUID, payload: s.GeneratePayload, authorization: str = Header(default="")
):
    with get_connection() as conn, conn.cursor() as cursor:
        return s.request_job(cursor, editor_id, payload, staff(cursor, authorization))


@router.get(
    "/admin/badge-images/{editor_id}", response_model=s.common.JobResponse | None
)
def latest(editor_id: UUID, authorization: str = Header(default="")):
    with get_connection() as conn, conn.cursor() as cursor:
        actor = staff(cursor, authorization)
        cursor.execute(
            "SELECT * FROM gotrendlabs_thumbnail_jobs WHERE kind='badge' AND editor_id=%s AND operator_id=%s AND session_id=%s ORDER BY created_at DESC LIMIT 1",
            (editor_id, actor["id"], actor["session_id"]),
        )
        job = cursor.fetchone()
        return s.serialize(job) if job else None


@router.get(
    "/admin/badge-images/{editor_id}/{request_id}", response_model=s.common.JobResponse
)
def status(editor_id: UUID, request_id: UUID, authorization: str = Header(default="")):
    with get_connection() as conn, conn.cursor() as cursor:
        return s.serialize(
            s.get_job(cursor, editor_id, request_id, staff(cursor, authorization))
        )


@router.get(
    "/admin/badge-images/{editor_id}/{request_id}/preview",
    responses={200: {"content": {"image/png": {}}}},
)
def preview(editor_id: UUID, request_id: UUID, theme: Literal["light", "dark"] = "light", authorization: str = Header(default="")):
    with get_connection() as conn, conn.cursor() as cursor:
        job = s.get_job(cursor, editor_id, request_id, staff(cursor, authorization))
        if s.serialize(job)["state"] != "succeeded":
            raise HTTPException(409, "Imagem indisponível.")
        return Response(
            s.candidate_bytes(job, theme),
            media_type="image/png",
            headers={
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )


@router.get("/admin/badge-image-settings", response_model=s.BadgeImageSettings)
def settings(authorization: str = Header(default="")):
    with get_connection() as conn, conn.cursor() as cursor:
        staff(cursor, authorization)
        return s.settings(cursor)


@router.put("/admin/badge-image-settings", response_model=s.BadgeImageSettings)
def update_settings(
    payload: s.BadgeImageSettings, authorization: str = Header(default="")
):
    with get_connection() as conn, conn.cursor() as cursor:
        return s.save_settings(cursor, payload, staff(cursor, authorization))
