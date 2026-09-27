"""Run Django migrations using migration-only database credentials."""

import os
from pathlib import Path
import sys

from config.env import load_env_file


def main():
    root = Path(__file__).resolve().parents[2]
    load_env_file(root / ".env")
    if os.environ.get("GOTRENDLABS_ENV", "").lower() not in {"prod", "production"}:
        load_env_file(root / ".env.migrate.local")
    user = os.environ.get("MIGRATION_POSTGRES_USER")
    password = os.environ.get("MIGRATION_POSTGRES_PASSWORD")
    if not user or not password:
        raise RuntimeError("MIGRATION_POSTGRES_USER/PASSWORD are required for migrations")
    os.environ["DJANGO_POSTGRES_USER"] = user
    os.environ["DJANGO_POSTGRES_PASSWORD"] = password
    if os.environ.get("MIGRATION_POSTGRES_DB"):
        os.environ["DJANGO_POSTGRES_DB"] = os.environ["MIGRATION_POSTGRES_DB"]
    if os.environ.get("MIGRATION_POSTGRES_HOST"):
        os.environ["DJANGO_POSTGRES_HOST"] = os.environ["MIGRATION_POSTGRES_HOST"]
    if os.environ.get("MIGRATION_POSTGRES_PORT"):
        os.environ["DJANGO_POSTGRES_PORT"] = os.environ["MIGRATION_POSTGRES_PORT"]
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(["manage.py", "migrate", *sys.argv[1:]])


if __name__ == "__main__":
    main()
