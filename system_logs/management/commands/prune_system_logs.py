from django.core.management.base import BaseCommand
from django.utils import timezone

from system_logs.models import SystemLog


class Command(BaseCommand):
    help = "Remove system troubleshooting logs past their expiration date."

    def handle(self, *args, **options):
        deleted, _ = SystemLog.objects.filter(expires_at__lt=timezone.now()).delete()
        self.stdout.write(self.style.SUCCESS(f"Removed {deleted} expired system logs."))
