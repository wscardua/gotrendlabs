from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("markets", "0018_market_events"),
    ]

    operations = [
        migrations.AddField(
            model_name="marketevent",
            name="notice",
            field=models.TextField(blank=True, default=""),
        ),
    ]
