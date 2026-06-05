from django.db import migrations


LEGACY_TABLES = (
    "orynth_market_funnels",
    "orynth_market_funnel_sources",
    "orynth_market_funnel_source_capabilities",
    "orynth_market_funnel_source_links",
    "orynth_market_funnel_topics",
    "orynth_market_funnel_topic_signals",
    "orynth_market_funnel_runs",
    "orynth_market_funnel_run_events",
    "orynth_market_funnel_raw_items",
    "orynth_market_funnel_ideas",
    "orynth_market_funnel_idea_signals",
    "orynth_market_funnel_candidates",
    "orynth_market_funnel_candidate_signals",
    "orynth_market_funnel_candidate_evaluations",
    "orynth_market_funnel_adversarial_reviews",
    "orynth_market_funnel_resolution_probes",
    "orynth_market_funnel_quality_metrics",
    "orynth_market_funnel_editorial_decisions",
    "orynth_market_funnel_market_links",
    "orynth_market_funnel_learning_events",
    "orynth_market_funnel_global_config",
    "orynth_market_funnel_signals",
)


def rename_legacy_market_funnel_tables(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for old_table in LEGACY_TABLES:
            new_table = old_table.replace("orynth_", "gotrendlabs_", 1)
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF to_regclass(%s) IS NOT NULL AND to_regclass(%s) IS NULL THEN
                        EXECUTE format('ALTER TABLE %%I RENAME TO %%I', %s, %s);
                    END IF;
                END $$;
                """,
                [f"public.{old_table}", f"public.{new_table}", old_table, new_table],
            )
        cursor.execute(
            """
            DO $$
            BEGIN
                IF to_regclass('public.gotrendlabs_market_funnel_quality_metrics') IS NOT NULL
                   AND EXISTS (
                       SELECT 1
                         FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'gotrendlabs_market_funnel_quality_metrics'
                          AND column_name = 'prediction_volume_oc'
                   )
                   AND NOT EXISTS (
                       SELECT 1
                         FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'gotrendlabs_market_funnel_quality_metrics'
                          AND column_name = 'prediction_volume_gtl'
                   ) THEN
                    ALTER TABLE gotrendlabs_market_funnel_quality_metrics
                    RENAME COLUMN prediction_volume_oc TO prediction_volume_gtl;
                END IF;
            END $$;
            """
        )


class Migration(migrations.Migration):
    dependencies = [
        ("markets", "0023_gotrendlabs_guest_email_domains"),
    ]

    operations = [
        migrations.RunPython(rename_legacy_market_funnel_tables, migrations.RunPython.noop),
    ]
