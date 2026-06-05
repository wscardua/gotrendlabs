from accounts.api_client import AuthAPIError, get_me, get_notifications, get_wallet
from accounts.session import auth_token, auth_user, is_authenticated
from core.domain_client import get_domain_client
from core.platform_config import maintenance_enabled


def _display_handle(value):
    value = (value or "").strip()
    return value if value.startswith("@") else f"@{value}"


def session_context(request):
    client = get_domain_client()
    viewer = client.viewer().copy()
    user = auth_user(request)
    if user:
        viewer["name"] = user["display_name"]
        viewer["handle"] = _display_handle(user["handle"])
        viewer["initials"] = "".join(part[0] for part in viewer["name"].split()[:2]).upper() or "U"
        viewer["language"] = user["preferred_language"].upper()
        is_operator = bool(user.get("is_staff") or user.get("is_superuser"))
        try:
            wallet = get_wallet(auth_token(request))
        except AuthAPIError:
            wallet = _local_wallet(user.get("id"))
        viewer["balance_gtl"] = wallet.get("available_gtl", viewer["balance_gtl"])
        viewer["locked_gtl"] = wallet.get("locked_gtl", viewer["locked_gtl"])
        if is_operator:
            viewer["reputation"] = ""
            viewer["accuracy"] = ""
            viewer["streak"] = ""
        else:
            try:
                profile = get_me(auth_token(request))
                reputation = profile.get("reputation", {})
            except AuthAPIError:
                reputation = _local_reputation(user.get("id"))
            viewer["reputation"] = reputation.get("reputation_score", viewer["reputation"])
            viewer["accuracy"] = reputation.get("accuracy_indicator", viewer.get("accuracy", "0%"))
            viewer["streak"] = reputation.get("streak", viewer.get("streak", 0))
        try:
            notifications = get_notifications(auth_token(request))
        except AuthAPIError:
            notifications = _local_notifications(user.get("id"))
    else:
        notifications = {"unread_count": 0, "notifications": []}
    operator_maintenance_notice = bool(
        user
        and (user.get("is_staff") or user.get("is_superuser"))
        and maintenance_enabled()
    )
    can_access_admin_ops = bool(user and (user.get("is_staff") or user.get("is_superuser")))
    return {
        "viewer": viewer,
        "is_guest": not is_authenticated(request),
        "can_access_admin_ops": can_access_admin_ops,
        "operator_maintenance_notice": operator_maintenance_notice,
        "notifications": notifications,
    }


def _local_wallet(user_id):
    if not user_id:
        return {}
    try:
        from accounts.models import WalletBalance

        balance = WalletBalance.objects.get(user_id=user_id)
    except Exception:
        return {}
    return {
        "available_gtl": balance.available_gtl,
        "locked_gtl": balance.locked_gtl,
        "total_earned_gtl": balance.total_earned_gtl,
    }


def _local_reputation(user_id):
    if not user_id:
        return {}
    try:
        from accounts.models import UserReputation

        reputation = UserReputation.objects.get(user_id=user_id)
    except Exception:
        return {}
    return {
        "reputation_score": reputation.reputation_score,
        "accuracy_indicator": reputation.accuracy_indicator,
        "streak": reputation.streak,
    }


def _local_notifications(user_id):
    if not user_id:
        return {"unread_count": 0, "notifications": []}
    try:
        from markets.models import UserNotification

        queryset = (
            UserNotification.objects.select_related("actor", "market")
            .filter(recipient_id=user_id)
            .order_by("-created_at", "-id")
        )
        unread_count = queryset.filter(is_read=False).count()
        items = []
        for notification in queryset[:10]:
            actor_handle = _display_handle(notification.actor.username) if notification.actor_id else ""
            actor_name = (notification.actor.first_name if notification.actor_id else "") or actor_handle
            items.append(
                {
                    "id": notification.id,
                    "event_type": notification.event_type,
                    "title": notification.title,
                    "body": notification.body,
                    "is_read": notification.is_read,
                    "actor_handle": actor_handle,
                    "actor_display_name": actor_name,
                    "market_slug": notification.market.slug if notification.market_id else "",
                    "market_title": notification.market.title if notification.market_id else "",
                    "comment_id": notification.comment_id,
                    "metadata": notification.metadata,
                    "created_at": notification.created_at.isoformat() if notification.created_at else "",
                    "created_at_label": "",
                }
            )
        return {"unread_count": unread_count, "notifications": items}
    except Exception:
        return {"unread_count": 0, "notifications": []}
