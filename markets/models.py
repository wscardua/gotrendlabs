from django.conf import settings
from django.db import models


class MarketCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    notice = models.TextField(blank=True, default="")
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(null=True, blank=True)
    blocked_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_market_categories"
        ordering = ["name"]


class MarketSubcategory(models.Model):
    category = models.ForeignKey(MarketCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=100)
    notice = models.TextField(blank=True, default="")
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(null=True, blank=True)
    blocked_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_market_subcategories"
        ordering = ["category__name", "name"]
        constraints = [
            models.UniqueConstraint(fields=["category", "slug"], name="uniq_market_subcategory_category_slug"),
        ]


class MarketEvent(models.Model):
    subcategory = models.ForeignKey(MarketSubcategory, on_delete=models.CASCADE, related_name="events")
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=100)
    notice = models.TextField(blank=True, default="")
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(null=True, blank=True)
    blocked_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_market_events"
        ordering = ["subcategory__category__name", "subcategory__name", "name"]
        constraints = [
            models.UniqueConstraint(fields=["subcategory", "slug"], name="uniq_market_event_subcategory_slug"),
        ]


class Market(models.Model):
    KIND_CHOICES = (("binary", "Binary"), ("multiple", "Multiple"))
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("open", "Open"),
        ("locked", "Locked"),
        ("resolved", "Resolved"),
        ("canceled", "Canceled"),
    )

    category = models.ForeignKey(MarketCategory, on_delete=models.PROTECT, related_name="markets")
    subcategory = models.ForeignKey(MarketSubcategory, on_delete=models.PROTECT, related_name="markets")
    event = models.ForeignKey(MarketEvent, on_delete=models.PROTECT, null=True, blank=True, related_name="markets")
    slug = models.SlugField(max_length=160, unique=True)
    title = models.CharField(max_length=240)
    summary = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    status_label = models.CharField(max_length=80)
    primary_outcome = models.CharField(max_length=80)
    primary_probability_exact = models.DecimalField(max_digits=7, decimal_places=4, default=0)
    secondary_probability_exact = models.DecimalField(max_digits=7, decimal_places=4, default=0)
    volume_gtl = models.CharField(max_length=80, blank=True)
    participants = models.CharField(max_length=80, blank=True)
    source = models.CharField(max_length=180, blank=True)
    closes_in = models.CharField(max_length=40, blank=True)
    close_label = models.CharField(max_length=120, blank=True)
    thumb = models.CharField(max_length=12, blank=True)
    thumb_color = models.CharField(max_length=20, blank=True)
    image_url = models.CharField(max_length=255, blank=True)
    resolution_criteria = models.TextField(blank=True)
    resolution_type = models.CharField(max_length=40, blank=True)
    close_at = models.DateTimeField(null=True, blank=True)
    close_timezone = models.CharField(max_length=64, blank=True)
    auto_close_enabled = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    view_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_timezone = models.CharField(max_length=64, blank=True, default="")
    canceled_at = models.DateTimeField(null=True, blank=True)
    winning_option = models.ForeignKey(
        "MarketOption",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="winning_markets",
    )
    resolution_note = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_markets",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_markets",
    )
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_markets"
        ordering = ["display_order", "id"]
        indexes = [
            models.Index(fields=["status", "display_order"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["subcategory", "status"]),
            models.Index(fields=["event", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.event_id and self.subcategory_id:
            self.event, _ = MarketEvent.objects.get_or_create(
                subcategory_id=self.subcategory_id,
                slug="geral",
                defaults={"name": "Geral", "is_blocked": False, "blocked_reason": ""},
            )
        super().save(*args, **kwargs)


class MarketOption(models.Model):
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=80)
    probability_exact = models.DecimalField(max_digits=7, decimal_places=4, default=0)
    hint = models.CharField(max_length=160, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_market_options"
        ordering = ["display_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["market", "label"], name="uniq_market_option_market_label"),
        ]


class Prediction(models.Model):
    STATUS_CHOICES = (
        ("open", "Open"),
        ("resolved", "Resolved"),
        ("canceled", "Canceled"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="predictions")
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="predictions")
    market_option = models.ForeignKey(MarketOption, on_delete=models.PROTECT, related_name="predictions")
    stake_amount = models.PositiveIntegerField()
    probability_at_entry = models.DecimalField(max_digits=7, decimal_places=4)
    weight_at_entry = models.PositiveBigIntegerField()
    potential_payout = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open", db_index=True)
    won = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_predictions"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["market", "-created_at"]),
            models.Index(fields=["market_option"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["user", "market"], name="uniq_prediction_user_market"),
        ]


class MarketFavorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="market_favorites")
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_market_favorites"
        indexes = [
            models.Index(fields=["user", "-created_at"], name="gtl_fav_user_8f6c74_idx"),
            models.Index(fields=["market"], name="gtl_fav_mkt_0f7d22_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["user", "market"], name="uniq_market_favorite_user_market"),
        ]


class MarketLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="market_likes")
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_market_likes"
        indexes = [
            models.Index(fields=["user", "-created_at"], name="gtl_like_user_7d3f2a_idx"),
            models.Index(fields=["market"], name="gtl_like_mkt_6b8a91_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["user", "market"], name="uniq_market_like_user_market"),
        ]


class MarketComment(models.Model):
    STATUS_CHOICES = (("visible", "Visible"), ("hidden", "Hidden"))

    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="market_comments")
    body = models.TextField(max_length=1000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="visible", db_index=True)
    moderation_note = models.TextField(blank=True)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_market_comments",
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_market_comments"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["market", "status", "-created_at"], name="gtl_mark_mkt_f9e441_idx"),
            models.Index(fields=["author", "-created_at"], name="gtl_mark_auth_e373b2_idx"),
            models.Index(fields=["status", "-created_at"], name="gtl_mark_stat_1e4f0e_idx"),
        ]


class CommentReaction(models.Model):
    REACTION_CHOICES = (("like", "Like"), ("dislike", "Dislike"))

    comment = models.ForeignKey(MarketComment, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_reactions")
    reaction = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_comment_reactions"
        indexes = [
            models.Index(fields=["comment", "reaction"], name="gtl_comm_cmt_e86827_idx"),
            models.Index(fields=["user", "-created_at"], name="gtl_comm_user_53c6e6_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["comment", "user"], name="uniq_comment_reaction_comment_user"),
        ]


class UserNotification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
    )
    market = models.ForeignKey(Market, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    comment = models.ForeignKey(MarketComment, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    event_type = models.CharField(max_length=40)
    source_key = models.CharField(max_length=160)
    title = models.CharField(max_length=160)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_user_notifications"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"], name="gtl_notif_rec_7f17_idx"),
            models.Index(fields=["market", "-created_at"], name="gtl_notif_mkt_74d6_idx"),
            models.Index(fields=["comment", "-created_at"], name="gtl_notif_cmt_6c58_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["recipient", "source_key"], name="uniq_notification_recipient_source"),
        ]


class AdminEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_events")
    action = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=80)
    entity_identifier = models.CharField(max_length=160)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_admin_events"
        indexes = [
            models.Index(fields=["entity_type", "entity_identifier", "-created_at"]),
            models.Index(fields=["actor", "-created_at"]),
        ]


class MarketSuggestion(models.Model):
    STATUS_CHOICES = (("pending", "Pending"), ("reviewed", "Reviewed"), ("converted", "Converted"), ("rewarded", "Rewarded"), ("rejected", "Rejected"))
    KIND_CHOICES = (("binary", "Binary"), ("multiple", "Multiple"))

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="market_suggestions")
    guest_name = models.CharField(max_length=150, blank=True)
    guest_email = models.EmailField(blank=True)
    question = models.CharField(max_length=240)
    category = models.CharField(max_length=80)
    subcategory = models.CharField(max_length=80, blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="binary")
    suggested_source = models.CharField(max_length=180)
    rationale = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    admin_note = models.TextField(blank=True)
    reward_gtl = models.PositiveIntegerField(null=True, blank=True)
    converted_market = models.ForeignKey(Market, on_delete=models.SET_NULL, null=True, blank=True, related_name="source_suggestions")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_suggestions")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rewarded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_market_suggestions"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]


class ProductFeedback(models.Model):
    STATUS_CHOICES = (("pending", "Pending"), ("reviewed", "Reviewed"), ("rewarded", "Rewarded"), ("rejected", "Rejected"))
    SEVERITY_CHOICES = (("low", "Low"), ("medium", "Medium"), ("high", "High"))

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="product_feedback")
    guest_name = models.CharField(max_length=150, blank=True)
    guest_email = models.EmailField(blank=True)
    feedback_type = models.CharField(max_length=80)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium", db_index=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    admin_note = models.TextField(blank=True)
    reward_gtl = models.PositiveIntegerField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_feedback")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rewarded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gotrendlabs_product_feedback"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["severity", "status"]),
            models.Index(fields=["author", "-created_at"]),
        ]
