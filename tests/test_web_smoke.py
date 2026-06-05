from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO
import importlib
import json
import logging
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unicodedata
from urllib.parse import quote, urlparse

from django.conf import settings
from django.core.management import call_command
from django.contrib.staticfiles import finders
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from fastapi.testclient import TestClient
from unittest.mock import patch

from accounts.api_client import AuthAPIError, get_market as api_get_market, get_markets as api_get_markets
from accounts.models import AuthEvent, BadgeDefinition, BadgeRule, PasswordResetToken, UserBadgeAward, UserReputation, WalletBalance, WalletLedgerEntry, WalletRechargeRequest
from accounts.session import TOKEN_KEY, USER_KEY
from admin_ops.models import SiteConfig
from backend_api.db import get_connection
from backend_api.db import database_config
from agents.models import AiAgent, AiAgentAction
from backend_api.agent_prompts import build_comment_prompt
from backend_api.agent_services import _safe_comment_text, ai_health_summary, run_ai_agent_cycle
from backend_api.agent_llm import AgentLLMError, _extract_output_text, request_market_comment
from backend_api.badge_engine import BadgeAwardEngine
from backend_api.daemon_services import AUTO_CANCEL_NO_HUMANS_NOTE, AUTO_CLOSE_NOTE, close_due_auto_markets, daemon_dashboard_status, prune_expired_operational_records, prune_expired_system_logs
from backend_api.daemon_services import _locked_markets_message
from backend_api.main import app
from backend_api.main import _ensure_user_core
from backend_api.main import _record_wallet_entry
from config.recaptcha import RecaptchaError
from communications.models import EmailConfirmationToken, EmailDelivery, EmailTemplate
from communications.services import DEFAULT_EMAIL_TEMPLATES, process_due_email_deliveries, render_template
from core.domain_client import get_domain_client
from core.platform_config import load_platform_config, save_platform_config
from core.social_share import public_badge_share_token
from markets.models import AdminEvent, CommentReaction, Market, MarketCategory, MarketComment, MarketEvent, MarketFavorite, MarketLike, MarketOption, MarketSubcategory, MarketSuggestion, Prediction, ProductFeedback, UserNotification
from system_logs.models import SystemLog
from system_logs.services import log_system_event


def _fixture_slug(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "geral"


def _seed_test_markets():
    fixture_path = Path(settings.BASE_DIR) / "data" / "fixtures" / "domain.json"
    with fixture_path.open(encoding="utf-8") as fixture:
        markets = json.load(fixture)["markets"]

    for index, payload in enumerate(markets, start=1):
        category, _ = MarketCategory.objects.update_or_create(
            slug=_fixture_slug(payload["category"]),
            defaults={"name": payload["category"]},
        )
        subcategory, _ = MarketSubcategory.objects.update_or_create(
            category=category,
            slug=_fixture_slug(payload["subcategory"]),
            defaults={"name": payload["subcategory"]},
        )
        market, _ = Market.objects.update_or_create(
            slug=payload["slug"],
            defaults={
                "category": category,
                "subcategory": subcategory,
                "title": payload["title"],
                "summary": payload.get("summary", ""),
                "kind": payload["kind"],
                "status": payload["status"],
                "status_label": payload.get("status_label", payload["status"]),
                "primary_outcome": payload.get("primary_outcome", ""),
                "primary_probability_exact": payload.get("primary_probability_exact", payload.get("primary_probability", 0)),
                "secondary_probability_exact": payload.get("secondary_probability_exact", payload.get("secondary_probability", 0)),
                "volume_gtl": payload.get("volume_gtl", ""),
                "participants": payload.get("participants", ""),
                "source": payload.get("source", ""),
                "closes_in": payload.get("closes_in", ""),
                "close_label": payload.get("close_label", ""),
                "thumb": payload.get("thumb", ""),
                "thumb_color": payload.get("thumb_color", ""),
                "image_url": payload.get("image_url", ""),
                "resolution_criteria": payload.get("resolution_criteria", ""),
                "resolution_type": payload.get("resolution_type", ""),
                "resolution_note": payload.get("resolution_note", ""),
                "is_featured": payload.get("is_featured", False),
                "display_order": index,
            },
        )
        for option_index, option in enumerate(payload.get("options", []), start=1):
            MarketOption.objects.update_or_create(
                market=market,
                label=option["label"],
                defaults={
                    "probability_exact": option.get("probability_exact", option.get("probability", 0)),
                    "hint": option.get("hint", ""),
                    "display_order": option_index,
                },
            )


def _seed_test_badges():
    badge_seed = importlib.import_module("accounts.migrations.0009_badgedefinition_userbadgeaward_badgerule_and_more")
    for item in badge_seed.DEFAULT_BADGES:
        badge, _ = BadgeDefinition.objects.update_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "description": item["description"],
                "rule_description": item["rule_description"],
                "badge_type": item["badge_type"],
                "is_active": True,
            },
        )
        BadgeRule.objects.update_or_create(
            badge=badge,
            defaults={
                "rule_type": item["rule_type"],
                "threshold_value": item["threshold_value"],
                "category": "",
                "subcategory": "",
                "is_active": True,
            },
            )


def _seed_test_email_templates():
    for key, locales in DEFAULT_EMAIL_TEMPLATES.items():
        for locale, payload in locales.items():
            EmailTemplate.objects.update_or_create(
                key=key,
                locale=locale,
                defaults={
                    "subject": payload["subject"],
                    "body_text": payload["body_text"],
                    "body_html": payload.get("body_html", ""),
                    "is_active": True,
                },
            )


class FixtureDomainClientTests(TestCase):
    def test_market_fixture_contract_has_expected_fields(self):
        market = get_domain_client().market("openai-gpt6-2026")

        self.assertEqual(market["status"], "open")
        self.assertIn("options", market)
        self.assertIn("resolution_criteria", market)
        self.assertIn("probability_exact", market["options"][0])
        self.assertGreaterEqual(len(market["options"]), 2)

    def test_api_client_normalizes_legacy_gtl_volume_labels(self):
        with patch("accounts.api_client._request", return_value={"slug": "legacy", "volume_gtl": "1355 GTL"}):
            self.assertEqual(api_get_market("legacy")["volume_gtl"], "1355 GT₵")

        with patch("accounts.api_client._request", return_value={"markets": [{"slug": "legacy", "volume_gtl": "1355 GTL"}]}):
            self.assertEqual(api_get_markets()[0]["volume_gtl"], "1355 GT₵")


class BackendAuthAPITests(TransactionTestCase):
    def setUp(self):
        _seed_test_badges()
        _seed_test_markets()
        _seed_test_email_templates()

    def _reset_ai_agent_state(self):
        AiAgentAction.objects.all().delete()
        AiAgent.objects.all().delete()
        MarketComment.objects.filter(author__is_bot=True).delete()

    def _fastapi_test_db_env(self):
        return {
            "FASTAPI_POSTGRES_DB": "",
            "FASTAPI_POSTGRES_USER": "",
            "FASTAPI_POSTGRES_PASSWORD": "",
            "FASTAPI_POSTGRES_HOST": "",
            "FASTAPI_POSTGRES_PORT": "",
        }

    def _run_ai_cycle_for_test(self, now=None):
        with patch.dict(os.environ, self._fastapi_test_db_env()):
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    return run_ai_agent_cycle(cursor, now=now or timezone.now())

    def _ai_health_for_test(self, now=None):
        with patch.dict(os.environ, self._fastapi_test_db_env()):
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    return ai_health_summary(cursor, now=now or timezone.now())

    def test_social_auth_placeholder_supports_initial_providers(self):
        client = TestClient(app)

        for provider in ("google", "facebook", "x"):
            response = client.post(f"/auth/social/{provider}")
            self.assertEqual(response.status_code, 501)

        unsupported = client.post("/auth/social/apple")
        self.assertEqual(unsupported.status_code, 404)

    def test_system_log_model_defaults_retention_and_context(self):
        log = SystemLog.objects.create(
            level="INFO",
            source="django",
            event_type="request",
            message="Modelo de log operacional",
            context={"request_id": "model-smoke"},
        )
        self.assertEqual(log.context["request_id"], "model-smoke")
        self.assertGreater(log.expires_at, timezone.now() + timedelta(days=89))

    def test_market_api_seed_filters_and_detail_contract(self):
        self.assertEqual(Market.objects.filter(slug="openai-gpt6-2026").count(), 1)
        self.assertTrue(MarketEvent.objects.filter(name="Geral", subcategory__name="Modelos").exists())
        self.assertGreaterEqual(MarketOption.objects.filter(market__slug="openai-gpt6-2026").count(), 2)
        Market.objects.filter(slug="tiktok-ban-eua-2026").update(status="canceled", status_label="Cancelado")

        client = TestClient(app)
        listing = client.get("/markets")
        self.assertEqual(listing.status_code, 200)
        markets = listing.json()["markets"]
        self.assertIn("openai-gpt6-2026", [market["slug"] for market in markets])
        self.assertNotIn("draft", [market["status"] for market in markets])
        self.assertNotIn("canceled", [market["status"] for market in markets])
        self.assertIn("created_at", markets[0])
        self.assertEqual(markets[0]["event"], "Geral")
        self.assertEqual(markets[0]["category_notice"], "")
        self.assertEqual(markets[0]["subcategory_notice"], "")
        self.assertEqual(markets[0]["event_notice"], "")

        open_markets = client.get("/markets", params={"status": "open"})
        self.assertEqual(open_markets.status_code, 200)
        self.assertTrue(all(market["status"] == "open" for market in open_markets.json()["markets"]))

        category_markets = client.get("/markets", params={"category": "IA", "subcategory": "Modelos"})
        self.assertEqual(category_markets.status_code, 200)
        self.assertEqual(category_markets.json()["markets"][0]["category"], "IA")
        self.assertEqual(category_markets.json()["markets"][0]["subcategory"], "Modelos")

        detail = client.get("/markets/openai-gpt6-2026")
        self.assertEqual(detail.status_code, 200)
        payload = detail.json()
        self.assertEqual(payload["slug"], "openai-gpt6-2026")
        self.assertEqual(payload["event"], "Geral")
        self.assertEqual(payload["category_notice"], "")
        self.assertEqual(payload["subcategory_notice"], "")
        self.assertEqual(payload["event_notice"], "")
        self.assertIn("resolution_criteria", payload)
        self.assertIn("view_count", payload)
        self.assertIn("share_count", payload)
        self.assertGreaterEqual(len(payload["options"]), 2)
        self.assertIn("comments", payload)
        self.assertIsInstance(payload["comments"], list)

        missing = client.get("/markets/mercado-inexistente")
        self.assertEqual(missing.status_code, 404)

    def test_market_listing_marks_viewer_predictions_when_authenticated(self):
        client = TestClient(app)
        register = client.post(
            "/auth/register",
            json={
                "display_name": "Feed Prediction User",
                "email": "feed-prediction-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(register.status_code, 201)
        headers = {"Authorization": f"Bearer {register.json()['session']['token']}"}
        option = MarketOption.objects.get(market__slug="openai-gpt6-2026", label="SIM")

        prediction = client.post(
            "/markets/openai-gpt6-2026/predict",
            headers=headers,
            json={"option_id": option.id, "stake_amount": 80, "client_locale": "pt-br"},
        )
        self.assertEqual(prediction.status_code, 201)

        authenticated_listing = client.get("/markets", headers=headers)
        self.assertEqual(authenticated_listing.status_code, 200)
        predicted_market = next(market for market in authenticated_listing.json()["markets"] if market["slug"] == "openai-gpt6-2026")
        self.assertTrue(predicted_market["viewer_has_prediction"])

        guest_listing = client.get("/markets")
        guest_market = next(market for market in guest_listing.json()["markets"] if market["slug"] == "openai-gpt6-2026")
        self.assertFalse(guest_market["viewer_has_prediction"])

    def test_market_favorites_api_is_personal_and_idempotent(self):
        client = TestClient(app)
        register = client.post(
            "/auth/register",
            json={
                "display_name": "Favorite User",
                "email": "favorite-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(register.status_code, 201)
        headers = {"Authorization": f"Bearer {register.json()['session']['token']}"}

        guest_listing = client.get("/markets")
        guest_market = next(market for market in guest_listing.json()["markets"] if market["slug"] == "openai-gpt6-2026")
        self.assertFalse(guest_market["viewer_has_favorite"])

        favorite = client.post("/markets/openai-gpt6-2026/favorite", headers=headers)
        self.assertEqual(favorite.status_code, 200)
        self.assertTrue(favorite.json()["viewer_has_favorite"])
        second_favorite = client.post("/markets/openai-gpt6-2026/favorite", headers=headers)
        self.assertEqual(second_favorite.status_code, 200)
        self.assertEqual(MarketFavorite.objects.filter(market__slug="openai-gpt6-2026").count(), 1)

        authenticated_listing = client.get("/markets", headers=headers)
        favorite_market = next(market for market in authenticated_listing.json()["markets"] if market["slug"] == "openai-gpt6-2026")
        self.assertTrue(favorite_market["viewer_has_favorite"])

        unfavorite = client.delete("/markets/openai-gpt6-2026/favorite", headers=headers)
        self.assertEqual(unfavorite.status_code, 200)
        self.assertFalse(unfavorite.json()["viewer_has_favorite"])
        second_unfavorite = client.delete("/markets/openai-gpt6-2026/favorite", headers=headers)
        self.assertEqual(second_unfavorite.status_code, 200)
        self.assertEqual(MarketFavorite.objects.filter(market__slug="openai-gpt6-2026").count(), 0)

    def test_market_likes_api_is_personal_idempotent_and_separate_from_comment_likes(self):
        client = TestClient(app)
        first = client.post(
            "/auth/register",
            json={
                "display_name": "Like User",
                "email": "like-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        second = client.post(
            "/auth/register",
            json={
                "display_name": "Second Like User",
                "email": "second-like-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        first_headers = {"Authorization": f"Bearer {first.json()['session']['token']}"}
        second_headers = {"Authorization": f"Bearer {second.json()['session']['token']}"}
        market = Market.objects.get(slug="openai-gpt6-2026")
        comment = MarketComment.objects.create(market=market, author_id=first.json()["user"]["id"], body="Comentário com like.")
        CommentReaction.objects.create(comment=comment, user_id=second.json()["user"]["id"], reaction="like")

        guest_market = next(market for market in client.get("/markets").json()["markets"] if market["slug"] == "openai-gpt6-2026")
        self.assertFalse(guest_market["viewer_has_like"])
        self.assertEqual(guest_market["market_like_count"], 0)

        like = client.post("/markets/openai-gpt6-2026/like", headers=first_headers)
        self.assertEqual(like.status_code, 200)
        self.assertTrue(like.json()["viewer_has_like"])
        self.assertEqual(like.json()["market_like_count"], 1)
        second_like = client.post("/markets/openai-gpt6-2026/like", headers=first_headers)
        self.assertEqual(second_like.status_code, 200)
        self.assertEqual(second_like.json()["market_like_count"], 1)
        self.assertEqual(MarketLike.objects.filter(market__slug="openai-gpt6-2026").count(), 1)

        other_like = client.post("/markets/openai-gpt6-2026/like", headers=second_headers)
        self.assertEqual(other_like.status_code, 200)
        self.assertEqual(other_like.json()["market_like_count"], 2)

        authenticated_listing = client.get("/markets", headers=first_headers)
        liked_market = next(market for market in authenticated_listing.json()["markets"] if market["slug"] == "openai-gpt6-2026")
        self.assertTrue(liked_market["viewer_has_like"])
        self.assertEqual(liked_market["market_like_count"], 2)

        unlike = client.delete("/markets/openai-gpt6-2026/like", headers=first_headers)
        self.assertEqual(unlike.status_code, 200)
        self.assertFalse(unlike.json()["viewer_has_like"])
        self.assertEqual(unlike.json()["market_like_count"], 1)
        second_unlike = client.delete("/markets/openai-gpt6-2026/like", headers=first_headers)
        self.assertEqual(second_unlike.status_code, 200)
        self.assertEqual(second_unlike.json()["market_like_count"], 1)

    def test_market_comment_count_and_notifications_contract(self):
        client = TestClient(app)
        first = client.post(
            "/auth/register",
            json={
                "display_name": "Notification First",
                "email": "notification-first@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        second = client.post(
            "/auth/register",
            json={
                "display_name": "Notification Second",
                "email": "notification-second@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        first_headers = {"Authorization": f"Bearer {first.json()['session']['token']}"}
        second_headers = {"Authorization": f"Bearer {second.json()['session']['token']}"}
        market = Market.objects.get(slug="openai-gpt6-2026")
        option = MarketOption.objects.get(market=market, label="SIM")
        hidden_comment = MarketComment.objects.create(market=market, author_id=first.json()["user"]["id"], body="Oculto", status="hidden")
        visible_comment = MarketComment.objects.create(market=market, author_id=first.json()["user"]["id"], body="Visível")

        detail = client.get("/markets/openai-gpt6-2026")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["comment_count"], 1)
        listing_market = next(item for item in client.get("/markets").json()["markets"] if item["slug"] == "openai-gpt6-2026")
        self.assertEqual(listing_market["comment_count"], 1)
        self.assertNotIn(hidden_comment.id, [item["id"] for item in detail.json()["comments"]])
        self.assertIn(visible_comment.id, [item["id"] for item in detail.json()["comments"]])

        first_prediction = client.post(
            "/markets/openai-gpt6-2026/predict",
            headers=first_headers,
            json={"option_id": option.id, "stake_amount": 80, "client_locale": "pt-br"},
        )
        self.assertEqual(first_prediction.status_code, 201)
        second_prediction = client.post(
            "/markets/openai-gpt6-2026/predict",
            headers=second_headers,
            json={"option_id": option.id, "stake_amount": 80, "client_locale": "pt-br"},
        )
        self.assertEqual(second_prediction.status_code, 201)
        self.assertTrue(UserNotification.objects.filter(recipient_id=first.json()["user"]["id"], event_type="market_prediction").exists())

        liked = client.post("/markets/openai-gpt6-2026/like", headers=second_headers)
        self.assertEqual(liked.status_code, 200)
        liked_again = client.post("/markets/openai-gpt6-2026/like", headers=second_headers)
        self.assertEqual(liked_again.status_code, 200)
        self.assertEqual(
            UserNotification.objects.filter(recipient_id=first.json()["user"]["id"], event_type="market_like").count(),
            1,
        )

        comment = client.post(
            "/markets/openai-gpt6-2026/comments",
            headers=second_headers,
            json={"body": "Comentário que notifica participantes."},
        )
        self.assertEqual(comment.status_code, 201)
        self.assertTrue(UserNotification.objects.filter(recipient_id=first.json()["user"]["id"], event_type="market_comment").exists())

        comment_like = client.post(f"/comments/{visible_comment.id}/like", headers=second_headers)
        self.assertEqual(comment_like.status_code, 200)
        self.assertEqual(
            UserNotification.objects.filter(recipient_id=first.json()["user"]["id"], event_type="comment_like").count(),
            1,
        )
        self.assertFalse(UserNotification.objects.filter(recipient_id=second.json()["user"]["id"], actor_id=second.json()["user"]["id"]).exists())

        inbox = client.get("/users/me/notifications", headers=first_headers)
        self.assertEqual(inbox.status_code, 200)
        self.assertGreaterEqual(inbox.json()["unread_count"], 4)
        self.assertGreaterEqual(len(inbox.json()["notifications"]), 4)

        read_all = client.post("/users/me/notifications/read-all", headers=first_headers)
        self.assertEqual(read_all.status_code, 200)
        self.assertEqual(read_all.json()["unread_count"], 0)
        self.assertFalse(UserNotification.objects.filter(recipient_id=first.json()["user"]["id"], is_read=False).exists())

    def test_market_popularity_api_tracks_views_and_shares(self):
        client = TestClient(app)
        initial = client.get("/markets/openai-gpt6-2026").json()
        initial_views = initial["view_count"]
        initial_shares = initial["share_count"]

        viewed = client.post("/markets/openai-gpt6-2026/view")
        self.assertEqual(viewed.status_code, 200)
        self.assertEqual(viewed.json()["view_count"], initial_views + 1)
        self.assertEqual(viewed.json()["share_count"], initial_shares)

        shared = client.post("/markets/openai-gpt6-2026/share")
        self.assertEqual(shared.status_code, 200)
        self.assertEqual(shared.json()["view_count"], initial_views + 1)
        self.assertEqual(shared.json()["share_count"], initial_shares + 1)

        detail = client.get("/markets/openai-gpt6-2026")
        self.assertEqual(detail.json()["view_count"], initial_views + 1)
        self.assertEqual(detail.json()["share_count"], initial_shares + 1)

        staff_email = f"metrics-staff-{initial_views}-{initial_shares}@example.com"
        user = client.post(
            "/auth/register",
            json={"display_name": "Metrics Staff", "email": staff_email, "password": "testpass123", "terms_accepted": True},
        )
        self.assertEqual(user.status_code, 201)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", (staff_email,))
        admin_markets = client.get("/admin/markets", headers={"Authorization": f"Bearer {user.json()['session']['token']}"})
        self.assertEqual(admin_markets.status_code, 200)
        admin_market = next(item for item in admin_markets.json()["markets"] if item["slug"] == "openai-gpt6-2026")
        self.assertEqual(admin_market["view_count"], initial_views + 1)
        self.assertEqual(admin_market["share_count"], initial_shares + 1)

        missing = client.post("/markets/mercado-inexistente/view")
        self.assertEqual(missing.status_code, 404)

    def test_register_session_and_logout_contract(self):
        client = TestClient(app)

        response = client.post(
            "/auth/register",
            json={
                "display_name": "Carol Vision",
                "email": "carol-api@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["user"]["handle"], "@carolvision")
        self.assertIn("token", payload["session"])

        session_response = client.get(
            "/auth/session",
            headers={"Authorization": f"Bearer {payload['session']['token']}"},
        )
        self.assertEqual(session_response.status_code, 200)
        self.assertEqual(session_response.json()["user"]["email"], "carol-api@example.com")

        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {payload['session']['token']}"},
        )
        self.assertEqual(logout_response.status_code, 204)

        revoked_response = client.get(
            "/auth/session",
            headers={"Authorization": f"Bearer {payload['session']['token']}"},
        )
        self.assertEqual(revoked_response.status_code, 401)

    def test_admin_user_management_contracts_audit_wallet_and_sessions(self):
        client = TestClient(app)
        staff = client.post(
            "/auth/register",
            json={"display_name": "User Admin Staff", "email": "user-admin-staff@example.com", "password": "testpass123", "terms_accepted": True},
        )
        target = client.post(
            "/auth/register",
            json={"display_name": "Managed User", "email": "managed-user@example.com", "password": "testpass123", "terms_accepted": True},
        )
        self.assertEqual(staff.status_code, 201)
        self.assertEqual(target.status_code, 201)
        staff_headers = {"Authorization": f"Bearer {staff.json()['session']['token']}"}
        target_headers = {"Authorization": f"Bearer {target.json()['session']['token']}"}
        staff_id = staff.json()["user"]["id"]
        target_id = target.json()["user"]["id"]
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("user-admin-staff@example.com",))

        forbidden = client.get("/admin/users", headers=target_headers)
        self.assertEqual(forbidden.status_code, 403)

        listing = client.get("/admin/users", headers=staff_headers, params={"q": "managed", "status": "active", "role": "user", "order": "wallet_desc"})
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()["users"][0]["email"], "managed-user@example.com")
        self.assertIn("counts", listing.json())

        detail = client.get(f"/admin/users/{target_id}", headers=staff_headers)
        self.assertEqual(detail.status_code, 200)
        payload = detail.json()
        self.assertEqual(payload["user"]["handle"], "@manageduser")
        self.assertFalse(payload["user"]["is_bot"])
        self.assertEqual(payload["wallet"]["available_gtl"], 2000)
        self.assertIn("sessions", payload)
        self.assertIn("auth_events", payload)

        marked_bot = client.post(
            f"/admin/users/{target_id}/bot",
            headers=staff_headers,
            json={"is_bot": True, "note": "Conta controlada por robô interno"},
        )
        self.assertEqual(marked_bot.status_code, 200)
        self.assertTrue(marked_bot.json()["user"]["is_bot"])
        self.assertTrue(AdminEvent.objects.filter(action="user.bot_update", entity_identifier=str(target_id)).exists())
        bot_listing = client.get("/admin/users", headers=staff_headers, params={"bot": "yes"})
        self.assertEqual(bot_listing.status_code, 200)
        self.assertIn("managed-user@example.com", [user["email"] for user in bot_listing.json()["users"]])

        credit = client.post(
            f"/admin/users/{target_id}/wallet/adjust",
            headers=staff_headers,
            json={"direction": "credit", "amount_gtl": 75, "note": "Crédito de suporte"},
        )
        self.assertEqual(credit.status_code, 200)
        self.assertEqual(credit.json()["wallet"]["available_gtl"], 2075)
        self.assertTrue(
            WalletLedgerEntry.objects.filter(
                user_id=target_id,
                entry_type="manual_adjustment",
                direction="credit",
                amount=75,
                reference_type="admin_user_adjustment",
                reference_id=str(target_id),
            ).exists()
        )
        self.assertTrue(AdminEvent.objects.filter(action="user.wallet_adjust", entity_identifier=str(target_id)).exists())

        excessive_debit = client.post(
            f"/admin/users/{target_id}/wallet/adjust",
            headers=staff_headers,
            json={"direction": "debit", "amount_gtl": 999999, "note": "Débito excessivo"},
        )
        self.assertEqual(excessive_debit.status_code, 422)

        self_credit = client.post(
            f"/admin/users/{staff_id}/wallet/adjust",
            headers=staff_headers,
            json={"direction": "credit", "amount_gtl": 25, "note": "Ajuste operacional próprio"},
        )
        self.assertEqual(self_credit.status_code, 200)
        self.assertEqual(self_credit.json()["wallet"]["available_gtl"], 2025)
        self.assertTrue(
            UserNotification.objects.filter(
                recipient_id=staff_id,
                actor_id=staff_id,
                event_type="wallet_credit",
                metadata__entry_type="manual_adjustment",
                metadata__amount=25,
            ).exists()
        )
        self.assertTrue(AdminEvent.objects.filter(action="user.wallet_adjust", entity_identifier=str(staff_id)).exists())

        self_action = client.post(
            f"/admin/users/{staff_id}/sessions/revoke",
            headers=staff_headers,
            json={"note": "self"},
        )
        self.assertEqual(self_action.status_code, 422)

        revoke = client.post(f"/admin/users/{target_id}/sessions/revoke", headers=staff_headers, json={"note": "Rotação de suporte"})
        self.assertEqual(revoke.status_code, 200)
        revoked_session = client.get("/auth/session", headers=target_headers)
        self.assertEqual(revoked_session.status_code, 401)
        self.assertTrue(AdminEvent.objects.filter(action="user.sessions_revoke", entity_identifier=str(target_id)).exists())

        relogin = client.post("/auth/login", json={"email": "managed-user@example.com", "password": "testpass123"})
        self.assertEqual(relogin.status_code, 200)
        fresh_headers = {"Authorization": f"Bearer {relogin.json()['session']['token']}"}
        deactivated = client.post(f"/admin/users/{target_id}/deactivate", headers=staff_headers, json={"note": "Abuso confirmado"})
        self.assertEqual(deactivated.status_code, 200)
        self.assertEqual(deactivated.json()["user"]["account_status"], "deactivated")
        self.assertTrue(AdminEvent.objects.filter(action="user.deactivate", entity_identifier=str(target_id)).exists())
        blocked_login = client.post("/auth/login", json={"email": "managed-user@example.com", "password": "testpass123"})
        self.assertEqual(blocked_login.status_code, 401)
        self.assertEqual(client.get("/auth/session", headers=fresh_headers).status_code, 401)

        reactivated = client.post(f"/admin/users/{target_id}/reactivate", headers=staff_headers, json={"note": "Revisão concluída"})
        self.assertEqual(reactivated.status_code, 200)
        self.assertEqual(reactivated.json()["user"]["account_status"], "active")
        allowed_login = client.post("/auth/login", json={"email": "managed-user@example.com", "password": "testpass123"})
        self.assertEqual(allowed_login.status_code, 200)
        self.assertTrue(AdminEvent.objects.filter(action="user.reactivate", entity_identifier=str(target_id)).exists())

    def test_admin_user_roles_require_superuser_and_preserve_last_superuser(self):
        client = TestClient(app)
        superuser = client.post(
            "/auth/register",
            json={"display_name": "Root Admin", "email": "root-admin@example.com", "password": "testpass123", "terms_accepted": True},
        )
        staff = client.post(
            "/auth/register",
            json={"display_name": "Role Staff", "email": "role-staff@example.com", "password": "testpass123", "terms_accepted": True},
        )
        target = client.post(
            "/auth/register",
            json={"display_name": "Role Target", "email": "role-target@example.com", "password": "testpass123", "terms_accepted": True},
        )
        self.assertEqual(superuser.status_code, 201)
        self.assertEqual(staff.status_code, 201)
        self.assertEqual(target.status_code, 201)
        superuser_id = superuser.json()["user"]["id"]
        target_id = target.json()["user"]["id"]
        superuser_headers = {"Authorization": f"Bearer {superuser.json()['session']['token']}"}
        staff_headers = {"Authorization": f"Bearer {staff.json()['session']['token']}"}
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true, is_superuser = true WHERE email = %s", ("root-admin@example.com",))
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("role-staff@example.com",))

        forbidden = client.post(
            f"/admin/users/{target_id}/roles",
            headers=staff_headers,
            json={"is_staff": True, "is_superuser": False, "note": "Promover suporte"},
        )
        self.assertEqual(forbidden.status_code, 403)

        promoted_staff = client.post(
            f"/admin/users/{target_id}/roles",
            headers=superuser_headers,
            json={"is_staff": True, "is_superuser": False, "note": "Promover suporte"},
        )
        self.assertEqual(promoted_staff.status_code, 200)
        self.assertTrue(promoted_staff.json()["user"]["is_staff"])
        self.assertFalse(promoted_staff.json()["user"]["is_superuser"])

        promoted_super = client.post(
            f"/admin/users/{target_id}/roles",
            headers=superuser_headers,
            json={"is_staff": False, "is_superuser": True, "note": "Promover super"},
        )
        self.assertEqual(promoted_super.status_code, 200)
        self.assertTrue(promoted_super.json()["user"]["is_staff"])
        self.assertTrue(promoted_super.json()["user"]["is_superuser"])

        self_action = client.post(
            f"/admin/users/{superuser_id}/roles",
            headers=superuser_headers,
            json={"is_staff": False, "is_superuser": False, "note": "self"},
        )
        self.assertEqual(self_action.status_code, 422)

        demoted_target = client.post(
            f"/admin/users/{target_id}/roles",
            headers=superuser_headers,
            json={"is_staff": False, "is_superuser": False, "note": "Rebaixar"},
        )
        self.assertEqual(demoted_target.status_code, 200)
        self.assertFalse(demoted_target.json()["user"]["is_staff"])
        self.assertFalse(demoted_target.json()["user"]["is_superuser"])

        self.assertTrue(AdminEvent.objects.filter(action="user.roles_update", entity_identifier=str(target_id)).exists())

    def test_admin_user_password_reset_contracts_permissions_and_audit(self):
        client = TestClient(app)
        staff = client.post(
            "/auth/register",
            json={"display_name": "Reset Staff", "email": "reset-staff@example.com", "password": "testpass123", "terms_accepted": True},
        )
        superuser = client.post(
            "/auth/register",
            json={"display_name": "Reset Super", "email": "reset-super@example.com", "password": "testpass123", "terms_accepted": True},
        )
        target = client.post(
            "/auth/register",
            json={"display_name": "Reset Target", "email": "reset-target@example.com", "password": "testpass123", "terms_accepted": True},
        )
        admin_target = client.post(
            "/auth/register",
            json={"display_name": "Reset Admin Target", "email": "reset-admin-target@example.com", "password": "testpass123", "terms_accepted": True},
        )
        disabled = client.post(
            "/auth/register",
            json={"display_name": "Reset Disabled", "email": "reset-disabled@example.com", "password": "testpass123", "terms_accepted": True},
        )
        self.assertEqual(staff.status_code, 201)
        self.assertEqual(superuser.status_code, 201)
        self.assertEqual(target.status_code, 201)
        self.assertEqual(admin_target.status_code, 201)
        self.assertEqual(disabled.status_code, 201)
        staff_id = staff.json()["user"]["id"]
        superuser_id = superuser.json()["user"]["id"]
        target_id = target.json()["user"]["id"]
        admin_target_id = admin_target.json()["user"]["id"]
        disabled_id = disabled.json()["user"]["id"]
        staff_headers = {"Authorization": f"Bearer {staff.json()['session']['token']}"}
        superuser_headers = {"Authorization": f"Bearer {superuser.json()['session']['token']}"}
        target_headers = {"Authorization": f"Bearer {target.json()['session']['token']}"}
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE id = %s", (staff_id,))
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true, is_superuser = true WHERE id = %s", (superuser_id,))
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE id = %s", (admin_target_id,))
                cursor.execute("UPDATE gotrendlabs_users SET account_status = 'deactivated', is_active = false WHERE id = %s", (disabled_id,))

        reset = client.post(
            f"/admin/users/{target_id}/password-reset",
            headers=staff_headers,
            json={"note": "Atendimento solicitado pelo usuário"},
        )
        self.assertEqual(reset.status_code, 200)
        self.assertIn("/password-reset/confirm/", reset.json()["reset_url"])
        self.assertTrue(PasswordResetToken.objects.filter(user_id=target_id, used_at__isnull=True).exists())
        self.assertTrue(AuthEvent.objects.filter(user_id=target_id, event_type="password_reset_requested").exists())
        self.assertTrue(AdminEvent.objects.filter(action="user.password_reset_request", entity_identifier=str(target_id)).exists())
        self.assertEqual(client.get("/auth/session", headers=target_headers).status_code, 200)

        self_reset = client.post(
            f"/admin/users/{staff_id}/password-reset",
            headers=staff_headers,
            json={"note": "self"},
        )
        self.assertEqual(self_reset.status_code, 422)

        staff_to_admin = client.post(
            f"/admin/users/{admin_target_id}/password-reset",
            headers=staff_headers,
            json={"note": "Reset de conta administrativa"},
        )
        self.assertEqual(staff_to_admin.status_code, 403)

        super_to_admin = client.post(
            f"/admin/users/{admin_target_id}/password-reset",
            headers=superuser_headers,
            json={"note": "Reset aprovado por superuser"},
        )
        self.assertEqual(super_to_admin.status_code, 200)
        self.assertTrue(PasswordResetToken.objects.filter(user_id=admin_target_id, used_at__isnull=True).exists())

        disabled_count = PasswordResetToken.objects.filter(user_id=disabled_id).count()
        disabled_reset = client.post(
            f"/admin/users/{disabled_id}/password-reset",
            headers=superuser_headers,
            json={"note": "Conta desativada"},
        )
        self.assertEqual(disabled_reset.status_code, 422)
        self.assertEqual(PasswordResetToken.objects.filter(user_id=disabled_id).count(), disabled_count)

    def test_password_reset_request_confirm_revokes_sessions_and_rejects_reuse(self):
        client = TestClient(app)
        registered = client.post(
            "/auth/register",
            json={"display_name": "Reset User", "email": "reset-user@example.com", "password": "testpass123", "terms_accepted": True},
        )
        self.assertEqual(registered.status_code, 201)
        old_headers = {"Authorization": f"Bearer {registered.json()['session']['token']}"}

        missing = client.post("/auth/password-reset/request", json={"email": "missing-reset@example.com"})
        self.assertEqual(missing.status_code, 200)
        self.assertEqual(missing.json()["reset_url"], "")

        requested = client.post("/auth/password-reset/request", json={"email": "reset-user@example.com"})
        self.assertEqual(requested.status_code, 200)
        self.assertEqual(requested.json()["reset_url"], "")
        reset_url = EmailDelivery.objects.get(
            recipient_user__email="reset-user@example.com",
            template_key="account.password_reset",
        ).context["reset_url"]
        self.assertIn("/password-reset/confirm/", reset_url)
        token = urlparse(reset_url).path.strip("/").split("/")[-1]
        self.assertTrue(PasswordResetToken.objects.filter(user__email="reset-user@example.com", used_at__isnull=True).exists())

        invalid = client.post("/auth/password-reset/confirm", json={"token": "invalid-token-that-is-long-enough", "password": "newpass123"})
        self.assertEqual(invalid.status_code, 422)

        confirmed = client.post("/auth/password-reset/confirm", json={"token": token, "password": "newpass123"})
        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(client.get("/auth/session", headers=old_headers).status_code, 401)

        old_login = client.post("/auth/login", json={"email": "reset-user@example.com", "password": "testpass123"})
        self.assertEqual(old_login.status_code, 401)
        new_login = client.post("/auth/login", json={"email": "reset-user@example.com", "password": "newpass123"})
        self.assertEqual(new_login.status_code, 200)
        reused = client.post("/auth/password-reset/confirm", json={"token": token, "password": "anotherpass123"})
        self.assertEqual(reused.status_code, 422)

    def test_password_reset_pages_render_from_login(self):
        login = self.client.get(reverse("login"))
        self.assertEqual(login.status_code, 200)
        self.assertContains(login, "Esqueci minha senha")
        self.assertContains(login, reverse("password-reset"))

        request_page = self.client.get(reverse("password-reset"))
        self.assertEqual(request_page.status_code, 200)
        self.assertContains(request_page, "Recuperar senha")

        confirm_page = self.client.get(reverse("password-reset-confirm", args=["dev-token-for-rendering"]))
        self.assertEqual(confirm_page.status_code, 200)
        self.assertContains(confirm_page, "Definir nova senha")

    def test_admin_system_logs_contracts_filters_redaction_and_staff_gate(self):
        client = TestClient(app)
        staff = client.post(
            "/auth/register",
            json={"display_name": "Logs Staff", "email": "logs-staff@example.com", "password": "testpass123", "terms_accepted": True},
        )
        user = client.post(
            "/auth/register",
            json={"display_name": "Logs User", "email": "logs-user@example.com", "password": "testpass123", "terms_accepted": True},
        )
        self.assertEqual(staff.status_code, 201)
        self.assertEqual(user.status_code, 201)
        staff_headers = {"Authorization": f"Bearer {staff.json()['session']['token']}"}
        user_headers = {"Authorization": f"Bearer {user.json()['session']['token']}"}
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("logs-staff@example.com",))

        forbidden = client.get("/admin/system-logs", headers=user_headers)
        self.assertEqual(forbidden.status_code, 403)

        request_id = "req-system-log-test"
        log_id = log_system_event(
            level="ERROR",
            source="fastapi",
            logger_name="gotrendlabs_tests",
            event_type="request_exception",
            message="Falha simulada de troubleshooting",
            request_id=request_id,
            method="POST",
            path="/admin/test",
            status_code=500,
            user_id=user.json()["user"]["id"],
            exception_type="RuntimeError",
            stack_trace="RuntimeError: boom",
            context={"headers": {"Authorization": "Bearer secret-token"}, "password": "hidden"},
        )
        self.assertIsNotNone(log_id)

        listing = client.get(
            "/admin/system-logs",
            headers=staff_headers,
            params={"level": "ERROR", "source": "fastapi", "status_code": 500, "request_id": request_id, "exception_type": "RuntimeError", "user_identifier": "@logsuser"},
        )
        self.assertEqual(listing.status_code, 200)
        payload = listing.json()
        self.assertGreaterEqual(payload["total"], 1)
        self.assertEqual(payload["logs"][0]["request_id"], request_id)
        self.assertIn("@logsuser", payload["logs"][0]["user_identifier"])
        self.assertIn("counts", payload)

        detail = client.get(f"/admin/system-logs/{log_id}", headers=staff_headers)
        self.assertEqual(detail.status_code, 200)
        detail_payload = detail.json()
        self.assertEqual(detail_payload["exception_type"], "RuntimeError")
        self.assertIn("@logsuser", detail_payload["user_identifier"])
        self.assertEqual(detail_payload["context"]["headers"]["Authorization"], "[REDACTED]")
        self.assertEqual(detail_payload["context"]["password"], "[REDACTED]")

        combo_listing = client.get(
            "/admin/system-logs",
            headers=staff_headers,
            params={"request_id": request_id, "user_identifier": "@logsuser · Logs User · logs-user@example.com"},
        )
        self.assertEqual(combo_listing.status_code, 200)
        self.assertGreaterEqual(combo_listing.json()["total"], 1)

    def test_admin_dashboard_summary_contract_staff_gate_and_metrics(self):
        client = TestClient(app)
        staff = client.post(
            "/auth/register",
            json={"display_name": "Dashboard Staff", "email": "dashboard-staff@example.com", "password": "testpass123", "terms_accepted": True},
        )
        user = client.post(
            "/auth/register",
            json={"display_name": "Dashboard User", "email": "dashboard-user@example.com", "password": "testpass123", "terms_accepted": True},
        )
        self.assertEqual(staff.status_code, 201)
        self.assertEqual(user.status_code, 201)
        staff_headers = {"Authorization": f"Bearer {staff.json()['session']['token']}"}
        user_headers = {"Authorization": f"Bearer {user.json()['session']['token']}"}
        now = timezone.now()
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("dashboard-staff@example.com",))
                cursor.execute("SELECT id FROM gotrendlabs_users WHERE email = %s", ("dashboard-staff@example.com",))
                staff_id = cursor.fetchone()["id"]
                cursor.execute("SELECT id FROM gotrendlabs_markets WHERE slug = %s", ("openai-gpt6-2026",))
                market_id = cursor.fetchone()["id"]
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_market_suggestions
                        (author_id, guest_name, guest_email, question, category, subcategory, kind, suggested_source, rationale, status, admin_note, created_at, updated_at)
                    VALUES (%s, '', '', 'Contrato operacional pendente?', 'IA', 'Modelos', 'binary', 'Fonte', '', 'pending', '', %s, %s)
                    """,
                    (staff_id, now, now),
                )
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_product_feedback
                        (author_id, guest_name, guest_email, feedback_type, severity, description, status, admin_note, created_at, updated_at)
                    VALUES (%s, '', '', 'bug', 'high', 'Falha importante para dashboard.', 'pending', '', %s, %s)
                    """,
                    (staff_id, now, now),
                )
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_market_comments
                        (market_id, author_id, body, status, moderation_note, created_at, updated_at)
                    VALUES (%s, %s, 'Comentário oculto de teste.', 'hidden', '', %s, %s)
                    """,
                    (market_id, staff_id, now, now),
                )
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_admin_events
                        (actor_id, action, entity_type, entity_identifier, note, created_at)
                    VALUES (%s, 'dashboard_probe', 'market', 'openai-gpt6-2026', 'Evento para resumo', %s)
                    """,
                    (staff_id, now),
                )
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_system_logs
                        (created_at, expires_at, level, source, logger_name, event_type, message, request_id, method, path, status_code, duration_ms, user_id, ip_address, user_agent, exception_type, stack_trace, context)
                    VALUES (%s, %s, 'ERROR', 'fastapi', 'test.dashboard', 'dashboard_error', 'Erro para resumo', 'req-dashboard', 'GET', '/admin/dashboard-summary', 500, 12, %s, '127.0.0.1', 'test', 'RuntimeError', 'RuntimeError: boom', '{}'::jsonb)
                    """,
                    (now, now + timedelta(days=90), staff_id),
                )
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_system_logs
                        (created_at, expires_at, level, source, logger_name, event_type, message, request_id, method, path, status_code, duration_ms, user_id, ip_address, user_agent, exception_type, stack_trace, context)
                    VALUES (%s, %s, 'INFO', 'python', 'gotrendlabs.daemon', 'daemon.heartbeat', 'Daemon operacional ativo.', '', '', '', NULL, NULL, NULL, NULL, '', '', '', '{"locked_markets": 1}'::jsonb)
                    """,
                    (now, now + timedelta(days=90)),
                )
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_admin_events
                        (actor_id, action, entity_type, entity_identifier, note, created_at)
                    VALUES (NULL, 'market.lock', 'market', 'daemon-dashboard-market', %s, %s)
                    """,
                    (AUTO_CLOSE_NOTE, now),
                )
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_site_config
                        (
                            singleton_key, wallet_recharge_min_balance_gtl, daemon_stale_after_minutes, daemon_missing_after_minutes,
                            system_log_retention_days, ai_audit_retention_days,
                            email_enabled, smtp_host, smtp_port, smtp_username, smtp_use_tls, smtp_use_ssl, smtp_timeout_seconds,
                            default_from_email, default_reply_to_email,
                            ai_agents_enabled, ai_commenting_enabled, ai_predictions_enabled, ai_llm_provider, ai_llm_base_url,
                            ai_model, ai_high_reasoning_model, ai_market_cooldown_hours, ai_max_comments_per_market_per_day,
                            ai_max_comments_per_cycle, ai_max_comment_attempts_per_cycle, ai_comment_candidate_limit,
                            ai_max_comments_per_day, ai_comment_max_chars, ai_min_humans_for_prediction,
                            ai_max_stake_gtl, ai_max_predictions_per_cycle, ai_max_predictions_per_day, ai_skip_if_human_comments_recent,
                            ai_recent_human_comment_window_hours, ai_openai_timeout_seconds, ai_openai_max_retries, ai_pause_reason,
                            updated_by_id, updated_at
                        )
                    VALUES (
                        1, 100, 5, 15, 90, 90, true, 'smtp.example.com', 587, 'mailer', true, false, 10, 'noreply@example.com', '',
                        false, false, false, 'openai', 'https://api.openai.com/v1', 'gpt-5.4-mini', 'gpt-5.5', 24, 1,
                        1, 3, 200, 20, 700, 1, 25, 1, 10, true, 6, 20, 1, '', %s, %s
                    )
                    ON CONFLICT (singleton_key) DO UPDATE SET
                        email_enabled = EXCLUDED.email_enabled,
                        smtp_host = EXCLUDED.smtp_host,
                        smtp_port = EXCLUDED.smtp_port,
                        default_from_email = EXCLUDED.default_from_email,
                        daemon_stale_after_minutes = EXCLUDED.daemon_stale_after_minutes,
                        daemon_missing_after_minutes = EXCLUDED.daemon_missing_after_minutes,
                        system_log_retention_days = EXCLUDED.system_log_retention_days,
                        ai_audit_retention_days = EXCLUDED.ai_audit_retention_days,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (staff_id, now),
                )

        with TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "platform_config.json")
            with open(config_path, "w", encoding="utf-8") as config_file:
                config_file.write('{"maintenance_enabled": true}')
            with patch.dict(
                os.environ,
                {
                    "GOTRENDLABS_RUNTIME_CONFIG_PATH": config_path,
                    "GOTRENDLABS_SMTP_PASSWORD": "secret",
                    "RECAPTCHA_ENABLED": "1",
                },
            ):
                forbidden = client.get("/admin/dashboard-summary", headers=user_headers)
                self.assertEqual(forbidden.status_code, 403)
                summary = client.get("/admin/dashboard-summary", headers=staff_headers)

        self.assertEqual(summary.status_code, 200)
        payload = summary.json()
        self.assertIn("markets", payload)
        self.assertIn("queues", payload)
        self.assertIn("system", payload)
        self.assertGreaterEqual(payload["markets"]["open"], 1)
        self.assertGreaterEqual(payload["queues"]["suggestions_pending"], 1)
        self.assertGreaterEqual(payload["queues"]["feedback_high_pending"], 1)
        self.assertGreaterEqual(payload["queues"]["comments_hidden"], 1)
        self.assertGreaterEqual(payload["system"]["logs_error_7d"], 1)
        self.assertTrue(payload["system"]["maintenance_enabled"])
        self.assertTrue(payload["system"]["recaptcha_enabled"])
        self.assertEqual(payload["system"]["smtp_status"], "ready")
        self.assertEqual(payload["system"]["daemon_status"], "active")
        self.assertEqual(payload["system"]["daemon_status_label"], "Ativo")
        self.assertGreaterEqual(payload["system"]["daemon_locked_markets_24h"], 1)
        self.assertTrue(any(event["action"] == "dashboard_probe" for event in payload["recent_admin_events"]))
        self.assertTrue(any(market["slug"] == "openai-gpt6-2026" for market in payload["top_markets"]))

    def test_daemon_backend_services_auto_close_prune_and_status(self):
        now = timezone.now()
        site_config = SiteConfig.get_solo()
        site_config.system_log_retention_days = 1
        site_config.ai_audit_retention_days = 1
        site_config.save(update_fields=["system_log_retention_days", "ai_audit_retention_days"])
        due_close_at = now - timedelta(minutes=5)
        future_close_at = now + timedelta(hours=2)
        expired_at = now + timedelta(days=30)
        valid_expires_at = now + timedelta(days=10)
        expired_action = AiAgentAction.objects.create(action_type="cycle", status="skipped", reason="old_retention")
        valid_action = AiAgentAction.objects.create(action_type="cycle", status="skipped", reason="fresh_retention")
        AiAgentAction.objects.filter(id=expired_action.id).update(created_at=now - timedelta(days=2))
        AiAgentAction.objects.filter(id=valid_action.id).update(created_at=now)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM gotrendlabs_users WHERE is_staff = true ORDER BY id LIMIT 1")
                staff = cursor.fetchone()
                staff_id = staff["id"] if staff else None
                cursor.execute("SELECT id FROM gotrendlabs_market_categories ORDER BY id LIMIT 1")
                category_id = cursor.fetchone()["id"]
                cursor.execute("SELECT id FROM gotrendlabs_market_subcategories WHERE category_id = %s ORDER BY id LIMIT 1", (category_id,))
                subcategory_id = cursor.fetchone()["id"]
                market_rows = [
                    ("daemon-auto-vencido", "open", True, due_close_at),
                    ("daemon-manual-vencido", "open", False, due_close_at),
                    ("daemon-auto-futuro", "open", True, future_close_at),
                    ("daemon-auto-resolvido", "resolved", True, due_close_at),
                ]
                for slug, status_value, auto_close_enabled, close_at in market_rows:
                    cursor.execute(
                        """
                        INSERT INTO gotrendlabs_markets
                            (slug, title, summary, kind, status, status_label, primary_outcome, primary_probability_exact,
                             secondary_probability_exact, volume_gtl, participants, source, closes_in, close_label, thumb,
                             thumb_color, image_url, resolution_criteria, resolution_type, close_at, close_timezone,
                             auto_close_enabled, resolved_at, resolution_timezone, canceled_at, winning_option_id,
                             resolution_note, admin_notes, category_id, subcategory_id, created_by_id, updated_by_id,
                             display_order, view_count, share_count, is_featured, created_at, updated_at)
                        VALUES
                            (%s, %s, 'Resumo daemon', 'binary', %s, %s, '', 0, 0, '', '', 'Fonte',
                             '', '', '', '#136f4a', '', 'Critério', '', %s, 'America/Sao_Paulo',
                             %s, NULL, '', NULL, NULL, '', '', %s, %s, %s, %s, 0, 0, 0, false, %s, %s)
                        """,
                        (
                            slug,
                            slug,
                            status_value,
                            "Aberto" if status_value == "open" else "Resolvido",
                            close_at,
                            auto_close_enabled,
                            category_id,
                            subcategory_id,
                            staff_id,
                            staff_id,
                            now - timedelta(days=30),
                            now - timedelta(days=30),
                        ),
                    )
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_system_logs
                        (created_at, expires_at, level, source, logger_name, event_type, message, request_id, method, path, status_code, duration_ms, user_id, ip_address, user_agent, exception_type, stack_trace, context)
                    VALUES
                        (%s, %s, 'INFO', 'python', 'test.prune', 'expired', 'expired', '', '', '', NULL, NULL, NULL, NULL, '', '', '', '{}'::jsonb),
                        (%s, %s, 'INFO', 'python', 'test.prune', 'valid', 'valid', '', '', '', NULL, NULL, NULL, NULL, '', '', '', '{}'::jsonb)
                    """,
                    (now - timedelta(days=2), expired_at, now, valid_expires_at),
                )

        locked = close_due_auto_markets(now=now)
        self.assertEqual(locked, [])
        self.assertEqual(Market.objects.get(slug="daemon-auto-vencido").status, "canceled")
        self.assertEqual(Market.objects.get(slug="daemon-manual-vencido").status, "open")
        self.assertEqual(Market.objects.get(slug="daemon-auto-futuro").status, "open")
        self.assertEqual(Market.objects.get(slug="daemon-auto-resolvido").status, "resolved")
        self.assertTrue(AdminEvent.objects.filter(action="market.cancel", actor__isnull=True, entity_identifier="daemon-auto-vencido", note=AUTO_CANCEL_NO_HUMANS_NOTE).exists())

        removed = prune_expired_system_logs(now=now)
        self.assertGreaterEqual(removed, 1)
        self.assertFalse(SystemLog.objects.filter(logger_name="test.prune", event_type="expired").exists())
        self.assertTrue(SystemLog.objects.filter(logger_name="test.prune", event_type="valid").exists())
        self.assertTrue(AiAgentAction.objects.filter(id=expired_action.id).exists())

        pruned = prune_expired_operational_records(now=now)
        self.assertGreaterEqual(pruned["ai_agent_actions"], 1)
        self.assertFalse(AiAgentAction.objects.filter(id=expired_action.id).exists())
        self.assertTrue(AiAgentAction.objects.filter(id=valid_action.id).exists())
        self.assertIn("system_logs", pruned)
        self.assertIn("ai_agent_actions", pruned)

        log_system_event(logger_name="gotrendlabs.daemon", event_type="daemon.heartbeat", message="Daemon operacional ativo.")
        with get_connection() as connection:
            with connection.cursor() as cursor:
                status_payload = daemon_dashboard_status(cursor, now=now + timedelta(minutes=1))
                self.assertEqual(status_payload["daemon_status"], "active")
                status_payload = daemon_dashboard_status(cursor, now=now + timedelta(minutes=6), stale_after_minutes=5, missing_after_minutes=15)
                self.assertEqual(status_payload["daemon_status"], "stale")
                status_payload = daemon_dashboard_status(cursor, now=now + timedelta(minutes=16), stale_after_minutes=5, missing_after_minutes=15)
                self.assertEqual(status_payload["daemon_status"], "missing")

    def test_daemon_management_commands_use_backend_services(self):
        out = StringIO()
        with patch(
            "system_logs.management.commands.run_gotrendlabs_daemon.run_daemon_cycle",
            return_value={"locked_markets": [{"slug": "x"}], "pruned_logs": 3, "pruned_log_details": {"system_logs": 2, "ai_agent_actions": 1}},
        ) as cycle:
            call_command("run_gotrendlabs_daemon", "--once", stdout=out)
        cycle.assert_called_once()
        self.assertIn("locked 1 market", out.getvalue())
        self.assertIn("2 system log", out.getvalue())
        self.assertIn("1 AI audit action", out.getvalue())

        out = StringIO()
        with patch(
            "system_logs.management.commands.prune_system_logs.prune_expired_operational_records",
            return_value={"system_logs": 3, "ai_agent_actions": 2, "total": 5},
        ) as prune:
            call_command("prune_system_logs", stdout=out)
        prune.assert_called_once()
        self.assertIn("Removed 3 expired system logs and 2 expired AI audit actions.", out.getvalue())

    def test_daemon_locked_markets_message_includes_market_slugs(self):
        self.assertEqual(
            _locked_markets_message([{"slug": "mercado-a"}]),
            "Daemon fechou 1 mercado(s) automaticamente: mercado-a.",
        )
        many_markets = [{"slug": f"mercado-{index}"} for index in range(12)]
        message = _locked_markets_message(many_markets)
        self.assertIn("Daemon fechou 12 mercado(s) automaticamente.", message)
        self.assertIn("mercado-0, mercado-1", message)
        self.assertIn("Mais 2 no detalhe do log.", message)

    def test_ai_agent_cycle_noops_when_disabled(self):
        SiteConfig.get_solo()
        with get_connection() as connection:
            with connection.cursor() as cursor:
                summary = run_ai_agent_cycle(cursor, now=timezone.now())

        self.assertFalse(summary["enabled"])
        self.assertEqual(summary["reason"], "ai_agents_disabled")
        self.assertTrue(AiAgentAction.objects.filter(action_type="cycle", status="skipped", reason="ai_agents_disabled").exists())

    def test_ai_comment_llm_failure_is_audited_without_breaking_cycle(self):
        site_config = SiteConfig.get_solo()
        site_config.ai_agents_enabled = True
        site_config.ai_commenting_enabled = True
        site_config.ai_predictions_enabled = False
        site_config.save()
        User = get_user_model()
        bot = User.objects.create_user(username="@gotrendlabs_ai_test", email="gotrendlabs-ai-test@example.com", password="x", is_bot=True, first_name="GoTrendLabs AI Test")
        AiAgent.objects.create(name="GoTrendLabs AI Test", agent_type="analyst", user=bot, is_active=True)

        with patch("backend_api.agent_services.request_market_comment", side_effect=AgentLLMError("llm down")):
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    summary = run_ai_agent_cycle(cursor, now=timezone.now())

        self.assertGreaterEqual(summary["errors"], 1)
        self.assertTrue(AiAgentAction.objects.filter(action_type="comment", status="failed").exists())

    def test_ai_health_recovers_after_successful_cycle(self):
        site_config = SiteConfig.get_solo()
        site_config.ai_agents_enabled = True
        site_config.save(update_fields=["ai_agents_enabled"])
        now = timezone.now()
        failed = AiAgentAction.objects.create(action_type="comment", status="failed", reason="llm_error")
        success = AiAgentAction.objects.create(action_type="cycle", status="created", reason="cycle_completed")
        AiAgentAction.objects.filter(id=failed.id).update(created_at=now - timedelta(minutes=10))
        AiAgentAction.objects.filter(id=success.id).update(created_at=now)

        health = self._ai_health_for_test(now=now)

        self.assertEqual(health["status"], "active")
        self.assertEqual(health["status_label"], "Ativo")
        self.assertGreaterEqual(health["errors_24h"], 1)

    def test_ai_comment_contract_marks_official_bot_author(self):
        User = get_user_model()
        bot = User.objects.create_user(username="@gotrendlabs_ai_comment", email="gotrendlabs-ai-comment@example.com", password="x", is_bot=True, first_name="GoTrendLabs AI Comment")
        market = Market.objects.get(slug="openai-gpt6-2026")
        MarketComment.objects.create(market=market, author=bot, body="Tese SIM: sinal. Tese NÃO: contraponto. Sinais: acompanhar fontes.")

        response = TestClient(app).get(f"/markets/{market.slug}/comments")

        self.assertEqual(response.status_code, 200)
        comment = response.json()["comments"][0]
        self.assertTrue(comment["author_is_bot"])
        self.assertEqual(comment["author_badge_label"], "IA oficial")

    def test_ai_comment_prompt_uses_multiple_choice_structure(self):
        prompt = build_comment_prompt(
            agent={"personality_prompt": "", "comment_style": ""},
            market={
                "kind": "multiple",
                "title": "Quem vencerá o torneio?",
                "options": [
                    {"label": "Time A", "probability_exact": 42.0, "hint": ""},
                    {"label": "Time B", "probability_exact": 31.0, "hint": ""},
                    {"label": "Time C", "probability_exact": 27.0, "hint": ""},
                ],
            },
            comments=[],
            config={"ai_comment_max_chars": 700},
        )

        self.assertIn("Mercado de multipla escolha", prompt)
        self.assertIn("nao use tese SIM/NAO", prompt)
        self.assertIn('"kind": "multiple"', prompt)
        self.assertIn("nao comece o comentario", prompt)
        self.assertIn("Nao afirme upgrades tecnicos", prompt)
        self.assertIn("linguagem condicional", prompt)
        self.assertIn("fatos especificos nao confirmados", prompt)

    def test_ai_comment_text_strips_official_prefix(self):
        body = _safe_comment_text("Agente IA oficial da GoTrendLabs: Tese SIM: sinal. Tese NÃO: contraponto.", 700)

        self.assertEqual(body, "Tese SIM: sinal. Tese NÃO: contraponto.")

    def test_ai_comment_cycle_falls_back_when_llm_declines_first_market(self):
        self._reset_ai_agent_state()
        site_config = SiteConfig.get_solo()
        site_config.ai_agents_enabled = True
        site_config.ai_commenting_enabled = True
        site_config.ai_predictions_enabled = False
        site_config.ai_max_comments_per_cycle = 1
        site_config.ai_max_comment_attempts_per_cycle = 3
        site_config.ai_comment_candidate_limit = 200
        site_config.save()
        User = get_user_model()
        bot = User.objects.create_user(username="@gotrendlabs_ai_fallback", email="gotrendlabs-ai-fallback@example.com", password="x", is_bot=True, first_name="GoTrendLabs AI Fallback")
        AiAgent.objects.create(name="GoTrendLabs AI Fallback", agent_type="analyst", user=bot, is_active=True)
        Market.objects.filter(status="open").update(is_featured=False, view_count=0)
        first = Market.objects.get(slug="openai-gpt6-2026")
        second = Market.objects.exclude(id=first.id).filter(status="open").order_by("id").first()
        first.view_count = 1000
        second.view_count = 900
        first.save(update_fields=["view_count"])
        second.save(update_fields=["view_count"])

        with patch(
            "backend_api.agent_services.request_market_comment",
            side_effect=[
                {"comment": "", "should_publish": False, "confidence": 0.2, "risk_flags": ["thin_signal"]},
                {"comment": "Tese SIM: sinal. Tese NÃO: contraponto. Sinais: acompanhar fontes.", "should_publish": True, "confidence": 0.7, "risk_flags": []},
            ],
        ) as llm:
            summary = self._run_ai_cycle_for_test()

        self.assertEqual(llm.call_count, 2)
        self.assertEqual(summary["comments_created"], 1)
        self.assertTrue(AiAgentAction.objects.filter(market_id=first.id, status="skipped", reason="llm_should_publish_false").exists())
        self.assertTrue(MarketComment.objects.filter(market=second, author=bot).exists())

    def test_ai_comment_cycle_falls_back_when_comment_validation_fails(self):
        self._reset_ai_agent_state()
        site_config = SiteConfig.get_solo()
        site_config.ai_agents_enabled = True
        site_config.ai_commenting_enabled = True
        site_config.ai_predictions_enabled = False
        site_config.ai_max_comments_per_cycle = 1
        site_config.ai_max_comment_attempts_per_cycle = 3
        site_config.save()
        User = get_user_model()
        bot = User.objects.create_user(username="@gotrendlabs_ai_validation", email="gotrendlabs-ai-validation@example.com", password="x", is_bot=True, first_name="GoTrendLabs AI Validation")
        AiAgent.objects.create(name="GoTrendLabs AI Validation", agent_type="analyst", user=bot, is_active=True)
        Market.objects.filter(status="open").update(is_featured=False, view_count=0)
        first = Market.objects.get(slug="openai-gpt6-2026")
        second = Market.objects.exclude(id=first.id).filter(status="open").order_by("id").first()
        first.view_count = 1000
        second.view_count = 900
        first.save(update_fields=["view_count"])
        second.save(update_fields=["view_count"])

        with patch(
            "backend_api.agent_services.request_market_comment",
            side_effect=[
                {"comment": "eu apostei nesse mercado", "should_publish": True, "confidence": 0.5, "risk_flags": []},
                {"comment": "Tese SIM: sinal. Tese NÃO: contraponto. Sinais: acompanhar fontes.", "should_publish": True, "confidence": 0.8, "risk_flags": []},
            ],
        ) as llm:
            summary = self._run_ai_cycle_for_test()

        self.assertEqual(llm.call_count, 2)
        self.assertEqual(summary["comments_created"], 1)
        self.assertTrue(AiAgentAction.objects.filter(market_id=first.id, status="failed", reason="comment_validation_failed").exists())
        self.assertTrue(MarketComment.objects.filter(market=second, author=bot).exists())

    def test_ai_comment_cycle_stops_on_llm_error_without_extra_attempt(self):
        self._reset_ai_agent_state()
        site_config = SiteConfig.get_solo()
        site_config.ai_agents_enabled = True
        site_config.ai_commenting_enabled = True
        site_config.ai_predictions_enabled = False
        site_config.ai_max_comment_attempts_per_cycle = 3
        site_config.save()
        User = get_user_model()
        bot = User.objects.create_user(username="@gotrendlabs_ai_timeout", email="gotrendlabs-ai-timeout@example.com", password="x", is_bot=True, first_name="GoTrendLabs AI Timeout")
        AiAgent.objects.create(name="GoTrendLabs AI Timeout", agent_type="analyst", user=bot, is_active=True)

        with patch("backend_api.agent_services.request_market_comment", side_effect=AgentLLMError("timeout")) as llm:
            summary = self._run_ai_cycle_for_test()

        self.assertEqual(llm.call_count, 1)
        self.assertEqual(summary["comments_created"], 0)
        self.assertGreaterEqual(summary["errors"], 1)
        self.assertTrue(AiAgentAction.objects.filter(action_type="comment", status="failed", reason="llm_error").exists())

    def test_ai_comment_attempt_limit_caps_llm_calls(self):
        self._reset_ai_agent_state()
        site_config = SiteConfig.get_solo()
        site_config.ai_agents_enabled = True
        site_config.ai_commenting_enabled = True
        site_config.ai_predictions_enabled = False
        site_config.ai_max_comments_per_cycle = 1
        site_config.ai_max_comment_attempts_per_cycle = 1
        site_config.ai_comment_candidate_limit = 200
        site_config.save()
        User = get_user_model()
        bot = User.objects.create_user(username="@gotrendlabs_ai_attempt_limit", email="gotrendlabs-ai-attempt-limit@example.com", password="x", is_bot=True, first_name="GoTrendLabs AI Attempt Limit")
        AiAgent.objects.create(name="GoTrendLabs AI Attempt Limit", agent_type="analyst", user=bot, is_active=True)

        with patch("backend_api.agent_services.request_market_comment", return_value={"comment": "", "should_publish": False, "confidence": 0.2, "risk_flags": []}) as llm:
            summary = self._run_ai_cycle_for_test()

        self.assertEqual(llm.call_count, 1)
        self.assertEqual(summary["comments_created"], 0)
        self.assertTrue(AiAgentAction.objects.filter(action_type="comment", status="skipped", reason="comment_attempt_limit_reached").exists())

    def test_ai_comment_candidate_limit_reaches_market_after_many_local_skips(self):
        self._reset_ai_agent_state()
        site_config = SiteConfig.get_solo()
        site_config.ai_agents_enabled = True
        site_config.ai_commenting_enabled = True
        site_config.ai_predictions_enabled = False
        site_config.ai_max_comments_per_cycle = 1
        site_config.ai_max_comment_attempts_per_cycle = 3
        site_config.ai_comment_candidate_limit = 200
        site_config.save()
        User = get_user_model()
        bot = User.objects.create_user(username="@gotrendlabs_ai_candidate_limit", email="gotrendlabs-ai-candidate-limit@example.com", password="x", is_bot=True, first_name="GoTrendLabs AI Candidate Limit")
        AiAgent.objects.create(name="GoTrendLabs AI Candidate Limit", agent_type="analyst", user=bot, is_active=True)
        Market.objects.filter(status="open").update(is_featured=False, view_count=0)
        category = MarketCategory.objects.first()
        subcategory = MarketSubcategory.objects.filter(category=category).first()
        now = timezone.now()
        for index in range(60):
            market = Market.objects.create(
                category=category,
                subcategory=subcategory,
                slug=f"ai-local-skip-{index}",
                title=f"Mercado local skip {index}",
                summary="Resumo",
                kind="binary",
                status="open",
                status_label="Aberto",
                primary_outcome="SIM",
                view_count=1000 - index,
            )
            MarketComment.objects.create(market=market, author=bot, body="Comentario IA recente.", created_at=now)
        eligible = Market.objects.create(
            category=category,
            subcategory=subcategory,
            slug="ai-eligible-after-local-skips",
            title="Mercado elegivel depois de skips",
            summary="Resumo",
            kind="binary",
            status="open",
            status_label="Aberto",
            primary_outcome="SIM",
            view_count=100,
        )
        MarketOption.objects.create(market=eligible, label="SIM", probability_exact=50, display_order=1)
        MarketOption.objects.create(market=eligible, label="NAO", probability_exact=50, display_order=2)

        with patch("backend_api.agent_services.request_market_comment", return_value={"comment": "Tese SIM: sinal. Tese NÃO: contraponto. Sinais: acompanhar fontes.", "should_publish": True, "confidence": 0.7, "risk_flags": []}) as llm:
            summary = self._run_ai_cycle_for_test(now=now)

        self.assertEqual(llm.call_count, 1)
        self.assertEqual(summary["comments_created"], 1)
        self.assertTrue(MarketComment.objects.filter(market=eligible, author=bot).exists())

    def test_agent_llm_allows_bedrock_openai_compatible_provider(self):
        class FakeResponse:
            status_code = 200
            text = ""

            def json(self):
                return {
                    "output_text": json.dumps(
                        {
                            "comment": "Comentário seguro.",
                            "should_publish": True,
                            "confidence": 0.7,
                            "risk_flags": [],
                        }
                    )
                }

        config = {
            "ai_llm_provider": "bedrock",
            "ai_llm_base_url": "https://bedrock-mantle.us-west-2.api.aws/v1",
            "ai_model": "openai.gpt-oss-20b",
            "ai_openai_timeout_seconds": 20,
            "ai_openai_max_retries": 0,
        }
        with patch.dict(os.environ, {"AWS_BEARER_TOKEN_BEDROCK": "bedrock-test-key"}), patch("backend_api.agent_llm.httpx.post", return_value=FakeResponse()) as post:
            result = request_market_comment(config=config, prompt="teste")

        self.assertTrue(result["should_publish"])
        self.assertEqual(post.call_args.args[0], "https://bedrock-mantle.us-west-2.api.aws/v1/responses")
        self.assertFalse(post.call_args.kwargs["json"]["store"])
        self.assertNotIn("text", post.call_args.kwargs["json"])

    def test_agent_llm_extracts_bedrock_output_without_reasoning_text(self):
        payload = {
            "output": [
                {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "internal reasoning"}]},
                {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "{\"ok\": true}"}]},
            ]
        }

        self.assertEqual(_extract_output_text(payload), "{\"ok\": true}")

    def test_ranking_and_badges_ignore_bots(self):
        User = get_user_model()
        human = User.objects.create_user(username="@ranking_human", email="ranking-human@example.com", password="x")
        bot = User.objects.create_user(username="@ranking_bot", email="ranking-bot@example.com", password="x", is_bot=True, first_name="GoTrendLabs AI Ranking")
        UserReputation.objects.create(user=human, reputation_score=120, accuracy_indicator="0%")
        UserReputation.objects.create(user=bot, reputation_score=999, accuracy_indicator="0%")
        BadgeDefinition.objects.update_or_create(
            code="bot_comment_guard",
            defaults={"name": "Guard", "description": "Guard", "rule_description": "Guard", "badge_type": "engagement", "is_active": True},
        )
        badge = BadgeDefinition.objects.get(code="bot_comment_guard")
        BadgeRule.objects.update_or_create(badge=badge, defaults={"rule_type": "comments_count", "threshold_value": 1, "is_active": True})
        market = Market.objects.get(slug="openai-gpt6-2026")
        MarketComment.objects.create(market=market, author=bot, body="Comentário bot oficial.")

        response = TestClient(app).get("/rankings")
        handles = [row["handle"] for row in response.json()["rows"]]
        self.assertIn("@rankinghuman", handles)
        self.assertNotIn("@rankingbot", handles)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                BadgeAwardEngine.on_comment_created(cursor, bot.id, market_id=market.id)
        self.assertFalse(UserBadgeAward.objects.filter(user=bot, badge=badge).exists())

    def test_rankings_include_recent_active_badges(self):
        User = get_user_model()
        BadgeDefinition.objects.update(is_active=False)
        user = User.objects.create_user(username="@ranking_badge_user", email="ranking-badge-user@example.com", password="x")
        UserReputation.objects.create(user=user, reputation_score=130, accuracy_indicator="75%")
        base_time = timezone.now()
        for index in range(1, 5):
            badge = BadgeDefinition.objects.create(
                code=f"ranking_active_{index}",
                name=f"Ranking ativa {index}",
                description="Badge ativa no ranking.",
                rule_description="Regra pública.",
                badge_type="performance",
                image_url=f"/media/badge_images/ranking-active-{index}.png",
                image_dark_url=f"/media/badge_images/ranking-active-{index}-dark.png",
                is_active=True,
            )
            UserBadgeAward.objects.create(user=user, badge=badge, awarded_at=base_time + timedelta(minutes=index), reason_snapshot="ranking:test")
        inactive_badge = BadgeDefinition.objects.create(
            code="ranking_inactive",
            name="Ranking inativa",
            description="Badge inativa.",
            is_active=False,
            image_url="/media/badge_images/inactive.png",
        )
        UserBadgeAward.objects.create(user=user, badge=inactive_badge, awarded_at=base_time + timedelta(minutes=10), reason_snapshot="ranking:test")
        dev_badge = BadgeDefinition.objects.create(
            code="dev_ranking_noise",
            name="Ranking DEV",
            description="Badge de simulação dev.",
            rule_description="preview local",
            badge_type="performance",
            image_url="/media/badge_images/dev-ranking.png",
            is_active=True,
        )
        UserBadgeAward.objects.create(user=user, badge=dev_badge, awarded_at=base_time + timedelta(minutes=11), reason_snapshot="ranking:test")

        response = TestClient(app).get("/rankings")
        self.assertEqual(response.status_code, 200)
        row = next(item for item in response.json()["rows"] if item["handle"] == "@rankingbadgeuser")
        self.assertEqual(row["badges_total"], 4)
        self.assertEqual([badge["code"] for badge in row["badges"]], ["ranking_active_4", "ranking_active_3", "ranking_active_2"])
        self.assertEqual(row["badges"][0]["image_url"], "/media/badge_images/ranking-active-4.png")
        self.assertEqual(row["badges"][0]["image_dark_url"], "/media/badge_images/ranking-active-4-dark.png")
        self.assertNotIn("ranking_inactive", [badge["code"] for badge in row["badges"]])

    def test_ai_prediction_bot_is_blocked_without_human_participants(self):
        site_config = SiteConfig.get_solo()
        site_config.ai_agents_enabled = True
        site_config.ai_commenting_enabled = False
        site_config.ai_predictions_enabled = True
        site_config.ai_min_humans_for_prediction = 1
        site_config.ai_max_stake_gtl = 25
        site_config.save()
        User = get_user_model()
        bot = User.objects.create_user(username="@gotrendlabs_liquidity_bot", email="gotrendlabs-liquidity@example.com", password="x", is_bot=True, first_name="GoTrendLabs Liquidity Bot")
        AiAgent.objects.create(name="GoTrendLabs Liquidity Bot", agent_type="liquidity", user=bot, is_active=True)
        WalletBalance.objects.create(user=bot, available_gtl=100, locked_gtl=0, total_earned_gtl=0)
        market = Market.objects.get(slug="openai-gpt6-2026")

        with get_connection() as connection:
            with connection.cursor() as cursor:
                summary = run_ai_agent_cycle(cursor, now=timezone.now())

        self.assertEqual(summary["predictions_created"], 0)
        self.assertFalse(Prediction.objects.filter(user=bot, market=market).exists())
        self.assertTrue(AiAgentAction.objects.filter(action_type="prediction", status="skipped", reason="no_eligible_market").exists())

    def test_ai_prediction_cycle_skips_markets_already_predicted_by_bot(self):
        site_config = SiteConfig.get_solo()
        site_config.ai_agents_enabled = True
        site_config.ai_commenting_enabled = False
        site_config.ai_predictions_enabled = True
        site_config.ai_min_humans_for_prediction = 1
        site_config.ai_max_stake_gtl = 5
        site_config.save()
        User = get_user_model()
        human = User.objects.create_user(username="@skip_human", email="skip-human@example.com", password="x")
        bot = User.objects.create_user(username="@skip_liquidity_bot", email="skip-liquidity@example.com", password="x", is_bot=True, first_name="GoTrendLabs Liquidity")
        AiAgent.objects.create(name="GoTrendLabs Liquidity Skip", agent_type="liquidity", user=bot, is_active=True)
        WalletBalance.objects.create(user=bot, available_gtl=100, locked_gtl=0, total_earned_gtl=0)
        markets = list(Market.objects.filter(status="open").order_by("id")[:2])
        first = markets[0]
        second = markets[1]
        first.view_count = 1000
        second.view_count = 900
        first.save(update_fields=["view_count"])
        second.save(update_fields=["view_count"])
        first_option = first.options.first()
        second_option = second.options.first()
        Prediction.objects.create(user=human, market=first, market_option=first_option, stake_amount=10, probability_at_entry=50, weight_at_entry=1000, potential_payout=20, status="open")
        Prediction.objects.create(user=human, market=second, market_option=second_option, stake_amount=10, probability_at_entry=50, weight_at_entry=1000, potential_payout=20, status="open")
        Prediction.objects.create(user=bot, market=first, market_option=first_option, stake_amount=5, probability_at_entry=50, weight_at_entry=500, potential_payout=10, status="open")

        with get_connection() as connection:
            with connection.cursor() as cursor:
                summary = run_ai_agent_cycle(cursor, now=timezone.now())

        self.assertEqual(summary["predictions_created"], 1)
        self.assertTrue(Prediction.objects.filter(user=bot, market=second).exists())
        self.assertEqual(Prediction.objects.filter(user=bot, market=first).count(), 1)

    def test_system_log_capture_and_python_logging_handler(self):
        client = TestClient(app)
        request_id = "req-capture-smoke"
        response = client.get("/markets", headers={"X-Request-ID": request_id, "Authorization": "Bearer should-not-leak"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-request-id"], request_id)
        self.assertTrue(SystemLog.objects.filter(request_id=request_id, source="fastapi", event_type="request").exists())
        captured = SystemLog.objects.filter(request_id=request_id).latest("id")
        self.assertEqual(captured.context["headers"]["authorization"], "[REDACTED]")

        logging.getLogger("gotrendlabs_tests.system_logs").warning("handler persistence smoke", extra={"api_token": "secret"})
        self.assertTrue(SystemLog.objects.filter(logger_name="gotrendlabs_tests.system_logs", event_type="logging", message__icontains="handler persistence smoke").exists())

    def test_register_handle_collision_keeps_at_prefix(self):
        client = TestClient(app)
        first = client.post(
            "/auth/register",
            json={
                "display_name": "Collision User",
                "email": "collision-one@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        second = client.post(
            "/auth/register",
            json={
                "display_name": "Collision User",
                "email": "collision-two@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["user"]["handle"], "@collisionuser")
        self.assertEqual(second.json()["user"]["handle"], "@collisionuser2")

    def test_register_creates_user_core_wallet_badges_activity_and_ranking(self):
        client = TestClient(app)
        response = client.post(
            "/auth/register",
            json={
                "display_name": "User Core",
                "email": "user-core@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(response.status_code, 201)
        token = response.json()["session"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/users/me", headers=headers)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["user"]["display_name"], "User Core")
        self.assertEqual(me.json()["reputation"]["reputation_score"], 100)
        self.assertIn("profile_id", me.json())
        self.assertIn("profile_created_at", me.json())
        self.assertIn("profile_updated_at", me.json())
        self.assertIsNone(me.json()["birth_date"])
        self.assertEqual(me.json()["sex"], "")

        wallet = client.get("/users/me/wallet", headers=headers)
        self.assertEqual(wallet.status_code, 200)
        self.assertEqual(wallet.json()["available_gtl"], 2000)
        self.assertEqual(wallet.json()["locked_gtl"], 0)
        self.assertEqual(WalletBalance.objects.get(user__username="@usercore").available_gtl, 2000)

        ledger = client.get("/users/me/ledger", headers=headers)
        self.assertEqual(ledger.status_code, 200)
        self.assertEqual(ledger.json()["entries"][0]["entry_type"], "grant_initial")
        self.assertEqual(WalletLedgerEntry.objects.filter(user__username="@usercore", entry_type="grant_initial").count(), 1)

        badges = client.get("/users/me/badges", headers=headers)
        self.assertEqual(badges.status_code, 200)
        self.assertIn("founding_member", [badge["code"] for badge in badges.json()])

        activity = client.get("/users/me/activity", headers=headers)
        self.assertEqual(activity.status_code, 200)
        self.assertEqual(activity.json()[0]["activity_type"], "register")

        public_profile = client.get("/users/usercore")
        self.assertEqual(public_profile.status_code, 200)
        self.assertEqual(public_profile.json()["user"]["handle"], "@usercore")
        self.assertEqual(public_profile.json()["user"]["display_name"], "User Core")

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM gotrendlabs_users WHERE username = %s", ("@usercore",))
                user_id = cursor.fetchone()["id"]
                cursor.execute("UPDATE gotrendlabs_users SET first_name = '' WHERE id = %s", (user_id,))
                cursor.execute("UPDATE gotrendlabs_user_profiles SET display_name = %s WHERE user_id = %s", ("Nome vindo do perfil", user_id))
        profile_backed_me = client.get("/users/me", headers=headers)
        self.assertEqual(profile_backed_me.status_code, 200)
        self.assertEqual(profile_backed_me.json()["user"]["display_name"], "Nome vindo do perfil")
        self.assertEqual(profile_backed_me.json()["strong_category"], "")

        ranking = client.get("/rankings")
        self.assertEqual(ranking.status_code, 200)
        self.assertIn("@usercore", [row["handle"] for row in ranking.json()["rows"]])

        repeat_me = client.get("/users/me", headers=headers)
        self.assertEqual(repeat_me.status_code, 200)
        self.assertEqual(UserReputation.objects.filter(user__username="@usercore").count(), 1)
        self.assertEqual(WalletLedgerEntry.objects.filter(user__username="@usercore", entry_type="grant_initial").count(), 1)
        self.assertEqual(WalletBalance.objects.get(user__username="@usercore").available_gtl, 2000)

        invalid = client.get("/users/me", headers={"Authorization": "Bearer invalid"})
        self.assertEqual(invalid.status_code, 401)

    def test_email_confirmation_outbox_blocks_sensitive_actions_until_confirmed(self):
        site_config = SiteConfig.get_solo()
        site_config.email_enabled = True
        site_config.save()
        client = TestClient(app)
        response = client.post(
            "/auth/register",
            json={
                "display_name": "Confirm Email User",
                "email": "confirm-email-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()["user"]["email_confirmed"])
        user_id = response.json()["user"]["id"]
        delivery = EmailDelivery.objects.get(recipient_user_id=user_id, template_key="user.email_confirmation")
        self.assertIn("confirmation_url", delivery.context)
        self.assertEqual(EmailConfirmationToken.objects.filter(user_id=user_id, used_at__isnull=True).count(), 1)

        option = MarketOption.objects.get(market__slug="openai-gpt6-2026", label="SIM")
        headers = {"Authorization": f"Bearer {response.json()['session']['token']}"}
        blocked = client.post(
            "/markets/openai-gpt6-2026/predict",
            headers=headers,
            json={"option_id": option.id, "stake_amount": 80, "client_locale": "pt-br"},
        )
        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(blocked.json()["detail"], "Confirme seu email para liberar esta ação.")

        token = delivery.context["confirmation_url"].rstrip("/").rsplit("/", 1)[-1]
        confirmed = client.post("/auth/email-confirm/confirm", json={"token": token})
        self.assertEqual(confirmed.status_code, 200)
        session = client.get("/auth/session", headers=headers)
        self.assertTrue(session.json()["user"]["email_confirmed"])
        allowed = client.post(
            "/markets/openai-gpt6-2026/predict",
            headers=headers,
            json={"option_id": option.id, "stake_amount": 80, "client_locale": "pt-br"},
        )
        self.assertEqual(allowed.status_code, 201, allowed.json())

    def test_password_reset_request_hides_public_url_and_queues_email(self):
        user = get_user_model().objects.create_user(
            username="@resetmail",
            email="reset-mail@example.com",
            password="testpass123",
            first_name="Reset Mail",
            email_confirmed_at=timezone.now(),
        )
        client = TestClient(app)
        response = client.post("/auth/password-reset/request", json={"email": user.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reset_url"], "")
        delivery = EmailDelivery.objects.get(recipient_user=user, template_key="account.password_reset")
        self.assertIn("/password-reset/confirm/", delivery.context["reset_url"])

    def test_email_template_rendering_and_sandbox_worker_guard(self):
        template = EmailTemplate.objects.get(key="wallet.credited", locale="pt-br")
        template.subject = "Crédito: {{ amount }} GT₵"
        template.body_text = "Motivo: {{ description }}"
        template.save()
        rendered = render_template("wallet.credited", "pt-br", {"amount": 42, "description": "Teste"})
        self.assertEqual(rendered["subject"], "Crédito: 42 GT₵")
        self.assertEqual(rendered["body_text"], "Motivo: Teste")

        site_config = SiteConfig.get_solo()
        site_config.email_enabled = True
        site_config.smtp_host = "email-smtp.us-east-1.amazonaws.com"
        site_config.smtp_port = 587
        site_config.smtp_username = "smtp-user"
        site_config.default_from_email = "no-reply@gotrendlabs.com.br"
        site_config.save()
        delivery = EmailDelivery.objects.create(
            event_type="wallet.credited",
            recipient_email="person@example.com",
            template_key="wallet.credited",
            locale="pt-br",
            context={"amount": 10, "description": "sandbox"},
            idempotency_key="sandbox-guard-test",
        )
        with override_settings(
            GOTRENDLABS_SMTP_PASSWORD="smtp-secret",
            GOTRENDLABS_SMTP_API_KEY="",
            GOTRENDLABS_SES_PRODUCTION_ACCESS=False,
            GOTRENDLABS_EMAIL_SANDBOX_ALLOWLIST=set(),
        ):
            stats = process_due_email_deliveries()
        delivery.refresh_from_db()
        self.assertEqual(stats["suppressed"], 1)
        self.assertEqual(delivery.status, "suppressed")
        self.assertIn("SES sandbox guard", delivery.last_error)

    def test_operator_core_bootstrap_does_not_create_public_reputation_or_initial_grant(self):
        User = get_user_model()

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_users (
                        password, last_login, is_superuser, username, first_name, last_name, email,
                        is_staff, is_active, date_joined, preferred_language, external_provider,
                        external_subject, terms_accepted_at, terms_version, account_status,
                        deletion_requested_at, deactivated_at, is_bot
                    )
                    VALUES (
                        '', NULL, true, '@operator', 'Operator', '', 'operator@example.com',
                        true, true, NOW(), 'pt-br', '', '', NULL, '', 'active', NULL, NULL, false
                    )
                    RETURNING id
                    """
                )
                operator_id = cursor.fetchone()["id"]
                _ensure_user_core(cursor, operator_id)
                _ensure_user_core(cursor, operator_id)

        operator = User.objects.get(id=operator_id)

        self.assertFalse(UserReputation.objects.filter(user=operator).exists())
        self.assertFalse(WalletLedgerEntry.objects.filter(user=operator).exists())
        self.assertFalse(WalletLedgerEntry.objects.filter(user=operator, entry_type="grant_initial").exists())
        self.assertEqual(WalletBalance.objects.get(user=operator).available_gtl, 0)
        self.assertFalse(operator.badges.exists())
        self.assertFalse(operator.activities.exists())

    def test_badge_catalog_public_personalized_and_admin_contracts(self):
        client = TestClient(app)
        user = client.post(
            "/auth/register",
            json={"display_name": "Badge User", "email": "badge-user@example.com", "password": "testpass123", "terms_accepted": True},
        )
        staff = client.post(
            "/auth/register",
            json={"display_name": "Badge Staff", "email": "badge-staff@example.com", "password": "testpass123", "terms_accepted": True},
        )
        self.assertEqual(user.status_code, 201)
        self.assertEqual(staff.status_code, 201)
        user_headers = {"Authorization": f"Bearer {user.json()['session']['token']}"}
        staff_headers = {"Authorization": f"Bearer {staff.json()['session']['token']}"}
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("badge-staff@example.com",))

        public_catalog = client.get("/badges")
        self.assertEqual(public_catalog.status_code, 200)
        self.assertIn("badges", public_catalog.json())
        self.assertIn("founding_member", [badge["code"] for badge in public_catalog.json()["badges"]])

        personal_catalog = client.get("/badges", headers=user_headers)
        self.assertEqual(personal_catalog.status_code, 200)
        founding = next(badge for badge in personal_catalog.json()["badges"] if badge["code"] == "founding_member")
        self.assertEqual(founding["status"], "earned")
        self.assertIn("rule_description", founding)

        forbidden = client.get("/admin/badges", headers=user_headers)
        self.assertEqual(forbidden.status_code, 403)

        created = client.post(
            "/admin/badges",
            headers=staff_headers,
            json={
                "code": "one-comment",
                "name": "Um comentário",
                "description": "Comentou em um mercado.",
                "rule_description": "Publique pelo menos 1 comentário visível.",
                "badge_type": "engagement",
                "image_url": "/media/badge_images/comment.png",
                "image_dark_url": "/media/badge_images/comment-dark.png",
                "is_active": True,
                "rule_type": "comments_count",
                "threshold_value": 1,
            },
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["code"], "one-comment")
        self.assertEqual(created.json()["image_dark_url"], "/media/badge_images/comment-dark.png")

        updated = client.patch(
            "/admin/badges/one-comment",
            headers=staff_headers,
            json={
                "name": "Comentador",
                "description": "Comentou em um mercado.",
                "rule_description": "Publique pelo menos 1 comentário visível.",
                "badge_type": "engagement",
                "image_url": "",
                "image_dark_url": "",
                "is_active": True,
                "rule_type": "comments_count",
                "threshold_value": 1,
            },
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["name"], "Comentador")

        deactivated = client.post("/admin/badges/one-comment/deactivate", headers=staff_headers, json={"note": "pausar"})
        self.assertEqual(deactivated.status_code, 200)
        self.assertFalse(deactivated.json()["is_active"])

    def test_badge_awards_are_idempotent_for_automatic_rules(self):
        client = TestClient(app)
        user = client.post(
            "/auth/register",
            json={"display_name": "Badge Auto", "email": "badge-auto@example.com", "password": "testpass123", "terms_accepted": True},
        )
        self.assertEqual(user.status_code, 201)
        headers = {"Authorization": f"Bearer {user.json()['session']['token']}"}
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_badge_definitions
                        (code, name, description, rule_description, badge_type, image_url, image_dark_url, is_active, created_at, updated_at)
                    VALUES ('auto-comment', 'Comentou IA', 'Fez um comentário em IA.', 'Publique 1 comentário visível em IA/Modelos.', 'engagement', '', '', true, now(), now())
                    RETURNING id
                    """
                )
                badge_id = cursor.fetchone()["id"]
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_badge_rules
                        (badge_id, rule_type, threshold_value, category, subcategory, is_active, created_at, updated_at)
                    VALUES (%s, 'comments_count', 1, 'IA', 'Modelos', true, now(), now())
                    """,
                    (badge_id,),
                )
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_badge_definitions
                        (code, name, description, rule_description, badge_type, image_url, image_dark_url, is_active, created_at, updated_at)
                    VALUES ('auto-comment-event', 'Comentou em Geral', 'Fez um comentário no evento Geral.', 'Publique 1 comentário visível em IA/Modelos/Geral.', 'engagement', '', '', true, now(), now())
                    RETURNING id
                    """
                )
                event_badge_id = cursor.fetchone()["id"]
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_badge_rules
                        (badge_id, rule_type, threshold_value, category, subcategory, event, is_active, created_at, updated_at)
                    VALUES (%s, 'comments_count', 1, 'IA', 'Modelos', 'Geral', true, now(), now())
                    """,
                    (event_badge_id,),
                )
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_badge_definitions
                        (code, name, description, rule_description, badge_type, image_url, image_dark_url, is_active, created_at, updated_at)
                    VALUES ('auto-comment-wrong-event', 'Comentou Bitcoin', 'Fez um comentário no evento Bitcoin.', 'Publique 1 comentário visível em IA/Modelos/Bitcoin.', 'engagement', '', '', true, now(), now())
                    RETURNING id
                    """
                )
                wrong_event_badge_id = cursor.fetchone()["id"]
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_badge_rules
                        (badge_id, rule_type, threshold_value, category, subcategory, event, is_active, created_at, updated_at)
                    VALUES (%s, 'comments_count', 1, 'IA', 'Modelos', 'Bitcoin', true, now(), now())
                    """,
                    (wrong_event_badge_id,),
                )
        market = Market.objects.get(slug="openai-gpt6-2026")
        self.assertEqual(market.event.name, "Geral")
        first = client.post(f"/markets/{market.slug}/comments", headers=headers, json={"body": "Comentário que libera badge."})
        second = client.post(f"/markets/{market.slug}/comments", headers=headers, json={"body": "Outro comentário."})
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM gotrendlabs_user_badge_awards a
                    JOIN gotrendlabs_users u ON u.id = a.user_id
                    JOIN gotrendlabs_badge_definitions b ON b.id = a.badge_id
                    WHERE u.email = 'badge-auto@example.com'
                      AND b.code = 'auto-comment'
                    """
                )
                self.assertEqual(cursor.fetchone()["total"], 1)
                cursor.execute(
                    """
                    SELECT b.code, COUNT(a.id) AS total
                    FROM gotrendlabs_badge_definitions b
                    LEFT JOIN gotrendlabs_user_badge_awards a ON a.badge_id = b.id
                    LEFT JOIN gotrendlabs_users u ON u.id = a.user_id AND u.email = 'badge-auto@example.com'
                    WHERE b.code IN ('auto-comment-event', 'auto-comment-wrong-event')
                    GROUP BY b.code
                    ORDER BY b.code
                    """
                )
                awarded_by_code = {row["code"]: row["total"] for row in cursor.fetchall()}
                self.assertEqual(awarded_by_code["auto-comment-event"], 1)
                self.assertEqual(awarded_by_code["auto-comment-wrong-event"], 0)

    def test_rankings_filter_category_subcategory_recalculates_theme(self):
        client = TestClient(app)
        alpha = client.post(
            "/auth/register",
            json={"display_name": "Theme Alpha", "email": "theme-alpha@example.com", "password": "supersecret123", "terms_accepted": True},
        )
        beta = client.post(
            "/auth/register",
            json={"display_name": "Theme Beta", "email": "theme-beta@example.com", "password": "supersecret123", "terms_accepted": True},
        )
        staff = client.post(
            "/auth/register",
            json={"display_name": "Theme Staff", "email": "theme-staff@example.com", "password": "supersecret123", "terms_accepted": True},
        )
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("theme-staff@example.com",))
        staff_headers = {"Authorization": f"Bearer {staff.json()['session']['token']}"}

        market_response = client.post(
            "/admin/markets",
            headers=staff_headers,
            json={
                "title": "Ranking temático calcula reputação?",
                "slug": "ranking-theme-teste",
                "summary": "Mercado isolado para ranking temático.",
                "kind": "binary",
                "category": "IA",
                "subcategory": "Modelos",
                "source": "Fonte pública",
                "resolution_criteria": "Critério público verificável.",
                "close_at": "2026-12-31T23:59:00-03:00",
                "close_timezone": "America/Sao_Paulo",
                "thumb_color": "#d8ece2",
                "auto_close_enabled": False,
            },
        )
        self.assertEqual(market_response.status_code, 201)
        self.assertEqual(client.post("/admin/markets/ranking-theme-teste/publish", headers=staff_headers, json={"note": "publicar"}).status_code, 200)
        ia_market = Market.objects.get(slug="ranking-theme-teste")
        ia_option = MarketOption.objects.get(market=ia_market, label="SIM")
        no_option = MarketOption.objects.get(market=ia_market, label="NAO")
        alpha_prediction = client.post(
            "/markets/ranking-theme-teste/predict",
            headers={"Authorization": f"Bearer {alpha.json()['session']['token']}"},
            json={"option_id": ia_option.id, "stake_amount": 10},
        )
        beta_prediction = client.post(
            "/markets/ranking-theme-teste/predict",
            headers={"Authorization": f"Bearer {beta.json()['session']['token']}"},
            json={"option_id": no_option.id, "stake_amount": 10},
        )
        self.assertEqual(alpha_prediction.status_code, 201)
        self.assertEqual(beta_prediction.status_code, 201)
        self.assertEqual(client.post("/admin/markets/ranking-theme-teste/lock", headers=staff_headers, json={"note": "fechar"}).status_code, 200)
        resolved = client.post(
            "/admin/markets/ranking-theme-teste/resolve",
            headers=staff_headers,
            json={"winning_option_id": ia_option.id, "source_url": "https://example.com/ranking", "note": "resolver"},
        )
        self.assertEqual(resolved.status_code, 200)
        theme_badge = BadgeDefinition.objects.create(
            code="theme_ranking_badge",
            name="Badge temática",
            description="Conquista temática.",
            image_url="/media/badge_images/theme.png",
            is_active=True,
        )
        UserBadgeAward.objects.create(user=get_user_model().objects.get(username="@themealpha"), badge=theme_badge, awarded_at=timezone.now(), reason_snapshot="ranking:theme")

        global_ranking = client.get("/rankings")
        self.assertEqual(global_ranking.status_code, 200)
        self.assertIn("rows", global_ranking.json())

        category = client.get("/rankings", params={"category": "ia"})
        self.assertEqual(category.status_code, 200)
        payload = category.json()
        self.assertEqual(payload["selected_category"], "ia")
        self.assertIn("IA", [item["name"] for item in payload["categories"]])
        handles = [row["handle"] for row in payload["rows"]]
        self.assertIn("@themealpha", handles)
        self.assertIn("@themebeta", handles)
        self.assertLess(handles.index("@themealpha"), handles.index("@themebeta"))
        alpha_row = next(row for row in payload["rows"] if row["handle"] == "@themealpha")
        beta_row = next(row for row in payload["rows"] if row["handle"] == "@themebeta")
        self.assertEqual(alpha_row["reputation_score"], 105)
        self.assertEqual(alpha_row["accuracy_indicator"], "100%")
        self.assertEqual(alpha_row["badges"][0]["code"], "theme_ranking_badge")
        self.assertEqual(beta_row["reputation_score"], 95)

        subcategory = client.get("/rankings", params={"category": "ia", "subcategory": "modelos"})
        self.assertEqual(subcategory.status_code, 200)
        self.assertEqual(subcategory.json()["selected_subcategory"], "modelos")
        subcategory_handles = [row["handle"] for row in subcategory.json()["rows"]]
        self.assertIn("@themealpha", subcategory_handles)
        self.assertIn("@themebeta", subcategory_handles)
        event = client.get("/rankings", params={"category": "ia", "subcategory": "modelos", "event": "geral"})
        self.assertEqual(event.status_code, 200)
        self.assertEqual(event.json()["selected_event"], "geral")
        event_handles = [row["handle"] for row in event.json()["rows"]]
        self.assertIn("@themealpha", event_handles)
        self.assertIn("@themebeta", event_handles)
        event_alpha_row = next(row for row in event.json()["rows"] if row["handle"] == "@themealpha")
        self.assertEqual(event_alpha_row["strong_category"], "Geral")
        ia_category = next(item for item in event.json()["categories"] if item["slug"] == "ia")
        modelos_subcategory = next(item for item in ia_category["subcategories"] if item["slug"] == "modelos")
        self.assertIn("geral", [item["slug"] for item in modelos_subcategory["events"]])

        empty = client.get("/rankings", params={"category": "politica", "subcategory": "regulacao"})
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json()["rows"], [])

    def test_rankings_exclude_staff_and_superusers(self):
        client = TestClient(app)
        regular = client.post(
            "/auth/register",
            json={"display_name": "Ranking Regular", "email": "ranking-regular@example.com", "password": "supersecret123", "terms_accepted": True},
        )
        staff = client.post(
            "/auth/register",
            json={"display_name": "Ranking Staff", "email": "ranking-staff@example.com", "password": "supersecret123", "terms_accepted": True},
        )
        superuser = client.post(
            "/auth/register",
            json={"display_name": "Ranking Super", "email": "ranking-super@example.com", "password": "supersecret123", "terms_accepted": True},
        )
        dev_user = client.post(
            "/auth/register",
            json={"display_name": "Dev Ranking", "email": "dev-ranking@example.com", "password": "supersecret123", "terms_accepted": True},
        )
        self.assertEqual(regular.status_code, 201)
        self.assertEqual(staff.status_code, 201)
        self.assertEqual(superuser.status_code, 201)
        self.assertEqual(dev_user.status_code, 201)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("ranking-staff@example.com",))
                cursor.execute("UPDATE gotrendlabs_users SET is_superuser = true WHERE email = %s", ("ranking-super@example.com",))
                cursor.execute(
                    """
                    UPDATE gotrendlabs_user_reputations r
                    SET reputation_score = CASE u.email
                        WHEN 'ranking-regular@example.com' THEN 120
                        WHEN 'ranking-staff@example.com' THEN 999
                        WHEN 'ranking-super@example.com' THEN 998
                        WHEN 'dev-ranking@example.com' THEN 997
                        ELSE r.reputation_score
                    END
                    FROM gotrendlabs_users u
                    WHERE r.user_id = u.id
                    """
                )
                cursor.execute(
                    """
                    UPDATE gotrendlabs_user_reputations r
                    SET strong_category = 'DEV Ranking'
                    FROM gotrendlabs_users u
                    WHERE r.user_id = u.id
                      AND u.email = %s
                    """,
                    ("dev-ranking@example.com",),
                )

        ranking = client.get("/rankings")
        self.assertEqual(ranking.status_code, 200)
        handles = [row["handle"] for row in ranking.json()["rows"]]
        self.assertIn("@rankingregular", handles)
        self.assertNotIn("@rankingstaff", handles)
        self.assertNotIn("@rankingsuper", handles)
        self.assertNotIn("@devranking", handles)

    def test_register_requires_terms_profile_update_and_logical_deletion(self):
        client = TestClient(app)
        missing_terms = client.post(
            "/auth/register",
            json={
                "display_name": "Policy Case",
                "email": "policy-case@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": False,
            },
        )
        self.assertEqual(missing_terms.status_code, 422)

        response = client.post(
            "/auth/register",
            json={
                "display_name": "Policy Case",
                "email": "policy-case@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(response.status_code, 201)
        token = response.json()["session"]["token"]
        headers = {"Authorization": f"Bearer {token}"}
        user = get_user_model().objects.get(username="@policycase")
        self.assertEqual(user.terms_version, "2026-05-17")
        self.assertIsNotNone(user.terms_accepted_at)

        updated = client.patch(
            "/users/me",
            headers=headers,
            json={
                "display_name": "Policy Updated",
                "handle": "policyupdated",
                "email": "policy-updated@example.com",
                "preferred_language": "en",
                "birth_date": "1990-04-23",
                "sex": "prefer_not_to_say",
                "bio": "Updated bio",
            },
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["user"]["handle"], "@policyupdated")
        self.assertEqual(updated.json()["user"]["email"], "policy-updated@example.com")
        self.assertEqual(updated.json()["user"]["preferred_language"], "en")
        self.assertEqual(updated.json()["user"]["display_name"], "Policy Updated")
        self.assertEqual(updated.json()["birth_date"], "1990-04-23")
        self.assertEqual(updated.json()["sex"], "prefer_not_to_say")
        user.profile.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(user.profile.display_name, "Policy Updated")
        self.assertEqual(user.first_name, "Policy Updated")
        self.assertEqual(user.profile.birth_date.isoformat(), "1990-04-23")
        self.assertEqual(user.profile.sex, "prefer_not_to_say")
        self.assertIsNone(user.email_confirmed_at)
        get_user_model().objects.filter(id=user.id).update(email_confirmed_at=timezone.now())

        cleared = client.patch(
            "/users/me",
            headers=headers,
            json={"birth_date": None, "sex": ""},
        )
        self.assertEqual(cleared.status_code, 200)
        self.assertIsNone(cleared.json()["birth_date"])
        self.assertEqual(cleared.json()["sex"], "")

        future_date = client.patch("/users/me", headers=headers, json={"birth_date": "2999-01-01"})
        self.assertEqual(future_date.status_code, 422)

        invalid_sex = client.patch("/users/me", headers=headers, json={"sex": "invalid"})
        self.assertEqual(invalid_sex.status_code, 422)

        public_profile = client.get("/users/policyupdated")
        self.assertEqual(public_profile.status_code, 200)
        self.assertNotIn("email", public_profile.json()["user"])
        self.assertNotIn("birth_date", public_profile.json())
        self.assertNotIn("sex", public_profile.json())
        self.assertNotIn("profile_id", public_profile.json())
        self.assertNotIn("profile_created_at", public_profile.json())
        self.assertNotIn("profile_updated_at", public_profile.json())

        deletion = client.post("/auth/account-deletion-request", headers=headers)
        self.assertEqual(deletion.status_code, 204)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertEqual(user.account_status, "deactivated")
        self.assertIsNotNone(user.deactivated_at)

        blocked_login = client.post(
            "/auth/login",
            json={"email": "policy-updated@example.com", "password": "testpass123"},
        )
        self.assertEqual(blocked_login.status_code, 401)
        blocked_session = client.get("/users/me", headers=headers)
        self.assertEqual(blocked_session.status_code, 401)

    def test_recaptcha_blocks_register_and_guest_queue_when_required(self):
        client = TestClient(app)

        with patch("backend_api.main.verify_recaptcha_response", side_effect=RecaptchaError("Confirme que você não é um robô.")):
            blocked_register = client.post(
                "/auth/register",
                json={
                    "display_name": "Captcha User",
                    "email": "captcha-user@example.com",
                    "language": "pt-br",
                    "password": "testpass123",
                    "terms_accepted": True,
                },
            )
            self.assertEqual(blocked_register.status_code, 422)
            self.assertIn("robô", blocked_register.json()["detail"])

            blocked_suggestion = client.post(
                "/suggestions",
                json={
                    "guest_name": "Visitante",
                    "guest_email": "visitante-sugestao@example.com",
                    "question": "A Apple lançará app IA próprio em 2026?",
                    "category": "IA",
                    "kind": "binary",
                    "suggested_source": "Apple Newsroom",
                    "rationale": "Fonte pública.",
                },
            )
            self.assertEqual(blocked_suggestion.status_code, 422)

            blocked_feedback = client.post(
                "/feedback",
                json={
                    "guest_name": "Visitante",
                    "guest_email": "visitante-feedback@example.com",
                    "feedback_type": "Ideia de melhoria",
                    "severity": "low",
                    "description": "Melhorar filtros.",
                },
            )
            self.assertEqual(blocked_feedback.status_code, 422)

    def test_recaptcha_not_required_for_authenticated_queue_items(self):
        client = TestClient(app)
        user_register = client.post(
            "/auth/register",
            json={
                "display_name": "Captcha Bypass",
                "email": "captcha-bypass@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(user_register.status_code, 201)
        headers = {"Authorization": f"Bearer {user_register.json()['session']['token']}"}

        with patch("backend_api.main.verify_recaptcha_response", side_effect=AssertionError("CAPTCHA should not run for authenticated queue items")):
            suggestion = client.post(
                "/suggestions",
                headers=headers,
                json={
                    "question": "A Microsoft lançará novo modelo aberto em 2026?",
                    "category": "IA",
                    "kind": "binary",
                    "suggested_source": "Microsoft Blog",
                    "rationale": "Fonte pública.",
                },
            )
            self.assertEqual(suggestion.status_code, 201)

            feedback = client.post(
                "/feedback",
                headers=headers,
                json={
                    "feedback_type": "Ideia de melhoria",
                    "severity": "low",
                    "description": "Melhorar filtros.",
                },
            )
            self.assertEqual(feedback.status_code, 201)

    def test_wallet_mutation_writes_ledger_and_balance_atomically(self):
        User = get_user_model()
        user = User.objects.create_user(username="walletcase", email="walletcase@example.com", password="testpass123")

        from django.db import connection

        with connection.cursor() as cursor:
            entry_id = _record_wallet_entry(
                cursor,
                user.id,
                entry_type="manual_adjustment",
                amount=55,
                direction="credit",
                description="Crédito de teste",
                reference_type="manual_test",
                reference_id="walletcase-55",
            )

        self.assertTrue(WalletLedgerEntry.objects.filter(id=entry_id, user=user, amount=55).exists())
        balance = WalletBalance.objects.get(user=user)
        self.assertEqual(balance.available_gtl, 55)
        self.assertEqual(balance.locked_gtl, 0)

    def test_prediction_stake_locks_wallet_updates_market_and_blocks_duplicate_user_entry(self):
        client = TestClient(app)
        user_register = client.post(
            "/auth/register",
            json={
                "display_name": "Prediction User",
                "email": "prediction-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(user_register.status_code, 201)
        user_headers = {"Authorization": f"Bearer {user_register.json()['session']['token']}"}
        option = MarketOption.objects.get(market__slug="openai-gpt6-2026", label="SIM")

        response = client.post(
            "/markets/openai-gpt6-2026/predict",
            headers=user_headers,
            json={"option_id": option.id, "stake_amount": 80, "client_locale": "pt-br"},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["stake_amount"], 80)
        self.assertEqual(payload["option_id"], option.id)
        self.assertEqual(payload["potential_payout"], int((Decimal(80) * Decimal("100") / option.probability_exact).to_integral_value()))
        self.assertEqual(
            sum(Decimal(str(item["probability_exact"])) for item in payload["market_probability_snapshot"]),
            Decimal("100.0000"),
        )

        user = get_user_model().objects.get(username="@predictionuser")
        self.assertTrue(Prediction.objects.filter(id=payload["prediction_id"], user=user, market__slug="openai-gpt6-2026").exists())
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_stake_lock", direction="lock", amount=80, reference_id=str(payload["prediction_id"])).exists())
        balance = WalletBalance.objects.get(user=user)
        self.assertEqual(balance.available_gtl, 1920)
        self.assertEqual(balance.locked_gtl, 80)
        option.refresh_from_db()
        self.assertGreater(option.probability_exact, Decimal("50.0000"))

        duplicate = client.post(
            "/markets/openai-gpt6-2026/predict",
            headers=user_headers,
            json={"option_id": option.id, "stake_amount": 20, "client_locale": "pt-br"},
        )
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(Prediction.objects.filter(user=user, market__slug="openai-gpt6-2026").count(), 1)

        other_register = client.post(
            "/auth/register",
            json={
                "display_name": "Other Prediction User",
                "email": "other-prediction-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(other_register.status_code, 201)
        other_headers = {"Authorization": f"Bearer {other_register.json()['session']['token']}"}
        other_prediction = client.post(
            "/markets/openai-gpt6-2026/predict",
            headers=other_headers,
            json={"option_id": option.id, "stake_amount": 25, "client_locale": "pt-br"},
        )
        self.assertEqual(other_prediction.status_code, 201)

        invalid_option = MarketOption.objects.get(market__slug="tiktok-ban-eua-2026", label="SIM")
        option_error = client.post(
            "/markets/openai-gpt6-2026/predict",
            headers=other_headers,
            json={"option_id": invalid_option.id, "stake_amount": 10, "client_locale": "pt-br"},
        )
        self.assertEqual(option_error.status_code, 422)

        closed_option = MarketOption.objects.get(market__slug="tiktok-resolvido-2026", label="NAO")
        closed_market = client.post(
            "/markets/tiktok-resolvido-2026/predict",
            headers=user_headers,
            json={"option_id": closed_option.id, "stake_amount": 10, "client_locale": "pt-br"},
        )
        self.assertEqual(closed_market.status_code, 422)

        insufficient_option = MarketOption.objects.get(market__slug="tiktok-ban-eua-2026", label="SIM")
        insufficient = client.post(
            "/markets/tiktok-ban-eua-2026/predict",
            headers=user_headers,
            json={"option_id": insufficient_option.id, "stake_amount": 5000, "client_locale": "pt-br"},
        )
        self.assertEqual(insufficient.status_code, 422)

        unauthenticated = client.post(
            "/markets/tiktok-ban-eua-2026/predict",
            json={"option_id": insufficient_option.id, "stake_amount": 10, "client_locale": "pt-br"},
        )
        self.assertEqual(unauthenticated.status_code, 401)

    def test_admin_resolve_market_applies_payout_loss_and_reputation_formula(self):
        client = TestClient(app)
        staff_register = client.post(
            "/auth/register",
            json={
                "display_name": "Resolution Staff",
                "email": "resolution-staff@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        winner_register = client.post(
            "/auth/register",
            json={
                "display_name": "Resolution Winner",
                "email": "resolution-winner@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        loser_register = client.post(
            "/auth/register",
            json={
                "display_name": "Resolution Loser",
                "email": "resolution-loser@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(staff_register.status_code, 201)
        self.assertEqual(winner_register.status_code, 201)
        self.assertEqual(loser_register.status_code, 201)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("resolution-staff@example.com",))

        staff_headers = {"Authorization": f"Bearer {staff_register.json()['session']['token']}"}
        winner_headers = {"Authorization": f"Bearer {winner_register.json()['session']['token']}"}
        loser_headers = {"Authorization": f"Bearer {loser_register.json()['session']['token']}"}
        market_response = client.post(
            "/admin/markets",
            headers=staff_headers,
            json={
                "title": "Mercado de resolução MVP?",
                "slug": "resolucao-mvp-teste",
                "summary": "Mercado isolado para testar resolução.",
                "kind": "binary",
                "category": "IA",
                "subcategory": "Modelos",
                "source": "Fonte pública",
                "resolution_criteria": "Critério público verificável.",
                "close_at": "2026-12-31T23:59:00-03:00",
                "close_timezone": "America/Sao_Paulo",
                "thumb_color": "#d8ece2",
                "auto_close_enabled": False,
            },
        )
        self.assertEqual(market_response.status_code, 201)
        publish_response = client.post("/admin/markets/resolucao-mvp-teste/publish", headers=staff_headers, json={"note": "publicar"})
        self.assertEqual(publish_response.status_code, 200)
        winning_option = MarketOption.objects.get(market__slug="resolucao-mvp-teste", label="SIM")
        losing_option = MarketOption.objects.get(market__slug="resolucao-mvp-teste", label="NAO")

        winner_prediction_response = client.post(
            "/markets/resolucao-mvp-teste/predict",
            headers=winner_headers,
            json={"option_id": winning_option.id, "stake_amount": 100, "client_locale": "pt-br"},
        )
        loser_prediction_response = client.post(
            "/markets/resolucao-mvp-teste/predict",
            headers=loser_headers,
            json={"option_id": losing_option.id, "stake_amount": 100, "client_locale": "pt-br"},
        )
        self.assertEqual(winner_prediction_response.status_code, 201)
        self.assertEqual(loser_prediction_response.status_code, 201)
        winner_prediction = Prediction.objects.get(id=winner_prediction_response.json()["prediction_id"])
        loser_prediction = Prediction.objects.get(id=loser_prediction_response.json()["prediction_id"])
        lock_response = client.post("/admin/markets/resolucao-mvp-teste/lock", headers=staff_headers, json={"note": "fechar"})
        self.assertEqual(lock_response.status_code, 200)
        lifecycle_market_id = Market.objects.get(slug="resolucao-mvp-teste").id
        self.assertTrue(UserNotification.objects.filter(recipient_id=winner_register.json()["user"]["id"], event_type="market_locked", source_key=f"market_locked:{lifecycle_market_id}").exists())
        self.assertTrue(UserNotification.objects.filter(recipient_id=loser_register.json()["user"]["id"], event_type="market_locked", source_key=f"market_locked:{lifecycle_market_id}").exists())
        audit_locked = client.get("/admin/markets/resolucao-mvp-teste/resolution-audit", headers=staff_headers)
        self.assertEqual(audit_locked.status_code, 422)

        non_staff = client.post(
            "/admin/markets/resolucao-mvp-teste/resolve",
            headers=winner_headers,
            json={"winning_option_id": winning_option.id, "source_url": "https://fonte.example/resolucao", "note": "Fonte validada."},
        )
        self.assertEqual(non_staff.status_code, 403)
        invalid_option = MarketOption.objects.get(market__slug="tiktok-ban-eua-2026", label="SIM")
        invalid = client.post(
            "/admin/markets/resolucao-mvp-teste/resolve",
            headers=staff_headers,
            json={"winning_option_id": invalid_option.id, "source_url": "https://fonte.example/resolucao", "note": "Fonte validada."},
        )
        self.assertEqual(invalid.status_code, 422)

        resolved = client.post(
            "/admin/markets/resolucao-mvp-teste/resolve",
            headers=staff_headers,
            json={
                "winning_option_id": winning_option.id,
                "source_url": "https://fonte.example/resolucao",
                "note": "Fonte validada.",
                "resolved_at": "2026-05-18T20:03:00",
                "resolution_timezone": "America/Sao_Paulo",
            },
        )
        self.assertEqual(resolved.status_code, 200)
        self.assertEqual(resolved.json()["status"], "resolved")
        self.assertEqual(resolved.json()["winning_option_id"], winning_option.id)
        self.assertIn("Fonte:", resolved.json()["resolution_note"])
        self.assertEqual(resolved.json()["resolution_timezone"], "America/Sao_Paulo")
        self.assertEqual(resolved.json()["resolved_at_label"], "18/05/2026 20:03 America/Sao_Paulo")
        self.assertTrue(UserNotification.objects.filter(recipient_id=winner_register.json()["user"]["id"], event_type="market_resolved", source_key=f"market_resolved:{lifecycle_market_id}").exists())
        self.assertTrue(UserNotification.objects.filter(recipient_id=loser_register.json()["user"]["id"], event_type="market_resolved", source_key=f"market_resolved:{lifecycle_market_id}").exists())

        winner_prediction.refresh_from_db()
        loser_prediction.refresh_from_db()
        self.assertEqual(winner_prediction.status, "resolved")
        self.assertTrue(winner_prediction.won)
        self.assertEqual(loser_prediction.status, "resolved")
        self.assertFalse(loser_prediction.won)
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_refund", direction="release", reference_id=str(winner_prediction.id), amount=100).exists())
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_payout", direction="credit", reference_id=str(winner_prediction.id), amount=winner_prediction.potential_payout - 100).exists())
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_loss", direction="settle", reference_id=str(loser_prediction.id), amount=100).exists())
        self.assertTrue(
            UserNotification.objects.filter(
                recipient_id=winner_register.json()["user"]["id"],
                event_type="wallet_credit",
                metadata__entry_type="prediction_payout",
                metadata__reference_id=str(winner_prediction.id),
            ).exists()
        )

        winner_balance = WalletBalance.objects.get(user__username="@resolutionwinner")
        loser_balance = WalletBalance.objects.get(user__username="@resolutionloser")
        self.assertEqual(winner_balance.available_gtl, 1900 + winner_prediction.potential_payout)
        self.assertEqual(winner_balance.locked_gtl, 0)
        self.assertEqual(loser_balance.available_gtl, 1900)
        self.assertEqual(loser_balance.locked_gtl, 0)

        winner_p = Decimal(winner_prediction.probability_at_entry) / Decimal("100")
        loser_p = Decimal(loser_prediction.probability_at_entry) / Decimal("100")
        winner_delta = int((Decimal("10") * (Decimal("1") - winner_p)).to_integral_value(rounding=ROUND_HALF_UP))
        loser_delta = int((-(Decimal("10") * loser_p)).to_integral_value(rounding=ROUND_HALF_UP))
        self.assertEqual(UserReputation.objects.get(user__username="@resolutionwinner").reputation_score, 100 + winner_delta)
        self.assertEqual(UserReputation.objects.get(user__username="@resolutionwinner").accuracy_indicator, "100%")
        self.assertEqual(UserReputation.objects.get(user__username="@resolutionloser").reputation_score, 100 + loser_delta)
        self.assertEqual(UserReputation.objects.get(user__username="@resolutionloser").accuracy_indicator, "0%")
        self.assertTrue(UserBadgeAward.objects.filter(user__username="@resolutionwinner", badge__code="first_resolution").exists())
        self.assertTrue(UserBadgeAward.objects.filter(user__username="@resolutionloser", badge__code="first_resolution").exists())
        self.assertTrue(UserNotification.objects.filter(recipient_id=winner_register.json()["user"]["id"], event_type="badge_awarded", source_key="badge_awarded:first_resolution").exists())
        self.assertTrue(UserNotification.objects.filter(recipient_id=loser_register.json()["user"]["id"], event_type="badge_awarded", source_key="badge_awarded:first_resolution").exists())
        self.assertTrue(AdminEvent.objects.filter(action="market.resolve", entity_identifier="resolucao-mvp-teste").exists())
        audit_non_staff = client.get("/admin/markets/resolucao-mvp-teste/resolution-audit", headers=winner_headers)
        self.assertEqual(audit_non_staff.status_code, 403)
        audit = client.get("/admin/markets/resolucao-mvp-teste/resolution-audit", headers=staff_headers, params={"limit": 1, "offset": 0})
        self.assertEqual(audit.status_code, 200)
        audit_payload = audit.json()
        self.assertEqual(audit_payload["market"]["slug"], "resolucao-mvp-teste")
        self.assertEqual(audit_payload["market"]["winning_option_id"], winning_option.id)
        self.assertEqual(audit_payload["summary"]["predictions_total"], 2)
        self.assertEqual(audit_payload["summary"]["winners_total"], 1)
        self.assertEqual(audit_payload["summary"]["losers_total"], 1)
        self.assertEqual(audit_payload["summary"]["stake_total"], 200)
        self.assertEqual(audit_payload["summary"]["refund_total"], 100)
        self.assertEqual(audit_payload["summary"]["payout_total"], winner_prediction.potential_payout - 100)
        self.assertEqual(audit_payload["summary"]["loss_total"], 100)
        self.assertGreaterEqual(audit_payload["summary"]["badge_awards_total"], 2)
        self.assertEqual(audit_payload["pagination"], {"limit": 1, "offset": 0, "total": 2})
        self.assertEqual(len(audit_payload["participants"]), 1)
        self.assertIn("prediction_refund", audit_payload["participants"][0]["ledger"])

        duplicate = client.post(
            "/admin/markets/resolucao-mvp-teste/resolve",
            headers=staff_headers,
            json={"winning_option_id": winning_option.id, "source_url": "https://fonte.example/resolucao", "note": "Duplicada."},
        )
        self.assertEqual(duplicate.status_code, 422)
        cancel_resolved = client.post("/admin/markets/resolucao-mvp-teste/cancel", headers=staff_headers, json={"note": "cancelar resolução e aplicar refund"})
        self.assertEqual(cancel_resolved.status_code, 200)
        self.assertEqual(cancel_resolved.json()["status"], "locked")
        self.assertIsNone(cancel_resolved.json()["resolved_at"])
        self.assertIsNone(cancel_resolved.json()["winning_option_id"])
        winner_prediction.refresh_from_db()
        loser_prediction.refresh_from_db()
        self.assertEqual(winner_prediction.status, "open")
        self.assertIsNone(winner_prediction.won)
        self.assertEqual(loser_prediction.status, "open")
        self.assertIsNone(loser_prediction.won)
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_payout_reversal", direction="debit", reference_id=str(winner_prediction.id), amount=winner_prediction.potential_payout - 100).exists())
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_refund", direction="credit", reference_id=str(loser_prediction.id), amount=100).exists())
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_resolution_relock", direction="lock", reference_id=str(winner_prediction.id), amount=100).exists())
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_resolution_relock", direction="lock", reference_id=str(loser_prediction.id), amount=100).exists())
        winner_balance.refresh_from_db()
        loser_balance.refresh_from_db()
        self.assertEqual(winner_balance.available_gtl, 1900)
        self.assertEqual(winner_balance.locked_gtl, 100)
        self.assertEqual(loser_balance.available_gtl, 1900)
        self.assertEqual(loser_balance.locked_gtl, 100)
        self.assertEqual(UserReputation.objects.get(user__username="@resolutionwinner").reputation_score, 100)
        self.assertEqual(UserReputation.objects.get(user__username="@resolutionwinner").resolved_predictions_count, 0)
        self.assertEqual(UserReputation.objects.get(user__username="@resolutionloser").reputation_score, 100)
        self.assertEqual(UserReputation.objects.get(user__username="@resolutionloser").resolved_predictions_count, 0)
        self.assertTrue(AdminEvent.objects.filter(action="market.resolution_undo", entity_identifier="resolucao-mvp-teste").exists())
        duplicate_cancel = client.post("/admin/markets/resolucao-mvp-teste/cancel", headers=staff_headers, json={"note": "segunda tentativa"})
        self.assertEqual(duplicate_cancel.status_code, 200)
        self.assertEqual(duplicate_cancel.json()["status"], "canceled")

    def test_market_resolution_distribution_math_undo_and_refund_audit(self):
        client = TestClient(app)
        users = {}
        for key, display_name, email in [
            ("staff", "Audit Staff", "audit-staff@example.com"),
            ("winner", "Audit Winner", "audit-winner@example.com"),
            ("loser_mid", "Audit Loser Mid", "audit-loser-mid@example.com"),
            ("loser_long", "Audit Loser Long", "audit-loser-long@example.com"),
            ("winner_small", "Audit Winner Small", "audit-winner-small@example.com"),
        ]:
            response = client.post(
                "/auth/register",
                json={
                    "display_name": display_name,
                    "email": email,
                    "language": "pt-br",
                    "password": "testpass123",
                    "terms_accepted": True,
                },
            )
            self.assertEqual(response.status_code, 201)
            users[key] = {
                "token": response.json()["session"]["token"],
                "headers": {"Authorization": f"Bearer {response.json()['session']['token']}"},
            }
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("audit-staff@example.com",))

        market_response = client.post(
            "/admin/markets",
            headers=users["staff"]["headers"],
            json={
                "title": "Auditoria de distribuição MVP?",
                "slug": "auditoria-distribuicao-mvp",
                "summary": "Mercado isolado para auditar matemática de liquidação.",
                "kind": "multiple",
                "category": "IA",
                "subcategory": "Modelos",
                "source": "Fonte pública",
                "resolution_criteria": "Critério público verificável.",
                "close_at": "2026-12-31T23:59:00-03:00",
                "close_timezone": "America/Sao_Paulo",
                "thumb_color": "#d8ece2",
                "auto_close_enabled": False,
                "options": [
                    {"label": "Azul"},
                    {"label": "Verde"},
                    {"label": "Cinza"},
                ],
            },
        )
        self.assertEqual(market_response.status_code, 201)
        self.assertEqual(client.post("/admin/markets/auditoria-distribuicao-mvp/publish", headers=users["staff"]["headers"], json={"note": "publicar"}).status_code, 200)
        option_probabilities = {"Azul": Decimal("25.0000"), "Verde": Decimal("60.0000"), "Cinza": Decimal("15.0000")}
        options = {option.label: option for option in MarketOption.objects.filter(market__slug="auditoria-distribuicao-mvp")}
        prediction_plan = {
            "winner": {"option": "Verde", "stake": 150, "won": True},
            "loser_mid": {"option": "Azul", "stake": 120, "won": False},
            "loser_long": {"option": "Cinza", "stake": 90, "won": False},
            "winner_small": {"option": "Verde", "stake": 75, "won": True},
        }
        predictions = {}
        for key, plan in prediction_plan.items():
            p_percent = option_probabilities[plan["option"]]
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE gotrendlabs_market_options SET probability_exact = %s WHERE id = %s",
                        (p_percent, options[plan["option"]].id),
                    )
            response = client.post(
                "/markets/auditoria-distribuicao-mvp/predict",
                headers=users[key]["headers"],
                json={"option_id": options[plan["option"]].id, "stake_amount": plan["stake"], "client_locale": "pt-br"},
            )
            self.assertEqual(response.status_code, 201)
            prediction = Prediction.objects.get(id=response.json()["prediction_id"])
            predictions[key] = prediction
            expected_payout_total = int((Decimal(plan["stake"]) * Decimal("100") / p_percent).to_integral_value())
            self.assertEqual(prediction.probability_at_entry, p_percent)
            self.assertEqual(prediction.potential_payout, expected_payout_total)
            balance = WalletBalance.objects.get(user__username=f"@audit{key.replace('_', '')}")
            self.assertEqual(balance.available_gtl, 2000 - plan["stake"])
            self.assertEqual(balance.locked_gtl, plan["stake"])

        self.assertEqual(client.post("/admin/markets/auditoria-distribuicao-mvp/lock", headers=users["staff"]["headers"], json={"note": "fechar"}).status_code, 200)
        resolved = client.post(
            "/admin/markets/auditoria-distribuicao-mvp/resolve",
            headers=users["staff"]["headers"],
            json={"winning_option_id": options["Verde"].id, "source_url": "https://fonte.example/auditoria", "note": "Resultado auditado."},
        )
        self.assertEqual(resolved.status_code, 200)
        self.assertEqual(resolved.json()["status"], "resolved")

        for key, plan in prediction_plan.items():
            prediction = predictions[key]
            prediction.refresh_from_db()
            p = prediction.probability_at_entry / Decimal("100")
            expected_delta = int((Decimal("10") * (Decimal("1") - p if plan["won"] else -p)).to_integral_value(rounding=ROUND_HALF_UP))
            expected_payout_total = int((Decimal(plan["stake"]) * Decimal("100") / prediction.probability_at_entry).to_integral_value())
            expected_net_payout = max(0, expected_payout_total - plan["stake"])
            expected_available = 2000 + expected_net_payout if plan["won"] else 2000 - plan["stake"]
            expected_earned = expected_net_payout if plan["won"] else 0

            self.assertEqual(prediction.status, "resolved")
            self.assertEqual(prediction.won, plan["won"])
            balance = WalletBalance.objects.get(user__username=f"@audit{key.replace('_', '')}")
            self.assertEqual(balance.available_gtl, expected_available)
            self.assertEqual(balance.locked_gtl, 0)
            self.assertEqual(balance.total_earned_gtl, expected_earned)
            reputation = UserReputation.objects.get(user__username=f"@audit{key.replace('_', '')}")
            self.assertEqual(reputation.reputation_score, 100 + expected_delta)
            self.assertEqual(reputation.resolved_predictions_count, 1)
            self.assertEqual(reputation.accuracy_indicator, "100%" if plan["won"] else "0%")
            if plan["won"]:
                self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_refund", direction="release", reference_id=str(prediction.id), amount=plan["stake"]).exists())
                self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_payout", direction="credit", reference_id=str(prediction.id), amount=expected_net_payout).exists())
            else:
                self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_loss", direction="settle", reference_id=str(prediction.id), amount=plan["stake"]).exists())
                self.assertFalse(WalletLedgerEntry.objects.filter(entry_type="prediction_payout", reference_id=str(prediction.id)).exists())

        undo = client.post("/admin/markets/auditoria-distribuicao-mvp/cancel", headers=users["staff"]["headers"], json={"note": "desfazer resolução auditada"})
        self.assertEqual(undo.status_code, 200)
        self.assertEqual(undo.json()["status"], "locked")
        self.assertIsNone(undo.json()["winning_option_id"])
        self.assertIsNone(undo.json()["resolved_at"])

        for key, plan in prediction_plan.items():
            prediction = predictions[key]
            prediction.refresh_from_db()
            balance = WalletBalance.objects.get(user__username=f"@audit{key.replace('_', '')}")
            self.assertEqual(prediction.status, "open")
            self.assertIsNone(prediction.won)
            self.assertEqual(balance.available_gtl, 2000 - plan["stake"])
            self.assertEqual(balance.locked_gtl, plan["stake"])
            self.assertEqual(balance.total_earned_gtl, 0)
            reputation = UserReputation.objects.get(user__username=f"@audit{key.replace('_', '')}")
            self.assertEqual(reputation.reputation_score, 100)
            self.assertEqual(reputation.resolved_predictions_count, 0)
            self.assertEqual(reputation.accuracy_indicator, "0%")
            self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_resolution_relock", direction="lock", reference_id=str(prediction.id), amount=plan["stake"]).exists())

        canceled = client.post("/admin/markets/auditoria-distribuicao-mvp/cancel", headers=users["staff"]["headers"], json={"note": "refund final"})
        self.assertEqual(canceled.status_code, 200)
        self.assertEqual(canceled.json()["status"], "canceled")
        for key, plan in prediction_plan.items():
            prediction = predictions[key]
            prediction.refresh_from_db()
            balance = WalletBalance.objects.get(user__username=f"@audit{key.replace('_', '')}")
            self.assertEqual(prediction.status, "canceled")
            self.assertIsNone(prediction.won)
            self.assertEqual(balance.available_gtl, 2000)
            self.assertEqual(balance.locked_gtl, 0)
            self.assertEqual(balance.total_earned_gtl, 0)
            self.assertEqual(UserReputation.objects.get(user__username=f"@audit{key.replace('_', '')}").reputation_score, 100)
            self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_refund", direction="release", reference_id=str(prediction.id), amount=plan["stake"]).exists())

    def test_admin_cancel_market_refunds_open_predictions_without_reputation_change(self):
        client = TestClient(app)
        staff_register = client.post(
            "/auth/register",
            json={
                "display_name": "Cancel Staff",
                "email": "cancel-staff@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        user_register = client.post(
            "/auth/register",
            json={
                "display_name": "Cancel User",
                "email": "cancel-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(staff_register.status_code, 201)
        self.assertEqual(user_register.status_code, 201)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("cancel-staff@example.com",))
        staff_headers = {"Authorization": f"Bearer {staff_register.json()['session']['token']}"}
        user_headers = {"Authorization": f"Bearer {user_register.json()['session']['token']}"}
        market_response = client.post(
            "/admin/markets",
            headers=staff_headers,
            json={
                "title": "Mercado de cancelamento MVP?",
                "slug": "cancelamento-refund-teste",
                "summary": "Mercado isolado para testar refund.",
                "kind": "binary",
                "category": "IA",
                "subcategory": "Modelos",
                "source": "Fonte pública",
                "resolution_criteria": "Critério público verificável.",
                "close_at": "2026-12-31T23:59:00-03:00",
                "close_timezone": "America/Sao_Paulo",
                "thumb_color": "#d8ece2",
                "auto_close_enabled": False,
            },
        )
        self.assertEqual(market_response.status_code, 201)
        publish_response = client.post("/admin/markets/cancelamento-refund-teste/publish", headers=staff_headers, json={"note": "publicar"})
        self.assertEqual(publish_response.status_code, 200)
        option = MarketOption.objects.get(market__slug="cancelamento-refund-teste", label="SIM")
        prediction_response = client.post(
            "/markets/cancelamento-refund-teste/predict",
            headers=user_headers,
            json={"option_id": option.id, "stake_amount": 125, "client_locale": "pt-br"},
        )
        self.assertEqual(prediction_response.status_code, 201)
        before_reputation = UserReputation.objects.get(user__username="@canceluser")

        canceled = client.post("/admin/markets/cancelamento-refund-teste/cancel", headers=staff_headers, json={"note": "Critério impossível de validar."})
        self.assertEqual(canceled.status_code, 200)
        self.assertEqual(canceled.json()["status"], "canceled")

        prediction = Prediction.objects.get(id=prediction_response.json()["prediction_id"])
        self.assertEqual(prediction.status, "canceled")
        self.assertIsNone(prediction.won)
        balance = WalletBalance.objects.get(user__username="@canceluser")
        self.assertEqual(balance.available_gtl, 2000)
        self.assertEqual(balance.locked_gtl, 0)
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="prediction_refund", direction="release", amount=125, reference_id=str(prediction.id)).exists())
        after_reputation = UserReputation.objects.get(user__username="@canceluser")
        self.assertEqual(after_reputation.reputation_score, before_reputation.reputation_score)
        self.assertEqual(after_reputation.resolved_predictions_count, before_reputation.resolved_predictions_count)
        self.assertEqual(after_reputation.accuracy_indicator, before_reputation.accuracy_indicator)
        self.assertFalse(WalletLedgerEntry.objects.filter(entry_type="prediction_payout", reference_id=str(prediction.id)).exists())
        self.assertTrue(AdminEvent.objects.filter(action="market.cancel", entity_identifier="cancelamento-refund-teste").exists())

        duplicate = client.post("/admin/markets/cancelamento-refund-teste/cancel", headers=staff_headers, json={"note": "segunda tentativa"})
        self.assertEqual(duplicate.status_code, 422)
        self.assertEqual(WalletLedgerEntry.objects.filter(entry_type="prediction_refund", reference_id=str(prediction.id)).count(), 1)

    def test_reconcile_canceled_market_refunds_open_prediction_orphans(self):
        client = TestClient(app)
        staff_register = client.post(
            "/auth/register",
            json={
                "display_name": "Reconcile Staff",
                "email": "reconcile-staff@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        user_register = client.post(
            "/auth/register",
            json={
                "display_name": "Reconcile User",
                "email": "reconcile-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(staff_register.status_code, 201)
        self.assertEqual(user_register.status_code, 201)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("reconcile-staff@example.com",))
        staff_headers = {"Authorization": f"Bearer {staff_register.json()['session']['token']}"}
        user_headers = {"Authorization": f"Bearer {user_register.json()['session']['token']}"}
        market_response = client.post(
            "/admin/markets",
            headers=staff_headers,
            json={
                "title": "Mercado cancelado com orfao?",
                "slug": "reconcile-cancelado-orfao",
                "summary": "Mercado isolado para reconciliar refund.",
                "kind": "binary",
                "category": "IA",
                "subcategory": "Modelos",
                "source": "Fonte pública",
                "resolution_criteria": "Critério público verificável.",
                "close_at": "2026-12-31T23:59:00-03:00",
                "close_timezone": "America/Sao_Paulo",
                "thumb_color": "#d8ece2",
                "auto_close_enabled": False,
            },
        )
        self.assertEqual(market_response.status_code, 201)
        publish_response = client.post("/admin/markets/reconcile-cancelado-orfao/publish", headers=staff_headers, json={"note": "publicar"})
        self.assertEqual(publish_response.status_code, 200)
        option = MarketOption.objects.get(market__slug="reconcile-cancelado-orfao", label="SIM")
        prediction_response = client.post(
            "/markets/reconcile-cancelado-orfao/predict",
            headers=user_headers,
            json={"option_id": option.id, "stake_amount": 180, "client_locale": "pt-br"},
        )
        self.assertEqual(prediction_response.status_code, 201)
        prediction = Prediction.objects.get(id=prediction_response.json()["prediction_id"])
        before_reputation = UserReputation.objects.get(user__username="@reconcileuser")

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE gotrendlabs_markets
                    SET status = 'canceled',
                        status_label = 'Cancelado',
                        canceled_at = %s
                    WHERE slug = %s
                    """,
                    (timezone.now(), "reconcile-cancelado-orfao"),
                )
        prediction.refresh_from_db()
        self.assertEqual(prediction.status, "open")

        dry_run_output = StringIO()
        call_command("reconcile_canceled_market_refunds", "--slug", "reconcile-cancelado-orfao", "--dry-run", stdout=dry_run_output)
        self.assertIn("DRY-RUN reconcile-cancelado-orfao: 1 open predictions", dry_run_output.getvalue())
        prediction.refresh_from_db()
        self.assertEqual(prediction.status, "open")
        self.assertFalse(WalletLedgerEntry.objects.filter(entry_type="prediction_refund", reference_id=str(prediction.id)).exists())

        output = StringIO()
        call_command("reconcile_canceled_market_refunds", "--slug", "reconcile-cancelado-orfao", stdout=output)
        self.assertIn("1 predictions canceled", output.getvalue())
        prediction.refresh_from_db()
        self.assertEqual(prediction.status, "canceled")
        self.assertIsNone(prediction.won)
        balance = WalletBalance.objects.get(user__username="@reconcileuser")
        self.assertEqual(balance.available_gtl, 2000)
        self.assertEqual(balance.locked_gtl, 0)
        self.assertEqual(WalletLedgerEntry.objects.filter(entry_type="prediction_refund", direction="release", amount=180, reference_id=str(prediction.id)).count(), 1)
        after_reputation = UserReputation.objects.get(user__username="@reconcileuser")
        self.assertEqual(after_reputation.reputation_score, before_reputation.reputation_score)
        self.assertEqual(after_reputation.resolved_predictions_count, before_reputation.resolved_predictions_count)
        self.assertEqual(after_reputation.accuracy_indicator, before_reputation.accuracy_indicator)
        self.assertTrue(AdminEvent.objects.filter(action="market.cancel_reconcile", entity_identifier="reconcile-cancelado-orfao").exists())

        second_output = StringIO()
        call_command("reconcile_canceled_market_refunds", "--slug", "reconcile-cancelado-orfao", stdout=second_output)
        self.assertIn("No canceled markets with open predictions found.", second_output.getvalue())
        self.assertEqual(WalletLedgerEntry.objects.filter(entry_type="prediction_refund", reference_id=str(prediction.id)).count(), 1)

    def test_admin_market_edit_preserves_collected_resolution_and_graph_data(self):
        client = TestClient(app)
        staff_register = client.post(
            "/auth/register",
            json={
                "display_name": "Preserve Staff",
                "email": "preserve-staff@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        first_register = client.post(
            "/auth/register",
            json={
                "display_name": "Preserve First",
                "email": "preserve-first@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        second_register = client.post(
            "/auth/register",
            json={
                "display_name": "Preserve Second",
                "email": "preserve-second@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(staff_register.status_code, 201)
        self.assertEqual(first_register.status_code, 201)
        self.assertEqual(second_register.status_code, 201)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("preserve-staff@example.com",))

        staff_headers = {"Authorization": f"Bearer {staff_register.json()['session']['token']}"}
        first_headers = {"Authorization": f"Bearer {first_register.json()['session']['token']}"}
        second_headers = {"Authorization": f"Bearer {second_register.json()['session']['token']}"}
        created = client.post(
            "/admin/markets",
            headers=staff_headers,
            json={
                "title": "Mercado preserva dados internos?",
                "slug": "preserva-dados-internos",
                "summary": "Mercado isolado para testar edição segura.",
                "kind": "binary",
                "category": "IA",
                "subcategory": "Modelos",
                "source": "Fonte pública",
                "resolution_criteria": "Critério público verificável.",
                "close_at": "2026-12-31T23:59:00-03:00",
                "close_timezone": "America/Sao_Paulo",
                "thumb_color": "#d8ece2",
                "auto_close_enabled": True,
            },
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(client.post("/admin/markets/preserva-dados-internos/publish", headers=staff_headers, json={"note": "publicar"}).status_code, 200)
        sim = MarketOption.objects.get(market__slug="preserva-dados-internos", label="SIM")
        nao = MarketOption.objects.get(market__slug="preserva-dados-internos", label="NAO")
        self.assertEqual(client.post("/markets/preserva-dados-internos/predict", headers=first_headers, json={"option_id": sim.id, "stake_amount": 75}).status_code, 201)
        self.assertEqual(client.post("/markets/preserva-dados-internos/predict", headers=second_headers, json={"option_id": nao.id, "stake_amount": 25}).status_code, 201)

        before = client.get("/admin/markets/preserva-dados-internos", headers=staff_headers).json()
        before_option_state = [(option["label"], option["probability_exact"], option["sparkline_path"]) for option in before["options"]]
        before_series = [(series["label"], series["path"]) for series in before["sparkline_series"]]
        dangerous_payload = {
            **before,
            "title": "Mercado preserva dados internos? Editado",
            "summary": "Texto editado sem limpar dados coletados.",
            "auto_close_enabled": False,
            "status_label": "Rascunho",
            "primary_outcome": "SIM",
            "primary_probability_exact": 0,
            "secondary_probability_exact": 0,
            "volume_gtl": "0 GT₵",
            "participants": "0 usuários",
            "resolution_type": "",
            "resolution_note": "",
            "options": [
                {**option, "probability_exact": 50, "probability": 50}
                for option in before["options"]
            ],
        }
        edited = client.patch("/admin/markets/preserva-dados-internos", headers=staff_headers, json=dangerous_payload)
        self.assertEqual(edited.status_code, 200)
        edited_payload = edited.json()
        self.assertFalse(edited_payload["auto_close_enabled"])
        self.assertEqual(edited_payload["status_label"], before["status_label"])
        self.assertEqual(edited_payload["volume_gtl"], before["volume_gtl"])
        self.assertEqual(edited_payload["participants"], before["participants"])
        self.assertEqual(edited_payload["primary_probability_exact"], before["primary_probability_exact"])
        self.assertEqual(edited_payload["secondary_probability_exact"], before["secondary_probability_exact"])
        self.assertEqual(
            [(option["label"], option["probability_exact"], option["sparkline_path"]) for option in edited_payload["options"]],
            before_option_state,
        )
        self.assertEqual([(series["label"], series["path"]) for series in edited_payload["sparkline_series"]], before_series)

        lock = client.post("/admin/markets/preserva-dados-internos/lock", headers=staff_headers, json={"note": "fechar manualmente"})
        self.assertEqual(lock.status_code, 200)
        resolved = client.post(
            "/admin/markets/preserva-dados-internos/resolve",
            headers=staff_headers,
            json={"winning_option_id": sim.id, "source_url": "https://fonte.example/resolucao", "note": "Fonte validada."},
        )
        self.assertEqual(resolved.status_code, 200)
        resolved_payload = resolved.json()
        self.assertEqual([(series["label"], series["path"]) for series in resolved_payload["sparkline_series"]], before_series)
        resolved_dangerous_payload = {
            **resolved_payload,
            "title": "Mercado preserva dados internos? Pós-resolução",
            "status_label": "Rascunho",
            "primary_outcome": "NAO",
            "primary_probability_exact": 0,
            "secondary_probability_exact": 0,
            "volume_gtl": "0 GT₵",
            "participants": "0 usuários",
            "resolution_type": "",
            "resolution_note": "",
            "options": [
                {**option, "probability_exact": 50, "probability": 50}
                for option in resolved_payload["options"]
            ],
        }
        edited_resolved = client.patch("/admin/markets/preserva-dados-internos", headers=staff_headers, json=resolved_dangerous_payload)
        self.assertEqual(edited_resolved.status_code, 422)

    def test_comments_create_list_react_and_admin_moderate(self):
        client = TestClient(app)
        user_register = client.post(
            "/auth/register",
            json={
                "display_name": "Comment User",
                "email": "comment-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(user_register.status_code, 201)
        user_headers = {"Authorization": f"Bearer {user_register.json()['session']['token']}"}

        anonymous = client.post("/markets/openai-gpt6-2026/comments", json={"body": "Sem sessão"})
        self.assertEqual(anonymous.status_code, 401)

        response = client.post(
            "/markets/openai-gpt6-2026/comments",
            headers=user_headers,
            json={"body": "Critério bom, mas eu observaria o nome comercial.", "client_locale": "pt-br"},
        )
        self.assertEqual(response.status_code, 201)
        comment_id = response.json()["id"]
        self.assertEqual(response.json()["status"], "visible")
        self.assertTrue(MarketComment.objects.filter(id=comment_id, market__slug="openai-gpt6-2026").exists())

        detail = client.get("/markets/openai-gpt6-2026", headers=user_headers)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["comments"][0]["id"], comment_id)

        listed = client.get("/markets/openai-gpt6-2026/comments", headers=user_headers)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["comments"][0]["body"], "Critério bom, mas eu observaria o nome comercial.")

        like = client.post(f"/comments/{comment_id}/like", headers=user_headers)
        self.assertEqual(like.status_code, 200)
        self.assertEqual(like.json()["like_count"], 1)
        self.assertEqual(like.json()["viewer_reaction"], "like")
        dislike = client.post(f"/comments/{comment_id}/dislike", headers=user_headers)
        self.assertEqual(dislike.status_code, 200)
        self.assertEqual(dislike.json()["like_count"], 0)
        self.assertEqual(dislike.json()["dislike_count"], 1)
        self.assertEqual(CommentReaction.objects.filter(comment_id=comment_id, user__username="@commentuser").count(), 1)
        undislike = client.delete(f"/comments/{comment_id}/dislike", headers=user_headers)
        self.assertEqual(undislike.status_code, 200)
        self.assertEqual(undislike.json()["dislike_count"], 0)

        resolved_comment = client.post(
            "/markets/tiktok-resolvido-2026/comments",
            headers=user_headers,
            json={"body": "Discussão histórica segue útil."},
        )
        self.assertEqual(resolved_comment.status_code, 201)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_markets SET status = 'canceled' WHERE slug = %s", ("tiktok-ban-eua-2026",))
        canceled = client.post(
            "/markets/tiktok-ban-eua-2026/comments",
            headers=user_headers,
            json={"body": "Não deveria entrar."},
        )
        self.assertEqual(canceled.status_code, 422)

        common_admin = client.get("/admin/comments", headers=user_headers)
        self.assertEqual(common_admin.status_code, 403)
        staff_register = client.post(
            "/auth/register",
            json={
                "display_name": "Comment Staff",
                "email": "comment-staff@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(staff_register.status_code, 201)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("comment-staff@example.com",))
        staff_headers = {"Authorization": f"Bearer {staff_register.json()['session']['token']}"}
        admin_comments = client.get("/admin/comments", headers=staff_headers)
        self.assertEqual(admin_comments.status_code, 200)
        self.assertIn(comment_id, [comment["id"] for comment in admin_comments.json()["comments"]])

        hidden = client.patch(
            f"/admin/comments/{comment_id}/moderation",
            headers=staff_headers,
            json={"status": "hidden", "note": "Conteúdo ocultado para teste."},
        )
        self.assertEqual(hidden.status_code, 200)
        self.assertEqual(hidden.json()["status"], "hidden")
        self.assertTrue(AdminEvent.objects.filter(action="comment.hide", entity_identifier=str(comment_id)).exists())
        public_after_hide = client.get("/markets/openai-gpt6-2026/comments")
        self.assertNotIn(comment_id, [comment["id"] for comment in public_after_hide.json()["comments"]])

        restored = client.patch(
            f"/admin/comments/{comment_id}/moderation",
            headers=staff_headers,
            json={"status": "visible", "note": "Restaurar comentário."},
        )
        self.assertEqual(restored.status_code, 200)
        self.assertEqual(restored.json()["status"], "visible")
        self.assertTrue(AdminEvent.objects.filter(action="comment.restore", entity_identifier=str(comment_id)).exists())

    def test_admin_market_api_requires_staff_and_manages_markets_taxonomy(self):
        client = TestClient(app)

        common_register = client.post(
            "/auth/register",
            json={
                "display_name": "Common Admin Case",
                "email": "common-admin@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(common_register.status_code, 201)
        common_headers = {"Authorization": f"Bearer {common_register.json()['session']['token']}"}
        self.assertEqual(client.get("/admin/markets", headers=common_headers).status_code, 403)

        staff_register = client.post(
            "/auth/register",
            json={
                "display_name": "Staff Admin Case",
                "email": "staff-admin@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(staff_register.status_code, 201)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("staff-admin@example.com",))
        headers = {"Authorization": f"Bearer {staff_register.json()['session']['token']}"}
        staff_session = client.get("/auth/session", headers=headers)
        self.assertEqual(staff_session.status_code, 200)
        self.assertTrue(staff_session.json()["user"]["is_staff"])

        taxonomy = client.post(
            "/admin/categories",
            headers=headers,
            json={"name": "Energia", "slug": "energia", "notice": "Aviso geral da categoria Energia."},
        )
        self.assertEqual(taxonomy.status_code, 201)
        subcategory = client.post(
            "/admin/categories/energia/subcategories",
            headers=headers,
            json={"name": "Renováveis", "slug": "renovaveis", "notice": "Aviso da subcategoria Renováveis."},
        )
        self.assertEqual(subcategory.status_code, 201)
        self.assertIn("Energia", [category["name"] for category in subcategory.json()["categories"]])
        energia_payload = next(category for category in subcategory.json()["categories"] if category["slug"] == "energia")
        renovaveis_payload = next(subcategory for subcategory in energia_payload["subcategories"] if subcategory["slug"] == "renovaveis")
        self.assertEqual(energia_payload["notice"], "Aviso geral da categoria Energia.")
        self.assertEqual(renovaveis_payload["notice"], "Aviso da subcategoria Renováveis.")
        event = client.post(
            "/admin/categories/energia/subcategories/renovaveis/events",
            headers=headers,
            json={"name": "Solar", "slug": "solar", "notice": "Não caracteriza recomendação de investimento."},
        )
        self.assertEqual(event.status_code, 201)
        energia_payload = next(category for category in event.json()["categories"] if category["slug"] == "energia")
        renovaveis_payload = next(subcategory for subcategory in energia_payload["subcategories"] if subcategory["slug"] == "renovaveis")
        self.assertIn("Solar", [event["name"] for event in renovaveis_payload["events"]])
        empty_event = client.post(
            "/admin/categories/energia/subcategories/renovaveis/events",
            headers=headers,
            json={"name": "Eólica", "slug": "eolica", "notice": ""},
        )
        self.assertEqual(empty_event.status_code, 201)
        delete_empty_event = client.delete("/admin/categories/energia/subcategories/renovaveis/events/eolica", headers=headers)
        self.assertEqual(delete_empty_event.status_code, 200)
        energia_payload = next(category for category in delete_empty_event.json()["categories"] if category["slug"] == "energia")
        renovaveis_payload = next(subcategory for subcategory in energia_payload["subcategories"] if subcategory["slug"] == "renovaveis")
        self.assertNotIn("eolica", [event["slug"] for event in renovaveis_payload["events"]])

        block_category = client.post("/admin/categories/energia/block", headers=headers, json={"note": "Congelar categoria"})
        self.assertEqual(block_category.status_code, 200)
        energia_payload = next(category for category in block_category.json()["categories"] if category["slug"] == "energia")
        self.assertTrue(energia_payload["is_blocked"])
        self.assertEqual(energia_payload["blocked_reason"], "Congelar categoria")
        blocked_category_market = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Mercado com categoria bloqueada",
                "slug": "mercado-categoria-bloqueada",
                "summary": "Nao deve salvar.",
                "kind": "binary",
                "category": "Energia",
                "subcategory": "Renováveis",
                "source": "Fonte",
                "resolution_criteria": "Critério",
                "close_at": "2026-12-31T23:59:00-03:00",
                "close_timezone": "America/Sao_Paulo",
                "thumb_color": "#d8ece2",
            },
        )
        self.assertEqual(blocked_category_market.status_code, 422)
        unblock_category = client.post("/admin/categories/energia/unblock", headers=headers, json={"note": "Reativar categoria"})
        self.assertEqual(unblock_category.status_code, 200)

        block_subcategory = client.post("/admin/categories/energia/subcategories/renovaveis/block", headers=headers, json={"note": "Congelar subcategoria"})
        self.assertEqual(block_subcategory.status_code, 200)
        energia_payload = next(category for category in block_subcategory.json()["categories"] if category["slug"] == "energia")
        renovaveis_payload = next(subcategory for subcategory in energia_payload["subcategories"] if subcategory["slug"] == "renovaveis")
        self.assertTrue(renovaveis_payload["is_blocked"])
        blocked_subcategory_market = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Mercado com subcategoria bloqueada",
                "slug": "mercado-subcategoria-bloqueada",
                "summary": "Nao deve salvar.",
                "kind": "binary",
                "category": "Energia",
                "subcategory": "Renováveis",
                "source": "Fonte",
                "resolution_criteria": "Critério",
                "close_at": "2026-12-31T23:59:00-03:00",
                "close_timezone": "America/Sao_Paulo",
                "thumb_color": "#d8ece2",
            },
        )
        self.assertEqual(blocked_subcategory_market.status_code, 422)
        unblock_subcategory = client.post("/admin/categories/energia/subcategories/renovaveis/unblock", headers=headers, json={"note": "Reativar subcategoria"})
        self.assertEqual(unblock_subcategory.status_code, 200)

        block_event = client.post("/admin/categories/energia/subcategories/renovaveis/events/solar/block", headers=headers, json={"note": "Congelar evento"})
        self.assertEqual(block_event.status_code, 200)
        energia_payload = next(category for category in block_event.json()["categories"] if category["slug"] == "energia")
        renovaveis_payload = next(subcategory for subcategory in energia_payload["subcategories"] if subcategory["slug"] == "renovaveis")
        solar_payload = next(event for event in renovaveis_payload["events"] if event["slug"] == "solar")
        self.assertEqual(solar_payload["notice"], "Não caracteriza recomendação de investimento.")
        update_event_notice = client.patch(
            "/admin/categories/energia/subcategories/renovaveis/events/solar",
            headers=headers,
            json={"name": "Solar", "slug": "solar", "notice": "Aviso operacional atualizado."},
        )
        self.assertEqual(update_event_notice.status_code, 200)
        energia_payload = next(category for category in update_event_notice.json()["categories"] if category["slug"] == "energia")
        renovaveis_payload = next(subcategory for subcategory in energia_payload["subcategories"] if subcategory["slug"] == "renovaveis")
        solar_payload = next(event for event in renovaveis_payload["events"] if event["slug"] == "solar")
        self.assertEqual(solar_payload["notice"], "Aviso operacional atualizado.")
        self.assertTrue(solar_payload["is_blocked"])
        blocked_event_market = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Mercado com evento bloqueado",
                "slug": "mercado-evento-bloqueado",
                "summary": "Nao deve salvar.",
                "kind": "binary",
                "category": "Energia",
                "subcategory": "Renováveis",
                "event": "Solar",
                "source": "Fonte",
                "resolution_criteria": "Critério",
                "close_at": "2026-12-31T23:59:00-03:00",
                "close_timezone": "America/Sao_Paulo",
                "thumb_color": "#d8ece2",
            },
        )
        self.assertEqual(blocked_event_market.status_code, 422)
        unblock_event = client.post("/admin/categories/energia/subcategories/renovaveis/events/solar/unblock", headers=headers, json={"note": "Reativar evento"})
        self.assertEqual(unblock_event.status_code, 200)

        required_market_fields = {
            "source": "Fonte",
            "resolution_criteria": "Critério",
            "close_at": "2026-12-31T23:59:00-03:00",
            "close_timezone": "America/Sao_Paulo",
            "thumb_color": "#d8ece2",
        }
        invalid_market = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Mercado rascunho incompleto?",
                "slug": "mercado-rascunho-incompleto",
                "kind": "binary",
                "category": "Energia",
                "subcategory": "Renováveis",
                "options": [{"label": "SIM", "probability": 60}, {"label": "NAO", "probability": 40}],
            },
        )
        self.assertEqual(invalid_market.status_code, 422)
        self.assertFalse(Market.objects.filter(slug="mercado-rascunho-incompleto").exists())

        valid_market = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Energia solar será maioria em 2030?",
                "slug": "energia-solar-maioria-2030",
                "summary": "Mercado administrativo real para energia solar.",
                "kind": "binary",
                "category": "Energia",
                "subcategory": "Renováveis",
                "event": "Solar",
                "source": "Agência Internacional de Energia",
                "resolution_criteria": "Será resolvido com relatório público consolidado.",
                "close_at": "2026-12-31T23:59:00-03:00",
                "close_timezone": "America/Sao_Paulo",
                "image_url": "/media/market_thumbnails/teste.png",
                "thumb": "EN",
                "thumb_color": "#d8ece2",
                "options": [{"label": "SIM", "probability": 55}, {"label": "NAO", "probability": 45}],
            },
        )
        self.assertEqual(valid_market.status_code, 201)
        self.assertEqual(valid_market.json()["status"], "draft")
        self.assertEqual(valid_market.json()["event"], "Solar")
        self.assertEqual([option["label"] for option in valid_market.json()["options"]], ["SIM", "NAO"])
        self.assertEqual([option["probability"] for option in valid_market.json()["options"]], [50, 50])
        self.assertEqual(valid_market.json()["close_timezone"], "America/Sao_Paulo")
        self.assertTrue(valid_market.json()["auto_close_enabled"])
        self.assertEqual(valid_market.json()["image_url"], "/media/market_thumbnails/teste.png")
        self.assertTrue(valid_market.json()["closes_in"].endswith("d") or valid_market.json()["closes_in"].endswith("h") or valid_market.json()["closes_in"] == "fim")
        filtered_markets = client.get("/admin/markets?q=solar", headers=headers)
        self.assertEqual(filtered_markets.status_code, 200)
        self.assertIn("energia-solar-maioria-2030", [market["slug"] for market in filtered_markets.json()["markets"]])
        filtered_empty = client.get("/admin/markets?q=nao-existe-mercado", headers=headers)
        self.assertEqual(filtered_empty.status_code, 200)
        self.assertEqual(filtered_empty.json()["markets"], [])
        delete_linked_event = client.delete("/admin/categories/energia/subcategories/renovaveis/events/solar", headers=headers)
        self.assertEqual(delete_linked_event.status_code, 422)

        featured_market = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Mercado em destaque inicial",
                "slug": "mercado-em-destaque-inicial",
                "summary": "Primeiro destaque configurado pelo Admin Ops.",
                "kind": "binary",
                "category": "Energia",
                "subcategory": "Renováveis",
                **required_market_fields,
                "is_featured": True,
            },
        )
        self.assertEqual(featured_market.status_code, 201)
        self.assertTrue(featured_market.json()["is_featured"])
        make_featured = client.patch(
            "/admin/markets/energia-solar-maioria-2030",
            headers=headers,
            json={**valid_market.json(), "is_featured": True},
        )
        self.assertEqual(make_featured.status_code, 200)
        self.assertTrue(make_featured.json()["is_featured"])
        self.assertTrue(Market.objects.get(slug="energia-solar-maioria-2030").is_featured)
        self.assertTrue(Market.objects.get(slug="mercado-em-destaque-inicial").is_featured)
        third_featured = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Terceiro destaque substitui o mais antigo",
                "slug": "terceiro-destaque-substitui-antigo",
                "summary": "Terceiro destaque configurado pelo Admin Ops.",
                "kind": "binary",
                "category": "Energia",
                "subcategory": "Renováveis",
                **required_market_fields,
                "is_featured": True,
            },
        )
        self.assertEqual(third_featured.status_code, 201)
        self.assertEqual(Market.objects.filter(is_featured=True).count(), 2)
        self.assertTrue(Market.objects.get(slug="terceiro-destaque-substitui-antigo").is_featured)
        self.assertFalse(Market.objects.get(slug="mercado-em-destaque-inicial").is_featured)

        publish = client.post("/admin/markets/energia-solar-maioria-2030/publish", headers=headers, json={"note": "publicar"})
        self.assertEqual(publish.status_code, 200)
        self.assertEqual(publish.json()["status"], "open")

        predictor_register = client.post(
            "/auth/register",
            json={
                "display_name": "Admin Edit Predictor",
                "email": "admin-edit-predictor@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(predictor_register.status_code, 201)
        predictor_headers = {"Authorization": f"Bearer {predictor_register.json()['session']['token']}"}
        predicted_option = MarketOption.objects.get(market__slug="energia-solar-maioria-2030", label="SIM")
        prediction = client.post(
            "/markets/energia-solar-maioria-2030/predict",
            headers=predictor_headers,
            json={"option_id": predicted_option.id, "stake_amount": 20, "client_locale": "pt-br"},
        )
        self.assertEqual(prediction.status_code, 201)
        participants_response = client.get("/admin/markets/energia-solar-maioria-2030/participants", headers=headers)
        self.assertEqual(participants_response.status_code, 200)
        self.assertEqual(participants_response.json()["summary"]["human_participants"], 1)
        self.assertEqual(participants_response.json()["summary"]["bot_participants"], 0)
        self.assertEqual(participants_response.json()["participants"][0]["handle"], "@admineditpredictor")
        self.assertEqual(participants_response.json()["participants"][0]["stake_amount"], 20)
        predicted_option.refresh_from_db()
        probability_after_prediction = predicted_option.probability_exact
        edited_market_payload = {
            **valid_market.json(),
            "title": "Energia solar será maioria em 2030? Revisado",
            "summary": "Mercado administrativo real para energia solar revisado.",
            "auto_close_enabled": False,
        }
        edit_after_prediction = client.patch(
            "/admin/markets/energia-solar-maioria-2030",
            headers=headers,
            json=edited_market_payload,
        )
        self.assertEqual(edit_after_prediction.status_code, 200)
        self.assertEqual(edit_after_prediction.json()["title"], "Energia solar será maioria em 2030? Revisado")
        self.assertFalse(edit_after_prediction.json()["auto_close_enabled"])
        self.assertEqual(edit_after_prediction.json()["status_label"], "Aberto")
        self.assertEqual(edit_after_prediction.json()["volume_gtl"], "20 GT₵")
        self.assertEqual(edit_after_prediction.json()["participants"], "1 participante")
        self.assertEqual(
            Decimal(str(next(option for option in edit_after_prediction.json()["options"] if option["label"] == "SIM")["probability_exact"])),
            probability_after_prediction,
        )

        republish_open = client.post("/admin/markets/energia-solar-maioria-2030/publish", headers=headers, json={"note": "publicar de novo"})
        self.assertEqual(republish_open.status_code, 200)
        self.assertEqual(republish_open.json()["status"], "open")
        self.assertEqual(republish_open.json()["volume_gtl"], "20 GT₵")
        self.assertEqual(
            Decimal(str(next(option for option in republish_open.json()["options"] if option["label"] == "SIM")["probability_exact"])),
            probability_after_prediction,
        )

        auto_close_lock = client.post("/admin/markets/energia-solar-maioria-2030/lock", headers=headers, json={"note": "fechar"})
        self.assertEqual(auto_close_lock.status_code, 200)

        one_option = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Mercado multipla invalido",
                "slug": "mercado-multipla-invalido",
                "summary": "Invalido por ter uma opção.",
                "kind": "multiple",
                "category": "Energia",
                "subcategory": "Renováveis",
                **required_market_fields,
                "options": [{"label": "A"}],
            },
        )
        self.assertEqual(one_option.status_code, 422)

        duplicate_options = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Mercado multipla duplicado",
                "slug": "mercado-multipla-duplicado",
                "summary": "Invalido por duplicidade.",
                "kind": "multiple",
                "category": "Energia",
                "subcategory": "Renováveis",
                **required_market_fields,
                "options": [{"label": "A"}, {"label": "a"}],
            },
        )
        self.assertEqual(duplicate_options.status_code, 422)

        multiple_market = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Qual tecnologia lidera energia limpa?",
                "slug": "tecnologia-lidera-energia-limpa",
                "summary": "Mercado multipla escolha com distribuição automática.",
                "kind": "multiple",
                "category": "Energia",
                "subcategory": "Renováveis",
                **required_market_fields,
                "options": [{"label": "Solar"}, {"label": "Eólica"}, {"label": "Hidrogênio"}],
            },
        )
        self.assertEqual(multiple_market.status_code, 201)
        self.assertEqual([option["probability"] for option in multiple_market.json()["options"]], [33, 33, 33])
        self.assertEqual(
            [Decimal(str(option["probability_exact"])) for option in multiple_market.json()["options"]],
            [Decimal("33.3333"), Decimal("33.3333"), Decimal("33.3333")],
        )

        many_options = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Qual fonte cresce mais?",
                "slug": "qual-fonte-cresce-mais",
                "summary": "Mercado com várias opções.",
                "kind": "multiple",
                "category": "Energia",
                "subcategory": "Renováveis",
                **required_market_fields,
                "options": [{"label": f"Opção {index}"} for index in range(1, 7)],
            },
        )
        self.assertEqual(many_options.status_code, 201)
        self.assertEqual(len(many_options.json()["options"]), 6)
        self.assertEqual([option["probability"] for option in many_options.json()["options"]], [16, 16, 16, 16, 16, 16])
        self.assertEqual(
            [Decimal(str(option["probability_exact"])) for option in many_options.json()["options"]],
            [Decimal("16.6667")] * 6,
        )

        manual_market = client.post(
            "/admin/markets",
            headers=headers,
            json={
                "title": "Fechamento manual será usado?",
                "slug": "fechamento-manual-sera-usado",
                "summary": "Mercado com fechamento manual.",
                "kind": "binary",
                "category": "Energia",
                "subcategory": "Renováveis",
                **required_market_fields,
                "auto_close_enabled": False,
            },
        )
        self.assertEqual(manual_market.status_code, 201)
        manual_publish = client.post("/admin/markets/fechamento-manual-sera-usado/publish", headers=headers, json={"note": "publicar"})
        self.assertEqual(manual_publish.status_code, 200)
        manual_lock = client.post("/admin/markets/fechamento-manual-sera-usado/lock", headers=headers, json={"note": "fechar manualmente"})
        self.assertEqual(manual_lock.status_code, 200)
        self.assertEqual(manual_lock.json()["status"], "locked")
        self.assertTrue(AdminEvent.objects.filter(action="market.lock", entity_identifier="fechamento-manual-sera-usado").exists())

        draft_listing = client.get("/admin/markets", headers=headers, params={"status": "draft"})
        self.assertEqual(draft_listing.status_code, 200)
        self.assertTrue(all(market["status"] == "draft" for market in draft_listing.json()["markets"]))
        self.assertGreaterEqual(draft_listing.json()["counts"]["open"], 1)

        public_detail = client.get("/markets/energia-solar-maioria-2030")
        self.assertEqual(public_detail.status_code, 200)
        self.assertEqual(public_detail.json()["subcategory"], "Renováveis")
        self.assertEqual(public_detail.json()["event"], "Solar")
        self.assertEqual(public_detail.json()["category_notice"], "Aviso geral da categoria Energia.")
        self.assertEqual(public_detail.json()["subcategory_notice"], "Aviso da subcategoria Renováveis.")
        self.assertEqual(public_detail.json()["event_notice"], "Aviso operacional atualizado.")

        cancel = client.post("/admin/markets/energia-solar-maioria-2030/cancel", headers=headers, json={"note": "cancelar"})
        self.assertEqual(cancel.status_code, 200)
        self.assertEqual(cancel.json()["status"], "canceled")
        self.assertFalse(cancel.json()["is_featured"])
        canceled_feature_attempt = client.patch(
            "/admin/markets/energia-solar-maioria-2030",
            headers=headers,
            json={**valid_market.json(), "is_featured": True},
        )
        self.assertEqual(canceled_feature_attempt.status_code, 422)
        self.assertTrue(AdminEvent.objects.filter(action="market.cancel", entity_identifier="energia-solar-maioria-2030").exists())

    def test_operational_queues_submit_review_convert_and_reward(self):
        client = TestClient(app)

        user_register = client.post(
            "/auth/register",
            json={
                "display_name": "Queue User",
                "email": "queue-user@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(user_register.status_code, 201)
        user_headers = {"Authorization": f"Bearer {user_register.json()['session']['token']}"}

        suggestion = client.post(
            "/suggestions",
            headers=user_headers,
            json={
                "question": "A Apple lançará app IA próprio em 2026?",
                "category": "IA",
                "kind": "binary",
                "suggested_source": "Apple Newsroom",
                "rationale": "Fonte pública e interesse alto.",
            },
        )
        self.assertEqual(suggestion.status_code, 201)
        self.assertEqual(suggestion.json()["status"], "pending")
        self.assertTrue(MarketSuggestion.objects.filter(question__icontains="Apple").exists())

        feedback = client.post(
            "/feedback",
            headers=user_headers,
            json={
                "feedback_type": "Mercado ambíguo",
                "severity": "high",
                "description": "Critério deveria citar fonte primária.",
            },
        )
        self.assertEqual(feedback.status_code, 201)
        self.assertEqual(feedback.json()["kind"], "feedback")
        self.assertTrue(ProductFeedback.objects.filter(severity="high").exists())

        blocked_recharge = client.post("/users/me/wallet/recharge-requests", headers=user_headers)
        self.assertEqual(blocked_recharge.status_code, 422)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO gotrendlabs_site_config (
                        singleton_key,
                        wallet_recharge_min_balance_gtl,
                        daemon_stale_after_minutes,
                        daemon_missing_after_minutes,
                        system_log_retention_days,
                        ai_audit_retention_days,
                        email_enabled,
                        smtp_host,
                        smtp_port,
                        smtp_username,
                        smtp_use_tls,
                        smtp_use_ssl,
                        smtp_timeout_seconds,
                        default_from_email,
                        default_reply_to_email,
                        ai_agents_enabled,
                        ai_commenting_enabled,
                        ai_predictions_enabled,
                        ai_llm_provider,
                        ai_llm_base_url,
                        ai_model,
                        ai_high_reasoning_model,
                        ai_market_cooldown_hours,
                        ai_max_comments_per_market_per_day,
                        ai_max_comments_per_cycle,
                        ai_max_comment_attempts_per_cycle,
                        ai_comment_candidate_limit,
                        ai_max_comments_per_day,
                        ai_comment_max_chars,
                        ai_min_humans_for_prediction,
                        ai_max_stake_gtl,
                        ai_max_predictions_per_cycle,
                        ai_max_predictions_per_day,
                        ai_skip_if_human_comments_recent,
                        ai_recent_human_comment_window_hours,
                        ai_openai_timeout_seconds,
                        ai_openai_max_retries,
                        ai_pause_reason,
                        updated_at
                    )
                    VALUES (
                        1, 10000, 5, 15, 90, 90, false, '', 587, '', true, false, 10, '', '',
                        false, false, false, 'openai', 'https://api.openai.com/v1', 'gpt-5.4-mini', 'gpt-5.5', 24, 1,
                        1, 3, 200, 20, 700, 1, 25, 1, 10, true, 6, 20, 1, '', NOW()
                    )
                    ON CONFLICT (singleton_key)
                    DO UPDATE SET
                        wallet_recharge_min_balance_gtl = EXCLUDED.wallet_recharge_min_balance_gtl,
                        system_log_retention_days = EXCLUDED.system_log_retention_days,
                        ai_audit_retention_days = EXCLUDED.ai_audit_retention_days,
                        updated_at = NOW()
                    """
                )

        recharge = client.post("/users/me/wallet/recharge-requests", headers=user_headers)
        self.assertEqual(recharge.status_code, 201)
        self.assertEqual(recharge.json()["status"], "pending")
        recharge_id = recharge.json()["id"]
        self.assertTrue(WalletRechargeRequest.objects.filter(id=recharge_id, status="pending").exists())
        duplicate_recharge = client.post("/users/me/wallet/recharge-requests", headers=user_headers)
        self.assertEqual(duplicate_recharge.status_code, 409)
        my_recharges = client.get("/users/me/wallet/recharge-requests", headers=user_headers)
        self.assertEqual(my_recharges.status_code, 200)
        self.assertEqual(my_recharges.json()["requests"][0]["id"], recharge_id)

        common_queue = client.get("/admin/queues", headers=user_headers)
        self.assertEqual(common_queue.status_code, 403)

        staff_register = client.post(
            "/auth/register",
            json={
                "display_name": "Queue Staff",
                "email": "queue-staff@example.com",
                "language": "pt-br",
                "password": "testpass123",
                "terms_accepted": True,
            },
        )
        self.assertEqual(staff_register.status_code, 201)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff = true WHERE email = %s", ("queue-staff@example.com",))
        staff_headers = {"Authorization": f"Bearer {staff_register.json()['session']['token']}"}

        queue = client.get("/admin/queues", headers=staff_headers)
        self.assertEqual(queue.status_code, 200)
        self.assertIn("suggestion", [item["kind"] for item in queue.json()["items"]])
        self.assertIn("feedback", [item["kind"] for item in queue.json()["items"]])
        self.assertIn("wallet_recharge", [item["kind"] for item in queue.json()["items"]])
        recharge_queue = client.get("/admin/queues", headers=staff_headers, params={"kind": "wallet_recharge"})
        self.assertEqual(recharge_queue.status_code, 200)
        self.assertEqual(recharge_queue.json()["items"][0]["id"], recharge_id)

        approved_recharge = client.post(
            f"/admin/queues/wallet-recharges/{recharge_id}/approve",
            headers=staff_headers,
            json={"amount_gtl": 250, "note": "Recarga educativa controlada."},
        )
        self.assertEqual(approved_recharge.status_code, 200)
        self.assertEqual(approved_recharge.json()["status"], "approved")
        self.assertEqual(approved_recharge.json()["reward_gtl"], 250)
        self.assertTrue(
            WalletLedgerEntry.objects.filter(
                entry_type="educational_recharge",
                direction="credit",
                amount=250,
                reference_type="wallet_recharge_request",
                reference_id=str(recharge_id),
            ).exists()
        )
        self.assertTrue(AdminEvent.objects.filter(action="wallet_recharge.approve", entity_identifier=str(recharge_id)).exists())
        duplicate_recharge_approval = client.post(
            f"/admin/queues/wallet-recharges/{recharge_id}/approve",
            headers=staff_headers,
            json={"amount_gtl": 100, "note": "Duplicado."},
        )
        self.assertEqual(duplicate_recharge_approval.status_code, 422)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE gotrendlabs_site_config
                    SET wallet_recharge_min_balance_gtl = 10000, updated_at = NOW()
                    WHERE singleton_key = 1
                    """
                )
        second_recharge = client.post("/users/me/wallet/recharge-requests", headers=user_headers)
        self.assertEqual(second_recharge.status_code, 201)
        rejected_recharge = client.post(
            f"/admin/queues/wallet-recharges/{second_recharge.json()['id']}/reject",
            headers=staff_headers,
            json={"note": "Saldo ainda suficiente para participar."},
        )
        self.assertEqual(rejected_recharge.status_code, 200)
        self.assertEqual(rejected_recharge.json()["status"], "rejected")
        self.assertFalse(WalletLedgerEntry.objects.filter(reference_type="wallet_recharge_request", reference_id=str(second_recharge.json()["id"])).exists())
        self.assertTrue(AdminEvent.objects.filter(action="wallet_recharge.reject", entity_identifier=str(second_recharge.json()["id"])).exists())

        suggestion_id = suggestion.json()["id"]
        converted = client.post(
            f"/admin/queues/suggestions/{suggestion_id}/convert-draft",
            headers=staff_headers,
            json={"note": "Converter para curadoria."},
        )
        self.assertEqual(converted.status_code, 200)
        self.assertEqual(converted.json()["status"], "converted")
        self.assertIsNotNone(converted.json()["converted_market_slug"])
        self.assertTrue(Market.objects.filter(slug=converted.json()["converted_market_slug"], status="draft").exists())
        self.assertTrue(AdminEvent.objects.filter(action="suggestion.convert_draft", entity_identifier=str(suggestion_id)).exists())

        feedback_id = feedback.json()["id"]
        rewarded = client.post(
            f"/admin/queues/feedback/{feedback_id}/reward",
            headers=staff_headers,
            json={"amount_gtl": 75, "note": "Feedback útil."},
        )
        self.assertEqual(rewarded.status_code, 200)
        self.assertEqual(rewarded.json()["status"], "rewarded")
        self.assertEqual(rewarded.json()["reward_gtl"], 75)
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="reward_feedback", amount=75, reference_id=str(feedback_id)).exists())
        self.assertTrue(UserBadgeAward.objects.filter(user__username="@queueuser", badge__code="feedback_ally").exists())
        self.assertTrue(AdminEvent.objects.filter(action="feedback.reward", entity_identifier=str(feedback_id)).exists())
        duplicate_reward = client.post(
            f"/admin/queues/feedback/{feedback_id}/reward",
            headers=staff_headers,
            json={"amount_gtl": 25, "note": "Duplicado."},
        )
        self.assertEqual(duplicate_reward.status_code, 422)

        suggestion_reward = client.post(
            f"/admin/queues/suggestions/{suggestion_id}/reward",
            headers=staff_headers,
            json={"amount_gtl": 30, "note": "Sugestão útil."},
        )
        self.assertEqual(suggestion_reward.status_code, 200)
        self.assertEqual(suggestion_reward.json()["status"], "rewarded")
        self.assertTrue(WalletLedgerEntry.objects.filter(entry_type="reward_suggestion", amount=30, reference_id=str(suggestion_id)).exists())
        self.assertTrue(UserBadgeAward.objects.filter(user__username="@queueuser", badge__code="market_scout").exists())
        duplicate_suggestion_reward = client.post(
            f"/admin/queues/suggestions/{suggestion_id}/reward",
            headers=staff_headers,
            json={"amount_gtl": 15, "note": "Duplicado."},
        )
        self.assertEqual(duplicate_suggestion_reward.status_code, 422)
        balance = WalletBalance.objects.get(user__username="@queueuser")
        self.assertEqual(balance.available_gtl, 2355)
        self.assertEqual(balance.total_earned_gtl, 105)

        anonymous_feedback = client.post(
            "/feedback",
            json={"guest_name": "Visitante", "guest_email": "visitante@example.com", "feedback_type": "Ideia de melhoria", "severity": "low", "description": "Melhorar filtros."},
        )
        self.assertEqual(anonymous_feedback.status_code, 201)
        blocked_reward = client.post(
            f"/admin/queues/feedback/{anonymous_feedback.json()['id']}/reward",
            headers=staff_headers,
            json={"amount_gtl": 10, "note": "Sem usuário."},
        )
        self.assertEqual(blocked_reward.status_code, 422)


class WebSmokeTests(TransactionTestCase):
    def setUp(self):
        _seed_test_badges()
        _seed_test_markets()

    def test_user_model_uses_gotrendlabs_postgres_table(self):
        User = get_user_model()

        self.assertEqual(User._meta.label, "accounts.User")
        self.assertEqual(User._meta.db_table, "gotrendlabs_users")

    def test_main_pages_render(self):
        category_notice = "Aviso amplo da categoria."
        subcategory_notice = "Aviso específico da subcategoria."
        event_notice = "Este mercado não caracteriza recomendação de investimento."
        market = Market.objects.select_related("category", "subcategory", "event").get(slug="openai-gpt6-2026")
        market.category.notice = category_notice
        market.category.save(update_fields=["notice"])
        market.subcategory.notice = subcategory_notice
        market.subcategory.save(update_fields=["notice"])
        event = market.event
        event.notice = event_notice
        event.save(update_fields=["notice"])
        public_routes = [
            reverse("home"),
            reverse("market-detail", args=["openai-gpt6-2026"]),
            reverse("login"),
            reverse("register"),
            reverse("rankings"),
            reverse("concepts"),
            reverse("categories"),
            reverse("security"),
            reverse("use-policy"),
            reverse("feedback"),
            reverse("share-market", args=["openai-gpt6-2026"]),
            reverse("share-result", args=["tiktok-resolvido-2026"]),
        ]

        for route in public_routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                if route == reverse("feedback"):
                    self.assertContains(response, "Ajude a deixar a GoTrendLabs mais clara.")
                if route == reverse("home"):
                    self.assertNotContains(response, category_notice)
                if route == reverse("concepts"):
                    self.assertContains(response, "IA oficial aparece identificada e separada da comunidade")
                    self.assertContains(response, "Analyst")
                    self.assertContains(response, "Liquidity")
                if route == reverse("use-policy"):
                    self.assertContains(response, "Agentes oficiais devem ser identificados e auditáveis")
                    self.assertContains(response, "não podem fingir ser humanos")
                    self.assertContains(response, "contas oficiais automatizadas")
                    self.assertContains(response, "Segredos de integração")
                    self.assertNotContains(response, subcategory_notice)
                    self.assertNotContains(response, event_notice)
                if route == reverse("market-detail", args=["openai-gpt6-2026"]):
                    self.assertContains(response, "Sua previsão")
                    self.assertContains(response, "detail-title-block")
                    self.assertContains(response, "detail-title-row")
                    self.assertContains(response, "detail-market-thumb")
                    self.assertContains(response, "Avisos do mercado")
                    self.assertContains(response, category_notice)
                    self.assertContains(response, subcategory_notice)
                    self.assertContains(response, event_notice)
                    content = response.content.decode()
                    self.assertLess(content.index("Critério de resolução"), content.index("Avisos do mercado"))
                    self.assertContains(response, "detail-market-actions")
                    self.assertContains(response, "detail-comment-count")
                    self.assertContains(response, "detail-like-button readonly")
                    self.assertContains(response, "detail-favorite-button readonly")
                    self.assertContains(response, "data-guest-favorite-button")
                    self.assertNotContains(response, '<form class="market-like-form"')
                    self.assertNotContains(response, '<form class="market-favorite-form"')

    def test_prediction_ticket_starts_without_selected_option_for_authenticated_user(self):
        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": 31,
            "handle": "@ticketuser",
            "email": "ticket-user@example.com",
            "display_name": "Ticket User",
            "preferred_language": "pt-br",
        }
        session.save()

        response = self.client.get(reverse("market-detail", args=["openai-gpt6-2026"]))
        content = response.content.decode()
        self.assertIn('data-selected-option-id type="radio" name="option_id"', content)
        self.assertIn("required", content)
        self.assertIn("data-requires-choice", content)
        self.assertIn("Primeiro passo", content)
        self.assertIn("Selecione uma opção para registrar sua previsão.", content)
        ticket = content.split('data-prediction-preview-url="', 1)[1].split("</form>", 1)[0]
        self.assertNotIn("choice active", ticket)
        self.assertNotIn("checked", ticket)
        self.assertNotIn("disabled data-requires-choice", ticket)

    def test_prediction_ticket_shows_no_balance_state(self):
        User = get_user_model()
        user = User.objects.create_user(username="emptywallet", email="empty-wallet@example.com", password="testpass123", first_name="Empty Wallet")
        WalletBalance.objects.update_or_create(user=user, defaults={"available_gtl": 0, "locked_gtl": 0, "total_earned_gtl": 0})
        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": user.id,
            "handle": user.username,
            "email": user.email,
            "display_name": user.first_name,
            "preferred_language": "pt-br",
        }
        session.save()

        response = self.client.get(reverse("market-detail", args=["openai-gpt6-2026"]))

        self.assertContains(response, "Saldo indisponível")
        self.assertContains(response, "Você não tem GT₵ disponível para entrar neste mercado.")
        self.assertContains(response, "Sem saldo disponível, esta área fica somente para leitura.")
        self.assertNotContains(response, 'data-prediction-preview-url="')

    def test_django_system_log_uses_gotrendlabs_session_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="@loggedweb", email="logged-web@example.com", password="testpass123", first_name="Logged Web")
        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": user.id,
            "handle": user.username,
            "email": user.email,
            "display_name": user.first_name,
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()

        with patch("system_logs.middleware.log_system_event") as log_mock:
            response = self.client.get(reverse("rankings"), HTTP_X_REQUEST_ID="django-session-user-log")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(log_mock.called)
        self.assertEqual(log_mock.call_args.kwargs["request_id"], "django-session-user-log")
        self.assertEqual(log_mock.call_args.kwargs["source"], "django")
        self.assertEqual(log_mock.call_args.kwargs["user_id"], user.id)

    def test_register_links_to_use_policy(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("use-policy"))
        self.assertContains(response, 'data-open-modal="#use-policy-modal"')
        self.assertContains(response, 'id="use-policy-modal"')
        self.assertContains(response, 'target="_blank"')
        self.assertContains(response, "Mais visitado")
        self.assertContains(response, "visualizações")
        self.assertContains(response, "Mini gráfico de evolução do consenso")
        self.assertContains(response, "Primeira previsão")
        self.assertContains(response, "GTL Credits não representam dinheiro real")

    def test_register_ticket_uses_most_viewed_market(self):
        api_market = get_domain_client().market("openai-gpt6-2026")
        lower = {**api_market, "slug": "lower-signup", "title": "Mercado menos visitado", "view_count": 2}
        viewed = {**api_market, "slug": "viewed-signup", "title": "Mercado preferido no cadastro", "view_count": 15}
        draft = {**api_market, "slug": "draft-signup", "title": "Rascunho mais visitado", "status": "draft", "status_label": "Rascunho", "view_count": 120}
        canceled = {**api_market, "slug": "canceled-signup", "title": "Mercado cancelado mais visitado", "status": "canceled", "status_label": "Cancelado", "view_count": 99}

        with patch("accounts.views.get_markets", return_value=[lower, draft, canceled, viewed]), patch("accounts.views.local_markets", return_value=[]):
            response = self.client.get(reverse("register"))

        self.assertContains(response, "Mercado preferido no cadastro")
        self.assertContains(response, "15 visualizações")
        self.assertNotContains(response, "Mercado menos visitado")
        self.assertNotContains(response, "Rascunho mais visitado")
        self.assertNotContains(response, "Mercado cancelado mais visitado")

    def test_register_ticket_uses_newest_market_when_no_views(self):
        api_market = get_domain_client().market("openai-gpt6-2026")
        older = {**api_market, "slug": "older-signup", "title": "Mercado antigo sem visualizações", "view_count": 0, "created_at": "2026-05-17T12:00:00+00:00"}
        newer = {**api_market, "slug": "newer-signup", "title": "Mercado novo sem visualizações", "view_count": 0, "created_at": "2026-05-19T12:00:00+00:00"}

        with patch("accounts.views.get_markets", return_value=[older, newer]), patch("accounts.views.local_markets", return_value=[]):
            response = self.client.get(reverse("register"))

        self.assertContains(response, "Mercado novo sem visualizações")
        self.assertNotContains(response, "Mercado antigo sem visualizações")

    def test_auth_pages_show_public_navigation(self):
        for route, cta in ((reverse("login"), "Criar conta"), (reverse("register"), "Entrar")):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="topbar"')
                self.assertContains(response, "Mercados")
                self.assertContains(response, "Badges")
                self.assertContains(response, "Ranking")
                self.assertContains(response, "← Feed")
                self.assertContains(response, 'class="footer"')
                self.assertContains(response, "Rede social para prever eventos")
                self.assertContains(response, "GT₵ educativa")
                self.assertContains(response, cta)
                if route == reverse("login"):
                    self.assertContains(response, "Lembrar meu acesso neste dispositivo")

    def test_ranking_guest_card_uses_real_session_state(self):
        response = self.client.get(reverse("rankings"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entre para acompanhar sua posição real")
        self.assertNotContains(response, "top 12%")

    def test_prediction_confirm_redirects_guests_and_renders_api_feedback(self):
        route = reverse("prediction-confirm", args=["openai-gpt6-2026"])
        guest = self.client.post(route, {"option_id": 1, "stake_amount": 80})
        self.assertEqual(guest.status_code, 302)
        self.assertIn(reverse("login"), guest["Location"])

        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": 40,
            "handle": "@predictionuser",
            "email": "prediction-user@example.com",
            "display_name": "Prediction User",
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()
        api_market = get_domain_client().market("openai-gpt6-2026")
        api_market["options"] = [{**option, "id": index} for index, option in enumerate(api_market["options"], start=1)]
        result = {"stake_amount": 80, "potential_payout": 160}

        with patch("markets.views.create_prediction", return_value=result), patch("markets.views.get_market", return_value=api_market):
            response = self.client.post(route, {"option_id": 1, "stake_amount": 80})
            self.assertContains(response, "Previsão registrada")

        with patch("markets.views.create_prediction", side_effect=AuthAPIError("Você já registrou uma previsão neste mercado.", 409)), patch("markets.views.get_market", return_value=api_market):
            response = self.client.post(route, {"option_id": 1, "stake_amount": 80})
            self.assertContains(response, "Você já registrou uma previsão neste mercado.", status_code=400)

    def test_prediction_confirm_does_not_persist_locally_when_api_is_unavailable(self):
        User = get_user_model()
        user = User.objects.create_user(username="localpredict", email="local-predict@example.com", password="testpass123", first_name="Local Predict")
        WalletBalance.objects.create(user=user, available_gtl=2000, locked_gtl=0, total_earned_gtl=0)
        option = MarketOption.objects.get(market__slug="openai-gpt6-2026", label="SIM")
        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": user.id,
            "handle": user.username,
            "email": user.email,
            "display_name": user.first_name,
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()

        api_market = get_domain_client().market("openai-gpt6-2026")
        api_market["options"] = [{**row, "id": option.id if row["label"] == "SIM" else row.get("id", option.id + 1)} for row in api_market["options"]]
        with patch("markets.views.create_prediction", side_effect=AuthAPIError("Serviço de autenticação indisponível.", None)), patch("markets.views.get_market", return_value=api_market):
            response = self.client.post(reverse("prediction-confirm", args=["openai-gpt6-2026"]), {"option_id": option.id, "stake_amount": 80})

        self.assertContains(response, "Serviço de autenticação indisponível.", status_code=400)
        self.assertFalse(Prediction.objects.filter(user=user, market__slug="openai-gpt6-2026").exists())
        balance = WalletBalance.objects.get(user=user)
        self.assertEqual(balance.available_gtl, 2000)
        self.assertEqual(balance.locked_gtl, 0)

    def test_market_detail_hydrates_option_ids_from_local_db_when_api_payload_is_stale(self):
        User = get_user_model()
        user = User.objects.create_user(username="hydratecase", email="hydratecase@example.com", password="testpass123")
        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": user.id,
            "handle": user.username,
            "email": user.email,
            "display_name": user.username,
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()
        api_market = get_domain_client().market("openai-gpt6-2026")
        self.assertNotIn("id", api_market["options"][0])

        with patch("markets.views.get_market", return_value=api_market):
            response = self.client.get(reverse("market-detail", args=["openai-gpt6-2026"]))

        option = MarketOption.objects.get(market__slug="openai-gpt6-2026", label=api_market["options"][0]["label"])
        self.assertContains(response, f'data-option-id="{option.id}"')
        self.assertContains(response, f'data-selected-option-id type="radio" name="option_id" value="{option.id}" required')

    def test_resolved_market_detail_shows_resolution_time_and_personal_outcome(self):
        User = get_user_model()
        user = User.objects.create_user(username="resolvedviewer", email="resolved-viewer@example.com", password="testpass123")
        market = Market.objects.get(slug="openai-gpt6-2026")
        winning_option = MarketOption.objects.get(market=market, label="SIM")
        Prediction.objects.create(
            user=user,
            market=market,
            market_option=winning_option,
            stake_amount=80,
            probability_at_entry=Decimal("50.0000"),
            weight_at_entry=8000,
            potential_payout=160,
            status="resolved",
            won=True,
        )
        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": user.id,
            "handle": user.username,
            "email": user.email,
            "display_name": user.username,
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()
        api_market = {
            **get_domain_client().market("openai-gpt6-2026"),
            "status": "resolved",
            "status_label": "Resolvido",
            "primary_outcome": "SIM",
            "resolved_at": "2026-05-18T12:30:00+00:00",
            "resolution_timezone": "America/Sao_Paulo",
            "resolved_at_label": "18/05/2026 09:30 America/Sao_Paulo",
            "resolution_note": "Fonte validada.",
        }
        api_market["options"] = [{**option, "id": index} for index, option in enumerate(api_market["options"], start=1)]

        with patch("markets.views.get_market", return_value=api_market):
            response = self.client.get(reverse("market-detail", args=["openai-gpt6-2026"]))

        self.assertContains(response, "Resultado oficial")
        self.assertContains(response, "detail-market-actions")
        self.assertContains(response, "detail-comment-count")
        self.assertContains(response, "detail-like-button")
        self.assertContains(response, "detail-favorite-button")
        self.assertContains(response, "Criação")
        self.assertContains(response, "Aberto")
        self.assertContains(response, "Fechamento")
        self.assertContains(response, "Resolução")
        self.assertContains(response, "Distribuição")
        self.assertContains(response, "18/05/2026 09:30 America/Sao_Paulo")
        self.assertContains(response, "Timezone: America/Sao_Paulo")
        self.assertNotContains(response, '<div class="resolution-meta"><span>18/05/2026 09:30 America/Sao_Paulo</span><span>America/Sao_Paulo</span></div>', html=True)
        self.assertContains(response, "Você acertou esta previsão.")
        self.assertContains(response, "acerto creditado")

    def test_market_detail_renders_comments_and_comment_actions_use_api(self):
        session = self.client.session
        session[TOKEN_KEY] = "comment-token"
        session[USER_KEY] = {
            "id": 51,
            "handle": "commentviewer",
            "email": "comment-viewer@example.com",
            "display_name": "Comment Viewer",
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()
        api_market = get_domain_client().market("openai-gpt6-2026")
        api_market["options"] = [{**option, "id": index} for index, option in enumerate(api_market["options"], start=1)]
        api_market["comments"] = [
            {
                "id": 12,
                "market_slug": "openai-gpt6-2026",
                "author_id": 50,
                "author_handle": "analista",
                "author_display_name": "Analista",
                "body": "Comentário vindo da API.",
                "status": "visible",
                "like_count": 2,
                "dislike_count": 1,
                "viewer_reaction": "like",
                "created_at": "2026-05-18T12:00:00+00:00",
            }
        ]

        with patch("markets.views.get_market", return_value=api_market):
            response = self.client.get(reverse("market-detail", args=["openai-gpt6-2026"]))
        self.assertContains(response, "Comentário vindo da API.")
        self.assertContains(response, "detail-comment-count")
        self.assertContains(response, 'aria-label="1 comentário"')
        self.assertContains(response, "@analista")
        self.assertContains(response, 'aria-label="Curtir comentário"')
        self.assertContains(response, 'aria-label="Discordar do comentário"')

        with patch("markets.views.create_comment", return_value=api_market["comments"][0]) as create_comment:
            response = self.client.post(reverse("comment-submit", args=["openai-gpt6-2026"]), {"body": "Novo comentário"})
            self.assertEqual(response.status_code, 302)
            create_comment.assert_called_once()

        with patch("markets.views.create_comment", side_effect=AuthAPIError("Comentário não pode ficar vazio.", 422)), patch("markets.views.get_market", return_value=api_market):
            response = self.client.post(reverse("comment-submit", args=["openai-gpt6-2026"]), {"body": " "})
            self.assertContains(response, "Comentário não pode ficar vazio.", status_code=400)

        with patch("markets.views.react_to_comment", return_value=api_market["comments"][0]) as react:
            response = self.client.post(
                reverse("comment-reaction", args=["openai-gpt6-2026", 12]),
                {"reaction": "dislike", "current_reaction": "like"},
            )
            self.assertEqual(response.status_code, 302)
            react.assert_called_once_with("comment-token", 12, "dislike")

        with patch("markets.views.clear_comment_reaction", return_value=api_market["comments"][0]) as clear:
            response = self.client.post(
                reverse("comment-reaction", args=["openai-gpt6-2026", 12]),
                {"reaction": "like", "current_reaction": "like"},
            )
            self.assertEqual(response.status_code, 302)
            clear.assert_called_once_with("comment-token", 12, "like")

    def test_comment_submit_redirects_guest_to_login(self):
        response = self.client.post(reverse("comment-submit", args=["openai-gpt6-2026"]), {"body": "Olá"})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_home_hydrates_card_sparklines_when_api_payload_is_stale(self):
        api_market = get_domain_client().market("openai-gpt6-2026")
        api_market.pop("sparkline_series", None)
        api_market.pop("sparkline_path", None)

        with patch("core.views.get_markets", return_value=[api_market]):
            response = self.client.get(reverse("home"))

        self.assertContains(response, "sparkline-card")
        self.assertContains(response, "sparkline-line series-1")
        self.assertNotContains(response, 'd=""')

    def test_market_card_renders_thumbnail_image_when_available(self):
        market = get_domain_client().market("openai-gpt6-2026")
        market["image_url"] = "/media/market_thumbnails/test-thumb.jpg"
        with patch("core.views.get_markets", return_value=[market]):
            response = self.client.get(reverse("home"))

        self.assertContains(
            response,
            '<img src="/media/market_thumbnails/test-thumb.jpg" alt="" loading="lazy" decoding="async" data-thumb-image>',
            html=True,
        )

    def test_market_card_title_links_to_market_detail(self):
        market = get_domain_client().market("openai-gpt6-2026")
        with patch("core.views.get_markets", return_value=[market]):
            response = self.client.get(reverse("home"))

        expected = f'<h3><a class="market-title-link" href="{reverse("market-detail", args=[market["slug"]])}">{market["title"]}</a></h3>'
        self.assertContains(response, expected, html=True)

    def test_home_prediction_filter_is_only_rendered_for_authenticated_users(self):
        market = {**get_domain_client().market("openai-gpt6-2026"), "viewer_has_prediction": True, "viewer_has_favorite": True, "viewer_has_like": True}

        with patch("core.views.get_markets", return_value=[market]):
            guest_response = self.client.get(reverse("home"))
        self.assertNotContains(guest_response, 'data-filter="predicted"')
        self.assertNotContains(guest_response, 'data-filter="favorited"')
        self.assertNotContains(guest_response, '<form class="market-favorite-form"')
        self.assertNotContains(guest_response, '<form class="market-like-form"')
        self.assertContains(guest_response, "market-like-button readonly")
        self.assertContains(guest_response, "market-favorite-button readonly")
        self.assertContains(guest_response, "deadline-rail")
        self.assertContains(guest_response, "data-deadline-rail")
        self.assertContains(guest_response, "Tempo restante:")
        self.assertContains(guest_response, "data-guest-like-button")
        self.assertContains(guest_response, "data-guest-favorite-button")
        self.assertContains(guest_response, 'data-filter="likes"')
        self.assertContains(guest_response, "market-card-actions")
        self.assertContains(guest_response, 'data-market-predicted="true"')
        self.assertContains(guest_response, 'data-market-favorited="true"')
        self.assertContains(guest_response, 'data-market-liked="true"')

        session = self.client.session
        session[TOKEN_KEY] = "feed-token"
        session[USER_KEY] = {
            "id": 40,
            "handle": "@feedpredictionuser",
            "email": "feed-prediction-user@example.com",
            "display_name": "Feed Prediction User",
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()
        with (
            patch("core.views.get_markets", return_value=[market]) as get_markets,
            patch("core.views.get_me", side_effect=AuthAPIError("off")),
            patch("core.views.get_badges", side_effect=AuthAPIError("off")),
        ):
            auth_response = self.client.get(reverse("home"))

        get_markets.assert_called_once_with(token="feed-token")
        self.assertContains(auth_response, 'class="filter personal-filter" type="button" data-filter="predicted"')
        self.assertContains(auth_response, 'data-filter="favorited"')
        self.assertContains(auth_response, 'data-filter="likes"')
        self.assertContains(auth_response, "Minhas previsões")
        self.assertContains(auth_response, 'data-market-predicted="true"')
        self.assertContains(auth_response, 'data-market-favorited="true"')
        self.assertContains(auth_response, 'data-market-liked="true"')
        self.assertContains(auth_response, "market-favorite-button active")
        self.assertContains(auth_response, "market-card-actions")
        self.assertContains(auth_response, "market-like-button active")
        self.assertContains(auth_response, "Nenhum mercado com previsão sua ainda.")

    def test_home_renders_comment_count_and_notification_bell(self):
        User = get_user_model()
        user = User.objects.create_user(username="@notifyweb", email="notify-web@example.com", password="testpass123", first_name="Notify Web")
        market_model = Market.objects.get(slug="openai-gpt6-2026")
        UserNotification.objects.create(
            recipient=user,
            actor=user,
            market=market_model,
            event_type="market_comment",
            source_key="web-notification",
            title="Novo comentário em um mercado seu",
            body="Alguém comentou em um mercado em que você fez previsão.",
        )
        UserNotification.objects.create(
            recipient=user,
            event_type="wallet_credit",
            source_key="web-wallet-credit",
            title="Créditos recebidos",
            body="Você recebeu 250 créditos.",
        )
        UserNotification.objects.create(
            recipient=user,
            event_type="badge_awarded",
            source_key="web-badge-awarded",
            title="Badge recebida",
            body="Você recebeu uma badge.",
        )
        market = {**get_domain_client().market("openai-gpt6-2026"), "comment_count": 3}

        with patch("core.views.get_markets", return_value=[market]):
            guest_response = self.client.get(reverse("home"))
        self.assertContains(guest_response, 'data-market-comments="3"')
        self.assertContains(guest_response, "market-comment-count")
        self.assertContains(guest_response, ">3</span>")
        self.assertContains(guest_response, "guest-notification-button")
        self.assertContains(guest_response, "Notificações disponíveis para usuários logados")
        self.assertContains(guest_response, "disabled")
        self.assertNotContains(guest_response, "notification-menu")

        session = self.client.session
        session[TOKEN_KEY] = "notify-token"
        session[USER_KEY] = {
            "id": user.id,
            "handle": user.username,
            "email": user.email,
            "display_name": user.first_name,
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()
        with (
            patch("core.views.get_markets", return_value=[market]),
            patch("core.views.get_me", side_effect=AuthAPIError("off")),
            patch("core.views.get_badges", side_effect=AuthAPIError("off")),
            patch("core.context_processors.get_notifications", side_effect=AuthAPIError("off")),
        ):
            auth_response = self.client.get(reverse("home"))
        self.assertContains(auth_response, "notification-button")
        self.assertContains(auth_response, "notification-menu")
        self.assertContains(auth_response, "Novo comentário em um mercado seu")
        self.assertContains(auth_response, 'href="/wallet/"')
        self.assertContains(auth_response, 'href="/badges/"')
        self.assertContains(auth_response, "Marcar lidas")
        self.assertContains(auth_response, "3 notificações não lidas")

        with patch("core.views.mark_notifications_read", side_effect=AuthAPIError("off")):
            response = self.client.post(reverse("notifications-read-all"), {"next": reverse("home")})
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(UserNotification.objects.filter(recipient=user, is_read=False).exists())

    def test_home_prediction_filter_uses_local_prediction_flag_when_api_payload_is_stale(self):
        User = get_user_model()
        user = User.objects.create_user(username="@feedlocal", email="feed-local@example.com", password="testpass123")
        market = Market.objects.get(slug="openai-gpt6-2026")
        option = MarketOption.objects.get(market=market, label="SIM")
        Prediction.objects.create(
            user=user,
            market=market,
            market_option=option,
            stake_amount=50,
            probability_at_entry=Decimal("50.0000"),
            weight_at_entry=5000,
            potential_payout=100,
        )
        MarketFavorite.objects.create(user=user, market=market)
        MarketLike.objects.create(user=user, market=market)
        api_market = get_domain_client().market("openai-gpt6-2026")
        api_market.pop("viewer_has_prediction", None)
        api_market.pop("viewer_has_favorite", None)
        api_market.pop("viewer_has_like", None)
        session = self.client.session
        session[TOKEN_KEY] = "feed-local-token"
        session[USER_KEY] = {
            "id": user.id,
            "handle": user.username,
            "email": user.email,
            "display_name": "Feed Local",
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()

        with (
            patch("core.views.get_markets", return_value=[api_market]),
            patch("core.views.get_me", side_effect=AuthAPIError("off")),
            patch("core.views.get_badges", side_effect=AuthAPIError("off")),
        ):
            response = self.client.get(reverse("home"))

        self.assertContains(response, 'data-market-predicted="true"')
        self.assertContains(response, 'data-market-favorited="true"')
        self.assertContains(response, 'data-market-liked="true"')

    def test_market_filter_javascript_supports_open_and_view_based_trending(self):
        script = (settings.BASE_DIR / "static/js/gotrendlabs.js").read_text()

        self.assertIn("views: parseNumber(card.dataset.marketViews)", script)
        self.assertIn('mode === "likes"', script)
        self.assertIn("return right.likes - left.likes || tieBreak;", script)
        self.assertIn('mode === "open" && card.dataset.marketStatus !== "open"', script)
        self.assertIn('mode === "closing" && card.dataset.marketStatus !== "locked"', script)
        self.assertIn('mode === "favorited" && card.dataset.marketFavorited !== "true"', script)
        self.assertIn('favorited: "Nenhum mercado favorito ainda."', script)
        self.assertIn("return right.views - left.views || tieBreak;", script)
        self.assertIn("Number(list.dataset.marketPageSize || 18)", script)
        self.assertIn("hydrateDeadlineRail", script)
        self.assertIn("card.dataset.marketCloseAt", script)
        self.assertIn("--time-left", script)
        self.assertIn("deadlineState", script)
        self.assertIn("deadlineAccent", script)
        self.assertIn("window.setInterval", script)
        self.assertIn("rail.dataset.deadlineState = state", script)
        self.assertIn("renderMarketChunk(list, mode, visibleCount)", script)
        self.assertIn("data-market-load-more-button", script)
        self.assertIn("[data-market-favorite-form]", script)
        self.assertIn("[data-market-like-form]", script)
        self.assertIn("[data-guest-like-button]", script)
        self.assertIn("[data-guest-favorite-button]", script)
        self.assertIn("Curtir mercados é permitido apenas para usuários logados.", script)
        self.assertIn("Favoritar mercados é permitido apenas para usuários logados.", script)
        self.assertIn('headers: {"X-Requested-With": "XMLHttpRequest"}', script)
        self.assertIn("syncMarketFavorite(payload.slug || form.dataset.marketSlug", script)
        self.assertIn("syncMarketLike(payload.slug || form.dataset.marketSlug", script)
        styles = (settings.BASE_DIR / "static/css/gotrendlabs.css").read_text()
        self.assertIn('[data-market-list][data-market-filter-mode="closing"] [data-market-card]:not([data-market-status="locked"])', styles)
        self.assertIn('[data-market-list][data-market-filter-mode="favorited"] [data-market-card][data-market-favorited="false"]', styles)
        self.assertIn(".market-favorite-button", styles)
        self.assertIn(".market-favorite-button.readonly", styles)
        self.assertIn(".deadline-rail", styles)
        self.assertIn(".deadline-rail-fill", styles)
        self.assertIn("width: var(--time-left)", styles)
        self.assertIn(".detail-market-thumb", styles)
        self.assertIn(".detail-title-row", styles)
        self.assertIn(".like-chip-button", styles)
        self.assertIn(".market-like-button.readonly", styles)
        self.assertIn(".market-auth-toast", styles)
        self.assertIn("color: var(--red)", styles)
        self.assertIn(".detail-market-actions", styles)
        self.assertIn(".detail-comment-count", styles)
        self.assertIn(".detail-like-button", styles)
        self.assertIn(".market-load-more", styles)
        self.assertIn(".market-load-more[hidden]", styles)
        self.assertIn('body[data-theme="dark"] .result-highlight .resolution-meta span', styles)
        self.assertIn('body[data-theme="dark"] .result-highlight .ticket-note', styles)

    def test_home_guest_load_more_is_available_when_feed_has_more_than_one_chunk(self):
        api_market = get_domain_client().market("openai-gpt6-2026")
        markets = [
            {
                **api_market,
                "slug": f"guest-load-more-{index}",
                "title": f"Mercado visitante {index}",
                "view_count": index,
                "created_at": f"2026-05-{index:02d}T12:00:00+00:00",
            }
            for index in range(1, 20)
        ]

        with patch("core.views.get_markets", return_value=markets):
            response = self.client.get(reverse("home"))

        html = response.content.decode()
        self.assertNotIn('data-filter="predicted"', html)
        self.assertContains(response, 'data-market-page-size="18"')
        self.assertContains(response, 'data-market-load-more')
        self.assertContains(response, "Exibindo 18 de 19 mercados")
        load_more = html.split('<div class="market-load-more" data-market-load-more', 1)[1].split(">", 1)[0]
        self.assertNotIn("hidden", load_more)
        rendered_cards = html.split("<article\n  class=\"market-card\"")[1:]
        self.assertEqual(len(rendered_cards), 19)
        first_chunk_opening_tags = [card.split(">", 1)[0] for card in rendered_cards[:18]]
        nineteenth_opening_tag = rendered_cards[18].split(">", 1)[0]
        self.assertTrue(all("hidden" not in tag for tag in first_chunk_opening_tags))
        self.assertIn("hidden", nineteenth_opening_tag)

    def test_market_favorite_toggle_view_requires_login_and_calls_api(self):
        login_redirect = self.client.post(reverse("market-favorite-toggle", args=["openai-gpt6-2026"]), {"next": reverse("home")})
        self.assertEqual(login_redirect.status_code, 302)
        self.assertIn(reverse("login"), login_redirect["Location"])

        session = self.client.session
        session[TOKEN_KEY] = "favorite-token"
        session[USER_KEY] = {
            "id": 51,
            "handle": "@favoriteuser",
            "email": "favorite-user@example.com",
            "display_name": "Favorite User",
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()

        with patch("markets.views.favorite_market", return_value={"viewer_has_favorite": True}) as favorite:
            response = self.client.post(
                reverse("market-favorite-toggle", args=["openai-gpt6-2026"]),
                {"current_favorite": "false", "next": reverse("home")},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "slug": "openai-gpt6-2026", "favorited": True})
        favorite.assert_called_once_with("favorite-token", "openai-gpt6-2026")

        with patch("markets.views.unfavorite_market", return_value={"viewer_has_favorite": False}) as unfavorite:
            response = self.client.post(
                reverse("market-favorite-toggle", args=["openai-gpt6-2026"]),
                {"current_favorite": "true", "next": reverse("home")},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["favorited"])
        unfavorite.assert_called_once_with("favorite-token", "openai-gpt6-2026")

    def test_market_like_toggle_view_requires_login_and_calls_api_without_refresh(self):
        login_redirect = self.client.post(reverse("market-like-toggle", args=["openai-gpt6-2026"]), {"next": reverse("home")})
        self.assertEqual(login_redirect.status_code, 302)
        self.assertIn(reverse("login"), login_redirect["Location"])

        session = self.client.session
        session[TOKEN_KEY] = "like-token"
        session[USER_KEY] = {
            "id": 52,
            "handle": "@likeuser",
            "email": "like-user@example.com",
            "display_name": "Like User",
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()

        with patch("markets.views.like_market", return_value={"viewer_has_like": True, "market_like_count": 12}) as like:
            response = self.client.post(
                reverse("market-like-toggle", args=["openai-gpt6-2026"]),
                {"current_like": "false", "next": reverse("home")},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "slug": "openai-gpt6-2026", "liked": True, "like_count": 12})
        like.assert_called_once_with("like-token", "openai-gpt6-2026")

        with patch("markets.views.unlike_market", return_value={"viewer_has_like": False, "market_like_count": 11}) as unlike:
            response = self.client.post(
                reverse("market-like-toggle", args=["openai-gpt6-2026"]),
                {"current_like": "true", "next": reverse("home")},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["liked"])
        self.assertEqual(response.json()["like_count"], 11)
        unlike.assert_called_once_with("like-token", "openai-gpt6-2026")

    def test_market_card_renders_thumb_fallback_when_api_payload_has_empty_thumb(self):
        market = {
            **get_domain_client().market("openai-gpt6-2026"),
            "title": "Auditoria de distribuição MVP?",
            "category": "Modelos",
            "subcategory": "IA",
            "thumb": "",
            "thumb_color": "",
            "image_url": "",
        }
        with patch("core.views.get_markets", return_value=[market]):
            response = self.client.get(reverse("home"))

        self.assertContains(response, 'style="--thumb:#d8ece2"')
        self.assertContains(response, "MO")

    def test_home_does_not_render_canceled_markets(self):
        open_market = get_domain_client().market("openai-gpt6-2026")
        canceled_market = {
            **get_domain_client().market("tiktok-ban-eua-2026"),
            "status": "canceled",
            "status_label": "Cancelado",
        }

        with patch("core.views.get_markets", return_value=[open_market, canceled_market]):
            response = self.client.get(reverse("home"))

        self.assertContains(response, open_market["title"])
        market_list = response.content.decode().split(
            '<div class="market-list" data-market-list data-market-page-size="18">',
            1,
        )[1]
        self.assertNotIn(canceled_market["title"], market_list)

    def test_public_badges_page_renders_for_guest_and_authenticated_user(self):
        badges = [
            {
                "code": "founding_member",
                "name": "Membro fundador",
                "description": "Entrou cedo.",
                "rule_description": "Criar conta.",
                "badge_type": "global",
                "image_url": "/media/badge_images/founding.png",
                "image_dark_url": "/media/badge_images/founding-dark.png",
                "status": "earned",
                "earned_at": "2026-05-19T00:00:00+00:00",
            }
        ]
        with patch("core.views.get_badge_catalog", return_value=badges) as catalog_mock:
            response = self.client.get(reverse("badges"))
            self.assertContains(response, "Membro fundador")
            self.assertContains(response, "Entrar para ver progresso")
            self.assertContains(response, "/media/badge_images/founding.png")
            self.assertContains(response, "/media/badge_images/founding-dark.png")
            self.assertNotContains(response, "Compartilhar")
            catalog_mock.assert_called_with(None)

        session = self.client.session
        session[TOKEN_KEY] = "badge-token"
        session[USER_KEY] = {
            "id": 50,
            "handle": "badgeviewer",
            "email": "badge-viewer@example.com",
            "display_name": "Badge Viewer",
            "preferred_language": "pt-br",
        }
        session.save()
        with patch("core.views.get_badge_catalog", return_value=badges) as catalog_mock:
            response = self.client.get(reverse("badges"))
            self.assertContains(response, "Conquistada")
            self.assertContains(response, "Compartilhar")
            self.assertContains(response, reverse("share-badge", args=["founding_member"]))
            catalog_mock.assert_called_with("badge-token")

    def test_share_badge_page_requires_earned_badge(self):
        earned_badges = [
            {
                "code": "founding_member",
                "name": "Membro fundador",
                "description": "Entrou cedo.",
                "rule_description": "Criar conta.",
                "image_url": "/media/badge_images/founding.png",
                "image_dark_url": "/media/badge_images/founding-dark.png",
                "status": "earned",
            },
            {
                "code": "top_10",
                "name": "Top 10",
                "description": "Entrou no ranking.",
                "rule_description": "Alcance o top 10.",
                "status": "locked",
            },
        ]
        response = self.client.get(reverse("share-badge", args=["founding_member"]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

        session = self.client.session
        session[TOKEN_KEY] = "badge-token"
        session[USER_KEY] = {
            "id": 50,
            "handle": "badgeviewer",
            "email": "badge-viewer@example.com",
            "display_name": "Badge Viewer",
            "preferred_language": "pt-br",
        }
        session.save()
        with patch("core.views.get_badges", return_value=earned_badges) as badges_mock:
            response = self.client.get(reverse("share-badge", args=["founding_member"]))
            self.assertContains(response, "Badge Viewer conquistou Membro fundador")
            self.assertContains(response, "Conquistas públicas em previsões com resolução auditável")
            self.assertNotContains(response, "Compartilhar em")
            self.assertNotContains(response, "Compartilhar conquista")
            self.assertContains(response, 'aria-label="Copiar link"')
            self.assertContains(response, 'data-share-text="http://testserver/share/badge/founding_member/?t=')
            self.assertNotContains(response, 'data-share-text="Badge Viewer conquistou')
            self.assertContains(response, "/media/badge_images/founding.png")
            self.assertContains(response, "/media/badge_images/founding-dark.png")
            self.assertContains(response, "GoTrendLabs")
            self.assertContains(response, "testserver/share/badge/founding_member")
            self.assertContains(response, "t=")
            self.assertNotContains(response, "u=50")
            self.assertContains(response, 'property="og:image"')
            self.assertContains(response, 'name="twitter:image"')
            self.assertContains(response, "https://wa.me/")
            self.assertContains(response, "https://t.me/share/url")
            self.assertContains(response, "https://x.com/intent/tweet")
            self.assertContains(response, "https://www.facebook.com/sharer/sharer.php")
            self.assertContains(response, "https://www.linkedin.com/sharing/share-offsite/")
            self.assertContains(response, "Preview social indisponível neste host")
            self.assertNotContains(response, "Voltar às badges")
            badges_mock.assert_called_with("badge-token")

        with patch("core.views.get_badges", return_value=earned_badges):
            response = self.client.get(reverse("share-badge-image", args=["founding_member"]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/png")
            self.assertGreater(len(response.content), 1000)

        with patch("core.views.get_badges", return_value=earned_badges):
            response = self.client.get(reverse("share-badge", args=["top_10"]))
            self.assertRedirects(response, reverse("badges"))

        with patch("core.views.get_badges", return_value=earned_badges):
            response = self.client.get(reverse("share-badge-image", args=["top_10"]))
            self.assertRedirects(response, reverse("badges"))

    def test_public_badge_share_link_is_unique_to_awarded_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="@publicbadge", email="public-badge@example.com", password="testpass123", first_name="Public Badge")
        badge = BadgeDefinition.objects.create(
            code="public_founder",
            name="Membro publico",
            description="Entrou cedo.",
            rule_description="Criar conta na fase inicial.",
            image_url="/media/badge_images/founding_member.png",
        )
        UserBadgeAward.objects.create(user=user, badge=badge, awarded_at=timezone.now(), reason_snapshot="Criar conta.")
        token = public_badge_share_token(user.id, "public_founder")

        url = f"{reverse('share-badge', args=['public_founder'])}?t={token}"
        image_url = f"{reverse('share-badge-image', args=['public_founder'])}?t={token}"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Badge conquistou Membro publico")
        self.assertContains(response, f"testserver/share/badge/public_founder/?t={token}")
        self.assertContains(response, f"testserver/share/badge/public_founder/image/?t={token}")
        self.assertNotContains(response, f"u={user.id}")
        self.assertNotContains(response, "public-badge@example.com")

        response = self.client.get(image_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertGreater(len(response.content), 1000)

    def test_market_and_result_share_pages_expose_social_cards(self):
        market = get_domain_client().market("openai-gpt6-2026")
        resolved_market = {**market, "slug": "resolved-api", "status": "resolved", "title": "Resultado vindo da API", "primary_outcome": "SIM"}

        with patch("core.views.get_market", return_value=market):
            response = self.client.get(reverse("share-market", args=["openai-gpt6-2026"]))
            self.assertContains(response, "GoTrendLabs")
            self.assertContains(response, "testserver/share/market/openai-gpt6-2026")
            self.assertContains(response, "Consenso público, reputação e resolução auditável")
            self.assertContains(response, "Registre previsões, compare com a comunidade e construa reputação.")
            self.assertContains(response, "Opções do mercado")
            self.assertContains(response, "SIM")
            self.assertContains(response, 'class="share-cta"')
            self.assertContains(response, reverse("market-detail", args=["openai-gpt6-2026"]))
            self.assertNotContains(response, "Abrir mercado")
            self.assertNotContains(response, "Entrar na previsão")
            self.assertContains(response, 'property="og:image"')
            self.assertContains(response, 'name="twitter:image"')
            self.assertContains(response, "https://wa.me/")
            self.assertContains(response, "https://t.me/share/url")
            self.assertContains(response, "https://x.com/intent/tweet")
            self.assertContains(response, "https://www.facebook.com/sharer/sharer.php")
            self.assertContains(response, "https://www.linkedin.com/sharing/share-offsite/")
            self.assertContains(response, reverse("share-market-track", args=["openai-gpt6-2026"]))

        empty_thumb_market = {
            **market,
            "slug": "empty-thumb-share",
            "title": "Auditoria de distribuição MVP?",
            "category": "Modelos",
            "thumb": "",
            "thumb_color": "",
            "image_url": "",
        }
        with patch("core.views.get_market", return_value=empty_thumb_market):
            response = self.client.get(reverse("share-market", args=["empty-thumb-share"]))
            self.assertContains(response, '<span class="badge-icon">MO</span>', html=True)

        with patch("core.views.get_market", return_value=market):
            response = self.client.get(reverse("share-market-image", args=["openai-gpt6-2026"]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/png")
            self.assertGreater(len(response.content), 1000)

        with patch("core.views.get_market", return_value=resolved_market):
            response = self.client.get(reverse("share-result", args=["resolved-api"]))
            self.assertContains(response, "GoTrendLabs")
            self.assertContains(response, "Resultado vindo da API")
            self.assertContains(response, "<span>Resultado</span><strong>SIM</strong>", html=True)
            self.assertLess(response.content.decode().index("Resultado vindo da API"), response.content.decode().index("<span>Resultado</span>"))
            self.assertContains(response, "testserver/share/result/resolved-api")
            self.assertNotContains(response, "Resultado publicado no GoTrendLabs.")
            self.assertContains(response, "Consenso público, reputação e resolução auditável")
            self.assertNotContains(response, "Will Costa")
            self.assertNotContains(response, "compartilhou um resultado.")
            self.assertNotContains(response, "Reputação atual")
            self.assertContains(response, 'property="og:image"')
            self.assertContains(response, 'name="twitter:image"')
            self.assertContains(response, "https://wa.me/")
            self.assertContains(response, "https://t.me/share/url")
            self.assertContains(response, "https://x.com/intent/tweet")
            self.assertContains(response, "https://www.facebook.com/sharer/sharer.php")
            self.assertContains(response, "https://www.linkedin.com/sharing/share-offsite/")
            self.assertContains(response, reverse("share-market-track", args=["resolved-api"]))
            self.assertNotContains(response, "Ver perfil")

        with patch("core.views.get_market", return_value=resolved_market):
            response = self.client.get(reverse("share-result-image", args=["resolved-api"]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/png")
            self.assertGreater(len(response.content), 1000)

    def test_market_detail_and_share_tracking_increment_local_counters(self):
        market = Market.objects.get(slug="openai-gpt6-2026")
        market.view_count = 0
        market.share_count = 0
        market.save(update_fields=["view_count", "share_count"])

        with patch("markets.views.track_market_view", side_effect=AuthAPIError("offline")):
            response = self.client.get(reverse("market-detail", args=["openai-gpt6-2026"]))
        self.assertEqual(response.status_code, 200)
        market.refresh_from_db()
        self.assertEqual(market.view_count, 1)

        with patch("core.views.track_market_share", side_effect=AuthAPIError("offline")):
            response = self.client.post(reverse("share-market-track", args=["openai-gpt6-2026"]))
        self.assertEqual(response.status_code, 200)
        market.refresh_from_db()
        self.assertEqual(market.share_count, 1)

    def test_admin_config_persists_maintenance_json_and_smtp_database_config(self):
        staff = get_user_model().objects.create_user(
            username="@configstaff",
            email="config-staff@example.com",
            password="testpass123",
            first_name="Config Staff",
        )
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": staff.id,
            "handle": staff.username,
            "email": staff.email,
            "display_name": staff.first_name,
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()

        with TemporaryDirectory() as tmpdir, override_settings(
            GOTRENDLABS_RUNTIME_CONFIG_PATH=os.path.join(tmpdir, "platform_config.json"),
            GOTRENDLABS_SMTP_PASSWORD="super-secret-smtp",
            GOTRENDLABS_SMTP_API_KEY="",
        ):
            response = self.client.get(reverse("admin-ops-config"))
            self.assertContains(response, "Controles da plataforma")
            self.assertContains(response, "Segredo SMTP")
            self.assertContains(response, "Configurado por ambiente")
            self.assertContains(response, "Preset AWS SES")
            self.assertContains(response, "Enviar teste sandbox")
            self.assertContains(response, "Saldo máximo para solicitar")
            self.assertContains(response, "Purge de logs e auditoria IA")
            self.assertContains(response, 'name="retention-system_log_retention_days"')
            self.assertContains(response, 'name="retention-ai_audit_retention_days"')
            self.assertContains(response, "Agentes IA oficiais nunca simulam pessoas.")
            self.assertContains(response, "Regras dos agentes")
            self.assertContains(response, "Comentários IA podem ocorrer com 0 humanos")
            self.assertContains(response, "Previsão bot só roda")
            self.assertContains(response, "Falhas da LLM/provedor configurado são auditadas")
            self.assertContains(response, "Horas mínimas antes de voltar ao mesmo mercado.")
            self.assertContains(response, "Bot só prevê após atingir este número de humanos.")
            self.assertContains(response, "Tempo máximo de espera por chamada LLM.")
            self.assertContains(response, 'name="ai-ai_llm_provider"')
            self.assertContains(response, 'name="ai-ai_max_stake_gtl"')
            self.assertContains(response, 'name="ai-ai_predictions_enabled"')
            self.assertContains(response, 'name="ai-ai_max_comment_attempts_per_cycle"')
            self.assertContains(response, 'name="ai-ai_comment_candidate_limit"')
            self.assertNotContains(response, "super-secret-smtp")

            response = self.client.post(
                reverse("admin-ops-config"),
                {
                    "maintenance-maintenance_enabled": "on",
                    "maintenance-maintenance_message": "Voltamos logo depois da janela operacional.",
                    "economy-wallet_recharge_min_balance_gtl": "150",
                    "daemon-daemon_stale_after_minutes": "7",
                    "daemon-daemon_missing_after_minutes": "21",
                    "retention-system_log_retention_days": "45",
                    "retention-ai_audit_retention_days": "120",
                    "email-email_enabled": "on",
                    "email-smtp_host": "smtp.example.com",
                    "email-smtp_port": "587",
                    "email-smtp_username": "mailer@example.com",
                    "email-smtp_use_tls": "on",
                    "email-smtp_timeout_seconds": "15",
                    "email-default_from_email": "no-reply@example.com",
                    "email-default_reply_to_email": "support@example.com",
                },
            )
            self.assertEqual(response.status_code, 302)
            config = load_platform_config()
            self.assertTrue(config["maintenance_enabled"])
            self.assertEqual(config["maintenance_message"], "Voltamos logo depois da janela operacional.")
            self.assertEqual(config["updated_by"], "@configstaff")
            self.assertNotIn("super-secret-smtp", str(config))

            site_config = SiteConfig.get_solo()
            self.assertTrue(site_config.email_enabled)
            self.assertEqual(site_config.smtp_host, "smtp.example.com")
            self.assertEqual(site_config.smtp_port, 587)
            self.assertTrue(site_config.smtp_use_tls)
            self.assertFalse(site_config.smtp_use_ssl)
            self.assertEqual(site_config.smtp_timeout_seconds, 15)
            self.assertEqual(site_config.default_from_email, "no-reply@example.com")
            self.assertEqual(site_config.default_reply_to_email, "support@example.com")
            self.assertEqual(site_config.wallet_recharge_min_balance_gtl, 150)
            self.assertEqual(site_config.daemon_stale_after_minutes, 7)
            self.assertEqual(site_config.daemon_missing_after_minutes, 21)
            self.assertEqual(site_config.system_log_retention_days, 45)
            self.assertEqual(site_config.ai_audit_retention_days, 120)
            self.assertNotIn("super-secret-smtp", str(site_config.__dict__))

            _seed_test_email_templates()
            template = EmailTemplate.objects.get(key="user.email_confirmation", locale="pt-br")
            response = self.client.get(reverse("admin-ops-email-template-edit", args=[template.id]))
            self.assertContains(response, "Politica de Emails")
            self.assertContains(response, "Logs de envio")
            self.assertContains(response, "Somente PT-BR nesta versão")
            self.assertContains(response, "Variáveis disponíveis")
            self.assertContains(response, "Visualizar email HTML")
            self.assertContains(response, "user.email_confirmation")
            self.assertContains(response, "Confirme seu email e libere sua conta")
            self.assertContains(response, "confirmation_url")
            self.assertContains(response, "{{ confirmation_url }}")
            self.assertContains(response, "https://gotrendlabs.com.br/email-confirm/confirm/exemplo/")
            response = self.client.post(
                reverse("admin-ops-email-template-edit", args=[template.id]),
                {
                    "subject": "Assunto editado {{ display_name }}",
                    "body_text": "Corpo editado {{ confirmation_url }}",
                    "body_html": "",
                    "is_active": "on",
                },
            )
            self.assertEqual(response.status_code, 302)
            template.refresh_from_db()
            self.assertEqual(template.subject, "Assunto editado {{ display_name }}")
            self.assertEqual(template.updated_by, staff)

            EmailDelivery.objects.create(
                event_type="account.password_reset",
                recipient_user=staff,
                recipient_email=staff.email,
                template_key="account.password_reset",
                locale="pt-br",
                subject="Redefina sua senha na GoTrendLabs",
                body_text="Use o link",
                body_html="<a href='https://gotrendlabs.com.br/password-reset/confirm/secret/'>Reset</a>",
                context={"reset_url": "https://gotrendlabs.com.br/password-reset/confirm/secret/"},
                idempotency_key="account.password_reset:test-admin-log",
                status="sent",
                attempt_count=1,
                sent_at=timezone.now(),
            )
            EmailDelivery.objects.create(
                event_type="wallet.credited",
                recipient_email="person@example.com",
                template_key="wallet.credited",
                locale="pt-br",
                context={"wallet_url": "https://gotrendlabs.com.br/wallet/"},
                idempotency_key="wallet.credited:sandbox-suppressed",
                status="suppressed",
                last_error="SES sandbox guard suppressed delivery to an unverified recipient.",
            )
            response = self.client.get(reverse("admin-ops-email-delivery-logs"))
            self.assertContains(response, "Politica de Emails")
            self.assertContains(response, "Outbox, tentativas e falhas")
            self.assertContains(response, "Enviado")
            self.assertContains(response, "Bloqueado")
            self.assertContains(response, "account.password_reset")
            self.assertContains(response, "wallet.credited")
            self.assertContains(response, "account.password_reset:test-admin-log")
            self.assertNotContains(response, "password-reset/confirm/secret")
            response = self.client.get(f"{reverse('admin-ops-email-delivery-logs')}?status=suppressed&template_key=wallet.credited&recipient=person")
            self.assertContains(response, "person@example.com")
            self.assertNotContains(response, staff.email)

            response = self.client.post(
                reverse("admin-ops-config"),
                {
                    "maintenance-maintenance_message": "",
                    "economy-wallet_recharge_min_balance_gtl": "150",
                    "daemon-daemon_stale_after_minutes": "7",
                    "daemon-daemon_missing_after_minutes": "21",
                    "retention-system_log_retention_days": "0",
                    "retention-ai_audit_retention_days": "3651",
                    "email-smtp_port": "587",
                    "email-smtp_timeout_seconds": "15",
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'name="retention-system_log_retention_days"')
            self.assertContains(response, 'name="retention-ai_audit_retention_days"')
            site_config.refresh_from_db()
            self.assertEqual(site_config.system_log_retention_days, 45)
            self.assertEqual(site_config.ai_audit_retention_days, 120)

    def test_smtp_test_command_uses_site_config_and_environment_secret(self):
        site_config = SiteConfig.get_solo()
        site_config.email_enabled = False
        site_config.smtp_host = "email-smtp.us-east-1.amazonaws.com"
        site_config.smtp_port = 587
        site_config.smtp_username = "smtp-user"
        site_config.smtp_use_tls = True
        site_config.smtp_use_ssl = False
        site_config.smtp_timeout_seconds = 12
        site_config.default_from_email = "no-reply@gotrendlabs.com.br"
        site_config.default_reply_to_email = "support@gotrendlabs.com.br"
        site_config.save()

        out = StringIO()
        smtp_context = patch("admin_ops.management.commands.send_smtp_test_email.smtplib.SMTP")
        ssl_context = patch("admin_ops.management.commands.send_smtp_test_email.ssl.create_default_context", return_value="tls-context")
        with override_settings(GOTRENDLABS_SMTP_PASSWORD="smtp-secret", GOTRENDLABS_SMTP_API_KEY=""), smtp_context as smtp_cls, ssl_context:
            smtp = smtp_cls.return_value.__enter__.return_value
            call_command("send_smtp_test_email", "--to", "success@simulator.amazonses.com", stdout=out)

        smtp_cls.assert_called_once_with("email-smtp.us-east-1.amazonaws.com", 587, timeout=12)
        smtp.starttls.assert_called_once_with(context="tls-context")
        smtp.login.assert_called_once_with("smtp-user", "smtp-secret")
        smtp.send_message.assert_called_once()
        message = smtp.send_message.call_args.args[0]
        self.assertEqual(message["From"], "no-reply@gotrendlabs.com.br")
        self.assertEqual(message["To"], "success@simulator.amazonses.com")
        self.assertEqual(message["Reply-To"], "support@gotrendlabs.com.br")
        self.assertIn("Email delivery flag is disabled", out.getvalue())
        self.assertIn("SMTP test email sent", out.getvalue())

    def test_smtp_test_command_validates_required_secret(self):
        site_config = SiteConfig.get_solo()
        site_config.smtp_host = "email-smtp.us-east-1.amazonaws.com"
        site_config.smtp_port = 587
        site_config.smtp_username = "smtp-user"
        site_config.default_from_email = "no-reply@gotrendlabs.com.br"
        site_config.save()

        with override_settings(GOTRENDLABS_SMTP_PASSWORD="", GOTRENDLABS_SMTP_API_KEY=""):
            with self.assertRaisesMessage(Exception, "GOTRENDLABS_SMTP_PASSWORD or GOTRENDLABS_SMTP_API_KEY"):
                call_command("send_smtp_test_email", "--dry-run")

    def test_admin_config_persists_ai_agent_parameters(self):
        staff = get_user_model().objects.create_user(
            username="aiconfigstaff",
            email="ai-config-staff@example.com",
            password="test",
            is_staff=True,
            first_name="AI Config Staff",
        )
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": staff.id,
            "handle": staff.username,
            "email": staff.email,
            "display_name": staff.first_name,
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()

        with TemporaryDirectory() as tmpdir, override_settings(
            GOTRENDLABS_RUNTIME_CONFIG_PATH=os.path.join(tmpdir, "platform_config.json"),
            OPENAI_API_KEY="test-openai-key",
        ):
            response = self.client.post(
                reverse("admin-ops-config"),
                {
                    "maintenance-maintenance_message": "",
                    "economy-wallet_recharge_min_balance_gtl": "100",
                    "daemon-daemon_stale_after_minutes": "6",
                    "daemon-daemon_missing_after_minutes": "18",
                    "retention-system_log_retention_days": "90",
                    "retention-ai_audit_retention_days": "90",
                    "email-smtp_host": "",
                    "email-smtp_port": "587",
                    "email-smtp_username": "",
                    "email-smtp_timeout_seconds": "10",
                    "email-default_from_email": "",
                    "email-default_reply_to_email": "",
                    "ai-ai_agents_enabled": "on",
                    "ai-ai_commenting_enabled": "on",
                    "ai-ai_predictions_enabled": "on",
                    "ai-ai_llm_provider": "openai",
                    "ai-ai_llm_base_url": "https://api.openai.com/v1",
                    "ai-ai_model": "gpt-5.4-mini",
                    "ai-ai_high_reasoning_model": "gpt-5.5",
                    "ai-ai_market_cooldown_hours": "12",
                    "ai-ai_max_comments_per_market_per_day": "1",
                    "ai-ai_max_comments_per_cycle": "2",
                    "ai-ai_max_comment_attempts_per_cycle": "4",
                    "ai-ai_comment_candidate_limit": "250",
                    "ai-ai_max_comments_per_day": "15",
                    "ai-ai_comment_max_chars": "650",
                    "ai-ai_min_humans_for_prediction": "2",
                    "ai-ai_max_stake_gtl": "30",
                    "ai-ai_max_predictions_per_cycle": "2",
                    "ai-ai_max_predictions_per_day": "8",
                    "ai-ai_skip_if_human_comments_recent": "on",
                    "ai-ai_recent_human_comment_window_hours": "4",
                    "ai-ai_openai_timeout_seconds": "25",
                    "ai-ai_openai_max_retries": "2",
                    "ai-ai_pause_reason": "janela operacional",
                },
            )
            self.assertEqual(response.status_code, 302)

            site_config = SiteConfig.get_solo()
            self.assertTrue(site_config.ai_agents_enabled)
            self.assertTrue(site_config.ai_commenting_enabled)
            self.assertTrue(site_config.ai_predictions_enabled)
            self.assertEqual(site_config.ai_model, "gpt-5.4-mini")
            self.assertEqual(site_config.ai_high_reasoning_model, "gpt-5.5")
            self.assertEqual(site_config.ai_market_cooldown_hours, 12)
            self.assertEqual(site_config.ai_max_comments_per_cycle, 2)
            self.assertEqual(site_config.ai_max_comment_attempts_per_cycle, 4)
            self.assertEqual(site_config.ai_comment_candidate_limit, 250)
            self.assertEqual(site_config.ai_max_comments_per_day, 15)
            self.assertEqual(site_config.ai_comment_max_chars, 650)
            self.assertEqual(site_config.ai_min_humans_for_prediction, 2)
            self.assertEqual(site_config.ai_max_stake_gtl, 30)
            self.assertEqual(site_config.ai_max_predictions_per_cycle, 2)
            self.assertEqual(site_config.ai_max_predictions_per_day, 8)
            self.assertEqual(site_config.ai_recent_human_comment_window_hours, 4)
            self.assertEqual(site_config.ai_openai_timeout_seconds, 25)
            self.assertEqual(site_config.ai_openai_max_retries, 2)
            self.assertEqual(site_config.ai_pause_reason, "janela operacional")
            self.assertNotIn("test-openai-key", str(site_config.__dict__))

    def test_admin_config_rejects_tls_and_ssl_together(self):
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 404,
            "handle": "@staff",
            "email": "staff@example.com",
            "display_name": "Staff",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()

        with TemporaryDirectory() as tmpdir, override_settings(GOTRENDLABS_RUNTIME_CONFIG_PATH=os.path.join(tmpdir, "platform_config.json")):
            response = self.client.post(
                reverse("admin-ops-config"),
                {
                    "maintenance-maintenance_message": "Manutenção rápida.",
                    "economy-wallet_recharge_min_balance_gtl": "100",
                    "daemon-daemon_stale_after_minutes": "5",
                    "daemon-daemon_missing_after_minutes": "15",
                    "retention-system_log_retention_days": "90",
                    "retention-ai_audit_retention_days": "90",
                    "email-smtp_host": "smtp.example.com",
                    "email-smtp_port": "465",
                    "email-smtp_use_tls": "on",
                    "email-smtp_use_ssl": "on",
                    "email-smtp_timeout_seconds": "10",
                    "email-default_from_email": "no-reply@example.com",
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "TLS e SSL não podem ficar ativos ao mesmo tempo.")

    def test_admin_ai_agent_form_explains_types_and_uses_active_bot_users(self):
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 404,
            "handle": "@staff",
            "email": "staff@example.com",
            "display_name": "Staff",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()
        user_payload = {
            "users": [
                {
                    "id": 91,
                    "handle": "@gotrendlabs_ai_analyst",
                    "email": "ai@example.com",
                    "display_name": "GoTrendLabs AI Analyst",
                    "preferred_language": "pt-br",
                    "account_status": "active",
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "is_bot": True,
                    "created_at": "2026-05-22T00:00:00+00:00",
                    "last_login": None,
                    "deactivated_at": None,
                    "available_gtl": 500,
                    "locked_gtl": 0,
                    "reputation_score": 0,
                },
                {
                    "id": 92,
                    "handle": "@human",
                    "email": "human@example.com",
                    "display_name": "Human User",
                    "preferred_language": "pt-br",
                    "account_status": "active",
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "is_bot": False,
                    "created_at": "2026-05-22T00:00:00+00:00",
                    "last_login": None,
                    "deactivated_at": None,
                    "available_gtl": 100,
                    "locked_gtl": 0,
                    "reputation_score": 0,
                },
                {
                    "id": 93,
                    "handle": "@inactivebot",
                    "email": "inactive@example.com",
                    "display_name": "Inactive Bot",
                    "preferred_language": "pt-br",
                    "account_status": "deactivated",
                    "is_active": False,
                    "is_staff": False,
                    "is_superuser": False,
                    "is_bot": True,
                    "created_at": "2026-05-22T00:00:00+00:00",
                    "last_login": None,
                    "deactivated_at": "2026-05-22T01:00:00+00:00",
                    "available_gtl": 300,
                    "locked_gtl": 0,
                    "reputation_score": 0,
                },
            ],
            "counts": {"total": 3, "bots": 2},
        }
        created_agent = {
            "id": 7,
            "name": "GoTrendLabs Analyst",
            "agent_type": "analyst",
            "is_active": True,
            "user_id": 91,
            "user_handle": "@gotrendlabs_ai_analyst",
            "user_display_name": "GoTrendLabs AI Analyst",
            "user_is_bot": True,
            "personality_prompt": "",
            "comment_style": "",
        }
        with patch("admin_ops.views.admin_get_users", return_value=user_payload) as users_mock, patch("admin_ops.views.admin_create_ai_agent", return_value=created_agent) as create_mock:
            response = self.client.get(reverse("admin-ops-ai-agent-new"))
            self.assertContains(response, "Comenta mercados")
            self.assertContains(response, "Testa previsão bot")
            self.assertContains(response, "Experimental, sem ciclo ativo")
            self.assertContains(response, "Prévia operacional")
            self.assertContains(response, "Parâmetros globais atuais")
            self.assertContains(response, "sem rotina backend ativa")
            self.assertContains(response, "Não usado por Analyst")
            self.assertContains(response, "Não usado por Liquidity")
            self.assertContains(response, "GoTrendLabs AI Analyst (@gotrendlabs_ai_analyst) · ID 91 · 500 GT₵")
            self.assertNotContains(response, "Human User")
            self.assertNotContains(response, "Inactive Bot")
            users_mock.assert_called_with("staff-token", bot="yes", status="active", order="created_desc")

            response = self.client.post(
                reverse("admin-ops-ai-agent-new"),
                {
                    "name": "GoTrendLabs Analyst",
                    "agent_type": "analyst",
                    "user_id": "91",
                    "is_active": "on",
                    "personality_prompt": "Comente de forma equilibrada.",
                    "comment_style": "direto",
                    "max_comments_per_day": "",
                    "max_predictions_per_day": "",
                    "max_stake_gtl": "",
                    "cooldown_hours": "",
                    "min_humans_for_prediction": "",
                },
            )
            self.assertEqual(response.status_code, 302)
            create_mock.assert_called_once()
            self.assertEqual(create_mock.call_args.args[1]["user_id"], 91)
            self.assertIsNone(create_mock.call_args.args[1]["max_predictions_per_day"])
            self.assertIsNone(create_mock.call_args.args[1]["max_stake_gtl"])
            self.assertIsNone(create_mock.call_args.args[1]["min_humans_for_prediction"])

            create_mock.reset_mock()
            response = self.client.post(
                reverse("admin-ops-ai-agent-new"),
                {
                    "name": "GoTrendLabs Liquidity",
                    "agent_type": "liquidity",
                    "user_id": "91",
                    "is_active": "on",
                    "personality_prompt": "Este texto deve ser limpo para liquidity.",
                    "comment_style": "este estilo deve ser limpo",
                    "max_comments_per_day": "7",
                    "max_predictions_per_day": "3",
                    "max_stake_gtl": "25",
                    "cooldown_hours": "12",
                    "min_humans_for_prediction": "2",
                },
            )
            self.assertEqual(response.status_code, 302)
            payload = create_mock.call_args.args[1]
            self.assertEqual(payload["personality_prompt"], "")
            self.assertEqual(payload["comment_style"], "")
            self.assertIsNone(payload["max_comments_per_day"])
            self.assertIsNone(payload["cooldown_hours"])
            self.assertEqual(payload["max_predictions_per_day"], 3)
            self.assertEqual(payload["max_stake_gtl"], 25)
            self.assertEqual(payload["min_humans_for_prediction"], 2)

    def test_admin_ai_agent_audit_filters_reason_and_loads_more_in_blocks(self):
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 404,
            "handle": "@staff",
            "email": "staff@example.com",
            "display_name": "Staff",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()
        actions = [
            {
                "id": index,
                "agent_id": 2,
                "agent_name": "GoTrendLabs AI Analyst",
                "market_id": 43,
                "market_slug": "vencedor-grupo-c-copa-2026",
                "market_title": "Quem vencerá o Grupo C da Copa 2026?",
                "action_type": "comment",
                "status": "skipped" if index % 2 else "failed",
                "reason": "llm_error_timeout",
                "payload_summary": {},
                "prompt_template_version": "gotrendlabs-ai-agent-v2",
                "prompt_hash": "abc123",
                "comment_id": None,
                "prediction_id": None,
                "created_at": f"2026-05-23T10:{index:02d}:00+00:00",
            }
            for index in range(1, 13)
        ]
        with patch("admin_ops.views.admin_get_ai_agents", return_value={"agents": [], "health": {}}), patch("admin_ops.views.admin_get_ai_agent_actions", return_value={"actions": actions, "health": {}}) as actions_mock:
            response = self.client.get(reverse("admin-ops-ai-agent-actions") + "?reason=llm_error")

        self.assertEqual(response.status_code, 200)
        actions_mock.assert_called_with("staff-token", agent_id="", market_slug="", action_type="", status="", reason="llm_error")
        self.assertContains(response, 'name="reason"')
        self.assertContains(response, "10 de 12 ações")
        self.assertContains(response, "Carregar mais")
        self.assertContains(response, "reason=llm_error")
        self.assertContains(response, "Detalhe", count=10)

    def test_admin_ai_agent_action_detail_has_context_and_pretty_payload(self):
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 404,
            "handle": "@staff",
            "email": "staff@example.com",
            "display_name": "Staff",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()
        action = {
            "id": 7,
            "agent_id": 2,
            "agent_name": "GoTrendLabs AI Analyst",
            "market_id": 43,
            "market_slug": "vencedor-grupo-c-copa-2026",
            "market_title": "Quem vencerá o Grupo C da Copa 2026?",
            "action_type": "comment",
            "status": "created",
            "reason": "comment_created",
            "payload_summary": {"confidence": 0.68, "risk_flags": []},
            "prompt_template_version": "gotrendlabs-ai-agent-v2",
            "prompt_hash": "abc123def456abc123def456",
            "comment_id": 163,
            "prediction_id": None,
            "created_at": "2026-05-23T10:00:00+00:00",
        }
        with patch("admin_ops.views.admin_get_ai_agent_action", return_value=action):
            response = self.client.get(reverse("admin-ops-ai-agent-action-detail", args=[7]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ação #7")
        self.assertContains(response, "Agentes oficiais")
        self.assertContains(response, "Contexto")
        self.assertContains(response, "Prompt")
        self.assertContains(response, "Payload resumido")
        self.assertContains(response, "&quot;confidence&quot;: 0.68")
        self.assertContains(response, "vencedor-grupo-c-copa-2026")

    def test_maintenance_mode_redirects_public_pages_without_blocking_admin_or_assets(self):
        with TemporaryDirectory() as tmpdir, override_settings(GOTRENDLABS_RUNTIME_CONFIG_PATH=os.path.join(tmpdir, "platform_config.json")):
            save_platform_config(
                {
                    "maintenance_enabled": True,
                    "maintenance_message": "Manutenção de teste.",
                    "updated_by": "@ops",
                }
            )
            response = self.client.get(reverse("home"))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], reverse("maintenance"))
            response = self.client.get(reverse("rankings"))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], reverse("maintenance"))
            response = self.client.get(reverse("maintenance"))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Manutenção de teste.")
            self.assertContains(response, "GoTrendLabs está ficando mais estável.")
            self.assertContains(response, "Entrar como operador")
            self.assertContains(response, "Leituras com reputação pública")
            response = self.client.get(reverse("login"))
            self.assertEqual(response.status_code, 200)
            response = self.client.get(reverse("admin-ops-config"))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("login"), response["Location"])
            self.assertTrue(finders.find("css/gotrendlabs.css"))
            self.assertTrue(finders.find("js/gotrendlabs.js"))
            self.assertTrue(finders.find("brand/gtl-constellation-mark-light.svg"))
            self.assertTrue(finders.find("brand/gtl-constellation-mark-dark.svg"))

    def test_staff_can_browse_public_site_during_maintenance_with_operator_banner(self):
        staff = get_user_model().objects.create_user(
            username="@maintstaff",
            email="maint-staff@example.com",
            password="testpass123",
            first_name="Maint Staff",
        )
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": staff.id,
            "handle": staff.username,
            "email": staff.email,
            "display_name": staff.first_name,
            "preferred_language": "pt-br",
            "is_staff": True,
            "is_superuser": False,
        }
        session.save()
        with TemporaryDirectory() as tmpdir, override_settings(GOTRENDLABS_RUNTIME_CONFIG_PATH=os.path.join(tmpdir, "platform_config.json")):
            save_platform_config(
                {
                    "maintenance_enabled": True,
                    "maintenance_message": "Manutenção para visitantes.",
                    "updated_by": "@ops",
                }
            )
            response = self.client.get(reverse("home"))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Modo manutenção ativo")
            self.assertContains(response, "Você está navegando como operador")
            self.assertContains(response, reverse("admin-ops-config"))

    def test_user_chip_admin_link_only_renders_for_staff_or_superuser(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, reverse("admin-ops-dashboard"))

        session = self.client.session
        session[TOKEN_KEY] = "common-token"
        session[USER_KEY] = {
            "id": 501,
            "handle": "@commonfooter",
            "email": "common-footer@example.com",
            "display_name": "Common Footer",
            "preferred_language": "pt-br",
            "is_staff": False,
            "is_superuser": False,
        }
        session.save()
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, reverse("admin-ops-dashboard"))
        self.assertContains(response, "Carteira educativa")

        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 502,
            "handle": "@stafffooter",
            "email": "staff-footer@example.com",
            "display_name": "Staff Footer",
            "preferred_language": "pt-br",
            "is_staff": True,
            "is_superuser": False,
        }
        session.save()
        response = self.client.get(reverse("home"))
        html = response.content.decode()
        self.assertContains(response, "Painel Administrativo")
        self.assertContains(response, "Acesso restrito")
        self.assertContains(response, reverse("admin-ops-dashboard"))
        self.assertLess(html.find("Painel Administrativo"), html.find("Perfil e badges"))

    def test_public_top_nav_links_to_suggestion_for_all_visitors(self):
        home_response = self.client.get(reverse("home"))
        self.assertContains(home_response, "Sugerir mercado")
        self.assertContains(home_response, f'href="{reverse("suggestion")}"')

        suggestion_response = self.client.get(reverse("suggestion"))
        self.assertContains(suggestion_response, "Sugerir mercado")
        self.assertContains(suggestion_response, f'class="nav-link active" href="{reverse("suggestion")}"')

    def test_database_config_prefers_fastapi_postgres_environment(self):
        with patch.dict(
            os.environ,
            {
                "FASTAPI_POSTGRES_DB": "gotrendlabs_api",
                "FASTAPI_POSTGRES_USER": "gotrendlabs_fastapi",
                "FASTAPI_POSTGRES_PASSWORD": "fastapi-secret",
                "FASTAPI_POSTGRES_HOST": "db.internal",
                "FASTAPI_POSTGRES_PORT": "6543",
            },
            clear=False,
        ):
            self.assertEqual(
                database_config(),
                {
                    "dbname": "gotrendlabs_api",
                    "user": "gotrendlabs_fastapi",
                    "password": "fastapi-secret",
                    "host": "db.internal",
                    "port": "6543",
                },
            )

    def test_admin_ops_does_not_render_local_market_data_when_api_errors(self):
        market = Market.objects.get(slug="openai-gpt6-2026")
        market.view_count = 12
        market.share_count = 3
        market.save(update_fields=["view_count", "share_count"])
        session = self.client.session
        session[TOKEN_KEY] = "admin-token"
        session[USER_KEY] = {"id": 1, "handle": "@admin", "display_name": "Admin", "preferred_language": "pt-br", "is_staff": True}
        session.save()

        with patch("admin_ops.views.admin_get_markets", side_effect=AuthAPIError("offline")):
            response = self.client.get(reverse("admin-ops-markets"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Popularidade")
        self.assertContains(response, "Mais visualizados")
        self.assertContains(response, "Mais compartilhados")
        self.assertContains(response, "offline")
        self.assertNotContains(response, "<small>Views</small><strong>12</strong>", html=True)
        self.assertNotContains(response, "<small>Shares</small><strong>3</strong>", html=True)

        with patch("admin_ops.views.admin_get_market", return_value={
            "slug": market.slug,
            "title": market.title,
            "summary": market.summary,
            "kind": market.kind,
            "status": market.status,
            "status_label": market.status_label,
            "primary_outcome": market.primary_outcome,
            "primary_probability_exact": float(market.primary_probability_exact),
            "secondary_probability_exact": float(market.secondary_probability_exact),
            "volume_gtl": market.volume_gtl,
            "participants": market.participants,
            "category": market.category.name,
            "subcategory": market.subcategory.name,
            "source": market.source,
            "close_label": market.close_label,
            "thumb": market.thumb,
            "thumb_color": market.thumb_color,
            "image_url": market.image_url,
            "resolution_criteria": market.resolution_criteria,
            "admin_notes": market.admin_notes,
            "close_at": market.close_at.isoformat() if market.close_at else None,
            "close_timezone": market.close_timezone,
            "auto_close_enabled": market.auto_close_enabled,
            "is_featured": market.is_featured,
            "view_count": 12,
            "share_count": 3,
            "options": [],
        }), patch("admin_ops.views.admin_get_taxonomy", return_value={"categories": []}):
            response = self.client.get(reverse("admin-ops-market-edit", args=[market.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Popularidade operacional")
        self.assertContains(response, "12 visualizações · 3 compartilhamentos")

    @override_settings(PUBLIC_SHARE_BASE_URL="https://share.gotrendlabs.example")
    def test_share_links_use_configured_public_origin(self):
        market = get_domain_client().market("openai-gpt6-2026")
        resolved_market = {**market, "slug": "resolved-api", "status": "resolved", "title": "Resultado vindo da API", "primary_outcome": "SIM"}
        public_market_url = "https://share.gotrendlabs.example/share/market/openai-gpt6-2026/"
        public_market_image_url = "https://share.gotrendlabs.example/share/market/openai-gpt6-2026/image/"
        public_result_url = "https://share.gotrendlabs.example/share/result/resolved-api/"
        public_result_image_url = "https://share.gotrendlabs.example/share/result/resolved-api/image/"

        with patch("core.views.get_market", return_value=market):
            response = self.client.get(reverse("share-market", args=["openai-gpt6-2026"]))
            self.assertContains(response, public_market_url)
            self.assertContains(response, public_market_image_url)
            self.assertNotContains(response, "Preview social indisponível neste host")
            self.assertContains(response, f"url={quote(public_market_url, safe='')}")
            self.assertContains(response, f"u={quote(public_market_url, safe='')}")
            self.assertContains(response, quote(public_market_url, safe=""))
            self.assertContains(response, "https://wa.me/")
            self.assertContains(response, "https://t.me/share/url")
            self.assertContains(response, "https://x.com/intent/tweet")
            self.assertContains(response, "https://www.facebook.com/sharer/sharer.php")
            self.assertContains(response, "https://www.linkedin.com/sharing/share-offsite/")

        with patch("core.views.get_market", return_value=resolved_market):
            response = self.client.get(reverse("share-result", args=["resolved-api"]))
            self.assertContains(response, public_result_url)
            self.assertContains(response, public_result_image_url)
            self.assertContains(response, f"url={quote(public_result_url, safe='')}")
            self.assertContains(response, f"u={quote(public_result_url, safe='')}")
            self.assertContains(response, quote(public_result_url, safe=""))
            self.assertContains(response, "https://wa.me/")
            self.assertContains(response, "https://t.me/share/url")
            self.assertContains(response, "https://x.com/intent/tweet")
            self.assertContains(response, "https://www.facebook.com/sharer/sharer.php")
            self.assertContains(response, "https://www.linkedin.com/sharing/share-offsite/")

        User = get_user_model()
        user = User.objects.create_user(username="@publicorigin", email="public-origin@example.com", password="testpass123", first_name="Public Origin")
        badge = BadgeDefinition.objects.create(code="origin_founder", name="Membro origem", description="Entrou cedo.")
        UserBadgeAward.objects.create(user=user, badge=badge, awarded_at=timezone.now(), reason_snapshot="Criar conta.")
        token = public_badge_share_token(user.id, "origin_founder")
        public_badge_url = f"https://share.gotrendlabs.example/share/badge/origin_founder/?t={token}"
        public_badge_image_url = f"https://share.gotrendlabs.example/share/badge/origin_founder/image/?t={token}"

        response = self.client.get(f"{reverse('share-badge', args=['origin_founder'])}?t={token}")
        self.assertContains(response, public_badge_url)
        self.assertContains(response, public_badge_image_url)
        self.assertContains(response, f"url={quote(public_badge_url, safe='')}")
        self.assertContains(response, f"u={quote(public_badge_url, safe='')}")
        self.assertContains(response, quote(public_badge_url, safe=""))
        self.assertContains(response, "https://wa.me/")
        self.assertContains(response, "https://t.me/share/url")
        self.assertContains(response, "https://x.com/intent/tweet")
        self.assertContains(response, "https://www.facebook.com/sharer/sharer.php")
        self.assertContains(response, "https://www.linkedin.com/sharing/share-offsite/")
        self.assertNotContains(response, f"u={user.id}")
        self.assertNotContains(response, "public-origin@example.com")


    def test_admin_ops_requires_staff_and_renders_api_data(self):
        admin_routes = [
            reverse("admin-ops-dashboard"),
            reverse("admin-ops-config"),
            reverse("admin-ops-markets"),
            reverse("admin-ops-users"),
            reverse("admin-ops-user-detail", args=[1]),
            reverse("admin-ops-system-logs"),
            reverse("admin-ops-system-log-detail", args=[1]),
            reverse("admin-ops-badges"),
            reverse("admin-ops-badge-new"),
            reverse("admin-ops-badge-edit", args=["founding-member"]),
            reverse("admin-ops-moderation"),
            reverse("admin-ops-resolution"),
            reverse("admin-ops-taxonomy"),
            reverse("admin-ops-market-new"),
            reverse("admin-ops-market-edit", args=["openai-gpt6-2026"]),
            reverse("admin-ops-resolution-action", args=["resolve"]),
            reverse("admin-ops-resolution-action", args=["review"]),
            reverse("admin-ops-resolution-action", args=["request-review"]),
            reverse("admin-ops-queue-action", args=["convert-draft"]),
            reverse("admin-ops-queue-action", args=["reward-feedback"]),
            reverse("admin-ops-queue-action", args=["view-item"]),
            reverse("admin-ops-queue-action", args=["moderate"]),
            reverse("admin-ops-category-action", args=["new"]),
            reverse("admin-ops-category-action", args=["edit"]),
            reverse("admin-ops-category-action", args=["delete"]),
            reverse("admin-ops-category-action", args=["badge-rules"]),
        ]

        for route in admin_routes:
            with self.subTest(route=route, state="guest"):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response["Location"])

        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": 40,
            "handle": "commonuser",
            "email": "common-user@example.com",
            "display_name": "Common User",
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()
        self.assertEqual(self.client.get(reverse("admin-ops-dashboard")).status_code, 403)

        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 41,
            "handle": "staffuser",
            "email": "staff-user@example.com",
            "display_name": "Staff User",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()
        api_market = {**get_domain_client().market("openai-gpt6-2026"), "title": "Mercado admin API", "auto_close_enabled": False, "participants": "3 participantes", "bot_participants": 1}
        market_data = {"markets": [api_market], "counts": {"open": 1, "draft": 0, "locked": 0, "canceled": 0}}
        taxonomy_data = {
            "categories": [
                {
                    "name": "IA",
                    "slug": "ia",
                    "notice": "Aviso geral de IA.",
                    "markets_count": 1,
                    "subcategories": [
                        {
                            "name": "Modelos",
                            "slug": "modelos",
                            "notice": "Aviso de modelos.",
                            "markets_count": 1,
                            "events": [
                                {
                                    "name": "Geral",
                                    "slug": "geral",
                                    "markets_count": 1,
                                    "is_blocked": False,
                                    "notice": "Aviso operacional de IA.",
                                },
                                {
                                    "name": "Sem mercado",
                                    "slug": "sem-mercado",
                                    "markets_count": 0,
                                    "is_blocked": False,
                                    "notice": "",
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        dashboard_summary = {
            "markets": {"total": 1, "open": 1, "draft": 0, "locked": 0, "closing_24h": 0, "total_views": 42, "total_shares": 7},
            "queues": {
                "suggestions_pending": 1,
                "feedback_pending": 2,
                "feedback_high_pending": 1,
                "comments_hidden": 0,
                "action_total": 4,
            },
            "users": {"total": 3, "active": 2, "deactivated": 1, "staff": 1, "superuser": 0, "new_7d": 1},
            "engagement": {
                "predictions_total": 12,
                "predictions_open": 4,
                "predictions_resolved": 7,
                "predictions_canceled": 1,
                "predictions_7d": 5,
                "comments_total": 3,
                "comments_visible": 3,
                "comments_hidden": 0,
            },
            "wallet": {"available_gtl": 2000, "locked_gtl": 50},
            "badges": {"active_catalog": 2, "awarded": 6},
            "system": {
                "logs_error_7d": 1,
                "logs_warning_7d": 2,
                "logs_critical_7d": 0,
                "admin_events_7d": 3,
                "maintenance_enabled": True,
                "smtp_status": "pending",
                "recaptcha_enabled": True,
                "daemon_status": "stale",
                "daemon_status_label": "Atrasado",
                "daemon_locked_markets_24h": 2,
            },
            "top_markets": [
                {
                    "slug": "openai-gpt6-2026",
                    "title": "Mercado admin API",
                    "status": "open",
                    "status_label": "Aberto",
                    "category": "IA",
                    "subcategory": "Modelos",
                    "view_count": 42,
                    "share_count": 7,
                }
            ],
            "recent_admin_events": [
                {
                    "action": "market_publish",
                    "entity_type": "market",
                    "entity_identifier": "openai-gpt6-2026",
                    "note": "Publicado",
                    "created_at": "2026-05-20T00:00:00+00:00",
                    "actor": "staffuser",
                }
            ],
        }

        with (
            patch("admin_ops.views.get_backend_health", return_value={"status": "ok"}) as health_mock,
            patch("admin_ops.views.admin_get_dashboard_summary", return_value=dashboard_summary) as dashboard_mock,
            patch("admin_ops.views.admin_get_markets", return_value=market_data) as markets_mock,
        ):
            response = self.client.get(reverse("admin-ops-dashboard"))
            self.assertContains(response, "Mercado admin API")
            self.assertContains(response, "Ação necessária")
            self.assertContains(response, "Saúde técnica")
            self.assertContains(response, "Backend API")
            self.assertContains(response, "Online")
            self.assertContains(response, "Top mercados")
            self.assertContains(response, "Eventos administrativos recentes")
            self.assertContains(response, "Pendente")
            self.assertContains(response, "Daemon")
            self.assertContains(response, "Atrasado")
            self.assertContains(response, "2 fechamentos 24h")
            self.assertContains(response, reverse("admin-ops-resolution"))
            self.assertContains(response, reverse("admin-ops-users"))
            self.assertNotContains(response, 'class="panel admin-menu"')
            health_mock.assert_called_once_with()
            dashboard_mock.assert_called_once_with("staff-token")
            response = self.client.get(reverse("admin-ops-markets"))
            self.assertContains(response, "Mercado admin API")
            self.assertContains(response, "Participantes")
            self.assertContains(response, "3 participantes")
            self.assertContains(response, "1 bot oficial")
            self.assertContains(response, "Destaque")
            self.assertNotContains(response, 'class="panel admin-menu"')
            self.assertNotContains(response, "Ver público")
            self.assertContains(response, "Gerencie contratos publicados, rascunhos e cancelamentos usados no feed público.")
            self.assertContains(response, "Fechados 0")
            response = self.client.get(f"{reverse('admin-ops-markets')}?q=admin%20api&status=open&order=views_desc")
            self.assertContains(response, "Buscar mercado")
            self.assertContains(response, 'value="admin api"', html=False)
            markets_mock.assert_any_call("staff-token", status="open", q="admin api", order="views_desc")
            response = self.client.get(f"{reverse('admin-ops-markets')}?status=draft")
            self.assertContains(response, "Rascunhos")
            markets_mock.assert_any_call("staff-token", status="draft", q="", order="display")
            response = self.client.get(f"{reverse('admin-ops-markets')}?status=locked")
            self.assertContains(response, "Fechados")
            markets_mock.assert_any_call("staff-token", status="locked", q="", order="display")

        user_data = {
            "users": [
                {
                    "id": 55,
                    "handle": "@operated",
                    "email": "operated@example.com",
                    "display_name": "Operated User",
                    "preferred_language": "pt-br",
                    "account_status": "active",
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "is_bot": True,
                    "created_at": "2026-05-19T00:00:00+00:00",
                    "last_login": "2026-05-19T01:00:00+00:00",
                    "deactivated_at": None,
                    "available_gtl": 2100,
                    "locked_gtl": 50,
                    "reputation_score": 120,
                }
            ],
            "counts": {"total": 1, "active": 1, "deactivated": 0, "staff": 0, "superuser": 0, "bots": 1, "users": 1},
        }
        user_detail = {
            "user": user_data["users"][0],
            "profile": {"bio": "Bio privada", "strong_category": "IA", "birth_date": "1990-01-01", "sex": "other", "is_public": True},
            "wallet": {"available_gtl": 2100, "locked_gtl": 50, "total_earned_gtl": 100},
            "ledger": [{"entry_id": 1, "entry_type": "grant_initial", "amount": 2000, "direction": "credit", "description": "Saldo inicial", "reference_type": "auth_register", "reference_id": "55", "created_at": "2026-05-19T00:00:00+00:00", "created_by": None}],
            "reputation": {"reputation_score": 120, "ranking_position": 3, "resolved_predictions_count": 2, "accuracy_indicator": "50%", "streak": 1, "strong_category": "IA", "last_updated_at": "2026-05-19T00:00:00+00:00"},
            "prediction_counts": {"open": 1},
            "predictions": [{"id": 1, "status": "open", "stake_amount": 50, "won": None, "market_title": "Mercado", "market_slug": "mercado", "option_label": "SIM", "created_at": "2026-05-19T00:00:00+00:00"}],
            "comment_counts": {"visible": 1},
            "comments": [{"id": 1, "status": "visible", "body": "Comentário", "market_title": "Mercado", "market_slug": "mercado", "created_at": "2026-05-19T00:00:00+00:00"}],
            "badges": [{"code": "founding_member", "name": "Membro fundador", "description": "Entrou cedo.", "badge_type": "global", "image_url": "", "image_dark_url": "", "awarded_at": "2026-05-19T00:00:00+00:00", "reason_snapshot": "Cadastro concluído."}],
            "suggestions": [],
            "feedback": [],
            "sessions": [{"id": 1, "created_at": "2026-05-19T00:00:00+00:00", "last_seen_at": None, "expires_at": "2026-06-01T00:00:00+00:00", "revoked_at": None}],
            "auth_events": [{"event_type": "login_success", "email": "operated@example.com", "provider": "", "ip_address": "127.0.0.1", "user_agent": "test", "created_at": "2026-05-19T00:00:00+00:00"}],
            "admin_events": [],
        }
        with patch("admin_ops.views.admin_get_users", return_value=user_data) as users_mock, patch("admin_ops.views.admin_get_user", return_value=user_detail), patch(
            "admin_ops.views.admin_request_user_password_reset",
            return_value={"message": "Se o email existir, enviaremos instruções.", "reset_url": "http://testserver/password-reset/confirm/admin-token/"},
        ) as reset_mock:
            response = self.client.get(reverse("admin-ops-users"))
            self.assertContains(response, "Suporte operacional")
            self.assertContains(response, "Usuários")
            self.assertContains(response, "Operated User")
            self.assertContains(response, "2100 GT₵")
            response = self.client.get(f"{reverse('admin-ops-users')}?q=operated&status=active&role=user&order=wallet_desc")
            self.assertContains(response, "Operated User")
            self.assertContains(response, "Bot")
            users_mock.assert_any_call("staff-token", q="operated", status="active", role="user", bot="", order="wallet_desc")
            response = self.client.get(reverse("admin-ops-user-detail", args=[55]))
            self.assertContains(response, "Conta e perfil")
            self.assertContains(response, "Dados privados")
            self.assertContains(response, "Badges adquiridas")
            self.assertContains(response, "Membro fundador")
            self.assertContains(response, "Ajuste de wallet")
            self.assertContains(response, "Conta controlada por robôs")
            self.assertContains(response, '<option value="" selected>Selecione</option>', html=True)
            self.assertContains(response, "Gerar link de reset")
            self.assertContains(response, "Revogar sessões")
            response = self.client.post(reverse("admin-ops-user-detail", args=[55]), {"action": "password_reset", "note": "Usuário solicitou reset"})
            self.assertContains(response, "Link de reset de senha gerado.")
            self.assertContains(response, "Envie este link ao usuário.")
            self.assertContains(response, "http://testserver/password-reset/confirm/admin-token/")
            reset_mock.assert_called_once_with("staff-token", 55, "Usuário solicitou reset")

        log_payload = {
            "logs": [
                {
                    "id": 10,
                    "created_at": "2026-05-20T00:00:00+00:00",
                    "expires_at": "2026-08-18T00:00:00+00:00",
                    "level": "ERROR",
                    "source": "fastapi",
                    "logger_name": "fastapi.request",
                    "event_type": "request_exception",
                    "message": "Falha simulada",
                    "request_id": "req-admin-log",
                    "method": "GET",
                    "path": "/admin/system-logs",
                    "status_code": 500,
                    "duration_ms": 42,
                    "user_id": 55,
                    "user_identifier": "@operated · Operated User",
                    "ip_address": "127.0.0.1",
                    "user_agent": "test",
                    "exception_type": "RuntimeError",
                    "stack_trace": "RuntimeError: boom",
                    "context": {"headers": {"authorization": "[REDACTED]"}},
                }
            ],
            "counts": {"total": 120, "info": 0, "warning": 0, "error": 1, "critical": 0},
            "page": 1,
            "page_size": 10,
            "total": 120,
        }
        with patch("admin_ops.views.admin_get_system_logs", return_value=log_payload) as logs_mock, patch("admin_ops.views.admin_get_system_log", return_value=log_payload["logs"][0]), patch("admin_ops.views.admin_get_users", return_value=user_data) as log_users_mock:
            response = self.client.get(reverse("admin-ops-system-logs"))
            self.assertContains(response, "Logs do sistema")
            self.assertContains(response, "Troubleshooting")
            self.assertContains(response, '<datalist id="system-log-users">')
            self.assertContains(response, 'value="@operated · Operated User · operated@example.com"')
            self.assertContains(response, "@operated · Operated User")
            self.assertNotContains(response, "Falha simulada")
            self.assertContains(response, "1")
            self.assertContains(response, "de 120 registros filtrados")
            self.assertContains(response, "Carregar mais")
            log_users_mock.assert_any_call("staff-token", order="created_desc")
            log_users_mock.assert_any_call("staff-token", role="staff", order="created_desc")
            log_users_mock.assert_any_call("staff-token", role="superuser", order="created_desc")
            response = self.client.get(f"{reverse('admin-ops-system-logs')}?level=ERROR&source=fastapi&request_id=req-admin-log&user_identifier=%40operated")
            self.assertContains(response, "req-admin-log")
            logs_mock.assert_any_call(
                "staff-token",
                q="",
                level="ERROR",
                source="fastapi",
                logger="",
                event_type="",
                method="",
                path="",
                status_code="",
                user_identifier="@operated",
                request_id="req-admin-log",
                exception_type="",
                **{"from": "", "to": "", "page": "1", "page_size": "10"},
            )
            response = self.client.get(reverse("admin-ops-system-log-detail", args=[10]))
            self.assertContains(response, "Log #10")
            self.assertContains(response, "Evento registrado")
            self.assertContains(response, "@operated · Operated User")
            self.assertContains(response, "RuntimeError")
            self.assertContains(response, "[REDACTED]")

        badge_data = {
            "badges": [
                {
                    "code": "founding-member",
                    "name": "Membro fundador",
                    "description": "Entrou cedo.",
                    "rule_description": "Criar conta.",
                    "badge_type": "global",
                    "image_url": "/media/badge_images/founding.png",
                    "image_dark_url": "",
                    "is_active": True,
                    "rule_type": "founding_member",
                    "threshold_value": 1,
                    "category": "IA",
                    "subcategory": "Modelos",
                    "rule_active": True,
                    "awards_count": 3,
                    "created_at": "2026-05-19T00:00:00+00:00",
                    "updated_at": "2026-05-19T00:00:00+00:00",
                }
            ]
        }
        with patch("admin_ops.views.admin_get_badges", return_value=badge_data), patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data):
            response = self.client.get(reverse("admin-ops-badges"))
            self.assertContains(response, "Membro fundador")
            self.assertContains(response, "badge-browse-thumb")
            self.assertContains(response, "/media/badge_images/founding.png")
            self.assertContains(response, "Criar badge")
            self.assertContains(response, "Categoria")
            self.assertContains(response, "IA / Modelos")
            response = self.client.get(reverse("admin-ops-badge-edit", args=["founding-member"]))
            self.assertContains(response, "Editar badge")
            self.assertContains(response, "Regra automática")
            self.assertContains(response, "Prévia da badge")
            self.assertContains(response, "data-badge-preview")
            self.assertContains(response, "data-preview-badge-name")
            self.assertContains(response, "data-preview-badge-image-light")
            self.assertContains(response, "data-preview-badge-image-dark")
            self.assertContains(response, "Imagem tema claro")
            self.assertContains(response, "Imagem tema escuro")
            self.assertContains(response, "Todas as categorias")
            self.assertContains(response, 'data-category="IA"', html=False)

        locked_market = {
            **api_market,
            "slug": "locked-api",
            "title": "Mercado fechado API",
            "status": "locked",
            "status_label": "Fechado",
            "close_timezone": "America/Sao_Paulo",
            "options": [{**option, "id": index} for index, option in enumerate(api_market["options"], start=1)],
        }
        resolved_market = {
            **api_market,
            "slug": "resolved-api",
            "title": "Mercado resolvido API",
            "status": "resolved",
            "status_label": "Resolvido",
            "resolved_at": "2026-05-18T12:00:00+00:00",
            "resolved_at_label": "18/05/2026 09:00 America/Sao_Paulo",
            "resolution_timezone": "America/Sao_Paulo",
        }

        def resolution_markets(token, **filters):
            if filters.get("status") == "locked":
                return {"markets": [locked_market], "counts": {"locked": 1, "resolved": 1}}
            if filters.get("status") == "resolved":
                return {"markets": [resolved_market], "counts": {"locked": 1, "resolved": 1}}
            return market_data

        with patch("admin_ops.views.admin_get_markets", side_effect=resolution_markets):
            response = self.client.get(reverse("admin-ops-resolution"))
            self.assertContains(response, "Mercado fechado API")
            self.assertContains(response, "Mercado resolvido API")
            self.assertContains(response, "Resolver")
            self.assertContains(response, "Desfazer resolução")
            self.assertContains(response, "Auditoria")
            self.assertContains(response, "Resolução recente")
            self.assertContains(response, "Revise mercados fechados, publique decisões e desfaça resoluções quando houver necessidade operacional.")
            self.assertContains(response, "18/05/2026 09:00 America/Sao_Paulo")
            self.assertContains(response, "Aguardando decisão")

        with patch("admin_ops.views.admin_get_market", return_value=locked_market):
            response = self.client.get(reverse("admin-ops-resolution-market-action", args=["locked-api", "resolve"]))
            self.assertContains(response, '<option value="" selected>Selecione o resultado</option>', html=True)
            self.assertContains(response, 'type="datetime-local"', html=False)
            self.assertContains(response, '<select name="resolution_timezone"', html=False)
            self.assertContains(response, '<option value="America/Sao_Paulo" selected>America/Sao_Paulo</option>', html=False)
            self.assertContains(response, '<span class="required-marker">Obrigatório</span>', html=True, count=5)

        with patch("admin_ops.views.admin_get_market", return_value=locked_market), patch("admin_ops.views.admin_resolve_market", return_value={**locked_market, "status": "resolved", "title": "Mercado fechado API"}) as resolve_mock:
            response = self.client.post(
                reverse("admin-ops-resolution-market-action", args=["locked-api", "resolve"]),
                {
                    "winning_option_id": locked_market["options"][0]["id"],
                    "source_url": "https://fonte.example/resolucao",
                    "note": "Fonte validada.",
                    "resolved_at": "2026-05-18T20:03",
                    "resolution_timezone": "America/Sao_Paulo",
                },
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(resolve_mock.call_args.args[5].strftime("%Y-%m-%dT%H:%M"), "2026-05-18T20:03")
            self.assertEqual(resolve_mock.call_args.args[6], "America/Sao_Paulo")

        audit_payload = {
            "market": {
                "slug": "resolved-api",
                "title": "Mercado resolvido API",
                "status": "resolved",
                "winning_option_label": "SIM",
                "resolved_at_label": "18/05/2026 09:00 America/Sao_Paulo",
                "resolution_timezone": "America/Sao_Paulo",
                "resolution_note": "Resultado confirmado.\nFonte: https://fonte.example",
            },
            "summary": {
                "predictions_total": 2,
                "winners_total": 1,
                "losers_total": 1,
                "stake_total": 200,
                "refund_total": 100,
                "payout_total": 80,
                "loss_total": 100,
                "badge_awards_total": 1,
            },
            "participants": [
                {
                    "user_id": 10,
                    "handle": "@auditwinner",
                    "display_name": "Audit Winner",
                    "prediction_id": 90,
                    "option_label": "SIM",
                    "stake_amount": 100,
                    "probability_at_entry": 55.0,
                    "potential_payout": 180,
                    "won": True,
                    "ledger": {"prediction_refund": 100, "prediction_payout": 80, "prediction_loss": 0},
                    "badges": [{"code": "first_resolution", "name": "Primeira resolução", "awarded_at": "2026-05-18T12:01:00+00:00", "reason_snapshot": "market_resolved:1"}],
                }
            ],
            "pagination": {"limit": 1, "offset": 0, "total": 2},
        }
        with patch("admin_ops.views.admin_get_market", return_value=resolved_market), patch("admin_ops.views.admin_get_market_resolution_audit", return_value=audit_payload) as audit_mock:
            response = self.client.get(f"{reverse('admin-ops-resolution-market-action', args=['resolved-api', 'audit'])}?limit=1&offset=0")
            self.assertContains(response, "Auditoria da resolução")
            self.assertContains(response, "Resultado aplicado")
            self.assertContains(response, "Como ler o ledger")
            self.assertContains(response, "Crédito líquido do vencedor")
            self.assertContains(response, "Liquida o stake de quem errou")
            self.assertContains(response, "SIM")
            self.assertContains(response, "payout 80 GT₵")
            self.assertContains(response, "Primeira resolução")
            self.assertContains(response, "Próxima")
            audit_mock.assert_called_once_with("staff-token", "resolved-api", limit=1, offset=0)

        with patch("admin_ops.views.admin_get_market", return_value=resolved_market), patch("admin_ops.views.admin_get_market_resolution_audit", return_value={**audit_payload, "pagination": {"limit": 10, "offset": 0, "total": 20}}) as audit_mock:
            response = self.client.get(reverse("admin-ops-resolution-market-action", args=["resolved-api", "audit"]))
            self.assertContains(response, "1-10 de 20")
            self.assertContains(response, "?limit=10&offset=10")
            audit_mock.assert_called_once_with("staff-token", "resolved-api", limit=10, offset=0)

        queue_data = {
            "items": [
                {
                    "id": 7,
                    "kind": "suggestion",
                    "title": "Apple app IA",
                    "queue_label": "Mercado",
                    "age_label": "2d",
                    "severity_label": "Média",
                    "owner_label": "Editorial",
                    "status": "pending",
                    "status_label": "Pendente",
                    "author_handle": "@queueuser",
                },
                {
                    "id": 8,
                    "kind": "feedback",
                    "title": "Critério confuso",
                    "queue_label": "Feedback",
                    "age_label": "6h",
                    "severity_label": "Alta",
                    "owner_label": "Operação",
                    "status": "pending",
                    "status_label": "Pendente",
                    "author_id": 40,
                },
            ],
            "counts": {},
        }
        with patch("admin_ops.views.admin_get_queues", return_value=queue_data):
            response = self.client.get(reverse("admin-ops-moderation"))
            self.assertContains(response, "Apple app IA")
            self.assertContains(response, "Critério confuso")
            self.assertContains(response, "Abrir fila")

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data):
            response = self.client.get(reverse("admin-ops-taxonomy"))
            self.assertContains(response, "Categorias e subcategorias")
            self.assertContains(response, "data-taxonomy-browser")
            self.assertContains(response, 'data-taxonomy-category-trigger="ia"')
            self.assertContains(response, "taxonomy-detail-panel")
            self.assertContains(response, "Modelos")
            self.assertContains(response, "Mercados vinculados")
            self.assertContains(response, "Editar categoria")
            self.assertContains(response, "Adicionar subcategoria")
            self.assertContains(response, "Regras de bloqueio")
            self.assertContains(response, "Aviso da categoria")
            self.assertContains(response, "Aviso da subcategoria")
            self.assertContains(response, "Aviso do evento")
            self.assertContains(response, "Aviso geral de IA.")
            self.assertContains(response, "Aviso de modelos.")
            self.assertContains(response, "Aviso operacional de IA.")
            self.assertContains(response, "Bloquear")
            self.assertContains(response, "delete_event")
            self.assertContains(response, "Excluir evento")
            self.assertContains(response, "update_category")
            self.assertContains(response, "update_subcategory")
            self.assertContains(response, "update_event")

        participant_payload = {
            "market": {"slug": "openai-gpt6-2026", "title": "Mercado admin API", "status": "open"},
            "summary": {
                "participants": "1 participante",
                "human_participants": 1,
                "bot_participants": 1,
                "human_volume_gtl": 10,
                "bot_volume_gtl": 25,
                "total_volume_gtl": 35,
                "participants_total": 2,
                "human_predictions": 1,
                "bot_predictions": 1,
            },
            "participants": [
                {
                    "prediction_id": 1,
                    "user_id": 10,
                    "handle": "@human",
                    "display_name": "Humano Admin",
                    "is_bot": False,
                    "badge_label": "",
                    "option_label": "SIM",
                    "stake_amount": 10,
                    "probability_at_entry": 50.0,
                    "potential_payout": 20,
                    "status": "open",
                    "won": None,
                    "created_at": "2026-05-23T12:00:00+00:00",
                },
                {
                    "prediction_id": 2,
                    "user_id": 11,
                    "handle": "@gotrendlabs_ai_liquidity",
                    "display_name": "GoTrendLabs AI Liquidity",
                    "is_bot": True,
                    "badge_label": "IA oficial",
                    "option_label": "NAO",
                    "stake_amount": 25,
                    "probability_at_entry": 50.0,
                    "potential_payout": 50,
                    "status": "open",
                    "won": None,
                    "created_at": "2026-05-23T12:01:00+00:00",
                },
            ],
        }
        with patch("admin_ops.views.admin_get_market", return_value=api_market), patch("admin_ops.views.admin_get_market_participants", return_value=participant_payload), patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data):
            response = self.client.get(reverse("admin-ops-market-edit", args=["openai-gpt6-2026"]))
            self.assertContains(response, "Mercado admin API")
            self.assertContains(response, "Participantes do mercado")
            self.assertContains(response, "Humanos")
            self.assertContains(response, "Bots oficiais")
            self.assertContains(response, "Humano Admin")
            self.assertContains(response, "GoTrendLabs AI Liquidity")
            self.assertContains(response, "IA oficial")
            self.assertContains(response, "data-market-form")
            self.assertContains(response, "data-add-option")
            self.assertContains(response, "data-multiple-options")
            self.assertContains(response, "option-builder-head")
            self.assertContains(response, "Thumbnail do card")
            self.assertContains(response, "Data/hora de fechamento")
            self.assertContains(response, "Fechamento automático pelo daemon")
            self.assertContains(response, "Obrigatório")
            self.assertContains(response, "data-category-select")
            self.assertContains(response, "data-subcategory-select")
            self.assertContains(response, "Mensagem pública de fechamento")
            self.assertContains(response, "Fechar manualmente")
            self.assertContains(response, "Salvar alterações")
            self.assertContains(response, "Guia rápido")
            self.assertContains(response, "Fonte e critério devem permitir auditoria objetiva da resolução.")
            self.assertNotContains(response, "Salvar rascunho")
            self.assertNotContains(response, "Publicar mercado")
            self.assertNotContains(response, "Rótulo curto de prazo")
            self.assertContains(response, "data-market-preview")
            self.assertContains(response, "gotrendlabs.js?v=20260605-email-template-preview")

        posted_market = {
            **api_market,
            "status_label": "Aberto",
            "close_at": "2026-12-31T23:59:00-03:00",
            "close_timezone": "America/Sao_Paulo",
            "image_url": "",
            "primary_outcome": "SIM",
            "primary_probability_exact": 72.0721,
            "secondary_probability_exact": 27.9279,
            "volume_gtl": "910 GT₵",
            "participants": "10 participantes",
            "resolution_type": "manual",
            "resolution_note": "Nota interna preservada",
            "options": [
                {**api_market["options"][0], "id": 11, "probability": 72, "probability_exact": 72.0721},
                {**api_market["options"][1], "id": 12, "probability": 27, "probability_exact": 27.9279},
            ],
        }
        post_payload = {
            "action": "save",
            "title": posted_market["title"],
            "slug": posted_market["slug"],
            "kind": posted_market["kind"],
            "category": posted_market["category"],
            "subcategory": posted_market["subcategory"],
            "summary": posted_market["summary"],
            "close_at": posted_market["close_at"][:16],
            "close_timezone": posted_market["close_timezone"],
            "close_label": posted_market["close_label"],
            "thumb": posted_market["thumb"],
            "thumb_color": posted_market["thumb_color"],
            "image_url": posted_market["image_url"],
            "source": posted_market["source"],
            "resolution_criteria": posted_market["resolution_criteria"],
            "admin_notes": "Salvar como fechamento manual",
        }
        with (
            patch("admin_ops.views.admin_get_market", return_value=posted_market),
            patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data),
            patch("admin_ops.views.admin_update_market", return_value={**posted_market, "auto_close_enabled": False}) as update_market,
        ):
            response = self.client.post(reverse("admin-ops-market-edit", args=["openai-gpt6-2026"]), post_payload)
            self.assertEqual(response.status_code, 302)
            sent_payload = update_market.call_args.args[2]
            self.assertFalse(sent_payload["auto_close_enabled"])
            self.assertEqual(sent_payload["status_label"], "Aberto")
            self.assertEqual(sent_payload["volume_gtl"], "910 GT₵")
            self.assertEqual(sent_payload["participants"], "10 participantes")
            self.assertEqual(sent_payload["primary_probability_exact"], 72.0721)
            self.assertEqual(sent_payload["secondary_probability_exact"], 27.9279)
            self.assertEqual(sent_payload["resolution_note"], "Nota interna preservada")
            self.assertEqual(sent_payload["options"][0]["probability_exact"], 72.0721)

        readonly_market = {**posted_market, "status": "resolved", "status_label": "Resolvido", "resolved_at": "2026-05-18T12:00:00+00:00", "winning_option_id": 11}
        with patch("admin_ops.views.admin_get_market", return_value=readonly_market), patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data):
            response = self.client.get(reverse("admin-ops-market-edit", args=["openai-gpt6-2026"]))
            self.assertContains(response, "Mercado resolvido fica em modo somente leitura. Desfaça a resolução antes de editar.")
            self.assertContains(response, "<fieldset", html=False)
            self.assertContains(response, "disabled", html=False)
            self.assertNotContains(response, "Salvar alterações")
            self.assertNotContains(response, "Cancelar mercado")

    def test_admin_list_pages_use_load_more_blocks_of_ten(self):
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 41,
            "handle": "staffuser",
            "email": "staff-user@example.com",
            "display_name": "Staff User",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()

        users = [
            {
                "id": index,
                "handle": f"@adminuser{index}",
                "email": f"admin-user-{index}@example.com",
                "display_name": f"Admin Usuário {index}",
                "preferred_language": "pt-br",
                "account_status": "active",
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "created_at": "2026-05-20T00:00:00+00:00",
                "last_login": "2026-05-20T00:00:00+00:00",
                "deactivated_at": None,
                "available_gtl": 1000 + index,
                "locked_gtl": 0,
                "reputation_score": index,
            }
            for index in range(1, 13)
        ]
        with patch("admin_ops.views.admin_get_users", return_value={"users": users, "counts": {"total": 12}}):
            first_page = self.client.get(reverse("admin-ops-users"))
            self.assertContains(first_page, "mostrando 10 de 12")
            self.assertContains(first_page, "Carregar mais")
            self.assertNotContains(first_page, "Admin Usuário 11")
            second_page = self.client.get(f"{reverse('admin-ops-users')}?limit=20")
            self.assertContains(second_page, "mostrando 12 de 12")
            self.assertContains(second_page, "Admin Usuário 11")
            self.assertNotContains(second_page, "Carregar mais")

        markets = [
            {
                "slug": f"admin-market-{index}",
                "title": f"Mercado Admin {index}",
                "status": "open",
                "status_label": "Aberto",
                "is_featured": False,
                "kind": "binary",
                "category": "IA",
                "subcategory": "Modelos",
                "view_count": index,
                "share_count": index,
            }
            for index in range(1, 13)
        ]
        with patch("admin_ops.views.admin_get_markets", return_value={"markets": markets, "counts": {"open": 12}}):
            first_page = self.client.get(reverse("admin-ops-markets"))
            self.assertContains(first_page, "mostrando 10 de 12")
            self.assertContains(first_page, "Carregar mais")
            self.assertNotContains(first_page, "Mercado Admin 11")
            second_page = self.client.get(f"{reverse('admin-ops-markets')}?limit=20")
            self.assertContains(second_page, "mostrando 12 de 12")
            self.assertContains(second_page, "Mercado Admin 11")
            self.assertNotContains(second_page, "Carregar mais")

        resolution_markets = [
            {
                **markets[index - 1],
                "slug": f"locked-market-{index}",
                "title": f"Resolução Admin {index}",
                "status": "locked",
                "status_label": "Fechado",
                "resolved_at": None,
                "resolution_timezone": "America/Sao_Paulo",
                "participants": f"{index} participantes",
                "volume_gtl": f"{index * 10} GT₵",
            }
            for index in range(1, 13)
        ]

        def resolution_markets_payload(token, status="", order="resolution_desc"):
            if status == "locked":
                return {"markets": resolution_markets, "counts": {"locked": 12}}
            return {"markets": [], "counts": {"resolved": 0}}

        with patch("admin_ops.views.admin_get_markets", side_effect=resolution_markets_payload):
            first_page = self.client.get(reverse("admin-ops-resolution"))
            self.assertContains(first_page, "mostrando 10 de 12")
            self.assertContains(first_page, "Carregar mais")
            self.assertNotContains(first_page, "Resolução Admin 11")
            second_page = self.client.get(f"{reverse('admin-ops-resolution')}?limit=20")
            self.assertContains(second_page, "mostrando 12 de 12")
            self.assertContains(second_page, "Resolução Admin 11")
            self.assertNotContains(second_page, "Carregar mais")

        queue_items = [
            {
                "id": index,
                "kind": "suggestion",
                "title": f"Fila Admin {index}",
                "queue_label": "Mercado",
                "item_type": "Sugestão",
                "created_at": f"2026-05-20T{index:02d}:00:00+00:00",
                "created_at_label": f"20/05/2026 {index:02d}:00",
                "severity_label": "Média",
                "status": "pending",
                "status_label": "Pendente",
            }
            for index in range(1, 13)
        ]
        with patch("admin_ops.views.admin_get_queues", return_value={"items": queue_items, "counts": {}}), patch("admin_ops.views.admin_get_comments", return_value={"comments": []}):
            first_page = self.client.get(f"{reverse('admin-ops-moderation')}?order=created_asc")
            self.assertContains(first_page, "mostrando 10 de 12")
            self.assertContains(first_page, "Carregar mais")
            self.assertNotContains(first_page, "Fila Admin 11")
            second_page = self.client.get(f"{reverse('admin-ops-moderation')}?order=created_asc&limit=20")
            self.assertContains(second_page, "mostrando 12 de 12")
            self.assertContains(second_page, "Fila Admin 11")
            self.assertNotContains(second_page, "Carregar mais")

        logs = [
            {
                "id": index,
                "created_at": f"2026-05-20T{index:02d}:00:00+00:00",
                "expires_at": "2026-08-18T00:00:00+00:00",
                "level": "INFO",
                "source": "django",
                "logger_name": "django.request",
                "event_type": "request",
                "message": f"Log Admin {index}",
                "request_id": f"req-admin-{index}",
                "method": "GET",
                "path": "/admin-ops/logs/",
                "status_code": 200,
                "duration_ms": 10,
                "user_id": 41,
                "user_identifier": "@staffuser",
                "ip_address": "127.0.0.1",
                "user_agent": "test",
                "exception_type": "",
                "stack_trace": "",
                "context": {},
            }
            for index in range(1, 13)
        ]

        def logs_payload(token, **filters):
            page_size = int(filters.get("page_size") or 10)
            return {"logs": logs[:page_size], "counts": {"total": 12}, "page": 1, "page_size": page_size, "total": 12}

        with patch("admin_ops.views.admin_get_system_logs", side_effect=logs_payload), patch("admin_ops.views.admin_get_users", return_value={"users": []}):
            first_page = self.client.get(reverse("admin-ops-system-logs"))
            self.assertContains(first_page, "10")
            self.assertContains(first_page, "de 12 registros filtrados")
            self.assertContains(first_page, "Carregar mais")
            self.assertNotContains(first_page, "req-admin-11")
            second_page = self.client.get(f"{reverse('admin-ops-system-logs')}?limit=20")
            self.assertContains(second_page, "12")
            self.assertContains(second_page, "de 12 registros filtrados")
            self.assertContains(second_page, "req-admin-11")
            self.assertNotContains(second_page, "Carregar mais")

    def test_admin_markets_shows_api_error_without_local_fallback(self):
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 41,
            "handle": "staffuser",
            "email": "staff-user@example.com",
            "display_name": "Staff User",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()

        with patch("admin_ops.views.admin_get_markets", side_effect=AuthAPIError("Serviço da API retornou erro interno.", 500)):
            response = self.client.get(reverse("admin-ops-markets"))

        self.assertNotContains(response, "OpenAI anuncia GPT-6")
        self.assertContains(response, "Serviço da API retornou erro interno.")

    def test_admin_dashboard_backend_health_offline_does_not_block_summary(self):
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 41,
            "handle": "staffuser",
            "email": "staff-user@example.com",
            "display_name": "Staff User",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()
        dashboard_summary = {
            "markets": {},
            "queues": {},
            "users": {},
            "engagement": {},
            "wallet": {},
            "badges": {},
            "system": {},
            "top_markets": [],
            "recent_admin_events": [],
        }

        with (
            patch("admin_ops.views.get_backend_health", side_effect=AuthAPIError("Health indisponível.", None)),
            patch("admin_ops.views.admin_get_dashboard_summary", return_value=dashboard_summary),
        ):
            response = self.client.get(reverse("admin-ops-dashboard"))

        self.assertContains(response, "Backend API")
        self.assertContains(response, "Offline")
        self.assertContains(response, "Health indisponível.")
        self.assertNotContains(response, "Resumo operacional indisponível")

    def test_public_suggestion_and_feedback_post_to_api_client(self):
        session = self.client.session
        session[TOKEN_KEY] = "user-token"
        session[USER_KEY] = {
            "id": 50,
            "handle": "@queueuser",
            "email": "queue-user@example.com",
            "display_name": "Queue User",
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()

        with patch("core.views.create_suggestion", return_value={"id": 1}) as create_suggestion:
            response = self.client.post(
                reverse("suggestion"),
                {
                    "question": "A Apple lançará app IA?",
                    "category": "IA",
                    "kind": "binary",
                    "suggested_source": "Apple Newsroom",
                    "rationale": "Fonte pública.",
                },
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], reverse("home"))
            create_suggestion.assert_called_once()

        with patch("core.views.create_feedback", return_value={"id": 2}) as create_feedback:
            response = self.client.post(
                reverse("feedback"),
                {
                    "feedback_type": "Mercado ambíguo",
                    "severity": "medium",
                    "description": "Critério confuso.",
                },
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], reverse("home"))
            create_feedback.assert_called_once()

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SITE_KEY="site-key")
    def test_recaptcha_widget_renders_for_register_and_guest_forms(self):
        register_response = self.client.get(reverse("register"))
        self.assertContains(register_response, "https://www.google.com/recaptcha/api.js")
        self.assertContains(register_response, 'class="g-recaptcha"')
        self.assertContains(register_response, 'data-sitekey="site-key"')

        suggestion_response = self.client.get(reverse("suggestion"))
        self.assertContains(suggestion_response, 'class="g-recaptcha"')
        self.assertContains(suggestion_response, 'data-sitekey="site-key"')

        feedback_response = self.client.get(reverse("feedback"))
        self.assertContains(feedback_response, 'class="g-recaptcha"')
        self.assertContains(feedback_response, 'data-sitekey="site-key"')

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SITE_KEY="site-key")
    def test_recaptcha_widget_is_hidden_for_authenticated_queue_forms(self):
        session = self.client.session
        session[TOKEN_KEY] = "user-token"
        session[USER_KEY] = {
            "id": 51,
            "handle": "@queueuser",
            "email": "queue-user@example.com",
            "display_name": "Queue User",
            "preferred_language": "pt-br",
            "is_staff": False,
        }
        session.save()

        self.assertNotContains(self.client.get(reverse("suggestion")), 'class="g-recaptcha"')
        self.assertNotContains(self.client.get(reverse("feedback")), 'class="g-recaptcha"')

    def test_admin_taxonomy_inline_crud_posts_to_api_client(self):
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 42,
            "handle": "taxonomyadmin",
            "email": "taxonomy-admin@example.com",
            "display_name": "Taxonomy Admin",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()
        taxonomy_data = {
            "categories": [
                {
                    "name": "IA",
                    "slug": "ia",
                    "notice": "",
                    "markets_count": 1,
                    "subcategories": [
                        {
                            "name": "Modelos",
                            "slug": "modelos",
                            "notice": "",
                            "markets_count": 1,
                            "events": [
                                {
                                    "name": "Geral",
                                    "slug": "geral",
                                    "markets_count": 1,
                                    "is_blocked": False,
                                    "notice": "",
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_create_category", return_value=taxonomy_data) as create_category:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {"action": "create_category", "name": "Ciência", "slug": "ciencia", "notice": "Aviso de ciência"},
            )
            self.assertEqual(response.status_code, 200)
            create_category.assert_called_once_with("staff-token", {"name": "Ciência", "slug": "ciencia", "notice": "Aviso de ciência"})

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_update_category", return_value=taxonomy_data) as update_category:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {
                    "action": "update_category",
                    "category_slug": "ia",
                    "name": "Inteligência Artificial",
                    "slug": "ia",
                    "notice": "Aviso atualizado de IA",
                },
            )
            self.assertEqual(response.status_code, 200)
            update_category.assert_called_once_with(
                "staff-token",
                "ia",
                {"name": "Inteligência Artificial", "slug": "ia", "notice": "Aviso atualizado de IA"},
            )

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_create_subcategory", return_value=taxonomy_data) as create_subcategory:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {
                    "action": "create_subcategory",
                    "category_slug": "ia",
                    "name": "Agentes",
                    "slug": "agentes",
                    "notice": "Aviso de agentes",
                },
            )
            self.assertEqual(response.status_code, 200)
            create_subcategory.assert_called_once_with("staff-token", "ia", {"name": "Agentes", "slug": "agentes", "notice": "Aviso de agentes"})

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_update_subcategory", return_value=taxonomy_data) as update_subcategory:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {
                    "action": "update_subcategory",
                    "category_slug": "ia",
                    "subcategory_slug": "modelos",
                    "name": "Modelos fundacionais",
                    "slug": "modelos-fundacionais",
                    "notice": "Aviso atualizado de modelos",
                },
            )
            self.assertEqual(response.status_code, 200)
            update_subcategory.assert_called_once_with(
                "staff-token",
                "ia",
                "modelos",
                {"name": "Modelos fundacionais", "slug": "modelos-fundacionais", "notice": "Aviso atualizado de modelos"},
            )

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_block_category", return_value=taxonomy_data) as block_category:
            response = self.client.post(reverse("admin-ops-taxonomy"), {"action": "block_category", "category_slug": "ia", "block_note": "Congelar uso"})
            self.assertEqual(response.status_code, 200)
            block_category.assert_called_once_with("staff-token", "ia", "Congelar uso")

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_unblock_category", return_value=taxonomy_data) as unblock_category:
            response = self.client.post(reverse("admin-ops-taxonomy"), {"action": "unblock_category", "category_slug": "ia", "block_note": "Reativar uso"})
            self.assertEqual(response.status_code, 200)
            unblock_category.assert_called_once_with("staff-token", "ia", "Reativar uso")

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_block_subcategory", return_value=taxonomy_data) as block_subcategory:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {"action": "block_subcategory", "category_slug": "ia", "subcategory_slug": "modelos", "block_note": "Bloquear sub"},
            )
            self.assertEqual(response.status_code, 200)
            block_subcategory.assert_called_once_with("staff-token", "ia", "modelos", "Bloquear sub")

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_unblock_subcategory", return_value=taxonomy_data) as unblock_subcategory:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {"action": "unblock_subcategory", "category_slug": "ia", "subcategory_slug": "modelos", "block_note": "Desbloquear sub"},
            )
            self.assertEqual(response.status_code, 200)
            unblock_subcategory.assert_called_once_with("staff-token", "ia", "modelos", "Desbloquear sub")

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_create_event", return_value=taxonomy_data) as create_event:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {
                    "action": "create_event",
                    "category_slug": "ia",
                    "subcategory_slug": "modelos",
                    "name": "GPT-6",
                    "slug": "gpt-6",
                    "notice": "Aviso do GPT-6",
                },
            )
            self.assertEqual(response.status_code, 200)
            create_event.assert_called_once_with("staff-token", "ia", "modelos", {"name": "GPT-6", "slug": "gpt-6", "notice": "Aviso do GPT-6"})

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_update_event", return_value=taxonomy_data) as update_event:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {
                    "action": "update_event",
                    "category_slug": "ia",
                    "subcategory_slug": "modelos",
                    "event_slug": "geral",
                    "name": "Geral IA",
                    "slug": "geral-ia",
                    "notice": "Aviso atualizado",
                },
            )
            self.assertEqual(response.status_code, 200)
            update_event.assert_called_once_with(
                "staff-token",
                "ia",
                "modelos",
                "geral",
                {"name": "Geral IA", "slug": "geral-ia", "notice": "Aviso atualizado"},
            )

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_block_event", return_value=taxonomy_data) as block_event:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {"action": "block_event", "category_slug": "ia", "subcategory_slug": "modelos", "event_slug": "geral", "block_note": "Bloquear evento"},
            )
            self.assertEqual(response.status_code, 200)
            block_event.assert_called_once_with("staff-token", "ia", "modelos", "geral", "Bloquear evento")

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_unblock_event", return_value=taxonomy_data) as unblock_event:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {"action": "unblock_event", "category_slug": "ia", "subcategory_slug": "modelos", "event_slug": "geral", "block_note": "Desbloquear evento"},
            )
            self.assertEqual(response.status_code, 200)
            unblock_event.assert_called_once_with("staff-token", "ia", "modelos", "geral", "Desbloquear evento")

        with patch("admin_ops.views.admin_get_taxonomy", return_value=taxonomy_data), patch("admin_ops.views.admin_delete_event", return_value=taxonomy_data) as delete_event:
            response = self.client.post(
                reverse("admin-ops-taxonomy"),
                {"action": "delete_event", "category_slug": "ia", "subcategory_slug": "modelos", "event_slug": "geral"},
            )
            self.assertEqual(response.status_code, 200)
            delete_event.assert_called_once_with("staff-token", "ia", "modelos", "geral")

    def test_admin_comment_moderation_uses_api_client(self):
        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 42,
            "handle": "commentadmin",
            "email": "comment-admin@example.com",
            "display_name": "Comment Admin",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()
        comment_payload = {
            "id": 77,
            "market_slug": "openai-gpt6-2026",
            "author_id": 50,
            "author_handle": "@commentuser",
            "author_display_name": "Comment User",
            "body": "Comentário para moderação.",
            "status": "visible",
            "like_count": 0,
            "dislike_count": 0,
            "viewer_reaction": None,
            "moderation_note": "",
            "created_at": "2026-05-18T12:00:00+00:00",
        }

        with patch("admin_ops.views.admin_get_comments", return_value={"comments": [comment_payload]}):
            response = self.client.get(reverse("admin-ops-moderation") + "?kind=comment")
            self.assertContains(response, "Comentário para moderação.")
            self.assertContains(response, "Comentários")

        with patch("admin_ops.views.admin_get_comments", return_value={"comments": [comment_payload]}), patch("admin_ops.views.admin_moderate_comment", return_value={**comment_payload, "status": "hidden"}) as moderate:
            response = self.client.post(
                reverse("admin-ops-queue-item-action", args=["comment", 77, "review"]),
                {"status": "hidden", "note": "Ocultar."},
            )
            self.assertEqual(response.status_code, 302)
            moderate.assert_called_once_with("staff-token", 77, "hidden", "Ocultar.")

    def test_wallet_recharge_web_flow_uses_api_and_admin_queue(self):
        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": 91,
            "handle": "@rechargeuser",
            "email": "recharge-user@example.com",
            "display_name": "Recharge User",
            "preferred_language": "pt-br",
        }
        session.save()
        ledger_payload = {"wallet": {"available_gtl": 0, "locked_gtl": 0, "total_earned_gtl": 0}, "entries": []}
        recharge_requests = {
            "requests": [
                {
                    "id": 12,
                    "status": "pending",
                    "status_label": "Pendente",
                    "amount_gtl": None,
                    "created_at": "2026-05-20T12:00:00+00:00",
                    "created_at_label": "20/05/2026 12:00",
                    "reviewed_at": None,
                }
            ]
        }

        with patch("wallet.views.get_ledger", return_value=ledger_payload), patch("wallet.views.get_me", return_value={"reputation": {}}), patch(
            "wallet.views.get_wallet_recharge_requests", return_value=recharge_requests
        ):
            response = self.client.get(reverse("wallet"))
            self.assertContains(response, "Em análise")
            self.assertContains(response, "Histórico")
            self.assertContains(response, "últimas 3")

        with patch("wallet.views.create_wallet_recharge_request", return_value={"id": 13}) as create_recharge:
            response = self.client.post(reverse("wallet-recharge-request"))
            self.assertEqual(response.status_code, 302)
            create_recharge.assert_called_once_with("api-token")

        session = self.client.session
        session[TOKEN_KEY] = "staff-token"
        session[USER_KEY] = {
            "id": 92,
            "handle": "rechargeadmin",
            "email": "recharge-admin@example.com",
            "display_name": "Recharge Admin",
            "preferred_language": "pt-br",
            "is_staff": True,
        }
        session.save()
        queue_item = {
            "id": 12,
            "kind": "wallet_recharge",
            "title": "Solicitação de recarga educativa",
            "queue_label": "Recarga",
            "item_type": "Recarga educativa",
            "status": "pending",
            "status_label": "Pendente",
            "severity_label": "Média",
            "author_handle": "@rechargeuser",
            "author_id": 91,
            "created_at": "2026-05-20T12:00:00+00:00",
            "created_at_label": "20/05/2026 12:00",
            "description": "Pedido de crédito educativo.",
            "admin_note": "",
            "reward_gtl": None,
        }
        with patch("admin_ops.views.admin_get_queues", return_value={"items": [queue_item], "counts": {"wallet_recharge": {"pending": 1}}}):
            response = self.client.get(reverse("admin-ops-moderation") + "?kind=wallet_recharge")
            self.assertContains(response, "Recarga")
            self.assertContains(response, "Solicitação de recarga educativa")

        with patch("admin_ops.views.admin_get_queues", return_value={"items": [queue_item], "counts": {"wallet_recharge": {"pending": 1}}}), patch(
            "admin_ops.views.admin_approve_wallet_recharge", return_value={**queue_item, "status": "approved", "reward_gtl": 300}
        ) as approve:
            response = self.client.post(
                reverse("admin-ops-queue-item-action", args=["wallet_recharge", 12, "review"]),
                {"operation": "approve-recharge", "amount_gtl": 300, "note": "Recarga aprovada."},
            )
            self.assertEqual(response.status_code, 302)
            approve.assert_called_once_with("staff-token", 12, 300, "Recarga aprovada.")

        with patch("admin_ops.views.admin_get_queues", return_value={"items": [queue_item], "counts": {"wallet_recharge": {"pending": 1}}}), patch(
            "admin_ops.views.admin_reject_wallet_recharge", return_value={**queue_item, "status": "rejected"}
        ) as reject:
            response = self.client.post(
                reverse("admin-ops-queue-item-action", args=["wallet_recharge", 12, "review"]),
                {"operation": "reject-recharge", "note": "Aguardar nova tentativa."},
            )
            self.assertEqual(response.status_code, 302)
            reject.assert_called_once_with("staff-token", 12, "Aguardar nova tentativa.")

    def test_wallet_ledger_and_recharge_history_use_load_more(self):
        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": 93,
            "handle": "@walletpages",
            "email": "wallet-pages@example.com",
            "display_name": "Wallet Pages",
            "preferred_language": "pt-br",
        }
        session.save()
        ledger_entries = [
            {
                "entry_id": index,
                "entry_type": "manual_adjustment",
                "amount": index,
                "direction": "credit",
                "description": f"Movimentação {index}",
                "reference_type": "test",
                "reference_id": str(index),
                "created_at": f"2026-05-{index:02d}T12:00:00+00:00",
                "created_by": None,
            }
            for index in range(1, 13)
        ]
        ledger_payload = {"wallet": {"available_gtl": 1200, "locked_gtl": 0, "total_earned_gtl": 0}, "entries": ledger_entries}
        recharge_payload = {
            "requests": [
                {
                    "id": index,
                    "status": "approved",
                    "status_label": f"Status {index}",
                    "amount_gtl": index * 10,
                    "created_at": f"2026-05-{index:02d}T12:00:00+00:00",
                    "created_at_label": f"20/05/2026 1{index}:00",
                    "reviewed_at": None,
                }
                for index in range(1, 5)
            ]
        }

        with patch("wallet.views.get_ledger", return_value=ledger_payload), patch("wallet.views.get_me", return_value={"reputation": {}}), patch(
            "wallet.views.get_wallet_recharge_requests", return_value=recharge_payload
        ):
            first_page = self.client.get(reverse("wallet"))
            self.assertContains(first_page, "Movimentação 1")
            self.assertContains(first_page, "Movimentação 10")
            self.assertNotContains(first_page, "Movimentação 11")
            self.assertContains(first_page, "mostrando 10 de 12")
            self.assertContains(first_page, "Carregar mais")
            self.assertContains(first_page, "?ledger_limit=20")
            self.assertContains(first_page, "Status 1")
            self.assertContains(first_page, "Status 3")
            self.assertNotContains(first_page, "Status 4")

            second_page = self.client.get(f"{reverse('wallet')}?ledger_limit=20")
            self.assertContains(second_page, "Movimentação 9")
            self.assertContains(second_page, "Movimentação 11")
            self.assertContains(second_page, "Movimentação 12")
            self.assertContains(second_page, "mostrando 12 de 12")
            self.assertNotContains(second_page, "Carregar mais")

    def test_login_page_has_focused_auth_layout(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, "Acessar conta")
        self.assertContains(response, "Google")
        self.assertContains(response, "Facebook")
        self.assertContains(response, "Entrar com X")
        self.assertNotContains(response, "will@example.com")
        self.assertNotContains(response, "2FA")
        self.assertNotContains(response, "Continuar com Apple")

    def test_private_pages_redirect_guest_and_render_for_user(self):
        private_routes = [reverse("wallet"), reverse("profile")]
        for route in private_routes:
            with self.subTest(route=route, state="guest"):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response["Location"])

        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": 1,
            "handle": "willcosta",
            "email": "will@gotrendlabs.com.br",
            "display_name": "Will Costa",
            "preferred_language": "pt-br",
        }
        session.save()

        for route in private_routes:
            with self.subTest(route=route, state="authenticated"):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)

    def test_ranking_page_shows_error_without_local_fallback_when_api_fails(self):
        User = get_user_model()
        user = User.objects.create_user(username="@localtheme", email="local-theme@example.com", password="pass", first_name="Local Theme")
        UserReputation.objects.create(user=user, reputation_score=100, accuracy_indicator="0%")

        with patch("profiles.views.get_rankings", side_effect=AuthAPIError("off")):
            response = self.client.get(f"{reverse('rankings')}?category=ia&subcategory=modelos")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "off")
            self.assertNotContains(response, "@localtheme")
            self.assertContains(response, "Ainda não há previsões resolvidas para este recorte.")

    def test_ranking_page_uses_api_payload_as_authoritative(self):
        payload = {
            "rows": [
                {"position": 1, "user_id": 10, "handle": "@apirow", "display_name": "API Row", "reputation_score": 120, "accuracy_indicator": "50%", "strong_category": "Geral"},
            ],
            "categories": [{"name": "IA", "slug": "ia", "subcategories": [{"name": "Modelos", "slug": "modelos"}]}],
            "selected_category": "ia",
            "selected_subcategory": "modelos",
        }

        with patch("profiles.views.get_rankings", return_value=payload):
            response = self.client.get(f"{reverse('rankings')}?category=ia&subcategory=modelos")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "@apirow")
            self.assertContains(response, "IA")
            self.assertContains(response, "Modelos")
            self.assertContains(response, "ranking-event")

    def test_ranking_page_renders_badges_from_api_payload(self):
        payload = {
            "rows": [
                {
                    "position": 1,
                    "user_id": 10,
                    "handle": "@badgerow",
                    "display_name": "Badge Row",
                    "reputation_score": 140,
                    "accuracy_indicator": "80%",
                    "strong_category": "Geral",
                    "badges_total": 5,
                    "badges": [
                        {"code": "first", "name": "Primeira", "image_url": "/media/badge_images/first.png", "image_dark_url": "/media/badge_images/first-dark.png", "badge_type": "global", "awarded_at": "2026-05-19T00:00:00+00:00"},
                        {"code": "second", "name": "Segunda", "image_url": "/media/badge_images/second.png", "image_dark_url": "", "badge_type": "performance", "awarded_at": "2026-05-18T00:00:00+00:00"},
                        {"code": "third", "name": "Terceira", "image_url": "", "image_dark_url": "", "badge_type": "engagement", "awarded_at": "2026-05-17T00:00:00+00:00"},
                    ],
                },
            ],
            "categories": [],
            "selected_category": "",
            "selected_subcategory": "",
        }

        with patch("profiles.views.get_rankings", return_value=payload):
            response = self.client.get(reverse("rankings"))
            self.assertContains(response, "@badgerow")
            self.assertContains(response, 'class="ranking-user-badges"')
            self.assertContains(response, "/media/badge_images/first.png")
            self.assertContains(response, "/media/badge_images/first-dark.png")
            self.assertContains(response, "Terceira")
            self.assertContains(response, "+2")
            content = response.content.decode()
            self.assertLess(content.index("@badgerow"), content.index('class="ranking-user-badges"'))

    def test_ranking_page_uses_load_more_rows_by_ten(self):
        payload = {
            "rows": [
                {
                    "position": index,
                    "user_id": index,
                    "handle": f"@rank{index}",
                    "display_name": f"Rank {index}",
                    "reputation_score": 200 - index,
                    "accuracy_indicator": "50%",
                    "strong_category": "Geral",
                }
                for index in range(1, 13)
            ],
            "categories": [{"name": "IA", "slug": "ia", "subcategories": [{"name": "Modelos", "slug": "modelos", "events": [{"name": "Geral", "slug": "geral"}]}]}],
            "selected_category": "ia",
            "selected_subcategory": "modelos",
            "selected_event": "geral",
        }

        with patch("profiles.views.get_rankings", return_value=payload):
            first_page = self.client.get(f"{reverse('rankings')}?category=ia&subcategory=modelos&event=geral")
            self.assertContains(first_page, "@rank1")
            self.assertContains(first_page, "@rank10")
            self.assertNotContains(first_page, "@rank11")
            self.assertContains(first_page, "mostrando 10 de 12")
            self.assertContains(first_page, "Carregar mais")
            self.assertContains(first_page, "category=ia&subcategory=modelos&event=geral&limit=20")

            second_page = self.client.get(f"{reverse('rankings')}?category=ia&subcategory=modelos&event=geral&limit=20")
            self.assertContains(second_page, "@rank10")
            self.assertContains(second_page, "@rank11")
            self.assertContains(second_page, "@rank12")
            self.assertContains(second_page, "mostrando 12 de 12")
            self.assertNotContains(second_page, "Carregar mais")

    def test_profile_wallet_and_ranking_render_api_data(self):
        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": 20,
            "handle": "@apiviewer",
            "email": "api-viewer@example.com",
            "display_name": "API Viewer",
            "preferred_language": "pt-br",
        }
        session.save()

        profile_payload = {
            "user": session[USER_KEY],
            "profile_id": 12,
            "bio": "",
            "strong_category": "Geral",
            "birth_date": "1992-08-11",
            "sex": "female",
            "profile_created_at": "2026-05-17T00:00:00+00:00",
            "profile_updated_at": "2026-05-19T00:00:00+00:00",
            "is_public": True,
            "reputation": {
                "reputation_score": 100,
                "ranking_position": 1,
                "resolved_predictions_count": 0,
                "accuracy_indicator": "0%",
                "streak": 0,
                "strong_category": "",
                "last_updated_at": "2026-05-17T00:00:00+00:00",
            },
        }
        ledger_payload = {
            "wallet": {"available_gtl": 2000, "locked_gtl": 0, "total_earned_gtl": 0},
            "entries": [
                {
                    "entry_id": 1,
                    "entry_type": "grant_initial",
                    "amount": 2000,
                    "direction": "credit",
                    "description": "Saldo inicial do GoTrendLabs",
                    "reference_type": "auth_register",
                    "reference_id": "20",
                    "created_at": "2026-05-17T00:00:00+00:00",
                    "created_by": None,
                }
            ],
        }

        with patch("profiles.views.get_me", return_value=profile_payload), patch("profiles.views.get_badges", return_value=[]), patch("profiles.views.get_activity", return_value=[]):
            response = self.client.get(reverse("profile"))
            self.assertContains(response, "@apiviewer")
            self.assertContains(response, "#1")
            self.assertContains(response, "Editar dados")
            self.assertContains(response, "api-viewer@example.com")
            self.assertContains(response, "Data de nascimento")
            self.assertContains(response, 'value="1992-08-11"')
            self.assertContains(response, "Sexo")
            self.assertContains(response, "Confirma a exclusão da minha conta")
            self.assertNotContains(response, "Ver ranking")
            self.assertNotContains(response, "Confirmo a exclusão lógica da minha conta")
            self.assertNotContains(response, "Identidade")

        profile_badges = [
            {
                "code": "founding_member",
                "name": "Membro fundador",
                "description": "Entrou cedo.",
                "rule_description": "Criar conta.",
                "image_url": "/media/badge_images/founding.png",
                "image_dark_url": "/media/badge_images/founding-dark.png",
                "status": "earned",
            },
            {
                "code": "top_10",
                "name": "Top 10",
                "description": "Entrou no ranking.",
                "rule_description": "Alcance o top 10.",
                "status": "locked",
            },
        ]
        with patch("profiles.views.get_me", return_value=profile_payload), patch("profiles.views.get_badges", return_value=profile_badges), patch("profiles.views.get_activity", return_value=[]):
            response = self.client.get(reverse("profile"))
            badge_grid = response.content.decode().split('<div class="badge-grid badge-grid-profile">', 1)[1].split("</div>\n  </section>", 1)[0]
            self.assertContains(response, "badge-card earned")
            self.assertContains(response, "badge-card locked")
            self.assertContains(response, "Conquistada")
            self.assertContains(response, "Bloqueada")
            self.assertContains(response, reverse("share-badge", args=["founding_member"]))
            self.assertNotIn(reverse("share-result", args=["tiktok-resolvido-2026"]), badge_grid)
            self.assertNotContains(response, "<h4>Conta</h4>", html=True)
            self.assertNotContains(response, "ID do perfil")
            self.assertNotContains(response, "Previsões resolvidas")

        with patch(
            "wallet.views.get_me",
            return_value={**profile_payload, "reputation": {**profile_payload["reputation"], "reputation_score": 117}},
        ), patch("wallet.views.get_ledger", return_value=ledger_payload), patch("wallet.views.get_wallet_recharge_requests", return_value={"requests": []}):
            response = self.client.get(reverse("wallet"))
            self.assertContains(response, "2000 GT₵")
            self.assertContains(response, "117")
            self.assertContains(response, "grant_initial")

        with patch(
            "profiles.views.get_rankings",
            return_value={
                "rows": [
                    {
                        "position": 1,
                        "user_id": 20,
                        "handle": "@apiviewer",
                        "display_name": "API Viewer",
                        "reputation_score": 100,
                        "accuracy_indicator": "0%",
                        "strong_category": "Geral",
                    }
                ],
                "categories": [{"name": "IA", "slug": "ia", "subcategories": [{"name": "Modelos", "slug": "modelos", "events": [{"name": "Geral", "slug": "geral"}]}]}],
                "selected_category": "ia",
                "selected_subcategory": "modelos",
                "selected_event": "geral",
            },
        ) as rankings_mock:
            response = self.client.get(f"{reverse('rankings')}?category=ia&subcategory=modelos&event=geral")
            rankings_mock.assert_called_once_with(category="ia", subcategory="modelos", event="geral")
            self.assertContains(response, "@apiviewer")
            self.assertContains(response, "Você está em #1 neste recorte")
            self.assertContains(response, "Reputação")
            self.assertContains(response, "ranking-category")
            self.assertContains(response, "ranking-event")
            self.assertContains(response, "selected")

    def test_profile_update_and_logical_delete_use_api(self):
        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": 21,
            "handle": "editviewer",
            "email": "edit-viewer@example.com",
            "display_name": "Edit Viewer",
            "preferred_language": "pt-br",
        }
        session.save()
        profile_payload = {
            "user": {
                **session[USER_KEY],
                "created_at": "2026-05-17T00:00:00+00:00",
                "last_login": "2026-05-17T01:00:00+00:00",
                "account_status": "active",
            },
            "profile_id": 21,
            "bio": "",
            "strong_category": "Geral",
            "birth_date": "",
            "sex": "",
            "profile_created_at": "2026-05-17T00:00:00+00:00",
            "profile_updated_at": "2026-05-17T00:00:00+00:00",
            "is_public": True,
            "reputation": {
                "reputation_score": 100,
                "ranking_position": 1,
                "resolved_predictions_count": 0,
                "accuracy_indicator": "0%",
                "streak": 0,
                "strong_category": "",
                "last_updated_at": "2026-05-17T00:00:00+00:00",
            },
        }
        updated_payload = {
            **profile_payload,
            "user": {
                **profile_payload["user"],
                "email": "edit-updated@example.com",
                "display_name": "Edit Updated",
                "preferred_language": "en",
            },
            "bio": "Nova bio",
            "strong_category": "IA",
            "birth_date": "1988-12-30",
            "sex": "other",
        }

        with patch("profiles.views.get_me", return_value=updated_payload), patch("profiles.views.get_badges", return_value=[]), patch("profiles.views.get_activity", return_value=[]), patch("profiles.views.update_me", return_value=updated_payload) as update_mock:
            response = self.client.post(
                reverse("profile"),
                {
                    "action": "update_profile",
                    "display_name": "Edit Updated",
                    "handle": "editupdated",
                    "email": "edit-updated@example.com",
                    "preferred_language": "en",
                    "birth_date": "1988-12-30",
                    "sex": "other",
                    "bio": "Nova bio",
                },
            )
            self.assertEqual(response.status_code, 200)
            update_mock.assert_called_once()
            self.assertNotIn("strong_category", update_mock.call_args.args[1])
            self.assertEqual(update_mock.call_args.args[1]["handle"], "@editupdated")
            self.assertEqual(update_mock.call_args.args[1]["birth_date"], "1988-12-30")
            self.assertEqual(update_mock.call_args.args[1]["sex"], "other")
            self.assertContains(response, "Perfil atualizado.")
            self.assertContains(response, "Editar dados")
            self.assertContains(response, "account-delete-card")

        with patch("profiles.views.request_account_deletion", return_value={}) as delete_mock:
            response = self.client.post(reverse("profile"), {"action": "delete_account", "confirm_delete": "on"})
            self.assertRedirects(response, reverse("home"))
            delete_mock.assert_called_once_with("api-token")
            self.assertNotIn(TOKEN_KEY, self.client.session)

    def test_home_stays_market_focused_for_guest_and_user(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Mercados em destaque")
        self.assertNotContains(response, "Seu resumo")
        self.assertNotContains(response, "Sua progressão")
        self.assertNotContains(response, "Modo visitante")
        self.assertNotContains(response, "Como participar em 40 segundos")
        self.assertNotContains(response, "Inteligência coletiva")

        session = self.client.session
        session[TOKEN_KEY] = "api-token"
        session[USER_KEY] = {
            "id": 30,
            "handle": "homeviewer",
            "email": "home-viewer@example.com",
            "display_name": "Home Viewer",
            "preferred_language": "pt-br",
        }
        session.save()
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Mercados em destaque")
        self.assertContains(response, 'data-filter="favorited"')
        self.assertContains(response, 'data-filter="predicted"')
        self.assertNotContains(response, "Seu resumo")
        self.assertNotContains(response, "Sua progressão")
        self.assertNotContains(response, "Membro fundador")

    def test_home_stats_show_real_total_predictions(self):
        User = get_user_model()
        user = User.objects.create_user(username="totalpredictions", email="total-predictions@example.com", password="testpass123")
        staff_user = User.objects.create_user(username="staffstats", email="staff-stats@example.com", password="testpass123", is_staff=True)
        super_user = User.objects.create_user(username="superstats", email="super-stats@example.com", password="testpass123", is_superuser=True)
        market = Market.objects.get(slug="openai-gpt6-2026")
        option = MarketOption.objects.filter(market=market).first()
        WalletLedgerEntry.objects.create(
            user=user,
            entry_type="reward_feedback",
            amount=1200,
            direction="credit",
            description="Recompensa pública para métrica da home",
        )
        WalletLedgerEntry.objects.create(user=staff_user, entry_type="manual_adjustment", amount=900, direction="credit", description="Crédito interno staff")
        WalletLedgerEntry.objects.create(user=super_user, entry_type="manual_adjustment", amount=800, direction="credit", description="Crédito interno superuser")
        prediction = Prediction.objects.create(
            user=user,
            market=market,
            market_option=option,
            stake_amount=80,
            probability_at_entry=Decimal("50.0000"),
            weight_at_entry=8000,
            potential_payout=160,
            status="resolved",
            won=True,
        )
        Prediction.objects.filter(id=prediction.id).update(created_at=timezone.now() - timedelta(days=45))
        total_predictions = Prediction.objects.count()
        distributed_gtl = sum(
            WalletLedgerEntry.objects.filter(direction="credit", user__is_staff=False, user__is_superuser=False).values_list("amount", flat=True)
        )
        moved_gtl = sum(Prediction.objects.values_list("stake_amount", flat=True))
        distributed_label = f"{distributed_gtl:,}".replace(",", ".")
        moved_label = f"{moved_gtl:,}".replace(",", ".")

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Mercados em destaque")
        self.assertNotContains(response, "previsões totais")
        self.assertNotContains(response, f"<strong>{total_predictions}</strong><span>previsões totais</span>", html=True)
        self.assertNotContains(response, f"<strong>{distributed_label} GT₵</strong><span>creditadas na comunidade</span>", html=True)
        self.assertNotContains(response, f"<strong>{moved_label} GT₵</strong><span>reservadas em previsões</span>", html=True)
        self.assertNotContains(response, "previsões no mês")
        self.assertNotContains(response, "<span>sem dinheiro real</span>", html=True)

        api_response = TestClient(app).get("/stats")
        self.assertEqual(api_response.status_code, 200)
        self.assertIn("distributed_gtl", api_response.json())
        self.assertIn("moved_gtl", api_response.json())

    def test_market_pages_consume_api_and_fallback_to_fixture(self):
        api_market = {
            **get_domain_client().market("openai-gpt6-2026"),
            "title": "Mercado vindo da API",
        }

        with patch("core.views.get_markets", return_value=[api_market]):
            response = self.client.get(reverse("home"))
            self.assertContains(response, "Mercado vindo da API")
            self.assertContains(response, "Feedback/suporte")

        liked_market = {**api_market, "slug": "liked-api", "title": "Mercado com mais curtidas", "is_featured": False, "market_like_count": 9, "view_count": 9, "created_at": "2026-05-17T12:00:00+00:00"}
        low_like_market = {**api_market, "slug": "low-like-api", "title": "Mercado com poucas curtidas", "is_featured": False, "market_like_count": 1, "view_count": 1, "created_at": "2026-05-18T12:00:00+00:00"}
        resolved_liked_market = {**api_market, "slug": "resolved-liked-api", "title": "Resolvido com curtidas", "status": "resolved", "is_featured": False, "market_like_count": 99, "view_count": 99, "created_at": "2026-05-19T12:00:00+00:00"}
        canceled_liked_market = {**api_market, "slug": "canceled-liked-api", "title": "Cancelado com curtidas", "status": "canceled", "is_featured": False, "market_like_count": 100, "view_count": 100, "created_at": "2026-05-20T12:00:00+00:00"}
        with patch("core.views.get_markets", return_value=[low_like_market, resolved_liked_market, canceled_liked_market, liked_market]):
            response = self.client.get(reverse("home"))
            self.assertNotContains(response, '<aside class="watch-card">')
            self.assertNotContains(response, "Inteligência coletiva")
            self.assertNotContains(response, "Modo visitante")
            self.assertNotContains(response, "Como participar em 40 segundos")
            self.assertContains(response, "Ver resolução")
            self.assertContains(response, 'data-filter-target="[data-market-list]"')
            filter_html = response.content.decode().split('<div class="filters" data-filter-group data-filter-target="[data-market-list]">', 1)[1].split("</div>", 1)[0]
            expected_filter_order = [
                'data-filter="trending"',
                'data-filter="new"',
                'data-filter="open"',
                'data-filter="closing"',
                'data-filter="resolved"',
                'data-filter="volume"',
                'data-filter="likes"',
            ]
            self.assertEqual([filter_html.index(item) for item in expected_filter_order], sorted(filter_html.index(item) for item in expected_filter_order))
            self.assertNotIn('data-filter="featured"', filter_html)
            self.assertNotIn('data-filter="favorited"', filter_html)
            self.assertIn("Em alta", filter_html)
            self.assertIn("Em apuração", filter_html)
            self.assertContains(response, "data-market-card")
            self.assertContains(response, 'data-market-likes="9"')
            self.assertContains(response, 'data-market-views="9"')
            self.assertContains(response, 'data-market-created-at="2026-05-17T12:00:00+00:00"')
            self.assertContains(response, 'data-market-featured="false"')
            self.assertContains(response, 'data-market-page-size="18"')
            self.assertContains(response, 'data-market-load-more')
            self.assertContains(response, 'data-market-load-more-button')
            self.assertContains(response, 'Carregar mais')
            self.assertContains(response, "9 curtidas")
            self.assertContains(response, "1 curtida")
            self.assertContains(response, '<span class="like-mark" aria-hidden="true">👍</span>')
            self.assertNotContains(response, '<span class="like-mark">♥</span>')
            self.assertContains(response, "Mercado com mais curtidas")
            self.assertContains(response, "Mercado com poucas curtidas")
            self.assertContains(response, "Resolvido com curtidas")
            market_list = response.content.decode().split(
                '<div class="market-list" data-market-list data-market-page-size="18">',
                1,
            )[1]
            self.assertNotIn("Cancelado com curtidas", market_list)

        with patch("markets.views.get_market", return_value=api_market):
            response = self.client.get(reverse("market-detail", args=["openai-gpt6-2026"]))
            self.assertContains(response, "Mercado vindo da API")

        with patch("core.views.get_market", return_value=api_market):
            response = self.client.get(reverse("share-market", args=["openai-gpt6-2026"]))
            self.assertContains(response, "Mercado vindo da API")

        with patch("core.views.get_markets", side_effect=AuthAPIError("api off")):
            response = self.client.get(reverse("home"))
            self.assertContains(response, "OpenAI anuncia GPT-6")

    def test_register_login_and_logout_flow(self):
        auth_response = {
            "user": {
                "id": 10,
                "handle": "@carolvision",
                "email": "carol@gotrendlabs.com.br",
                "display_name": "Carol Vision",
                "preferred_language": "pt-br",
            },
            "session": {"token": "api-token", "expires_at": "2026-06-01T00:00:00+00:00"},
        }

        with patch("accounts.views.register_user", return_value=auth_response) as register_user:
            response = self.client.post(
                reverse("register"),
                {
                    "display_name": "Carol Vision",
                    "email": "carol@gotrendlabs.com.br",
                    "language": "pt-br",
                    "password": "testpass123",
                    "terms_accepted": "on",
                    "g-recaptcha-response": "captcha-token",
                },
            )
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(register_user.call_args.args[0]["recaptcha_token"], "captcha-token")

        with patch("accounts.views.logout_user", return_value={}):
            self.client.get(reverse("logout"))

        with patch("accounts.views.login_user", return_value=auth_response) as login_user:
            response = self.client.post(
                reverse("login"),
                {"email": "carol@gotrendlabs.com.br", "password": "testpass123"},
            )
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(login_user.call_args.args[0], {"email": "carol@gotrendlabs.com.br", "password": "testpass123"})
        self.assertLess(self.client.session.get_expiry_age(), 60 * 60 * 24 * 30)

        with patch("accounts.views.logout_user", return_value={}):
            self.client.get(reverse("logout"))

        with patch("accounts.views.login_user", return_value=auth_response):
            response = self.client.post(
                reverse("login"),
                {"email": "carol@gotrendlabs.com.br", "password": "testpass123", "remember_me": "on"},
            )
        self.assertRedirects(response, reverse("home"))
        self.assertGreaterEqual(self.client.session.get_expiry_age(), (60 * 60 * 24 * 30) - 5)

    def test_prediction_preview_partial_renders(self):
        option = MarketOption.objects.get(market__slug="openai-gpt6-2026", label="SIM")
        with patch("markets.views.preview_prediction", return_value={"estimated_return": 240}):
            response = self.client.post(
                reverse("prediction-preview", args=["openai-gpt6-2026"]),
                {"choice": "SIM", "amount": "120", "option_id": option.id},
                HTTP_HX_REQUEST="true",
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SIM")
        self.assertContains(response, "120 GT₵")
        self.assertContains(response, "240 GT₵")
