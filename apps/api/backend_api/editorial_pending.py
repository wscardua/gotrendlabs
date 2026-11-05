"""Explain preparation warnings without claiming semantic or human verification.

Only explicit declarations are interpreted. Prose is returned as evidence for the
reviewer; keyword matches never introduce lifecycle gates or certify sufficiency.
"""

import re

GAPS = "unresolved_editorial_gaps"
SECTION = re.compile(
    r"(?im)^[ \t]*(?:#{1,6}[ \t]+)?PENDÊNCIAS E CONCLUSÃO[ \t]*#*[ \t]*$"
)
DECLARATION = re.compile(r"(?i)^Pendências para aprovação\s*:\s*(.*?)\s*$")
NONE = re.compile(r"(?i)^nenhuma\.?$")
# Deliberately explicit labels, not occurrences of 'pendente' in contingencies.
PENDING_LABEL = re.compile(
    r"(?i)^(?:[-*]\s*)?(?:pendências?(?: humanas?| essenciais?| de pesquisa| de regra| para aprovação)?|lacunas?(?: essenciais?| de fonte| de regra)?|conferências técnicas ainda não executadas)\s*:"
)


def detail(
    reason,
    description,
    *,
    excerpt=None,
    criteria=(),
    code=GAPS,
    stage="before_human_approval",
    submission="allowed",
    kind="unspecified",
):
    return {
        "code": code,
        "reason": reason,
        "description": description,
        "declared_kind": kind,
        "criterion_ids": list(criteria),
        "resolve_by": stage,
        "excerpt": excerpt,
        "impact": {
            "creation": "allowed",
            "submission": submission,
            "approval": "human_resolution_required",
            "publication": "requires_current_human_approval",
        },
    }


def document_details(document):
    text = document.replace("\r\n", "\n").replace("\r", "\n")
    sections = list(SECTION.finditer(text))
    result = []
    if not sections:
        result.append(
            detail(
                "conclusion_section_missing",
                "Seção PENDÊNCIAS E CONCLUSÃO não localizada; não é possível identificar a conclusão declarada.",
            )
        )
    elif len(sections) > 1:
        result.append(
            detail(
                "conclusion_section_repeated",
                "Há mais de uma seção de pendências e conclusão; reconciliar as versões.",
            )
        )
    final = text[sections[0].end() :] if sections else ""
    # Do not let declarations in subsequent Markdown sections clear this section.
    final = re.split(r"(?m)^\s*#{1,6}\s+", final, maxsplit=1)[0]
    lines = [line.strip() for line in final.splitlines() if line.strip()]
    declarations = [DECLARATION.fullmatch(line) for line in lines]
    declarations = [m for m in declarations if m]
    declared = []
    for line in text.splitlines():
        line = line.strip()
        match = PENDING_LABEL.match(line)
        if not match:
            continue
        label = match[0].casefold()
        kind = (
            "human_task"
            if "humana" in label
            else "research_or_rule_gap"
            if any(word in label for word in ("essencia", "pesquisa", "regra", "fonte"))
            else "unspecified"
        )
        value = line[match.end() :].strip()
        if NONE.fullmatch(value):
            continue
        # Keep each explicitly listed item, preserving its exact wording and only
        # criterion IDs actually supplied by the author (never inferred).
        for item in value.split(";"):
            item = item.strip()
            if item:
                declared.append(
                    detail(
                        "declared_pending",
                        "Pendência declarada: " + item,
                        excerpt=item,
                        kind=kind,
                        criteria=sorted(
                            set(re.findall(r"\bE(?:0[1-9]|1[01])\b", item))
                        ),
                    )
                )
    # The template also permits a Markdown list instead of a labelled sentence.
    # Read list items only in the conclusion section and before its conclusion;
    # conditional fallback rules elsewhere are not outstanding tasks.
    for line in lines:
        if re.match(r"(?i)^conclusão\s*:", line):
            break
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if not bullet or PENDING_LABEL.match(line):
            continue
        item = bullet[1].strip()
        if not item or NONE.fullmatch(item):
            continue
        declared.append(
            detail(
                "declared_pending",
                "Pendência listada: " + item,
                excerpt=item,
                criteria=sorted(set(re.findall(r"\bE(?:0[1-9]|1[01])\b", item))),
            )
        )
    result.extend(declared)
    if sections:
        if len(declarations) > 1:
            result.append(
                detail(
                    "approval_declaration_repeated",
                    "Há múltiplas declarações de pendências para aprovação; reconciliar o documento.",
                )
            )
        elif not declarations and not declared:
            result.append(
                detail(
                    "pending_status_unspecified",
                    "A seção não identifica explicitamente as pendências nem declara ausência delas; revisar o texto, sem afirmar ausência se houver pendências reais.",
                    excerpt=final.strip() or None,
                )
            )
        elif declarations and not declarations[0][1].strip():
            result.append(
                detail(
                    "pending_status_unspecified",
                    "Declaração de pendências vazia; registrar as pendências reais ou a ausência conhecida.",
                )
            )
        elif declarations and NONE.fullmatch(declarations[0][1]):
            if declared:
                result.append(
                    detail(
                        "contradictory_pending_declarations",
                        "A declaração de ausência conflita com pendências explícitas no documento; esclarecer sem apagar pendências reais.",
                    )
                )
            elif not lines or not DECLARATION.fullmatch(lines[0]):
                result.append(
                    detail(
                        "approval_declaration_not_first",
                        "A declaração de ausência não é a primeira linha de conteúdo da seção, como orienta o modelo de preparação.",
                    )
                )
    return result


def validation_details(record, current_policy, schedule_pending):
    result = []
    if (
        record["policy_version"] != current_policy["version"]
        or record["policy_hash"] != current_policy["hash"]
    ):
        result.append(
            detail(
                "policy_outdated",
                "Versão/hash da política divergem da política vigente; atualizar antes da submissão.",
                code="policy_outdated",
                stage="before_submission",
                submission="blocked",
            )
        )
    if not (record.get("document") or "").strip():
        result.append(
            detail(
                "empty_document",
                "Documento editorial vazio; preencher a ficha.",
                code="empty_document",
            )
        )
    else:
        result.extend(document_details(record["document"]))
    if schedule_pending:
        item = detail(
            "schedule_incomplete",
            "Preencher resolução prevista e fuso IANA antes de submeter.",
            code="schedule_incomplete",
            criteria=("E05", "E07"),
            stage="before_submission",
            submission="blocked",
        )
        item["impact"]["publication"] = "blocked"
        result.append(item)
    return result
