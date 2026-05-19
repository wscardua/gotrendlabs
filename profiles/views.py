from django.shortcuts import render

from core.domain_client import get_domain_client


def profile(request):
    return render(request, "profiles/profile.html", {"ranking": get_domain_client().ranking()})


def rankings(request):
    return render(request, "profiles/rankings.html", {"ranking": get_domain_client().ranking()})
