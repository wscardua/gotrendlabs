"""Session/CSRF adapter. FastAPI validates permissions and market state for every call."""

import json
import urllib.error
import urllib.request
from uuid import UUID
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from apps.web.django.accounts.session import admin_api_required, auth_token
from apps.web.django.accounts.api_client import _request, _http_urlopen, AuthAPIError


def output(slug, job):
    if job and job.get("candidate_id"):
        job["preview_url"] = reverse(
            "admin-ops-thumbnail-preview",
            kwargs={"slug": slug, "request_id": job["request_id"]},
        )
    return job


@admin_api_required
@require_http_methods(["GET", "POST"])
def jobs(request, slug, request_id=None):
    path = "/admin/markets/" + slug + "/thumbnails"
    try:
        if request_id:
            UUID(str(request_id))
            path += "/" + str(request_id)
        if request.method == "POST" and request_id:
            return JsonResponse({"message": "Método não permitido."}, status=405)
        payload = json.loads(request.body) if request.method == "POST" else None
        job = _request(request.method, path, payload, token=auth_token(request))
        response = JsonResponse(
            output(slug, job),
            safe=False,
            status=202 if request.method == "POST" else 200,
        )
    except (ValueError, TypeError):
        response = JsonResponse({"message": "Dados inválidos."}, status=400)
    except AuthAPIError as exc:
        response = JsonResponse({"message": str(exc)}, status=exc.status_code or 503)
    response["Cache-Control"] = "private, no-store"
    return response


@admin_api_required
@require_http_methods(["GET"])
def preview(request, slug, request_id):
    path = f"/admin/markets/{slug}/thumbnails/{request_id}/preview"
    upstream = urllib.request.Request(
        settings.BACKEND_API_URL + path,
        headers={"Authorization": "Bearer " + auth_token(request)},
    )
    try:
        with _http_urlopen(upstream, timeout=5) as stream:
            raw = stream.read(5 * 1024 * 1024 + 1)
            if (
                stream.headers.get_content_type() != "image/png"
                or len(raw) > 5 * 1024 * 1024
            ):
                raise ValueError
            response = HttpResponse(raw, content_type="image/png")
    except (urllib.error.URLError, AuthAPIError, ValueError) as exc:
        response = HttpResponse(
            "Thumbnail indisponível.", status=getattr(exc, "code", 503)
        )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
