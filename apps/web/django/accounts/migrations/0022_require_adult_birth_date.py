from datetime import date

from django.db import migrations, models


PREPRODUCTION_DEFAULT_BIRTH_DATE = date(1990, 1, 1)


def populate_missing_birth_dates(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    UserProfile.objects.filter(birth_date__isnull=True).update(
        birth_date=PREPRODUCTION_DEFAULT_BIRTH_DATE
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0021_grant_badge_requirement_runtime_permissions"),
    ]

    operations = [
        migrations.RunPython(populate_missing_birth_dates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="userprofile",
            name="birth_date",
            field=models.DateField(default=PREPRODUCTION_DEFAULT_BIRTH_DATE),
        ),
    ]
