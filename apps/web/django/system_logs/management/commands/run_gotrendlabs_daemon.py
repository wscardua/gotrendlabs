import time

from django.core.management.base import BaseCommand

from apps.api.backend_api.daemon_services import run_daemon_cycle


class Command(BaseCommand):
    help = "Run the GoTrendLabs operational daemon."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run a single daemon cycle and exit.")
        parser.add_argument("--interval-seconds", type=int, default=60, help="Seconds between daemon cycles.")

    def handle(self, *args, **options):
        interval_seconds = max(1, int(options["interval_seconds"]))
        while True:
            result = run_daemon_cycle()
            ai = result.get("ai", {})
            email = result.get("email", {})
            pruned = result.get("pruned_log_details", {})
            self.stdout.write(
                self.style.SUCCESS(
                    "Daemon cycle complete: "
                    f"locked {len(result['locked_markets'])} market(s), "
                    f"pruned {result['pruned_logs']} operational record(s) "
                    f"({pruned.get('system_logs', result['pruned_logs'])} system log(s), "
                    f"{pruned.get('ai_agent_actions', 0)} AI audit action(s)), "
                    f"AI comments {ai.get('comments_created', 0)}, "
                    f"AI predictions {ai.get('predictions_created', 0)}, "
                    f"AI skips {ai.get('skipped', 0)}, "
                    f"AI errors {ai.get('errors', 0)}, "
                    f"email sent {email.get('sent', 0)}, "
                    f"email failed {email.get('failed', 0)}, "
                    f"email suppressed {email.get('suppressed', 0)}."
                )
            )
            if options["once"]:
                return
            time.sleep(interval_seconds)
