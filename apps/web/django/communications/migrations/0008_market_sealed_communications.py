from django.db import migrations


def seed_market_sealed(apps, schema_editor):
    EmailTemplate = apps.get_model("communications", "EmailTemplate")
    PushEventPolicy = apps.get_model("communications", "PushEventPolicy")
    PushTemplate = apps.get_model("communications", "PushTemplate")
    EmailTemplate.objects.update_or_create(
        key="market.sealed",
        locale="pt-br",
        defaults={
            "subject": "Histórico finalizado: {{ market_title }}",
            "body_text": "Olá {{ display_name }},\n\nHistórico finalizado e verificável: o registro deste mercado está disponível para conferência.\n\n{{ market_url }}",
            "body_html": "",
            "is_active": True,
        },
    )
    variables = ["market_title", "market_slug", "notification_id"]
    PushEventPolicy.objects.update_or_create(
        event_type="market_sealed",
        defaults={"mode": "immediate", "is_active": True, "default_user_enabled": True, "priority": 25, "template_key": "market_sealed", "allowed_variables": variables},
    )
    PushTemplate.objects.update_or_create(
        event_type="market_sealed",
        locale="pt-br",
        defaults={"title": "Histórico finalizado e verificável", "body": "O registro deste mercado está disponível para conferência.", "is_active": True, "allowed_variables": variables},
    )


class Migration(migrations.Migration):
    dependencies = [("communications", "0007_transactional_footer_template")]
    operations = [migrations.RunPython(seed_market_sealed, migrations.RunPython.noop)]
