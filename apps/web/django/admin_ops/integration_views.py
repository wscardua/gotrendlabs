"""Admin Ops surfaces consume FastAPI only; Django never writes integration ORM."""

from zoneinfo import ZoneInfo

from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_http_methods
from apps.web.django.accounts.api_client import _request, AuthAPIError
from apps.web.django.accounts.session import admin_api_required, auth_token
from apps.api.backend_api.editorial_schemas import SCOPES


class IntegrationExpiryField(forms.DateTimeField):
    """The picker always displays/interprets São Paulo, regardless of browser zone."""

    def prepare_value(self, value):
        if isinstance(value, str):
            try:
                value = parse_datetime(value) or value
            except ValueError:
                pass  # Preserve invalid bound input for the ordinary field error.
        with timezone.override(ZoneInfo("America/Sao_Paulo")):
            return super().prepare_value(value)

    def to_python(self, value):
        with timezone.override(ZoneInfo("America/Sao_Paulo")):
            return super().to_python(value)


class IntegrationForm(forms.Form):
    name = forms.CharField(label=_("Nome"), max_length=120)
    description = forms.CharField(
        label=_("Descrição"),
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    responsible_id = forms.TypedChoiceField(
        label=_("Responsável humano"), coerce=int, choices=[]
    )
    expires_at = IntegrationExpiryField(
        label=_("Data e hora de validade"),
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "step": "60",
                "aria-describedby": "integration-expiry-help",
            },
            format="%Y-%m-%dT%H:%M",
        ),
    )
    scopes = forms.MultipleChoiceField(
        label=_("Permissões"),
        choices=list(
            zip(
                SCOPES,
                (
                    _("Ler política e parecer editorial"),
                    _("Consultar catálogo e taxonomia"),
                    _("Ler métricas agregadas"),
                    _("Criar e editar drafts próprios"),
                    _("Submeter drafts à revisão humana"),
                ),
            )
        ),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    drafts_per_day = forms.IntegerField(
        label=_("Drafts por dia (São Paulo)"), min_value=0, max_value=1000, initial=5
    )
    calls_per_minute = forms.IntegerField(
        label=_("Chamadas por minuto"), min_value=0, max_value=10000, initial=60
    )
    concurrent_calls = forms.IntegerField(
        label=_("Chamadas concorrentes"), min_value=1, max_value=20, initial=2
    )
    expected_revision = forms.IntegerField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, responsible_choices=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsible_id"].choices = [
            ("", _("Selecione o responsável")),
            *responsible_choices,
        ]

    def payload(self):
        d = dict(self.cleaned_data)
        d["expires_at"] = d["expires_at"].isoformat()
        return d


class TransferForm(forms.Form):
    new_responsible_id = forms.TypedChoiceField(
        label=_("Novo responsável"), coerce=int, choices=[]
    )

    def __init__(self, *args, responsible_choices=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_responsible_id"].choices = [
            ("", _("Selecione o responsável")),
            *responsible_choices,
        ]


def responsible_options(token):
    people = []
    after = 0
    while True:
        page = _request(
            "GET", f"/admin/agent-integration-responsibles?after={after}", token=token
        )
        people.extend(page["items"])
        if not page["has_more"]:
            break
        next_cursor = int(page["next_cursor"])
        if next_cursor <= after:
            raise AuthAPIError(_("Não foi possível carregar os responsáveis."))
        after = next_cursor
    labels = {
        person["id"]: (
            person["display_name"]
            if person["display_name"] == person["username"]
            else f"{person['display_name']} ({person['username']})"
        )
        for person in people
    }
    return sorted(labels.items(), key=lambda item: item[1].casefold())


def private(response):
    response["Cache-Control"] = "private, no-store"
    response["Pragma"] = "no-cache"
    return response


@admin_api_required
@require_http_methods(["GET", "POST"])
def integrations(request, identifier=None, create=False):
    error = ""
    data = None
    secret = None
    items = []
    activity = []
    token = auth_token(request)
    choices = []
    try:
        choices = responsible_options(token)
    except (AuthAPIError, ValueError, KeyError):
        error = _("Não foi possível carregar os responsáveis. Tente novamente.")
    form = IntegrationForm(responsible_choices=choices)
    transfer_form = TransferForm(responsible_choices=choices)
    try:
        if identifier:
            data = _request(
                "GET", f"/admin/agent-integrations/{identifier}", token=token
            )
            form = IntegrationForm(
                initial={**data, "expected_revision": data["revision"]},
                responsible_choices=choices,
            )
        if request.method == "POST":
            action = request.POST.get("action", "save")
            base = f"/admin/agent-integrations/{identifier}"
            if action == "save":
                form = IntegrationForm(request.POST, responsible_choices=choices)
                if form.is_valid():
                    data = _request(
                        "PATCH" if identifier else "POST",
                        base if identifier else "/admin/agent-integrations",
                        form.payload(),
                        token,
                    )
                    return private(
                        redirect("admin-ops-integration-detail", identifier=data["id"])
                    )
            elif identifier and action == "credentials":
                secret = _request("POST", base + "/credentials", {}, token)
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return private(
                        render(
                            request,
                            "admin_ops/partials/integration_secret_once.html",
                            {"secret_once": secret},
                        )
                    )
            elif identifier and action in ("activate", "pause", "revoke"):
                if action == "revoke" and request.POST.get("confirm") != "revoke":
                    raise AuthAPIError(_("Confirme a revogação terminal."))
                _request(
                    "POST",
                    base + "/" + action,
                    {"expected_revision": int(request.POST["expected_revision"])},
                    token,
                )
                return private(
                    redirect("admin-ops-integration-detail", identifier=identifier)
                )
            elif identifier and action == "transfer":
                transfer_form = TransferForm(request.POST, responsible_choices=choices)
                if transfer_form.is_valid():
                    _request(
                        "POST",
                        base + "/transfer-responsibility",
                        {
                            "expected_revision": int(request.POST["expected_revision"]),
                            "responsible_id": transfer_form.cleaned_data[
                                "new_responsible_id"
                            ],
                        },
                        token,
                    )
                    return private(
                        redirect("admin-ops-integration-detail", identifier=identifier)
                    )
            elif identifier and action in ("revoke-credential", "revoke-connection"):
                kind = "credentials" if action == "revoke-credential" else "connections"
                _request(
                    "POST",
                    base + "/" + kind + "/" + request.POST["origin_id"] + "/revoke",
                    {},
                    token,
                )
                return private(
                    redirect("admin-ops-integration-detail", identifier=identifier)
                )
        if not identifier:
            items = _request("GET", "/admin/agent-integrations", token=token).get(
                "items", []
            )
        else:
            activity = _request(
                "GET",
                "/admin/agent-integrations/" + str(identifier) + "/activity",
                token=token,
            ).get("items", [])
    except (AuthAPIError, ValueError, KeyError) as exc:
        error = str(exc) if isinstance(exc, AuthAPIError) else _("Dados inválidos.")
    if not identifier and not create and request.method == "GET":
        try:
            activity = (
                _request(
                    "GET", "/admin/system-logs?logger=editorial&limit=10", token=token
                ).get("logs", [])
                if not error
                else []
            )
            activity = activity[:10]
            names = {item["id"]: item["name"] for item in items}
            for log in activity:
                log["integration_name"] = names.get(
                    log.get("context", {}).get("integration_id"), ""
                )
        except AuthAPIError as exc:
            error = str(exc)
    responsible_names = dict(choices)
    for item in items:
        item["responsible_name"] = responsible_names.get(
            item["responsible_id"], _("Responsável indisponível")
        )
    return private(
        render(
            request,
            "admin_ops/integration_list.html"
            if not identifier and not create and request.method == "GET"
            else "admin_ops/integrations.html",
            {
                "title": _("Nova integração") if create else _("Integrações e agentes"),
                "integration_counts": {
                    state: sum(
                        item.get("effective_state", item["state"]) == state
                        for item in items
                    )
                    for state in ("active", "paused", "revoked", "expired")
                },
                "form": form,
                "transfer_form": transfer_form,
                "responsible_name": responsible_names.get(
                    data["responsible_id"] if data else None,
                    _("Responsável indisponível"),
                ),
                "integration": data,
                "secret_once": secret,
                "items": items,
                "admin_error": error,
                "activity": activity,
            },
        )
    )


@admin_api_required
@require_http_methods(["GET", "POST"])
def consent(request):
    error = ""
    info = None
    if request.method == "GET":
        # Session holds the validated request between GET and CSRF-protected POST.
        request.session["mcp_oauth_request"] = request.GET.dict()
    parameters = request.session.get("mcp_oauth_request", {})
    try:
        info = _request("POST", "/oauth/consent-info", parameters, auth_token(request))
        if request.method == "POST":
            if request.POST.get("consent") == "allow":
                response = _request(
                    "POST",
                    "/oauth/consent",
                    {
                        "parameters": parameters,
                        "integration_id": request.POST["integration_id"],
                    },
                    auth_token(request),
                )
                request.session.pop("mcp_oauth_request", None)
                return private(HttpResponseRedirect(response["redirect"]))
            request.session.pop("mcp_oauth_request", None)
            return private(redirect("admin-ops-integrations"))
    except (AuthAPIError, KeyError) as exc:
        error = str(exc)
    return private(
        render(
            request,
            "admin_ops/integration_consent.html",
            {"title": _("Autorizar conexão MCP"), "info": info, "admin_error": error},
        )
    )


def _review_pending_label(code):
    labels = {
        "policy_outdated": _("A política editorial mudou. Consulte a política atual e atualize o documento antes de registrar o parecer."),
        "empty_document": _("O documento editorial está vazio."),
    }
    return labels.get(code, _("Pendência editorial: %(code)s") % {"code": code})


@admin_api_required
@require_http_methods(["GET", "POST"])
def reviews(request, market_id=None):
    error = ""
    detail = None
    items = []
    try:
        if market_id:
            detail = _request(
                "GET",
                f"/admin/agent-editorial-reviews/{market_id}",
                token=auth_token(request),
            )
            if request.method == "POST":
                if request.POST.get("action") != "assessment":
                    raise ValueError("invalid action")
                document = request.POST.get("document", "")
                previous = detail["draft"]["record"]
                policy = detail if document != previous.get("document", "") else previous
                payload = {
                    "expected_revision": int(request.POST["expected_revision"]),
                    "snapshot_hash": request.POST["snapshot_hash"],
                    "decision": request.POST["decision"],
                    "confirmed": request.POST.get("confirmed") == "yes",
                    "editorial_record": {
                        "policy_version": policy["policy_version"],
                        "policy_hash": policy["policy_hash"],
                        "document": document,
                    },
                }
                _request(
                    "POST",
                    f"/admin/agent-editorial-reviews/{market_id}/assessment",
                    payload,
                    auth_token(request),
                )
                return private(
                    redirect("admin-ops-agent-review-detail", market_id=market_id)
                )
        else:
            items = _request(
                "GET", "/admin/agent-editorial-reviews", token=auth_token(request)
            ).get("items", [])
    except (AuthAPIError, ValueError, KeyError) as exc:
        error = str(exc) if isinstance(exc, AuthAPIError) else _("Dados inválidos.")
        if isinstance(exc, AuthAPIError) and isinstance(exc.detail, dict):
            reasons = exc.detail.get("pending", [])
            if reasons:
                if detail:
                    detail["pending"] = reasons
                error += " " + " ".join(
                    str(_review_pending_label(code)) for code in reasons
                )
    if detail:
        pending_codes = detail.get("pending", [])
        detail["pending_labels"] = [_review_pending_label(code) for code in pending_codes]
    return private(
        render(
            request,
            "admin_ops/integration_reviews.html",
            {
                "title": _("Parecer editorial humano"),
                "detail": detail,
                "items": items,
                "admin_error": error,
                "review_document": request.POST.get("document", detail.get("document", "") if detail else ""),
                "review_decision": request.POST.get("decision", "returned"),
                "review_confirmed": request.POST.get("confirmed") == "yes",
            },
        )
    )
