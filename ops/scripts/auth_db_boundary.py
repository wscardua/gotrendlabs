"""Apply or verify the password-column boundary with distinct database roles."""

import argparse
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg import sql

from config.env import load_env_file


ROOT = Path(__file__).resolve().parents[2]
OWNER = "gotrendlabs_auth_owner"


def _load_environment(action):
    load_env_file(ROOT / ".env")
    if action == "apply" and os.environ.get("GOTRENDLABS_ENV", "").lower() not in {"prod", "production"}:
        load_env_file(ROOT / ".env.migrate.local")
    if action in {"check-api", "inventory"} and os.environ.get("GOTRENDLABS_ENV", "").lower() not in {"prod", "production"}:
        load_env_file(ROOT / ".env.api.local")


def _config(prefix):
    common = "DJANGO_" if prefix == "MIGRATION_" else prefix
    return {
        "dbname": os.environ.get(f"{prefix}POSTGRES_DB") or os.environ.get(f"{common}POSTGRES_DB") or os.environ.get("POSTGRES_DB"),
        "user": os.environ.get(f"{prefix}POSTGRES_USER"),
        "password": os.environ.get(f"{prefix}POSTGRES_PASSWORD"),
        "host": os.environ.get(f"{prefix}POSTGRES_HOST") or os.environ.get(f"{common}POSTGRES_HOST") or os.environ.get("POSTGRES_HOST"),
        "port": os.environ.get(f"{prefix}POSTGRES_PORT") or os.environ.get(f"{common}POSTGRES_PORT") or os.environ.get("POSTGRES_PORT"),
    }


def apply_boundary():
    config = _config("MIGRATION_")
    if not config["user"] or not config["password"]:
        raise RuntimeError("MIGRATION_POSTGRES_USER/PASSWORD are required for the auth boundary")
    with psycopg.connect(**config, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('gotrendlabs_users') AS users_table")
            if cursor.fetchone()["users_table"] is None:
                print("Auth table not created yet; apply the boundary after migrations.")
                return
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (OWNER,))
            if cursor.fetchone() is None:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(OWNER)))
            cursor.execute("SELECT has_schema_privilege(%s, 'public', 'CREATE') AS allowed", (OWNER,))
            if not cursor.fetchone()["allowed"]:
                cursor.execute(sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(sql.Identifier(OWNER)))
            cursor.execute("SELECT current_user AS role")
            migration_role = cursor.fetchone()["role"]
            cursor.execute("SELECT pg_has_role(current_user, %s, 'member') AS member", (OWNER,))
            if not cursor.fetchone()["member"]:
                cursor.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(OWNER), sql.Identifier(migration_role)))
            cursor.execute((ROOT / "ops/sql/auth_password_boundary.sql").read_text(encoding="utf-8"))
            _assert_boundary(cursor)
    print("Auth database boundary applied and privileges verified.")


def _assert_boundary(cursor):
    cursor.execute(
        """SELECT pg_get_userbyid(c.relowner) AS owner,
                  has_column_privilege('gotrendlabs_django', c.oid, 'password', 'UPDATE') AS django_password_update,
                  has_column_privilege('gotrendlabs_django', c.oid, 'first_name', 'UPDATE') AS django_profile_update,
                  has_table_privilege('gotrendlabs_django', c.oid, 'INSERT') AS django_insert,
                  has_column_privilege('gotrendlabs_fastapi', c.oid, 'password', 'UPDATE') AS fastapi_password_update,
                  has_table_privilege('gotrendlabs_fastapi', c.oid, 'INSERT') AS fastapi_insert,
                  pg_has_role('gotrendlabs_django', 'gotrendlabs_auth_owner', 'member') AS django_owner_member,
                  EXISTS (SELECT 1 FROM pg_trigger t WHERE t.tgrelid = c.oid
                          AND t.tgname = 'gotrendlabs_guard_django_password_write'
                          AND t.tgenabled = 'O') AS trigger_enabled
           FROM pg_class c WHERE c.oid = 'gotrendlabs_users'::regclass"""
    )
    row = cursor.fetchone()
    if (row["owner"] != OWNER or row["django_password_update"] or
            not row["django_profile_update"] or not row["django_insert"] or
            not row["fastapi_password_update"] or not row["fastapi_insert"] or
            row["django_owner_member"] or not row["trigger_enabled"]):
        raise RuntimeError("Auth database ownership or password privileges are unsafe")
    cursor.execute("SELECT pg_get_userbyid(p.proowner) AS owner FROM pg_proc p WHERE p.oid = 'gotrendlabs_guard_django_password_write()'::regprocedure")
    if cursor.fetchone()["owner"] != OWNER:
        raise RuntimeError("Auth password trigger function has an unsafe owner")


def check_boundary():
    leaked = [name for name in (
        "FASTAPI_POSTGRES_USER", "FASTAPI_POSTGRES_PASSWORD", "MIGRATION_POSTGRES_USER",
        "MIGRATION_POSTGRES_PASSWORD", "POSTGRES_USER", "POSTGRES_PASSWORD"
    ) if os.environ.get(name)]
    if leaked:
        raise RuntimeError("Django runtime exposes another database credential: " + ", ".join(leaked))
    config = _config("DJANGO_")
    with psycopg.connect(**config, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            _assert_boundary(cursor)
            cursor.execute("SELECT current_user AS role")
            if cursor.fetchone()["role"] != "gotrendlabs_django":
                raise RuntimeError("Runtime Django must use the gotrendlabs_django database role")
    print("Auth database boundary is active for the Django runtime role.")


def check_api_boundary():
    config = _config("FASTAPI_")
    if not config["user"] or not config["password"]:
        raise RuntimeError("FASTAPI_POSTGRES_USER/PASSWORD are required for the API runtime")
    with psycopg.connect(**config, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT current_user AS role,
                          has_column_privilege(current_user, 'gotrendlabs_users', 'password', 'UPDATE') AS can_update_password"""
            )
            row = cursor.fetchone()
            if row["role"] != "gotrendlabs_fastapi" or not row["can_update_password"]:
                raise RuntimeError("FastAPI runtime must use the password-authorized database role")
    print("Auth database boundary is active for the FastAPI runtime role.")


def inventory_passwords():
    with psycopg.connect(**_config("FASTAPI_"), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT COUNT(*) AS total,
                          COUNT(*) FILTER (WHERE starts_with(password, 'argon2id_pepper_v1$')) AS argon2id_pepper_v1,
                          COUNT(*) FILTER (WHERE starts_with(password, 'pbkdf2_sha256$')) AS pbkdf2,
                          COUNT(*) FILTER (WHERE password = '' OR starts_with(password, '!')) AS unusable,
                          COUNT(*) FILTER (WHERE is_staff OR is_superuser) AS administrators
                   FROM gotrendlabs_users"""
            )
            print(dict(cursor.fetchone()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "check", "check-api", "inventory"))
    action = parser.parse_args().action
    _load_environment(action)
    {"apply": apply_boundary, "check": check_boundary, "check-api": check_api_boundary,
     "inventory": inventory_passwords}[action]()


if __name__ == "__main__":
    main()
