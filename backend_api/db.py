import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


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
            "dbname": fastapi_config["dbname"] or os.environ.get("POSTGRES_DB", "orynth"),
            "user": fastapi_config["user"] or os.environ.get("POSTGRES_USER", "orynth"),
            "password": fastapi_config["password"] or os.environ.get("POSTGRES_PASSWORD", "orynth_dev_password"),
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
        "dbname": os.environ.get("POSTGRES_DB", "orynth"),
        "user": os.environ.get("POSTGRES_USER", "orynth"),
        "password": os.environ.get("POSTGRES_PASSWORD", "orynth_dev_password"),
        "host": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
    }


@contextmanager
def get_connection():
    with psycopg.connect(**database_config(), row_factory=dict_row) as connection:
        yield connection
