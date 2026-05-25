from django.conf import settings
from django.db import models


class SiteConfig(models.Model):
    singleton_key = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    wallet_recharge_min_balance_oc = models.PositiveIntegerField(default=100)
    daemon_stale_after_minutes = models.PositiveIntegerField(default=5)
    daemon_missing_after_minutes = models.PositiveIntegerField(default=15)
    system_log_retention_days = models.PositiveIntegerField(default=90)
    ai_audit_retention_days = models.PositiveIntegerField(default=90)
    ai_agents_enabled = models.BooleanField(default=False)
    ai_commenting_enabled = models.BooleanField(default=False)
    ai_predictions_enabled = models.BooleanField(default=False)
    ai_llm_provider = models.CharField(max_length=40, default="openai")
    ai_llm_base_url = models.URLField(default="https://api.openai.com/v1")
    ai_model = models.CharField(max_length=120, default="gpt-5.4-mini")
    ai_high_reasoning_model = models.CharField(max_length=120, default="gpt-5.5")
    ai_market_cooldown_hours = models.PositiveIntegerField(default=24)
    ai_max_comments_per_market_per_day = models.PositiveIntegerField(default=1)
    ai_max_comments_per_cycle = models.PositiveIntegerField(default=1)
    ai_max_comment_attempts_per_cycle = models.PositiveIntegerField(default=3)
    ai_comment_candidate_limit = models.PositiveIntegerField(default=200)
    ai_max_comments_per_day = models.PositiveIntegerField(default=20)
    ai_comment_max_chars = models.PositiveIntegerField(default=700)
    ai_min_humans_for_prediction = models.PositiveIntegerField(default=1)
    ai_max_stake_oc = models.PositiveIntegerField(default=25)
    ai_max_predictions_per_cycle = models.PositiveIntegerField(default=1)
    ai_max_predictions_per_day = models.PositiveIntegerField(default=10)
    ai_skip_if_human_comments_recent = models.BooleanField(default=True)
    ai_recent_human_comment_window_hours = models.PositiveIntegerField(default=6)
    ai_openai_timeout_seconds = models.PositiveIntegerField(default=20)
    ai_openai_max_retries = models.PositiveIntegerField(default=1)
    ai_paused_until = models.DateTimeField(null=True, blank=True)
    ai_pause_reason = models.TextField(blank=True, default="")
    email_enabled = models.BooleanField(default=False)
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_use_ssl = models.BooleanField(default=False)
    smtp_timeout_seconds = models.PositiveIntegerField(default=10)
    default_from_email = models.EmailField(blank=True)
    default_reply_to_email = models.EmailField(blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_site_configs",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orynth_site_config"
        constraints = [
            models.CheckConstraint(
                check=~(models.Q(smtp_use_tls=True) & models.Q(smtp_use_ssl=True)),
                name="site_config_tls_ssl_not_both",
            ),
        ]

    @classmethod
    def get_solo(cls):
        config, _created = cls.objects.get_or_create(singleton_key=1)
        return config

    @property
    def is_ready_for_delivery(self):
        return bool(self.email_enabled and self.smtp_host and self.smtp_port and self.default_from_email)
