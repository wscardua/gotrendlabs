from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agents", "0004_gotrendlabs_bot_identities"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiagent",
            name="max_comments_per_market_override",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
