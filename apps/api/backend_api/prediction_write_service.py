"""Authoritative persistence primitives shared by human and internal-agent predictions."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from apps.api.backend_api.integrity_service import commit_prediction


INITIAL_REPUTATION = 100
PROBABILITY_QUANT = Decimal("0.0001")


def _decimal_probability(value):
    return Decimal(str(value or 0)).quantize(PROBABILITY_QUANT)


def create_initial_prediction_with_integrity(
    cursor,
    *,
    user_id: int,
    market: dict,
    option: dict,
    stake_amount: int,
    wallet_description: str,
    occurred_at: datetime | None = None,
):
    """Persist prediction, wallet lock and signed commitment in the caller transaction."""
    occurred_at = occurred_at or datetime.now(timezone.utc)
    cursor.execute("SELECT reputation_score FROM gotrendlabs_user_reputations WHERE user_id=%s", (user_id,))
    reputation = cursor.fetchone()
    reputation_score = int(reputation["reputation_score"] if reputation else INITIAL_REPUTATION)
    probability_at_entry = max(_decimal_probability(option["probability_exact"]), PROBABILITY_QUANT)
    weight_at_entry = reputation_score * int(stake_amount)
    potential_payout = int((Decimal(stake_amount) * Decimal("100") / probability_at_entry).to_integral_value())
    cursor.execute(
        """INSERT INTO gotrendlabs_predictions
           (user_id,market_id,market_option_id,action_type,position_sequence,stake_amount,
            probability_at_entry,weight_at_entry,potential_payout,status,won,created_at,updated_at)
           VALUES (%s,%s,%s,'initial',1,%s,%s,%s,%s,'open',NULL,%s,%s)
           RETURNING id,created_at""",
        (user_id, market["id"], option["id"], int(stake_amount), probability_at_entry,
         weight_at_entry, potential_payout, occurred_at, occurred_at),
    )
    prediction = dict(cursor.fetchone())
    prediction["potential_payout"] = potential_payout
    cursor.execute(
        """INSERT INTO gotrendlabs_wallet_ledger
           (user_id,entry_type,amount,direction,description,reference_type,reference_id,created_by_id,created_at)
           VALUES (%s,'prediction_stake_lock',%s,'lock',%s,'prediction',%s,NULL,%s)""",
        (user_id, int(stake_amount), wallet_description, str(prediction["id"]), occurred_at),
    )
    cursor.execute(
        """UPDATE gotrendlabs_wallet_balances
           SET available_gtl=available_gtl-%s,locked_gtl=locked_gtl+%s,updated_at=%s
           WHERE user_id=%s""",
        (int(stake_amount), int(stake_amount), occurred_at, user_id),
    )
    prediction["commitment"] = commit_prediction(
        cursor, prediction_id=prediction["id"], user_id=user_id, occurred_at=prediction["created_at"]
    )
    return prediction
