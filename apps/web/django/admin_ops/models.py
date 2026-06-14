import hashlib
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone


def _release_slug(value):
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value or "").strip()).strip("-") or "release"


def mobile_app_release_upload_to(instance, filename):
    extension = ".apk" if str(filename or "").lower().endswith(".apk") else ""
    version = _release_slug(instance.version_name)
    code = _release_slug(instance.version_code)
    return f"app_releases/{instance.platform}/gotrendlabs-{instance.platform}-{version}-{code}{extension}"


class SiteConfig(models.Model):
    EMAIL_PROVIDER_SMTP = "smtp"
    EMAIL_PROVIDER_RESEND = "resend"
    EMAIL_PROVIDER_CHOICES = (
        (EMAIL_PROVIDER_SMTP, "SMTP"),
        (EMAIL_PROVIDER_RESEND, "Resend"),
    )

    singleton_key = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    wallet_recharge_min_balance_gtl = models.PositiveIntegerField(default=100)
    referral_bonus_gtl = models.PositiveIntegerField(default=200)
    position_reinforcement_enabled = models.BooleanField(default=True)
    position_reinforcement_max_count = models.PositiveIntegerField(default=3)
    position_revision_enabled = models.BooleanField(default=True)
    position_revision_max_count = models.PositiveIntegerField(default=1)
    position_revision_cutoff_hours = models.PositiveIntegerField(default=24)
    position_revision_penalty_percent = models.PositiveIntegerField(default=20)
    position_reinforcement_min_gtl = models.PositiveIntegerField(default=1)
    position_revision_min_remaining_gtl = models.PositiveIntegerField(default=1)
    daemon_stale_after_minutes = models.PositiveIntegerField(default=7)
    daemon_missing_after_minutes = models.PositiveIntegerField(default=21)
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
    ai_max_stake_gtl = models.PositiveIntegerField(default=25)
    ai_max_predictions_per_cycle = models.PositiveIntegerField(default=1)
    ai_max_predictions_per_day = models.PositiveIntegerField(default=10)
    ai_skip_if_human_comments_recent = models.BooleanField(default=True)
    ai_recent_human_comment_window_hours = models.PositiveIntegerField(default=6)
    ai_openai_timeout_seconds = models.PositiveIntegerField(default=20)
    ai_openai_max_retries = models.PositiveIntegerField(default=1)
    ai_paused_until = models.DateTimeField(null=True, blank=True)
    ai_pause_reason = models.TextField(blank=True, default="")
    email_enabled = models.BooleanField(default=False)
    email_provider = models.CharField(max_length=20, choices=EMAIL_PROVIDER_CHOICES, default=EMAIL_PROVIDER_SMTP)
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
        db_table = "gotrendlabs_site_config"
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
        if self.email_provider == self.EMAIL_PROVIDER_RESEND:
            return bool(self.email_enabled and self.default_from_email)
        return bool(self.email_enabled and self.smtp_host and self.smtp_port and self.default_from_email)


class MobileAppRelease(models.Model):
    PLATFORM_CHOICES = (("android", "Android"),)

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default="android")
    version_name = models.CharField(max_length=40)
    version_code = models.PositiveIntegerField()
    apk = models.FileField(upload_to=mobile_app_release_upload_to)
    sha256 = models.CharField(max_length=64, blank=True, editable=False)
    file_size = models.PositiveBigIntegerField(default=0, editable=False)
    release_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_mobile_app_releases",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_mobile_app_releases"
        ordering = ["-published_at", "-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["platform"],
                condition=Q(is_active=True),
                name="uniq_active_mobile_release_per_platform",
            ),
        ]
        indexes = [
            models.Index(fields=["platform", "is_active"], name="gtl_mobrel_platform_active_idx"),
            models.Index(fields=["platform", "version_code"], name="gtl_mobrel_plat_ver_idx"),
        ]

    def __str__(self):
        return f"{self.get_platform_display()} {self.version_name} ({self.version_code})"

    def clean(self):
        super().clean()
        if self.platform != "android":
            raise ValidationError({"platform": "Apenas Android é suportado nesta fase."})
        if self.apk and not self.apk.name.lower().endswith(".apk"):
            raise ValidationError({"apk": "Envie um arquivo .apk."})

    @classmethod
    def active_android(cls):
        return cls.objects.filter(platform="android", is_active=True).order_by("-published_at", "-id").first()

    def save(self, *args, **kwargs):
        if self.is_active and not self.published_at:
            self.published_at = timezone.now()
        with transaction.atomic():
            if self.is_active:
                MobileAppRelease.objects.filter(platform=self.platform, is_active=True).exclude(pk=self.pk).update(is_active=False)
            super().save(*args, **kwargs)
            sha256, file_size = self._calculate_file_metadata()
            updates = {}
            if sha256 and sha256 != self.sha256:
                self.sha256 = sha256
                updates["sha256"] = sha256
            if file_size and file_size != self.file_size:
                self.file_size = file_size
                updates["file_size"] = file_size
            if updates:
                MobileAppRelease.objects.filter(pk=self.pk).update(**updates)

    def _calculate_file_metadata(self):
        if not self.apk:
            return "", 0
        digest = hashlib.sha256()
        size = 0
        with self.apk.open("rb") as apk_file:
            for chunk in iter(lambda: apk_file.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
        return digest.hexdigest(), size
