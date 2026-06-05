from django.db import migrations


LEGACY_DOMAINS = (
    "orynth.test",
    "orynth.local",
    "orynth.com",
    "orynth.com.br",
    "gotrendlabs.test",
    "gotrendlabs.local",
)
TARGET_DOMAIN = "gotrendlabs.com.br"


def rewrite_controlled_email_domains(apps, schema_editor):
    connection = schema_editor.connection
    placeholders = ", ".join(["%s"] * len(LEGACY_DOMAINS))
    params = [TARGET_DOMAIN, *LEGACY_DOMAINS]
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE gotrendlabs_users
               SET email = split_part(email, '@', 1) || '@' || %s
             WHERE lower(split_part(email, '@', 2)) IN ({placeholders})
            """,
            [TARGET_DOMAIN, *LEGACY_DOMAINS],
        )
        for table in ("gotrendlabs_external_identities", "gotrendlabs_auth_events"):
            cursor.execute(
                f"""
                UPDATE {table}
                   SET email = split_part(email, '@', 1) || '@' || %s
                 WHERE email <> ''
                   AND lower(split_part(email, '@', 2)) IN ({placeholders})
                """,
                params,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0016_gotrendlabs_rebrand"),
    ]

    operations = [
        migrations.RunPython(rewrite_controlled_email_domains, migrations.RunPython.noop),
    ]
