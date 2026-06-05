from django.db import migrations


PTBR_TEMPLATES = {
    "user.email_confirmation": {
        "subject": "Confirme seu email e libere sua conta",
        "body_text": (
            "Olá {{ display_name }},\n\n"
            "Que bom ter você na GoTrendLabs.\n\n"
            "Confirme seu email para liberar previsões, comentários, sugestões e demais ações da conta:\n"
            "{{ confirmation_url }}\n\n"
            "Este link expira em {{ expires_hours }} horas. Se você não criou esta conta, pode ignorar esta mensagem."
        ),
        "body_html": (
            "<div style=\"font-family:Arial,sans-serif;line-height:1.55;color:#1f2b2b;max-width:620px;margin:0 auto;padding:24px;\">"
            "<p style=\"margin:0 0 16px;\">Olá {{ display_name }},</p>"
            "<h1 style=\"margin:0 0 14px;font-size:24px;line-height:1.2;color:#101413;\">Bem-vindo à GoTrendLabs</h1>"
            "<p>Confirme seu email para liberar previsões, comentários, sugestões e outras ações da sua conta.</p>"
            "<p style=\"margin:24px 0;\"><a href=\"{{ confirmation_url }}\" style=\"display:inline-block;background:#101413;color:#fff;text-decoration:none;border-radius:999px;padding:12px 18px;font-weight:700;\">Confirmar email</a></p>"
            "<p style=\"color:#5f6b6b;font-size:14px;\">O link expira em {{ expires_hours }} horas. Se você não criou esta conta, pode ignorar esta mensagem.</p>"
            "</div>"
        ),
    },
    "account.password_reset": {
        "subject": "Redefina sua senha na GoTrendLabs",
        "body_text": (
            "Olá {{ display_name }},\n\n"
            "Recebemos uma solicitação para redefinir sua senha.\n\n"
            "Use este link para criar uma nova senha:\n"
            "{{ reset_url }}\n\n"
            "O link expira em {{ expires_minutes }} minutos. Se você não pediu isso, ignore este email."
        ),
        "body_html": (
            "<div style=\"font-family:Arial,sans-serif;line-height:1.55;color:#1f2b2b;max-width:620px;margin:0 auto;padding:24px;\">"
            "<p style=\"margin:0 0 16px;\">Olá {{ display_name }},</p>"
            "<h1 style=\"margin:0 0 14px;font-size:24px;line-height:1.2;color:#101413;\">Vamos proteger seu acesso</h1>"
            "<p>Recebemos uma solicitação para redefinir sua senha na GoTrendLabs.</p>"
            "<p style=\"margin:24px 0;\"><a href=\"{{ reset_url }}\" style=\"display:inline-block;background:#101413;color:#fff;text-decoration:none;border-radius:999px;padding:12px 18px;font-weight:700;\">Redefinir senha</a></p>"
            "<p style=\"color:#5f6b6b;font-size:14px;\">O link expira em {{ expires_minutes }} minutos. Se você não pediu isso, ignore este email.</p>"
            "</div>"
        ),
    },
    "market.locked": {
        "subject": "{{ market_title }} foi fechado para novas previsões",
        "body_text": (
            "Olá {{ display_name }},\n\n"
            "O mercado \"{{ market_title }}\" foi fechado.\n\n"
            "A partir de agora, ninguém consegue alterar posições. É hora de acompanhar a apuração:\n"
            "{{ market_url }}\n\n"
            "Quando houver resolução, avisaremos por aqui."
        ),
        "body_html": (
            "<div style=\"font-family:Arial,sans-serif;line-height:1.55;color:#1f2b2b;max-width:620px;margin:0 auto;padding:24px;\">"
            "<p style=\"margin:0 0 16px;\">Olá {{ display_name }},</p>"
            "<h1 style=\"margin:0 0 14px;font-size:24px;line-height:1.2;color:#101413;\">Mercado fechado para novas previsões</h1>"
            "<p>O mercado <strong>{{ market_title }}</strong> entrou em apuração. As posições não podem mais ser alteradas.</p>"
            "<p style=\"margin:24px 0;\"><a href=\"{{ market_url }}\" style=\"display:inline-block;background:#101413;color:#fff;text-decoration:none;border-radius:999px;padding:12px 18px;font-weight:700;\">Acompanhar mercado</a></p>"
            "<p style=\"color:#5f6b6b;font-size:14px;\">Quando o resultado for publicado, você recebe um novo aviso.</p>"
            "</div>"
        ),
    },
    "market.resolved": {
        "subject": "Resultado publicado: {{ market_title }}",
        "body_text": (
            "Olá {{ display_name }},\n\n"
            "O resultado do mercado \"{{ market_title }}\" foi publicado.\n\n"
            "Resultado: {{ winning_option }}\n"
            "Veja os detalhes, o histórico do consenso e os efeitos na sua carteira:\n"
            "{{ market_url }}"
        ),
        "body_html": (
            "<div style=\"font-family:Arial,sans-serif;line-height:1.55;color:#1f2b2b;max-width:620px;margin:0 auto;padding:24px;\">"
            "<p style=\"margin:0 0 16px;\">Olá {{ display_name }},</p>"
            "<h1 style=\"margin:0 0 14px;font-size:24px;line-height:1.2;color:#101413;\">Resultado publicado</h1>"
            "<p>O mercado <strong>{{ market_title }}</strong> foi resolvido.</p>"
            "<p style=\"padding:12px 14px;border-left:4px solid #136f4a;background:#eef7f0;\"><strong>Resultado:</strong> {{ winning_option }}</p>"
            "<p style=\"margin:24px 0;\"><a href=\"{{ market_url }}\" style=\"display:inline-block;background:#101413;color:#fff;text-decoration:none;border-radius:999px;padding:12px 18px;font-weight:700;\">Ver detalhes</a></p>"
            "<p style=\"color:#5f6b6b;font-size:14px;\">Confira o consenso final e os efeitos na sua carteira educativa.</p>"
            "</div>"
        ),
    },
    "wallet.credited": {
        "subject": "Você recebeu {{ amount }} GT₵",
        "body_text": (
            "Olá {{ display_name }},\n\n"
            "Você recebeu {{ amount }} GT₵ na sua carteira educativa.\n\n"
            "Motivo: {{ description }}\n"
            "Confira sua carteira:\n"
            "{{ wallet_url }}"
        ),
        "body_html": (
            "<div style=\"font-family:Arial,sans-serif;line-height:1.55;color:#1f2b2b;max-width:620px;margin:0 auto;padding:24px;\">"
            "<p style=\"margin:0 0 16px;\">Olá {{ display_name }},</p>"
            "<h1 style=\"margin:0 0 14px;font-size:24px;line-height:1.2;color:#101413;\">Créditos adicionados à sua carteira</h1>"
            "<p style=\"font-size:28px;font-weight:800;margin:18px 0;color:#136f4a;\">{{ amount }} GT₵</p>"
            "<p><strong>Motivo:</strong> {{ description }}</p>"
            "<p style=\"margin:24px 0;\"><a href=\"{{ wallet_url }}\" style=\"display:inline-block;background:#101413;color:#fff;text-decoration:none;border-radius:999px;padding:12px 18px;font-weight:700;\">Abrir carteira</a></p>"
            "<p style=\"color:#5f6b6b;font-size:14px;\">GTL Credits são educativos e usados apenas dentro da GoTrendLabs.</p>"
            "</div>"
        ),
    },
}


def polish_ptbr_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("communications", "EmailTemplate")
    for key, payload in PTBR_TEMPLATES.items():
        EmailTemplate.objects.update_or_create(
            key=key,
            locale="pt-br",
            defaults={
                "subject": payload["subject"],
                "body_text": payload["body_text"],
                "body_html": payload["body_html"],
                "is_active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("communications", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(polish_ptbr_templates, migrations.RunPython.noop),
    ]
