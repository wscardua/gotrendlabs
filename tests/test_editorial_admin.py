import json
import re
from unittest.mock import patch

from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve, reverse

from apps.web.django.admin_ops.editorial_content import EDITORIAL_DIR
from apps.web.django.admin_ops.views import editorial_reference


@override_settings(TEMPLATES=[{**settings.TEMPLATES[0], "OPTIONS": {**settings.TEMPLATES[0]["OPTIONS"], "context_processors": ["django.template.context_processors.request"]}}])
class EditorialReferenceTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse("admin-ops-editorial")

    def _request(self, *, session=None, query="", method="get"):
        request = getattr(self.factory, method)(self.url + query)
        request.session = session or {}
        request.resolver_match = resolve(self.url)
        return request

    def test_staff_can_read_all_approved_documents_without_backend_api(self):
        session = {"auth_api_token": "test-token", "auth_api_user": {"is_staff": True, "display_name": "Editor", "handle": "@editor"}}
        for view, expected in (
            ("manual", "O que é um mercado de previsão"),
            ("checklist", "Checklist de publicação de mercado"),
            ("ficha", "Ficha editorial de mercado"),
        ):
            response = editorial_reference(self._request(session=session, query=f"?view={view}"))
            content = response.content.decode()
            self.assertEqual(response.status_code, 200)
            self.assertIn(expected, content)
            if view == "checklist":
                self.assertIn('id="E06"', content)
            if view == "ficha":
                self.assertIn("CONTEXTO E DUPLICIDADE", content)
            self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_guest_and_non_staff_cannot_read_editorial(self):
        guest = editorial_reference(self._request())
        self.assertEqual(guest.status_code, 302)
        self.assertIn(reverse("login"), guest["Location"])

        session = {"auth_api_token": "test-token", "auth_api_user": {"is_staff": False, "display_name": "Leitor", "handle": "@leitor"}}
        with patch("apps.web.django.accounts.session.get_session", return_value=None):
            regular_user = editorial_reference(self._request(session=session))
        self.assertEqual(regular_user.status_code, 403)

    def test_page_is_read_only_and_unknown_document_falls_back_to_manual(self):
        session = {"auth_api_token": "test-token", "auth_api_user": {"is_staff": True, "display_name": "Editor", "handle": "@editor"}}
        response = editorial_reference(self._request(session=session, method="post"))
        self.assertEqual(response.status_code, 405)
        response = editorial_reference(self._request(session=session, query="?view=unknown"))
        self.assertIn("O que é um mercado de previsão", response.content.decode())

    def test_criteria_match_approved_checklist_and_form(self):
        rules = json.loads((EDITORIAL_DIR / "criteria-v1.2.json").read_text(encoding="utf-8"))
        checklist = (EDITORIAL_DIR / "checklist-de-publicacao.md").read_text(encoding="utf-8")
        form = (EDITORIAL_DIR / "ficha-de-mercado.md").read_text(encoding="utf-8")
        rows = re.findall(r"^\| (E\d\d) \| ([^|]+) \| ([^|]+) \|$", checklist, re.M)
        self.assertEqual(len(rows), 11)
        self.assertEqual(rules["version"], "1.2")
        self.assertEqual(rules["status"], "approved")
        self.assertEqual(
            [{key: rule[key] for key in ("id", "question", "evidence")} for rule in rules["criteria"]],
            [{"id": code, "question": question.strip(), "evidence": evidence.strip()} for code, question, evidence in rows],
        )
        self.assertTrue(all(rule["publication_blocking"] for rule in rules["criteria"]))
        self.assertTrue(next(rule for rule in rules["criteria"] if rule["id"] == "E06")["source_access_required"])
        self.assertTrue(rules["human_decision_required"])
        self.assertIn("checklist E01–E11", form)

    def test_markdown_html_is_escaped(self):
        from apps.web.django.admin_ops.editorial_content import _render_document

        rendered = _render_document("## Teste\n<script>alert(1)</script>")
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_context_links_use_staff_route(self):
        from apps.web.django.admin_ops.editorial_content import _render_document

        rendered = _render_document("[checklist](checklist-de-publicacao.md)")
        self.assertIn(self.url + "?view=checklist", rendered)


class EditorialDocumentLineEndingTests(SimpleTestCase):
    def test_browser_line_endings_accept_valid_announcement_and_conclusion(self):
        from datetime import datetime
        from apps.api.backend_api.editorial_service import document_announcement, approval_document_pending

        for newline in ('\n', '\r\n', '\r'):
            for value in ('não informado', '2026-12-01T15:00:00-03:00', '2026-12-01T18:00:00Z'):
                document = newline.join([
                    'PERGUNTA, REGRAS E PRAZOS', 'Anúncio esperado: ' + value,
                    'Horário exato não confirmado.' if value == 'não informado' else 'Fonte oficial.',
                    '', 'PENDÊNCIAS E CONCLUSÃO', 'Pendências para aprovação: nenhuma', 'Conclusão: aprovado.',
                ])
                with self.subTest(newline=newline, value=value):
                    announced_at = document_announcement(document)
                    if value == 'não informado':
                        self.assertIsNone(announced_at)
                    else:
                        self.assertEqual(announced_at, datetime.fromisoformat('2026-12-01T18:00:00+00:00'))
                    self.assertEqual(approval_document_pending(document), [])

    def test_browser_line_endings_preserve_announcement_and_pending_guards(self):
        from datetime import datetime
        from fastapi import HTTPException
        from apps.api.backend_api.editorial_service import document_announcement, validate_document_timing, approval_document_pending

        for newline in ('\n', '\r\n', '\r'):
            for value in ('amanhã', '2026-12-01T15:00:00', 'não informado' + newline + 'Anúncio esperado: não informado'):
                with self.subTest(newline=newline, value=value), self.assertRaises(HTTPException) as raised:
                    document_announcement('Anúncio esperado: ' + value + newline + 'Observação.')
                self.assertEqual(raised.exception.detail['code'], 'invalid_editorial_announcement')
            with self.assertRaises(HTTPException) as raised:
                validate_document_timing('Anúncio esperado: 2026-12-01T15:00:00-03:00' + newline + 'Fonte.', datetime.fromisoformat('2026-12-01T18:00:00+00:00'))
            self.assertEqual(raised.exception.detail['code'], 'close_after_editorial_announcement')
            for conclusion in ('Fonte pendente.', 'Pendências para aprovação: nenhuma' + newline + 'Pendências para aprovação: nenhuma'):
                self.assertEqual(approval_document_pending('PENDÊNCIAS E CONCLUSÃO' + newline + conclusion), ['unresolved_editorial_gaps'])
