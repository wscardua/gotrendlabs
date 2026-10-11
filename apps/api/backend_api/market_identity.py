"""Identity fence for administrative mutations while the market row is locked."""

from fastapi import HTTPException


def validate_market_identity(cursor, slug, market_id, expected_market_id):
    if expected_market_id is None:
        cursor.execute(
            "SELECT 1 FROM gotrendlabs_admin_events WHERE entity_type='market' "
            "AND entity_identifier=%s AND action='market.delete' LIMIT 1", (slug,),
        )
        conflict = bool(cursor.fetchone())
    else:
        conflict = market_id != expected_market_id
    if conflict:
        raise HTTPException(
            409, "A identidade do mercado mudou. Recarregue a página antes de continuar."
        )
