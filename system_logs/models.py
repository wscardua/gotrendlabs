from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_expires_at():
    try:
        from system_logs.services import get_system_log_retention_days

        retention_days = get_system_log_retention_days()
    except Exception:
        retention_days = getattr(settings, "SYSTEM_LOG_RETENTION_DAYS", 90)
    return timezone.now() + timedelta(days=retention_days)


class SystemLog(models.Model):
    LEVEL_CHOICES = (
        ("DEBUG", "Debug"),
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("CRITICAL", "Critical"),
    )
    SOURCE_CHOICES = (
        ("django", "Django"),
        ("fastapi", "FastAPI"),
        ("python", "Python"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expires_at)
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES, db_index=True)
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, db_index=True)
    logger_name = models.CharField(max_length=160, blank=True)
    event_type = models.CharField(max_length=80, db_index=True)
    message = models.TextField()
    request_id = models.CharField(max_length=64, blank=True, db_index=True)
    method = models.CharField(max_length=12, blank=True)
    path = models.CharField(max_length=500, blank=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="system_logs")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    exception_type = models.CharField(max_length=160, blank=True, db_index=True)
    stack_trace = models.TextField(blank=True)
    context = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "orynth_system_logs"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["-created_at", "-id"], name="orynth_sys_created_9652c9_idx"),
            models.Index(fields=["expires_at"], name="orynth_sys_expires_376d29_idx"),
            models.Index(fields=["source", "level", "-created_at"], name="orynth_sys_source__c1423a_idx"),
            models.Index(fields=["request_id", "-created_at"], name="orynth_sys_request_05fdd2_idx"),
            models.Index(fields=["user", "-created_at"], name="orynth_sys_user_id_65648e_idx"),
            models.Index(fields=["event_type", "-created_at"], name="orynth_sys_event_t_97b621_idx"),
            models.Index(fields=["status_code", "-created_at"], name="orynth_sys_status__ae46db_idx"),
            models.Index(fields=["exception_type", "-created_at"], name="orynth_sys_except_79ea7c_idx"),
        ]
