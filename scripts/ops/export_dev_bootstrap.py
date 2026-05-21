#!/usr/bin/env python3
"""Export the curated DEV bootstrap package for a first PRD population."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.models import BadgeDefinition, UserBadgeAward, UserProfile, UserReputation, WalletBalance, WalletLedgerEntry
from admin_ops.models import SiteConfig
from markets.models import Market, MarketCategory, MarketOption, MarketSubcategory


ADMIN_USERNAME = "@admin"
DEFAULT_MARKET_SLUGS_FILE = BASE_DIR / "docs" / "specs" / "state" / "editorial-seed-markets-20260521.md"


def serialize(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def model_payload(instance, fields):
    return {field: serialize(getattr(instance, field)) for field in fields}


def media_relative_path(url):
    if not url or not url.startswith(settings.MEDIA_URL):
        return ""
    return url[len(settings.MEDIA_URL) :].lstrip("/")


def collect_media(media_files, url):
    relative = media_relative_path(url)
    if relative:
        media_files.add(relative)


def export_admin(media_files):
    User = get_user_model()
    admin = User.objects.get(username=ADMIN_USERNAME, is_superuser=True)
    payload = model_payload(
        admin,
        [
            "username",
            "email",
            "first_name",
            "last_name",
            "preferred_language",
            "is_staff",
            "is_superuser",
            "is_active",
            "terms_accepted_at",
            "terms_version",
            "account_status",
            "deletion_requested_at",
            "deactivated_at",
            "is_bot",
        ],
    )

    profile = getattr(admin, "profile", None)
    reputation = getattr(admin, "reputation", None)
    wallet = getattr(admin, "wallet_balance", None)

    return {
        "user": payload,
        "profile": model_payload(profile, ["display_name", "bio", "strong_category", "birth_date", "sex", "is_public"]) if profile else None,
        "reputation": model_payload(
            reputation,
            ["reputation_score", "resolved_predictions_count", "accuracy_indicator", "streak", "strong_category"],
        )
        if reputation
        else None,
        "wallet_balance": model_payload(wallet, ["available_oc", "locked_oc", "total_earned_oc"]) if wallet else None,
        "wallet_ledger": [
            model_payload(entry, ["entry_type", "amount", "direction", "description", "reference_type", "reference_id", "created_at"])
            for entry in WalletLedgerEntry.objects.filter(user=admin).order_by("created_at", "id")
        ],
        "badge_awards": [
            {
                "badge_code": award.badge.code,
                "awarded_at": serialize(award.awarded_at),
                "reason_snapshot": award.reason_snapshot,
            }
            for award in UserBadgeAward.objects.select_related("badge").filter(user=admin).order_by("awarded_at", "id")
        ],
    }


def export_badges(media_files):
    badges = []
    for badge in BadgeDefinition.objects.select_related("rule").order_by("code"):
        if not badge.image_url:
            continue
        collect_media(media_files, badge.image_url)
        collect_media(media_files, badge.image_dark_url)
        badges.append(
            {
                **model_payload(
                    badge,
                    ["code", "name", "description", "rule_description", "badge_type", "image_url", "image_dark_url", "is_active"],
                ),
                "rule": model_payload(
                    badge.rule,
                    ["rule_type", "threshold_value", "category", "subcategory", "is_active"],
                )
                if hasattr(badge, "rule")
                else None,
            }
        )
    return badges


def export_site_config():
    config = SiteConfig.get_solo()
    return model_payload(
        config,
        [
            "singleton_key",
            "wallet_recharge_min_balance_oc",
            "daemon_stale_after_minutes",
            "daemon_missing_after_minutes",
            "email_enabled",
            "smtp_host",
            "smtp_port",
            "smtp_username",
            "smtp_use_tls",
            "smtp_use_ssl",
            "smtp_timeout_seconds",
            "default_from_email",
            "default_reply_to_email",
        ],
    )


def load_market_slugs(path):
    content = Path(path).read_text(encoding="utf-8")
    slugs = []
    in_markets_section = False
    for line in content.splitlines():
        if line.strip() == "## Mercados":
            in_markets_section = True
            continue
        if in_markets_section and line.startswith("## "):
            break
        if not in_markets_section:
            continue
        match = re.search(r"`([^`]+)`", line)
        if match:
            slugs.append(match.group(1))
    if not slugs:
        raise SystemExit(f"No market slugs found in {path}")
    return slugs


def export_markets(media_files, market_slugs):
    market_queryset = (
        Market.objects.select_related("category", "subcategory", "winning_option")
        .prefetch_related("options")
        .filter(slug__in=market_slugs)
        .order_by("display_order", "id")
    )
    found_slugs = set(market_queryset.values_list("slug", flat=True))
    missing_slugs = [slug for slug in market_slugs if slug not in found_slugs]
    if missing_slugs:
        raise SystemExit(f"Missing editorial markets in DEV: {', '.join(missing_slugs)}")

    category_slugs = set(market_queryset.values_list("category__slug", flat=True))
    subcategory_ids = set(market_queryset.values_list("subcategory_id", flat=True))
    categories = [
        model_payload(category, ["name", "slug", "is_blocked", "blocked_at", "blocked_reason"])
        for category in MarketCategory.objects.filter(slug__in=category_slugs).order_by("slug")
    ]
    subcategories = [
        {
            **model_payload(subcategory, ["name", "slug", "is_blocked", "blocked_at", "blocked_reason"]),
            "category_slug": subcategory.category.slug,
        }
        for subcategory in MarketSubcategory.objects.select_related("category").filter(id__in=subcategory_ids).order_by("category__slug", "slug")
    ]
    markets = []
    for market in market_queryset:
        collect_media(media_files, market.image_url)
        markets.append(
            {
                **model_payload(
                    market,
                    [
                        "slug",
                        "title",
                        "summary",
                        "kind",
                        "status",
                        "status_label",
                        "primary_outcome",
                        "primary_probability_exact",
                        "secondary_probability_exact",
                        "volume_oc",
                        "participants",
                        "source",
                        "closes_in",
                        "close_label",
                        "thumb",
                        "thumb_color",
                        "image_url",
                        "resolution_criteria",
                        "resolution_type",
                        "close_at",
                        "close_timezone",
                        "auto_close_enabled",
                        "is_featured",
                        "view_count",
                        "share_count",
                        "resolved_at",
                        "resolution_timezone",
                        "canceled_at",
                        "resolution_note",
                        "admin_notes",
                        "display_order",
                    ],
                ),
                "category_slug": market.category.slug,
                "subcategory_slug": market.subcategory.slug,
                "winning_option_label": market.winning_option.label if market.winning_option else "",
                "options": [
                    model_payload(option, ["label", "probability_exact", "hint", "display_order"])
                    for option in market.options.order_by("display_order", "id")
                ],
            }
        )
    return {"categories": categories, "subcategories": subcategories, "markets": markets}


def copy_media(bundle_dir, media_files):
    media_root = Path(settings.MEDIA_ROOT)
    output_root = bundle_dir / "media"
    missing = []
    for relative in sorted(media_files):
        source = media_root / relative
        if not source.exists():
            missing.append(relative)
            continue
        target = output_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    if missing:
        raise SystemExit(f"Missing media files: {', '.join(missing)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=".runtime/prod-bootstrap", help="Directory that will receive bootstrap.json and media/")
    parser.add_argument("--market-slugs-file", default=str(DEFAULT_MARKET_SLUGS_FILE), help="Markdown file listing editorial market slugs to export")
    args = parser.parse_args()

    bundle_dir = Path(args.output_dir).resolve()
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True)

    media_files = set()
    market_slugs = load_market_slugs(args.market_slugs_file)
    data = {
        "version": 1,
        "source": "dev",
        "admin": export_admin(media_files),
        "badges": export_badges(media_files),
        "site_config": export_site_config(),
        "editorial": export_markets(media_files, market_slugs),
    }
    data["summary"] = {
        "admin_users": 1,
        "badges": len(data["badges"]),
        "categories": len(data["editorial"]["categories"]),
        "subcategories": len(data["editorial"]["subcategories"]),
        "markets": len(data["editorial"]["markets"]),
        "options": sum(len(market["options"]) for market in data["editorial"]["markets"]),
        "media_files": len(media_files),
    }

    (bundle_dir / "bootstrap.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    copy_media(bundle_dir, media_files)
    print(json.dumps(data["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
