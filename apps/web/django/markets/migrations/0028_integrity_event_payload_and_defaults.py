from django.db import migrations, models


def install_database_defaults(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("ALTER TABLE gotrendlabs_markets ALTER COLUMN integrity_version SET DEFAULT ''")


class Migration(migrations.Migration):
    dependencies = [("markets", "0027_market_integrity_ledger")]
    operations = [
        migrations.AddField(model_name="integrityledgerevent", name="protocol_version", field=models.CharField(default="gtl-integrity/v1", max_length=40), preserve_default=False),
        migrations.AddField(model_name="integrityledgerevent", name="canonical_payload", field=models.BinaryField(default=b""), preserve_default=False),
        migrations.AddField(model_name="integrityledgerevent", name="payload_json", field=models.JSONField(default=dict)),
        migrations.RunPython(install_database_defaults, migrations.RunPython.noop),
    ]
