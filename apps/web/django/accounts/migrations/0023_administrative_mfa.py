# Generated manually for the FastAPI-owned administrative MFA boundary.
import os

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


MFA_TABLES = ("gotrendlabs_totp_factors", "gotrendlabs_mfa_challenges", "gotrendlabs_mfa_recovery_codes", "gotrendlabs_mfa_attempts")


def grant_fastapi_mfa_permissions(apps, schema_editor):
    """Only FastAPI needs runtime access; deployments use a separate migrator/owner."""
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return
    role = os.environ.get("FASTAPI_POSTGRES_USER")
    if not role:
        return
    quote = connection.ops.quote_name
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role])
        if not cursor.fetchone():
            return
        for table in MFA_TABLES:
            cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {quote(table)} TO {quote(role)}")
            cursor.execute("SELECT pg_get_serial_sequence(%s, 'id')", [table])
            sequence = cursor.fetchone()[0]
            if sequence:
                schema, sequence_name = sequence.split(".", 1)
                cursor.execute(f"GRANT USAGE, SELECT ON SEQUENCE {quote(schema)}.{quote(sequence_name)} TO {quote(role)}")


class Migration(migrations.Migration):
    dependencies = [("accounts", "0022_require_adult_birth_date")]

    operations = [
        migrations.AddField(model_name="authsession", name="mfa_verified_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="authsession", name="mfa_method", field=models.CharField(blank=True, max_length=32)),
        migrations.CreateModel(
            name="TotpFactor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("secret_encrypted", models.TextField()), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)), ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("last_accepted_timestep", models.BigIntegerField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="totp_factors", to=settings.AUTH_USER_MODEL)),
            ], options={"db_table": "gotrendlabs_totp_factors"},
        ),
        migrations.CreateModel(
            name="MfaChallenge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token_hash", models.CharField(max_length=64, unique=True)), ("purpose", models.CharField(max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("expires_at", models.DateTimeField()), ("used_at", models.DateTimeField(blank=True, null=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)), ("user_agent", models.CharField(blank=True, max_length=255)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ], options={"db_table": "gotrendlabs_mfa_challenges"},
        ),
        migrations.CreateModel(
            name="MfaRecoveryCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code_hash", models.CharField(max_length=64)), ("created_at", models.DateTimeField(auto_now_add=True)), ("used_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ], options={"db_table": "gotrendlabs_mfa_recovery_codes"},
        ),
        migrations.AddConstraint(model_name="mfarecoverycode", constraint=models.UniqueConstraint(fields=("user", "code_hash"), name="uniq_mfa_recovery_code")),
        migrations.AddIndex(model_name="mfachallenge", index=models.Index(fields=["user", "used_at", "expires_at"], name="mfa_challenge_user_exp_idx")),
        migrations.AddIndex(model_name="mfarecoverycode", index=models.Index(fields=["user", "used_at"], name="mfa_recovery_user_used_idx")),
        migrations.RunSQL("CREATE TABLE gotrendlabs_mfa_attempts (id bigserial PRIMARY KEY, identity_hash varchar(64) NOT NULL, created_at timestamptz NOT NULL); CREATE INDEX mfa_attempt_identity_created_idx ON gotrendlabs_mfa_attempts (identity_hash, created_at)"),
        migrations.RunPython(grant_fastapi_mfa_permissions, migrations.RunPython.noop),
        migrations.RunSQL("UPDATE gotrendlabs_auth_sessions s SET revoked_at = NOW() FROM gotrendlabs_users u WHERE s.user_id = u.id AND s.revoked_at IS NULL AND (u.is_staff = true OR u.is_superuser = true)", migrations.RunSQL.noop),
    ]
