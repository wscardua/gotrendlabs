from django.conf import settings
from django.db import models


class SiteConfig(models.Model):
    singleton_key = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    wallet_recharge_min_balance_oc = models.PositiveIntegerField(default=100)
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
