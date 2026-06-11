import uuid
from types import SimpleNamespace

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.web.django.admin_ops.models import SiteConfig
from apps.web.django.communications.services import _send_resend_message


class Command(BaseCommand):
    help = "Send an operational Resend test email using the SiteConfig sender settings."

    def add_arguments(self, parser):
        parser.add_argument("--to", default="wsca@icloud.com", help="Recipient address for the Resend test.")
        parser.add_argument("--subject", default="GoTrendLabs Resend transactional email test")
        parser.add_argument(
            "--body",
            default=(
                "GoTrendLabs Resend transactional email test. "
                "This message validates the operational Resend configuration only."
            ),
        )
        parser.add_argument("--dry-run", action="store_true", help="Validate settings and build the message without sending.")

    def handle(self, *args, **options):
        site_config = SiteConfig.get_solo()
        secret = settings.GOTRENDLABS_RESEND_API_KEY
        recipient = options["to"].strip()
        missing = []

        if not site_config.default_from_email:
            missing.append("default_from_email")
        if not secret:
            missing.append("GOTRENDLABS_RESEND_API_KEY")
        if not recipient:
            missing.append("--to")
        if missing:
            raise CommandError("Resend test is missing required setting(s): " + ", ".join(missing))

        if not site_config.email_enabled:
            self.stdout.write("Email delivery flag is disabled; continuing with operational Resend test.")

        delivery = SimpleNamespace(
            recipient_email=recipient,
            idempotency_key=f"admin.resend_test:{uuid.uuid4()}",
        )
        rendered = {
            "subject": options["subject"],
            "body_text": options["body"],
            "body_html": "",
        }

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"Resend dry run ready for {recipient}."))
            return

        try:
            message_id = _send_resend_message(site_config, delivery, rendered, secret)
        except Exception as exc:
            raise CommandError(f"Resend test failed: {exc}") from exc

        suffix = f" provider_message_id={message_id}" if message_id else ""
        self.stdout.write(self.style.SUCCESS(f"Resend test email sent to {recipient}.{suffix}"))
