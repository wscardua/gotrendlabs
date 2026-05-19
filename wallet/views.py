from django.shortcuts import render

from core.domain_client import get_domain_client


def wallet_home(request):
    return render(request, "wallet/wallet.html", {"ledger": get_domain_client().ledger()})
