from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("admin_ops", "0013_siteconfig_position_reinforcement_enabled_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            """
            ALTER TABLE gotrendlabs_site_config
              ALTER COLUMN position_reinforcement_enabled SET DEFAULT true,
              ALTER COLUMN position_revision_enabled SET DEFAULT true,
              ALTER COLUMN position_revision_max_count SET DEFAULT 1,
              ALTER COLUMN position_revision_cutoff_hours SET DEFAULT 24,
              ALTER COLUMN position_revision_penalty_percent SET DEFAULT 20,
              ALTER COLUMN position_reinforcement_min_gtl SET DEFAULT 1,
              ALTER COLUMN position_revision_min_remaining_gtl SET DEFAULT 1
            """,
            """
            ALTER TABLE gotrendlabs_site_config
              ALTER COLUMN position_reinforcement_enabled DROP DEFAULT,
              ALTER COLUMN position_revision_enabled DROP DEFAULT,
              ALTER COLUMN position_revision_max_count DROP DEFAULT,
              ALTER COLUMN position_revision_cutoff_hours DROP DEFAULT,
              ALTER COLUMN position_revision_penalty_percent DROP DEFAULT,
              ALTER COLUMN position_reinforcement_min_gtl DROP DEFAULT,
              ALTER COLUMN position_revision_min_remaining_gtl DROP DEFAULT
            """,
        ),
    ]
