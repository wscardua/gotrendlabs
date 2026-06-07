#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gotrendlabs}"
BRANCH="${BRANCH:-main}"
REPO_URL="${REPO_URL:-}"
COMPOSE_FILE="ops/deploy/production/docker-compose.yml"
ENV_FILE=".env.prod"

if [[ ! -d "$APP_DIR/.git" ]]; then
  if [[ -z "$REPO_URL" ]]; then
    echo "REPO_URL is required when $APP_DIR is not initialized as a git repository." >&2
    exit 1
  fi

  mkdir -p "$APP_DIR"

  if [[ -n "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name "$ENV_FILE" ! -name ".git" -print -quit)" ]]; then
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

git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Missing compose file: $APP_DIR/$COMPOSE_FILE" >&2
  exit 1
fi

docker compose -f "$COMPOSE_FILE" build
docker compose -f "$COMPOSE_FILE" run --rm django python manage.py migrate
docker compose -f "$COMPOSE_FILE" run --rm django python manage.py collectstatic --noinput
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
docker compose -f "$COMPOSE_FILE" ps
