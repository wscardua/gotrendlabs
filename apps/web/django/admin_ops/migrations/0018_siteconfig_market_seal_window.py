from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("admin_ops", "0017_siteconfig_mobile_compatibility")]
    operations = [migrations.AddField(model_name="siteconfig", name="market_seal_window_hours", field=models.PositiveIntegerField(default=12))]
