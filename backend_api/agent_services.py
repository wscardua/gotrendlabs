from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
import re

from backend_api.agent_llm import AgentLLMError, request_market_comment
from backend_api.agent_prompts import PROMPT_TEMPLATE_VERSION, build_comment_prompt, template_hash


INITIAL_REPUTATION = 100
BASE_PREDICTION_WEIGHT = 10_000
PROBABILITY_QUANT = Decimal("0.0001")


def _decimal_probability(value):
    return Decimal(str(value or 0)).quantize(PROBABILITY_QUANT)


def _participants_label(count):
    return "1 participante" if count == 1 else f"{count} participantes"


def _volume_label(amount):
    return f"{int(amount or 0)} O₵"


def _empty_summary():
    return {
        "enabled": False,
        "comments_created": 0,
        "predictions_created": 0,
        "skipped": 0,
        "errors": 0,
        "reason": "",
    }


def _site_config(cursor):
    cursor.execute("SELECT * FROM orynth_site_config WHERE singleton_key = 1")
    row = cursor.fetchone()
    if row:
        return dict(row)
    return {
        "ai_agents_enabled": False,
        "ai_commenting_enabled": False,
        "ai_predictions_enabled": False,
        "ai_llm_provider": "openai",
        "ai_llm_base_url": "https://api.openai.com/v1",
        "ai_model": "gpt-5.4-mini",
        "ai_high_reasoning_model": "gpt-5.5",
        "ai_market_cooldown_hours": 24,
        "ai_max_comments_per_market_per_day": 1,
        "ai_max_comments_per_cycle": 1,
        "ai_max_comment_attempts_per_cycle": 3,
        "ai_comment_candidate_limit": 200,
        "ai_max_comments_per_day": 20,
        "ai_comment_max_chars": 700,
        "ai_min_humans_for_prediction": 1,
        "ai_max_stake_oc": 25,
        "ai_max_predictions_per_cycle": 1,
        "ai_max_predictions_per_day": 10,
        "ai_skip_if_human_comments_recent": True,
        "ai_recent_human_comment_window_hours": 6,
        "ai_openai_timeout_seconds": 20,
        "ai_openai_max_retries": 1,
        "ai_paused_until": None,
        "ai_pause_reason": "",
    }


def _record_action(cursor, *, agent_id=None, market_id=None, action_type="cycle", status="skipped", reason="", payload=None, comment_id=None, prediction_id=None):
    cursor.execute(
        """
        INSERT INTO orynth_ai_agent_actions
            (agent_id, market_id, action_type, status, reason, payload_summary,
             prompt_template_version, prompt_hash, comment_id, prediction_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            agent_id,
            market_id,
            action_type,
            status,
            (reason or "")[:255],
            json.dumps(payload or {}, ensure_ascii=True, default=str),
            PROMPT_TEMPLATE_VERSION,
            template_hash(),
            comment_id,
            prediction_id,
            datetime.now(timezone.utc),
        ),
    )
    return cursor.fetchone()["id"]


def _active_agents(cursor, agent_type):
    cursor.execute(
        """
        SELECT a.*, u.username, u.first_name, u.is_bot
        FROM orynth_ai_agents a
        JOIN orynth_users u ON u.id = a.user_id
        WHERE a.is_active = true
          AND a.agent_type = %s
          AND u.is_bot = true
          AND u.is_active = true
        ORDER BY a.id ASC
        """,
        (agent_type,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _human_prediction_totals(cursor, market_id):
    cursor.execute(
        """
        SELECT COUNT(DISTINCT p.user_id) AS participants,
               COALESCE(SUM(p.stake_amount), 0) AS volume_oc
        FROM orynth_predictions p
        JOIN orynth_users u ON u.id = p.user_id
        WHERE p.market_id = %s
          AND p.status = 'open'
          AND u.is_bot = false
        """,
        (market_id,),
    )
    row = cursor.fetchone()
    return int(row["participants"] or 0), int(row["volume_oc"] or 0)


def _prediction_totals(cursor, market_id):
    cursor.execute(
        """
        SELECT
            COUNT(DISTINCT CASE WHEN u.is_bot = false THEN p.user_id END) AS human_participants,
            COUNT(DISTINCT CASE WHEN u.is_bot = true THEN p.user_id END) AS bot_participants,
            COALESCE(SUM(CASE WHEN u.is_bot = false THEN p.stake_amount ELSE 0 END), 0) AS human_volume_oc,
            COALESCE(SUM(CASE WHEN u.is_bot = true THEN p.stake_amount ELSE 0 END), 0) AS bot_volume_oc,
            COALESCE(SUM(p.stake_amount), 0) AS total_volume_oc
        FROM orynth_predictions p
        JOIN orynth_users u ON u.id = p.user_id
        WHERE p.market_id = %s
          AND p.status = 'open'
        """,
        (market_id,),
    )
    row = cursor.fetchone()
    return {
        "human_participants": int(row["human_participants"] or 0),
        "bot_participants": int(row["bot_participants"] or 0),
        "human_volume_oc": int(row["human_volume_oc"] or 0),
        "bot_volume_oc": int(row["bot_volume_oc"] or 0),
        "total_volume_oc": int(row["total_volume_oc"] or 0),
    }


def market_public_metrics(cursor, market_id):
    totals = _prediction_totals(cursor, market_id)
    return {
        **totals,
        "participants": _participants_label(totals["human_participants"]),
        "volume_oc": _volume_label(totals["human_volume_oc"]),
        "human_volume_label": _volume_label(totals["human_volume_oc"]),
        "bot_volume_label": _volume_label(totals["bot_volume_oc"]),
        "total_volume_label": _volume_label(totals["total_volume_oc"]),
    }


def refresh_market_public_metrics(cursor, market_id):
    metrics = market_public_metrics(cursor, market_id)
    cursor.execute(
        """
        UPDATE orynth_markets
        SET volume_oc = %s,
            participants = %s,
            updated_at = %s
        WHERE id = %s
        """,
        (metrics["volume_oc"], metrics["participants"], datetime.now(timezone.utc), market_id),
    )
    return metrics


def _recalculate_market_probabilities(cursor, market_id):
    cursor.execute(
        """
        SELECT o.id, o.display_order,
               %s + COALESCE(SUM(p.weight_at_entry), 0) AS total_weight
        FROM orynth_market_options o
        LEFT JOIN orynth_predictions p ON p.market_option_id = o.id AND p.status = 'open'
        WHERE o.market_id = %s
        GROUP BY o.id, o.display_order
        ORDER BY o.display_order ASC, o.id ASC
        """,
        (BASE_PREDICTION_WEIGHT, market_id),
    )
    rows = cursor.fetchall()
    total_weight = sum(int(row["total_weight"] or 0) for row in rows)
    if not rows or total_weight <= 0:
        return
    probabilities = []
    for row in rows:
        probability = (Decimal(int(row["total_weight"] or 0)) * Decimal("100") / Decimal(total_weight)).quantize(PROBABILITY_QUANT)
        probabilities.append((row["id"], probability))
        cursor.execute("UPDATE orynth_market_options SET probability_exact = %s, updated_at = %s WHERE id = %s", (probability, datetime.now(timezone.utc), row["id"]))
    primary = probabilities[0][1]
    secondary = probabilities[1][1] if len(probabilities) > 1 else Decimal("0.0000")
    cursor.execute(
        """
        UPDATE orynth_markets
        SET primary_probability_exact = %s,
            secondary_probability_exact = %s,
            updated_at = %s
        WHERE id = %s
        """,
        (primary, secondary, datetime.now(timezone.utc), market_id),
    )


def _comment_daily_count(cursor, agent_id=None, market_id=None, now=None):
    now = now or datetime.now(timezone.utc)
    where = ["action_type = 'comment'", "status = 'created'", "created_at >= %s"]
    params = [now - timedelta(hours=24)]
    if agent_id:
        where.append("agent_id = %s")
        params.append(agent_id)
    if market_id:
        where.append("market_id = %s")
        params.append(market_id)
    cursor.execute(f"SELECT COUNT(*) AS total FROM orynth_ai_agent_actions WHERE {' AND '.join(where)}", params)
    return int(cursor.fetchone()["total"] or 0)


def _prediction_daily_count(cursor, agent_id=None, now=None):
    now = now or datetime.now(timezone.utc)
    where = ["action_type = 'prediction'", "status = 'created'", "created_at >= %s"]
    params = [now - timedelta(hours=24)]
    if agent_id:
        where.append("agent_id = %s")
        params.append(agent_id)
    cursor.execute(f"SELECT COUNT(*) AS total FROM orynth_ai_agent_actions WHERE {' AND '.join(where)}", params)
    return int(cursor.fetchone()["total"] or 0)


def _recent_human_comment_exists(cursor, market_id, config, now):
    if not config.get("ai_skip_if_human_comments_recent", True):
        return False
    window = now - timedelta(hours=int(config.get("ai_recent_human_comment_window_hours") or 6))
    cursor.execute(
        """
        SELECT 1
        FROM orynth_market_comments mc
        JOIN orynth_users u ON u.id = mc.author_id
        WHERE mc.market_id = %s
          AND mc.status = 'visible'
          AND u.is_bot = false
          AND mc.created_at >= %s
        LIMIT 1
        """,
        (market_id, window),
    )
    return bool(cursor.fetchone())


def _recent_ai_comment_exists(cursor, market_id, now, cooldown_hours):
    if int(cooldown_hours or 0) <= 0:
        return False
    window = now - timedelta(hours=int(cooldown_hours))
    cursor.execute(
        """
        SELECT 1
        FROM orynth_market_comments mc
        JOIN orynth_users u ON u.id = mc.author_id
        WHERE mc.market_id = %s
          AND mc.status = 'visible'
          AND u.is_bot = true
          AND mc.created_at >= %s
        LIMIT 1
        """,
        (market_id, window),
    )
    return bool(cursor.fetchone())


def _candidate_comment_markets(cursor, config, now, cooldown_hours=None):
    candidate_limit = max(1, int(config.get("ai_comment_candidate_limit") or 200))
    cursor.execute(
        """
        SELECT m.id, m.slug, m.title, m.summary, m.kind, m.resolution_criteria, m.source,
               m.close_at, m.is_featured, m.view_count, m.share_count,
               c.name AS category, sc.name AS subcategory, COALESCE(ev.name, 'Geral') AS event
        FROM orynth_markets m
        JOIN orynth_market_categories c ON c.id = m.category_id
        JOIN orynth_market_subcategories sc ON sc.id = m.subcategory_id
        LEFT JOIN orynth_market_events ev ON ev.id = m.event_id
        WHERE m.status = 'open'
        ORDER BY m.is_featured DESC, m.view_count DESC, m.close_at ASC NULLS LAST, m.id ASC
        LIMIT %s
        """,
        (candidate_limit,),
    )
    candidates = []
    for market in cursor.fetchall():
        market_id = market["id"]
        if _comment_daily_count(cursor, market_id=market_id, now=now) >= int(config.get("ai_max_comments_per_market_per_day") or 1):
            continue
        if _recent_ai_comment_exists(cursor, market_id, now, cooldown_hours or config.get("ai_market_cooldown_hours") or 24):
            continue
        if _recent_human_comment_exists(cursor, market_id, config, now):
            continue
        candidates.append(dict(market))
    return candidates


def _recent_comments(cursor, market_id):
    cursor.execute(
        """
        SELECT mc.body, mc.created_at, u.username, u.is_bot
        FROM orynth_market_comments mc
        JOIN orynth_users u ON u.id = mc.author_id
        WHERE mc.market_id = %s
          AND mc.status = 'visible'
        ORDER BY mc.created_at DESC, mc.id DESC
        LIMIT 5
        """,
        (market_id,),
    )
    return [
        {
            "author": row["username"],
            "author_is_bot": bool(row["is_bot"]),
            "body": row["body"][:300],
            "created_at": row["created_at"].isoformat(),
        }
        for row in cursor.fetchall()
    ]


def _market_options_context(cursor, market_id):
    cursor.execute(
        """
        SELECT id, label, probability_exact, hint
        FROM orynth_market_options
        WHERE market_id = %s
        ORDER BY display_order ASC, id ASC
        """,
        (market_id,),
    )
    return [
        {
            "id": row["id"],
            "label": row["label"],
            "probability_exact": float(_decimal_probability(row["probability_exact"])),
            "hint": row["hint"] or "",
        }
        for row in cursor.fetchall()
    ]


def _safe_comment_text(value, max_chars):
    text = " ".join(str(value or "").strip().split())
    text = re.sub(r"^(?:agente\s+ia\s+oficial\s+da\s+orynth|ia\s+oficial(?:\s+da\s+orynth)?)\s*[:\-–—]\s*", "", text, flags=re.IGNORECASE).strip()
    forbidden = ["eu apostei", "minha aposta", "como humano", "minha experiencia", "minha experiência", "garantido", "certeza de lucro"]
    lowered = text.lower()
    if not text or any(term in lowered for term in forbidden):
        return ""
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


def _run_comment_cycle(cursor, config, summary, now):
    if not config.get("ai_commenting_enabled"):
        summary["skipped"] += 1
        _record_action(cursor, action_type="cycle", status="skipped", reason="ai_commenting_disabled")
        return
    agents = _active_agents(cursor, "analyst")
    if not agents:
        summary["skipped"] += 1
        _record_action(cursor, action_type="cycle", status="skipped", reason="no_active_analyst_agent")
        return
    max_cycle = int(config.get("ai_max_comments_per_cycle") or 1)
    max_attempts = max(1, int(config.get("ai_max_comment_attempts_per_cycle") or 3))
    max_day = int(config.get("ai_max_comments_per_day") or 20)
    if _comment_daily_count(cursor, now=now) >= max_day:
        summary["skipped"] += 1
        _record_action(cursor, action_type="comment", status="skipped", reason="global_daily_comment_limit")
        return
    created = 0
    for agent in agents:
        if created >= max_cycle:
            break
        agent_limit = int(agent.get("max_comments_per_day") or max_day)
        if _comment_daily_count(cursor, agent_id=agent["id"], now=now) >= agent_limit:
            _record_action(cursor, agent_id=agent["id"], action_type="comment", status="skipped", reason="agent_daily_comment_limit")
            summary["skipped"] += 1
            continue
        markets = _candidate_comment_markets(cursor, config, now, agent.get("cooldown_hours"))
        if not markets:
            _record_action(cursor, agent_id=agent["id"], action_type="comment", status="skipped", reason="no_eligible_market")
            summary["skipped"] += 1
            continue
        attempts = 0
        for index, market in enumerate(markets):
            if created >= max_cycle:
                break
            if _comment_daily_count(cursor, now=now) >= max_day:
                _record_action(cursor, agent_id=agent["id"], action_type="comment", status="skipped", reason="global_daily_comment_limit")
                summary["skipped"] += 1
                break
            if attempts >= max_attempts:
                _record_action(cursor, agent_id=agent["id"], action_type="comment", status="skipped", reason="comment_attempt_limit_reached", payload={"attempts": attempts, "attempt_limit": max_attempts, "candidate_count": len(markets), "remaining_candidates": len(markets) - index})
                summary["skipped"] += 1
                break
            attempts += 1
            comments = _recent_comments(cursor, market["id"])
            market_context = {
                **market,
                "options": _market_options_context(cursor, market["id"]),
                **market_public_metrics(cursor, market["id"]),
            }
            prompt = build_comment_prompt(agent=agent, market=market_context, comments=comments, config=config)
            try:
                llm_result = request_market_comment(config=config, prompt=prompt)
                if not bool(llm_result.get("should_publish")):
                    _record_action(cursor, agent_id=agent["id"], market_id=market["id"], action_type="comment", status="skipped", reason="llm_should_publish_false", payload={"confidence": llm_result.get("confidence"), "risk_flags": llm_result.get("risk_flags", [])})
                    summary["skipped"] += 1
                    continue
                body = _safe_comment_text(llm_result.get("comment"), int(config.get("ai_comment_max_chars") or 700))
                if not body:
                    _record_action(cursor, agent_id=agent["id"], market_id=market["id"], action_type="comment", status="failed", reason="comment_validation_failed", payload={"risk_flags": llm_result.get("risk_flags", [])})
                    summary["errors"] += 1
                    continue
                cursor.execute(
                    """
                    INSERT INTO orynth_market_comments
                        (market_id, author_id, body, status, moderation_note, moderated_by_id, moderated_at, created_at, updated_at)
                    VALUES (%s, %s, %s, 'visible', '', NULL, NULL, %s, %s)
                    RETURNING id
                    """,
                    (market["id"], agent["user_id"], body, now, now),
                )
                comment_id = cursor.fetchone()["id"]
                _record_action(cursor, agent_id=agent["id"], market_id=market["id"], action_type="comment", status="created", reason="comment_created", payload={"confidence": llm_result.get("confidence"), "risk_flags": llm_result.get("risk_flags", [])}, comment_id=comment_id)
                cursor.execute("UPDATE orynth_ai_agents SET last_action_at = %s, last_error = '', updated_at = %s WHERE id = %s", (now, now, agent["id"]))
                created += 1
                summary["comments_created"] += 1
            except AgentLLMError as exc:
                _record_action(cursor, agent_id=agent["id"], market_id=market["id"], action_type="comment", status="failed", reason="llm_error", payload={"error": str(exc)[:300]})
                cursor.execute("UPDATE orynth_ai_agents SET last_error = %s, updated_at = %s WHERE id = %s", (str(exc)[:1000], now, agent["id"]))
                summary["errors"] += 1
                return


def _candidate_prediction_market(cursor, config, now, min_humans=None, user_id=None):
    cursor.execute(
        """
        SELECT id, slug, title
        FROM orynth_markets
        WHERE status = 'open'
        ORDER BY is_featured DESC, view_count DESC, id ASC
        LIMIT 50
        """
    )
    for market in cursor.fetchall():
        humans, _volume = _human_prediction_totals(cursor, market["id"])
        if humans < int(min_humans or config.get("ai_min_humans_for_prediction") or 1):
            continue
        if user_id:
            cursor.execute("SELECT 1 FROM orynth_predictions WHERE user_id = %s AND market_id = %s LIMIT 1", (user_id, market["id"]))
            if cursor.fetchone():
                continue
        return dict(market)
    return None


def _conservative_option(cursor, market_id):
    cursor.execute(
        """
        SELECT o.id, o.probability_exact,
               %s + COALESCE(SUM(p.weight_at_entry), 0) AS total_weight
        FROM orynth_market_options o
        LEFT JOIN orynth_predictions p ON p.market_option_id = o.id AND p.status = 'open'
        WHERE o.market_id = %s
        GROUP BY o.id, o.probability_exact, o.display_order
        ORDER BY total_weight ASC, o.probability_exact ASC, o.display_order ASC, o.id ASC
        LIMIT 1
        """,
        (BASE_PREDICTION_WEIGHT, market_id),
    )
    return cursor.fetchone()


def _record_wallet_entry(cursor, user_id, *, entry_type, amount, direction, description, reference_type="", reference_id=""):
    now = datetime.now(timezone.utc)
    cursor.execute(
        """
        INSERT INTO orynth_wallet_ledger
            (user_id, entry_type, amount, direction, description, reference_type, reference_id, created_by_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, %s)
        """,
        (user_id, entry_type, amount, direction, description, reference_type, reference_id, now),
    )
    cursor.execute("SELECT user_id FROM orynth_wallet_balances WHERE user_id = %s", (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO orynth_wallet_balances (user_id, available_oc, locked_oc, total_earned_oc, updated_at)
            VALUES (%s, 0, 0, 0, %s)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id, now),
        )
    if direction == "lock":
        cursor.execute(
            """
            UPDATE orynth_wallet_balances
            SET available_oc = available_oc - %s,
                locked_oc = locked_oc + %s,
                updated_at = %s
            WHERE user_id = %s
            """,
            (amount, amount, now, user_id),
        )


def _create_bot_prediction(cursor, agent, market, option, stake):
    user_id = agent["user_id"]
    cursor.execute("SELECT id FROM orynth_predictions WHERE user_id = %s AND market_id = %s", (user_id, market["id"]))
    if cursor.fetchone():
        raise ValueError("bot_already_predicted_market")
    cursor.execute("SELECT available_oc FROM orynth_wallet_balances WHERE user_id = %s FOR UPDATE", (user_id,))
    balance = cursor.fetchone()
    if not balance or int(balance["available_oc"] or 0) < stake:
        raise ValueError("insufficient_bot_balance")
    cursor.execute("SELECT reputation_score FROM orynth_user_reputations WHERE user_id = %s", (user_id,))
    reputation = cursor.fetchone()
    reputation_score = int(reputation["reputation_score"] if reputation else INITIAL_REPUTATION)
    probability_at_entry = max(_decimal_probability(option["probability_exact"]), PROBABILITY_QUANT)
    weight_at_entry = reputation_score * stake
    potential_payout = int((Decimal(stake) * Decimal("100") / probability_at_entry).to_integral_value())
    now = datetime.now(timezone.utc)
    cursor.execute(
        """
        INSERT INTO orynth_predictions
            (user_id, market_id, market_option_id, stake_amount, probability_at_entry,
             weight_at_entry, potential_payout, status, won, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'open', NULL, %s, %s)
        RETURNING id
        """,
        (user_id, market["id"], option["id"], stake, probability_at_entry, weight_at_entry, potential_payout, now, now),
    )
    prediction_id = cursor.fetchone()["id"]
    _record_wallet_entry(
        cursor,
        user_id,
        entry_type="prediction_stake_lock",
        amount=stake,
        direction="lock",
        description=f"Stake bot oficial em previsão: {market['slug']}",
        reference_type="prediction",
        reference_id=str(prediction_id),
    )
    _recalculate_market_probabilities(cursor, market["id"])
    refresh_market_public_metrics(cursor, market["id"])
    return prediction_id


def _run_prediction_cycle(cursor, config, summary, now):
    if not config.get("ai_predictions_enabled"):
        summary["skipped"] += 1
        _record_action(cursor, action_type="prediction", status="skipped", reason="ai_predictions_disabled")
        return
    agents = _active_agents(cursor, "liquidity")
    if not agents:
        summary["skipped"] += 1
        _record_action(cursor, action_type="prediction", status="skipped", reason="no_active_liquidity_agent")
        return
    max_cycle = int(config.get("ai_max_predictions_per_cycle") or 1)
    max_day = int(config.get("ai_max_predictions_per_day") or 10)
    if _prediction_daily_count(cursor, now=now) >= max_day:
        summary["skipped"] += 1
        _record_action(cursor, action_type="prediction", status="skipped", reason="global_daily_prediction_limit")
        return
    created = 0
    for agent in agents:
        if created >= max_cycle:
            break
        agent_limit = int(agent.get("max_predictions_per_day") or max_day)
        if _prediction_daily_count(cursor, agent_id=agent["id"], now=now) >= agent_limit:
            summary["skipped"] += 1
            _record_action(cursor, agent_id=agent["id"], action_type="prediction", status="skipped", reason="agent_daily_prediction_limit")
            continue
        min_humans = int(agent.get("min_humans_for_prediction") or config.get("ai_min_humans_for_prediction") or 1)
        market = _candidate_prediction_market(cursor, config, now, min_humans=min_humans, user_id=agent["user_id"])
        if not market:
            summary["skipped"] += 1
            _record_action(cursor, agent_id=agent["id"], action_type="prediction", status="skipped", reason="no_eligible_market")
            continue
        humans, _volume = _human_prediction_totals(cursor, market["id"])
        if humans <= 0:
            summary["skipped"] += 1
            _record_action(cursor, agent_id=agent["id"], market_id=market["id"], action_type="prediction", status="skipped", reason="no_human_participants")
            continue
        option = _conservative_option(cursor, market["id"])
        stake = min(int(config.get("ai_max_stake_oc") or 25), int(agent.get("max_stake_oc") or config.get("ai_max_stake_oc") or 25))
        try:
            prediction_id = _create_bot_prediction(cursor, agent, market, option, stake)
            _record_action(cursor, agent_id=agent["id"], market_id=market["id"], action_type="prediction", status="created", reason="prediction_created", payload={"stake_oc": stake, "option_id": option["id"], "human_participants": humans, "min_humans": min_humans}, prediction_id=prediction_id)
            cursor.execute("UPDATE orynth_ai_agents SET last_action_at = %s, last_error = '', updated_at = %s WHERE id = %s", (now, now, agent["id"]))
            created += 1
            summary["predictions_created"] += 1
        except Exception as exc:
            _record_action(cursor, agent_id=agent["id"], market_id=market["id"], action_type="prediction", status="failed", reason=str(exc)[:255], payload={"stake_oc": stake})
            cursor.execute("UPDATE orynth_ai_agents SET last_error = %s, updated_at = %s WHERE id = %s", (str(exc)[:1000], now, agent["id"]))
            summary["errors"] += 1


def run_ai_agent_cycle(cursor, *, now=None):
    now = now or datetime.now(timezone.utc)
    summary = _empty_summary()
    config = _site_config(cursor)
    summary["enabled"] = bool(config.get("ai_agents_enabled"))
    if not config.get("ai_agents_enabled"):
        summary["reason"] = "ai_agents_disabled"
        _record_action(cursor, action_type="cycle", status="skipped", reason="ai_agents_disabled")
        return summary
    paused_until = config.get("ai_paused_until")
    if paused_until and paused_until > now:
        summary["reason"] = "ai_paused"
        _record_action(cursor, action_type="cycle", status="skipped", reason="ai_paused", payload={"paused_until": paused_until.isoformat(), "pause_reason": config.get("ai_pause_reason") or ""})
        return summary
    try:
        _run_comment_cycle(cursor, config, summary, now)
        _run_prediction_cycle(cursor, config, summary, now)
        _record_action(cursor, action_type="cycle", status="created", reason="cycle_completed", payload=summary)
    except Exception as exc:
        summary["errors"] += 1
        summary["reason"] = "cycle_error"
        _record_action(cursor, action_type="cycle", status="failed", reason="cycle_error", payload={"error": str(exc)[:300]})
    return summary


def ai_health_summary(cursor, *, now=None):
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(hours=24)
    config = _site_config(cursor)
    cursor.execute(
        """
        SELECT created_at
        FROM orynth_ai_agent_actions
        WHERE action_type = 'cycle'
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
    )
    last_cycle = cursor.fetchone()
    cursor.execute(
        """
        SELECT created_at
        FROM orynth_ai_agent_actions
        WHERE action_type = 'cycle'
          AND status = 'created'
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
    )
    last_success = cursor.fetchone()
    cursor.execute(
        """
        SELECT reason, payload_summary, created_at
        FROM orynth_ai_agent_actions
        WHERE status = 'failed'
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
    )
    last_error = cursor.fetchone()
    cursor.execute(
        """
        SELECT action_type, status, COUNT(*) AS total
        FROM orynth_ai_agent_actions
        WHERE created_at >= %s
        GROUP BY action_type, status
        """,
        (since,),
    )
    counts = {(row["action_type"], row["status"]): int(row["total"] or 0) for row in cursor.fetchall()}
    cursor.execute("SELECT COUNT(*) AS total FROM orynth_ai_agents WHERE is_active = true")
    active_agents = int(cursor.fetchone()["total"] or 0)
    paused_until = config.get("ai_paused_until")
    paused = bool(paused_until and paused_until > now)
    if not config.get("ai_agents_enabled"):
        status = "inactive"
        label = "Inativo"
    elif paused:
        status = "paused"
        label = "Pausado"
    elif last_error and (not last_success or last_error["created_at"] > last_success["created_at"]):
        status = "error"
        label = "Com erro"
    elif last_cycle:
        status = "active"
        label = "Ativo"
    else:
        status = "missing"
        label = "Sem sinal"
    return {
        "status": status,
        "status_label": label,
        "active_agents": active_agents,
        "last_cycle_at": last_cycle["created_at"].isoformat() if last_cycle else "",
        "last_success_at": last_success["created_at"].isoformat() if last_success else "",
        "last_error_at": last_error["created_at"].isoformat() if last_error else "",
        "last_error": last_error["reason"] if last_error else "",
        "errors_24h": counts.get(("cycle", "failed"), 0) + counts.get(("comment", "failed"), 0) + counts.get(("prediction", "failed"), 0),
        "comments_created_24h": counts.get(("comment", "created"), 0),
        "predictions_created_24h": counts.get(("prediction", "created"), 0),
        "skipped_24h": counts.get(("cycle", "skipped"), 0) + counts.get(("comment", "skipped"), 0) + counts.get(("prediction", "skipped"), 0),
        "openai_key_configured": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
        "config": {
            "ai_agents_enabled": bool(config.get("ai_agents_enabled")),
            "ai_commenting_enabled": bool(config.get("ai_commenting_enabled")),
            "ai_predictions_enabled": bool(config.get("ai_predictions_enabled")),
            "ai_llm_provider": config.get("ai_llm_provider") or "openai",
            "ai_llm_base_url": config.get("ai_llm_base_url") or "https://api.openai.com/v1",
            "ai_model": config.get("ai_model") or "gpt-5.4-mini",
            "ai_max_comments_per_cycle": int(config.get("ai_max_comments_per_cycle") or 1),
            "ai_max_comment_attempts_per_cycle": int(config.get("ai_max_comment_attempts_per_cycle") or 3),
            "ai_comment_candidate_limit": int(config.get("ai_comment_candidate_limit") or 200),
            "ai_max_predictions_per_cycle": int(config.get("ai_max_predictions_per_cycle") or 1),
            "ai_min_humans_for_prediction": int(config.get("ai_min_humans_for_prediction") or 1),
            "ai_max_stake_oc": int(config.get("ai_max_stake_oc") or 25),
        },
    }
