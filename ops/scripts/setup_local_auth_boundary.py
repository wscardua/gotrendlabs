"""Provision the local migration role and password boundary after Django migrations."""

import os
from pathlib import Path
import secrets
import subprocess

from config.env import load_env_file
from ops.scripts.auth_db_boundary import apply_boundary, check_boundary


ROOT = Path(__file__).resolve().parents[2]


def _admin_psql(statement):
    database = os.environ.get("POSTGRES_DB", "gotrendlabs")
    admin_role = None
    for candidate in ("gotrendlabs_postgres_admin", "gotrendlabs"):
        probe = subprocess.run(
            ["docker", "exec", "gotrendlabs-postgres", "psql", "-t", "-A", "-U", candidate,
             "-d", database, "-c", "SELECT rolsuper FROM pg_roles WHERE rolname = current_user"],
            text=True, capture_output=True, check=False,
        )
        if probe.returncode == 0 and probe.stdout.strip() == "t":
            admin_role = candidate
            break
    if admin_role is None:
        raise RuntimeError("No local PostgreSQL superuser is available through the postgres container")
    result = subprocess.run(
        ["docker", "exec", "-i", "gotrendlabs-postgres", "psql", "-t", "-A", "-v", "ON_ERROR_STOP=1",
         "-U", admin_role, "-d", database],
        input=statement,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Local PostgreSQL role setup failed")
    return result.stdout.strip()


def main():
    load_env_file(ROOT / ".env")
    path = ROOT / ".env.migrate.local"
    if path.exists():
        if path.stat().st_mode & 0o077:
            raise RuntimeError(".env.migrate.local must have permissions 0600")
        load_env_file(path)
        password = os.environ["MIGRATION_POSTGRES_PASSWORD"]
    else:
        if _admin_psql("SELECT 1 FROM pg_roles WHERE rolname = 'gotrendlabs_migrator_local';"):
            raise RuntimeError("Local migrator exists without .env.migrate.local; recover its credential before proceeding")
        password = secrets.token_urlsafe(32)
    sql = f"""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gotrendlabs_migrator_local') THEN
            CREATE ROLE gotrendlabs_migrator_local LOGIN INHERIT PASSWORD '{password}';
          END IF;
        END $$;
        GRANT gotrendlabs_django TO gotrendlabs_migrator_local;
        GRANT USAGE, CREATE ON SCHEMA public TO gotrendlabs_migrator_local;
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gotrendlabs_auth_owner') THEN
            CREATE ROLE gotrendlabs_auth_owner NOLOGIN;
          END IF;
        END $$;
        GRANT USAGE, CREATE ON SCHEMA public TO gotrendlabs_auth_owner;
        GRANT gotrendlabs_auth_owner TO gotrendlabs_migrator_local;
    """
    _admin_psql(sql)
    if not path.exists():
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write("MIGRATION_POSTGRES_USER=gotrendlabs_migrator_local\n")
            file.write(f"MIGRATION_POSTGRES_PASSWORD={password}\n")
    load_env_file(path)
    apply_boundary()
    check_boundary()


if __name__ == "__main__":
    main()
