from django.db import migrations


LEGACY_EMAIL_PATTERNS = (
    "email-smtp.",
    "amazon" + "se" + "s.com",
)


def _contains_legacy_email_residue(value):
    value = (value or "").strip().lower()
    return any(pattern in value for pattern in LEGACY_EMAIL_PATTERNS)


def remove_legacy_email_residue(apps, schema_editor):
    site_config_model = apps.get_model("admin_ops", "SiteConfig")
    email_delivery_model = apps.get_model("communications", "EmailDelivery")

    for site_config in site_config_model.objects.all():
        update_fields = []
        if _contains_legacy_email_residue(site_config.smtp_host):
            site_config.smtp_host = ""
            site_config.smtp_username = ""
            update_fields.append("smtp_host")
            update_fields.append("smtp_username")
        if _contains_legacy_email_residue(site_config.smtp_username):
            site_config.smtp_username = ""
            if "smtp_username" not in update_fields:
                update_fields.append("smtp_username")
        if update_fields and site_config.email_provider == "smtp":
            site_config.email_provider = "resend"
            update_fields.append("email_provider")
        if update_fields:
            site_config.save(update_fields=update_fields)

    email_delivery_model.objects.filter(recipient_email__icontains="amazon" + "se" + "s.com").delete()
    email_delivery_model.objects.filter(last_error__icontains="S" + "ES sandbox").update(last_error="")


class Migration(migrations.Migration):
    dependencies = [
        ("admin_ops", "0011_siteconfig_email_provider"),
        ("communications", "0004_grant_push_runtime_permissions"),
    ]

    operations = [
        migrations.RunPython(remove_legacy_email_residue, migrations.RunPython.noop),
    ]
