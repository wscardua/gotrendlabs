#!/usr/bin/env bash
set -euo pipefail

# Run on the production host through SSM. It deliberately prints only a
# confirmation, never the Secret Manager payload or the Fernet key.
APP_DIR="${APP_DIR:-/opt/gotrendlabs}"
AUTH_ENV_FILE="${AUTH_ENV_FILE:-$APP_DIR/.env.auth.prod}"
SECRET_ID="${SECRET_ID:-gotrendlabs/prod/app-secrets}"
AWS_REGION="${AWS_REGION:-us-east-1}"
export AUTH_ENV_FILE

secret_json="$(aws secretsmanager get-secret-value --region "$AWS_REGION" --secret-id "$SECRET_ID" --query SecretString --output text)"
export GOTRENDLABS_TOTP_SYNC_VALUE
GOTRENDLABS_TOTP_SYNC_VALUE="$(printf '%s' "$secret_json" | python3 -c 'import json, sys; value = json.load(sys.stdin).get("GOTRENDLABS_TOTP_ENCRYPTION_KEY"); assert value, "Missing GOTRENDLABS_TOTP_ENCRYPTION_KEY"; print(value)')"
unset secret_json

python3 -c '
import os
import pathlib
import tempfile

path = pathlib.Path(os.environ["AUTH_ENV_FILE"])
key = "GOTRENDLABS_TOTP_ENCRYPTION_KEY"
value = os.environ["GOTRENDLABS_TOTP_SYNC_VALUE"]
previous_stat = path.stat() if path.exists() else None
lines = path.read_text().splitlines() if path.exists() else []
lines = [line for line in lines if line.split("=", 1)[0].strip() != key]
lines.append(f"{key}={value}")
fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".env.auth.prod.")
os.close(fd)
temporary_path = pathlib.Path(temporary)
temporary_path.write_text("\n".join(lines) + "\n")
temporary_path.chmod(0o600)
if previous_stat is not None:
    os.chown(temporary, previous_stat.st_uid, previous_stat.st_gid)
temporary_path.replace(path)
'

unset GOTRENDLABS_TOTP_SYNC_VALUE
test "$(stat -c '%a' "$AUTH_ENV_FILE")" = "600"
python3 -c '
import pathlib
import sys

lines = pathlib.Path(sys.argv[1]).read_text().splitlines()
values = dict(line.split("=", 1) for line in lines if "=" in line and not line.lstrip().startswith("#"))
assert values.get("GOTRENDLABS_TOTP_ENCRYPTION_KEY")
' "$AUTH_ENV_FILE"
echo "FastAPI TOTP key synchronized (mode 0600)."
