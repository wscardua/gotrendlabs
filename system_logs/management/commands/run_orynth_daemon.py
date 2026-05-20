import time

from django.core.management.base import BaseCommand

from backend_api.daemon_services import run_daemon_cycle


class Command(BaseCommand):
    help = "Run the Orynth operational daemon."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run a single daemon cycle and exit.")
        parser.add_argument("--interval-seconds", type=int, default=60, help="Seconds between daemon cycles.")

    def handle(self, *args, **options):
        interval_seconds = max(1, int(options["interval_seconds"]))
        while True:
            result = run_daemon_cycle()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Daemon cycle complete: locked {len(result['locked_markets'])} market(s), pruned {result['pruned_logs']} log(s)."
                )
            )
            if options["once"]:
                return
            time.sleep(interval_seconds)
