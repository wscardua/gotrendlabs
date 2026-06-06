from django.db import migrations


REPLACEMENTS = [
    ("/Users/williamsca/Documents/gotrendlabs", "/Users/williamsca/Documents/gotrendlabs"),
    ("GoTrendLabs", "GoTrendLabs"),
    ("GTL Credits", "GTL Credits"),
    ("GTL Credits", "GTL Credits"),
    ("GoTrendLabs", "GoTrendLabs"),
    ("GOTRENDLABS", "GOTRENDLABS"),
    ("gotrendlabs", "gotrendlabs"),
    ("GT₵", "GT₵"),
    ("_gtl", "_gtl"),
]


def clean_identifier(name):
    cleaned = name
    for old, new in REPLACEMENTS:
        cleaned = cleaned.replace(old, new)
    if len(cleaned) <= 63:
        return cleaned
    import hashlib

    digest = hashlib.md5(name.encode("utf-8"), usedforsecurity=False).hexdigest()[:8]
    return f"{cleaned[:54]}_{digest}"


def cleanup_schema_identifiers(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.conname, c.conrelid::regclass::text
              FROM pg_constraint c
              JOIN pg_namespace n ON n.oid = c.connamespace
             WHERE n.nspname = 'public'
               AND (c.conname LIKE %s OR c.conname LIKE %s OR c.conname LIKE %s OR c.conname LIKE %s)
             ORDER BY c.conname
            """,
            ["%gotrendlabs%", "%GoTrendLabs%", "%GOTRENDLABS%", "%_gtl%"],
        )
        for old_name, table_name in cursor.fetchall():
            new_name = clean_identifier(old_name)
            if new_name == old_name:
                continue
            cursor.execute(
                """
                SELECT 1
                  FROM pg_constraint c
                  JOIN pg_class t ON t.oid = c.conrelid
                  JOIN pg_namespace n ON n.oid = c.connamespace
                 WHERE n.nspname = 'public'
                   AND t.oid = %s::regclass
                   AND c.conname = %s
                """,
                [table_name, new_name],
            )
            if cursor.fetchone():
                continue
            cursor.execute(
                f'ALTER TABLE "{table_name}" RENAME CONSTRAINT "{old_name}" TO "{new_name}"'
            )

        cursor.execute(
            """
            SELECT indexname
              FROM pg_indexes
             WHERE schemaname = 'public'
               AND (indexname LIKE %s OR indexname LIKE %s OR indexname LIKE %s OR indexname LIKE %s)
             ORDER BY indexname
            """,
            ["%gotrendlabs%", "%GoTrendLabs%", "%GOTRENDLABS%", "%_gtl%"],
        )
        for (old_name,) in cursor.fetchall():
            new_name = clean_identifier(old_name)
            if new_name == old_name:
                continue
            cursor.execute(
                "SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = %s",
                [new_name],
            )
            if cursor.fetchone():
                continue
            cursor.execute(f'ALTER INDEX "{old_name}" RENAME TO "{new_name}"')


def cleanup_text_residues(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name, column_name, data_type
              FROM information_schema.columns
             WHERE table_schema = 'public'
               AND data_type IN ('text', 'character varying', 'json', 'jsonb')
             ORDER BY table_name, column_name
            """
        )
        for table_name, column_name, data_type in cursor.fetchall():
            value_expr = f'"{column_name}"::text' if data_type in {"json", "jsonb"} else f'"{column_name}"'
            where_clause = " OR ".join(
                [f"strpos({value_expr}, %s) > 0" for _old, _new in REPLACEMENTS]
            )
            where_params = [old for old, _new in REPLACEMENTS]
            cursor.execute(
                f'SELECT count(*) FROM "{table_name}" WHERE {where_clause}',
                where_params,
            )
            if not cursor.fetchone()[0]:
                continue

            update_expr = value_expr
            update_params = []
            for old, new in REPLACEMENTS:
                update_expr = f"replace({update_expr}, %s, %s)"
                update_params.extend([old, new])
            cast = "::jsonb" if data_type == "jsonb" else "::json" if data_type == "json" else ""
            cursor.execute(
                f'UPDATE "{table_name}" SET "{column_name}" = ({update_expr}){cast} WHERE {where_clause}',
                update_params + where_params,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0017_gotrendlabs_email_domains"),
        ("admin_ops", "0007_gotrendlabs_rebrand"),
        ("agents", "0004_gotrendlabs_bot_identities"),
        ("markets", "0024_gotrendlabs_legacy_market_funnel_tables"),
        ("system_logs", "0002_gotrendlabs_rebrand"),
    ]

    operations = [
        migrations.RunPython(cleanup_schema_identifiers, migrations.RunPython.noop),
        migrations.RunPython(cleanup_text_residues, migrations.RunPython.noop),
    ]
