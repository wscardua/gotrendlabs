"""Restricted editorial contract shared by REST and MCP; no administrative payloads."""

from datetime import datetime
from uuid import UUID
from typing import Literal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCOPES = (
    "editorial:read",
    "catalog:read",
    "metrics:read",
    "drafts:write",
    "drafts:submit",
)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ResponsibleOption(Strict):
    id: int
    display_name: str
    username: str


class ResponsibleOptions(Strict):
    items: list[ResponsibleOption]
    has_more: bool
    next_cursor: int | None


class IntegrationConfig(Strict):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    responsible_id: int = Field(gt=0)
    expires_at: datetime
    scopes: list[
        Literal[
            "editorial:read",
            "catalog:read",
            "metrics:read",
            "drafts:write",
            "drafts:submit",
        ]
    ] = Field(default_factory=list, max_length=5)
    drafts_per_day: int = Field(default=5, ge=0, le=1000)
    calls_per_minute: int = Field(default=60, ge=0, le=10000)
    concurrent_calls: int = Field(default=2, ge=1, le=20)
    expected_revision: int | None = Field(default=None, ge=1)

    @field_validator("expires_at")
    @classmethod
    def aware(cls, v):
        if not v.tzinfo:
            raise ValueError("offset required")
        return v


class RevisionAction(Strict):
    expected_revision: int = Field(ge=1)


class Transfer(RevisionAction):
    responsible_id: int = Field(gt=0)


class EditorialRecord(Strict):
    policy_version: str = Field(max_length=20)
    policy_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    document: str = Field(
        min_length=1, max_length=60000,
        description="Ficha editorial única: contexto e duplicidade; pergunta, regras e prazos; fontes e evidências com URL e data; contingências, responsável, pendências e conclusão. Relato do agente não é verificação humana.",
    )


class Option(Strict):
    label: str = Field(min_length=1, max_length=80)
    hint: str = Field(default="", max_length=160)


class Draft(Strict):
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(min_length=1, max_length=5000)
    kind: Literal["binary", "multiple"]
    category_id: int = Field(gt=0)
    subcategory_id: int = Field(gt=0)
    event_id: int = Field(gt=0)
    options: list[Option] = Field(default_factory=list, max_length=20)
    source: str = Field(min_length=1, max_length=180)
    resolution_criteria: str = Field(min_length=1, max_length=5000)
    close_at: datetime
    close_timezone: str = Field(max_length=64)
    editorial_record: EditorialRecord

    @model_validator(mode="after")
    def dates(self):
        if not self.close_at.tzinfo:
            raise ValueError("close offset required")
        try:
            zone = ZoneInfo(self.close_timezone)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("invalid timezone")
        if self.close_at.utcoffset() != self.close_at.astimezone(zone).utcoffset():
            raise ValueError("offset inconsistent with timezone")
        return self


class CreateDraft(Draft):
    idempotency_key: str = Field(
        min_length=8, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$"
    )


class UpdateDraft(CreateDraft):
    expected_revision: int = Field(ge=1)


class SubmitDraft(RevisionAction):
    idempotency_key: str = Field(
        min_length=8, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$"
    )


class ReviewDecision(RevisionAction):
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approved", "returned", "rejected"]
    confirmed: bool = False


class HumanEditorialAssessment(ReviewDecision):
    editorial_record: EditorialRecord


class OAuthRegistration(Strict):
    # RFC 7591 section 2: unrecognized client metadata must be ignored.
    # This exception applies only to registration, never domain/admin payloads.
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    scope: str | None = Field(default=None, max_length=200)
    client_name: str = Field(default="MCP client", min_length=1, max_length=120)
    redirect_uris: list[str] = Field(min_length=1, max_length=10)
    token_endpoint_auth_method: Literal["none"] = "none"
    grant_types: list[Literal["authorization_code", "refresh_token"]] = [
        "authorization_code",
        "refresh_token",
    ]
    response_types: list[Literal["code"]] = ["code"]

    @field_validator("redirect_uris")
    @classmethod
    def redirects(cls, vs):
        for v in vs:
            u = urlsplit(v)
            if (
                len(v) > 1000
                or u.fragment
                or u.username
                or u.password
                or not u.hostname
                or (
                    u.scheme != "https"
                    and not (
                        u.scheme == "http"
                        and u.hostname in ("127.0.0.1", "localhost", "::1")
                    )
                )
            ):
                raise ValueError("HTTPS or loopback redirect required")
        return vs


class Delegation(Strict):
    access_token: str = Field(min_length=20, max_length=200)


class ToolEvent(Strict):
    event_id: str = Field(
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    tool: Literal[
        "get_editorial_policy",
        "get_taxonomy",
        "search_markets",
        "get_market",
        "get_editorial_signals",
        "validate_market_draft",
        "create_market_draft",
        "update_market_draft",
        "submit_draft_for_review",
        "get_draft_review",
    ]
    execution_id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,100}$")
    result: Literal["started", "completed", "failed", "denied"]


class Criterion(BaseModel):
    id: str
    question: str
    evidence: str
    publication_blocking: bool
    source_access_required: bool
    manual_section: str


class PolicyResponse(BaseModel):
    version: str
    status: Literal["approved"]
    hash: str
    approved_on: str
    source: str
    criteria: list[Criterion]
    manual: str
    checklist: str
    checklist_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    record_template: str
    record_template_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    as_of: datetime


class TaxonomyItem(BaseModel):
    category_id: int
    category: str
    subcategory_id: int
    subcategory: str
    event_id: int
    event: str


class TaxonomyResponse(BaseModel):
    items: list[TaxonomyItem]
    next_cursor: str | None
    has_more: bool
    coverage: str
    as_of: datetime


class SearchItem(BaseModel):
    id: int
    slug: str
    title: str
    summary: str
    kind: str
    status: str
    category_id: int
    subcategory_id: int
    event_id: int | None
    close_at: datetime | None
    close_timezone: str


class SearchResponse(BaseModel):
    items: list[SearchItem]
    next_cursor: str | None
    has_more: bool
    coverage: str
    as_of: datetime


class PrivateEditorial(BaseModel):
    revision: int
    state: str
    record: EditorialRecord
    snapshot_hash: str
    decision: dict


class MarketProjection(SearchItem):
    source: str
    resolution_criteria: str
    options: list[Option]
    editorial: PrivateEditorial | None = None


class SignalsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    as_of: datetime
    timezone: str
    unit: str
    availability: str
    humans: int | None
    bots: int | None
    analytics: dict


class ValidationResponse(BaseModel):
    structurally_valid: bool
    pending: list[str]
    evidence_origin: Literal["agent_reported"]
    similar: SearchResponse


class MutationResponse(BaseModel):
    market_id: int
    slug: str
    market_status: str
    editorial_status: str
    revision: int
    snapshot_hash: str
    policy_version: str
    admin_url: str
    request_id: str
    replayed: bool


class ReviewResponse(PrivateEditorial):
    market_id: int
    integration_id: UUID
