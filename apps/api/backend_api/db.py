import os
import atexit
import threading
from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout, TooManyRequests


class DatabaseCapacityError(Exception):
    """A database connection could not be acquired before any SQL was run."""


_pools = {}
_pools_lock = threading.Lock()


def _positive_int(name, default):
    value = int(os.environ.get(name, default))
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


def _pool_for_current_process():
    config = database_config()
    # Lazy creation occurs after uvicorn forks. Never reuse a pool for another PID/role.
    key = (os.getpid(), tuple(sorted(config.items())))
    with _pools_lock:
        pool = _pools.get(key)
        if pool is None:
            pool = ConnectionPool(
                kwargs={**config, "row_factory": dict_row, "connect_timeout": 2},
                min_size=0,
                max_size=_positive_int("GOTRENDLABS_DB_POOL_MAX", 4),
                max_waiting=_positive_int("GOTRENDLABS_DB_POOL_WAITING", 8),
                timeout=1,
                open=False,
            )
            pool.open()
            _pools[key] = pool
        return pool


def close_pools():
    with _pools_lock:
        pools = list(_pools.values())
        _pools.clear()
    for pool in pools:
        pool.close()


atexit.register(close_pools)


def database_config():
    fastapi_config = {
        "dbname": os.environ.get("FASTAPI_POSTGRES_DB"),
        "user": os.environ.get("FASTAPI_POSTGRES_USER"),
        "password": os.environ.get("FASTAPI_POSTGRES_PASSWORD"),
        "host": os.environ.get("FASTAPI_POSTGRES_HOST"),
        "port": os.environ.get("FASTAPI_POSTGRES_PORT"),
    }
    if any(fastapi_config.values()):
        return {
            "dbname": fastapi_config["dbname"] or os.environ.get("POSTGRES_DB", "gotrendlabs"),
            "user": fastapi_config["user"] or os.environ.get("POSTGRES_USER", "gotrendlabs"),
            "password": fastapi_config["password"] or os.environ.get("POSTGRES_PASSWORD", "gotrendlabs_dev_password"),
            "host": fastapi_config["host"] or os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            "port": fastapi_config["port"] or os.environ.get("POSTGRES_PORT", "5432"),
        }
    try:
        from django.conf import settings

        if settings.configured:
            db = settings.DATABASES["default"]
            if db["ENGINE"] == "django.db.backends.postgresql":
                return {
                    "dbname": db["NAME"],
                    "user": db["USER"],
                    "password": db["PASSWORD"],
                    "host": db["HOST"] or "127.0.0.1",
                    "port": db["PORT"] or "5432",
                }
    except Exception:
        pass

    return {
        "dbname": os.environ.get("POSTGRES_DB", "gotrendlabs"),
        "user": os.environ.get("POSTGRES_USER", "gotrendlabs"),
        "password": os.environ.get("POSTGRES_PASSWORD", "gotrendlabs_dev_password"),
        "host": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
    }


@contextmanager
def get_connection():
    try:
        with _pool_for_current_process().connection() as connection:
            yield connection
    except (PoolTimeout, TooManyRequests) as exc:
        raise DatabaseCapacityError("database connection capacity exhausted") from exc
