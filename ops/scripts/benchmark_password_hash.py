"""Measure Argon2id password work on a representative host without touching accounts."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import resource
import statistics
import sys
import time

from config.env import load_env_file
from packages.security.passwords import check_password, make_password, require_password_pepper


def _measure(work, workers, operations):
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        durations = list(pool.map(lambda _: work(), range(operations)))
    sorted_durations = sorted(durations)
    return {
        "workers": workers,
        "operations": operations,
        "p50_ms": round(statistics.median(durations) * 1000, 1),
        "p95_ms": round(sorted_durations[max(0, (len(sorted_durations) * 95 + 99) // 100 - 1)] * 1000, 1),
        "total_s": round(time.perf_counter() - started, 2),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", default="1,2,5,10", help="Comma-separated concurrency levels")
    parser.add_argument("--operations", type=int, default=8, help="Operations per level and action")
    args = parser.parse_args()
    if args.operations < 1:
        parser.error("--operations must be positive")
    root = Path(__file__).resolve().parents[2]
    load_env_file(root / ".env")
    if os.environ.get("GOTRENDLABS_ENV", "").lower() not in {"prod", "production"}:
        load_env_file(root / ".env.api.local")
    require_password_pepper()
    password = "capacity-probe-only"
    encoded = make_password(password)

    def verify():
        started = time.perf_counter()
        if not check_password(password, encoded):
            raise RuntimeError("Password verification failed")
        return time.perf_counter() - started

    def hash_new():
        started = time.perf_counter()
        make_password(password)
        return time.perf_counter() - started

    for raw in args.workers.split(","):
        workers = int(raw.strip())
        if workers < 1:
            parser.error("worker counts must be positive")
        print("verify", _measure(verify, workers, args.operations))
        print("hash", _measure(hash_new, workers, args.operations))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    mib = peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024
    print("peak_process_rss_mib", round(mib, 1))


if __name__ == "__main__":
    main()
