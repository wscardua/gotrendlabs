"""Keep the last human decision visible for markets published before conversion."""

from django.db import migrations


PUBLISHED_STATUSES = ("open", "locked", "resolved", "sealed", "canceled")


def restore_published_decisions(apps, schema_editor):
    Draft = apps.get_model("editorial_integrations", "EditorialDraft")
    Revision = apps.get_model("editorial_integrations", "EditorialRevision")
    alias = schema_editor.connection.alias
    drafts = (
        Draft.objects.using(alias)
        .filter(market__status__in=PUBLISHED_STATUSES, state="preparation", decision={})
        .order_by("pk")
    )
    for draft in drafts.iterator():
        if "document" not in draft.record:
            continue
        previous = (
            Revision.objects.using(alias)
            .filter(draft_id=draft.pk, revision=draft.revision - 1)
            .values_list("snapshot", flat=True)
            .first()
        )
        decision = previous.get("decision") if isinstance(previous, dict) else None
        if not isinstance(decision, dict) or decision.get("decision") not in {
            "approved", "returned", "rejected"
        }:
            continue
        if not decision.get("reviewer_id"):
            continue
        reviewed = (
            Revision.objects.using(alias)
            .filter(draft_id=draft.pk, revision=decision.get("expected_revision"))
            .values_list("snapshot", flat=True)
            .first()
        )
        reviewed_record = reviewed.get("editorial_record") if isinstance(reviewed, dict) else None
        if not isinstance(reviewed_record, dict) or "document" in reviewed_record:
            continue
        draft.state = decision["decision"]
        draft.decision = decision
        draft.save(using=alias, update_fields=["state", "decision"])


class Migration(migrations.Migration):
    dependencies = [("editorial_integrations", "0004_single_editorial_document")]
    operations = [migrations.RunPython(restore_published_decisions, migrations.RunPython.noop)]
