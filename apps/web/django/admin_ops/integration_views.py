"""Admin Ops surfaces consume FastAPI only; Django never writes integration ORM."""

import re

from zoneinfo import ZoneInfo
from urllib.parse import urlsplit

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


def _evidence_source_indexes(text, sources):
    """Map explicit URLs in editable evidence to the structured source catalogue."""
    urls = {url.rstrip(".,;)") for url in re.findall(r'https?://[^\s<>"\]]+', text)}
    return [index for index, source in enumerate(sources) if source["url"] in urls]


def _review_pending_label(code):
    labels = {
        "declared_gaps": _(
            "Lacunas ainda não resolvidas: confirme “Resolvi as lacunas descritas acima” após resolver e documentar cada pendência."
        ),
        "policy_outdated": _("A ficha usa uma versão anterior da política editorial."),
    }
    return labels.get(
        code,
        _("Critério %(criterion)s: confira a evidência e as fontes exigidas.")
        % {"criterion": code},
    )


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
            present = {
                entry["criterion_id"] for entry in detail["draft"]["record"]["evidence"]
            }
            for criterion in detail.get("criteria", []):
                if criterion["id"] not in present:
                    detail["draft"]["record"]["evidence"].append(
                        {
                            "criterion_id": criterion["id"],
                            "status": "pending",
                            "evidence": "",
                            "source_indexes": [],
                        }
                    )
            if request.method == "POST":
                action = request.POST.get("action", "decision")
                if action in ("prepare", "prepare-submit", "assessment"):
                    record = detail["draft"]["record"]
                    for key in (
                        "justification",
                        "search_coverage",
                        "internal_signals",
                        "external_signals",
                        "fallback",
                        "gaps",
                    ):
                        record[key] = request.POST[key]
                    for evidence in record["evidence"]:
                        cid = evidence["criterion_id"]
                        evidence["status"] = (
                            (
                                "satisfied"
                                if cid in request.POST.getlist("verified_criteria")
                                else "pending"
                            )
                            if action == "assessment"
                            else request.POST["status_" + cid]
                        )
                        evidence["evidence"] = request.POST["evidence_" + cid]
                        if action != "assessment":
                            evidence["source_indexes"] = [
                                int(x) for x in request.POST.getlist("sources_" + cid)
                            ]
                    for index, source in enumerate(record["sources"]):
                        source["url"] = request.POST["source_url_" + str(index)]
                        source["excerpt"] = request.POST["source_excerpt_" + str(index)]
                        source["reported_verified"] = str(
                            index
                        ) in request.POST.getlist(
                            "verified_source_indexes"
                            if action == "assessment"
                            else "reported_sources"
                        )
                    verified_sources = [
                        int(x) for x in request.POST.getlist("verified_source_indexes")
                    ]
                    new_source_url = request.POST.get("new_source_url", "").strip()
                    if action == "assessment" and new_source_url:
                        index = len(record["sources"])
                        verified = request.POST.get("new_source_verified") == "yes"
                        record["sources"].append(
                            {
                                "url": new_source_url,
                                "purpose": "resolution",
                                "reported_verified": verified,
                                "consulted_at": timezone.now().isoformat(),
                                "excerpt": request.POST.get("new_source_excerpt", ""),
                            }
                        )
                        if verified:
                            verified_sources.append(index)
                    if action == "assessment":
                        if request.POST.get("gaps_resolved") == "yes":
                            record["gaps"] = ""
                        for evidence in record["evidence"]:
                            evidence["source_indexes"] = _evidence_source_indexes(
                                evidence["evidence"], record["sources"]
                            )
                    payload = {
                        "expected_revision": int(request.POST["expected_revision"]),
                        "editorial_record": record,
                        "note": request.POST["note"]
                        if action == "assessment"
                        else request.POST["preparation_note"],
                    }
                    if action == "assessment":
                        payload.update(
                            {
                                "snapshot_hash": request.POST["snapshot_hash"],
                                "decision": request.POST["decision"],
                                "verified_criteria": request.POST.getlist(
                                    "verified_criteria"
                                ),
                                "verified_source_indexes": verified_sources,
                            }
                        )
                        _request(
                            "POST",
                            f"/admin/agent-editorial-reviews/{market_id}/assessment",
                            payload,
                            auth_token(request),
                        )
                    else:
                        payload["submit_for_review"] = action == "prepare-submit"
                        _request(
                            "PATCH",
                            f"/admin/agent-editorial-reviews/{market_id}/record",
                            payload,
                            auth_token(request),
                        )
                elif action == "decision":
                    payload = {
                        "expected_revision": int(request.POST["expected_revision"]),
                        "snapshot_hash": request.POST["snapshot_hash"],
                        "decision": request.POST["decision"],
                        "note": request.POST["note"],
                        "verified_criteria": request.POST.getlist("verified_criteria"),
                        "verified_source_indexes": [
                            int(x)
                            for x in request.POST.getlist("verified_source_indexes")
                        ],
                    }
                    _request(
                        "POST",
                        f"/admin/agent-editorial-reviews/{market_id}/decision",
                        payload,
                        auth_token(request),
                    )
                else:
                    raise ValueError("invalid action")
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
        detail["pending_labels"] = [
            _review_pending_label(code) for code in detail.get("pending", [])
        ]
        if request.method == "GET":
            for evidence in detail["draft"]["record"]["evidence"]:
                urls = [
                    detail["draft"]["record"]["sources"][index]["url"]
                    for index in evidence["source_indexes"]
                ]
                suggestions = [url for url in urls if url not in evidence["evidence"]]
                if suggestions:
                    suggested_text = (
                        evidence["evidence"]
                        + "\n\n"
                        + str(_("Fontes sugeridas:"))
                        + "\n"
                        + "\n".join(suggestions)
                    )
                    if len(suggested_text) <= 2000:
                        evidence["evidence"] = suggested_text
                    else:
                        evidence["suggested_urls"] = suggestions

        for source in detail["draft"]["record"]["sources"]:
            try:
                uri = urlsplit(source["url"])
                safe = (
                    uri.scheme in ("http", "https")
                    and uri.hostname
                    and not uri.username
                    and not uri.password
                )
            except ValueError:
                safe = False
            source["link_url"] = source["url"] if safe else ""
    return private(
        render(
            request,
            "admin_ops/integration_reviews.html",
            {
                "title": _("Parecer editorial humano"),
                "detail": detail,
                "items": items,
                "admin_error": error,
                "checked_criteria": request.POST.getlist("verified_criteria"),
                "checked_sources": request.POST.getlist("verified_source_indexes"),
                "new_source_url": request.POST.get("new_source_url", ""),
                "new_source_excerpt": request.POST.get("new_source_excerpt", ""),
                "new_source_verified": request.POST.get("new_source_verified") == "yes",
                "review_note": request.POST.get("note", ""),
                "review_decision": request.POST.get("decision", "returned"),
                "review_gaps": request.POST.get(
                    "gaps", detail["draft"]["record"].get("gaps", "")
                )
                if detail
                else "",
                "gaps_resolved": request.POST.get("gaps_resolved") == "yes",
            },
        )
    )
