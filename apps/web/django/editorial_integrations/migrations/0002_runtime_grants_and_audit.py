from django.db import migrations


def install(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as c:
        # Preserve raw SQL inserts from existing services and operator commands.
        c.execute(
            "ALTER TABLE gotrendlabs_admin_events ALTER COLUMN request_id SET DEFAULT '', ALTER COLUMN execution_id SET DEFAULT ''"
        )
        c.execute(
            "CREATE INDEX gtl_admin_integration_time ON gotrendlabs_admin_events(integration_id,created_at DESC)"
        )
        c.execute(
            "CREATE INDEX gtl_sys_integration_tool ON gotrendlabs_system_logs ((context->>'integration_id'),(context->>'tool'),created_at DESC)"
        )
        c.execute(
            "CREATE INDEX gtl_sys_execution_result ON gotrendlabs_system_logs ((context->>'execution_id'),(context->>'result'),created_at DESC)"
        )
        for role in ("gotrendlabs_fastapi", "gotrendlabs_django"):
            c.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,))
            if not c.fetchone():
                continue
            for model in apps.get_app_config("editorial_integrations").get_models():
                table = model._meta.db_table
                c.execute(f"REVOKE ALL ON TABLE {table} FROM {role}")
                if role == "gotrendlabs_fastapi":
                    permissions = (
                        "SELECT, INSERT"
                        if table == "gotrendlabs_agent_editorial_revisions"
                        else "SELECT, INSERT, UPDATE, DELETE"
                    )
                    c.execute(f"GRANT {permissions} ON TABLE {table} TO {role}")
                    c.execute(
                        "SELECT pg_get_serial_sequence(%s,%s)",
                        (
                            table,
                            "id"
                            if not table.endswith("editorial_drafts")
                            else "market_id",
                        ),
                    )
                    seq = c.fetchone()[0]
                    if seq:
                        c.execute(f"GRANT USAGE, SELECT ON SEQUENCE {seq} TO {role}")


class Migration(migrations.Migration):
    dependencies = [
        ("editorial_integrations", "0001_initial"),
        ("system_logs", "0001_initial"),
        ("markets", "0032_adminevent_execution_id_adminevent_integration_and_more"),
    ]
    operations = [migrations.RunPython(install, migrations.RunPython.noop)]
