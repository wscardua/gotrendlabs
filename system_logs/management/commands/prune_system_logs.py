from django.core.management.base import BaseCommand

from backend_api.daemon_services import prune_expired_system_logs


class Command(BaseCommand):
    help = "Remove system troubleshooting logs past their expiration date."

    def handle(self, *args, **options):
        deleted = prune_expired_system_logs()
        self.stdout.write(self.style.SUCCESS(f"Removed {deleted} expired system logs."))
