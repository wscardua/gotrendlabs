#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gotrendlabs}"
BRANCH="${BRANCH:-main}"
REPO_URL="${REPO_URL:-}"
COMPOSE_FILE="ops/deploy/production/docker-compose.yml"
MCP_COMPOSE_FILE="ops/deploy/mcp/docker-compose.override.yml"
COMPOSE=(docker compose -f "$COMPOSE_FILE" -f "$MCP_COMPOSE_FILE" --profile mcp)
ENV_FILE=".env.prod"
AUTH_ENV_FILE=".env.auth.prod"
FASTAPI_DB_ENV_FILE=".env.fastapi-db.prod"
MIGRATION_ENV_FILE=".env.migrate.prod"
THUMBNAIL_ENV_FILE=".env.thumbnails.prod"
WRITERS=(django fastapi daemon mcp)

if [[ ! -d "$APP_DIR/.git" ]]; then
  if [[ -z "$REPO_URL" ]]; then
    echo "REPO_URL is required when $APP_DIR is not initialized as a git repository." >&2
    exit 1
  fi

  mkdir -p "$APP_DIR"

  if [[ -n "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name "$ENV_FILE" ! -name "$AUTH_ENV_FILE" ! -name "$FASTAPI_DB_ENV_FILE" ! -name "$MIGRATION_ENV_FILE" ! -name "$THUMBNAIL_ENV_FILE" ! -name ".env.mcp.prod" ! -name ".env.mcp-api.prod" ! -name ".mcp-config.lock" ! -name ".git" -print -quit)" ]]; then
    echo "$APP_DIR contains unexpected files and cannot be bootstrapped safely." >&2
    exit 1
  fi

  git -C "$APP_DIR" init
  git -C "$APP_DIR" remote add origin "$REPO_URL"
  git -C "$APP_DIR" fetch --depth 1 origin "$BRANCH"
  git -C "$APP_DIR" checkout -B "$BRANCH" FETCH_HEAD
fi

cd "$APP_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $APP_DIR/$ENV_FILE. Create it before deploying." >&2
  exit 1
fi
if [[ ! -f "$AUTH_ENV_FILE" ]]; then
  echo "Missing $APP_DIR/$AUTH_ENV_FILE. Create it before deploying." >&2
  exit 1
fi
if [[ ! -f "$FASTAPI_DB_ENV_FILE" ]]; then
  echo "Missing $APP_DIR/$FASTAPI_DB_ENV_FILE. Create it before deploying." >&2
  exit 1
fi
if [[ ! -f "$MIGRATION_ENV_FILE" ]]; then
  echo "Missing $APP_DIR/$MIGRATION_ENV_FILE. Create it before deploying." >&2
  exit 1
fi
if grep -Eq '^[[:space:]]*(FASTAPI_POSTGRES_|POSTGRES_(USER|PASSWORD))[A-Z_]*[[:space:]]*=' "$ENV_FILE" "$AUTH_ENV_FILE"; then
  echo "Database credentials with password-write authority must not be in shared or pepper env files." >&2
  exit 1
fi
if ! grep -Eq '^[[:space:]]*FASTAPI_POSTGRES_USER[[:space:]]*=[[:space:]]*[^[:space:]#]+' "$FASTAPI_DB_ENV_FILE" ||
   ! grep -Eq '^[[:space:]]*FASTAPI_POSTGRES_PASSWORD[[:space:]]*=[[:space:]]*[^[:space:]#]+' "$FASTAPI_DB_ENV_FILE"; then
  echo "FASTAPI_POSTGRES_USER/PASSWORD are required in $FASTAPI_DB_ENV_FILE." >&2
  exit 1
fi
if grep -Eq '^[[:space:]]*GOTRENDLABS_PASSWORD_PEPPER[[:space:]]*=' "$FASTAPI_DB_ENV_FILE"; then
  echo "The pepper must exist only in $AUTH_ENV_FILE." >&2
  exit 1
fi
if grep -Eq '^[[:space:]]*GOTRENDLABS_TOTP_ENCRYPTION_KEY[[:space:]]*=' "$ENV_FILE" "$FASTAPI_DB_ENV_FILE" "$MIGRATION_ENV_FILE"; then
  echo "The TOTP encryption key must exist only in $AUTH_ENV_FILE." >&2
  exit 1
fi
if ! grep -Eq '^[[:space:]]*GOTRENDLABS_TOTP_ENCRYPTION_KEY[[:space:]]*=[[:space:]]*[^[:space:]#]+' "$AUTH_ENV_FILE"; then
  echo "GOTRENDLABS_TOTP_ENCRYPTION_KEY is required in $AUTH_ENV_FILE." >&2
  exit 1
fi
if grep -Eq '^[[:space:]]*FASTAPI_POSTGRES_[A-Z_]*[[:space:]]*=' "$MIGRATION_ENV_FILE"; then
  echo "FastAPI runtime credentials must exist only in $FASTAPI_DB_ENV_FILE." >&2
  exit 1
fi
if grep -Eq '^[[:space:]]*MIGRATION_POSTGRES_[A-Z_]*[[:space:]]*=' "$FASTAPI_DB_ENV_FILE"; then
  echo "Migration credentials must exist only in $MIGRATION_ENV_FILE." >&2
  exit 1
fi
if grep -Eq '^[[:space:]]*GOTRENDLABS_PASSWORD_PEPPER[[:space:]]*=' "$ENV_FILE"; then
  echo "Move GOTRENDLABS_PASSWORD_PEPPER out of $ENV_FILE and into $AUTH_ENV_FILE before deploying." >&2
  exit 1
fi
if grep -Eq '^[[:space:]]*MIGRATION_POSTGRES_(USER|PASSWORD)[[:space:]]*=' "$ENV_FILE" "$AUTH_ENV_FILE"; then
  echo "Migration credentials must exist only in $MIGRATION_ENV_FILE." >&2
  exit 1
fi
if grep -Eq '^[[:space:]]*GOTRENDLABS_PASSWORD_PEPPER[[:space:]]*=' "$MIGRATION_ENV_FILE"; then
  echo "The password pepper must exist only in $AUTH_ENV_FILE." >&2
  exit 1
fi

git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Missing compose file: $APP_DIR/$COMPOSE_FILE" >&2
  exit 1
fi

python3 ops/deploy/mcp/configure_environment.py --app-dir "$APP_DIR"

# Installing the worker secret opts into its lifecycle, independently of the
# runtime/database kill switches. Redeploy paused workers too; never leave an
# old executor running against a migrated schema or remove it as an orphan.
if [[ -f "$THUMBNAIL_ENV_FILE" ]]; then
  COMPOSE+=(--profile thumbnails)
  WRITERS+=(thumbnail-worker)
fi

"${COMPOSE[@]}" --profile ops build
# Existing media volumes predate this subdirectory. Create only that directory,
# preserving every existing file, before FastAPI's volume.subpath is mounted.
"${COMPOSE[@]}" run --rm --no-deps --user root migrate python -c 'import os,pwd; from pathlib import Path; u=pwd.getpwnam("gotrendlabs"); dirs=[Path("/app/media")/name for name in ("market_thumbnails","badge_images")]; [(p.mkdir(parents=True,exist_ok=True),os.chown(p,u.pw_uid,u.pw_gid)) for p in dirs]'
"${COMPOSE[@]}" run --rm fastapi python -c 'from packages.security.passwords import require_password_pepper; require_password_pepper()'
"${COMPOSE[@]}" run --rm fastapi python -c 'from apps.api.backend_api.mfa import require_totp_encryption_key; require_totp_encryption_key()'
# Prevent the old runtime from writing while the editorial backfill is applied.
# On migration failure, leave writers stopped for explicit recovery; do not
# restart an application version that cannot enforce the universal gate.
"${COMPOSE[@]}" stop "${WRITERS[@]}"
"${COMPOSE[@]}" run --rm migrate python -m ops.scripts.auth_db_boundary apply
"${COMPOSE[@]}" run --rm migrate python -m ops.scripts.migrate_with_role --noinput
"${COMPOSE[@]}" run --rm migrate python -m ops.scripts.auth_db_boundary apply
"${COMPOSE[@]}" run --rm django python -m ops.scripts.auth_db_boundary check
"${COMPOSE[@]}" run --rm fastapi python -m ops.scripts.auth_db_boundary check-api
"${COMPOSE[@]}" run --rm django python manage.py collectstatic --noinput
"${COMPOSE[@]}" up -d --wait --wait-timeout 180 --remove-orphans
"${COMPOSE[@]}" exec -T proxy caddy validate --config /etc/caddy/Caddyfile
"${COMPOSE[@]}" exec -T proxy caddy reload --config /etc/caddy/Caddyfile
"${COMPOSE[@]}" exec -T mcp python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8002/health", timeout=5)'
"${COMPOSE[@]}" ps
