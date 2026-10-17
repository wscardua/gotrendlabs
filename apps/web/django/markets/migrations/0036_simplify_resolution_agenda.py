"""Simplify active schedule; retain retired columns solely for signed history."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('markets', '0035_resolution_agenda_queue_index')]
    operations = [
        *[migrations.RemoveConstraint('market', name) for name in (
            'schedule_expected_after_cutoff', 'schedule_recovery_after_cutoff',
            'schedule_expected_within_recovery', 'schedule_registered_complete')],
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(
                "ALTER TABLE gotrendlabs_markets ALTER COLUMN evidence_recovery_status SET DEFAULT 'not_recorded'",
                migrations.RunSQL.noop)],
            state_operations=[migrations.RemoveField('market', field) for field in (
                'evidence_cutoff_at', 'evidence_recovery_deadline_at', 'evidence_recovery_status')]),
        migrations.AddConstraint('market', models.CheckConstraint(
            check=models.Q(schedule_version=0) | (models.Q(expected_resolution_at__isnull=False, original_expected_resolution_at__isnull=False) & ~models.Q(schedule_timezone='')),
            name='schedule_registered_complete')),
    ]
