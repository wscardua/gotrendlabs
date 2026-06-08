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


class PushDevice(models.Model):
    PROVIDER_CHOICES = (("fcm", "FCM"),)
    PLATFORM_CHOICES = (("android", "Android"), ("ios", "iOS"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_devices")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default="fcm")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    token = models.TextField()
    token_hash = models.CharField(max_length=64, db_index=True)
    app_version = models.CharField(max_length=40, blank=True)
    build_number = models.CharField(max_length=40, blank=True)
    device_label = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    push_enabled = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    provider_invalidated_at = models.DateTimeField(null=True, blank=True)
    disabled_reason = models.CharField(max_length=120, blank=True)
    last_registered_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_push_devices"
        ordering = ["-last_registered_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "provider", "token_hash"], name="uniq_push_device_user_provider_token"),
        ]
        indexes = [
            models.Index(fields=["user", "is_active", "-last_registered_at"], name="gtl_pushdev_user_active_idx"),
            models.Index(fields=["provider", "token_hash"], name="gtl_pushdev_provider_token_idx"),
        ]

    def __str__(self):
        return f"{self.provider}:{self.platform} user={self.user_id}"


class PushEventPolicy(models.Model):
    MODE_CHOICES = (("off", "Off"), ("immediate", "Immediate"), ("digest", "Digest"))

    event_type = models.CharField(max_length=80, unique=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="off")
    is_active = models.BooleanField(default=True)
    default_user_enabled = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=100)
    template_key = models.CharField(max_length=80, blank=True)
    allowed_variables = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_push_event_policies"
        ordering = ["priority", "event_type"]
        indexes = [
            models.Index(fields=["event_type", "is_active"]),
            models.Index(fields=["mode", "is_active"]),
        ]

    def __str__(self):
        return f"{self.event_type}: {self.mode}"


class PushTemplate(models.Model):
    event_type = models.CharField(max_length=80)
    locale = models.CharField(max_length=10, choices=(("pt-br", "PT-BR"), ("en", "EN")), default="pt-br")
    title = models.CharField(max_length=120)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    allowed_variables = models.JSONField(default=list, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_push_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_push_templates"
        ordering = ["event_type", "locale"]
        constraints = [
            models.UniqueConstraint(fields=["event_type", "locale"], name="uniq_push_template_event_locale"),
        ]
        indexes = [
            models.Index(fields=["event_type", "locale", "is_active"]),
        ]

    def __str__(self):
        return f"{self.event_type} [{self.locale}]"


class PushPreference(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_preferences")
    event_type = models.CharField(max_length=80, blank=True, default="")
    push_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_push_preferences"
        ordering = ["event_type", "id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "event_type"], name="uniq_push_preference_user_event"),
        ]
        indexes = [
            models.Index(fields=["user", "event_type"]),
        ]

    def __str__(self):
        return f"user={self.user_id} event={self.event_type or '*'} enabled={self.push_enabled}"


class PushDelivery(models.Model):
    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("sending", "Sending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("suppressed", "Suppressed"),
        ("dry_run", "Dry run"),
        ("invalid_token", "Invalid token"),
    )

    notification = models.ForeignKey("markets.UserNotification", on_delete=models.CASCADE, related_name="push_deliveries")
    device = models.ForeignKey(PushDevice, on_delete=models.CASCADE, related_name="push_deliveries")
    event_type = models.CharField(max_length=80)
    provider = models.CharField(max_length=20, default="fcm")
    template_key = models.CharField(max_length=80, blank=True)
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    policy_snapshot = models.JSONField(default=dict, blank=True)
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
        db_table = "gotrendlabs_push_deliveries"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "next_attempt_at"]),
            models.Index(fields=["event_type", "-created_at"]),
            models.Index(fields=["device", "-created_at"]),
            models.Index(fields=["notification", "device"]),
        ]

    def __str__(self):
        return f"{self.event_type} -> device={self.device_id}"
