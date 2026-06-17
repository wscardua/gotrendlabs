from django.db import migrations, models
import django.db.models.deletion


TOP_TEN_RULE_DESCRIPTION = "Alcance posição 10 ou melhor no ranking global após pelo menos 3 previsões resolvidas."


def configure_top_ten_requirement(apps, schema_editor):
    BadgeDefinition = apps.get_model("accounts", "BadgeDefinition")
    BadgeRuleRequirement = apps.get_model("accounts", "BadgeRuleRequirement")
    try:
        badge = BadgeDefinition.objects.get(code="top_ten")
    except BadgeDefinition.DoesNotExist:
        return
    badge.rule_description = TOP_TEN_RULE_DESCRIPTION
    badge.save(update_fields=["rule_description", "updated_at"])
    BadgeRuleRequirement.objects.update_or_create(
        badge_rule=badge.rule,
        metric_type="resolved_predictions_count",
        defaults={
            "threshold_value": 3,
            "category": "",
            "subcategory": "",
            "event": "",
            "is_active": True,
        },
    )


def remove_top_ten_requirement(apps, schema_editor):
    BadgeDefinition = apps.get_model("accounts", "BadgeDefinition")
    BadgeRuleRequirement = apps.get_model("accounts", "BadgeRuleRequirement")
    try:
        badge = BadgeDefinition.objects.get(code="top_ten")
    except BadgeDefinition.DoesNotExist:
        return
    BadgeRuleRequirement.objects.filter(badge_rule=badge.rule, metric_type="resolved_predictions_count").delete()
    badge.rule_description = "Alcance posição 10 ou melhor no ranking global."
    badge.save(update_fields=["rule_description", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0019_referralreward_referralcode"),
    ]

    operations = [
        migrations.CreateModel(
            name="BadgeRuleRequirement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "metric_type",
                    models.CharField(
                        choices=[
                            ("founding_member", "Founding member"),
                            ("resolved_predictions_count", "Resolved predictions count"),
                            ("correct_predictions_count", "Correct predictions count"),
                            ("streak_count", "Streak count"),
                            ("ranking_position", "Ranking position"),
                            ("comments_count", "Comments count"),
                            ("approved_suggestions_count", "Approved suggestions count"),
                            ("rewarded_feedback_count", "Rewarded feedback count"),
                        ],
                        max_length=64,
                    ),
                ),
                ("threshold_value", models.DecimalField(decimal_places=4, default=1, max_digits=12)),
                ("category", models.CharField(blank=True, max_length=80)),
                ("subcategory", models.CharField(blank=True, max_length=80)),
                ("event", models.CharField(blank=True, default="", max_length=80)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "badge_rule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requirements",
                        to="accounts.badgerule",
                    ),
                ),
            ],
            options={
                "db_table": "gotrendlabs_badge_rule_requirements",
            },
        ),
        migrations.AddIndex(
            model_name="badgerulerequirement",
            index=models.Index(fields=["badge_rule", "is_active"], name="gtl_req_rule_active_idx"),
        ),
        migrations.AddIndex(
            model_name="badgerulerequirement",
            index=models.Index(fields=["metric_type", "is_active"], name="gtl_req_metric_active_idx"),
        ),
        migrations.RunPython(configure_top_ten_requirement, remove_top_ten_requirement),
    ]
