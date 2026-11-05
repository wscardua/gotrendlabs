"""Per-worker admission control for Django ORM and downstream API calls."""

import os
import threading
from html import escape

from django.http import HttpResponse
from django.db import InterfaceError, OperationalError


_limit = int(os.environ.get("GOTRENDLABS_WEB_CONCURRENCY", "5"))
if _limit < 1:
    raise ValueError("GOTRENDLABS_WEB_CONCURRENCY must be positive")
_available = threading.BoundedSemaphore(_limit)
_waiting_limit = int(os.environ.get("GOTRENDLABS_WEB_WAITING", "20"))
if _waiting_limit < 1:
    raise ValueError("GOTRENDLABS_WEB_WAITING must be positive")
_waiting = threading.BoundedSemaphore(_waiting_limit)


def _unavailable(request):
    action = (
        f'<p><a href="{escape(request.path, quote=True)}">Tentar novamente</a></p>'
        if request.method in {"GET", "HEAD"}
        else '<p><a href="/">Voltar ao início</a></p>'
    )
    response = HttpResponse(
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
        '<title>Temporariamente indisponível</title><body>'
        '<h1>Serviço temporariamente indisponível</h1>'
        '<p>Tente novamente em alguns instantes.</p>'
        f'{action}</body></html>',
        status=503,
    )
    response["Cache-Control"] = "no-store"
    return response


class RequestCapacityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        acquired = _available.acquire(blocking=False)
        if not acquired:
            if not _waiting.acquire(blocking=False):
                return _unavailable(request)
            try:
                acquired = _available.acquire(timeout=0.75)
            finally:
                _waiting.release()
            if not acquired:
                return _unavailable(request)
        try:
            return self.get_response(request)
        finally:
            _available.release()

    def process_exception(self, _request, exception):
        if isinstance(exception, (InterfaceError, OperationalError)):
            return _unavailable(_request)
        return None
