from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from accounts import views as account_views
from admin_ops import views as admin_ops_views
from core import views as core_views
from markets import views as market_views
from profiles import views as profile_views
from wallet import views as wallet_views

urlpatterns = [
    path("", core_views.home, name="home"),
    path("maintenance/", core_views.maintenance, name="maintenance"),
    path("concepts/", core_views.concepts, name="concepts"),
    path("categories/", core_views.categories, name="categories"),
    path("security/", core_views.security, name="security"),
    path("use-policy/", core_views.use_policy, name="use-policy"),
    path("suggestion/", core_views.suggestion, name="suggestion"),
    path("feedback/", core_views.feedback, name="feedback"),
    path("notifications/read-all/", core_views.notifications_read_all, name="notifications-read-all"),
    path("badges/", core_views.badges, name="badges"),
    path("share/badge/<slug:code>/image/", core_views.share_badge_image, name="share-badge-image"),
    path("share/badge/<slug:code>/", core_views.share_badge, name="share-badge"),
    path("share/market/<slug:slug>/track/", core_views.share_market_track, name="share-market-track"),
    path("share/market/<slug:slug>/image/", core_views.share_market_image, name="share-market-image"),
    path("share/market/<slug:slug>/", core_views.share_market, name="share-market"),
    path("share/result/<slug:slug>/image/", core_views.share_result_image, name="share-result-image"),
    path("share/result/<slug:slug>/", core_views.share_result, name="share-result"),
    path("markets/<slug:slug>/", market_views.detail, name="market-detail"),
    path("markets/<slug:slug>/predict/", market_views.prediction_preview, name="prediction-preview"),
    path("markets/<slug:slug>/predict/confirm/", market_views.confirm_prediction, name="prediction-confirm"),
    path("markets/<slug:slug>/comments/", market_views.submit_comment, name="comment-submit"),
    path("markets/<slug:slug>/comments/<int:comment_id>/reaction/", market_views.comment_reaction, name="comment-reaction"),
    path("markets/<slug:slug>/favorite/", market_views.favorite_toggle, name="market-favorite-toggle"),
    path("markets/<slug:slug>/like/", market_views.like_toggle, name="market-like-toggle"),
    path("login/", account_views.login_view, name="login"),
    path("register/", account_views.register_view, name="register"),
    path("password-reset/", account_views.password_reset_request_view, name="password-reset"),
    path("password-reset/confirm/<str:token>/", account_views.password_reset_confirm_view, name="password-reset-confirm"),
    path("logout/", account_views.logout_view, name="logout"),
    path("wallet/", wallet_views.wallet_home, name="wallet"),
    path("wallet/recharge-request/", wallet_views.request_recharge, name="wallet-recharge-request"),
    path("profile/", profile_views.profile, name="profile"),
    path("rankings/", profile_views.rankings, name="rankings"),
    path("admin-ops/", admin_ops_views.dashboard, name="admin-ops-dashboard"),
    path("admin-ops/config/", admin_ops_views.config, name="admin-ops-config"),
    path("admin-ops/ai-agents/", admin_ops_views.ai_agents, name="admin-ops-ai-agents"),
    path("admin-ops/ai-agent-actions/", admin_ops_views.ai_agents, name="admin-ops-ai-agent-actions"),
    path("admin-ops/ai-agents/new/", admin_ops_views.ai_agent_form, name="admin-ops-ai-agent-new"),
    path("admin-ops/ai-agents/<int:agent_id>/edit/", admin_ops_views.ai_agent_form, name="admin-ops-ai-agent-edit"),
    path("admin-ops/ai-agent-actions/<int:action_id>/", admin_ops_views.ai_agent_action_detail, name="admin-ops-ai-agent-action-detail"),
    path("admin-ops/markets/", admin_ops_views.markets, name="admin-ops-markets"),
    path("admin-ops/users/", admin_ops_views.users, name="admin-ops-users"),
    path("admin-ops/users/<int:user_id>/", admin_ops_views.user_detail, name="admin-ops-user-detail"),
    path("admin-ops/logs/", admin_ops_views.system_logs, name="admin-ops-system-logs"),
    path("admin-ops/logs/<int:log_id>/", admin_ops_views.system_log_detail, name="admin-ops-system-log-detail"),
    path("admin-ops/badges/", admin_ops_views.badges, name="admin-ops-badges"),
    path("admin-ops/badges/new/", admin_ops_views.badge_form, {"mode": "new"}, name="admin-ops-badge-new"),
    path("admin-ops/badges/<slug:code>/edit/", admin_ops_views.badge_form, {"mode": "edit"}, name="admin-ops-badge-edit"),
    path("admin-ops/moderation/", admin_ops_views.moderation, name="admin-ops-moderation"),
    path("admin-ops/resolution/", admin_ops_views.resolution, name="admin-ops-resolution"),
    path("admin-ops/taxonomy/", admin_ops_views.taxonomy, name="admin-ops-taxonomy"),
    path("admin-ops/markets/new/", admin_ops_views.market_form, {"mode": "new"}, name="admin-ops-market-new"),
    path("admin-ops/markets/<slug:slug>/edit/", admin_ops_views.market_form, {"mode": "edit"}, name="admin-ops-market-edit"),
    path("admin-ops/resolution/<slug:slug>/<str:action>/", admin_ops_views.resolution_action, name="admin-ops-resolution-market-action"),
    path("admin-ops/resolution/<str:action>/", admin_ops_views.resolution_action, name="admin-ops-resolution-action"),
    path("admin-ops/queues/<str:kind>/<int:item_id>/<str:action>/", admin_ops_views.queue_action, name="admin-ops-queue-item-action"),
    path("admin-ops/queues/<str:action>/", admin_ops_views.queue_action, name="admin-ops-queue-action"),
    path("admin-ops/taxonomy/<str:action>/", admin_ops_views.category_action, name="admin-ops-category-action"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
