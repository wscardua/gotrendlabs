from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("markets", "0013_clear_canceled_featured"),
    ]

    operations = [
        migrations.AddField(
            model_name="market",
            name="resolution_timezone",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
