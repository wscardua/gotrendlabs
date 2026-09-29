import json
import os
from ipaddress import ip_address, ip_network

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.web.django.accounts.api_client import AuthAPIError, send_analytics_events
from apps.web.django.accounts.session import auth_token


@require_POST
def collect(request):
    if len(request.body) > 20000:
        return JsonResponse({"detail": "Lote muito grande."}, status=413)
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "JSON inválido."}, status=400)
    headers = {}
    secret = os.environ.get("GOTRENDLABS_ANALYTICS_PROXY_SECRET", "")
    if secret:
        headers["X-Analytics-Proxy-Secret"] = secret
        peer = request.META.get("REMOTE_ADDR", "")
        trusted = os.environ.get("GOTRENDLABS_ANALYTICS_TRUSTED_PROXY_CIDRS", "")
        try:
            trusted_peer = any(ip_address(peer) in ip_network(value.strip()) for value in trusted.split(",") if value.strip())
        except ValueError:
            trusted_peer = False
        if trusted_peer:
            ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or peer
        else:
            ip = peer
        headers["X-Analytics-Client-IP"] = ip
    try:
        result = send_analytics_events(payload, auth_token(request), headers)
    except AuthAPIError as exc:
        return JsonResponse({"detail": str(exc)}, status=exc.status_code or 503)
    return JsonResponse(result)
