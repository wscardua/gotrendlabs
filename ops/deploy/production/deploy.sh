#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gotrendlabs}"
BRANCH="${BRANCH:-main}"
REPO_URL="${REPO_URL:-}"
COMPOSE_FILE="ops/deploy/production/docker-compose.yml"
ENV_FILE=".env.prod"
AUTH_ENV_FILE=".env.auth.prod"
FASTAPI_DB_ENV_FILE=".env.fastapi-db.prod"
MIGRATION_ENV_FILE=".env.migrate.prod"

if [[ ! -d "$APP_DIR/.git" ]]; then
  if [[ -z "$REPO_URL" ]]; then
    echo "REPO_URL is required when $APP_DIR is not initialized as a git repository." >&2
    exit 1
  fi

  mkdir -p "$APP_DIR"

  if [[ -n "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name "$ENV_FILE" ! -name "$AUTH_ENV_FILE" ! -name "$FASTAPI_DB_ENV_FILE" ! -name "$MIGRATION_ENV_FILE" ! -name ".git" -print -quit)" ]]; then
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

docker compose -f "$COMPOSE_FILE" --profile ops build
docker compose -f "$COMPOSE_FILE" run --rm fastapi python -c 'from packages.security.passwords import require_password_pepper; require_password_pepper()'
docker compose -f "$COMPOSE_FILE" run --rm fastapi python -c 'from apps.api.backend_api.mfa import require_totp_encryption_key; require_totp_encryption_key()'
docker compose -f "$COMPOSE_FILE" run --rm migrate python -m ops.scripts.auth_db_boundary apply
docker compose -f "$COMPOSE_FILE" run --rm migrate python -m ops.scripts.migrate_with_role --noinput
docker compose -f "$COMPOSE_FILE" run --rm migrate python -m ops.scripts.auth_db_boundary apply
docker compose -f "$COMPOSE_FILE" run --rm django python -m ops.scripts.auth_db_boundary check
docker compose -f "$COMPOSE_FILE" run --rm fastapi python -m ops.scripts.auth_db_boundary check-api
docker compose -f "$COMPOSE_FILE" run --rm django python manage.py collectstatic --noinput
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
docker compose -f "$COMPOSE_FILE" ps
