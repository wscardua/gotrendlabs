from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.api_client import AuthAPIError, create_wallet_recharge_request, get_ledger, get_me, get_wallet_recharge_requests
from accounts.referrals import referral_card_context
from accounts.session import api_login_required
from accounts.session import auth_token
from admin_ops.models import SiteConfig


LOAD_MORE_STEP = 10


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


@api_login_required
def wallet_home(request):
    token = auth_token(request)
    try:
        ledger = get_ledger(token)
    except AuthAPIError:
        ledger = {"wallet": {"available_gtl": 0, "locked_gtl": 0, "total_earned_gtl": 0}, "entries": []}
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
    entries_total = len(entries)
    entries_limit = _load_more_limit(request.GET.get("ledger_limit"), entries_total)
    visible_entries = entries[:entries_limit]
    recharge_min_balance = SiteConfig.get_solo().wallet_recharge_min_balance_gtl
    available_gtl = int(ledger.get("wallet", {}).get("available_gtl") or 0)
    recharge_eligible = available_gtl <= recharge_min_balance
    context = {
        **ledger,
        "entries": list(visible_entries),
        "entries_total": entries_total,
        "entries_visible_count": len(visible_entries),
        "entries_has_more": len(visible_entries) < entries_total,
        "entries_next_limit": entries_limit + LOAD_MORE_STEP,
        "recharge_requests": recharge_requests,
        "pending_recharge_request": next((item for item in recharge_requests if item.get("status") == "pending"), None),
        "recharge_min_balance": recharge_min_balance,
        "recharge_eligible": recharge_eligible,
        "referral": referral_card_context(request, token),
    }
    return render(request, "wallet/wallet.html", context)


@api_login_required
def request_recharge(request):
    if request.method != "POST":
        return redirect("wallet")
    try:
        wallet = get_ledger(auth_token(request)).get("wallet", {})
        recharge_min_balance = SiteConfig.get_solo().wallet_recharge_min_balance_gtl
        if int(wallet.get("available_gtl") or 0) > recharge_min_balance:
            messages.error(request, f"Recarga disponível apenas para saldo disponível de até {recharge_min_balance} GT₵.")
            return redirect("wallet")
    except AuthAPIError:
        pass
    try:
        create_wallet_recharge_request(auth_token(request))
        messages.success(request, "Solicitação de recarga enviada para análise.")
    except AuthAPIError as exc:
        messages.error(request, str(exc))
    return redirect("wallet")
