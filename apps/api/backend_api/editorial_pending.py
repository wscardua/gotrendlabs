"""Explain preparation warnings without claiming semantic or human verification.

Only explicit declarations are interpreted. Prose is returned as evidence for the
reviewer; keyword matches never introduce lifecycle gates or certify sufficiency.
"""

import re

GAPS = "unresolved_editorial_gaps"
MAX_DECLARED_DETAILS = 50
SECTION = re.compile(
    r"(?im)^[ \t]*(?:#{1,6}[ \t]+)?PENDÊNCIAS E CONCLUSÃO[ \t]*#*[ \t]*$"
)
DECLARATION = re.compile(r"(?i)^Pendências para aprovação\s*:\s*(.*?)\s*$")
NONE = re.compile(r"(?i)^nenhuma\.?$")
# Deliberately explicit labels, not occurrences of 'pendente' in contingencies.
PENDING_LABEL = re.compile(
    r"(?i)^(?:[-*]\s*)?(?:pendências?(?: humanas?| essenciais?| de pesquisa| de regra| para aprovação)?|lacunas?(?: essenciais?| de fonte| de regra)?|conferências técnicas ainda não executadas)\s*:"
)


def _declared_kind(label):
    label = label.casefold()
    if "humana" in label:
        return "human_task"
    if any(word in label for word in ("essencia", "pesquisa", "regra", "fonte")):
        return "research_or_rule_gap"
    return "unspecified"


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
            "approval": "human_attestation_required",
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
    truncated = False

    def add_pending(item, *, kind="unspecified", prefix="Pendência declarada: "):
        nonlocal truncated
        if len(declared) >= MAX_DECLARED_DETAILS:
            truncated = True
            return
        declared.append(
            detail(
                "declared_pending",
                prefix + item,
                excerpt=item,
                kind=kind,
                criteria=sorted(set(re.findall(r"\bE(?:0[1-9]|1[01])\b", item))),
            )
        )

    for line in text.splitlines():
        if truncated:
            break
        line = line.strip()
        match = PENDING_LABEL.match(line)
        if not match:
            continue
        kind = _declared_kind(match[0])
        value = line[match.end() :].strip()
        if NONE.fullmatch(value):
            continue
        for item in value.split(";"):
            item = item.strip()
            if item:
                add_pending(item, kind=kind)
                if truncated:
                    break
    # A bullet belongs to pending only after an explicit, empty pending label.
    pending_list = False
    pending_list_kind = "unspecified"
    for line in lines:
        if re.match(r"(?i)^conclusão\s*:", line):
            break
        label = PENDING_LABEL.match(line)
        if label:
            pending_list = not line[label.end() :].strip()
            pending_list_kind = _declared_kind(label[0])
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if not bullet:
            pending_list = False
            continue
        if not pending_list:
            continue
        item = bullet[1].strip()
        if not item or NONE.fullmatch(item):
            continue
        add_pending(item, kind=pending_list_kind, prefix="Pendência listada: ")
        if truncated:
            break
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
    if truncated:
        result.append(
            detail(
                "details_truncated",
                f"Há mais de {MAX_DECLARED_DETAILS} pendências explícitas; somente as primeiras foram detalhadas. Consulte o documento completo.",
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
