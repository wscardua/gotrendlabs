from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_user_is_bot"),
    ]

    operations = [
        migrations.AddField(
            model_name="badgerule",
            name="event",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.RunSQL(
            "ALTER TABLE gotrendlabs_badge_rules ALTER COLUMN event SET DEFAULT ''",
            "ALTER TABLE gotrendlabs_badge_rules ALTER COLUMN event DROP DEFAULT",
        ),
    ]
