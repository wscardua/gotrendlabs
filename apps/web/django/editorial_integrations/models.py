import uuid
from django.conf import settings
from django.db import models


class Integration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=1000, default="")
    responsible = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    state = models.CharField(
        max_length=16,
        default="paused",
        choices=[(s, s) for s in ("active", "paused", "revoked")],
    )
    expires_at = models.DateTimeField()
    scopes = models.JSONField(default=list)
    drafts_per_day = models.PositiveIntegerField(default=5)
    calls_per_minute = models.PositiveIntegerField(default=60)
    concurrent_calls = models.PositiveIntegerField(default=2)
    revision = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "gotrendlabs_agent_integrations"
        indexes = [models.Index(fields=["state", "expires_at"])]


class Credential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.PROTECT)
    secret_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)
    last_used_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "gotrendlabs_agent_credentials"


class OAuthClient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    redirect_uris = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_agent_oauth_clients"


class Grant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.PROTECT)
    client = models.ForeignKey(OAuthClient, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    scopes = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_agent_grants"


class Token(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_hash = models.CharField(max_length=64, unique=True)
    integration = models.ForeignKey(Integration, on_delete=models.PROTECT)
    credential = models.ForeignKey(Credential, on_delete=models.PROTECT, null=True)
    grant = models.ForeignKey(Grant, on_delete=models.PROTECT, null=True)
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True)
    kind = models.CharField(max_length=16)
    issuer = models.CharField(max_length=255)
    audience = models.CharField(max_length=255)
    scopes = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "gotrendlabs_agent_tokens"
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(credential__isnull=False, grant__isnull=True)
                    | models.Q(credential__isnull=True, grant__isnull=False)
                ),
                name="agent_token_origin",
            )
        ]


class Idempotency(models.Model):
    integration = models.ForeignKey(Integration, on_delete=models.PROTECT)
    operation = models.CharField(max_length=100)
    key = models.CharField(max_length=100)
    payload_hash = models.CharField(max_length=64)
    response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_agent_idempotency"
        constraints = [
            models.UniqueConstraint(
                fields=["integration", "operation", "key"],
                name="agent_idempotency_unique",
            )
        ]


class Quota(models.Model):
    integration = models.ForeignKey(Integration, on_delete=models.PROTECT, null=True)
    bucket = models.CharField(max_length=150, unique=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "gotrendlabs_agent_quotas"


class Lease(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.PROTECT)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "gotrendlabs_agent_leases"


class EditorialDraft(models.Model):
    market = models.OneToOneField(
        "markets.Market", on_delete=models.PROTECT, primary_key=True
    )
    integration = models.ForeignKey(Integration, on_delete=models.PROTECT, null=True, blank=True)
    revision = models.PositiveIntegerField(default=1)
    state = models.CharField(max_length=16, default="preparation")
    record = models.JSONField(default=dict)
    snapshot_hash = models.CharField(max_length=64)
    decision = models.JSONField(default=dict)

    class Meta:
        db_table = "gotrendlabs_agent_editorial_drafts"
        indexes = [models.Index(fields=["state", "market"])]


class EditorialRevision(models.Model):
    draft = models.ForeignKey(EditorialDraft, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    snapshot = models.JSONField()
    snapshot_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_agent_editorial_revisions"
        constraints = [
            models.UniqueConstraint(
                fields=["draft", "revision"], name="agent_editorial_revision_unique"
            )
        ]


class IngestedEvent(models.Model):
    id = models.UUIDField(primary_key=True)
    integration = models.ForeignKey(Integration, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gotrendlabs_agent_ingested_events"
