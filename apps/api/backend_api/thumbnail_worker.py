"""Run with python -m apps.api.backend_api.thumbnail_worker. PostgreSQL queue, no HTTP tasks."""

import argparse
import logging
import os
import time
from datetime import timedelta
from uuid import uuid4

from psycopg.types.json import Jsonb
from apps.api.backend_api.db import get_connection
from apps.api.backend_api import thumbnail_service as s
from apps.api.backend_api.thumbnail_provider import generate, ProviderFailure

log = logging.getLogger(__name__)


def recover(cursor):
    cursor.execute(
        """UPDATE gotrendlabs_thumbnail_jobs SET state='uncertain',error_code='abandoned',finished_at=%s
        WHERE state='running' AND lease_until < %s RETURNING *""",
        (s.now(), s.now()),
    )
    for job in cursor.fetchall():
        s.event(cursor, job["operator_id"], "thumbnail.uncertain", job)


def eligible(cursor, job):
    cursor.execute(
        """SELECT 1 FROM gotrendlabs_users u JOIN gotrendlabs_auth_sessions a ON a.user_id=u.id
        JOIN gotrendlabs_markets m ON m.id=%s
        WHERE u.id=%s AND u.is_active AND u.account_status='active' AND (u.is_staff OR u.is_superuser)
        AND a.id=%s AND a.revoked_at IS NULL AND a.expires_at > %s AND a.mfa_verified_at IS NOT NULL AND m.status='draft' """,
        (job["market_id"], job["operator_id"], job["session_id"], s.now()),
    )
    return bool(cursor.fetchone())


def run_once(provider=generate):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            recover(cursor)
            if not s.enabled(cursor):
                return False
            cursor.execute(
                "SELECT * FROM gotrendlabs_thumbnail_jobs WHERE state='queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
            )
            job = cursor.fetchone()
            if not job:
                return False
            if job["expires_at"] <= s.now() or not eligible(cursor, job):
                cursor.execute(
                    "UPDATE gotrendlabs_thumbnail_jobs SET state='failed',error_code='ineligible',finished_at=%s WHERE id=%s",
                    (s.now(), job["id"]),
                )
                s.event(cursor, job["operator_id"], "thumbnail.failed", job)
                return True
            token = uuid4()
            lease = max(
                s.number("LEASE_SECONDS", 300),
                int(job["provider_config"].get("timeout_seconds", 180)) + 60,
            )
            cursor.execute(
                "UPDATE gotrendlabs_thumbnail_jobs SET state='running',started_at=%s,lease_until=%s,claim_token=%s WHERE id=%s",
                (s.now(), s.now() + timedelta(seconds=lease), token, job["id"]),
            )
            cursor.execute(
                "SELECT count(*) AS n FROM gotrendlabs_thumbnail_jobs WHERE market_id=%s AND created_at < %s",
                (job["market_id"], job["created_at"]),
            )
            job["variation"] = cursor.fetchone()["n"]
            s.event(cursor, job["operator_id"], "thumbnail.running", job)
    # Provider I/O occurs after claim COMMIT. Never retry running jobs.
    data, provider_id, usage, failure = None, None, None, None
    try:
        data, provider_id, usage = provider(job)
        data = s.validate_image(data)
    except ProviderFailure as exc:
        failure = exc
        provider_id, usage = exc.provider_id, exc.usage
    except ValueError:
        failure = ProviderFailure("invalid_image")
    except Exception:
        # Unknown failures are conservative; log no request/private payload or exception body.
        failure = ProviderFailure("executor_error", uncertain=True)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM gotrendlabs_thumbnail_jobs WHERE id=%s FOR UPDATE",
                (job["id"],),
            )
            current = cursor.fetchone()
            if current["state"] != "running" or current["claim_token"] != token:
                return True  # fenced late result cannot restore an abandoned job
            if current["lease_until"] <= s.now():
                failure = ProviderFailure(
                    "lease_expired",
                    uncertain=True,
                    provider_id=provider_id,
                    usage=usage,
                )
            if not failure and not eligible(cursor, job):
                failure = ProviderFailure("ineligible")
            if not failure:
                path = s.private_root() / (str(job["id"]) + ".png")
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("xb") as out:
                        out.write(data)
                    os.chmod(path, 0o600)
                except OSError:
                    s.discard_partial(path)
                    failure = ProviderFailure("storage_failed")
            state = (
                "uncertain"
                if failure and failure.uncertain
                else "failed"
                if failure
                else "succeeded"
            )
            cursor.execute(
                """UPDATE gotrendlabs_thumbnail_jobs SET state=%s,finished_at=%s,provider_id=%s,usage=%s,error_code=%s
                WHERE id=%s""",
                (
                    state,
                    s.now(),
                    provider_id,
                    Jsonb(usage) if usage is not None else None,
                    failure.code if failure else "",
                    job["id"],
                ),
            )
            s.event(cursor, job["operator_id"], "thumbnail." + state, job)
    log.info(
        "thumbnail job=%s state=%s code=%s",
        job["id"],
        state,
        failure.code if failure else "",
    )
    return True


def prune():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", (s.PROMOTION_LOCK,))
            recover(cursor)
            cursor.execute(
                "SELECT * FROM gotrendlabs_thumbnail_jobs WHERE expires_at < %s AND state NOT IN ('queued','running') FOR UPDATE",
                (s.now(),),
            )
            for job in cursor.fetchall():
                (s.private_root() / (str(job["id"]) + ".png")).unlink(missing_ok=True)
                if job["state"] == "succeeded":
                    cursor.execute(
                        "UPDATE gotrendlabs_thumbnail_jobs SET state='expired' WHERE id=%s",
                        (job["id"],),
                    )
            cursor.execute("SELECT id,state,expires_at FROM gotrendlabs_thumbnail_jobs")
            jobs = {str(j["id"]): j for j in cursor.fetchall()}
            grace = time.time() - 3600
            if s.private_root().exists():
                for path in s.private_root().glob("*.png"):
                    job = jobs.get(path.stem)
                    if path.stat().st_mtime < grace and (
                        not job
                        or job["state"] not in ("queued", "running", "succeeded")
                    ):
                        path.unlink(missing_ok=True)
            # Only our UUID filenames. Manual upload naming and published files are preserved.
            if s.public_root().exists():
                from uuid import UUID

                for path in s.public_root().glob("*.png"):
                    try:
                        UUID(path.stem)
                    except ValueError:
                        continue
                    if path.stat().st_mtime >= grace:
                        continue
                    url = "/media/market_thumbnails/" + path.name
                    cursor.execute(
                        "SELECT 1 FROM gotrendlabs_markets WHERE image_url=%s LIMIT 1",
                        (url,),
                    )
                    if not cursor.fetchone():
                        path.unlink(missing_ok=True)


def main():
    from pathlib import Path
    from config.env import load_env_file

    root = Path(__file__).resolve().parents[3]
    for name in (".env", ".env.api.local", ".env.thumbnails.local"):
        load_env_file(root / name)
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--prune", action="store_true")
    args = parser.parse_args()
    if args.prune:
        prune()
        return
    logging.basicConfig(level=logging.INFO)
    next_cleanup = 0.0
    while True:
        try:
            run_once()
            if time.monotonic() >= next_cleanup:
                prune()
                next_cleanup = time.monotonic() + s.number("CLEANUP_SECONDS", 300)
        except Exception:
            log.error(
                "thumbnail worker cycle failed; inspect database/storage configuration"
            )
            if args.once:
                raise
        if args.once:
            break
        time.sleep(3)


if __name__ == "__main__":
    main()
