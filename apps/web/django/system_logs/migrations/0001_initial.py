import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import apps.web.django.system_logs.models as system_log_models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(default=system_log_models.default_expires_at)),
                ("level", models.CharField(choices=[("DEBUG", "Debug"), ("INFO", "Info"), ("WARNING", "Warning"), ("ERROR", "Error"), ("CRITICAL", "Critical")], db_index=True, max_length=16)),
                ("source", models.CharField(choices=[("django", "Django"), ("fastapi", "FastAPI"), ("python", "Python")], db_index=True, max_length=32)),
                ("logger_name", models.CharField(blank=True, max_length=160)),
                ("event_type", models.CharField(db_index=True, max_length=80)),
                ("message", models.TextField()),
                ("request_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("method", models.CharField(blank=True, max_length=12)),
                ("path", models.CharField(blank=True, max_length=500)),
                ("status_code", models.PositiveSmallIntegerField(blank=True, db_index=True, null=True)),
                ("duration_ms", models.PositiveIntegerField(blank=True, null=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=255)),
                ("exception_type", models.CharField(blank=True, db_index=True, max_length=160)),
                ("stack_trace", models.TextField(blank=True)),
                ("context", models.JSONField(blank=True, default=dict)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="system_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "gotrendlabs_system_logs",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="systemlog",
            index=models.Index(fields=["-created_at", "-id"], name="gotrendlabs_sys_created_9652c9_idx"),
        ),
        migrations.AddIndex(
            model_name="systemlog",
            index=models.Index(fields=["expires_at"], name="gotrendlabs_sys_expires_376d29_idx"),
        ),
        migrations.AddIndex(
            model_name="systemlog",
            index=models.Index(fields=["source", "level", "-created_at"], name="gotrendlabs_sys_source__c1423a_idx"),
        ),
        migrations.AddIndex(
            model_name="systemlog",
            index=models.Index(fields=["request_id", "-created_at"], name="gotrendlabs_sys_request_05fdd2_idx"),
        ),
        migrations.AddIndex(
            model_name="systemlog",
            index=models.Index(fields=["user", "-created_at"], name="gotrendlabs_sys_user_id_65648e_idx"),
        ),
        migrations.AddIndex(
            model_name="systemlog",
            index=models.Index(fields=["event_type", "-created_at"], name="gotrendlabs_sys_event_t_97b621_idx"),
        ),
        migrations.AddIndex(
            model_name="systemlog",
            index=models.Index(fields=["status_code", "-created_at"], name="gotrendlabs_sys_status__ae46db_idx"),
        ),
        migrations.AddIndex(
            model_name="systemlog",
            index=models.Index(fields=["exception_type", "-created_at"], name="gotrendlabs_sys_except_79ea7c_idx"),
        ),
    ]
