from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("markets", "0019_marketevent_notice"),
    ]

    operations = [
        migrations.AddField(
            model_name="marketcategory",
            name="notice",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="marketsubcategory",
            name="notice",
            field=models.TextField(blank=True, default=""),
        ),
    ]
