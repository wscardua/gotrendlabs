from django.conf import settings
from django.db import models
from django.utils import timezone


class EmailTemplate(models.Model):
    key = models.CharField(max_length=80)
    locale = models.CharField(max_length=10, choices=(("pt-br", "PT-BR"), ("en", "EN")), default="pt-br")
    subject = models.CharField(max_length=255)
    body_text = models.TextField()
    body_html = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_email_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_email_templates"
        ordering = ["key", "locale"]
        constraints = [
            models.UniqueConstraint(fields=["key", "locale"], name="uniq_email_template_key_locale"),
        ]
        indexes = [
            models.Index(fields=["key", "locale", "is_active"]),
        ]

    def __str__(self):
        return f"{self.key} [{self.locale}]"


class EmailDelivery(models.Model):
    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("sending", "Sending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("suppressed", "Suppressed"),
    )

    event_type = models.CharField(max_length=80)
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_deliveries",
    )
    recipient_email = models.EmailField()
    template_key = models.CharField(max_length=80)
    locale = models.CharField(max_length=10, default="pt-br")
    subject = models.CharField(max_length=255, blank=True)
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    context = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=191, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    attempt_count = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    provider_message_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_email_deliveries"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "next_attempt_at"]),
            models.Index(fields=["recipient_user", "-created_at"]),
            models.Index(fields=["event_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} -> {self.recipient_email}"


class EmailConfirmationToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_confirmation_tokens")
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "gotrendlabs_email_confirmation_tokens"
        indexes = [
            models.Index(fields=["token_hash"]),
            models.Index(fields=["user", "used_at", "expires_at"]),
        ]
