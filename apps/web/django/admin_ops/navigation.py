"""Shared navigation only; access to every destination remains API-authorized."""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

GROUPS = (
    (
        _("Visão geral"),
        (
            (_("Dashboard"), "admin-ops-dashboard", ("admin-ops-dashboard",)),
            (_("Analytics"), "admin-ops-analytics", ("admin-ops-analytics",)),
        ),
    ),
    (
        _("Mercados e editorial"),
        (
            (_("Mercados"), "admin-ops-markets", ("admin-ops-market",)),
            (_("Resolução"), "admin-ops-resolution", ("admin-ops-resolution",)),
            (_("Manual editorial"), "admin-ops-editorial", ("admin-ops-editorial",)),
            (
                _("Revisão editorial"),
                "admin-ops-agent-reviews",
                ("admin-ops-agent-review",),
            ),
            (
                _("Categorias e eventos"),
                "admin-ops-taxonomy",
                ("admin-ops-taxonomy", "admin-ops-category"),
            ),
            (_("Badges"), "admin-ops-badges", ("admin-ops-badge",)),
        ),
    ),
    (
        _("Pessoas e automação"),
        (
            (_("Usuários"), "admin-ops-users", ("admin-ops-user",)),
            (
                _("Filas operacionais"),
                "admin-ops-moderation",
                ("admin-ops-moderation", "admin-ops-queue"),
            ),
            (_("Integrações"), "admin-ops-integrations", ("admin-ops-integration",)),
            (_("Agentes IA"), "admin-ops-ai-agents", ("admin-ops-ai-agent",)),
        ),
    ),
    (
        _("Comunicações"),
        (
            (_("Emails"), "admin-ops-email-templates", ("admin-ops-email-",)),
            (_("Push mobile"), "admin-ops-push-templates", ("admin-ops-push-",)),
        ),
    ),
    (
        _("Plataforma"),
        (
            (_("Configurações"), "admin-ops-config", ("admin-ops-config",)),
            (
                _("App Android"),
                "admin-ops-mobile-releases",
                ("admin-ops-mobile-release",),
            ),
            (_("Logs do sistema"), "admin-ops-system-logs", ("admin-ops-system-log",)),
            (_("Contratos da API"), "admin-ops-contracts", ("admin-ops-contracts",)),
        ),
    ),
)


def admin_navigation(request):
    route = getattr(getattr(request, "resolver_match", None), "url_name", "") or ""
    if not route.startswith("admin-ops-"):
        return {}
    groups = []
    for title, entries in GROUPS:
        links = [
            {
                "label": label,
                "url": reverse(destination),
                "active": route.startswith(prefixes),
            }
            for label, destination, prefixes in entries
        ]
        groups.append({"title": title, "links": links})
    return {"admin_navigation": groups}
