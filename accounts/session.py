from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse

from accounts.api_client import AuthAPIError, get_session


TOKEN_KEY = "auth_api_token"
USER_KEY = "auth_api_user"


def store_auth_session(request, auth_response):
    request.session[TOKEN_KEY] = auth_response["session"]["token"]
    request.session[USER_KEY] = auth_response["user"]


def clear_auth_session(request):
    request.session.pop(TOKEN_KEY, None)
    request.session.pop(USER_KEY, None)


def auth_user(request):
    return request.session.get(USER_KEY)


def auth_token(request):
    return request.session.get(TOKEN_KEY)


def is_authenticated(request):
    return bool(auth_token(request) and auth_user(request))


def api_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if is_authenticated(request):
            return view_func(request, *args, **kwargs)
        return redirect(f"{reverse('login')}?next={request.get_full_path()}")

    return wrapper


def admin_api_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_authenticated(request):
            return redirect(f"{reverse('login')}?next={request.get_full_path()}")
        user = auth_user(request)
        if not user.get("is_staff"):
            try:
                session = get_session(auth_token(request))
            except AuthAPIError:
                session = None
            if session:
                request.session[USER_KEY] = session["user"]
                user = session["user"]
        if not user.get("is_staff"):
            return HttpResponseForbidden("Acesso administrativo restrito.")
        return view_func(request, *args, **kwargs)

    return wrapper
