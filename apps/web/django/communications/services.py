import smtplib
import ssl
from datetime import timedelta
from email.message import EmailMessage

import httpx
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.template import Context, Engine
from django.utils import timezone

from apps.web.django.admin_ops.models import SiteConfig
from apps.web.django.communications.models import EmailDelivery, EmailTemplate


RESEND_EMAILS_API_URL = "https://api.resend.com/emails"
TRANSACTIONAL_FOOTER_TEMPLATE_KEY = "system.transactional_footer"


DEFAULT_EMAIL_TEMPLATES = {
    TRANSACTIONAL_FOOTER_TEMPLATE_KEY: {
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
    },
    "user.welcome": {
        "pt-br": {
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
        },
        "en": {
            "subject": "Welcome to GoTrendLabs",
            "body_text": (
                "Hi {{ display_name }},\n\n"
                "Your GoTrendLabs account has been created.\n\n"
                "You can now follow public markets, reputation, educational wallet, and community signals:\n"
                "{{ platform_url }}\n\n"
                "GoTrendLabs is an educational prediction social network. GTL Credits are not real money, investments, or withdrawable funds."
            ),
        },
    },
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


def _public_base_url():
    return (getattr(settings, "PUBLIC_SHARE_BASE_URL", "") or "https://gotrendlabs.com.br").rstrip("/")


def _transactional_footer_context(locale):
    locale = normalize_locale(locale)
    base_url = _public_base_url()
    if locale == "en":
        return {
            "platform_name": "GoTrendLabs",
            "platform_description": "Educational prediction markets, public consensus, and auditable reputation.",
            "transaction_reason": "This transactional email was sent because of an action on your account or participation on the platform.",
            "platform_url": base_url,
        }
    return {
        "platform_name": "GoTrendLabs",
        "platform_description": "Rede social de previsões educativas, consenso público e reputação auditável.",
        "transaction_reason": "Este é um email transacional enviado por uma ação na sua conta ou participação na plataforma.",
        "platform_url": base_url,
    }


def _template_sources(template_key, locale):
    template = (
        EmailTemplate.objects.filter(key=template_key, locale=locale, is_active=True).first()
        or EmailTemplate.objects.filter(key=template_key, locale="pt-br", is_active=True).first()
    )
    defaults = DEFAULT_EMAIL_TEMPLATES.get(template_key, {})
    default = defaults.get(locale) or defaults.get("pt-br") or {"subject": template_key, "body_text": ""}
    return {
        "subject": template.subject if template else default["subject"],
        "body_text": template.body_text if template else default["body_text"],
        "body_html": template.body_html if template and template.body_html else default.get("body_html", ""),
    }


def _render_source(source, context):
    return Engine(debug=False, string_if_invalid="").from_string(source).render(Context(context or {}, autoescape=True)).strip()


def _transactional_footer(locale, *, html=False):
    locale = normalize_locale(locale)
    source_key = "body_html" if html else "body_text"
    sources = _template_sources(TRANSACTIONAL_FOOTER_TEMPLATE_KEY, locale)
    source = sources.get(source_key) or DEFAULT_EMAIL_TEMPLATES[TRANSACTIONAL_FOOTER_TEMPLATE_KEY]["pt-br"][source_key]
    rendered = _render_source(source, _transactional_footer_context(locale))
    if not rendered:
        rendered = _render_source(DEFAULT_EMAIL_TEMPLATES[TRANSACTIONAL_FOOTER_TEMPLATE_KEY]["pt-br"][source_key], _transactional_footer_context(locale))
    return rendered if html else "\n\n" + rendered


def transactional_footer_preview(locale):
    return {
        "body_text": _transactional_footer(locale, html=False),
        "body_html": _transactional_footer(locale, html=True),
    }


def _with_transactional_footer(content, locale, *, html=False):
    if not content:
        return content
    if "Este é um email transacional" in content or "This transactional email was sent" in content:
        return content
    if html and content.rstrip().endswith("</div>"):
        return content.rstrip()[:-6] + _transactional_footer(locale, html=True) + "</div>"
    return content.rstrip() + _transactional_footer(locale, html=html)


def render_template(template_key, locale, context):
    locale = normalize_locale(locale)
    sources = _template_sources(template_key, locale)
    rendered = {
        "subject": _render_source(sources["subject"], context),
        "body_text": _render_source(sources["body_text"], context),
        "body_html": _render_source(sources["body_html"], context) if sources["body_html"] else "",
    }
    if template_key == TRANSACTIONAL_FOOTER_TEMPLATE_KEY:
        return rendered
    rendered["body_text"] = _with_transactional_footer(rendered["body_text"], locale)
    rendered["body_html"] = _with_transactional_footer(rendered["body_html"], locale, html=True) if rendered["body_html"] else ""
    return rendered


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


def _resend_payload(site_config, delivery, rendered):
    payload = {
        "from": site_config.default_from_email,
        "to": [delivery.recipient_email],
        "subject": rendered["subject"],
        "text": rendered["body_text"] or " ",
    }
    if rendered["body_html"]:
        payload["html"] = rendered["body_html"]
    if site_config.default_reply_to_email:
        payload["reply_to"] = site_config.default_reply_to_email
    return payload


def _send_resend_message(site_config, delivery, rendered, secret):
    response = httpx.post(
        RESEND_EMAILS_API_URL,
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
            "Idempotency-Key": delivery.idempotency_key[:256],
        },
        json=_resend_payload(site_config, delivery, rendered),
        timeout=site_config.smtp_timeout_seconds or 10,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = response.text[:500] if response.text else str(exc)
        raise RuntimeError(f"Resend API error {response.status_code}: {detail}") from exc
    data = response.json()
    return str(data.get("id", ""))


def _email_secret(site_config):
    if site_config.email_provider == SiteConfig.EMAIL_PROVIDER_RESEND:
        return settings.GOTRENDLABS_RESEND_API_KEY
    return settings.GOTRENDLABS_SMTP_PASSWORD or settings.GOTRENDLABS_SMTP_API_KEY


def _email_settings_error(site_config, secret):
    if not site_config.email_enabled:
        return "Email delivery is disabled."
    if not site_config.default_from_email:
        return "Default sender email is missing."
    if site_config.email_provider == SiteConfig.EMAIL_PROVIDER_RESEND:
        if not secret:
            return "GOTRENDLABS_RESEND_API_KEY is not configured."
        return ""
    if not site_config.smtp_host or not site_config.smtp_port or not site_config.smtp_username or not secret:
        return "SMTP settings are incomplete."
    if site_config.smtp_use_tls and site_config.smtp_use_ssl:
        return "SMTP TLS and SSL cannot both be enabled."
    return ""


def process_due_email_deliveries(*, limit=25, now=None, event_types=None):
    now = now or timezone.now()
    site_config = SiteConfig.get_solo()
    secret = _email_secret(site_config)
    stats = {"sent": 0, "failed": 0, "suppressed": 0, "skipped": 0}
    with transaction.atomic():
        queryset = EmailDelivery.objects.select_for_update(skip_locked=True).filter(
            status__in=["queued", "failed"],
            next_attempt_at__lte=now,
            attempt_count__lt=F("max_attempts"),
        )
        if event_types:
            queryset = queryset.filter(event_type__in=event_types)
        deliveries = list(queryset.order_by("next_attempt_at", "id")[:limit])
        for delivery in deliveries:
            settings_error = _email_settings_error(site_config, secret)
            if settings_error:
                delivery.status = "failed"
                delivery.last_error = settings_error
                delivery.next_attempt_at = now + timedelta(minutes=30)
                delivery.save(update_fields=["status", "last_error", "next_attempt_at", "updated_at"])
                stats["failed"] += 1
                continue
            delivery.status = "sending"
            delivery.last_attempt_at = now
            delivery.attempt_count += 1
            delivery.save(update_fields=["status", "last_attempt_at", "attempt_count", "updated_at"])
            try:
                rendered = render_template(delivery.template_key, delivery.locale, delivery.context)
                provider_message_id = ""
                if site_config.email_provider == SiteConfig.EMAIL_PROVIDER_RESEND:
                    provider_message_id = _send_resend_message(site_config, delivery, rendered, secret)
                else:
                    message, rendered = _build_message(site_config, delivery)
                    _send_message(site_config, message, secret)
            except (OSError, smtplib.SMTPException, httpx.HTTPError, RuntimeError, ValueError) as exc:
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
                delivery.provider_message_id = provider_message_id
                stats["sent"] += 1
            delivery.save()
    if not deliveries:
        stats["skipped"] += 1
    return stats
