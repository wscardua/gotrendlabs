from django.shortcuts import render

from accounts.api_client import AuthAPIError, get_ledger, get_me
from accounts.session import api_login_required
from accounts.session import auth_token


@api_login_required
def wallet_home(request):
    try:
        ledger = get_ledger(auth_token(request))
    except AuthAPIError:
        ledger = {"wallet": {"available_oc": 0, "locked_oc": 0, "total_earned_oc": 0}, "entries": []}
    try:
        profile = get_me(auth_token(request))
        ledger["reputation"] = profile.get("reputation", {})
    except AuthAPIError:
        ledger.setdefault("reputation", {})
    return render(request, "wallet/wallet.html", ledger)
