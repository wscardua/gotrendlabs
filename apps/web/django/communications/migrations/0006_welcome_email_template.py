from django.db import migrations


WELCOME_TEMPLATE = {
    "subject": "Bem-vindo à GoTrendLabs",
    "body_text": (
        "Olá {{ display_name }},\n\n"
        "Sua conta GoTrendLabs foi criada.\n\n"
        "Você já pode acompanhar mercados públicos, sua reputação, carteira educativa e sinais da comunidade:\n"
        "{{ platform_url }}\n\n"
        "A GoTrendLabs é uma rede social de previsões educativas. GTL Credits não representam dinheiro real, investimento ou saque financeiro."
    ),
    "body_html": (
        "<div style=\"font-family:Arial,sans-serif;line-height:1.55;color:#1f2b2b;max-width:620px;margin:0 auto;padding:24px;\">"
        "<p style=\"margin:0 0 16px;\">Olá {{ display_name }},</p>"
        "<h1 style=\"margin:0 0 14px;font-size:24px;line-height:1.2;color:#101413;\">Bem-vindo à GoTrendLabs</h1>"
        "<p>Sua conta foi criada. Você já pode acompanhar mercados públicos, reputação, carteira educativa e sinais da comunidade.</p>"
        "<p style=\"margin:24px 0;\"><a href=\"{{ platform_url }}\" style=\"display:inline-block;background:#101413;color:#fff;text-decoration:none;border-radius:999px;padding:12px 18px;font-weight:700;\">Abrir GoTrendLabs</a></p>"
        "<p style=\"color:#5f6b6b;font-size:14px;\">GTL Credits são educativos e usados apenas dentro da GoTrendLabs.</p>"
        "</div>"
    ),
}


def seed_welcome_template(apps, schema_editor):
    EmailTemplate = apps.get_model("communications", "EmailTemplate")
    EmailTemplate.objects.update_or_create(
        key="user.welcome",
        locale="pt-br",
        defaults={
            "subject": WELCOME_TEMPLATE["subject"],
            "body_text": WELCOME_TEMPLATE["body_text"],
            "body_html": WELCOME_TEMPLATE["body_html"],
            "is_active": True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("communications", "0005_grant_email_runtime_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_welcome_template, migrations.RunPython.noop),
    ]
