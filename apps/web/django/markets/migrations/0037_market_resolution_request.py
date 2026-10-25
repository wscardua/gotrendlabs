import os
from django.db import migrations, models
import django.db.models.deletion


def grant_receipt_access(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    quote = schema_editor.connection.ops.quote_name
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE TRIGGER resolution_requests_append_only BEFORE UPDATE OR DELETE ON gotrendlabs_market_resolution_requests FOR EACH ROW EXECUTE FUNCTION gotrendlabs_reject_integrity_mutation()")
        roles = {"gotrendlabs_fastapi", os.environ.get("FASTAPI_POSTGRES_USER")}
        for role in sorted(r for r in roles if r):
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", [role])
            if cursor.fetchone():
                cursor.execute(f"GRANT SELECT, INSERT ON gotrendlabs_market_resolution_requests TO {quote(role)}")
                cursor.execute(f"GRANT USAGE, SELECT ON SEQUENCE gotrendlabs_market_resolution_requests_id_seq TO {quote(role)}")


class Migration(migrations.Migration):
    dependencies = [("markets", "0036_simplify_resolution_agenda")]
    operations = [migrations.CreateModel(
        name="MarketResolutionRequest",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("idempotency_key", models.UUIDField(unique=True)),
            ("request_hash", models.CharField(max_length=64)),
            ("seal_due_at", models.DateTimeField()),
            ("created_at", models.DateTimeField()),
            ("market", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="resolution_requests", to="markets.market")),
        ],
        options={"db_table": "gotrendlabs_market_resolution_requests"},
    ), migrations.RunPython(grant_receipt_access, migrations.RunPython.noop)]
