import asyncio
from unittest.mock import AsyncMock, patch
from django.test import SimpleTestCase
from apps.api.backend_api import editorial_service as domain
from apps.api.backend_api.editorial_pending import document_details, validation_details
from apps.api.backend_api.editorial_schemas import ValidationResponse


class EditorialPendingTests(SimpleTestCase):
    def test_complete_record_future_human_tasks_do_not_block_preparation(self):
        document = """## FONTES E EVIDÊNCIAS
Fonte https://example.org/regulamento consultada pelo agente em 2026-11-05.
## PERGUNTA, REGRAS E PRAZOS
Sim se lançamento público ocorrer; Não caso contrário. Anúncio ainda desconhecido.
## PENDÊNCIAS E CONCLUSÃO
Pendências humanas: responsável e disponibilidade (E10); thumbnail e revisão visual (E09); conferência humana das fontes (E06); conteúdo final (E11)
Conclusão: encaminhar à revisão humana."""
        rows = document_details(document)
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            [r["criterion_ids"] for r in rows], [["E10"], ["E09"], ["E06"], ["E11"]]
        )
        for row in rows:
            self.assertEqual(row["declared_kind"], "human_task")
            self.assertEqual(row["resolve_by"], "before_human_approval")
            self.assertEqual(row["impact"]["creation"], "allowed")
            self.assertEqual(row["impact"]["submission"], "allowed")
            self.assertEqual(row["impact"]["approval"], "human_resolution_required")
        self.assertEqual(
            domain.approval_document_pending(document), ["unresolved_editorial_gaps"]
        )

    def test_essential_source_and_rule_gaps_are_reported_without_inventing_gates(self):
        rows = document_details("""## PENDÊNCIAS E CONCLUSÃO
Lacuna de fonte: fonte de resolução ainda não localizada (E06)
Lacuna de regra: não há regra para empate (E05)
Pendência: confirmar informação adicional""")
        self.assertEqual(
            [r["declared_kind"] for r in rows],
            ["research_or_rule_gap", "research_or_rule_gap", "unspecified"],
        )
        self.assertEqual(rows[-1]["criterion_ids"], [])
        self.assertEqual(
            rows[0]["excerpt"], "fonte de resolução ainda não localizada (E06)"
        )
        self.assertTrue(all(r["impact"]["submission"] == "allowed" for r in rows))
        self.assertTrue(
            all(
                r["impact"]["publication"] == "requires_current_human_approval"
                for r in rows
            )
        )

    def test_no_pending_accepts_template_markdown_and_line_endings(self):
        for heading in ("PENDÊNCIAS E CONCLUSÃO", "## PENDÊNCIAS E CONCLUSÃO"):
            for newline in ("\n", "\r", "\r\n"):
                doc = newline.join(
                    (
                        heading,
                        "",
                        "Pendências para aprovação: nenhuma",
                        "Conclusão: pronta para revisão.",
                    )
                )
                self.assertEqual(document_details(doc), [])
                self.assertEqual(domain.approval_document_pending(doc), [])

    def test_contradiction_anywhere_does_not_clear_real_pending(self):
        for before in (True, False):
            pending = "Lacuna de fonte: fonte não localizada (E06)\n"
            conclusion = (
                "## PENDÊNCIAS E CONCLUSÃO\nPendências para aprovação: nenhuma\n"
            )
            doc = pending + conclusion if before else conclusion + pending
            rows = document_details(doc)
            self.assertIn(
                "contradictory_pending_declarations", [r["reason"] for r in rows]
            )
            self.assertIn("declared_pending", [r["reason"] for r in rows])
            self.assertEqual(
                domain.approval_document_pending(doc), ["unresolved_editorial_gaps"]
            )

    def test_format_causes_are_distinct_and_have_no_invented_criterion(self):
        cases = {
            "sem seção": "conclusion_section_missing",
            "PENDÊNCIAS E CONCLUSÃO\nFonte pendente.": "pending_status_unspecified",
            "PENDÊNCIAS E CONCLUSÃO\nPendências para aprovação:": "pending_status_unspecified",
            "PENDÊNCIAS E CONCLUSÃO\nConclusão\nPendências para aprovação: nenhuma": "approval_declaration_not_first",
            "PENDÊNCIAS E CONCLUSÃO\nPendências para aprovação: nenhuma\nPendências para aprovação: nenhuma": "approval_declaration_repeated",
        }
        for doc, reason in cases.items():
            with self.subTest(reason=reason):
                rows = document_details(doc)
                self.assertIn(reason, [r["reason"] for r in rows])
                self.assertTrue(all(r["criterion_ids"] == [] for r in rows))

    def test_conditional_contingencies_do_not_become_pending(self):
        doc = """## CONTINGÊNCIAS E RESPONSÁVEL
Se a fonte estiver indisponível, manter apuração pendente.
## PENDÊNCIAS E CONCLUSÃO
Pendências para aprovação: nenhuma
Conclusão: recomenda revisão."""
        self.assertEqual(document_details(doc), [])

    def test_markdown_pending_list_is_detailed_and_conflicts_with_none(self):
        doc = """## PENDÊNCIAS E CONCLUSÃO
Pendências para aprovação: nenhuma
- Abrir a fonte de resolução (E06)
- Definir a regra de empate
Conclusão: devolver para pesquisa.
"""
        rows = document_details(doc)
        declared = [r for r in rows if r["reason"] == "declared_pending"]
        self.assertEqual(
            [r["excerpt"] for r in declared],
            ["Abrir a fonte de resolução (E06)", "Definir a regra de empate"],
        )
        self.assertEqual([r["criterion_ids"] for r in declared], [["E06"], []])
        self.assertIn("contradictory_pending_declarations", [r["reason"] for r in rows])

    def test_policy_schedule_and_empty_document_details(self):
        rows = validation_details(
            {"document": "", "policy_version": "old", "policy_hash": "old"},
            domain.policy(),
            ["schedule_incomplete"],
        )
        self.assertEqual(
            [r["code"] for r in rows],
            ["policy_outdated", "empty_document", "schedule_incomplete"],
        )
        self.assertEqual(rows[0]["impact"]["submission"], "blocked")
        self.assertEqual(rows[2]["impact"]["submission"], "blocked")
        self.assertEqual(rows[2]["criterion_ids"], ["E05", "E07"])

    def test_mcp_structured_output_preserves_application_details_and_schema(self):
        from apps.mcp import server

        rows = document_details(
            "## PENDÊNCIAS E CONCLUSÃO\nPendências humanas: thumbnail (E09)"
        )
        payload = dict(
            structurally_valid=True,
            pending=["unresolved_editorial_gaps"],
            pending_details=rows,
            assessment_scope="structural_and_explicit_declarations_only",
            evidence_origin="agent_reported",
            similar=dict(
                items=[],
                has_more=False,
                next_cursor=None,
                coverage="complete_for_query",
                as_of="2026-11-05T12:00:00Z",
            ),
        )

        async def run():
            with patch.object(server, "call", AsyncMock(return_value=payload)):
                # Exercise SDK structured serialization, not just the Python function.
                draft = dict(
                    title="Pergunta futura?",
                    summary="Contexto",
                    kind="binary",
                    category_id=1,
                    subcategory_id=1,
                    event_id=1,
                    close_at="2027-12-01T12:00:00Z",
                    close_timezone="UTC",
                    source="https://example.org",
                    resolution_criteria="Regra objetiva",
                    editorial_record=dict(
                        document="Ficha", policy_version="1.4", policy_hash="a" * 64
                    ),
                )
                result = await server.mcp._tool_manager.call_tool(
                    "validate_market_draft", {"draft": draft}, convert_result=True
                )
                self.assertEqual(result[1], payload)
                listed = await server.mcp.list_tools()
                schema = next(
                    t.outputSchema for t in listed if t.name == "validate_market_draft"
                )
                self.assertIn("pending_details", schema["required"])
                self.assertIn("assessment_scope", schema["required"])

        ValidationResponse.model_validate(payload)
        asyncio.run(run())
