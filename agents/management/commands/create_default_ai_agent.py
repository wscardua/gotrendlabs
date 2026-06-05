from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import UserProfile
from agents.models import AiAgent


class Command(BaseCommand):
    help = "Create the default official GoTrendLabs AI analyst bot and agent."

    def add_arguments(self, parser):
        parser.add_argument("--activate", action="store_true", help="Create the agent as active.")

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        user, user_created = User.objects.get_or_create(
            username="@gotrendlabs_ai_analyst",
            defaults={
                "email": "gotrendlabs-ai-analyst@gotrendlabs.com.br",
                "first_name": "GoTrendLabs AI Analyst",
                "preferred_language": "pt-br",
                "is_bot": True,
                "is_active": True,
                "account_status": "active",
            },
        )
        changed = False
        if not user.is_bot:
            user.is_bot = True
            changed = True
        if user.first_name != "GoTrendLabs AI Analyst":
            user.first_name = "GoTrendLabs AI Analyst"
            changed = True
        if user.email != "gotrendlabs-ai-analyst@gotrendlabs.com.br":
            user.email = "gotrendlabs-ai-analyst@gotrendlabs.com.br"
            changed = True
        if changed:
            user.save(update_fields=["is_bot", "first_name", "email"])

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "display_name": "GoTrendLabs AI Analyst",
                "bio": "Agente IA oficial da GoTrendLabs",
                "strong_category": "",
                "is_public": True,
            },
        )
        agent, agent_created = AiAgent.objects.update_or_create(
            user=user,
            defaults={
                "name": "GoTrendLabs AI Analyst",
                "agent_type": "analyst",
                "is_active": bool(options["activate"]),
                "personality_prompt": "Comente mercados de forma equilibrada, curta e útil para participantes da GoTrendLabs.",
                "comment_style": "analise objetiva",
            },
        )
        created = []
        if user_created:
            created.append("usuário bot")
        if agent_created:
            created.append("agente")
        suffix = f" Criado: {', '.join(created)}." if created else ""
        self.stdout.write(self.style.SUCCESS(f"Agente oficial pronto: {agent.name} ({user.username}).{suffix}"))
