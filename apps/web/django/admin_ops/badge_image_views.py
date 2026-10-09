"""Administrative session and CSRF adapters; no image generation in Django."""

import json
import urllib.error
import urllib.request
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from apps.web.django.accounts.session import admin_api_required, auth_token
from apps.web.django.accounts.api_client import _request, _http_urlopen, AuthAPIError


@admin_api_required
@require_http_methods(["GET", "POST"])
def jobs(request, editor_id, request_id=None):
    path = f"/admin/badge-images/{editor_id}"
    if request_id:
        path += "/" + str(request_id)
        if request.method == "POST":
            return JsonResponse({"message": "Método não permitido."}, status=405)
    try:
        job = _request(
            request.method,
            path,
            json.loads(request.body) if request.method == "POST" else None,
            token=auth_token(request),
        )
        if job and job.get("candidate_id"):
            job["preview_url"] = reverse(
                "admin-ops-badge-image-preview",
                kwargs={"editor_id": editor_id, "request_id": job["request_id"]},
            )
            job["preview_dark_url"] = job["preview_url"] + "?theme=dark"
        response = JsonResponse(
            job, safe=False, status=202 if request.method == "POST" else 200
        )
    except (ValueError, TypeError):
        response = JsonResponse({"message": "Dados inválidos."}, status=400)
    except AuthAPIError as exc:
        response = JsonResponse({"message": str(exc)}, status=exc.status_code or 503)
    response["Cache-Control"] = "private, no-store"
    return response


@admin_api_required
@require_http_methods(["GET"])
def preview(request, editor_id, request_id):
    theme = request.GET.get("theme", "light")
    if theme not in {"light", "dark"}:
        return HttpResponse("Tema inválido.", status=400)
    upstream = urllib.request.Request(
        settings.BACKEND_API_URL
        + f"/admin/badge-images/{editor_id}/{request_id}/preview?theme={theme}",
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
            "Imagem indisponível.", status=getattr(exc, "code", 503)
        )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
