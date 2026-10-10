"""Convert existing editorial drafts to the single-document format once."""

import hashlib
import json

from django.db import migrations


QUESTIONS = {
    "E01": "A resposta ainda é desconhecida e o assunto interessa ao público?",
    "E02": "O conteúdo respeita as pessoas e a proposta educativa?",
    "E03": "Conferimos se já existe uma pergunta equivalente?",
    "E04": "O leitor entenderá a mesma pergunta no título e nas regras?",
    "E05": "Conseguiremos indicar uma única opção vencedora?",
    "E06": "Abrimos a fonte e ela permitirá comprovar a resposta?",
    "E07": "Os prazos estão claros e permitem participar antes de conhecer a resposta?",
    "E08": "Sabemos o que fazer se houver um imprevisto?",
    "E09": "Categoria, imagem, avisos e traduções estão corretos?",
    "E10": "Alguém está responsável por acompanhar e apurar?",
    "E11": "O conteúdo no painel é exatamente o que foi revisado?",
}


def document_from_record(record, market, options):
    lines = [
        "CONTEXTO E DUPLICIDADE",
        "Pergunta: " + market.title,
        "Resumo: " + market.summary,
        record.get("justification", ""),
        "Pesquisa: " + record.get("search_coverage", ""),
        "Mercados semelhantes: " + ", ".join(map(str, record.get("similar_market_ids", []))),
        "Sinais internos: " + record.get("internal_signals", ""),
        "Sinais externos: " + record.get("external_signals", ""),
        "",
        "PERGUNTA, REGRAS E PRAZOS",
        "Opções: " + ", ".join(option.label for option in options),
        "Resolução: " + market.resolution_criteria,
        "Fechamento: " + str(market.close_at) + " (" + market.close_timezone + ")",
        "Anúncio esperado: " + str(record.get("expected_announcement_at") or "não informado"),
        "",
        "FONTES E EVIDÊNCIAS",
        "Fonte cadastrada no mercado (conferir): " + market.source,
    ]
    sources = record.get("sources", [])
    for source in sources:
        lines.append(
            f"{source['url']} | uso: {source.get('purpose', '')} | consulta: "
            f"{source.get('consulted_at', '')} | verificação relatada: "
            f"{source.get('reported_verified', False)} | relato do preparador: "
            f"{source.get('excerpt', '')}"
        )
    for item in record.get("evidence", []):
        label = QUESTIONS.get(item.get("criterion_id"), "Critério editorial")
        urls = [sources[i]["url"] for i in item.get("source_indexes", []) if 0 <= i < len(sources)]
        lines.append(f"{label} [{item.get('status', 'pendente')}]: {item.get('evidence', '')}")
        if urls:
            lines.append("Fontes citadas: " + ", ".join(urls))
    lines += [
        "",
        "CONTINGÊNCIAS E RESPONSÁVEL",
        record.get("fallback", ""),
        "Responsável: conferir no parecer humano.",
        "",
        "PENDÊNCIAS E CONCLUSÃO",
        record.get("gaps", ""),
    ]
    return "\n".join(lines).strip()


def forward(apps, schema_editor):
    Draft = apps.get_model("editorial_integrations", "EditorialDraft")
    Revision = apps.get_model("editorial_integrations", "EditorialRevision")
    Market = apps.get_model("markets", "Market")
    Option = apps.get_model("markets", "MarketOption")
    alias = schema_editor.connection.alias
    market_fields = (
        "id", "slug", "title", "summary", "kind", "status", "source",
        "resolution_criteria", "close_at", "close_timezone", "category_id",
        "subcategory_id", "event_id", "auto_close_enabled", "thumb_color",
        "image_url", "thumb", "is_featured",
    )
    for draft in Draft.objects.using(alias).select_for_update().order_by("pk").iterator():
        old = draft.record
        if "document" in old:
            continue
        market = Market.objects.using(alias).get(pk=draft.market_id)
        options = list(Option.objects.using(alias).filter(market_id=market.pk).order_by("display_order", "id"))
        document = document_from_record(old, market, options)
        if len(document) > 60000:
            raise ValueError(f"Editorial document exceeds 60000 characters for market {market.pk}")
        record = {"policy_version": old["policy_version"], "policy_hash": old["policy_hash"], "document": document}
        snapshot = Market.objects.using(alias).filter(pk=market.pk).values(*market_fields).get()
        snapshot["options"] = [{"label": option.label, "hint": option.hint} for option in options]
        snapshot["editorial_record"] = record
        snapshot = json.loads(json.dumps(snapshot, default=str))
        digest = hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        revision = draft.revision + 1
        Revision.objects.using(alias).create(draft_id=market.pk, revision=revision, snapshot=snapshot, snapshot_hash=digest)
        draft.record = record
        draft.revision = revision
        draft.snapshot_hash = digest
        draft.state = "preparation"
        draft.decision = {}
        draft.save(using=alias, update_fields=["record", "revision", "snapshot_hash", "state", "decision"])


class Migration(migrations.Migration):
    dependencies = [("editorial_integrations", "0003_universal_editorial")]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
