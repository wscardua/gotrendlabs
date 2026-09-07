import os

from django.db import migrations, models


def install_checkpoint_guard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    configured_roles = {
        schema_editor.connection.settings_dict.get("USER"),
        os.environ.get("FASTAPI_POSTGRES_USER"),
        os.environ.get("POSTGRES_USER"),
        os.environ.get("DJANGO_POSTGRES_USER"),
    }
    quote_name = schema_editor.connection.ops.quote_name
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """CREATE TRIGGER integrity_ledger_checkpoints_append_only
               BEFORE UPDATE OR DELETE ON integrity_ledger_checkpoints
               FOR EACH ROW EXECUTE FUNCTION gotrendlabs_reject_integrity_mutation()"""
        )
        cursor.execute(
            """CREATE TRIGGER integrity_ledger_checkpoints_no_truncate
               BEFORE TRUNCATE ON integrity_ledger_checkpoints
               FOR EACH STATEMENT EXECUTE FUNCTION gotrendlabs_reject_integrity_mutation()"""
        )
        cursor.execute("REVOKE UPDATE, DELETE, TRUNCATE ON TABLE integrity_ledger_checkpoints FROM PUBLIC")
        for role in sorted(item for item in configured_roles if item):
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role])
            if not cursor.fetchone():
                continue
            quoted_role = quote_name(role)
            cursor.execute(
                f"GRANT SELECT, INSERT ON TABLE integrity_ledger_checkpoints TO {quoted_role}"
            )
            cursor.execute("SELECT pg_get_serial_sequence('integrity_ledger_checkpoints', 'id')")
            sequence_row = cursor.fetchone()
            if sequence_row and sequence_row[0]:
                cursor.execute(f"GRANT USAGE, SELECT ON SEQUENCE {sequence_row[0]} TO {quoted_role}")


def remove_checkpoint_guard(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "DROP TRIGGER IF EXISTS integrity_ledger_checkpoints_append_only ON integrity_ledger_checkpoints"
            )
            cursor.execute(
                "DROP TRIGGER IF EXISTS integrity_ledger_checkpoints_no_truncate ON integrity_ledger_checkpoints"
            )


class Migration(migrations.Migration):
    dependencies = [("markets", "0030_integrity_alert_queue")]

    operations = [
        migrations.CreateModel(
            name="IntegrityLedgerCheckpoint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("checkpoint_sequence", models.PositiveBigIntegerField(unique=True)),
                ("audit_type", models.CharField(max_length=20)),
                ("status", models.CharField(max_length=20)),
                ("first_event_sequence", models.PositiveBigIntegerField(blank=True, null=True)),
                ("last_event_sequence", models.PositiveBigIntegerField(default=0)),
                ("last_event_hash", models.CharField(blank=True, max_length=64)),
                ("observed_head_sequence", models.PositiveBigIntegerField(default=0)),
                ("observed_head_hash", models.CharField(blank=True, max_length=64)),
                ("verified_event_count", models.PositiveBigIntegerField(default=0)),
                ("previous_checkpoint_hash", models.CharField(blank=True, max_length=64)),
                ("failure_sequence", models.PositiveBigIntegerField(blank=True, null=True)),
                ("issue_code", models.CharField(blank=True, max_length=80)),
                ("protocol_version", models.CharField(max_length=40)),
                ("verifier_version", models.CharField(max_length=40)),
                ("canonical_payload", models.BinaryField()),
                ("payload_json", models.JSONField(default=dict)),
                ("checkpoint_hash", models.CharField(max_length=64, unique=True)),
                ("signature", models.BinaryField()),
                ("algorithm", models.CharField(max_length=40)),
                ("key_id", models.CharField(max_length=255)),
                ("key_fingerprint", models.CharField(max_length=64)),
                ("verified_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "integrity_ledger_checkpoints",
                "ordering": ["checkpoint_sequence"],
                "indexes": [
                    models.Index(fields=["-last_event_sequence"], name="gtl_icheck_last_seq_idx"),
                    models.Index(fields=["audit_type", "-verified_at"], name="gtl_icheck_type_time_idx"),
                ],
            },
        ),
        migrations.RunPython(install_checkpoint_guard, remove_checkpoint_guard),
    ]
