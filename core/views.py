from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.db import DatabaseError
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.api_client import AuthAPIError, create_feedback, create_suggestion, get_badge_catalog, get_badges, get_market, get_markets, get_me, mark_notifications_read, track_market_share
from accounts.session import api_login_required
from accounts.session import auth_token, auth_user, is_authenticated
from config.recaptcha import RecaptchaError, verify_recaptcha_response
from core.domain_client import get_domain_client, local_market, local_markets
from core.platform_config import load_platform_config
from core.social_share import badge_share_context, market_share_context, png_response_bytes, public_badge_share_token, render_badge_card, render_market_card, render_result_card, result_share_context
from markets.models import Market, MarketFavorite, MarketLike, MarketSuggestion, Prediction, ProductFeedback, UserNotification
from accounts.models import UserBadgeAward, UserProfile, UserReputation


def _session_model_user(request):
    user = auth_user(request) or {}
    user_id = user.get("id")
    if not user_id:
        return None
    return get_user_model().objects.filter(id=user_id).first()


def _should_use_local_queue_fallback(exc):
    return exc.status_code in {None, 404}


def _request_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded_for.split(",")[0].strip() or request.META.get("REMOTE_ADDR")


def _verify_guest_recaptcha(request):
    if is_authenticated(request):
        return
    try:
        verify_recaptcha_response(request.POST.get("g-recaptcha-response", ""), remote_ip=_request_ip(request))
    except RecaptchaError as exc:
        raise AuthAPIError(str(exc), 422) from exc


def maintenance(request):
    return render(request, "core/maintenance.html", {"platform_config": load_platform_config()})


def _market_thumb_fallback(market):
    value = (market.get("thumb") or "").strip()
    if value:
        return value[:4].upper()
    for source in (market.get("event"), market.get("category"), market.get("subcategory"), market.get("title")):
        words = [word for word in str(source or "").replace("-", " ").split() if word]
        if not words:
            continue
        if len(words) == 1:
            return words[0][:2].upper()
        return "".join(word[0] for word in words[:2]).upper()
    return "OR"


def _hydrate_market_visuals(markets):
    local_by_slug = {market["slug"]: market for market in local_markets()}
    hydrated = []
    for market in markets:
        local = local_by_slug.get(market.get("slug"), {})
        needs_series = not market.get("sparkline_series")
        needs_path = not market.get("sparkline_path")
        needs_option_ids = not all(option.get("id") for option in market.get("options", []))
        needs_exact = not all("probability_exact" in option for option in market.get("options", []))
        if not (needs_series or needs_path or needs_option_ids or needs_exact):
            hydrated.append(market)
            continue
        merged = {**market}
        if needs_series:
            merged["sparkline_series"] = local.get("sparkline_series", [])
        if needs_path:
            merged["sparkline_path"] = local.get("sparkline_path", "M 4 22 L 216 22")
            merged["sparkline_area_path"] = local.get("sparkline_area_path", "")
        if needs_option_ids or needs_exact:
            local_options = {option["label"]: option for option in local.get("options", [])}
            merged["options"] = [
                {
                    **option,
                    "id": option.get("id") or local_options.get(option.get("label"), {}).get("id"),
                    "probability_exact": option.get(
                        "probability_exact",
                        local_options.get(option.get("label"), {}).get("probability_exact", 0),
                    ),
                }
                for option in market.get("options", [])
            ]
        hydrated.append(merged)
    return [
        {
            **market,
            "thumb": _market_thumb_fallback(market),
            "thumb_color": market.get("thumb_color") or "#d8ece2",
            "event": market.get("event") or "Geral",
            "category_notice": market.get("category_notice") or local.get("category_notice", ""),
            "subcategory_notice": market.get("subcategory_notice") or local.get("subcategory_notice", ""),
            "event_notice": market.get("event_notice") or local.get("event_notice", ""),
            "viewer_has_prediction": bool(market.get("viewer_has_prediction")),
            "viewer_has_favorite": bool(market.get("viewer_has_favorite")),
            "viewer_has_like": bool(market.get("viewer_has_like")),
            "comment_count": int(market.get("comment_count") or 0),
        }
        for market in hydrated
    ]


def _public_visible_markets(markets):
    return [market for market in markets if market.get("status") != "canceled"]


def _mark_viewer_prediction_flags(markets, user_id):
    if not user_id:
        return markets
    slugs = [market.get("slug") for market in markets if market.get("slug")]
    try:
        predicted_slugs = set(
            Prediction.objects.filter(user_id=user_id, market__slug__in=slugs).values_list("market__slug", flat=True)
        )
    except DatabaseError:
        predicted_slugs = set()
    return [{**market, "viewer_has_prediction": market.get("viewer_has_prediction") or market.get("slug") in predicted_slugs} for market in markets]


def _mark_viewer_favorite_flags(markets, user_id):
    if not user_id:
        return markets
    slugs = [market.get("slug") for market in markets if market.get("slug")]
    try:
        favorite_slugs = set(
            MarketFavorite.objects.filter(user_id=user_id, market__slug__in=slugs).values_list("market__slug", flat=True)
        )
    except DatabaseError:
        favorite_slugs = set()
    return [{**market, "viewer_has_favorite": market.get("viewer_has_favorite") or market.get("slug") in favorite_slugs} for market in markets]


def _mark_viewer_like_flags(markets, user_id):
    if not user_id:
        return markets
    slugs = [market.get("slug") for market in markets if market.get("slug")]
    try:
        liked_slugs = set(
            MarketLike.objects.filter(user_id=user_id, market__slug__in=slugs).values_list("market__slug", flat=True)
        )
    except DatabaseError:
        liked_slugs = set()
    return [{**market, "viewer_has_like": market.get("viewer_has_like") or market.get("slug") in liked_slugs} for market in markets]


def _share_viewer(request):
    user = auth_user(request)
    if not user:
        return {
            "id": None,
            "name": "",
            "handle": "",
            "reputation": "",
            "is_authenticated": False,
        }
    viewer = get_domain_client().viewer().copy()
    viewer["is_authenticated"] = True
    viewer["id"] = user.get("id")
    viewer["name"] = user.get("display_name") or viewer["name"]
    viewer["handle"] = user.get("handle") or viewer["handle"]
    try:
        profile = get_me(auth_token(request))
        reputation = profile.get("reputation", {})
        viewer["reputation"] = reputation.get("reputation_score", viewer["reputation"])
    except AuthAPIError:
        pass
    return viewer


def _load_share_market(slug):
    try:
        market = get_market(slug)
    except AuthAPIError:
        market = local_market(slug)
    return {**market, "thumb": _market_thumb_fallback(market), "thumb_color": market.get("thumb_color") or "#d8ece2"}


def _track_market_share(slug):
    try:
        track_market_share(slug)
        return True
    except AuthAPIError:
        pass
    try:
        updated = Market.objects.filter(slug=slug).exclude(status="draft").update(share_count=F("share_count") + 1)
        return bool(updated)
    except DatabaseError:
        return False


def _earned_badge(request, code):
    try:
        badges = get_badges(auth_token(request))
    except AuthAPIError:
        badges = []
    return next((item for item in badges if item.get("code") == code and item.get("status") == "earned"), None)


def _public_badge_share(code, token):
    if not token:
        return None, None
    award = None
    awards = UserBadgeAward.objects.select_related("badge", "user").filter(badge__code=code, badge__is_active=True)
    for candidate in awards:
        if constant_time_compare(public_badge_share_token(candidate.user_id, code), token):
            award = candidate
            break
    if not award:
        return None, None
    profile = UserProfile.objects.filter(user=award.user).first()
    reputation = UserReputation.objects.filter(user=award.user).first()
    display_name = (profile.display_name if profile else "") or award.user.first_name or award.user.username
    badge = {
        "code": award.badge.code,
        "name": award.badge.name,
        "description": award.badge.description,
        "rule_description": award.badge.rule_description or award.reason_snapshot,
        "image_url": award.badge.image_url,
        "image_dark_url": award.badge.image_dark_url,
        "status": "earned",
    }
    viewer = {
        "id": award.user_id,
        "name": display_name,
        "handle": award.user.username,
        "reputation": reputation.reputation_score if reputation else 100,
        "share_token": public_badge_share_token(award.user_id, code),
    }
    return badge, viewer


def _badge_share_payload(request, code):
    badge, viewer = _public_badge_share(code, request.GET.get("t"))
    if badge:
        return badge, viewer, True
    if not is_authenticated(request):
        return None, None, False
    badge = _earned_badge(request, code)
    if not badge:
        return None, None, False
    viewer = _share_viewer(request)
    if viewer.get("id"):
        viewer["share_token"] = public_badge_share_token(viewer["id"], code)
    return badge, viewer, False


def _image_response(image):
    return HttpResponse(png_response_bytes(image), content_type="image/png")


def home(request):
    try:
        raw_markets = get_markets(token=auth_token(request) if is_authenticated(request) else None)
    except AuthAPIError:
        raw_markets = local_markets()
    markets = _hydrate_market_visuals(_public_visible_markets(raw_markets))
    markets = _mark_viewer_prediction_flags(markets, (auth_user(request) or {}).get("id") if is_authenticated(request) else None)
    markets = _mark_viewer_favorite_flags(markets, (auth_user(request) or {}).get("id") if is_authenticated(request) else None)
    markets = _mark_viewer_like_flags(markets, (auth_user(request) or {}).get("id") if is_authenticated(request) else None)
    return render(
        request,
        "core/home.html",
        {
            "markets": markets,
        },
    )


@require_POST
@api_login_required
def notifications_read_all(request):
    try:
        mark_notifications_read(auth_token(request))
    except AuthAPIError:
        try:
            UserNotification.objects.filter(recipient_id=(auth_user(request) or {}).get("id"), is_read=False).update(is_read=True, read_at=timezone.now())
        except DatabaseError:
            pass
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect(request.POST.get("next") or reverse("home"))


def concepts(request):
    return render(request, "core/concepts.html")


def categories(request):
    try:
        markets = get_markets()
    except AuthAPIError:
        markets = local_markets()
    markets = _hydrate_market_visuals(_public_visible_markets(markets))
    return render(request, "core/categories.html", {"markets": markets})


def badges(request):
    try:
        badge_list = get_badge_catalog(auth_token(request) if is_authenticated(request) else None)
    except AuthAPIError:
        try:
            badge_list = get_badge_catalog()
        except AuthAPIError:
            badge_list = []
    return render(request, "core/badges.html", {"badges": badge_list})


def share_badge(request, code):
    badge, viewer, is_public = _badge_share_payload(request, code)
    if not badge and not is_authenticated(request):
        return redirect(f"{reverse('login')}?next={request.get_full_path()}")
    if not badge:
        messages.error(request, "Essa badge ainda não está disponível para compartilhamento.")
        return redirect("badges")
    share = badge_share_context(request, badge, viewer)
    return render(request, "core/share_badge.html", {"badge": badge, "share": share, "share_viewer": viewer, "is_public_share": is_public})


def share_badge_image(request, code):
    badge, viewer, _ = _badge_share_payload(request, code)
    if not badge and not is_authenticated(request):
        return redirect(f"{reverse('login')}?next={request.get_full_path()}")
    if not badge:
        messages.error(request, "Essa badge ainda não está disponível para compartilhamento.")
        return redirect("badges")
    share = badge_share_context(request, badge, viewer)
    return _image_response(render_badge_card(badge, viewer, share))


def security(request):
    return render(request, "core/security.html")


def use_policy(request):
    return render(request, "core/use_policy.html")


def suggestion(request):
    error = ""
    form_data = {}
    if request.method == "POST":
        payload = {
            "guest_name": request.POST.get("guest_name", ""),
            "guest_email": request.POST.get("guest_email", "") or None,
            "question": request.POST.get("question", ""),
            "category": request.POST.get("category", ""),
            "kind": "binary",
            "suggested_source": request.POST.get("suggested_source", ""),
            "rationale": request.POST.get("rationale", ""),
            "recaptcha_token": request.POST.get("g-recaptcha-response", ""),
        }
        form_data = payload
        try:
            create_suggestion(auth_token(request), payload)
            messages.success(request, "Sugestão enviada para a fila editorial.")
            return redirect("home")
        except AuthAPIError as exc:
            if _should_use_local_queue_fallback(exc):
                try:
                    _verify_guest_recaptcha(request)
                except AuthAPIError as fallback_exc:
                    error = str(fallback_exc)
                    return render(
                        request,
                        "core/suggestion.html",
                        {
                            "form_error": error,
                            "form_data": form_data,
                            "recaptcha_enabled": settings.RECAPTCHA_ENABLED and not is_authenticated(request),
                            "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
                        },
                    )
                MarketSuggestion.objects.create(
                    author=_session_model_user(request),
                    guest_name="" if is_authenticated(request) else payload["guest_name"].strip(),
                    guest_email="" if is_authenticated(request) else (payload["guest_email"] or "").lower(),
                    question=payload["question"].strip(),
                    category=payload["category"].strip(),
                    kind="binary",
                    suggested_source=payload["suggested_source"].strip(),
                    rationale=payload["rationale"].strip(),
                )
                messages.success(request, "Sugestão enviada para a fila editorial.")
                return redirect("home")
            error = str(exc)
    return render(
        request,
        "core/suggestion.html",
        {
            "form_error": error,
            "form_data": form_data,
            "recaptcha_enabled": settings.RECAPTCHA_ENABLED and not is_authenticated(request),
            "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
        },
    )


def feedback(request):
    error = ""
    form_data = {}
    if request.method == "POST":
        payload = {
            "guest_name": request.POST.get("guest_name", ""),
            "guest_email": request.POST.get("guest_email", "") or None,
            "feedback_type": request.POST.get("feedback_type", ""),
            "severity": "medium",
            "description": request.POST.get("description", ""),
            "recaptcha_token": request.POST.get("g-recaptcha-response", ""),
        }
        form_data = payload
        try:
            create_feedback(payload, token=auth_token(request) if is_authenticated(request) else None)
            messages.success(request, "Feedback enviado para a fila de produto.")
            return redirect("home")
        except AuthAPIError as exc:
            if _should_use_local_queue_fallback(exc):
                try:
                    _verify_guest_recaptcha(request)
                except AuthAPIError as fallback_exc:
                    error = str(fallback_exc)
                    return render(
                        request,
                        "core/feedback.html",
                        {
                            "form_error": error,
                            "form_data": form_data,
                            "recaptcha_enabled": settings.RECAPTCHA_ENABLED and not is_authenticated(request),
                            "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
                        },
                    )
                ProductFeedback.objects.create(
                    author=_session_model_user(request),
                    guest_name="" if is_authenticated(request) else payload["guest_name"].strip(),
                    guest_email="" if is_authenticated(request) else (payload["guest_email"] or "").lower(),
                    feedback_type=payload["feedback_type"].strip(),
                    severity="medium",
                    description=payload["description"].strip(),
                )
                messages.success(request, "Feedback enviado para a fila de produto.")
                return redirect("home")
            error = str(exc)
    return render(
        request,
        "core/feedback.html",
        {
            "form_error": error,
            "form_data": form_data,
            "recaptcha_enabled": settings.RECAPTCHA_ENABLED and not is_authenticated(request),
            "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
        },
    )


def share_market(request, slug):
    market = _load_share_market(slug)
    share = market_share_context(request, market)
    share["track_url"] = reverse("share-market-track", args=[slug])
    return render(request, "core/share_market.html", {"market": market, "share": share})


def share_market_image(request, slug):
    market = _load_share_market(slug)
    share = market_share_context(request, market)
    return _image_response(render_market_card(market, share))


def share_result(request, slug):
    market = _load_share_market(slug)
    viewer = _share_viewer(request)
    share = result_share_context(request, market, viewer)
    share["track_url"] = reverse("share-market-track", args=[slug])
    return render(request, "core/share_result.html", {"market": market, "share": share, "share_viewer": viewer})


def share_result_image(request, slug):
    market = _load_share_market(slug)
    viewer = _share_viewer(request)
    share = result_share_context(request, market, viewer)
    return _image_response(render_result_card(market, viewer, share))


@csrf_exempt
@require_POST
def share_market_track(request, slug):
    tracked = _track_market_share(slug)
    status_code = 200 if tracked else 404
    return JsonResponse({"tracked": tracked}, status=status_code)
