from django.db import migrations


SQL = """
CREATE TABLE gotrendlabs_analytics_history_days (
    day date PRIMARY KEY,
    source_events bigint NOT NULL CHECK (source_events >= 0),
    consolidated_at timestamptz NOT NULL DEFAULT now(),
    source_max_received_at timestamptz,
    raw_pruned boolean NOT NULL DEFAULT false,
    CHECK (source_events = 0 OR source_max_received_at IS NOT NULL)
);
CREATE TABLE gotrendlabs_analytics_history_counts (
    day date NOT NULL REFERENCES gotrendlabs_analytics_history_days(day) ON DELETE CASCADE,
    market_id bigint NOT NULL DEFAULT 0,
    platform varchar(16) NOT NULL,
    actor_type varchar(16) NOT NULL,
    event_name varchar(60) NOT NULL,
    events bigint NOT NULL CHECK (events >= 0),
    PRIMARY KEY (day, market_id, platform, actor_type, event_name)
);
CREATE INDEX analytics_history_counts_market_day ON gotrendlabs_analytics_history_counts(market_id, day);
CREATE TABLE gotrendlabs_analytics_history_actors (
    day date NOT NULL REFERENCES gotrendlabs_analytics_history_days(day) ON DELETE CASCADE,
    actor_kind varchar(16) NOT NULL CHECK (actor_kind IN ('visitor', 'registered')),
    actor_key varchar(64) NOT NULL,
    market_id bigint NOT NULL DEFAULT 0,
    platform varchar(16) NOT NULL,
    cohort_day date,
    active_view boolean NOT NULL DEFAULT false,
    different_session boolean NOT NULL DEFAULT false,
    PRIMARY KEY(day, actor_kind, actor_key, market_id, platform)
);
CREATE INDEX analytics_history_actors_period ON gotrendlabs_analytics_history_actors(actor_kind, day, actor_key);
CREATE INDEX analytics_history_actors_market ON gotrendlabs_analytics_history_actors(market_id, day, actor_kind);
CREATE TABLE gotrendlabs_analytics_history_funnel (
    day date NOT NULL REFERENCES gotrendlabs_analytics_history_days(day) ON DELETE CASCADE,
    market_id bigint NOT NULL DEFAULT 0,
    started bigint NOT NULL DEFAULT 0,
    chosen bigint NOT NULL DEFAULT 0,
    previewed bigint NOT NULL DEFAULT 0,
    submit_clicked bigint NOT NULL DEFAULT 0,
    eligible bigint NOT NULL DEFAULT 0,
    abandoned_before_choice bigint NOT NULL DEFAULT 0,
    abandoned_after_choice bigint NOT NULL DEFAULT 0,
    PRIMARY KEY(day,market_id)
);
CREATE TABLE gotrendlabs_analytics_market_publication (
    market_id bigint PRIMARY KEY,
    published_at timestamptz NOT NULL,
    category_id bigint NOT NULL,
    category_name varchar(80) NOT NULL,
    subcategory_id bigint NOT NULL,
    subcategory_name varchar(80) NOT NULL,
    event_id bigint,
    event_name varchar(80),
    kind varchar(20) NOT NULL,
    close_at timestamptz,
    provenance varchar(32) NOT NULL CHECK (provenance IN ('observed_publication','reconstructed_current')),
    captured_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX analytics_market_publication_segment ON gotrendlabs_analytics_market_publication(category_id,subcategory_id,event_id,kind,published_at);
"""


def create(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        cursor.execute("ALTER TABLE gotrendlabs_analytics_visitors ADD COLUMN first_session_id uuid")
        cursor.execute("""UPDATE gotrendlabs_analytics_visitors v SET first_session_id=s.id
            FROM (SELECT DISTINCT ON (visitor_id) visitor_id,id FROM gotrendlabs_analytics_sessions
                  ORDER BY visitor_id,started_at,id) s WHERE s.visitor_id=v.id""")
        cursor.execute("ALTER TABLE gotrendlabs_analytics_events ADD COLUMN market_id bigint")
        cursor.execute("CREATE INDEX analytics_events_occurred_at ON gotrendlabs_analytics_events(occurred_at)")
        cursor.execute("CREATE INDEX analytics_events_market_time ON gotrendlabs_analytics_events(market_id,occurred_at) WHERE market_id IS NOT NULL")
        cursor.execute("""UPDATE gotrendlabs_analytics_events e SET market_id=m.id
            FROM gotrendlabs_markets m WHERE m.slug=e.properties->>'market_slug'""")
        cursor.execute(SQL)
        cursor.execute("""
            INSERT INTO gotrendlabs_analytics_market_publication
                (market_id,published_at,category_id,category_name,subcategory_id,subcategory_name,
                 event_id,event_name,kind,close_at,provenance)
            SELECT m.id,m.published_at,m.category_id,c.name,m.subcategory_id,s.name,
                   m.event_id,e.name,m.kind,m.close_at,'reconstructed_current'
            FROM gotrendlabs_markets m
            JOIN gotrendlabs_market_categories c ON c.id=m.category_id
            JOIN gotrendlabs_market_subcategories s ON s.id=m.subcategory_id
            LEFT JOIN gotrendlabs_market_events e ON e.id=m.event_id
            WHERE m.published_at IS NOT NULL
        """)
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='gotrendlabs_fastapi'")
        if cursor.fetchone():
            for table in ('gotrendlabs_analytics_history_days', 'gotrendlabs_analytics_history_counts', 'gotrendlabs_analytics_history_actors', 'gotrendlabs_analytics_history_funnel', 'gotrendlabs_analytics_market_publication'):
                cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO gotrendlabs_fastapi")


def drop(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for table in ('gotrendlabs_analytics_market_publication', 'gotrendlabs_analytics_history_funnel', 'gotrendlabs_analytics_history_actors', 'gotrendlabs_analytics_history_counts', 'gotrendlabs_analytics_history_days'):
            cursor.execute(f"DROP TABLE {table}")
        cursor.execute("DROP INDEX analytics_events_market_time")
        cursor.execute("DROP INDEX analytics_events_occurred_at")
        cursor.execute("ALTER TABLE gotrendlabs_analytics_events DROP COLUMN market_id")
        cursor.execute("ALTER TABLE gotrendlabs_analytics_visitors DROP COLUMN first_session_id")


class Migration(migrations.Migration):
    dependencies = [("admin_ops", "0026_deleted_market_thumbnail_receipts")]
    operations = [migrations.RunPython(create, drop)]
