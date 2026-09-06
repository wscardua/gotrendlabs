import os

from django.db import migrations, models


def install_append_only_guard(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """CREATE TRIGGER integrity_signing_keys_append_only
               BEFORE UPDATE OR DELETE ON integrity_signing_keys
               FOR EACH ROW EXECUTE FUNCTION gotrendlabs_reject_integrity_mutation()"""
        )
        cursor.execute("REVOKE UPDATE, DELETE ON TABLE integrity_signing_keys FROM PUBLIC")
        configured_roles = {
            schema_editor.connection.settings_dict.get("USER"),
            os.environ.get("FASTAPI_POSTGRES_USER"),
            os.environ.get("POSTGRES_USER"),
            os.environ.get("DJANGO_POSTGRES_USER"),
        }
        quote_name = schema_editor.connection.ops.quote_name
        for role in sorted(item for item in configured_roles if item):
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role])
            if cursor.fetchone():
                cursor.execute(
                    f"GRANT SELECT, INSERT ON TABLE integrity_signing_keys TO {quote_name(role)}"
                )


def remove_append_only_guard(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("DROP TRIGGER IF EXISTS integrity_signing_keys_append_only ON integrity_signing_keys")


class Migration(migrations.Migration):
    dependencies = [("markets", "0028_integrity_event_payload_and_defaults")]

    operations = [
        migrations.CreateModel(
            name="IntegritySigningKey",
            fields=[
                ("key_id", models.CharField(max_length=255, primary_key=True, serialize=False)),
                ("algorithm", models.CharField(max_length=40)),
                ("key_fingerprint", models.CharField(max_length=64, unique=True)),
                ("public_key_der", models.BinaryField()),
                ("created_at", models.DateTimeField()),
            ],
            options={"db_table": "integrity_signing_keys"},
        ),
        migrations.RunPython(install_append_only_guard, remove_append_only_guard),
    ]
