import os

from django.db import migrations


BADGE_REQUIREMENT_TABLES = ("gotrendlabs_badge_rule_requirements",)


def grant_badge_requirement_runtime_permissions(apps, schema_editor):
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
            for table in BADGE_REQUIREMENT_TABLES:
                quoted_table = quote_name(table)
                cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {quoted_table} TO {quoted_role}")
                cursor.execute("SELECT pg_get_serial_sequence(%s, 'id')", [table])
                sequence_row = cursor.fetchone()
                sequence_name = sequence_row[0] if sequence_row else None
                if sequence_name:
                    cursor.execute(f"GRANT USAGE, SELECT, UPDATE ON SEQUENCE {sequence_name} TO {quoted_role}")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0020_badge_rule_requirements"),
    ]

    operations = [
        migrations.RunPython(grant_badge_requirement_runtime_permissions, migrations.RunPython.noop),
    ]
