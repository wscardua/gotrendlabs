from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("markets", "0020_category_subcategory_notice"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=40)),
                ("source_key", models.CharField(max_length=160)),
                ("title", models.CharField(max_length=160)),
                ("body", models.TextField(blank=True)),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="triggered_notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "comment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="markets.marketcomment",
                    ),
                ),
                (
                    "market",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="markets.market",
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "db_table": "gotrendlabs_user_notifications",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="usernotification",
            index=models.Index(fields=["recipient", "is_read", "-created_at"], name="gtl_notif_rec_7f17_idx"),
        ),
        migrations.AddIndex(
            model_name="usernotification",
            index=models.Index(fields=["market", "-created_at"], name="gtl_notif_mkt_74d6_idx"),
        ),
        migrations.AddIndex(
            model_name="usernotification",
            index=models.Index(fields=["comment", "-created_at"], name="gtl_notif_cmt_6c58_idx"),
        ),
        migrations.AddConstraint(
            model_name="usernotification",
            constraint=models.UniqueConstraint(fields=("recipient", "source_key"), name="uniq_notification_recipient_source"),
        ),
    ]
