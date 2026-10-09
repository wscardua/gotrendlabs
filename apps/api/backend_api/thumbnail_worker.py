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
    if job.get("kind", "market") == "badge":
        cursor.execute("""SELECT 1 FROM gotrendlabs_users u JOIN gotrendlabs_auth_sessions a ON a.user_id=u.id
            WHERE u.id=%s AND u.is_active AND u.account_status='active' AND (u.is_staff OR u.is_superuser)
            AND a.id=%s AND a.revoked_at IS NULL AND a.expires_at > %s AND a.mfa_verified_at IS NOT NULL
            AND (%s::bigint IS NULL OR EXISTS(SELECT 1 FROM gotrendlabs_badge_definitions WHERE id=%s))""", (job["operator_id"], job["session_id"], s.now(), job["badge_id"], job["badge_id"]))
        return bool(cursor.fetchone())
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
            from apps.api.backend_api import badge_image_service
            kinds = []
            if s.enabled(cursor): kinds.append("market")
            if badge_image_service.enabled(cursor): kinds.append("badge")
            if not kinds:
                return False
            cursor.execute(
                "SELECT * FROM gotrendlabs_thumbnail_jobs WHERE state='queued' AND kind=ANY(%s) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1", (kinds,)
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
                int(job["provider_config"].get("timeout_seconds", 180)) * (2 if job["kind"] == "badge" else 1) + 60,
            )
            cursor.execute(
                "UPDATE gotrendlabs_thumbnail_jobs SET state='running',started_at=%s,lease_until=%s,claim_token=%s WHERE id=%s",
                (s.now(), s.now() + timedelta(seconds=lease), token, job["id"]),
            )
            cursor.execute(
                "SELECT count(*) AS n FROM gotrendlabs_thumbnail_jobs WHERE kind=%s AND (market_id=%s OR badge_id=%s OR (kind='badge' AND operator_id=%s AND editor_id=%s)) AND created_at < %s",
                (job["kind"], job["market_id"], job["badge_id"], job["operator_id"], job["editor_id"], job["created_at"]),
            )
            job["variation"] = cursor.fetchone()["n"]
            s.event(cursor, job["operator_id"], "thumbnail.running", job)
    # Provider I/O occurs after claim COMMIT. Never retry running jobs.
    data, provider_id, usage, failure = None, None, None, None
    images, records, theme = {}, {}, "light"
    is_badge = job.get("kind") == "badge"
    try:
        if is_badge:
            from apps.api.backend_api.badge_image_service import VERSION
            if job["instructions_version"] != VERSION:
                raise ProviderFailure("unsupported_instructions")
        for theme in (("light", "dark") if is_badge else ("light",)):
            if is_badge:
                # Checkpoint before each paid call. No locks/transaction during provider I/O.
                # A crash leaves a running/uncertain job; recovery never invokes again.
                records[theme] = {"state": "started"}
                with get_connection() as connection, connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM gotrendlabs_thumbnail_jobs WHERE id=%s FOR UPDATE", (job["id"],))
                    current = cursor.fetchone()
                    if current["state"] != "running" or current["claim_token"] != token or current["lease_until"] <= s.now():
                        return True
                    if not eligible(cursor, job):
                        raise ProviderFailure("ineligible")
                    cursor.execute("UPDATE gotrendlabs_thumbnail_jobs SET usage=%s WHERE id=%s", (Jsonb({"variants": records}), job["id"]))
            data, provider_id, reported_usage = provider({**job, "theme": theme} if is_badge else job)
            if is_badge:
                records[theme] = {"state": "returned", "provider_id": provider_id, "reported_usage": reported_usage}
            else:
                usage = reported_usage
            data = s.validate_image(data)
            if is_badge:
                from PIL import Image
                from io import BytesIO
                image = Image.open(BytesIO(data))
                if image.width != image.height:
                    raise ValueError("badge_image_must_be_square")
                records[theme]["state"] = "validated"
            images[theme] = data
    except ProviderFailure as exc:
        failure = exc
        provider_id = exc.provider_id or provider_id
        if is_badge:
            records[theme] = {"state": "uncertain" if exc.uncertain else "failed", "provider_id": exc.provider_id, "reported_usage": exc.usage, "error_code": exc.code}
        else:
            usage = exc.usage
    except ValueError:
        failure = ProviderFailure("invalid_image")
        if is_badge:
            records.setdefault(theme, {})["state"] = "invalid"
    except Exception:
        # Unknown failures are conservative; log no request/private payload or exception body.
        failure = ProviderFailure("executor_error", uncertain=True)
        if is_badge:
            records.setdefault(theme, {})["state"] = "uncertain"
    if is_badge:
        usage = {"variants": records}
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
                written = []
                try:
                    for variant, image_data in images.items():
                        path = s.private_root() / (str(job["id"]) + (".dark" if variant == "dark" else "") + ".png")
                        path.parent.mkdir(parents=True, exist_ok=True)
                        with path.open("xb") as out:
                            written.append(path)
                            out.write(image_data)
                        os.chmod(path, 0o600)
                except OSError:
                    for path in written:
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
                for suffix in ("", ".dark"):
                    (s.private_root() / (str(job["id"]) + suffix + ".png")).unlink(missing_ok=True)
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
                    job = jobs.get(path.stem.removesuffix(".dark"))
                    if path.stat().st_mtime < grace and (
                        not job
                        or job["state"] not in ("queued", "running", "succeeded")
                    ):
                        path.unlink(missing_ok=True)
            # Only our UUID filenames. Manual upload naming and published files are preserved.
            prune_public_badges(cursor, grace)
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



def prune_public_badges(cursor, grace):
    from uuid import UUID
    root = s.public_root("badge")
    if not root.exists(): return
    for path in root.glob("*.png"):
        try: UUID(path.stem)
        except ValueError: continue
        if path.stat().st_mtime >= grace: continue
        url = "/media/badge_images/" + path.name
        cursor.execute("SELECT 1 FROM gotrendlabs_badge_definitions WHERE image_url=%s OR image_dark_url=%s LIMIT 1", (url,url))
        if not cursor.fetchone(): path.unlink(missing_ok=True)

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
