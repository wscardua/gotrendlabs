"""Repair FastAPI runtime grants for the administrative MFA tables.

The migration role owns schema changes, whereas the API role is deliberately
separate.  Keep the grant explicit and idempotent so existing installations
that applied 0023 without the API environment receive the same boundary.
"""

from django.db import migrations


MFA_TABLES = (
    "gotrendlabs_totp_factors",
    "gotrendlabs_mfa_challenges",
    "gotrendlabs_mfa_recovery_codes",
    "gotrendlabs_mfa_attempts",
)
FASTAPI_ROLE = "gotrendlabs_fastapi"


def grant_fastapi_mfa_permissions(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return

    quote = connection.ops.quote_name
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [FASTAPI_ROLE])
        if not cursor.fetchone():
            # CI and isolated development databases use the single ephemeral
            # PostgreSQL role. Production deploy preflight separately requires
            # and validates the dedicated runtime role before starting FastAPI.
            return
        for table in MFA_TABLES:
            cursor.execute(
                f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {quote(table)} TO {quote(FASTAPI_ROLE)}"
            )
            cursor.execute("SELECT pg_get_serial_sequence(%s, 'id')", [table])
            sequence = cursor.fetchone()[0]
            if sequence:
                schema, sequence_name = sequence.split(".", 1)
                cursor.execute(
                    f"GRANT USAGE, SELECT ON SEQUENCE {quote(schema)}.{quote(sequence_name)} TO {quote(FASTAPI_ROLE)}"
                )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0023_administrative_mfa")]

    operations = [
        migrations.RunPython(grant_fastapi_mfa_permissions, migrations.RunPython.noop),
    ]
