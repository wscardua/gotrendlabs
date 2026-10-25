"""Read the current winning settlement from the user's actual ledger entries."""


def resolution_returns(cursor, user_id):
    cursor.execute(
        """
        WITH winning_positions AS (
            SELECT p.id, p.user_id, m.id AS market_id, m.slug, m.title,
                   COALESCE((SELECT MAX(l.id) FROM gotrendlabs_wallet_ledger l
                             WHERE l.user_id = p.user_id AND l.reference_type = 'prediction'
                               AND l.reference_id = p.id::text AND l.direction = 'lock'), 0) AS lock_id
            FROM gotrendlabs_predictions p
            JOIN gotrendlabs_markets m ON m.id = p.market_id
            WHERE p.user_id = %s AND p.status = 'resolved' AND p.won = true
              AND m.status IN ('resolved', 'sealed')
        ), returns AS (
            SELECT p.market_id, p.slug AS market_slug, p.title AS market_title,
                   COALESCE(SUM(l.amount) FILTER (WHERE l.entry_type = 'prediction_refund' AND l.direction = 'release'), 0)::bigint AS released_gtl,
                   COALESCE(SUM(l.amount) FILTER (WHERE l.entry_type = 'prediction_payout' AND l.direction = 'credit'), 0)::bigint AS net_profit_gtl,
                   MAX(l.created_at) AS last_return_at
            FROM winning_positions p
            JOIN gotrendlabs_wallet_ledger l ON l.user_id = p.user_id
              AND l.reference_type = 'prediction' AND l.reference_id = p.id::text AND l.id > p.lock_id
            WHERE (l.entry_type = 'prediction_refund' AND l.direction = 'release')
               OR (l.entry_type = 'prediction_payout' AND l.direction = 'credit')
            GROUP BY p.market_id, p.slug, p.title
        )
        SELECT market_id, market_slug, market_title, released_gtl, net_profit_gtl,
               released_gtl + net_profit_gtl AS total_received_gtl
        FROM returns ORDER BY last_return_at DESC, market_id DESC
        """, (user_id,),
    )
    return [dict(row) for row in cursor.fetchall()]
