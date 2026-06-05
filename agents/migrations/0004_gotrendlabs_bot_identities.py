from django.db import migrations


BOT_IDENTITIES = (
    {
        "old_username": "@gotrendlabs_ai_analyst",
        "new_username": "@gotrendlabs_ai_analyst",
        "email": "gotrendlabs-ai-analyst@gotrendlabs.com.br",
        "first_name": "GoTrendLabs AI Analyst",
        "profile_bio": "Agente IA oficial da GoTrendLabs para comentarios de mercado.",
        "agent_name": "GoTrendLabs AI Analyst",
        "agent_type": "analyst",
    },
    {
        "old_username": "@gotrendlabs_ai_liquidity",
        "new_username": "@gotrendlabs_ai_liquidity",
        "email": "gotrendlabs-ai-liquidity@gotrendlabs.com.br",
        "first_name": "GoTrendLabs AI Liquidity",
        "profile_bio": "Bot oficial da GoTrendLabs para testes controlados de liquidez educativa.",
        "agent_name": "GoTrendLabs AI Liquidity",
        "agent_type": "liquidity",
    },
)


def rename_legacy_bot_identities(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    UserProfile = apps.get_model("accounts", "UserProfile")
    AiAgent = apps.get_model("agents", "AiAgent")

    for identity in BOT_IDENTITIES:
        old_user = User.objects.filter(username=identity["old_username"]).first()
        new_user = User.objects.filter(username=identity["new_username"]).first()
        user = old_user or new_user
        if not user:
            continue

        if old_user and not new_user:
            user.username = identity["new_username"]
        user.email = identity["email"]
        user.first_name = identity["first_name"]
        user.is_bot = True
        user.is_active = True
        user.account_status = "active"
        user.save(update_fields=["username", "email", "first_name", "is_bot", "is_active", "account_status"])

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "display_name": identity["first_name"],
                "bio": identity["profile_bio"],
                "is_public": True,
            },
        )

        AiAgent.objects.filter(user=user, agent_type=identity["agent_type"]).update(
            name=identity["agent_name"],
            personality_prompt=f"Atue como IA oficial da GoTrendLabs em mercados educativos de previsao.",
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0017_gotrendlabs_email_domains"),
        ("agents", "0003_gotrendlabs_rebrand"),
    ]

    operations = [
        migrations.RunPython(rename_legacy_bot_identities, migrations.RunPython.noop),
    ]
