from django.shortcuts import render

from core.domain_client import get_domain_client


def dashboard(request):
    return render(request, "admin_ops/dashboard.html", {"admin_summary": get_domain_client().admin_summary()})
