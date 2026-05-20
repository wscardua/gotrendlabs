from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("markets", "0015_market_popularity_counts"),
    ]

    operations = [
        migrations.CreateModel(
            name="MarketFavorite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "market",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorites", to="markets.market"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="market_favorites", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "db_table": "orynth_market_favorites",
            },
        ),
        migrations.AddIndex(
            model_name="marketfavorite",
            index=models.Index(fields=["user", "-created_at"], name="orynth_fav_user_id_8f6c74_idx"),
        ),
        migrations.AddIndex(
            model_name="marketfavorite",
            index=models.Index(fields=["market"], name="orynth_fav_market_0f7d22_idx"),
        ),
        migrations.AddConstraint(
            model_name="marketfavorite",
            constraint=models.UniqueConstraint(fields=("user", "market"), name="uniq_market_favorite_user_market"),
        ),
    ]
