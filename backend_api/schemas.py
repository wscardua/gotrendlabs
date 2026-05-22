from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterPayload(BaseModel):
    display_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    language: str = "pt-br"
    password: str = Field(min_length=8, max_length=128)
    terms_accepted: bool = False
    recaptcha_token: str = ""


class LoginPayload(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class PasswordResetRequestPayload(BaseModel):
    email: EmailStr


class PasswordResetRequestResponse(BaseModel):
    message: str
    reset_url: str = ""


class PasswordResetConfirmPayload(BaseModel):
    token: str = Field(min_length=20, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class PasswordResetConfirmResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    id: int
    handle: str
    email: str
    display_name: str
    preferred_language: str
    created_at: str
    last_login: Optional[str] = None
    account_status: str
    is_staff: bool = False


class PublicUserResponse(BaseModel):
    id: int
    handle: str
    display_name: str


class SessionResponse(BaseModel):
    token: str
    expires_at: str


class AuthResponse(BaseModel):
    user: UserResponse
    session: SessionResponse


class SessionContextResponse(BaseModel):
    user: UserResponse
    authenticated: bool = True


class ProfileUpdatePayload(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    handle: Optional[str] = Field(default=None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    preferred_language: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("birth_date", mode="before")
    @classmethod
    def empty_birth_date_as_none(cls, value):
        return None if value == "" else value


class ReputationResponse(BaseModel):
    reputation_score: int
    ranking_position: int
    resolved_predictions_count: int
    accuracy_indicator: str
    streak: int
    strong_category: str
    last_updated_at: str


class UserProfileResponse(BaseModel):
    user: UserResponse
    profile_id: int
    bio: str
    strong_category: str
    birth_date: Optional[str] = None
    sex: str = ""
    profile_created_at: str
    profile_updated_at: str
    is_public: bool
    reputation: ReputationResponse


class PublicUserProfileResponse(BaseModel):
    user: PublicUserResponse
    bio: str
    strong_category: str
    is_public: bool
    reputation: ReputationResponse


class WalletResponse(BaseModel):
    available_oc: int
    locked_oc: int
    total_earned_oc: int


class LedgerEntryResponse(BaseModel):
    entry_id: int
    entry_type: str
    amount: int
    direction: str
    description: str
    reference_type: str
    reference_id: str
    created_at: str
    created_by: Optional[int] = None


class LedgerResponse(BaseModel):
    wallet: WalletResponse
    entries: List[LedgerEntryResponse]


class WalletRechargeRequestResponse(BaseModel):
    id: int
    status: str
    status_label: str
    amount_oc: Optional[int] = None
    admin_note: str = ""
    created_at: str
    created_at_label: str = ""
    reviewed_at: Optional[str] = None


class WalletRechargeRequestListResponse(BaseModel):
    requests: List[WalletRechargeRequestResponse]


class AdminUserResponse(BaseModel):
    id: int
    handle: str
    email: str
    display_name: str
    preferred_language: str
    account_status: str
    is_active: bool
    is_staff: bool
    is_superuser: bool
    is_bot: bool = False
    created_at: str
    last_login: Optional[str] = None
    deactivated_at: Optional[str] = None
    available_oc: int = 0
    locked_oc: int = 0
    reputation_score: int = 0


class AdminUserListResponse(BaseModel):
    users: List[AdminUserResponse]
    counts: dict


class AdminUserDetailResponse(BaseModel):
    user: AdminUserResponse
    profile: dict
    wallet: WalletResponse
    ledger: List[LedgerEntryResponse]
    reputation: ReputationResponse
    prediction_counts: dict
    predictions: List[dict]
    comment_counts: dict
    comments: List[dict]
    badges: List[dict]
    suggestions: List[dict]
    feedback: List[dict]
    sessions: List[dict]
    auth_events: List[dict]
    admin_events: List[dict]


class AdminUserWalletAdjustmentPayload(BaseModel):
    direction: str
    amount_oc: int = Field(gt=0, le=1000000)
    note: str = Field(min_length=1, max_length=2000)


class AdminUserRolePayload(BaseModel):
    is_staff: bool = False
    is_superuser: bool = False
    note: str = Field(min_length=1, max_length=2000)


class AdminUserBotPayload(BaseModel):
    is_bot: bool = False
    note: str = Field(min_length=1, max_length=2000)


class SystemLogResponse(BaseModel):
    id: int
    created_at: str
    expires_at: str
    level: str
    source: str
    logger_name: str = ""
    event_type: str
    message: str
    request_id: str = ""
    method: str = ""
    path: str = ""
    status_code: Optional[int] = None
    duration_ms: Optional[int] = None
    user_id: Optional[int] = None
    user_identifier: str = ""
    ip_address: str = ""
    user_agent: str = ""
    exception_type: str = ""
    stack_trace: str = ""
    context: dict[str, Any] = Field(default_factory=dict)


class SystemLogListResponse(BaseModel):
    logs: List[SystemLogResponse]
    counts: dict
    page: int
    page_size: int
    total: int


class AdminDashboardSummaryResponse(BaseModel):
    markets: dict
    queues: dict
    users: dict
    engagement: dict
    wallet: dict
    badges: dict
    system: dict
    top_markets: List[dict]
    recent_admin_events: List[dict]


class BadgeResponse(BaseModel):
    code: str
    name: str
    description: str
    rule_description: str = ""
    badge_type: str = "global"
    image_url: str = ""
    image_dark_url: str = ""
    status: str
    earned_at: Optional[str] = None
    reason_snapshot: str = ""


class BadgeListResponse(BaseModel):
    badges: List[BadgeResponse]


class AdminBadgePayload(BaseModel):
    code: Optional[str] = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=255)
    rule_description: str = Field(default="", max_length=255)
    badge_type: str = "global"
    image_url: str = Field(default="", max_length=255)
    image_dark_url: str = Field(default="", max_length=255)
    is_active: bool = True
    rule_type: str
    threshold_value: float = Field(default=1, ge=0)
    category: str = Field(default="", max_length=80)
    subcategory: str = Field(default="", max_length=80)
    event: str = Field(default="", max_length=80)


class AdminBadgeResponse(BaseModel):
    code: str
    name: str
    description: str
    rule_description: str
    badge_type: str
    image_url: str
    image_dark_url: str
    is_active: bool
    rule_type: str
    threshold_value: float
    category: str
    subcategory: str
    event: str
    rule_active: bool
    awards_count: int = 0
    created_at: str
    updated_at: str


class AdminBadgeListResponse(BaseModel):
    badges: List[AdminBadgeResponse]


class ActivityResponse(BaseModel):
    activity_type: str
    title: str
    description: str
    reference_type: str
    reference_id: str
    occurred_at: str


class MarketOptionResponse(BaseModel):
    id: int
    label: str
    probability: int
    probability_exact: float = 0
    hint: str
    sparkline_path: str = ""


class CommentResponse(BaseModel):
    id: int
    market_slug: str
    author_id: int
    author_handle: str
    author_display_name: str
    body: str
    status: str
    like_count: int = 0
    dislike_count: int = 0
    viewer_reaction: Optional[str] = None
    moderation_note: str = ""
    moderated_by: Optional[int] = None
    moderated_at: Optional[str] = None
    created_at: str
    created_at_label: str = ""


class CommentListResponse(BaseModel):
    comments: List[CommentResponse]


class MarketResponse(BaseModel):
    slug: str
    title: str
    category: str
    category_notice: str = ""
    subcategory: str
    subcategory_notice: str = ""
    event: str
    event_notice: str = ""
    kind: str
    status: str
    status_label: str
    primary_outcome: str
    primary_probability: int
    primary_probability_exact: float = 0
    secondary_probability: int
    secondary_probability_exact: float = 0
    volume_oc: str
    participants: str
    source: str
    closes_in: str
    close_label: str
    thumb: str
    thumb_color: str
    image_url: str = ""
    summary: str
    resolution_criteria: str
    close_at: Optional[str] = None
    close_timezone: str = ""
    auto_close_enabled: bool = True
    is_featured: bool = False
    resolved_at: Optional[str] = None
    resolved_at_label: str = ""
    resolution_timezone: str = ""
    winning_option_id: Optional[int] = None
    resolution_note: str = ""
    resolution_type: str = ""
    market_like_count: int = 0
    view_count: int = 0
    share_count: int = 0
    viewer_has_prediction: bool = False
    viewer_has_favorite: bool = False
    viewer_has_like: bool = False
    created_at: str = ""
    sparkline_path: str = ""
    sparkline_area_path: str = ""
    sparkline_series: List[dict] = Field(default_factory=list)
    options: List[MarketOptionResponse]
    comments: List[CommentResponse] = Field(default_factory=list)


class MarketListResponse(BaseModel):
    markets: List[MarketResponse]


class PredictionCreatePayload(BaseModel):
    option_id: int
    stake_amount: int = Field(gt=0)
    client_locale: str = "pt-br"


class PredictionCreateResponse(BaseModel):
    prediction_id: int
    market_id: int
    option_id: int
    stake_amount: int
    accepted_at: str
    wallet_balance_after: WalletResponse
    market_probability_snapshot: List[MarketOptionResponse]
    potential_payout: int


class PredictionPreviewResponse(BaseModel):
    market_id: int
    option_id: int
    stake_amount: int
    probability_exact: float
    estimated_return: int


class CommentCreatePayload(BaseModel):
    body: str = Field(min_length=1, max_length=1000)
    client_locale: str = "pt-br"


class CommentModerationPayload(BaseModel):
    status: str
    note: str = Field(default="", max_length=2000)


class AdminMarketOptionPayload(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    probability_exact: float = Field(default=0, ge=0, le=100)
    hint: str = Field(default="", max_length=160)


class AdminMarketPayload(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    slug: Optional[str] = Field(default=None, max_length=160)
    summary: str = ""
    kind: str = "binary"
    category: str = Field(min_length=1, max_length=80)
    subcategory: str = Field(min_length=1, max_length=80)
    event: str = Field(default="Geral", max_length=80)
    status_label: str = ""
    primary_outcome: str = ""
    primary_probability_exact: float = Field(default=0, ge=0, le=100)
    secondary_probability_exact: float = Field(default=0, ge=0, le=100)
    volume_oc: str = ""
    participants: str = ""
    source: str = ""
    closes_in: str = ""
    close_label: str = ""
    thumb: str = ""
    thumb_color: str = ""
    image_url: str = ""
    resolution_criteria: str = ""
    close_at: Optional[datetime] = None
    close_timezone: str = "America/Sao_Paulo"
    auto_close_enabled: bool = True
    is_featured: bool = False
    resolution_type: str = ""
    resolution_note: str = ""
    admin_notes: str = ""
    options: List[AdminMarketOptionPayload] = Field(default_factory=list)


class AdminMarketActionPayload(BaseModel):
    note: str = ""


class AdminMarketResolvePayload(BaseModel):
    winning_option_id: int
    source_url: str = Field(default="", max_length=500)
    note: str = Field(default="", max_length=2000)
    resolved_at: Optional[datetime] = None
    resolution_timezone: str = Field(default="", max_length=64)


class AdminMarketResolutionAuditMarketResponse(BaseModel):
    slug: str
    title: str
    status: str
    winning_option_id: Optional[int] = None
    winning_option_label: str = ""
    resolved_at: Optional[str] = None
    resolved_at_label: str = ""
    resolution_timezone: str = ""
    resolution_note: str = ""
    source: str = ""


class AdminMarketResolutionAuditSummaryResponse(BaseModel):
    predictions_total: int = 0
    winners_total: int = 0
    losers_total: int = 0
    stake_total: int = 0
    refund_total: int = 0
    payout_total: int = 0
    loss_total: int = 0
    badge_awards_total: int = 0


class AdminMarketResolutionAuditBadgeResponse(BaseModel):
    code: str
    name: str
    awarded_at: str
    reason_snapshot: str = ""


class AdminMarketResolutionAuditParticipantResponse(BaseModel):
    user_id: int
    handle: str
    display_name: str
    prediction_id: int
    option_label: str
    stake_amount: int
    probability_at_entry: float
    potential_payout: int
    won: Optional[bool] = None
    ledger: dict
    badges: List[AdminMarketResolutionAuditBadgeResponse] = Field(default_factory=list)


class AdminMarketResolutionAuditPaginationResponse(BaseModel):
    limit: int
    offset: int
    total: int


class AdminMarketResolutionAuditResponse(BaseModel):
    market: AdminMarketResolutionAuditMarketResponse
    summary: AdminMarketResolutionAuditSummaryResponse
    participants: List[AdminMarketResolutionAuditParticipantResponse]
    pagination: AdminMarketResolutionAuditPaginationResponse


class MarketSuggestionPayload(BaseModel):
    guest_name: str = Field(default="", max_length=150)
    guest_email: Optional[EmailStr] = None
    question: str = Field(min_length=1, max_length=240)
    category: str = Field(min_length=1, max_length=80)
    subcategory: str = Field(default="", max_length=80)
    kind: str = "binary"
    suggested_source: str = Field(min_length=1, max_length=180)
    rationale: str = Field(default="", max_length=2000)
    recaptcha_token: str = ""


class ProductFeedbackPayload(BaseModel):
    guest_name: str = Field(default="", max_length=150)
    guest_email: Optional[EmailStr] = None
    feedback_type: str = Field(min_length=1, max_length=80)
    severity: str = "medium"
    description: str = Field(min_length=1, max_length=2000)
    recaptcha_token: str = ""


class QueueReviewPayload(BaseModel):
    status: str
    note: str = ""


class FeedbackRewardPayload(BaseModel):
    amount_oc: int = Field(gt=0, le=10000)
    note: str = ""


class SuggestionRewardPayload(BaseModel):
    amount_oc: int = Field(gt=0, le=10000)
    note: str = ""


class WalletRechargeApprovalPayload(BaseModel):
    amount_oc: int = Field(gt=0, le=10000)
    note: str = ""


class WalletRechargeRejectPayload(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


class QueueItemResponse(BaseModel):
    id: int
    kind: str
    title: str
    category: str = ""
    queue_label: str
    item_type: str = ""
    status: str
    status_label: str
    severity: str = ""
    severity_label: str = ""
    owner_label: str
    age_label: str
    author_handle: Optional[str] = None
    author_id: Optional[int] = None
    guest_name: str = ""
    guest_email: str = ""
    source: str = ""
    description: str = ""
    admin_note: str = ""
    reward_oc: Optional[int] = None
    converted_market_slug: Optional[str] = None
    created_at: str
    created_at_label: str = ""
    reviewed_at: Optional[str] = None


class QueueListResponse(BaseModel):
    items: List[QueueItemResponse]
    counts: dict


class AdminMarketListResponse(BaseModel):
    markets: List[MarketResponse]
    counts: dict


class AdminEventResponse(BaseModel):
    name: str
    slug: str
    notice: str = ""
    markets_count: int
    is_blocked: bool = False
    blocked_reason: str = ""
    blocked_at: Optional[str] = None


class AdminSubcategoryResponse(BaseModel):
    name: str
    slug: str
    notice: str = ""
    markets_count: int
    is_blocked: bool = False
    blocked_reason: str = ""
    blocked_at: Optional[str] = None
    events: List[AdminEventResponse] = Field(default_factory=list)


class AdminCategoryResponse(BaseModel):
    name: str
    slug: str
    notice: str = ""
    markets_count: int
    is_blocked: bool = False
    blocked_reason: str = ""
    blocked_at: Optional[str] = None
    subcategories: List[AdminSubcategoryResponse]


class AdminTaxonomyResponse(BaseModel):
    categories: List[AdminCategoryResponse]


class AdminCategoryPayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: Optional[str] = Field(default=None, max_length=100)
    notice: str = Field(default="", max_length=500)


class AdminSubcategoryPayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: Optional[str] = Field(default=None, max_length=100)
    notice: str = Field(default="", max_length=500)


class AdminEventPayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: Optional[str] = Field(default=None, max_length=100)
    notice: str = Field(default="", max_length=500)


class RankingRowResponse(BaseModel):
    position: int
    user_id: int
    handle: str
    display_name: str
    reputation_score: int
    accuracy_indicator: str
    strong_category: str


class RankingSubcategoryResponse(BaseModel):
    name: str
    slug: str


class RankingCategoryResponse(BaseModel):
    name: str
    slug: str
    subcategories: List[RankingSubcategoryResponse]


class RankingResponse(BaseModel):
    rows: List[RankingRowResponse]
    categories: List[RankingCategoryResponse] = Field(default_factory=list)
    selected_category: str = ""
    selected_subcategory: str = ""
