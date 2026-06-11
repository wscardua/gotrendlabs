import os

from django.db import migrations


EMAIL_TABLES = (
    "gotrendlabs_email_deliveries",
    "gotrendlabs_email_confirmation_tokens",
)


def grant_email_runtime_permissions(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return

    configured_roles = {
        connection.settings_dict.get("USER"),
        os.environ.get("FASTAPI_POSTGRES_USER"),
        os.environ.get("POSTGRES_USER"),
        os.environ.get("DJANGO_POSTGRES_USER"),
    }
    roles = sorted(role for role in configured_roles if role)
    if not roles:
        return

    quote_name = connection.ops.quote_name
    with connection.cursor() as cursor:
        for role in roles:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role])
            if not cursor.fetchone():
                continue

            quoted_role = quote_name(role)
            for table in EMAIL_TABLES:
                quoted_table = quote_name(table)
                cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {quoted_table} TO {quoted_role}")
                cursor.execute("SELECT pg_get_serial_sequence(%s, 'id')", [table])
                sequence_row = cursor.fetchone()
                sequence_name = sequence_row[0] if sequence_row else None
                if sequence_name:
                    cursor.execute(f"GRANT USAGE, SELECT, UPDATE ON SEQUENCE {sequence_name} TO {quoted_role}")


class Migration(migrations.Migration):

    dependencies = [
        ("communications", "0004_grant_push_runtime_permissions"),
    ]

    operations = [
        migrations.RunPython(grant_email_runtime_permissions, migrations.RunPython.noop),
    ]
