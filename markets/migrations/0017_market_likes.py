from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("markets", "0016_market_favorites"),
    ]

    operations = [
        migrations.CreateModel(
            name="MarketLike",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "market",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="likes", to="markets.market"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="market_likes", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "db_table": "orynth_market_likes",
            },
        ),
        migrations.AddIndex(
            model_name="marketlike",
            index=models.Index(fields=["user", "-created_at"], name="orynth_like_user_id_7d3f2a_idx"),
        ),
        migrations.AddIndex(
            model_name="marketlike",
            index=models.Index(fields=["market"], name="orynth_like_market_6b8a91_idx"),
        ),
        migrations.AddConstraint(
            model_name="marketlike",
            constraint=models.UniqueConstraint(fields=("user", "market"), name="uniq_market_like_user_market"),
        ),
    ]
