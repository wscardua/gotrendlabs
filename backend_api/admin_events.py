from datetime import datetime, timezone


def record_admin_event(cursor, actor_id, action, entity_type, entity_identifier, note=""):
    cursor.execute(
        """
        INSERT INTO orynth_admin_events (actor_id, action, entity_type, entity_identifier, note, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (actor_id, action, entity_type, entity_identifier, note or "", datetime.now(timezone.utc)),
    )
