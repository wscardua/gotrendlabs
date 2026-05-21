#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/orynth}"
BRANCH="${BRANCH:-main}"
COMPOSE_FILE="deploy/production/docker-compose.yml"

cd "$APP_DIR"

git pull origin "$BRANCH"

docker compose -f "$COMPOSE_FILE" build
docker compose -f "$COMPOSE_FILE" run --rm django python manage.py migrate
docker compose -f "$COMPOSE_FILE" run --rm django python manage.py collectstatic --noinput
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
docker compose -f "$COMPOSE_FILE" ps
