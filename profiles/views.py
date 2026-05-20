from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from accounts.api_client import AuthAPIError, get_activity, get_badges, get_me, get_rankings, request_account_deletion, update_me
from accounts.forms import ProfileForm
from accounts.session import api_login_required
from accounts.session import auth_token, auth_user, clear_auth_session, is_authenticated, store_auth_session


def _profile_form_initial(profile_data):
    return {
        "display_name": profile_data["user"]["display_name"],
        "handle": profile_data["user"]["handle"],
        "email": profile_data["user"]["email"],
        "preferred_language": profile_data["user"]["preferred_language"],
        "birth_date": profile_data.get("birth_date") or "",
        "sex": profile_data.get("sex") or "",
        "bio": profile_data["bio"],
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
        badges = get_badges(token)
        activity = get_activity(token)
    except AuthAPIError:
        profile_data = None
        badges = []
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
        },
    )


def rankings(request):
    selected_category = request.GET.get("category", "").strip()
    selected_subcategory = request.GET.get("subcategory", "").strip() if selected_category else ""
    ranking_error = ""
    try:
        ranking_payload = get_rankings(category=selected_category, subcategory=selected_subcategory)
    except AuthAPIError as exc:
        ranking_error = str(exc)
        ranking_payload = {
            "rows": [],
            "categories": [],
            "selected_category": selected_category,
            "selected_subcategory": selected_subcategory,
        }
    ranking_payload.setdefault("selected_category", selected_category)
    ranking_payload.setdefault("selected_subcategory", selected_subcategory)
    ranking_rows = ranking_payload.get("rows", [])
    viewer_handle = ""
    if is_authenticated(request):
        viewer_handle = (auth_user(request) or {}).get("handle", "")
        viewer_handle = viewer_handle if viewer_handle.startswith("@") else f"@{viewer_handle}"
    viewer_ranking = next((row for row in ranking_rows if row.get("handle") == viewer_handle), None)
    ranking_page = Paginator(ranking_rows, 10).get_page(request.GET.get("page") or 1)
    return render(
        request,
        "profiles/rankings.html",
        {
            "ranking": list(ranking_page.object_list),
            "ranking_page": ranking_page,
            "ranking_categories": ranking_payload.get("categories", []),
            "selected_category": ranking_payload.get("selected_category", selected_category),
            "selected_subcategory": ranking_payload.get("selected_subcategory", selected_subcategory),
            "viewer_ranking": viewer_ranking,
            "ranking_error": ranking_error,
        },
    )
