#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/gotrendlabs}"
BRANCH="${BRANCH:-main}"
REPO_URL="${REPO_URL:-}"
COMPOSE_FILE="deploy/production/docker-compose.yml"
ENV_FILE=".env.prod"
CERT_DIR=".runtime/caddy-certs"

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

HTTPS_SITE="$(grep -E "^GOTRENDLABS_HTTPS_SITE=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)"
if [[ -n "$HTTPS_SITE" && ! -f "$CERT_DIR/ip.crt" ]]; then
  HTTPS_HOST="${HTTPS_SITE#https://}"
  HTTPS_HOST="${HTTPS_HOST%%/*}"
  HTTPS_HOST="${HTTPS_HOST%%:*}"
  if [[ -z "$HTTPS_HOST" ]]; then
    HTTPS_HOST="$(grep -E "^GOTRENDLABS_ALLOWED_HOSTS=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- | cut -d, -f1 || true)"
  fi

  mkdir -p "$CERT_DIR"
  if [[ "$HTTPS_HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    SAN="IP:$HTTPS_HOST"
  else
    SAN="DNS:$HTTPS_HOST"
  fi

  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout "$CERT_DIR/ip.key" \
    -out "$CERT_DIR/ip.crt" \
    -subj "/CN=$HTTPS_HOST" \
    -addext "subjectAltName=$SAN"
fi

docker compose -f "$COMPOSE_FILE" build
docker compose -f "$COMPOSE_FILE" run --rm django python manage.py migrate
docker compose -f "$COMPOSE_FILE" run --rm django python manage.py collectstatic --noinput
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
docker compose -f "$COMPOSE_FILE" ps
