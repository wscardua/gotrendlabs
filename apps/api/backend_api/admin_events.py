from datetime import datetime, timezone


def record_admin_event(cursor, actor_id, action, entity_type, entity_identifier, note="", *, integration_id=None, responsible_id=None, request_id="", execution_id=""):
    cursor.execute(
        """
        INSERT INTO gotrendlabs_admin_events (actor_id, action, entity_type, entity_identifier, note, created_at, integration_id, responsible_id, request_id, execution_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (actor_id, action, entity_type, entity_identifier, note or "", datetime.now(timezone.utc), integration_id, responsible_id, request_id, execution_id),
    )
