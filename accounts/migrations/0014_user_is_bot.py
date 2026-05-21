from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_walletrechargerequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_bot",
            field=models.BooleanField(default=False),
        ),
    ]
