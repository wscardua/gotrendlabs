from django.db import migrations


INSTALL = """
CREATE FUNCTION public.delete_prepublication_editorial(p_market_id bigint, p_revision integer)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE
    m record;
    d record;
BEGIN
    SELECT status,published_at INTO m FROM public.gotrendlabs_markets WHERE id=p_market_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'market not found' USING ERRCODE='23514';
    END IF;
    SELECT state,revision INTO d FROM public.gotrendlabs_agent_editorial_drafts
        WHERE market_id=p_market_id FOR UPDATE;
    IF NOT FOUND OR m.status <> 'draft' OR m.published_at IS NOT NULL
       OR d.state NOT IN ('preparation','in_review') OR d.revision IS DISTINCT FROM p_revision THEN
        RAISE EXCEPTION 'market not eligible for editorial deletion' USING ERRCODE='23514';
    END IF;
    IF EXISTS(SELECT 1 FROM public.gotrendlabs_predictions WHERE market_id=p_market_id)
       OR EXISTS(SELECT 1 FROM public.market_integrity_definitions WHERE market_id=p_market_id)
       OR EXISTS(SELECT 1 FROM public.prediction_commitments WHERE market_id=p_market_id)
       OR EXISTS(SELECT 1 FROM public.market_seals WHERE market_id=p_market_id)
       OR EXISTS(SELECT 1 FROM public.market_merkle_leaves WHERE market_id=p_market_id)
       OR EXISTS(SELECT 1 FROM public.integrity_ledger_events WHERE market_id=p_market_id) THEN
        RAISE EXCEPTION 'market has protected records' USING ERRCODE='23514';
    END IF;
    DELETE FROM public.gotrendlabs_integrity_alerts WHERE market_id=p_market_id;
    DELETE FROM public.gotrendlabs_agent_editorial_revisions WHERE draft_id=p_market_id;
    DELETE FROM public.gotrendlabs_agent_editorial_drafts WHERE market_id=p_market_id;
END;
$$;
REVOKE ALL ON FUNCTION public.delete_prepublication_editorial(bigint,integer) FROM PUBLIC;
DO $$ BEGIN
    IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='gotrendlabs_fastapi') THEN
        GRANT EXECUTE ON FUNCTION public.delete_prepublication_editorial(bigint,integer) TO gotrendlabs_fastapi;
    END IF;
END $$;
"""


def install(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(INSTALL)


def uninstall(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('DROP FUNCTION public.delete_prepublication_editorial(bigint,integer)')


class Migration(migrations.Migration):
    dependencies = [('editorial_integrations', '0005_restore_published_editorial_decisions')]
    operations = [migrations.RunPython(install, uninstall)]
