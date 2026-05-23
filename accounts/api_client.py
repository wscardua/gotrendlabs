import json
import json.decoder
import urllib.error
import urllib.request
from urllib.parse import urlencode

from django.conf import settings


class AuthAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def _request(method, path, payload=None, token=None, timeout=5):
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{settings.BACKEND_API_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return json.loads(raw.decode()) if raw else {}
    except json.decoder.JSONDecodeError as exc:
        raise AuthAPIError("Serviço da API retornou resposta inesperada.") from exc
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode()
        try:
            detail = json.loads(raw_body).get("detail")
        except Exception:
            detail = None
        if isinstance(detail, list):
            detail = "; ".join(item.get("msg", str(item)) if isinstance(item, dict) else str(item) for item in detail)
        fallback = "Serviço da API retornou erro interno." if exc.code >= 500 else "Não foi possível concluir a requisição."
        raise AuthAPIError(detail or fallback, exc.code) from exc
    except urllib.error.URLError as exc:
        raise AuthAPIError("Serviço de autenticação indisponível.") from exc


def _currency_label(value):
    return str(value or "0 O₵").replace(" OC", " O₵")


def _normalize_market_payload(market):
    if isinstance(market, dict) and "volume_oc" in market:
        return {**market, "volume_oc": _currency_label(market.get("volume_oc"))}
    return market


def get_backend_health():
    return _request("GET", "/health", timeout=2)


def register_user(data):
    return _request("POST", "/auth/register", data)


def login_user(data):
    return _request("POST", "/auth/login", data)


def request_password_reset(email):
    return _request("POST", "/auth/password-reset/request", {"email": email})


def confirm_password_reset(token, password):
    return _request("POST", "/auth/password-reset/confirm", {"token": token, "password": password})


def logout_user(token):
    return _request("POST", "/auth/logout", token=token)


def get_session(token):
    return _request("GET", "/auth/session", token=token)


def get_me(token):
    return _request("GET", "/users/me", token=token)


def get_wallet(token):
    return _request("GET", "/users/me/wallet", token=token)


def get_ledger(token):
    return _request("GET", "/users/me/ledger", token=token)


def get_wallet_recharge_requests(token):
    return _request("GET", "/users/me/wallet/recharge-requests", token=token)


def create_wallet_recharge_request(token):
    return _request("POST", "/users/me/wallet/recharge-requests", token=token)


def get_badges(token):
    return _request("GET", "/users/me/badges", token=token)


def get_badge_catalog(token=None):
    return _request("GET", "/badges", token=token)["badges"]


def get_activity(token):
    return _request("GET", "/users/me/activity", token=token)


def get_notifications(token):
    return _request("GET", "/users/me/notifications", token=token)


def mark_notifications_read(token):
    return _request("POST", "/users/me/notifications/read-all", token=token)


def get_rankings(**filters):
    query = urlencode({key: value for key, value in filters.items() if value})
    path = f"/rankings?{query}" if query else "/rankings"
    return _request("GET", path)


def get_markets(token=None, **filters):
    query = urlencode({key: value for key, value in filters.items() if value})
    path = f"/markets?{query}" if query else "/markets"
    return [_normalize_market_payload(market) for market in _request("GET", path, token=token)["markets"]]


def get_market(slug, token=None):
    return _normalize_market_payload(_request("GET", f"/markets/{slug}", token=token))


def track_market_view(slug):
    return _request("POST", f"/markets/{slug}/view")


def track_market_share(slug):
    return _request("POST", f"/markets/{slug}/share")


def favorite_market(token, slug):
    return _request("POST", f"/markets/{slug}/favorite", token=token)


def unfavorite_market(token, slug):
    return _request("DELETE", f"/markets/{slug}/favorite", token=token)


def like_market(token, slug):
    return _request("POST", f"/markets/{slug}/like", token=token)


def unlike_market(token, slug):
    return _request("DELETE", f"/markets/{slug}/like", token=token)


def create_prediction(token, slug, data):
    return _request("POST", f"/markets/{slug}/predict", data, token=token)


def preview_prediction(slug, data):
    return _request("POST", f"/markets/{slug}/prediction-preview", data)


def get_market_comments(slug, token=None):
    return _request("GET", f"/markets/{slug}/comments", token=token)["comments"]


def create_comment(token, slug, data):
    return _request("POST", f"/markets/{slug}/comments", data, token=token)


def react_to_comment(token, comment_id, reaction):
    return _request("POST", f"/comments/{comment_id}/{reaction}", token=token)


def clear_comment_reaction(token, comment_id, reaction):
    return _request("DELETE", f"/comments/{comment_id}/{reaction}", token=token)


def create_suggestion(token, data):
    try:
        return _request("POST", "/suggestions", data, token=token)
    except AuthAPIError as exc:
        if exc.status_code == 404:
            return _request("POST", "/suggestions/", data, token=token)
        raise


def create_feedback(data, token=None):
    try:
        return _request("POST", "/feedback", data, token=token)
    except AuthAPIError as exc:
        if exc.status_code == 404:
            return _request("POST", "/feedback/", data, token=token)
        raise


def admin_get_markets(token, **filters):
    query = urlencode({key: value for key, value in filters.items() if value})
    path = f"/admin/markets?{query}" if query else "/admin/markets"
    payload = _request("GET", path, token=token)
    if isinstance(payload, dict) and "markets" in payload:
        return {**payload, "markets": [_normalize_market_payload(market) for market in payload["markets"]]}
    return payload


def admin_get_users(token, **filters):
    query = urlencode({key: value for key, value in filters.items() if value})
    path = f"/admin/users?{query}" if query else "/admin/users"
    return _request("GET", path, token=token)


def admin_get_user(token, user_id):
    return _request("GET", f"/admin/users/{user_id}", token=token)


def admin_deactivate_user(token, user_id, note):
    return _request("POST", f"/admin/users/{user_id}/deactivate", {"note": note}, token=token)


def admin_reactivate_user(token, user_id, note):
    return _request("POST", f"/admin/users/{user_id}/reactivate", {"note": note}, token=token)


def admin_revoke_user_sessions(token, user_id, note):
    return _request("POST", f"/admin/users/{user_id}/sessions/revoke", {"note": note}, token=token)


def admin_adjust_user_wallet(token, user_id, direction, amount_oc, note):
    return _request(
        "POST",
        f"/admin/users/{user_id}/wallet/adjust",
        {"direction": direction, "amount_oc": amount_oc, "note": note},
        token=token,
    )


def admin_update_user_roles(token, user_id, is_staff, is_superuser, note):
    return _request(
        "POST",
        f"/admin/users/{user_id}/roles",
        {"is_staff": is_staff, "is_superuser": is_superuser, "note": note},
        token=token,
    )


def admin_update_user_bot(token, user_id, is_bot, note):
    return _request(
        "POST",
        f"/admin/users/{user_id}/bot",
        {"is_bot": is_bot, "note": note},
        token=token,
    )


def admin_create_market(token, data):
    return _normalize_market_payload(_request("POST", "/admin/markets", data, token=token))


def admin_get_market(token, slug):
    return _normalize_market_payload(_request("GET", f"/admin/markets/{slug}", token=token))


def admin_get_market_participants(token, slug):
    return _request("GET", f"/admin/markets/{slug}/participants", token=token)


def admin_update_market(token, slug, data):
    return _normalize_market_payload(_request("PATCH", f"/admin/markets/{slug}", data, token=token))


def admin_publish_market(token, slug, note=""):
    return _normalize_market_payload(_request("POST", f"/admin/markets/{slug}/publish", {"note": note}, token=token))


def admin_cancel_market(token, slug, note=""):
    return _normalize_market_payload(_request("POST", f"/admin/markets/{slug}/cancel", {"note": note}, token=token))


def admin_lock_market(token, slug, note=""):
    return _normalize_market_payload(_request("POST", f"/admin/markets/{slug}/lock", {"note": note}, token=token))


def admin_resolve_market(token, slug, winning_option_id, source_url="", note="", resolved_at=None, resolution_timezone=""):
    payload = {"winning_option_id": winning_option_id, "source_url": source_url, "note": note}
    if resolved_at:
        payload["resolved_at"] = resolved_at.isoformat() if hasattr(resolved_at, "isoformat") else str(resolved_at)
    if resolution_timezone:
        payload["resolution_timezone"] = resolution_timezone
    return _normalize_market_payload(_request("POST", f"/admin/markets/{slug}/resolve", payload, token=token))


def admin_get_market_resolution_audit(token, slug, limit=50, offset=0):
    query = urlencode({"limit": limit, "offset": offset})
    return _request("GET", f"/admin/markets/{slug}/resolution-audit?{query}", token=token)


def admin_get_queues(token, **filters):
    query = urlencode({key: value for key, value in filters.items() if value})
    path = f"/admin/queues?{query}" if query else "/admin/queues"
    return _request("GET", path, token=token)


def admin_get_comments(token, **filters):
    query = urlencode({key: value for key, value in filters.items() if value})
    path = f"/admin/comments?{query}" if query else "/admin/comments"
    return _request("GET", path, token=token)


def admin_get_system_logs(token, **filters):
    query = urlencode({key: value for key, value in filters.items() if value})
    path = f"/admin/system-logs?{query}" if query else "/admin/system-logs"
    return _request("GET", path, token=token)


def admin_get_system_log(token, log_id):
    return _request("GET", f"/admin/system-logs/{log_id}", token=token)


def admin_get_dashboard_summary(token):
    return _request("GET", "/admin/dashboard-summary", token=token)


def admin_get_ai_agents(token):
    return _request("GET", "/admin/ai-agents", token=token)


def admin_get_ai_agent(token, agent_id):
    return _request("GET", f"/admin/ai-agents/{agent_id}", token=token)


def admin_create_ai_agent(token, data):
    return _request("POST", "/admin/ai-agents", data, token=token)


def admin_update_ai_agent(token, agent_id, data):
    return _request("PATCH", f"/admin/ai-agents/{agent_id}", data, token=token)


def admin_get_ai_agent_actions(token, **filters):
    query = urlencode({key: value for key, value in filters.items() if value})
    path = f"/admin/ai-agent-actions?{query}" if query else "/admin/ai-agent-actions"
    return _request("GET", path, token=token)


def admin_get_ai_agent_action(token, action_id):
    return _request("GET", f"/admin/ai-agent-actions/{action_id}", token=token)


def admin_moderate_comment(token, comment_id, status, note=""):
    return _request("PATCH", f"/admin/comments/{comment_id}/moderation", {"status": status, "note": note}, token=token)


def admin_review_queue_item(token, kind, item_id, status, note=""):
    return _request("POST", f"/admin/queues/{kind}/{item_id}/review", {"status": status, "note": note}, token=token)


def admin_convert_suggestion(token, item_id, note=""):
    return _request("POST", f"/admin/queues/suggestions/{item_id}/convert-draft", {"note": note}, token=token)


def admin_reward_feedback(token, item_id, amount_oc, note=""):
    return _request("POST", f"/admin/queues/feedback/{item_id}/reward", {"amount_oc": amount_oc, "note": note}, token=token)


def admin_reward_suggestion(token, item_id, amount_oc, note=""):
    return _request("POST", f"/admin/queues/suggestions/{item_id}/reward", {"amount_oc": amount_oc, "note": note}, token=token)


def admin_approve_wallet_recharge(token, item_id, amount_oc, note=""):
    return _request("POST", f"/admin/queues/wallet-recharges/{item_id}/approve", {"amount_oc": amount_oc, "note": note}, token=token)


def admin_reject_wallet_recharge(token, item_id, note=""):
    return _request("POST", f"/admin/queues/wallet-recharges/{item_id}/reject", {"note": note}, token=token)


def admin_get_taxonomy(token):
    return _request("GET", "/admin/taxonomy", token=token)


def admin_get_badges(token):
    return _request("GET", "/admin/badges", token=token)


def admin_create_badge(token, data):
    return _request("POST", "/admin/badges", data, token=token)


def admin_update_badge(token, code, data):
    return _request("PATCH", f"/admin/badges/{code}", data, token=token)


def admin_deactivate_badge(token, code, note=""):
    return _request("POST", f"/admin/badges/{code}/deactivate", {"note": note}, token=token)


def admin_create_category(token, data):
    return _request("POST", "/admin/categories", data, token=token)


def admin_update_category(token, slug, data):
    return _request("PATCH", f"/admin/categories/{slug}", data, token=token)


def admin_block_category(token, slug, note=""):
    return _request("POST", f"/admin/categories/{slug}/block", {"note": note}, token=token)


def admin_unblock_category(token, slug, note=""):
    return _request("POST", f"/admin/categories/{slug}/unblock", {"note": note}, token=token)


def admin_create_subcategory(token, category_slug, data):
    return _request("POST", f"/admin/categories/{category_slug}/subcategories", data, token=token)


def admin_update_subcategory(token, category_slug, subcategory_slug, data):
    return _request("PATCH", f"/admin/categories/{category_slug}/subcategories/{subcategory_slug}", data, token=token)


def admin_block_subcategory(token, category_slug, subcategory_slug, note=""):
    return _request("POST", f"/admin/categories/{category_slug}/subcategories/{subcategory_slug}/block", {"note": note}, token=token)


def admin_unblock_subcategory(token, category_slug, subcategory_slug, note=""):
    return _request("POST", f"/admin/categories/{category_slug}/subcategories/{subcategory_slug}/unblock", {"note": note}, token=token)


def admin_create_event(token, category_slug, subcategory_slug, data):
    return _request("POST", f"/admin/categories/{category_slug}/subcategories/{subcategory_slug}/events", data, token=token)


def admin_update_event(token, category_slug, subcategory_slug, event_slug, data):
    return _request("PATCH", f"/admin/categories/{category_slug}/subcategories/{subcategory_slug}/events/{event_slug}", data, token=token)


def admin_block_event(token, category_slug, subcategory_slug, event_slug, note=""):
    return _request("POST", f"/admin/categories/{category_slug}/subcategories/{subcategory_slug}/events/{event_slug}/block", {"note": note}, token=token)


def admin_unblock_event(token, category_slug, subcategory_slug, event_slug, note=""):
    return _request("POST", f"/admin/categories/{category_slug}/subcategories/{subcategory_slug}/events/{event_slug}/unblock", {"note": note}, token=token)


def admin_delete_event(token, category_slug, subcategory_slug, event_slug):
    return _request("DELETE", f"/admin/categories/{category_slug}/subcategories/{subcategory_slug}/events/{event_slug}", token=token)


def update_me(token, data):
    return _request("PATCH", "/users/me", data, token=token)


def request_account_deletion(token):
    return _request("POST", "/auth/account-deletion-request", token=token)
