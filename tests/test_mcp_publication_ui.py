from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase

from apps.web.django.admin_ops.views import _market_initial, market_form


class EditorialPublicationUiTests(SimpleTestCase):
    def test_publish_reviewed_uses_saved_version_without_saving_form(self):
        request = RequestFactory().post(
            "/admin-ops/markets/proposal/edit/",
            {"action": "publish-reviewed", "title": "Unsaved change"},
        )
        request.session = {
            "auth_api_token": "fixture",
            "auth_api_user": {"id": 1, "is_staff": True},
        }
        with (
            patch(
                "apps.web.django.admin_ops.views.admin_get_market",
                return_value={
                    "slug": "proposal",
                    "editorial_revision": 3,
                    "editorial_status": "approved",
                    "status": "draft",
                },
            ),
            patch("apps.web.django.admin_ops.views.admin_publish_market") as publish,
            patch("apps.web.django.admin_ops.views.admin_update_market") as update,
            patch("apps.web.django.admin_ops.views.messages.success"),
        ):
            response = market_form(request, mode="edit", slug="proposal")
        self.assertEqual(response.status_code, 302)
        publish.assert_called_once_with(
            "fixture", "proposal", "Publicação da versão aprovada"
        )
        update.assert_not_called()

    def test_editor_preserves_utc_instant_in_selected_timezone(self):
        initial = _market_initial(
            {
                "close_at": "2026-10-21T02:59:00+00:00",
                "close_timezone": "America/Sao_Paulo",
            }
        )
        self.assertEqual(initial["close_at"], "2026-10-20T23:59")
        self.assertEqual(initial["close_timezone"], "America/Sao_Paulo")


class EditorialMarketListUiTests(SimpleTestCase):
    def render_list(self, **metadata):
        return render_to_string(
            "admin_ops/markets.html",
            {
                "market_data": {
                    "markets": [
                        {
                            "title": "Proposta",
                            "slug": "proposta",
                            "status_label": "Rascunho",
                            **metadata,
                        }
                    ]
                }
            },
        )

    def test_agent_origin_all_editorial_states_and_direct_review_link(self):
        states = {
            "preparation": "Em preparação",
            "in_review": "Em revisão",
            "approved": "Aprovado",
            "returned": "Devolvido para ajustes",
            "rejected": "Rejeitado",
        }
        for state, label in states.items():
            with self.subTest(state=state):
                html = self.render_list(
                    editorial_market_id=5,
                    editorial_status=state,
                    editorial_origin="mcp",
                )
                self.assertIn("Gerado por agente IA via MCP", html)
                self.assertIn(label, html)
                self.assertIn('href="/admin-ops/agent-reviews/5/"', html)
                self.assertIn("Rascunho", html)
                self.assertIn('href="/admin-ops/markets/proposta/edit/"', html)

    def test_market_without_editorial_identity_has_no_agent_badge_or_review_link(self):
        html = self.render_list()
        self.assertNotIn("Gerado por agente IA via MCP", html)
        self.assertNotIn('href="/admin-ops/agent-reviews/', html)
        self.assertIn("Editar/visualizar", html)


class EditorialEvidenceSourceUiTests(SimpleTestCase):
    def test_editable_evidence_selects_only_explicit_catalogue_urls(self):
        from apps.web.django.admin_ops.integration_views import _evidence_source_indexes

        sources = [
            {"url": "https://example.org/report"},
            {"url": "https://example.org/"},
        ]
        self.assertEqual(
            _evidence_source_indexes("Read https://example.org/report.", sources), [0]
        )
        self.assertEqual(
            _evidence_source_indexes("Operator chose https://example.org/", sources),
            [1],
        )
        self.assertEqual(_evidence_source_indexes("No source cited", sources), [])
        self.assertEqual(
            _evidence_source_indexes("https://example.org/report-fake", sources), []
        )


class EditorialPublicationNoticeTests(SimpleTestCase):
    def render_notice(self, status, editorial_status):
        return render_to_string(
            "admin_ops/partials/editorial_publication.html",
            {
                "market": {
                    "status": status,
                    "editorial_status": editorial_status,
                    "editorial_market_id": 5,
                    "editorial_revision": 12,
                }
            },
        )

    def test_published_and_canceled_markets_do_not_show_publication_gate_or_button(
        self,
    ):
        for state in ("open", "locked", "resolved", "sealed", "canceled"):
            with self.subTest(state=state):
                html = self.render_notice(state, "approved")
                self.assertNotIn("Publicação bloqueada", html)
                self.assertNotIn('value="publish-reviewed"', html)
                self.assertIn(
                    "Mercado cancelado"
                    if state == "canceled"
                    else "Mercado já publicado",
                    html,
                )
                self.assertIn("/admin-ops/agent-reviews/5/", html)

    def test_unpublished_markets_show_approval_gate_only_when_needed(self):
        for state in ("draft", "scheduled"):
            for editorial in (
                "preparation",
                "in_review",
                "returned",
                "rejected",
                "approved",
            ):
                with self.subTest(state=state, editorial=editorial):
                    html = self.render_notice(state, editorial)
                    self.assertEqual(
                        "Publicação bloqueada" in html, editorial != "approved"
                    )
                    self.assertEqual(
                        'value="publish-reviewed"' in html, editorial == "approved"
                    )

    def test_legacy_editor_shows_lifecycle_without_editorial_review_or_gate(self):
        for state, label in {
            "open": "Aberto",
            "locked": "Fechado",
            "resolved": "Resolvido",
            "sealed": "Selado",
            "canceled": "Cancelado",
            "draft": "Rascunho",
            "scheduled": "Agendado",
        }.items():
            with self.subTest(state=state):
                html = render_to_string(
                    "admin_ops/partials/editorial_publication.html",
                    {"market": {"status": state, "status_label": label}},
                )
                self.assertNotIn("Publicação bloqueada", html)
                self.assertNotIn("Conferir ficha editorial", html)
                self.assertNotIn("publish-reviewed", html)
                self.assertEqual(
                    "Mercado já publicado" in html,
                    state in {"open", "locked", "resolved", "sealed"},
                )
                self.assertEqual("Mercado cancelado" in html, state == "canceled")
                if state in {"open", "locked", "resolved", "sealed"}:
                    self.assertIn("Estado atual: " + label, html)


class HumanMarketEditorialUiTests(SimpleTestCase):
    render_list = EditorialMarketListUiTests.render_list

    def test_human_market_links_review_without_claiming_agent_origin(self):
        html = self.render_list(
            editorial_market_id=3,
            editorial_status="preparation",
            editorial_origin="human",
        )
        self.assertIn("/admin-ops/agent-reviews/3/", html)
        self.assertIn("Em preparação", html)
        self.assertNotIn("Gerado por agente IA via MCP", html)


class PublishedClosureFeedbackTests(SimpleTestCase):
    def test_signed_legacy_alert_explains_saved_record_instead_of_repeat_input(self):
        html = render_to_string("admin_ops/market_form.html", {
            "market": {"slug": "ev-fixture", "status": "open", "integrity": {"definition_registered": True},
                       "closure_configuration_errors": ["Defina a data/hora", "Selecione um fuso"]},
        })
        self.assertIn("Fechamento incompleto na definição publicada", html)
        self.assertIn("não podem ser alterados pelo salvamento comum", html)
        self.assertNotIn("Defina a data/hora", html)
        self.assertNotIn("Selecione um fuso", html)

    def test_failed_save_keeps_submitted_closure_and_explains_no_persistence(self):
        from apps.web.django.accounts.api_client import AuthAPIError
        from django.http import HttpResponse
        market = {"title": "Qual empresa lidera vendas globais de carros elétricos no 4T26?",
                  "slug": "ev-fixture", "status": "open", "kind": "multiple",
                  "category": "Negócios", "subcategory": "Automotivo", "event": "Geral",
                  "summary": "Resumo", "source": "Fonte", "resolution_criteria": "Critério",
                  "close_at": None, "close_timezone": "", "auto_close_enabled": True,
                  "thumb_color": "#dce6f0", "editorial_revision": 1, "editorial_market_id": 3,
                  "integrity": {"definition_registered": True},
                  "closure_configuration_errors": ["Defina a data/hora", "Selecione um fuso"],
                  "options": [{"label": "Tesla", "hint": ""}, {"label": "BYD", "hint": ""}]}
        request = RequestFactory().post("/admin-ops/markets/ev-fixture/edit/", {
            **{k: market[k] for k in ("title", "slug", "kind", "category", "subcategory", "event", "summary", "source", "resolution_criteria", "thumb_color")},
            "action": "save", "editorial_revision": "1", "close_at": "2027-01-10T23:59",
            "close_timezone": "America/Sao_Paulo", "auto_close_enabled": "on",
            "option_label": ["Tesla", "BYD"], "option_hint": ["", ""],
        })
        request.session = {"auth_api_token": "fixture", "auth_api_user": {"id": 1, "is_staff": True, "display_name": "Fixture", "handle": "fixture", "email": "fixture@example.org", "language": "pt-br"}}
        with (patch("apps.web.django.admin_ops.views.admin_get_market", return_value=market),
              patch("apps.web.django.admin_ops.views.admin_get_taxonomy", return_value={"categories": []}),
              patch("apps.web.django.admin_ops.views._market_participants_context", return_value={}),
              patch("apps.web.django.admin_ops.views.render", side_effect=lambda request, template, context: HttpResponse(render_to_string(template, context))),
              patch("apps.web.django.admin_ops.views.admin_update_market", side_effect=AuthAPIError("Alterações não salvas: definição assinada.")) as update):
            response = market_form(request, mode="edit", slug="ev-fixture")
        self.assertEqual(response.status_code, 200)
        update.assert_called_once()
        payload = update.call_args.args[2]
        self.assertEqual(payload["close_timezone"], "America/Sao_Paulo")
        self.assertTrue(payload["close_at"].startswith("2027-01-10T23:59"))
        self.assertContains(response, 'value="2027-01-10T23:59"')
        self.assertContains(response, "Os valores preenchidos no formulário não foram gravados")
        self.assertContains(response, "Alterações não salvas")
        self.assertNotContains(response, "Defina a data/hora")


class MarketWallTimezoneTests(SimpleTestCase):
    def form(self, wall, zone):
        from apps.web.django.admin_ops.forms import AdminMarketForm
        return AdminMarketForm(data={"title":"DEV", "kind":"binary", "category":"IA", "subcategory":"Modelos", "event":"Geral", "summary":"Fixture", "source":"Fonte", "resolution_criteria":"Critério", "thumb_color":"#d8ece2", "close_at":wall, "close_timezone":zone})

    def test_selected_timezone_controls_instant_and_roundtrip_without_drift(self):
        for zone, offset in (("UTC","+00:00"),("America/Sao_Paulo","-03:00"),("America/New_York","-04:00"),("Europe/London","+01:00")):
            with self.subTest(zone=zone):
                form=self.form("2026-10-09T18:00",zone)
                self.assertTrue(form.is_valid(),form.errors)
                payload=form.to_payload()
                self.assertEqual(payload["close_at"],"2026-10-09T18:00:00"+offset)
                self.assertEqual(_market_initial(payload)["close_at"],"2026-10-09T18:00")
                repeated=self.form(_market_initial(payload)["close_at"],zone)
                self.assertTrue(repeated.is_valid(),repeated.errors)
                self.assertEqual(repeated.to_payload()["close_at"],payload["close_at"])

    def test_dst_gap_and_fold_require_unambiguous_time(self):
        for wall in ("2026-03-08T02:30","2026-11-01T01:30"):
            form=self.form(wall,"America/New_York")
            self.assertFalse(form.is_valid())
            self.assertIn("close_at",form.errors)

    def test_seconds_and_microseconds_survive_mcp_to_human_roundtrip(self):
        from datetime import datetime
        original = "2026-10-09T18:00:42.123456+00:00"
        initial = _market_initial({"close_at": original,"close_timezone":"UTC"})
        self.assertEqual(initial["close_at"],"2026-10-09T18:00:42.123456")
        form=self.form(initial["close_at"],"UTC")
        self.assertTrue(form.is_valid(),form.errors)
        self.assertEqual(datetime.fromisoformat(form.to_payload()["close_at"]),datetime.fromisoformat(original))
        self.assertEqual(form.fields["close_at"].widget.attrs["step"], "any")
        self.assertIn('value="2026-10-09T18:00:42.123456"', str(form["close_at"]))

    def test_invalid_revision_preserves_form_and_does_not_update_market(self):
        from django.http import HttpResponse

        for revision in ("not-an-integer", "0", "-1"):
            with self.subTest(revision=revision):
                form = self.form("2026-10-09T18:00", "UTC")
                request = RequestFactory().post("/admin-ops/markets/fixture/edit/", {
                    **form.data, "action": "save", "editorial_revision": revision,
                })
                request.session = {"auth_api_token": "fixture", "auth_api_user": {"id": 1, "is_staff": True}}
                with (patch("apps.web.django.admin_ops.views.admin_get_market", return_value={"slug": "fixture", "status": "draft", "editorial_revision": 1, "editorial_market_id": 1}),
                      patch("apps.web.django.admin_ops.views.admin_get_taxonomy", return_value={"categories": []}),
                      patch("apps.web.django.admin_ops.views._market_participants_context", return_value={}),
                      patch("apps.web.django.admin_ops.views.render", side_effect=lambda request, template, context: HttpResponse(render_to_string(template, context))),
                      patch("apps.web.django.admin_ops.views.admin_update_market") as update):
                    response = market_form(request, mode="edit", slug="fixture")
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Revisão editorial inválida")
                self.assertContains(response, 'value="2026-10-09T18:00"')
                update.assert_not_called()

    def test_legacy_new_publish_post_saves_once_and_redirects_to_reviewable_draft(self):
        form=self.form("2026-10-09T18:00","UTC")
        request=RequestFactory().post("/admin-ops/markets/new/",{**form.data,"action":"publish"})
        request.session={"auth_api_token":"fixture","auth_api_user":{"id":1,"is_staff":True}}
        with (patch("apps.web.django.admin_ops.views.admin_get_taxonomy",return_value={"categories":[]}),
              patch("apps.web.django.admin_ops.views.admin_create_market",return_value={"slug":"fixture","editorial_revision":1,"status":"draft"}) as create,
              patch("apps.web.django.admin_ops.views.admin_publish_market") as publish,
              patch("apps.web.django.admin_ops.views.messages.success") as message):
            response=market_form(request,mode="new")
        self.assertEqual(response.status_code,302)
        self.assertEqual(response.url,"/admin-ops/markets/fixture/edit/")
        create.assert_called_once()
        publish.assert_not_called()
        self.assertIn("parecer humano",message.call_args.args[1])


class ResolutionWallTimezoneTests(SimpleTestCase):
    def test_resolution_uses_selected_zone_and_rejects_dst_gap(self):
        from apps.web.django.admin_ops.forms import MarketResolutionForm
        base={"winning_option_id":"1", "source_url":"http://localhost:8000/", "note":"Ensaio", "resolved_at":"2026-10-07T20:00", "resolution_timezone":"UTC"}
        market={"options":[{"id":1,"label":"SIM"}]}
        form=MarketResolutionForm(data=base,market=market)
        self.assertTrue(form.is_valid(),form.errors)
        self.assertEqual(form.cleaned_data["resolved_at"].isoformat(),"2026-10-07T20:00:00+00:00")
        invalid=MarketResolutionForm(data={**base,"resolved_at":"2026-03-08T02:30","resolution_timezone":"America/New_York"},market=market)
        self.assertFalse(invalid.is_valid())
        self.assertIn("resolved_at",invalid.errors)
