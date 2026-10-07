"""Run MCP tests on isolated PostgreSQL loopback without loading provider secrets."""

import argparse
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-admin-env", required=True, type=Path)
    parser.add_argument("--database", default="gtl_mcp_pilot")
    parser.add_argument("labels", nargs="*")
    args = parser.parse_args()
    if ".prod" in args.db_admin_env.name or not re.fullmatch(
        r"gtl_mcp_[a-z0-9_]+", args.database
    ):
        parser.error("use a local administrator file and isolated gtl_mcp_ database")
    credentials = {}
    for line in args.db_admin_env.read_text().splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        if key.strip() in ("POSTGRES_USER", "POSTGRES_PASSWORD"):
            credentials[key.strip()] = value.strip().strip(chr(34)).strip(chr(39))
    if len(credentials) != 2:
        parser.error("local POSTGRES_USER and POSTGRES_PASSWORD required")
    os.environ.update(
        DJANGO_SETTINGS_MODULE="config.settings",
        POSTGRES_HOST="127.0.0.1",
        POSTGRES_PORT="5432",
        POSTGRES_DB=args.database,
        DJANGO_POSTGRES_DB=args.database,
        DJANGO_POSTGRES_HOST="127.0.0.1",
        DJANGO_POSTGRES_PORT="5432",
        DJANGO_POSTGRES_USER=credentials["POSTGRES_USER"],
        DJANGO_POSTGRES_PASSWORD=credentials["POSTGRES_PASSWORD"],
        BACKEND_API_URL="http://127.0.0.1:9",
        GOTRENDLABS_ENV="test",
        GOTRENDLABS_ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
        **{
            k: ""
            for k in (
                "FASTAPI_POSTGRES_DB",
                "FASTAPI_POSTGRES_USER",
                "FASTAPI_POSTGRES_PASSWORD",
                "FASTAPI_POSTGRES_HOST",
                "FASTAPI_POSTGRES_PORT",
            )
        },
    )
    from django.core.management import execute_from_command_line

    sys.argv = [
        "manage.py",
        "test",
        *(args.labels or ["tests.test_mcp_editorial", "tests.test_mcp_adapter"]),
        "--noinput",
    ]
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
