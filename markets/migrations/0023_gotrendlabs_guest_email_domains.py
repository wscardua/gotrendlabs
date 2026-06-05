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


def rewrite_guest_contact_domains(apps, schema_editor):
    placeholders = ", ".join(["%s"] * len(LEGACY_DOMAINS))
    with schema_editor.connection.cursor() as cursor:
        for table in ("gotrendlabs_market_suggestions", "gotrendlabs_product_feedback"):
            cursor.execute(
                f"""
                UPDATE {table}
                   SET guest_email = split_part(guest_email, '@', 1) || '@' || %s
                 WHERE guest_email <> ''
                   AND lower(split_part(guest_email, '@', 2)) IN ({placeholders})
                """,
                [TARGET_DOMAIN, *LEGACY_DOMAINS],
            )


class Migration(migrations.Migration):
    dependencies = [
        ("markets", "0022_gotrendlabs_rebrand"),
    ]

    operations = [
        migrations.RunPython(rewrite_guest_contact_domains, migrations.RunPython.noop),
    ]
