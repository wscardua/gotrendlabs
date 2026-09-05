import os

from django.db import migrations, models
import django.db.models.deletion


INTEGRITY_TABLES = (
    "market_integrity_definitions",
    "prediction_commitments",
    "market_merkle_leaves",
    "market_seals",
    "integrity_ledger_events",
)


def install_append_only_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE OR REPLACE FUNCTION gotrendlabs_reject_integrity_mutation()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
              RAISE EXCEPTION 'integrity records are append-only';
            END;
            $$
            """
        )
        for table in INTEGRITY_TABLES:
            cursor.execute(
                f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION gotrendlabs_reject_integrity_mutation()"
            )
            cursor.execute(f"REVOKE UPDATE, DELETE ON TABLE {table} FROM PUBLIC")

        configured_roles = {
            schema_editor.connection.settings_dict.get("USER"),
            os.environ.get("FASTAPI_POSTGRES_USER"),
            os.environ.get("POSTGRES_USER"),
            os.environ.get("DJANGO_POSTGRES_USER"),
        }
        quote_name = schema_editor.connection.ops.quote_name
        for role in sorted(item for item in configured_roles if item):
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role])
            if not cursor.fetchone():
                continue
            quoted_role = quote_name(role)
            for table in INTEGRITY_TABLES:
                quoted_table = quote_name(table)
                cursor.execute(f"GRANT SELECT, INSERT ON TABLE {quoted_table} TO {quoted_role}")
                cursor.execute("SELECT pg_get_serial_sequence(%s, 'id')", [table])
                sequence_row = cursor.fetchone()
                if sequence_row and sequence_row[0]:
                    cursor.execute(f"GRANT USAGE, SELECT ON SEQUENCE {sequence_row[0]} TO {quoted_role}")


def remove_append_only_guards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for table in INTEGRITY_TABLES:
            cursor.execute(f"DROP TRIGGER IF EXISTS {table}_append_only ON {table}")
        cursor.execute("DROP FUNCTION IF EXISTS gotrendlabs_reject_integrity_mutation()")


class Migration(migrations.Migration):
    dependencies = [("markets", "0026_remove_market_primary_probability_exact_and_more")]

    operations = [
        migrations.AddField(model_name="market", name="published_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="market", name="seal_due_at", field=models.DateTimeField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name="market", name="sealed_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="market", name="integrity_version", field=models.CharField(blank=True, default="", max_length=40)),
        migrations.AlterField(model_name="market", name="status", field=models.CharField(choices=[("draft", "Draft"), ("scheduled", "Scheduled"), ("open", "Open"), ("locked", "Locked"), ("resolved", "Resolved"), ("sealed", "Sealed"), ("canceled", "Canceled")], db_index=True, max_length=20)),
        migrations.CreateModel(
            name="MarketIntegrityDefinition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("definition_version", models.PositiveIntegerField(default=1)), ("protocol_version", models.CharField(max_length=40)),
                ("canonical_payload", models.BinaryField()), ("payload_json", models.JSONField(default=dict)),
                ("payload_hash", models.CharField(max_length=64, unique=True)), ("signature", models.BinaryField()),
                ("algorithm", models.CharField(max_length=40)), ("key_id", models.CharField(max_length=255)),
                ("key_fingerprint", models.CharField(max_length=64)), ("signed_at", models.DateTimeField()),
                ("market", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="integrity_definition", to="markets.market")),
            ], options={"db_table": "market_integrity_definitions"}),
        migrations.CreateModel(
            name="PredictionCommitment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("protocol_version", models.CharField(max_length=40)), ("canonical_payload", models.BinaryField()),
                ("payload_json", models.JSONField(default=dict)), ("commitment_hash", models.CharField(max_length=64, unique=True)),
                ("signature", models.BinaryField()), ("algorithm", models.CharField(max_length=40)),
                ("key_id", models.CharField(max_length=255)), ("key_fingerprint", models.CharField(max_length=64)),
                ("signed_at", models.DateTimeField()),
                ("definition", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="prediction_commitments", to="markets.marketintegritydefinition")),
                ("market", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="prediction_commitments", to="markets.market")),
                ("prediction", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="integrity_commitment", to="markets.prediction")),
                ("previous_commitment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="next_commitments", to="markets.predictioncommitment")),
            ], options={"db_table": "prediction_commitments"}),
        migrations.CreateModel(
            name="MarketSeal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("protocol_version", models.CharField(max_length=40)), ("predictions_root", models.CharField(max_length=64)),
                ("result_hash", models.CharField(max_length=64)), ("previous_event_hash", models.CharField(blank=True, max_length=64)),
                ("canonical_payload", models.BinaryField()), ("payload_json", models.JSONField(default=dict)),
                ("seal_hash", models.CharField(max_length=64, unique=True)), ("signature", models.BinaryField()),
                ("algorithm", models.CharField(max_length=40)), ("key_id", models.CharField(max_length=255)),
                ("key_fingerprint", models.CharField(max_length=64)), ("sealed_at", models.DateTimeField()),
                ("definition", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="seals", to="markets.marketintegritydefinition")),
                ("market", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="integrity_seal", to="markets.market")),
            ], options={"db_table": "market_seals"}),
        migrations.CreateModel(
            name="MarketMerkleLeaf",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("leaf_index", models.PositiveIntegerField()), ("leaf_hash", models.CharField(max_length=64)),
                ("proof", models.JSONField(default=list)),
                ("commitment", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="merkle_leaf", to="markets.predictioncommitment")),
                ("market", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="merkle_leaves", to="markets.market")),
                ("seal", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="leaves", to="markets.marketseal")),
            ], options={"db_table": "market_merkle_leaves", "constraints": [models.UniqueConstraint(fields=("market", "leaf_index"), name="uniq_market_merkle_leaf_index")]}),
        migrations.CreateModel(
            name="IntegrityLedgerEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sequence", models.PositiveBigIntegerField(unique=True)), ("event_type", models.CharField(db_index=True, max_length=60)),
                ("entity_type", models.CharField(max_length=40)), ("entity_identifier", models.CharField(max_length=160)),
                ("payload_reference", models.CharField(max_length=200)), ("payload_hash", models.CharField(max_length=64)),
                ("previous_event_hash", models.CharField(blank=True, max_length=64)), ("event_hash", models.CharField(max_length=64, unique=True)),
                ("signature", models.BinaryField()), ("algorithm", models.CharField(max_length=40)),
                ("key_id", models.CharField(max_length=255)), ("key_fingerprint", models.CharField(max_length=64)),
                ("correlation_id", models.UUIDField(blank=True, null=True)), ("causation_id", models.UUIDField(blank=True, null=True)),
                ("occurred_at", models.DateTimeField()), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("market", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="integrity_events", to="markets.market")),
            ], options={"db_table": "integrity_ledger_events", "ordering": ["sequence"]}),
        migrations.AddIndex(model_name="predictioncommitment", index=models.Index(fields=["market", "prediction"], name="gtl_commit_market_pred_idx")),
        migrations.RunPython(install_append_only_guards, remove_append_only_guards),
    ]
