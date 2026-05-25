from django.core.management.base import BaseCommand

from backend_api.daemon_services import prune_expired_operational_records


class Command(BaseCommand):
    help = "Remove system troubleshooting logs and AI agent audit actions past their retention date."

    def handle(self, *args, **options):
        deleted = prune_expired_operational_records()
        self.stdout.write(
            self.style.SUCCESS(
                "Removed "
                f"{deleted['system_logs']} expired system logs and "
                f"{deleted['ai_agent_actions']} expired AI audit actions."
            )
        )
