#!/usr/bin/env python3
"""Import a curated bootstrap package into PRD safely and idempotently."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils.dateparse import parse_date, parse_datetime

from accounts.models import BadgeDefinition, BadgeRule, UserBadgeAward, UserProfile, UserReputation, WalletBalance, WalletLedgerEntry
from admin_ops.models import SiteConfig
from markets.models import (
    AdminEvent,
    CommentReaction,
    Market,
    MarketCategory,
    MarketComment,
    MarketFavorite,
    MarketLike,
    MarketOption,
    MarketSubcategory,
    MarketSuggestion,
    Prediction,
    ProductFeedback,
)
from system_logs.models import SystemLog


BLOCKING_TABLES = [
    (Prediction, "predictions"),
    (MarketFavorite, "market favorites"),
    (MarketLike, "market likes"),
    (MarketComment, "market comments"),
    (CommentReaction, "comment reactions"),
    (MarketSuggestion, "market suggestions"),
    (ProductFeedback, "product feedback"),
    (AdminEvent, "admin events"),
]


def decimal_value(value):
    return Decimal(str(value or "0"))


def datetime_value(value):
    return parse_datetime(value) if value else None


def date_value(value):
    return parse_date(value) if value else None


def load_bundle(bundle_dir):
    bundle_path = bundle_dir / "bootstrap.json"
    if not bundle_path.exists():
        raise SystemExit(f"Missing bundle file: {bundle_path}")
    return json.loads(bundle_path.read_text(encoding="utf-8"))


def validate_media(bundle_dir, data):
    media_urls = []
    for badge in data["badges"]:
        media_urls.extend([badge.get("image_url", ""), badge.get("image_dark_url", "")])
    for market in data["editorial"]["markets"]:
        media_urls.append(market.get("image_url", ""))

    missing = []
    for url in media_urls:
        if not url or not url.startswith(settings.MEDIA_URL):
            continue
        relative = url[len(settings.MEDIA_URL) :].lstrip("/")
        if not (bundle_dir / "media" / relative).exists():
            missing.append(relative)
    if missing:
        raise SystemExit(f"Bundle is missing referenced media files: {', '.join(sorted(set(missing)))}")


def copy_media(bundle_dir):
    source_root = bundle_dir / "media"
    if not source_root.exists():
        return 0
    copied = 0
    for source in source_root.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(source_root)
        target = Path(settings.MEDIA_ROOT) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1
    return copied


def assert_safe_target(data):
    for model, label in BLOCKING_TABLES:
        count = model.objects.count()
        if count:
            raise SystemExit(f"Refusing to import because PRD already has {count} {label}.")

    User = get_user_model()
    allowed_username = data["admin"]["user"]["username"]
    unexpected_users = User.objects.exclude(username=allowed_username).count()
    if unexpected_users:
        raise SystemExit(f"Refusing to import because PRD already has {unexpected_users} non-bootstrap users.")


def import_admin(data):
    User = get_user_model()
    user_payload = data["admin"]["user"]
    password = os.environ.get("GOTRENDLABS_BOOTSTRAP_ADMIN_PASSWORD", "")
    existing_email = User.objects.filter(email=user_payload["email"]).exclude(username=user_payload["username"]).first()
    if existing_email:
        raise SystemExit(f"Email {user_payload['email']} is already used by another user.")

    user, _ = User.objects.update_or_create(
        username=user_payload["username"],
        defaults={
            "email": user_payload["email"],
            "first_name": user_payload.get("first_name", ""),
            "last_name": user_payload.get("last_name", ""),
            "preferred_language": user_payload.get("preferred_language", "pt-br"),
            "is_staff": True,
            "is_superuser": True,
            "is_active": user_payload.get("is_active", True),
            "terms_accepted_at": datetime_value(user_payload.get("terms_accepted_at")),
            "terms_version": user_payload.get("terms_version", ""),
            "account_status": user_payload.get("account_status", "active"),
            "deletion_requested_at": datetime_value(user_payload.get("deletion_requested_at")),
            "deactivated_at": datetime_value(user_payload.get("deactivated_at")),
            "is_bot": user_payload.get("is_bot", False),
        },
    )
    if password:
        user.set_password(password)
    else:
        user.set_unusable_password()
    user.save()

    profile = data["admin"].get("profile")
    if profile:
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "display_name": profile.get("display_name") or user.first_name or user.username,
                "bio": profile.get("bio", ""),
                "strong_category": profile.get("strong_category", ""),
                "birth_date": date_value(profile.get("birth_date")),
                "sex": profile.get("sex", ""),
                "is_public": profile.get("is_public", True),
            },
        )

    reputation = data["admin"].get("reputation") or {}
    UserReputation.objects.update_or_create(
        user=user,
        defaults={
            "reputation_score": reputation.get("reputation_score") or 100,
            "resolved_predictions_count": reputation.get("resolved_predictions_count") or 0,
            "accuracy_indicator": reputation.get("accuracy_indicator") or "0%",
            "streak": reputation.get("streak") or 0,
            "strong_category": reputation.get("strong_category") or "",
        },
    )

    wallet = data["admin"].get("wallet_balance")
    if wallet:
        WalletBalance.objects.update_or_create(
            user=user,
            defaults={
                "available_gtl": wallet.get("available_gtl", 0),
                "locked_gtl": wallet.get("locked_gtl", 0),
                "total_earned_gtl": wallet.get("total_earned_gtl", 0),
            },
        )

    for entry in data["admin"].get("wallet_ledger", []):
        WalletLedgerEntry.objects.get_or_create(
            user=user,
            entry_type=entry["entry_type"],
            amount=entry["amount"],
            direction=entry["direction"],
            description=entry["description"],
            reference_type=entry.get("reference_type", ""),
            reference_id=entry.get("reference_id", ""),
            defaults={"created_by": user},
        )
    return user


def import_badges(data, admin):
    badges = {}
    for item in data["badges"]:
        badge, _ = BadgeDefinition.objects.update_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "description": item["description"],
                "rule_description": item.get("rule_description", ""),
                "badge_type": item.get("badge_type", "global"),
                "image_url": item.get("image_url", ""),
                "image_dark_url": item.get("image_dark_url", ""),
                "is_active": item.get("is_active", True),
            },
        )
        if item.get("rule"):
            rule = item["rule"]
            BadgeRule.objects.update_or_create(
                badge=badge,
                defaults={
                    "rule_type": rule["rule_type"],
                    "threshold_value": decimal_value(rule.get("threshold_value", 1)),
                    "category": rule.get("category", ""),
                    "subcategory": rule.get("subcategory", ""),
                    "is_active": rule.get("is_active", True),
                },
            )
        badges[item["code"]] = badge

    for award in data["admin"].get("badge_awards", []):
        badge = badges.get(award["badge_code"])
        if not badge:
            continue
        UserBadgeAward.objects.update_or_create(
            user=admin,
            badge=badge,
            defaults={
                "awarded_at": datetime_value(award["awarded_at"]) or datetime.now(),
                "reason_snapshot": award.get("reason_snapshot", ""),
            },
        )


def import_site_config(data, admin):
    payload = data["site_config"]
    SiteConfig.objects.update_or_create(
        singleton_key=payload.get("singleton_key", 1),
        defaults={
            "wallet_recharge_min_balance_gtl": payload.get("wallet_recharge_min_balance_gtl", 100),
            "daemon_stale_after_minutes": payload.get("daemon_stale_after_minutes", 7),
            "daemon_missing_after_minutes": payload.get("daemon_missing_after_minutes", 21),
            "email_enabled": payload.get("email_enabled", False),
            "smtp_host": payload.get("smtp_host", ""),
            "smtp_port": payload.get("smtp_port", 587),
            "smtp_username": payload.get("smtp_username", ""),
            "smtp_use_tls": payload.get("smtp_use_tls", True),
            "smtp_use_ssl": payload.get("smtp_use_ssl", False),
            "smtp_timeout_seconds": payload.get("smtp_timeout_seconds", 10),
            "default_from_email": payload.get("default_from_email", ""),
            "default_reply_to_email": payload.get("default_reply_to_email", ""),
            "updated_by": admin,
        },
    )


def import_editorial(data, admin):
    category_by_slug = {}
    for item in data["editorial"]["categories"]:
        category, _ = MarketCategory.objects.update_or_create(
            slug=item["slug"],
            defaults={
                "name": item["name"],
                "is_blocked": item.get("is_blocked", False),
                "blocked_at": datetime_value(item.get("blocked_at")),
                "blocked_reason": item.get("blocked_reason", ""),
            },
        )
        category_by_slug[item["slug"]] = category

    subcategory_by_key = {}
    for item in data["editorial"]["subcategories"]:
        category = category_by_slug[item["category_slug"]]
        subcategory, _ = MarketSubcategory.objects.update_or_create(
            category=category,
            slug=item["slug"],
            defaults={
                "name": item["name"],
                "is_blocked": item.get("is_blocked", False),
                "blocked_at": datetime_value(item.get("blocked_at")),
                "blocked_reason": item.get("blocked_reason", ""),
            },
        )
        subcategory_by_key[(item["category_slug"], item["slug"])] = subcategory

    market_slugs = set()
    for item in data["editorial"]["markets"]:
        category = category_by_slug[item["category_slug"]]
        subcategory = subcategory_by_key[(item["category_slug"], item["subcategory_slug"])]
        market, _ = Market.objects.update_or_create(
            slug=item["slug"],
            defaults={
                "category": category,
                "subcategory": subcategory,
                "title": item["title"],
                "summary": item.get("summary", ""),
                "kind": item["kind"],
                "status": item["status"],
                "status_label": item.get("status_label", item["status"]),
                "primary_outcome": item.get("primary_outcome", ""),
                "primary_probability_exact": decimal_value(item.get("primary_probability_exact", 0)),
                "secondary_probability_exact": decimal_value(item.get("secondary_probability_exact", 0)),
                "volume_gtl": item.get("volume_gtl", ""),
                "participants": item.get("participants", ""),
                "source": item.get("source", ""),
                "closes_in": item.get("closes_in", ""),
                "close_label": item.get("close_label", ""),
                "thumb": item.get("thumb", ""),
                "thumb_color": item.get("thumb_color", ""),
                "image_url": item.get("image_url", ""),
                "resolution_criteria": item.get("resolution_criteria", ""),
                "resolution_type": item.get("resolution_type", ""),
                "close_at": datetime_value(item.get("close_at")),
                "close_timezone": item.get("close_timezone", ""),
                "auto_close_enabled": item.get("auto_close_enabled", True),
                "is_featured": item.get("is_featured", False),
                "view_count": item.get("view_count", 0),
                "share_count": item.get("share_count", 0),
                "resolved_at": datetime_value(item.get("resolved_at")),
                "resolution_timezone": item.get("resolution_timezone", ""),
                "canceled_at": datetime_value(item.get("canceled_at")),
                "winning_option": None,
                "resolution_note": item.get("resolution_note", ""),
                "admin_notes": item.get("admin_notes", ""),
                "created_by": admin,
                "updated_by": admin,
                "display_order": item.get("display_order", 0),
            },
        )
        market_slugs.add(market.slug)

        option_labels = set()
        option_by_label = {}
        for option_payload in item["options"]:
            option, _ = MarketOption.objects.update_or_create(
                market=market,
                label=option_payload["label"],
                defaults={
                    "probability_exact": decimal_value(option_payload.get("probability_exact", 0)),
                    "hint": option_payload.get("hint", ""),
                    "display_order": option_payload.get("display_order", 0),
                },
            )
            option_labels.add(option.label)
            option_by_label[option.label] = option

        MarketOption.objects.filter(market=market).exclude(label__in=option_labels).delete()
        winning_label = item.get("winning_option_label")
        if winning_label:
            market.winning_option = option_by_label.get(winning_label)
            market.save(update_fields=["winning_option"])

    package_category_slugs = {item["slug"] for item in data["editorial"]["categories"]}
    package_subcategory_keys = {(item["category_slug"], item["slug"]) for item in data["editorial"]["subcategories"]}
    for subcategory in MarketSubcategory.objects.select_related("category").filter(markets__isnull=True):
        if (subcategory.category.slug, subcategory.slug) not in package_subcategory_keys:
            subcategory.delete()
    MarketCategory.objects.filter(markets__isnull=True, subcategories__isnull=True).exclude(slug__in=package_category_slugs).delete()


def summarize():
    User = get_user_model()
    return {
        "users": User.objects.count(),
        "markets": Market.objects.count(),
        "options": MarketOption.objects.count(),
        "badges": BadgeDefinition.objects.count(),
        "site_config": SiteConfig.objects.count(),
        "system_logs": SystemLog.objects.count(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", default=".runtime/prod-bootstrap", help="Directory containing bootstrap.json and media/")
    parser.add_argument("--dry-run", action="store_true", help="Validate target and bundle without writing changes")
    args = parser.parse_args()

    bundle_dir = Path(args.bundle_dir).resolve()
    data = load_bundle(bundle_dir)
    validate_media(bundle_dir, data)
    assert_safe_target(data)

    if args.dry_run:
        print(json.dumps({"dry_run": True, "bundle_summary": data.get("summary", {}), "target_summary": summarize()}, indent=2))
        return

    copied = copy_media(bundle_dir)
    with transaction.atomic():
        admin = import_admin(data)
        import_badges(data, admin)
        import_site_config(data, admin)
        import_editorial(data, admin)

    summary = summarize()
    summary["copied_media_files"] = copied
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
