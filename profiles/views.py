from django.shortcuts import redirect, render

from accounts.api_client import AuthAPIError, get_activity, get_badge_catalog, get_badges, get_me, get_rankings, request_account_deletion, update_me
from accounts.forms import ProfileForm
from accounts.referrals import referral_card_context
from accounts.session import api_login_required
from accounts.session import auth_token, auth_user, clear_auth_session, is_authenticated, store_auth_session


LOAD_MORE_STEP = 10
RANKING_BADGE_LIMIT = 3


def _load_more_limit(raw_limit, total, step=LOAD_MORE_STEP):
    try:
        limit = int(raw_limit or step)
    except (TypeError, ValueError):
        limit = step
    if limit < step:
        limit = step
    if limit % step:
        limit = ((limit // step) + 1) * step
    return min(limit, total) if total else step


def _profile_form_initial(profile_data):
    user = profile_data.get("user") or {}
    handle = (user.get("handle", "") or "").lstrip("@")
    return {
        "display_name": user.get("display_name", ""),
        "handle": handle,
        "email": user.get("email", ""),
        "preferred_language": user.get("preferred_language", "pt-br"),
        "birth_date": profile_data.get("birth_date") or "",
        "sex": profile_data.get("sex") or "",
        "bio": profile_data.get("bio", ""),
    }


def _normalize_ranking_row(row):
    badges = list(row.get("badges") or [])
    try:
        badges_total = int(row.get("badges_total", len(badges)) or 0)
    except (TypeError, ValueError):
        badges_total = len(badges)
    visible_badges = badges[:RANKING_BADGE_LIMIT]
    return {
        **row,
        "badges": badges,
        "badges_total": badges_total,
        "visible_badges": visible_badges,
        "badge_overflow_count": max(badges_total - len(visible_badges), 0),
    }


@api_login_required
def profile(request):
    token = auth_token(request)
    form = None
    profile_error = ""
    profile_success = "Perfil atualizado." if request.GET.get("updated") == "1" else ""
    if request.method == "POST" and request.POST.get("action") == "update_profile":
        form = ProfileForm(request.POST)
        if form.is_valid():
            try:
                profile_data = update_me(token, form.cleaned_data)
                store_auth_session(request, {"user": profile_data["user"], "session": {"token": token}})
                profile_success = "Perfil atualizado."
            except AuthAPIError as exc:
                profile_error = str(exc)
        else:
            profile_error = "Revise os campos do perfil."
    elif request.method == "POST" and request.POST.get("action") == "delete_account":
        if request.POST.get("confirm_delete") == "on":
            try:
                request_account_deletion(token)
            except AuthAPIError:
                pass
            clear_auth_session(request)
            return redirect("home")
        profile_error = "Confirme a exclusão lógica para continuar."

    try:
        profile_data = get_me(token)
    except AuthAPIError:
        profile_data = None
    try:
        badges = get_badges(token)
    except AuthAPIError:
        try:
            badges = get_badge_catalog()
        except AuthAPIError:
            badges = []
    try:
        activity = get_activity(token)
    except AuthAPIError:
        activity = []
    if profile_data and form is None:
        form = ProfileForm(initial=_profile_form_initial(profile_data))
    return render(
        request,
        "profiles/profile.html",
        {
            "profile": profile_data,
            "form": form,
            "profile_error": profile_error,
            "profile_success": profile_success,
            "badges": badges,
            "activity": activity,
            "referral": referral_card_context(request, token),
        },
    )


def rankings(request):
    selected_category = request.GET.get("category", "").strip()
    selected_subcategory = request.GET.get("subcategory", "").strip() if selected_category else ""
    selected_event = request.GET.get("event", "").strip() if selected_category and selected_subcategory else ""
    ranking_error = ""
    try:
        ranking_payload = get_rankings(category=selected_category, subcategory=selected_subcategory, event=selected_event)
    except AuthAPIError as exc:
        ranking_error = str(exc)
        ranking_payload = {
            "rows": [],
            "categories": [],
            "selected_category": selected_category,
            "selected_subcategory": selected_subcategory,
            "selected_event": selected_event,
        }
    ranking_payload.setdefault("selected_category", selected_category)
    ranking_payload.setdefault("selected_subcategory", selected_subcategory)
    ranking_payload.setdefault("selected_event", selected_event)
    ranking_rows = [_normalize_ranking_row(row) for row in ranking_payload.get("rows", [])]
    viewer_handle = ""
    if is_authenticated(request):
        viewer_handle = (auth_user(request) or {}).get("handle", "")
        viewer_handle = viewer_handle if viewer_handle.startswith("@") else f"@{viewer_handle}"
    viewer_ranking = next((row for row in ranking_rows if row.get("handle") == viewer_handle), None)
    ranking_total = len(ranking_rows)
    ranking_limit = _load_more_limit(request.GET.get("limit"), ranking_total)
    ranking_visible = ranking_rows[:ranking_limit]
    return render(
        request,
        "profiles/rankings.html",
        {
            "ranking": list(ranking_visible),
            "ranking_total": ranking_total,
            "ranking_visible_count": len(ranking_visible),
            "ranking_has_more": len(ranking_visible) < ranking_total,
            "ranking_next_limit": ranking_limit + LOAD_MORE_STEP,
            "ranking_categories": ranking_payload.get("categories", []),
            "selected_category": ranking_payload.get("selected_category", selected_category),
            "selected_subcategory": ranking_payload.get("selected_subcategory", selected_subcategory),
            "selected_event": ranking_payload.get("selected_event", selected_event),
            "viewer_ranking": viewer_ranking,
            "ranking_error": ranking_error,
        },
    )
