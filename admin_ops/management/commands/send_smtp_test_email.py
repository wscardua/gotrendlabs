import smtplib
import ssl
from email.message import EmailMessage

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from admin_ops.models import SiteConfig


class Command(BaseCommand):
    help = "Send an operational SMTP test email using the SiteConfig SMTP settings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            default="success@simulator.amazonses.com",
            help="Recipient address. Defaults to the Amazon SES mailbox simulator success address.",
        )
        parser.add_argument("--subject", default="GoTrendLabs SES SMTP sandbox test")
        parser.add_argument(
            "--body",
            default=(
                "GoTrendLabs SMTP sandbox test. "
                "This message validates the operational SMTP configuration only."
            ),
        )
        parser.add_argument("--dry-run", action="store_true", help="Validate settings and build the message without sending.")

    def handle(self, *args, **options):
        site_config = SiteConfig.get_solo()
        secret = settings.GOTRENDLABS_SMTP_PASSWORD or settings.GOTRENDLABS_SMTP_API_KEY
        recipient = options["to"].strip()
        missing = []

        if not site_config.smtp_host:
            missing.append("smtp_host")
        if not site_config.smtp_port:
            missing.append("smtp_port")
        if not site_config.smtp_username:
            missing.append("smtp_username")
        if not site_config.default_from_email:
            missing.append("default_from_email")
        if not secret:
            missing.append("GOTRENDLABS_SMTP_PASSWORD or GOTRENDLABS_SMTP_API_KEY")
        if not recipient:
            missing.append("--to")
        if site_config.smtp_use_tls and site_config.smtp_use_ssl:
            missing.append("smtp_use_tls/smtp_use_ssl cannot both be enabled")
        if missing:
            raise CommandError("SMTP test is missing required setting(s): " + ", ".join(missing))

        message = EmailMessage()
        message["From"] = site_config.default_from_email
        message["To"] = recipient
        message["Subject"] = options["subject"]
        if site_config.default_reply_to_email:
            message["Reply-To"] = site_config.default_reply_to_email
        message.set_content(options["body"])

        if not site_config.email_enabled:
            self.stdout.write("Email delivery flag is disabled; continuing with operational SMTP test.")

        if options["dry_run"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"SMTP dry run ready for {recipient} via {site_config.smtp_host}:{site_config.smtp_port}."
                )
            )
            return

        try:
            if site_config.smtp_use_ssl:
                with smtplib.SMTP_SSL(
                    site_config.smtp_host,
                    site_config.smtp_port,
                    timeout=site_config.smtp_timeout_seconds,
                    context=ssl.create_default_context(),
                ) as smtp:
                    smtp.login(site_config.smtp_username, secret)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP(
                    site_config.smtp_host,
                    site_config.smtp_port,
                    timeout=site_config.smtp_timeout_seconds,
                ) as smtp:
                    smtp.ehlo()
                    if site_config.smtp_use_tls:
                        smtp.starttls(context=ssl.create_default_context())
                        smtp.ehlo()
                    smtp.login(site_config.smtp_username, secret)
                    smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise CommandError(f"SMTP test failed: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"SMTP test email sent to {recipient}."))
