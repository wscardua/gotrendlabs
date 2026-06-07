from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("markets", "0014_market_resolution_timezone"),
    ]

    operations = [
        migrations.AddField(
            model_name="market",
            name="view_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="market",
            name="share_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
