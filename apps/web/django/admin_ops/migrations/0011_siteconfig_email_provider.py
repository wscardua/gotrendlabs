from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_ops", "0010_mobileapprelease_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteconfig",
            name="email_provider",
            field=models.CharField(
                choices=[("smtp", "SMTP"), ("resend", "Resend")],
                default="smtp",
                max_length=20,
            ),
        ),
    ]
