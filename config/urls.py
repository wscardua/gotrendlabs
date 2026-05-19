from django.contrib import admin
from django.urls import path

from accounts import views as account_views
from admin_ops import views as admin_ops_views
from core import views as core_views
from markets import views as market_views
from profiles import views as profile_views
from wallet import views as wallet_views

urlpatterns = [
    path("", core_views.home, name="home"),
    path("concepts/", core_views.concepts, name="concepts"),
    path("categories/", core_views.categories, name="categories"),
    path("security/", core_views.security, name="security"),
    path("suggestion/", core_views.suggestion, name="suggestion"),
    path("feedback/", core_views.feedback, name="feedback"),
    path("markets/<slug:slug>/", market_views.detail, name="market-detail"),
    path("markets/<slug:slug>/predict/", market_views.prediction_preview, name="prediction-preview"),
    path("login/", account_views.login_view, name="login"),
    path("register/", account_views.register_view, name="register"),
    path("wallet/", wallet_views.wallet_home, name="wallet"),
    path("profile/", profile_views.profile, name="profile"),
    path("rankings/", profile_views.rankings, name="rankings"),
    path("admin-ops/", admin_ops_views.dashboard, name="admin-ops-dashboard"),
    path("admin/", admin.site.urls),
]
