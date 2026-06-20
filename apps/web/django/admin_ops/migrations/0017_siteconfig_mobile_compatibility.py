import os

from django.db import migrations, models


MOBILE_COMPATIBILITY_RUNTIME_TABLES = (
    "gotrendlabs_site_config",
    "gotrendlabs_mobile_app_releases",
)


def grant_mobile_compatibility_runtime_permissions(apps, schema_editor):
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
            for table in MOBILE_COMPATIBILITY_RUNTIME_TABLES:
                cursor.execute(f"GRANT SELECT ON TABLE {quote_name(table)} TO {quoted_role}")


class Migration(migrations.Migration):

    dependencies = [
        ("admin_ops", "0016_siteconfig_ai_max_comments_per_market"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteconfig",
            name="min_supported_android_build",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="siteconfig",
            name="recommended_android_build",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="siteconfig",
            name="mobile_update_required_message",
            field=models.CharField(default="Atualize o app para continuar usando o GoTrendLabs.", max_length=240),
        ),
        migrations.RunPython(grant_mobile_compatibility_runtime_permissions, migrations.RunPython.noop),
    ]
