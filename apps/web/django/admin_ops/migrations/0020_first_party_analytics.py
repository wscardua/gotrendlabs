from django.db import migrations


TABLES = (
    "gotrendlabs_analytics_visitors",
    "gotrendlabs_analytics_sessions",
    "gotrendlabs_analytics_views",
    "gotrendlabs_analytics_events",
)


def create_analytics(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE gotrendlabs_analytics_visitors (
                id uuid PRIMARY KEY,
                first_seen_at timestamptz NOT NULL DEFAULT now(),
                last_seen_at timestamptz NOT NULL DEFAULT now()
            )
        """)
        cursor.execute("""
            CREATE TABLE gotrendlabs_analytics_sessions (
                id uuid PRIMARY KEY,
                visitor_id uuid NOT NULL REFERENCES gotrendlabs_analytics_visitors(id),
                platform varchar(16) NOT NULL CHECK (platform IN ('web', 'mobile')),
                started_at timestamptz NOT NULL DEFAULT now(),
                last_seen_at timestamptz NOT NULL DEFAULT now(),
                entry_screen varchar(120) NOT NULL DEFAULT '',
                referrer_host varchar(255) NOT NULL DEFAULT '',
                utm_source varchar(120) NOT NULL DEFAULT '',
                utm_medium varchar(120) NOT NULL DEFAULT '',
                utm_campaign varchar(120) NOT NULL DEFAULT '',
                country_code varchar(2),
                region_code varchar(20),
                city_name varchar(120),
                geo_accuracy_radius_km integer,
                geo_database_version varchar(32)
            )
        """)
        cursor.execute("""
            CREATE TABLE gotrendlabs_analytics_views (
                id uuid PRIMARY KEY,
                session_id uuid NOT NULL REFERENCES gotrendlabs_analytics_sessions(id),
                screen_key varchar(120) NOT NULL,
                started_at timestamptz NOT NULL DEFAULT now()
            )
        """)
        cursor.execute("""
            CREATE TABLE gotrendlabs_analytics_events (
                id uuid PRIMARY KEY,
                session_id uuid NOT NULL REFERENCES gotrendlabs_analytics_sessions(id),
                view_id uuid REFERENCES gotrendlabs_analytics_views(id),
                user_id bigint,
                name varchar(60) NOT NULL,
                platform varchar(16) NOT NULL,
                actor_type varchar(16) NOT NULL,
                auth_state varchar(16) NOT NULL,
                screen_key varchar(120) NOT NULL DEFAULT '',
                target_key varchar(120) NOT NULL DEFAULT '',
                occurred_at timestamptz NOT NULL,
                received_at timestamptz NOT NULL DEFAULT now(),
                properties jsonb NOT NULL DEFAULT '{}'::jsonb
            )
        """)
        cursor.execute("CREATE INDEX gtl_analytics_events_time ON gotrendlabs_analytics_events (received_at DESC)")
        cursor.execute("CREATE INDEX gtl_analytics_events_name_time ON gotrendlabs_analytics_events (name, received_at DESC)")
        cursor.execute("CREATE INDEX gtl_analytics_events_session_time ON gotrendlabs_analytics_events (session_id, occurred_at)")
        cursor.execute("CREATE INDEX gtl_analytics_events_user_time ON gotrendlabs_analytics_events (user_id, occurred_at) WHERE user_id IS NOT NULL")
        cursor.execute("CREATE INDEX gtl_analytics_sessions_geo ON gotrendlabs_analytics_sessions (country_code, region_code, city_name, started_at DESC)")
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'gotrendlabs_fastapi'")
        if cursor.fetchone():
            for table in TABLES:
                cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {table} TO gotrendlabs_fastapi")
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'gotrendlabs_django'")
        if cursor.fetchone():
            for table in TABLES:
                cursor.execute(f"GRANT SELECT, DELETE ON TABLE {table} TO gotrendlabs_django")


def drop_analytics(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for table in reversed(TABLES):
            cursor.execute(f"DROP TABLE {table}")


class Migration(migrations.Migration):
    dependencies = [("admin_ops", "0019_siteconfig_seal_window_db_default"), ("accounts", "0024_grant_mfa_runtime_permissions")]
    operations = [migrations.RunPython(create_analytics, drop_analytics)]
