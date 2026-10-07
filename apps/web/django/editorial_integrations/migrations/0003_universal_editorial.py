"""Add human-origin records without inventing approval or changing markets."""

import copy
import hashlib
import json
from django.db import migrations, models
import django.db.models.deletion

RECORD = {
    "policy_version": "1.2",
    "policy_hash": "9d9b13bf75268cb236120e9aa3f3b46f512fd7b20f965514654d947cd2f40fa1",
    "justification": "Justificativa editorial ainda não documentada.",
    "search_coverage": "Pesquisa e comparação com mercados semelhantes ainda não documentadas.",
    "internal_signals": "",
    "external_signals": "",
    "similar_market_ids": [],
    "sources": [],
    "evidence": [
        {
            "criterion_id": "E01",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
        {
            "criterion_id": "E02",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
        {
            "criterion_id": "E03",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
        {
            "criterion_id": "E04",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
        {
            "criterion_id": "E05",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
        {
            "criterion_id": "E06",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
        {
            "criterion_id": "E07",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
        {
            "criterion_id": "E08",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
        {
            "criterion_id": "E09",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
        {
            "criterion_id": "E10",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
        {
            "criterion_id": "E11",
            "status": "pending",
            "evidence": "",
            "source_indexes": [],
        },
    ],
    "fallback": "",
    "gaps": "Completar ficha e verificar critérios E01–E11 antes do parecer.",
    "expected_announcement_at": None,
}


def backfill(apps, schema_editor):
    Market = apps.get_model("markets", "Market")
    Draft = apps.get_model("editorial_integrations", "EditorialDraft")
    Revision = apps.get_model("editorial_integrations", "EditorialRevision")
    Option = apps.get_model("markets", "MarketOption")
    alias = schema_editor.connection.alias
    fields = (
        "id",
        "slug",
        "title",
        "summary",
        "kind",
        "status",
        "source",
        "resolution_criteria",
        "close_at",
        "close_timezone",
        "category_id",
        "subcategory_id",
        "event_id",
        "auto_close_enabled",
        "thumb_color",
        "image_url",
        "thumb",
        "is_featured",
    )
    for market in (
        Market.objects.using(alias)
        .select_for_update()
        .order_by("pk")
        .values(*fields)
        .iterator()
    ):
        if Draft.objects.using(alias).filter(market_id=market["id"]).exists():
            continue
        record = copy.deepcopy(RECORD)
        snapshot = {
            **market,
            "options": list(
                Option.objects.using(alias)
                .filter(market_id=market["id"])
                .order_by("display_order", "id")
                .values("label", "hint")
            ),
            "editorial_record": record,
        }
        snapshot = json.loads(json.dumps(snapshot, default=str))
        digest = hashlib.sha256(
            json.dumps(
                snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        Draft.objects.using(alias).create(
            market_id=market["id"],
            integration_id=None,
            record=record,
            state="preparation",
            revision=1,
            snapshot_hash=digest,
        )
        Revision.objects.using(alias).create(
            draft_id=market["id"], revision=1, snapshot=snapshot, snapshot_hash=digest
        )


class Migration(migrations.Migration):
    dependencies = [("editorial_integrations", "0002_runtime_grants_and_audit")]
    operations = [
        migrations.AlterField(
            model_name="editorialdraft",
            name="integration",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="editorial_integrations.integration",
            ),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
