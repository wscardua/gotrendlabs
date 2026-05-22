from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    ACCOUNT_STATUS_CHOICES = (("active", "Active"), ("deactivated", "Deactivated"))

    email = models.EmailField(unique=True)
    preferred_language = models.CharField(
        max_length=10,
        choices=(("pt-br", "PT-BR"), ("en", "EN")),
        default="pt-br",
    )
    external_provider = models.CharField(max_length=50, blank=True)
    external_subject = models.CharField(max_length=191, blank=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    terms_version = models.CharField(max_length=32, blank=True)
    account_status = models.CharField(max_length=32, choices=ACCOUNT_STATUS_CHOICES, default="active")
    deletion_requested_at = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    is_bot = models.BooleanField(default=False)

    class Meta:
        db_table = "orynth_users"


class AuthSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_sessions")
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "orynth_auth_sessions"
        indexes = [
            models.Index(fields=["token_hash"]),
            models.Index(fields=["user", "revoked_at", "expires_at"]),
        ]


class ExternalIdentity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="external_identities")
    provider = models.CharField(max_length=50)
    subject = models.CharField(max_length=191)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "orynth_external_identities"
        constraints = [
            models.UniqueConstraint(fields=["provider", "subject"], name="uniq_external_identity_provider_subject"),
        ]


class AuthEvent(models.Model):
    EVENT_CHOICES = (
        ("register", "Register"),
        ("login_success", "Login success"),
        ("login_failure", "Login failure"),
        ("logout", "Logout"),
        ("session_check", "Session check"),
        ("account_deletion_requested", "Account deletion requested"),
        ("password_reset_requested", "Password reset requested"),
        ("password_reset_confirmed", "Password reset confirmed"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES)
    email = models.EmailField(blank=True)
    provider = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orynth_auth_events"
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["email", "created_at"]),
        ]


class PasswordResetToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "orynth_password_reset_tokens"
        indexes = [
            models.Index(fields=["token_hash"]),
            models.Index(fields=["user", "used_at", "expires_at"]),
        ]


class UserProfile(models.Model):
    SEX_CHOICES = (
        ("male", "Masculino"),
        ("female", "Feminino"),
        ("other", "Outro"),
        ("prefer_not_to_say", "Prefiro não informar"),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=150)
    bio = models.TextField(blank=True)
    strong_category = models.CharField(max_length=80, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=32, blank=True, choices=SEX_CHOICES, default="")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orynth_user_profiles"


class UserReputation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reputation")
    reputation_score = models.PositiveIntegerField(default=100)
    resolved_predictions_count = models.PositiveIntegerField(default=0)
    accuracy_indicator = models.CharField(max_length=16, default="0%")
    streak = models.PositiveIntegerField(default=0)
    strong_category = models.CharField(max_length=80, blank=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orynth_user_reputations"
        indexes = [
            models.Index(fields=["-reputation_score", "last_updated_at"]),
        ]


class WalletLedgerEntry(models.Model):
    DIRECTION_CHOICES = (("credit", "Credit"), ("debit", "Debit"), ("lock", "Lock"), ("release", "Release"), ("settle", "Settle"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet_ledger")
    entry_type = models.CharField(max_length=40)
    amount = models.IntegerField()
    direction = models.CharField(max_length=16, choices=DIRECTION_CHOICES)
    description = models.CharField(max_length=255)
    reference_type = models.CharField(max_length=60, blank=True)
    reference_id = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_ledger_entries")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orynth_wallet_ledger"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["entry_type", "-created_at"]),
        ]


class WalletBalance(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet_balance")
    available_oc = models.IntegerField(default=0)
    locked_oc = models.IntegerField(default=0)
    total_earned_oc = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orynth_wallet_balances"


class WalletRechargeRequest(models.Model):
    STATUS_CHOICES = (("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet_recharge_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    amount_oc = models.PositiveIntegerField(null=True, blank=True)
    admin_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_wallet_recharge_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orynth_wallet_recharge_requests"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status="pending"),
                name="uniq_pending_wallet_recharge_user",
            ),
        ]


class UserBadge(models.Model):
    STATUS_CHOICES = (("earned", "Earned"), ("locked", "Locked"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    code = models.CharField(max_length=80)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="locked")
    earned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "orynth_user_badges"
        constraints = [
            models.UniqueConstraint(fields=["user", "code"], name="uniq_user_badge_code"),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]


class BadgeDefinition(models.Model):
    BADGE_TYPE_CHOICES = (
        ("global", "Global"),
        ("category", "Category"),
        ("performance", "Performance"),
        ("engagement", "Engagement"),
    )

    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255)
    rule_description = models.CharField(max_length=255, blank=True)
    badge_type = models.CharField(max_length=32, choices=BADGE_TYPE_CHOICES, default="global")
    image_url = models.CharField(max_length=255, blank=True)
    image_dark_url = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orynth_badge_definitions"
        ordering = ["name", "code"]
        indexes = [
            models.Index(fields=["is_active", "badge_type"]),
        ]


class BadgeRule(models.Model):
    RULE_TYPE_CHOICES = (
        ("founding_member", "Founding member"),
        ("resolved_predictions_count", "Resolved predictions count"),
        ("correct_predictions_count", "Correct predictions count"),
        ("streak_count", "Streak count"),
        ("ranking_position", "Ranking position"),
        ("comments_count", "Comments count"),
        ("approved_suggestions_count", "Approved suggestions count"),
        ("rewarded_feedback_count", "Rewarded feedback count"),
    )

    badge = models.OneToOneField(BadgeDefinition, on_delete=models.CASCADE, related_name="rule")
    rule_type = models.CharField(max_length=64, choices=RULE_TYPE_CHOICES)
    threshold_value = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    category = models.CharField(max_length=80, blank=True)
    subcategory = models.CharField(max_length=80, blank=True)
    event = models.CharField(max_length=80, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orynth_badge_rules"
        indexes = [
            models.Index(fields=["rule_type", "is_active"]),
        ]


class UserBadgeAward(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badge_awards")
    badge = models.ForeignKey(BadgeDefinition, on_delete=models.CASCADE, related_name="awards")
    awarded_at = models.DateTimeField()
    reason_snapshot = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "orynth_user_badge_awards"
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="uniq_user_badge_award"),
        ]
        indexes = [
            models.Index(fields=["user", "-awarded_at"]),
            models.Index(fields=["badge", "-awarded_at"]),
        ]


class UserActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=60)
    title = models.CharField(max_length=160)
    description = models.CharField(max_length=255, blank=True)
    reference_type = models.CharField(max_length=60, blank=True)
    reference_id = models.CharField(max_length=120, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orynth_user_activities"
        indexes = [
            models.Index(fields=["user", "-occurred_at"]),
        ]
