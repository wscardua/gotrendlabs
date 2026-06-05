import smtplib
import ssl
from datetime import timedelta
from email.message import EmailMessage

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.template import Context, Engine
from django.utils import timezone

from admin_ops.models import SiteConfig
from communications.models import EmailDelivery, EmailTemplate


DEFAULT_EMAIL_TEMPLATES = {
    "user.email_confirmation": {
        "pt-br": {
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
        "en": {
            "subject": "Confirm your GoTrendLabs email",
            "body_text": (
                "Hi {{ display_name }},\n\n"
                "Welcome to GoTrendLabs. Confirm your email to unlock all account actions:\n"
                "{{ confirmation_url }}\n\n"
                "This link expires in {{ expires_hours }} hours."
            ),
        },
    },
    "account.password_reset": {
        "pt-br": {
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
        "en": {
            "subject": "Reset your GoTrendLabs password",
            "body_text": (
                "Hi {{ display_name }},\n\n"
                "We received a request to reset your password. Use the link below:\n"
                "{{ reset_url }}\n\n"
                "This link expires in {{ expires_minutes }} minutes. If you did not request this, ignore this email."
            ),
        },
    },
    "market.locked": {
        "pt-br": {
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
        "en": {
            "subject": "Market locked: {{ market_title }}",
            "body_text": (
                "The market \"{{ market_title }}\" is now closed for new predictions.\n\n"
                "Follow the result at {{ market_url }}."
            ),
        },
    },
    "market.resolved": {
        "pt-br": {
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
        "en": {
            "subject": "Market resolved: {{ market_title }}",
            "body_text": (
                "The market \"{{ market_title }}\" has been resolved.\n\n"
                "Outcome: {{ winning_option }}\n"
                "See details at {{ market_url }}."
            ),
        },
    },
    "wallet.credited": {
        "pt-br": {
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
        "en": {
            "subject": "Credits granted on GoTrendLabs",
            "body_text": (
                "You received {{ amount }} GT₵.\n\n"
                "Reason: {{ description }}\n"
                "See your wallet at {{ wallet_url }}."
            ),
        },
    },
}


def normalize_locale(locale):
    return locale if locale in {"pt-br", "en"} else "pt-br"


def render_template(template_key, locale, context):
    locale = normalize_locale(locale)
    template = (
        EmailTemplate.objects.filter(key=template_key, locale=locale, is_active=True).first()
        or EmailTemplate.objects.filter(key=template_key, locale="pt-br", is_active=True).first()
    )
    defaults = DEFAULT_EMAIL_TEMPLATES.get(template_key, {})
    default = defaults.get(locale) or defaults.get("pt-br") or {"subject": template_key, "body_text": ""}
    subject_source = template.subject if template else default["subject"]
    body_text_source = template.body_text if template else default["body_text"]
    body_html_source = template.body_html if template and template.body_html else default.get("body_html", "")
    engine = Engine(debug=False, string_if_invalid="")
    render_context = Context(context or {}, autoescape=True)
    return {
        "subject": engine.from_string(subject_source).render(render_context).strip(),
        "body_text": engine.from_string(body_text_source).render(render_context).strip(),
        "body_html": engine.from_string(body_html_source).render(render_context).strip() if body_html_source else "",
    }


def sandbox_recipient_allowed(recipient):
    recipient = (recipient or "").strip().lower()
    if not recipient:
        return False
    if getattr(settings, "GOTRENDLABS_SES_PRODUCTION_ACCESS", False):
        return True
    if recipient.endswith("@simulator.amazonses.com"):
        return True
    return recipient in getattr(settings, "GOTRENDLABS_EMAIL_SANDBOX_ALLOWLIST", set())


def _build_message(site_config, delivery):
    rendered = render_template(delivery.template_key, delivery.locale, delivery.context)
    message = EmailMessage()
    message["From"] = site_config.default_from_email
    message["To"] = delivery.recipient_email
    message["Subject"] = rendered["subject"]
    if site_config.default_reply_to_email:
        message["Reply-To"] = site_config.default_reply_to_email
    if rendered["body_html"]:
        message.set_content(rendered["body_text"] or " ")
        message.add_alternative(rendered["body_html"], subtype="html")
    else:
        message.set_content(rendered["body_text"] or " ")
    return message, rendered


def _send_message(site_config, message, secret):
    if site_config.smtp_use_ssl:
        with smtplib.SMTP_SSL(
            site_config.smtp_host,
            site_config.smtp_port,
            timeout=site_config.smtp_timeout_seconds,
            context=ssl.create_default_context(),
        ) as smtp:
            smtp.login(site_config.smtp_username, secret)
            smtp.send_message(message)
        return
    with smtplib.SMTP(site_config.smtp_host, site_config.smtp_port, timeout=site_config.smtp_timeout_seconds) as smtp:
        smtp.ehlo()
        if site_config.smtp_use_tls:
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
        smtp.login(site_config.smtp_username, secret)
        smtp.send_message(message)


def process_due_email_deliveries(*, limit=25, now=None):
    now = now or timezone.now()
    site_config = SiteConfig.get_solo()
    secret = settings.GOTRENDLABS_SMTP_PASSWORD or settings.GOTRENDLABS_SMTP_API_KEY
    stats = {"sent": 0, "failed": 0, "suppressed": 0, "skipped": 0}
    with transaction.atomic():
        deliveries = list(
            EmailDelivery.objects.select_for_update(skip_locked=True)
            .filter(status__in=["queued", "failed"], next_attempt_at__lte=now, attempt_count__lt=F("max_attempts"))
            .order_by("next_attempt_at", "id")[:limit]
        )
        for delivery in deliveries:
            if not site_config.email_enabled or not site_config.is_ready_for_delivery or not site_config.smtp_username or not secret:
                delivery.status = "failed"
                delivery.last_error = "SMTP settings are incomplete."
                delivery.next_attempt_at = now + timedelta(minutes=30)
                delivery.save(update_fields=["status", "last_error", "next_attempt_at", "updated_at"])
                stats["failed"] += 1
                continue
            if site_config.smtp_use_tls and site_config.smtp_use_ssl:
                delivery.status = "failed"
                delivery.last_error = "SMTP TLS and SSL cannot both be enabled."
                delivery.next_attempt_at = now + timedelta(minutes=30)
                delivery.save(update_fields=["status", "last_error", "next_attempt_at", "updated_at"])
                stats["failed"] += 1
                continue
            if not sandbox_recipient_allowed(delivery.recipient_email):
                delivery.status = "suppressed"
                delivery.last_error = "SES sandbox guard suppressed delivery to an unverified recipient."
                delivery.save(update_fields=["status", "last_error", "updated_at"])
                stats["suppressed"] += 1
                continue
            delivery.status = "sending"
            delivery.last_attempt_at = now
            delivery.attempt_count += 1
            delivery.save(update_fields=["status", "last_attempt_at", "attempt_count", "updated_at"])
            try:
                message, rendered = _build_message(site_config, delivery)
                _send_message(site_config, message, secret)
            except (OSError, smtplib.SMTPException) as exc:
                delivery.status = "failed"
                delivery.last_error = str(exc)
                delay_minutes = min(60, 5 * max(1, delivery.attempt_count))
                delivery.next_attempt_at = now + timedelta(minutes=delay_minutes)
                stats["failed"] += 1
            else:
                delivery.status = "sent"
                delivery.subject = rendered["subject"]
                delivery.body_text = rendered["body_text"]
                delivery.body_html = rendered["body_html"]
                delivery.sent_at = timezone.now()
                delivery.last_error = ""
                stats["sent"] += 1
            delivery.save()
    if not deliveries:
        stats["skipped"] += 1
    return stats
