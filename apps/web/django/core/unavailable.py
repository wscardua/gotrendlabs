"""A response that can be rendered while both the API and database are down."""

from html import escape

from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.translation import gettext as _


def unavailable_response(request, error, *, login_url=None):
    if error.status_code == 404:
        raise Http404(_("Mercado não encontrado."))
    if error.status_code == 401 and login_url:
        return redirect(login_url)
    if error.status_code == 403:
        return HttpResponseForbidden(_("Acesso não permitido."))
    action = (
        f'<p><a href="{escape(request.path, quote=True)}">Tentar novamente</a></p>'
        if request.method in {"GET", "HEAD"}
        else '<p><a href="/">Voltar ao início</a></p>'
    )
    response = HttpResponse(
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Temporariamente indisponível</title><body>'
        '<main><h1>Serviço temporariamente indisponível</h1>'
        '<p>Não foi possível carregar esta página agora. Tente novamente em alguns instantes.</p>'
        f'{action}</main></body></html>',
        status=503,
    )
    response["Cache-Control"] = "no-store"
    return response
