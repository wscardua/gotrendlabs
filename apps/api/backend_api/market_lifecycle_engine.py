from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status

from apps.api.backend_api.badge_engine import BadgeAwardEngine
from apps.api.backend_api.email_outbox import enqueue_user_email, public_url


INITIAL_REPUTATION = 100
PROBABILITY_QUANT = Decimal("0.0001")
REPUTATION_K_FACTOR = Decimal("10")


class MarketLifecycleEngine:
    def __init__(
        self,
        cursor,
        *,
        staff_id,
        record_wallet_entry,
        record_admin_event,
        ensure_user_core,
        validate_publishable,
    ):
        self.cursor = cursor
        self.staff_id = staff_id
        self.record_wallet_entry = record_wallet_entry
        self.record_admin_event = record_admin_event
        self.ensure_user_core = ensure_user_core
        self.validate_publishable = validate_publishable

    def publish_market(self, row, slug, note=""):
        if row["status"] == "open":
            return
        if row["status"] not in {"draft", "scheduled"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Apenas rascunhos ou mercados agendados podem ser publicados.",
            )
        self.validate_publishable(self.cursor, row["id"])
        self.cursor.execute(
            """
            UPDATE gotrendlabs_markets
            SET status = 'open', status_label = 'Aberto', updated_by_id = %s, updated_at = %s
            WHERE id = %s
            """,
            (self.staff_id, datetime.now(timezone.utc), row["id"]),
        )
        self.record_admin_event(self.cursor, self.staff_id, "market.publish", "market", slug, note)

    def cancel_market(self, row, slug, note=""):
        if row["status"] == "canceled":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Mercado já cancelado.")
        now = datetime.now(timezone.utc)
        if row["status"] == "resolved":
            self._undo_resolved_market_predictions(row["id"], slug, now)
            self.cursor.execute(
                """
                UPDATE gotrendlabs_markets
                SET status = 'locked',
                    status_label = 'Fechado',
                    winning_option_id = NULL,
                    resolved_at = NULL,
                    resolution_timezone = '',
                    resolution_type = '',
                    resolution_note = '',
                    admin_notes = %s,
                    updated_by_id = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (note, self.staff_id, now, row["id"]),
            )
            self.record_admin_event(self.cursor, self.staff_id, "market.resolution_undo", "market", slug, note)
            return

        self._refund_market_predictions(row["id"], slug, now)
        self._assert_no_open_predictions(row["id"], slug)
        self.cursor.execute(
            """
            UPDATE gotrendlabs_markets
            SET status = 'canceled',
                status_label = 'Cancelado',
                is_featured = false,
                canceled_at = %s,
                admin_notes = %s,
                updated_by_id = %s,
                updated_at = %s
            WHERE id = %s
            """,
            (now, note, self.staff_id, now, row["id"]),
        )
        self.record_admin_event(self.cursor, self.staff_id, "market.cancel", "market", slug, note)

    def resolve_market(self, row, slug, payload):
        if row["status"] != "locked":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Apenas mercados fechados podem ser resolvidos.",
            )
        evidence = (payload.source_url or "").strip()
        note = (payload.note or "").strip()
        if not evidence and not note:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resolução exige fonte pública ou justificativa operacional.",
            )
        self.cursor.execute(
            """
            SELECT id, label
            FROM gotrendlabs_market_options
            WHERE id = %s
              AND market_id = %s
            """,
            (payload.winning_option_id, row["id"]),
        )
        winning_option = self.cursor.fetchone()
        if not winning_option:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Opção vencedora inválida para este mercado.",
            )

        now = datetime.now(timezone.utc)
        resolution_timezone = (payload.resolution_timezone or row["close_timezone"] or "UTC").strip()
        try:
            target_timezone = ZoneInfo(resolution_timezone)
        except ZoneInfoNotFoundError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Timezone de resolução inválido.")
        resolved_at = payload.resolved_at or now
        if resolved_at.tzinfo is None:
            resolved_at = resolved_at.replace(tzinfo=target_timezone)
        resolved_at = resolved_at.astimezone(timezone.utc)
        resolution_note = note
        if evidence:
            resolution_note = f"{note}\nFonte: {evidence}".strip()
        self.cursor.execute(
            """
            UPDATE gotrendlabs_markets
            SET status = 'resolved',
                status_label = 'Resolvido',
                primary_outcome = %s,
                resolution_type = 'manual',
                resolved_at = %s,
                resolution_timezone = %s,
                winning_option_id = %s,
                resolution_note = %s,
                updated_by_id = %s,
                updated_at = %s
            WHERE id = %s
            """,
            (winning_option["label"], resolved_at, resolution_timezone, winning_option["id"], resolution_note, self.staff_id, now, row["id"]),
        )
        self._resolve_market_predictions(row["id"], winning_option["id"], slug, now)
        self._notify_market_participants(
            row["id"],
            event_type="market_resolved",
            source_key=f"market_resolved:{row['id']}",
            title="Mercado resolvido",
            body=f"O mercado {self._market_title(row['id'], slug)} foi resolvido.",
            metadata={
                "winning_option_id": winning_option["id"],
                "winning_option": winning_option["label"],
                "resolved_at": resolved_at.isoformat(),
            },
            actor_id=self.staff_id,
        )
        self.record_admin_event(self.cursor, self.staff_id, "market.resolve", "market", slug, resolution_note)

    def lock_market(self, row, slug, note=""):
        if row["auto_close_enabled"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Este mercado está configurado para fechamento automático pelo daemon.",
            )
        if row["status"] not in {"open", "scheduled"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Apenas mercados abertos ou agendados podem ser fechados manualmente.",
            )
        now = datetime.now(timezone.utc)
        self.cursor.execute(
            """
            UPDATE gotrendlabs_markets
            SET status = 'locked',
                status_label = 'Fechado',
                admin_notes = %s,
                updated_by_id = %s,
                updated_at = %s
            WHERE id = %s
            """,
            (note, self.staff_id, now, row["id"]),
        )
        self._notify_market_participants(
            row["id"],
            event_type="market_locked",
            source_key=f"market_locked:{row['id']}",
            title="Mercado fechado",
            body=f"O mercado {self._market_title(row['id'], slug)} foi fechado para novas previsões.",
            actor_id=self.staff_id,
        )
        self.record_admin_event(self.cursor, self.staff_id, "market.lock", "market", slug, note)

    def lock_market_automatically(self, row, slug, note="", now=None):
        if not row["auto_close_enabled"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Este mercado está configurado para fechamento manual.",
            )
        if row["status"] not in {"open", "scheduled"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Apenas mercados abertos ou agendados podem ser fechados automaticamente.",
            )
        now = now or datetime.now(timezone.utc)
        self.cursor.execute(
            """
            UPDATE gotrendlabs_markets
            SET status = 'locked',
                status_label = 'Fechado',
                admin_notes = %s,
                updated_by_id = NULL,
                updated_at = %s
            WHERE id = %s
            """,
            (note, now, row["id"]),
        )
        self._notify_market_participants(
            row["id"],
            event_type="market_locked",
            source_key=f"market_locked:{row['id']}",
            title="Mercado fechado",
            body=f"O mercado {self._market_title(row['id'], slug)} foi fechado para novas previsões.",
        )
        self.record_admin_event(self.cursor, None, "market.lock", "market", slug, note)

    def reconcile_canceled_market_refunds(self, market_id, slug, now):
        return self._refund_market_predictions(market_id, slug, now)

    def _market_title(self, market_id, fallback):
        self.cursor.execute("SELECT title FROM gotrendlabs_markets WHERE id = %s", (market_id,))
        market = self.cursor.fetchone()
        return (market and market["title"]) or fallback

    def _participant_user_ids(self, market_id):
        self.cursor.execute(
            """
            SELECT DISTINCT p.user_id
            FROM gotrendlabs_predictions p
            JOIN gotrendlabs_users u ON u.id = p.user_id
            WHERE p.market_id = %s
              AND u.is_bot = false
            ORDER BY p.user_id ASC
            """,
            (market_id,),
        )
        return [row["user_id"] for row in self.cursor.fetchall()]

    def _notify_market_participants(self, market_id, *, event_type, source_key, title, body, metadata=None, actor_id=None):
        market_title = self._market_title(market_id, str(market_id))
        email_key = {"market_locked": "market.locked", "market_resolved": "market.resolved"}.get(event_type)
        for recipient_id in self._participant_user_ids(market_id):
            self.cursor.execute(
                """
                INSERT INTO gotrendlabs_user_notifications
                    (recipient_id, actor_id, market_id, comment_id, event_type, source_key, title, body, is_read, read_at, metadata, created_at)
                VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, false, NULL, %s::jsonb, %s)
                ON CONFLICT (recipient_id, source_key) DO NOTHING
                """,
                (
                    recipient_id,
                    actor_id,
                    market_id,
                    event_type,
                    source_key,
                    title,
                    body,
                    json.dumps(metadata or {}),
                    datetime.now(timezone.utc),
                ),
            )
            if email_key:
                enqueue_user_email(
                    self.cursor,
                    event_type=email_key,
                    user_id=recipient_id,
                    template_key=email_key,
                    context={
                        "market_title": market_title,
                        "market_url": public_url(f"/markets/{self._market_slug(market_id)}/"),
                        "winning_option": (metadata or {}).get("winning_option", ""),
                    },
                    idempotency_key=f"{email_key}:{recipient_id}:{market_id}",
                )

    def _market_slug(self, market_id):
        self.cursor.execute("SELECT slug FROM gotrendlabs_markets WHERE id = %s", (market_id,))
        market = self.cursor.fetchone()
        return (market and market["slug"]) or str(market_id)

    def _accuracy_indicator(self, user_id):
        self.cursor.execute(
            """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(CASE WHEN won = true THEN 1 ELSE 0 END), 0) AS wins
            FROM gotrendlabs_predictions
            WHERE user_id = %s
              AND status = 'resolved'
            """,
            (user_id,),
        )
        row = self.cursor.fetchone()
        total = int(row["total"] or 0)
        if total <= 0:
            return "0%"
        wins = int(row["wins"] or 0)
        return f"{int((Decimal(wins) * Decimal('100') / Decimal(total)).to_integral_value(rounding=ROUND_HALF_UP))}%"

    def _apply_reputation_delta(self, user_id, probability_at_entry, won, now):
        self.ensure_user_core(self.cursor, user_id)
        probability = max(Decimal("0"), min(Decimal("1"), self._decimal_probability(probability_at_entry) / Decimal("100")))
        delta = REPUTATION_K_FACTOR * (Decimal("1") - probability) if won else -(REPUTATION_K_FACTOR * probability)
        rounded_delta = int(delta.to_integral_value(rounding=ROUND_HALF_UP))
        self.cursor.execute(
            """
            SELECT reputation_score, streak
            FROM gotrendlabs_user_reputations
            WHERE user_id = %s
            FOR UPDATE
            """,
            (user_id,),
        )
        reputation = self.cursor.fetchone()
        current_score = int(reputation["reputation_score"] if reputation else INITIAL_REPUTATION)
        current_streak = int(reputation["streak"] if reputation else 0)
        new_score = max(0, current_score + rounded_delta)
        new_streak = current_streak + 1 if won else 0
        self.cursor.execute(
            """
            UPDATE gotrendlabs_user_reputations
            SET reputation_score = %s,
                resolved_predictions_count = (
                    SELECT COUNT(*)
                    FROM gotrendlabs_predictions
                    WHERE user_id = %s
                      AND status = 'resolved'
                ),
                accuracy_indicator = %s,
                streak = %s,
                last_updated_at = %s
            WHERE user_id = %s
            """,
            (new_score, user_id, self._accuracy_indicator(user_id), new_streak, now, user_id),
        )

    def _recalculate_user_reputation(self, user_id, now):
        self.ensure_user_core(self.cursor, user_id)
        self.cursor.execute(
            """
            SELECT probability_at_entry, won
            FROM gotrendlabs_predictions
            WHERE user_id = %s
              AND status = 'resolved'
            ORDER BY updated_at ASC, id ASC
            """,
            (user_id,),
        )
        rows = self.cursor.fetchall()
        score = INITIAL_REPUTATION
        for prediction in rows:
            probability = max(Decimal("0"), min(Decimal("1"), self._decimal_probability(prediction["probability_at_entry"]) / Decimal("100")))
            delta = REPUTATION_K_FACTOR * (Decimal("1") - probability) if prediction["won"] else -(REPUTATION_K_FACTOR * probability)
            score = max(0, score + int(delta.to_integral_value(rounding=ROUND_HALF_UP)))

        self.cursor.execute(
            """
            SELECT won
            FROM gotrendlabs_predictions
            WHERE user_id = %s
              AND status = 'resolved'
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        )
        streak = 0
        for prediction in self.cursor.fetchall():
            if not prediction["won"]:
                break
            streak += 1

        self.cursor.execute(
            """
            UPDATE gotrendlabs_user_reputations
            SET reputation_score = %s,
                resolved_predictions_count = %s,
                accuracy_indicator = %s,
                streak = %s,
                last_updated_at = %s
            WHERE user_id = %s
            """,
            (score, len(rows), self._accuracy_indicator(user_id), streak, now, user_id),
        )

    def _resolve_market_predictions(self, market_id, winning_option_id, slug, now):
        self.cursor.execute(
            """
            SELECT p.id, p.user_id, p.market_option_id, p.stake_amount, p.probability_at_entry,
                   p.potential_payout, u.is_bot
            FROM gotrendlabs_predictions p
            JOIN gotrendlabs_users u ON u.id = p.user_id
            WHERE p.market_id = %s
              AND p.status = 'open'
            ORDER BY p.id ASC
            FOR UPDATE
            """,
            (market_id,),
        )
        predictions = self.cursor.fetchall()
        for prediction in predictions:
            won = prediction["market_option_id"] == winning_option_id
            self.cursor.execute(
                """
                UPDATE gotrendlabs_predictions
                SET status = 'resolved',
                    won = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (won, now, prediction["id"]),
            )
            if won:
                self.record_wallet_entry(
                    self.cursor,
                    prediction["user_id"],
                    entry_type="prediction_refund",
                    amount=int(prediction["stake_amount"]),
                    direction="release",
                    description=f"Stake liberado por acerto: {slug}",
                    reference_type="prediction",
                    reference_id=str(prediction["id"]),
                    created_by_id=self.staff_id,
                )
                payout_total = int(prediction["potential_payout"] or 0)
                payout_net = max(0, payout_total - int(prediction["stake_amount"]))
                if payout_net:
                    self.record_wallet_entry(
                        self.cursor,
                        prediction["user_id"],
                        entry_type="prediction_payout",
                        amount=payout_net,
                        direction="credit",
                        description=f"Crédito líquido por acerto: {slug}",
                        reference_type="prediction",
                        reference_id=str(prediction["id"]),
                        created_by_id=self.staff_id,
                    )
            else:
                self.record_wallet_entry(
                    self.cursor,
                    prediction["user_id"],
                    entry_type="prediction_loss",
                    amount=int(prediction["stake_amount"]),
                    direction="settle",
                    description=f"Stake liquidado por erro: {slug}",
                    reference_type="prediction",
                    reference_id=str(prediction["id"]),
                    created_by_id=self.staff_id,
                )
            if not prediction["is_bot"]:
                self._apply_reputation_delta(prediction["user_id"], prediction["probability_at_entry"], won, now)
        BadgeAwardEngine.on_market_resolved(self.cursor, market_id)

    def _refund_market_predictions(self, market_id, slug, now):
        self.cursor.execute(
            """
            SELECT id, user_id, stake_amount
            FROM gotrendlabs_predictions
            WHERE market_id = %s
              AND status = 'open'
            ORDER BY id ASC
            FOR UPDATE
            """,
            (market_id,),
        )
        predictions = self.cursor.fetchall()
        refunds_created = 0
        refunds_existing = 0
        for prediction in predictions:
            self.cursor.execute(
                """
                UPDATE gotrendlabs_predictions
                SET status = 'canceled',
                    won = NULL,
                    updated_at = %s
                WHERE id = %s
                """,
                (now, prediction["id"]),
            )
            self.cursor.execute(
                """
                SELECT id
                FROM gotrendlabs_wallet_ledger
                WHERE reference_type = 'prediction'
                  AND reference_id = %s
                  AND entry_type = 'prediction_refund'
                  AND direction = 'release'
                  AND id > COALESCE((
                      SELECT MAX(id)
                      FROM gotrendlabs_wallet_ledger
                      WHERE reference_type = 'prediction'
                        AND reference_id = %s
                        AND direction = 'lock'
                  ), 0)
                LIMIT 1
                """,
                (str(prediction["id"]), str(prediction["id"])),
            )
            if self.cursor.fetchone():
                refunds_existing += 1
                continue
            self.record_wallet_entry(
                self.cursor,
                prediction["user_id"],
                entry_type="prediction_refund",
                amount=int(prediction["stake_amount"]),
                direction="release",
                description=f"Refund por cancelamento: {slug}",
                reference_type="prediction",
                reference_id=str(prediction["id"]),
                created_by_id=self.staff_id,
            )
            refunds_created += 1
        return {
            "predictions_canceled": len(predictions),
            "refunds_created": refunds_created,
            "refunds_existing": refunds_existing,
        }

    def _assert_no_open_predictions(self, market_id, slug):
        self.cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM gotrendlabs_predictions
            WHERE market_id = %s
              AND status = 'open'
            """,
            (market_id,),
        )
        open_predictions = int(self.cursor.fetchone()["count"] or 0)
        if open_predictions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cancelamento inconsistente para {slug}: {open_predictions} previsões permaneceram abertas.",
            )

    def _undo_resolved_market_predictions(self, market_id, slug, now):
        self.cursor.execute(
            """
            SELECT id, user_id, stake_amount, won
            FROM gotrendlabs_predictions
            WHERE market_id = %s
              AND status = 'resolved'
            ORDER BY id ASC
            FOR UPDATE
            """,
            (market_id,),
        )
        predictions = self.cursor.fetchall()
        affected_user_ids = set()
        for prediction in predictions:
            affected_user_ids.add(prediction["user_id"])
            if prediction["won"]:
                self.cursor.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0) AS payout_amount
                    FROM gotrendlabs_wallet_ledger
                    WHERE reference_type = 'prediction'
                      AND reference_id = %s
                      AND entry_type = 'prediction_payout'
                      AND direction = 'credit'
                    """,
                    (str(prediction["id"]),),
                )
                payout_amount = int(self.cursor.fetchone()["payout_amount"] or 0)
                if payout_amount:
                    self.record_wallet_entry(
                        self.cursor,
                        prediction["user_id"],
                        entry_type="prediction_payout_reversal",
                        amount=payout_amount,
                        direction="debit",
                        description=f"Estorno de payout por cancelamento: {slug}",
                        reference_type="prediction",
                        reference_id=str(prediction["id"]),
                        created_by_id=self.staff_id,
                    )
                self.record_wallet_entry(
                    self.cursor,
                    prediction["user_id"],
                    entry_type="prediction_resolution_relock",
                    amount=int(prediction["stake_amount"]),
                    direction="lock",
                    description=f"Stake rebloqueado por resolução desfeita: {slug}",
                    reference_type="prediction",
                    reference_id=str(prediction["id"]),
                    created_by_id=self.staff_id,
                )
            else:
                self.record_wallet_entry(
                    self.cursor,
                    prediction["user_id"],
                    entry_type="prediction_refund",
                    amount=int(prediction["stake_amount"]),
                    direction="credit",
                    description=f"Refund intermediário por resolução desfeita: {slug}",
                    reference_type="prediction",
                    reference_id=str(prediction["id"]),
                    created_by_id=self.staff_id,
                )
                self.record_wallet_entry(
                    self.cursor,
                    prediction["user_id"],
                    entry_type="prediction_resolution_relock",
                    amount=int(prediction["stake_amount"]),
                    direction="lock",
                    description=f"Stake rebloqueado por resolução desfeita: {slug}",
                    reference_type="prediction",
                    reference_id=str(prediction["id"]),
                    created_by_id=self.staff_id,
                )
            self.cursor.execute(
                """
                UPDATE gotrendlabs_predictions
                SET status = 'open',
                    won = NULL,
                    updated_at = %s
                WHERE id = %s
                """,
                (now, prediction["id"]),
            )
        for user_id in affected_user_ids:
            self._recalculate_user_reputation(user_id, now)

    @staticmethod
    def _decimal_probability(value):
        return Decimal(str(value or 0)).quantize(PROBABILITY_QUANT)
