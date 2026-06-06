from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.db import DatabaseError
from django.db.models import F
from django.urls import reverse
from django.views.decorators.http import require_POST
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from accounts.api_client import (
    AuthAPIError,
    clear_comment_reaction,
    create_comment,
    create_prediction,
    favorite_market,
    preview_prediction,
    track_market_view,
    get_market,
    like_market,
    react_to_comment,
    unfavorite_market,
    unlike_market,
)
from accounts.session import auth_token, auth_user, is_authenticated, login_url_with_next, safe_redirect_url
from core.domain_client import local_market
from markets.models import CommentReaction, Market, MarketComment, MarketFavorite, MarketLike, MarketOption, Prediction


def _display_handle(value):
    value = (value or "").strip()
    return value if value.startswith("@") else f"@{value}"


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _datetime_label(value, timezone_name):
    parsed = _parse_datetime(value)
    if not parsed:
        return ""
    timezone_name = timezone_name or "UTC"
    try:
        target_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        target_timezone = ZoneInfo("UTC")
        timezone_name = "UTC"
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
    return f"{parsed.astimezone(target_timezone).strftime('%d/%m/%Y %H:%M')} {timezone_name}"


def _existing_prediction(user_id, slug):
    if not user_id:
        return None
    prediction = (
        Prediction.objects.select_related("market_option", "market")
        .filter(user_id=user_id, market__slug=slug)
        .order_by("-created_at")
        .first()
    )
    if not prediction:
        return None
    return {
        "id": prediction.id,
        "option_label": prediction.market_option.label,
        "stake_amount": prediction.stake_amount,
        "probability_at_entry": prediction.probability_at_entry,
        "potential_payout": prediction.potential_payout,
        "status": prediction.status,
        "won": prediction.won,
        "created_at": prediction.created_at,
    }


def _with_option_ids(slug, market):
    needs_ids = not all(option.get("id") for option in market.get("options", []))
    needs_exact = not all("probability_exact" in option for option in market.get("options", []))
    needs_sparkline = not market.get("sparkline_path") or not market.get("sparkline_series")
    needs_notices = not all(key in market for key in ("category_notice", "subcategory_notice", "event_notice"))
    if not needs_ids and not needs_exact and not needs_sparkline and not needs_notices:
        return market
    local_payload = local_market(slug)
    if needs_sparkline and not needs_ids and not needs_exact:
        hydrated = {**market}
        hydrated["sparkline_path"] = local_payload.get("sparkline_path", "")
        hydrated["sparkline_area_path"] = local_payload.get("sparkline_area_path", "")
        hydrated["sparkline_series"] = local_payload.get("sparkline_series", [])
        hydrated["category_notice"] = hydrated.get("category_notice", local_payload.get("category_notice", ""))
        hydrated["subcategory_notice"] = hydrated.get("subcategory_notice", local_payload.get("subcategory_notice", ""))
        hydrated["event_notice"] = hydrated.get("event_notice", local_payload.get("event_notice", ""))
        return hydrated
    option_ids = {
        option.label: option.id
        for option in MarketOption.objects.filter(market__slug=slug).order_by("display_order", "id")
    }
    hydrated = {**market}
    hydrated["sparkline_path"] = local_payload.get("sparkline_path", "")
    hydrated["sparkline_area_path"] = local_payload.get("sparkline_area_path", "")
    hydrated["sparkline_series"] = local_payload.get("sparkline_series", [])
    hydrated["category_notice"] = hydrated.get("category_notice", local_payload.get("category_notice", ""))
    hydrated["subcategory_notice"] = hydrated.get("subcategory_notice", local_payload.get("subcategory_notice", ""))
    hydrated["event_notice"] = hydrated.get("event_notice", local_payload.get("event_notice", ""))
    local_options = {option.get("label"): option for option in local_payload.get("options", [])}
    hydrated["options"] = []
    for option in market.get("options", []):
        local_option = local_options.get(option.get("label"), {})
        hydrated["options"].append(
            {
                **option,
                "id": option.get("id") or option_ids.get(option.get("label")),
                "probability_exact": option.get("probability_exact", local_option.get("probability_exact", 0)),
            }
        )
    return hydrated


def _local_comments(slug, user_id=None):
    try:
        comments = (
            MarketComment.objects.select_related("author", "market")
            .filter(market__slug=slug, status="visible")
            .order_by("-created_at", "-id")
        )
        comments = list(comments)
    except DatabaseError:
        return []
    payload = []
    viewer_reactions = {}
    if user_id:
        viewer_reactions = {
            reaction.comment_id: reaction.reaction
            for reaction in CommentReaction.objects.filter(user_id=user_id, comment__market__slug=slug)
        }
    for comment in comments:
        like_count = comment.reactions.filter(reaction="like").count()
        dislike_count = comment.reactions.filter(reaction="dislike").count()
        payload.append(
            {
                "id": comment.id,
                "market_slug": comment.market.slug,
                "author_id": comment.author_id,
                "author_handle": _display_handle(comment.author.username),
                "author_display_name": comment.author.first_name or _display_handle(comment.author.username),
                "author_is_bot": bool(getattr(comment.author, "is_bot", False)),
                "author_badge_label": "IA oficial" if getattr(comment.author, "is_bot", False) else "",
                "body": comment.body,
                "status": comment.status,
                "like_count": like_count,
                "dislike_count": dislike_count,
                "viewer_reaction": viewer_reactions.get(comment.id),
                "created_at": comment.created_at,
            }
        )
    return payload


def _normalized_comments(comments):
    normalized = []
    for comment in comments or []:
        item = {**comment}
        item["id"] = item.get("id") or ""
        item["author_display_name"] = item.get("author_display_name") or item.get("author") or item.get("author_handle", "")
        item["author_handle"] = _display_handle(item.get("author_handle") or item.get("author") or item["author_display_name"])
        item["author_is_bot"] = bool(item.get("author_is_bot", False))
        item["author_badge_label"] = item.get("author_badge_label") or ("IA oficial" if item["author_is_bot"] else "")
        item["like_count"] = item.get("like_count", item.get("up", 0))
        item["dislike_count"] = item.get("dislike_count", item.get("down", 0))
        item["viewer_reaction"] = item.get("viewer_reaction") or ""
        normalized.append(item)
    return normalized


def _detail_context(request, slug, market, **extra):
    market = _with_option_ids(slug, market)
    resolution_timezone = market.get("resolution_timezone") or market.get("close_timezone") or "UTC"
    market = {
        **market,
        "event": market.get("event") or "Geral",
        "category_notice": market.get("category_notice") or "",
        "subcategory_notice": market.get("subcategory_notice") or "",
        "event_notice": market.get("event_notice") or "",
        "resolution_timezone": resolution_timezone,
        "resolved_at_label": market.get("resolved_at_label") or _datetime_label(market.get("resolved_at"), resolution_timezone),
    }
    user = auth_user(request) or {}
    if is_authenticated(request) and not market.get("viewer_has_favorite") and user.get("id"):
        try:
            market = {
                **market,
                "viewer_has_favorite": MarketFavorite.objects.filter(user_id=user["id"], market__slug=slug).exists(),
            }
        except DatabaseError:
            market = {**market, "viewer_has_favorite": bool(market.get("viewer_has_favorite"))}
    if is_authenticated(request) and not market.get("viewer_has_like") and user.get("id"):
        try:
            market = {
                **market,
                "viewer_has_like": MarketLike.objects.filter(user_id=user["id"], market__slug=slug).exists(),
            }
        except DatabaseError:
            market = {**market, "viewer_has_like": bool(market.get("viewer_has_like"))}
    if "comments" not in market:
        market = {**market, "comments": _local_comments(slug, user.get("id"))}
    else:
        comments = _normalized_comments(market.get("comments", []))
        if not comments:
            comments = _local_comments(slug, user.get("id"))
        market = {**market, "comments": comments}
    if "comment_count" not in market or market.get("comment_count") is None:
        market = {**market, "comment_count": len(market.get("comments", []))}
    context = {
        "market": market,
        "is_guest": not is_authenticated(request),
        "existing_prediction": _existing_prediction(user.get("id"), slug),
    }
    context.update(extra)
    return context


def _track_market_view(slug):
    try:
        track_market_view(slug)
        return
    except AuthAPIError:
        pass
    try:
        Market.objects.filter(slug=slug).exclude(status="draft").update(view_count=F("view_count") + 1)
    except DatabaseError:
        pass


def detail(request, slug):
    try:
        market = get_market(slug, auth_token(request) if is_authenticated(request) else None)
    except AuthAPIError:
        market = local_market(slug)
        market["comments"] = _local_comments(slug, (auth_user(request) or {}).get("id")) or market.get("comments", [])
    response = render(request, "markets/detail.html", _detail_context(request, slug, market))
    _track_market_view(slug)
    return response


def prediction_preview(request, slug):
    try:
        market = get_market(slug)
    except AuthAPIError:
        market = local_market(slug)
    market = _with_option_ids(slug, market)
    amount = int(request.POST.get("amount", "80") or 80)
    option_id = request.POST.get("option_id") or market["options"][0]["id"]
    selected_option = next((option for option in market["options"] if str(option.get("id")) == str(option_id)), market["options"][0])
    choice = request.POST.get("choice") or selected_option.get("label")
    preview_error = ""
    try:
        preview = preview_prediction(
            slug,
            {
                "option_id": selected_option["id"],
                "stake_amount": amount,
                "client_locale": getattr(request, "LANGUAGE_CODE", "pt-br"),
            },
        )
        estimated_return = preview["estimated_return"]
    except AuthAPIError as exc:
        estimated_return = 0
        preview_error = str(exc)
    return render(
        request,
        "markets/partials/prediction_preview.html",
        {"market": market, "amount": amount, "choice": choice, "estimated_return": estimated_return, "preview_error": preview_error},
    )


@require_POST
def confirm_prediction(request, slug):
    if not is_authenticated(request):
        return redirect(login_url_with_next(request, reverse("market-detail", args=[slug])))

    data = {
        "option_id": request.POST.get("option_id"),
        "stake_amount": request.POST.get("stake_amount"),
        "client_locale": getattr(request, "LANGUAGE_CODE", "pt-br"),
    }
    try:
        result = create_prediction(auth_token(request), slug, data)
    except AuthAPIError as exc:
        try:
            market = get_market(slug, auth_token(request))
        except AuthAPIError:
            market = local_market(slug)
        return render(
            request,
            "markets/detail.html",
            _detail_context(request, slug, market, prediction_error=str(exc)),
            status=400 if exc.status_code != 401 else 401,
        )
    else:
        market = get_market(slug, auth_token(request))
        return render(
            request,
            "markets/detail.html",
            _detail_context(request, slug, market, prediction_result=result),
        )


@require_POST
def submit_comment(request, slug):
    if not is_authenticated(request):
        return redirect(login_url_with_next(request, reverse("market-detail", args=[slug])))

    data = {
        "body": request.POST.get("body", ""),
        "client_locale": getattr(request, "LANGUAGE_CODE", "pt-br"),
    }
    try:
        create_comment(auth_token(request), slug, data)
    except AuthAPIError as exc:
        try:
            market = get_market(slug, auth_token(request))
        except AuthAPIError:
            market = local_market(slug)
            market["comments"] = _local_comments(slug, (auth_user(request) or {}).get("id")) or market.get("comments", [])
        return render(
            request,
            "markets/detail.html",
            _detail_context(request, slug, market, comment_error=str(exc)),
            status=400 if exc.status_code != 401 else 401,
        )
    return redirect(f"{reverse('market-detail', args=[slug])}#comments")


@require_POST
def comment_reaction(request, slug, comment_id):
    if not is_authenticated(request):
        return redirect(login_url_with_next(request, reverse("market-detail", args=[slug])))
    reaction = request.POST.get("reaction")
    current = request.POST.get("current_reaction")
    if reaction not in {"like", "dislike"}:
        return redirect(f"{reverse('market-detail', args=[slug])}#comments")
    try:
        if current == reaction:
            clear_comment_reaction(auth_token(request), comment_id, reaction)
        else:
            react_to_comment(auth_token(request), comment_id, reaction)
    except AuthAPIError:
        pass
    return redirect(f"{reverse('market-detail', args=[slug])}#comments")


@require_POST
def favorite_toggle(request, slug):
    if not is_authenticated(request):
        return redirect(login_url_with_next(request, request.POST.get("next")))
    should_unfavorite = request.POST.get("current_favorite") == "true"
    if should_unfavorite:
        action = unfavorite_market
    else:
        action = favorite_market
    try:
        result = action(auth_token(request), slug)
        favorited = bool(result.get("viewer_has_favorite"))
    except AuthAPIError as exc:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": str(exc)}, status=400 if exc.status_code != 401 else 401)
        return redirect(safe_redirect_url(request, request.POST.get("next"), reverse("home")))
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "slug": slug, "favorited": favorited})
    return redirect(safe_redirect_url(request, request.POST.get("next"), reverse("home")))


@require_POST
def like_toggle(request, slug):
    if not is_authenticated(request):
        return redirect(login_url_with_next(request, request.POST.get("next")))
    should_unlike = request.POST.get("current_like") == "true"
    if should_unlike:
        action = unlike_market
    else:
        action = like_market
    try:
        result = action(auth_token(request), slug)
        liked = bool(result.get("viewer_has_like"))
        like_count = int(result.get("market_like_count") or 0)
    except AuthAPIError as exc:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": str(exc)}, status=400 if exc.status_code != 401 else 401)
        return redirect(safe_redirect_url(request, request.POST.get("next"), reverse("home")))
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "slug": slug, "liked": liked, "like_count": like_count})
    return redirect(safe_redirect_url(request, request.POST.get("next"), reverse("home")))
