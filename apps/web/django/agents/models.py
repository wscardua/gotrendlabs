from django.conf import settings
from django.db import models


class AiAgent(models.Model):
    AGENT_TYPE_CHOICES = (
        ("analyst", "Analyst"),
        ("liquidity", "Liquidity"),
        ("contrarian", "Contrarian"),
    )

    name = models.CharField(max_length=120)
    agent_type = models.CharField(max_length=32, choices=AGENT_TYPE_CHOICES, db_index=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ai_agent")
    is_active = models.BooleanField(default=False, db_index=True)
    personality_prompt = models.TextField(blank=True)
    comment_style = models.CharField(max_length=120, blank=True)
    max_comments_per_day = models.PositiveIntegerField(null=True, blank=True)
    max_predictions_per_day = models.PositiveIntegerField(null=True, blank=True)
    max_stake_gtl = models.PositiveIntegerField(null=True, blank=True)
    cooldown_hours = models.PositiveIntegerField(null=True, blank=True)
    min_humans_for_prediction = models.PositiveIntegerField(null=True, blank=True)
    last_action_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_ai_agents"
        ordering = ["agent_type", "name", "id"]
        indexes = [
            models.Index(fields=["agent_type", "is_active"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.agent_type})"


class AiAgentAction(models.Model):
    ACTION_TYPE_CHOICES = (
        ("comment", "Comment"),
        ("prediction", "Prediction"),
        ("cycle", "Cycle"),
    )
    STATUS_CHOICES = (
        ("created", "Created"),
        ("skipped", "Skipped"),
        ("failed", "Failed"),
    )

    agent = models.ForeignKey(AiAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name="actions")
    market = models.ForeignKey("markets.Market", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_agent_actions")
    action_type = models.CharField(max_length=32, choices=ACTION_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, db_index=True)
    reason = models.CharField(max_length=255, blank=True)
    payload_summary = models.JSONField(default=dict, blank=True)
    prompt_template_version = models.CharField(max_length=64, blank=True)
    prompt_hash = models.CharField(max_length=64, blank=True)
    comment = models.ForeignKey("markets.MarketComment", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_agent_actions")
    prediction = models.ForeignKey("markets.Prediction", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_agent_actions")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "gotrendlabs_ai_agent_actions"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["agent", "-created_at"]),
            models.Index(fields=["market", "-created_at"]),
            models.Index(fields=["action_type", "status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action_type}:{self.status}:{self.created_at:%Y-%m-%d %H:%M}"
