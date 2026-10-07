from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve
from apps.web.django.admin_ops.navigation import admin_navigation


class AdminNavigationTests(SimpleTestCase):
    def test_nested_destinations_have_one_current_area(self):
        cases = (
            ("/admin-ops/", "/admin-ops/"),
            ("/admin-ops/markets/sample/edit/", "/admin-ops/markets/"),
            ("/admin-ops/resolution/sample/publish/", "/admin-ops/resolution/"),
            ("/admin-ops/queues/suggestion/1/approve/", "/admin-ops/moderation/"),
            (
                "/admin-ops/integrations/00000000-0000-0000-0000-000000000001/",
                "/admin-ops/integrations/",
            ),
            ("/admin-ops/agent-reviews/1/", "/admin-ops/agent-reviews/"),
            ("/admin-ops/email-templates/1/", "/admin-ops/email-policy/"),
            ("/admin-ops/push-policy/devices/", "/admin-ops/push-policy/"),
            ("/admin-ops/ai-agent-actions/1/", "/admin-ops/ai-agents/"),
            ("/admin-ops/users/1/", "/admin-ops/users/"),
            ("/admin-ops/taxonomy/block/", "/admin-ops/taxonomy/"),
            ("/admin-ops/badges/test/edit/", "/admin-ops/badges/"),
            ("/admin-ops/logs/1/", "/admin-ops/logs/"),
        )
        for path, expected in cases:
            with self.subTest(path=path):
                request = RequestFactory().get(path)
                request.resolver_match = resolve(path)
                context = admin_navigation(request)
                current = [
                    link
                    for group in context["admin_navigation"]
                    for link in group["links"]
                    if link["active"]
                ]
                self.assertEqual([link["url"] for link in current], [expected])
                rendered = render_to_string(
                    "admin_ops/partials/navigation.html", context
                )
                self.assertEqual(rendered.count('aria-current="page"'), 1)

    def test_public_pages_do_not_receive_admin_navigation(self):
        request = RequestFactory().get("/login/")
        request.resolver_match = resolve("/login/")
        self.assertEqual(admin_navigation(request), {})
