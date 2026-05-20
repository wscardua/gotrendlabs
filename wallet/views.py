from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from accounts.api_client import AuthAPIError, create_wallet_recharge_request, get_ledger, get_me, get_wallet_recharge_requests
from accounts.session import api_login_required
from accounts.session import auth_token
from admin_ops.models import SiteConfig


@api_login_required
def wallet_home(request):
    token = auth_token(request)
    try:
        ledger = get_ledger(token)
    except AuthAPIError:
        ledger = {"wallet": {"available_oc": 0, "locked_oc": 0, "total_earned_oc": 0}, "entries": []}
    try:
        profile = get_me(token)
        ledger["reputation"] = profile.get("reputation", {})
    except AuthAPIError:
        ledger.setdefault("reputation", {})
    try:
        recharge_data = get_wallet_recharge_requests(token)
        recharge_requests = recharge_data.get("requests", [])
    except AuthAPIError as exc:
        recharge_requests = []
        ledger["recharge_error"] = str(exc)
    entries = ledger.get("entries", [])
    paginator = Paginator(entries, 10)
    entries_page = paginator.get_page(request.GET.get("ledger_page") or 1)
    recharge_min_balance = SiteConfig.get_solo().wallet_recharge_min_balance_oc
    available_oc = int(ledger.get("wallet", {}).get("available_oc") or 0)
    recharge_eligible = available_oc <= recharge_min_balance
    context = {
        **ledger,
        "entries": list(entries_page.object_list),
        "entries_page": entries_page,
        "recharge_requests": recharge_requests,
        "pending_recharge_request": next((item for item in recharge_requests if item.get("status") == "pending"), None),
        "recharge_min_balance": recharge_min_balance,
        "recharge_eligible": recharge_eligible,
    }
    return render(request, "wallet/wallet.html", context)


@api_login_required
def request_recharge(request):
    if request.method != "POST":
        return redirect("wallet")
    try:
        wallet = get_ledger(auth_token(request)).get("wallet", {})
        recharge_min_balance = SiteConfig.get_solo().wallet_recharge_min_balance_oc
        if int(wallet.get("available_oc") or 0) > recharge_min_balance:
            messages.error(request, f"Recarga disponível apenas para saldo disponível de até {recharge_min_balance} OC.")
            return redirect("wallet")
    except AuthAPIError:
        pass
    try:
        create_wallet_recharge_request(auth_token(request))
        messages.success(request, "Solicitação de recarga enviada para análise.")
    except AuthAPIError as exc:
        messages.error(request, str(exc))
    return redirect("wallet")
