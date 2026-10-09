"""Keep existing SQL configuration initialization compatible with new fields."""

from django.db import migrations


def defaults(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    fields = {
        "thumbnail_enabled": "false",
        "thumbnail_model": "'stability.stable-image-core-v1:1'",
        "thumbnail_region": "'us-west-2'",
        "thumbnail_aspect_ratio": "'3:2'",
        "thumbnail_timeout_seconds": "180",
        "thumbnail_operator_limit": "10",
        "thumbnail_market_limit": "5",
        "thumbnail_global_limit": "50",
        "thumbnail_period_hours": "24",
        "thumbnail_retention_hours": "24",
    }
    with schema_editor.connection.cursor() as cursor:
        for name, value in fields.items():
            cursor.execute(f"ALTER TABLE gotrendlabs_site_config ALTER COLUMN {name} SET DEFAULT {value}")


class Migration(migrations.Migration):
    dependencies = [("admin_ops", "0023_bedrock_thumbnail_settings")]
    operations = [migrations.RunPython(defaults, migrations.RunPython.noop)]
