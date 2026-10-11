"""Delete unpublished markets and editorial records in one audited transaction."""
import json

from fastapi import HTTPException
from apps.api.backend_api.admin_events import record_admin_event


def delete_market(cursor, slug, expected_revision, actor_id, expected_market_id):
    cursor.execute(
        "SELECT id,title,status,published_at FROM gotrendlabs_markets "
        "WHERE slug=%s FOR UPDATE", (slug,),
    )
    market = cursor.fetchone()
    if not market:
        raise HTTPException(404, "Mercado não encontrado.")
    if market["id"] != expected_market_id:
        raise HTTPException(409, "Este endereço pertence a outro mercado. Recarregue antes de excluir.")
    cursor.execute(
        "SELECT revision,state FROM gotrendlabs_agent_editorial_drafts WHERE market_id=%s FOR UPDATE",
        (market["id"],),
    )
    draft = cursor.fetchone()
    if market["status"] != "draft" or market["published_at"] or not draft or draft["state"] not in {"preparation", "in_review"}:
        raise HTTPException(409, "Só é possível excluir rascunhos em preparação ou revisão, antes da publicação.")
    if draft["revision"] != expected_revision:
        raise HTTPException(409, "O mercado foi alterado. Recarregue e confira a versão atual antes de excluir.")
    # Defensive checks also protect anomalous/legacy drafts. Never touch wallet or proofs.
    for table in ("gotrendlabs_predictions", "market_integrity_definitions", "prediction_commitments",
                  "market_seals", "market_merkle_leaves", "integrity_ledger_events"):
        cursor.execute(f"SELECT 1 FROM {table} WHERE market_id=%s LIMIT 1", (market["id"],))
        if cursor.fetchone():
            raise HTTPException(409, "Mercado com previsões ou registros de integridade não pode ser excluído.")
    market_id = market["id"]
    # The restricted database function can remove editorial revisions without
    # granting general DELETE access to their append-only runtime table.
    cursor.execute("SELECT public.delete_prepublication_editorial(%s,%s)", (market_id, expected_revision))
    cursor.execute(
        "UPDATE gotrendlabs_agent_idempotency SET response=jsonb_build_object('market_id',%s::bigint,'deleted',true) "
        "WHERE response->>'market_id'=%s", (market_id, str(market_id)),
    )
    cursor.execute("UPDATE gotrendlabs_market_suggestions SET converted_market_id=NULL WHERE converted_market_id=%s", (market_id,))
    cursor.execute("UPDATE gotrendlabs_ai_agent_actions SET market_id=NULL WHERE market_id=%s", (market_id,))
    cursor.execute(
        "UPDATE gotrendlabs_ai_agent_actions SET comment_id=NULL "
        "WHERE comment_id IN (SELECT id FROM gotrendlabs_market_comments WHERE market_id=%s)", (market_id,),
    )
    cursor.execute(
        "DELETE FROM gotrendlabs_push_deliveries WHERE notification_id IN "
        "(SELECT id FROM gotrendlabs_user_notifications WHERE market_id=%s OR comment_id IN "
        "(SELECT id FROM gotrendlabs_market_comments WHERE market_id=%s))", (market_id, market_id),
    )
    cursor.execute(
        "DELETE FROM gotrendlabs_user_notifications WHERE market_id=%s OR comment_id IN "
        "(SELECT id FROM gotrendlabs_market_comments WHERE market_id=%s)", (market_id, market_id),
    )
    cursor.execute(
        "DELETE FROM gotrendlabs_comment_reactions WHERE comment_id IN "
        "(SELECT id FROM gotrendlabs_market_comments WHERE market_id=%s)", (market_id,),
    )
    # Keep only the technical attempt for existing global/operator quotas.
    # Scrub editorial input and fence any provider result still in flight.
    cursor.execute(
        "UPDATE gotrendlabs_thumbnail_jobs SET market_id=NULL,state='expired',error_code='market_deleted',"
        "snapshot='{}'::jsonb,snapshot_hash='',usage=NULL,"
        "claim_token=NULL,lease_until=NULL,expires_at=LEAST(expires_at,CURRENT_TIMESTAMP),"
        "finished_at=COALESCE(finished_at,CURRENT_TIMESTAMP) WHERE market_id=%s", (market_id,),
    )
    for table in ("gotrendlabs_market_comments", "gotrendlabs_market_favorites", "gotrendlabs_market_likes"):
        cursor.execute(f"DELETE FROM {table} WHERE market_id=%s", (market_id,))
    # Some installations retain this pre-editorial funnel linkage table.
    cursor.execute("SELECT to_regclass('public.gotrendlabs_market_funnel_market_links') AS name")
    if cursor.fetchone()["name"]:
        cursor.execute("DELETE FROM gotrendlabs_market_funnel_market_links WHERE market_id=%s", (market_id,))
    cursor.execute("UPDATE gotrendlabs_markets SET winning_option_id=NULL WHERE id=%s", (market_id,))
    cursor.execute("DELETE FROM gotrendlabs_market_options WHERE market_id=%s", (market_id,))
    cursor.execute("DELETE FROM gotrendlabs_markets WHERE id=%s", (market_id,))
    record_admin_event(cursor, actor_id, "market.delete", "market", slug, json.dumps({
        "market_id": market["id"], "title": market["title"], "editorial_state": draft["state"],
        "revision": draft["revision"], "deletion": "physical",
    }, ensure_ascii=False))
