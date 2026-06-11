from django.db import migrations


FOOTER_TEMPLATES = {
    "pt-br": {
        "subject": "Rodapé transacional GoTrendLabs",
        "body_text": (
            "---\n"
            "{{ platform_name }}\n"
            "{{ platform_description }}\n"
            "{{ transaction_reason }}\n"
            "{{ platform_url }}"
        ),
        "body_html": (
            "<div style=\"border-top:1px solid #dde5e2;margin-top:28px;padding-top:16px;color:#66706f;font-size:12px;line-height:1.5;\">"
            "<p style=\"margin:0 0 6px;font-weight:700;color:#303b3a;\">{{ platform_name }}</p>"
            "<p style=\"margin:0 0 6px;\">{{ platform_description }}</p>"
            "<p style=\"margin:0 0 6px;\">{{ transaction_reason }}</p>"
            "<p style=\"margin:0;\"><a href=\"{{ platform_url }}\" style=\"color:#136f4a;text-decoration:none;\">{{ platform_url }}</a></p>"
            "</div>"
        ),
    },
    "en": {
        "subject": "GoTrendLabs transactional footer",
        "body_text": (
            "---\n"
            "{{ platform_name }}\n"
            "{{ platform_description }}\n"
            "{{ transaction_reason }}\n"
            "{{ platform_url }}"
        ),
        "body_html": (
            "<div style=\"border-top:1px solid #dde5e2;margin-top:28px;padding-top:16px;color:#66706f;font-size:12px;line-height:1.5;\">"
            "<p style=\"margin:0 0 6px;font-weight:700;color:#303b3a;\">{{ platform_name }}</p>"
            "<p style=\"margin:0 0 6px;\">{{ platform_description }}</p>"
            "<p style=\"margin:0 0 6px;\">{{ transaction_reason }}</p>"
            "<p style=\"margin:0;\"><a href=\"{{ platform_url }}\" style=\"color:#136f4a;text-decoration:none;\">{{ platform_url }}</a></p>"
            "</div>"
        ),
    },
}


def seed_transactional_footer_template(apps, schema_editor):
    EmailTemplate = apps.get_model("communications", "EmailTemplate")
    for locale, payload in FOOTER_TEMPLATES.items():
        EmailTemplate.objects.update_or_create(
            key="system.transactional_footer",
            locale=locale,
            defaults={
                "subject": payload["subject"],
                "body_text": payload["body_text"],
                "body_html": payload["body_html"],
                "is_active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("communications", "0006_welcome_email_template"),
    ]

    operations = [
        migrations.RunPython(seed_transactional_footer_template, migrations.RunPython.noop),
    ]
