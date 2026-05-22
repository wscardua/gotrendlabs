from django.db import migrations, models
import django.db.models.deletion


def seed_general_events(apps, schema_editor):
    Market = apps.get_model("markets", "Market")
    MarketEvent = apps.get_model("markets", "MarketEvent")
    MarketSubcategory = apps.get_model("markets", "MarketSubcategory")

    for subcategory in MarketSubcategory.objects.all():
        MarketEvent.objects.get_or_create(
            subcategory=subcategory,
            slug="geral",
            defaults={
                "name": "Geral",
                "is_blocked": False,
                "blocked_reason": "",
            },
        )

    for market in Market.objects.filter(event__isnull=True).select_related("subcategory"):
        event, _ = MarketEvent.objects.get_or_create(
            subcategory=market.subcategory,
            slug="geral",
            defaults={
                "name": "Geral",
                "is_blocked": False,
                "blocked_reason": "",
            },
        )
        market.event = event
        market.save(update_fields=["event"])


class Migration(migrations.Migration):

    dependencies = [
        ("markets", "0017_market_likes"),
    ]

    operations = [
        migrations.CreateModel(
            name="MarketEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("slug", models.SlugField(max_length=100)),
                ("is_blocked", models.BooleanField(default=False)),
                ("blocked_at", models.DateTimeField(blank=True, null=True)),
                ("blocked_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "subcategory",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="markets.marketsubcategory"),
                ),
            ],
            options={
                "db_table": "orynth_market_events",
                "ordering": ["subcategory__category__name", "subcategory__name", "name"],
            },
        ),
        migrations.AddField(
            model_name="market",
            name="event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="markets",
                to="markets.marketevent",
            ),
        ),
        migrations.AddConstraint(
            model_name="marketevent",
            constraint=models.UniqueConstraint(fields=("subcategory", "slug"), name="uniq_market_event_subcategory_slug"),
        ),
        migrations.RunPython(seed_general_events, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="market",
            name="event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="markets",
                to="markets.marketevent",
            ),
        ),
        migrations.AddIndex(
            model_name="market",
            index=models.Index(fields=["event", "status"], name="orynth_mark_event_i_ea32c2_idx"),
        ),
    ]
