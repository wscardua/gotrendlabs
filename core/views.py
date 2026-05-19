from django.shortcuts import render

from core.domain_client import get_domain_client


def home(request):
    client = get_domain_client()
    return render(
        request,
        "core/home.html",
        {
            "markets": client.markets(),
            "stats": client.stats(),
            "ranking": client.ranking()[:3],
        },
    )


def concepts(request):
    return render(request, "core/concepts.html")


def categories(request):
    return render(request, "core/categories.html", {"markets": get_domain_client().markets()})


def security(request):
    return render(request, "core/security.html")


def suggestion(request):
    return render(request, "core/simple_panel.html", {"eyebrow": "Comunidade", "title": "Sugerir mercado", "body": "Fluxo visual para sugestao de mercado, pronto para conectar ao backend-api."})


def feedback(request):
    return render(request, "core/simple_panel.html", {"eyebrow": "Feedback", "title": "Enviar feedback", "body": "Canal visual para feedback do MVP."})
