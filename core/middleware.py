from django.conf import settings
from django.shortcuts import redirect
import re

from accounts.session import USER_KEY
from core.platform_config import maintenance_enabled


class ReferralCaptureMiddleware:
    SESSION_KEY = "pending_referral_code"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in {"GET", "HEAD"}:
            code = re.sub(r"[^A-Za-z0-9]", "", request.GET.get("ref", ""))[:32]
            if code:
                request.session[self.SESSION_KEY] = code.upper()
        return self.get_response(request)


class MaintenanceModeMiddleware:
    EXEMPT_PREFIXES = (
        "/maintenance/",
        "/admin-ops/",
        "/login/",
        "/logout/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_redirect(request):
            return redirect("maintenance")
        return self.get_response(request)

    def _should_redirect(self, request):
        path = request.path_info or "/"
        if request.method not in {"GET", "HEAD"}:
            return False
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return False
        static_url = settings.STATIC_URL or ""
        static_prefixes = {static_url, f"/{static_url.lstrip('/')}"}
        media_url = settings.MEDIA_URL or ""
        media_prefixes = {media_url, f"/{media_url.lstrip('/')}"}
        if any(prefix and path.startswith(prefix) for prefix in static_prefixes):
            return False
        if any(prefix and path.startswith(prefix) for prefix in media_prefixes):
            return False
        if not maintenance_enabled():
            return False
        return not self._has_staff_bypass(request)

    def _has_staff_bypass(self, request):
        try:
            user = request.session.get(USER_KEY) or {}
        except Exception:
            return False
        return bool(user.get("is_staff") or user.get("is_superuser"))
