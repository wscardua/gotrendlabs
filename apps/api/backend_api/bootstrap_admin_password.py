"""Set an existing bootstrap administrator's password through the API credential code."""

import argparse
import getpass
import os
from pathlib import Path

from config.env import load_env_file

from apps.api.backend_api.db import get_connection
from apps.api.backend_api.security import make_password


def set_admin_password(username, password):
    if not 8 <= len(password) <= 128:
        raise ValueError("Password must contain between 8 and 128 characters.")
    encoded = make_password(password)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE gotrendlabs_users SET password = %s
                   WHERE username = %s AND is_staff AND is_superuser AND is_active
                   RETURNING id""",
                (encoded, username),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError("Active staff/superuser account not found.")
            cursor.execute(
                """UPDATE gotrendlabs_auth_sessions SET revoked_at = NOW()
                   WHERE user_id = %s AND revoked_at IS NULL""",
                (row["id"],),
            )
            cursor.execute(
                """INSERT INTO gotrendlabs_admin_events
                   (actor_id, action, entity_type, entity_identifier, note, created_at)
                   VALUES (NULL, 'user.bootstrap_password_set', 'user', %s,
                           'FastAPI operator CLI', NOW())""",
                (str(row["id"]),),
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True, help="Existing active staff/superuser username")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    load_env_file(root / ".env")
    if os.environ.get("GOTRENDLABS_ENV", "").lower() not in {"prod", "production"}:
        load_env_file(root / ".env.api.local")
    password = getpass.getpass("New admin password: ")
    if password != getpass.getpass("Confirm password: "):
        parser.error("Passwords do not match.")
    try:
        set_admin_password(args.username, password)
    except ValueError as exc:
        parser.error(str(exc))
    print("Admin password updated; previous API sessions revoked.")


if __name__ == "__main__":
    main()
