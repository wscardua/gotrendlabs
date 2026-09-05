from django.db import migrations


def install_database_default(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("ALTER TABLE gotrendlabs_site_config ALTER COLUMN market_seal_window_hours SET DEFAULT 12")


class Migration(migrations.Migration):
    dependencies = [("admin_ops", "0018_siteconfig_market_seal_window")]
    operations = [migrations.RunPython(install_database_default, migrations.RunPython.noop)]
