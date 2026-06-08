from datetime import datetime, timezone
from decimal import Decimal
import json


class BadgeAwardEngine:
    USER_REGISTERED_RULES = {"founding_member"}
    COMMENT_CREATED_RULES = {"comments_count"}
    SUGGESTION_APPROVED_RULES = {"approved_suggestions_count"}
    SUGGESTION_REWARDED_RULES = {"approved_suggestions_count"}
    FEEDBACK_REWARDED_RULES = {"rewarded_feedback_count"}
    MARKET_RESOLVED_RULES = {
        "resolved_predictions_count",
        "correct_predictions_count",
        "streak_count",
        "ranking_position",
    }

    @classmethod
    def on_user_registered(cls, cursor, user_id):
        return cls.evaluate_user(cursor, user_id, rule_types=cls.USER_REGISTERED_RULES, reason_prefix="user_registered")

    @classmethod
    def on_comment_created(cls, cursor, user_id, market_id=None):
        return cls.evaluate_user(
            cursor,
            user_id,
            rule_types=cls.COMMENT_CREATED_RULES,
            reason_prefix=f"comment_created:{market_id or ''}",
        )

    @classmethod
    def on_suggestion_approved(cls, cursor, user_id, suggestion_id=None):
        return cls.evaluate_user(
            cursor,
            user_id,
            rule_types=cls.SUGGESTION_APPROVED_RULES,
            reason_prefix=f"suggestion_approved:{suggestion_id or ''}",
        )

    @classmethod
    def on_suggestion_rewarded(cls, cursor, user_id, suggestion_id=None):
        return cls.evaluate_user(
            cursor,
            user_id,
            rule_types=cls.SUGGESTION_REWARDED_RULES,
            reason_prefix=f"suggestion_rewarded:{suggestion_id or ''}",
        )

    @classmethod
    def on_feedback_rewarded(cls, cursor, user_id, feedback_id=None):
        return cls.evaluate_user(
            cursor,
            user_id,
            rule_types=cls.FEEDBACK_REWARDED_RULES,
            reason_prefix=f"feedback_rewarded:{feedback_id or ''}",
        )

    @classmethod
    def on_market_resolved(cls, cursor, market_id):
        cursor.execute(
            """
            SELECT DISTINCT p.user_id
            FROM gotrendlabs_predictions p
            JOIN gotrendlabs_users u ON u.id = p.user_id
            WHERE p.market_id = %s
              AND p.status = 'resolved'
              AND u.is_bot = false
            ORDER BY p.user_id ASC
            """,
            (market_id,),
        )
        awarded = []
        for row in cursor.fetchall():
            awarded.extend(
                cls.evaluate_user(
                    cursor,
                    row["user_id"],
                    rule_types=cls.MARKET_RESOLVED_RULES,
                    reason_prefix=f"market_resolved:{market_id}",
                )
            )
        return awarded

    @classmethod
    def reconcile_user(cls, cursor, user_id, ensure_user_core=None):
        if ensure_user_core:
            ensure_user_core(cursor, user_id)
        return cls.evaluate_user(cursor, user_id, reason_prefix="reconcile")

    @classmethod
    def evaluate_user(cls, cursor, user_id, *, rule_types=None, reason_prefix="badge_engine"):
        cursor.execute("SELECT is_bot FROM gotrendlabs_users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user and user["is_bot"]:
            return []
        rules = cls._active_rules(cursor, rule_types=rule_types)
        awarded = []
        for rule in rules:
            value = cls._metric_value(cursor, user_id, rule)
            if cls._rule_is_met(value, rule):
                created = cls._award_by_code(
                    cursor,
                    user_id,
                    rule["code"],
                    f"{reason_prefix}; {rule['rule_type']}={value}",
                )
                if created:
                    awarded.append(rule["code"])
        return awarded

    @classmethod
    def _active_rules(cls, cursor, *, rule_types=None):
        params = []
        rule_filter = ""
        if rule_types:
            placeholders = ", ".join(["%s"] * len(rule_types))
            rule_filter = f" AND r.rule_type IN ({placeholders})"
            params.extend(sorted(rule_types))
        cursor.execute(
            f"""
            SELECT b.id, b.code, b.name, r.rule_type, r.threshold_value, r.category, r.subcategory, r.event
            FROM gotrendlabs_badge_definitions b
            JOIN gotrendlabs_badge_rules r ON r.badge_id = b.id
            WHERE b.is_active = true
              AND r.is_active = true
              {rule_filter}
            ORDER BY b.code ASC
            """,
            params,
        )
        return cursor.fetchall()

    @classmethod
    def _award_by_code(cls, cursor, user_id, code, reason_snapshot=""):
        cursor.execute("SELECT id, name FROM gotrendlabs_badge_definitions WHERE code = %s", (code,))
        badge = cursor.fetchone()
        if not badge:
            return False
        cursor.execute(
            """
            INSERT INTO gotrendlabs_user_badge_awards (user_id, badge_id, awarded_at, reason_snapshot)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, badge_id) DO NOTHING
            RETURNING id
            """,
            (user_id, badge["id"], datetime.now(timezone.utc), reason_snapshot or f"Conquista: {badge['name']}"),
        )
        award = cursor.fetchone()
        if not award:
            return False
        cls._notify_badge_awarded(cursor, user_id, code, badge["name"], award["id"])
        return True

    @classmethod
    def _notify_badge_awarded(cls, cursor, user_id, code, badge_name, award_id):
        cursor.execute("SELECT is_bot FROM gotrendlabs_users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        user_is_bot = user["is_bot"] if isinstance(user, dict) else user[0] if user else False
        if not user or user_is_bot:
            return
        cursor.execute(
            """
            INSERT INTO gotrendlabs_user_notifications
                (recipient_id, actor_id, market_id, comment_id, event_type, source_key, title, body, is_read, read_at, metadata, created_at)
            VALUES (%s, NULL, NULL, NULL, %s, %s, %s, %s, false, NULL, %s::jsonb, %s)
            ON CONFLICT (recipient_id, source_key) DO NOTHING
            RETURNING id
            """,
            (
                user_id,
                "badge_awarded",
                f"badge_awarded:{code}",
                "Badge recebida",
                f"Você recebeu a badge {badge_name}.",
                json.dumps({"badge_code": code, "badge_name": badge_name, "award_id": award_id}),
                datetime.now(timezone.utc),
            ),
        )
        created = cursor.fetchone()
        if created:
            from apps.web.django.communications.push_services import enqueue_push_for_notification

            notification_id = created["id"] if isinstance(created, dict) else created[0]
            enqueue_push_for_notification(cursor, notification_id)

    @classmethod
    def _prediction_rule_count(cls, cursor, user_id, rule_type, category="", subcategory="", event=""):
        predicates = ["p.user_id = %s", "p.status = 'resolved'"]
        params = [user_id]
        if rule_type == "correct_predictions_count":
            predicates.append("p.won = true")
        if category:
            predicates.append("(lower(c.name) = lower(%s) OR lower(c.slug) = lower(%s))")
            params.extend([category, category])
        if subcategory:
            predicates.append("(lower(sc.name) = lower(%s) OR lower(sc.slug) = lower(%s))")
            params.extend([subcategory, subcategory])
        if event:
            predicates.append("(lower(ev.name) = lower(%s) OR lower(ev.slug) = lower(%s))")
            params.extend([event, event])
        cursor.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM gotrendlabs_predictions p
            JOIN gotrendlabs_markets m ON m.id = p.market_id
            JOIN gotrendlabs_market_categories c ON c.id = m.category_id
            JOIN gotrendlabs_market_subcategories sc ON sc.id = m.subcategory_id
            JOIN gotrendlabs_market_events ev ON ev.id = m.event_id
            WHERE {' AND '.join(predicates)}
            """,
            params,
        )
        return int(cursor.fetchone()["total"] or 0)

    @classmethod
    def _ranking_positions(cls, cursor):
        cursor.execute(
            """
            SELECT u.id
            FROM gotrendlabs_user_reputations r
            JOIN gotrendlabs_users u ON u.id = r.user_id
            WHERE u.is_active = true
              AND u.is_staff = false
              AND u.is_superuser = false
              AND u.is_bot = false
            ORDER BY r.reputation_score DESC, u.date_joined ASC, u.id ASC
            """
        )
        return {row["id"]: index + 1 for index, row in enumerate(cursor.fetchall())}

    @classmethod
    def _metric_value(cls, cursor, user_id, rule):
        rule_type = rule["rule_type"]
        if rule_type == "founding_member":
            cursor.execute("SELECT date_joined FROM gotrendlabs_users WHERE id = %s", (user_id,))
            return 1 if cursor.fetchone() else 0
        if rule_type in {"resolved_predictions_count", "correct_predictions_count"}:
            return cls._prediction_rule_count(cursor, user_id, rule_type, rule["category"], rule["subcategory"], rule["event"])
        if rule_type == "streak_count":
            cursor.execute("SELECT streak FROM gotrendlabs_user_reputations WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            return int(row["streak"] or 0) if row else 0
        if rule_type == "ranking_position":
            return cls._ranking_positions(cursor).get(user_id, 0)
        if rule_type == "comments_count":
            return cls._comments_count(cursor, user_id, rule)
        if rule_type == "approved_suggestions_count":
            return cls._approved_suggestions_count(cursor, user_id, rule)
        if rule_type == "rewarded_feedback_count":
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM gotrendlabs_product_feedback
                WHERE author_id = %s
                  AND status = 'rewarded'
                """,
                (user_id,),
            )
            return int(cursor.fetchone()["total"] or 0)
        return 0

    @classmethod
    def _comments_count(cls, cursor, user_id, rule):
        predicates = ["mc.author_id = %s", "mc.status = 'visible'"]
        params = [user_id]
        joins = ""
        if rule["category"] or rule["subcategory"] or rule["event"]:
            joins = """
            JOIN gotrendlabs_markets m ON m.id = mc.market_id
            JOIN gotrendlabs_market_categories c ON c.id = m.category_id
            JOIN gotrendlabs_market_subcategories sc ON sc.id = m.subcategory_id
            JOIN gotrendlabs_market_events ev ON ev.id = m.event_id
            """
        if rule["category"]:
            predicates.append("(lower(c.name) = lower(%s) OR lower(c.slug) = lower(%s))")
            params.extend([rule["category"], rule["category"]])
        if rule["subcategory"]:
            predicates.append("(lower(sc.name) = lower(%s) OR lower(sc.slug) = lower(%s))")
            params.extend([rule["subcategory"], rule["subcategory"]])
        if rule["event"]:
            predicates.append("(lower(ev.name) = lower(%s) OR lower(ev.slug) = lower(%s))")
            params.extend([rule["event"], rule["event"]])
        cursor.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM gotrendlabs_market_comments mc
            {joins}
            WHERE {' AND '.join(predicates)}
            """,
            params,
        )
        return int(cursor.fetchone()["total"] or 0)

    @classmethod
    def _approved_suggestions_count(cls, cursor, user_id, rule):
        predicates = ["author_id = %s", "status IN ('reviewed', 'converted', 'rewarded')"]
        params = [user_id]
        if rule["category"]:
            predicates.append("lower(category) = lower(%s)")
            params.append(rule["category"])
        if rule["subcategory"]:
            predicates.append("lower(subcategory) = lower(%s)")
            params.append(rule["subcategory"])
        if rule["event"]:
            return 0
        cursor.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM gotrendlabs_market_suggestions
            WHERE {' AND '.join(predicates)}
            """,
            params,
        )
        return int(cursor.fetchone()["total"] or 0)

    @classmethod
    def _rule_is_met(cls, value, rule):
        threshold = Decimal(str(rule["threshold_value"] or 0))
        if rule["rule_type"] == "ranking_position":
            return value > 0 and Decimal(value) <= threshold
        return Decimal(value) >= threshold
