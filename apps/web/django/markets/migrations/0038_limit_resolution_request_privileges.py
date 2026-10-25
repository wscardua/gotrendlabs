"""Remove broad default ACLs from immutable administrative resolution receipts."""

import os

from django.db import migrations


TABLE = "gotrendlabs_market_resolution_requests"
SEQUENCE = "gotrendlabs_market_resolution_requests_id_seq"


def limit_receipt_privileges(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    quote = schema_editor.connection.ops.quote_name
    with schema_editor.connection.cursor() as cursor:
        writer_roles = {"gotrendlabs_fastapi", os.environ.get("FASTAPI_POSTGRES_USER")}
        for role in sorted(name for name in writer_roles if name):
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", [role])
            if not cursor.fetchone():
                continue
            identifier = quote(role)
            cursor.execute(f"REVOKE UPDATE, DELETE ON TABLE {TABLE} FROM {identifier}")
            cursor.execute(f"GRANT SELECT, INSERT ON TABLE {TABLE} TO {identifier}")
            cursor.execute(f"REVOKE UPDATE ON SEQUENCE {SEQUENCE} FROM {identifier}")
            cursor.execute(f"GRANT USAGE, SELECT ON SEQUENCE {SEQUENCE} TO {identifier}")

        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='gotrendlabs_django'")
        if cursor.fetchone():
            cursor.execute(f"REVOKE INSERT, UPDATE, DELETE ON TABLE {TABLE} FROM gotrendlabs_django")
            cursor.execute(f"GRANT SELECT ON TABLE {TABLE} TO gotrendlabs_django")
            cursor.execute(f"REVOKE ALL ON SEQUENCE {SEQUENCE} FROM gotrendlabs_django")


class Migration(migrations.Migration):
    dependencies = [("markets", "0037_market_resolution_request")]
    operations = [migrations.RunPython(limit_receipt_privileges, migrations.RunPython.noop)]
