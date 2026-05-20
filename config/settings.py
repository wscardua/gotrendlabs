import os
from pathlib import Path

from config.env import load_env_file

BASE_DIR = Path(__file__).resolve().parent.parent
load_env_file(BASE_DIR / ".env")

SECRET_KEY = "dev-only-orynth-django-fixtures"
DEBUG = True
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ORYNTH_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "markets",
    "accounts",
    "wallet",
    "profiles",
    "admin_ops",
    "system_logs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "system_logs.middleware.SystemLogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.session_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

if os.environ.get("ORYNTH_USE_SQLITE") == "1":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "orynth"),
            "USER": os.environ.get("POSTGRES_USER", "orynth"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "orynth_dev_password"),
            "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }

LANGUAGE_CODE = "pt-br"
LANGUAGES = [("pt-br", "Portuguese"), ("en", "English")]
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:8001")
PUBLIC_SHARE_BASE_URL = os.environ.get("ORYNTH_PUBLIC_BASE_URL", "").rstrip("/")
RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")
if "RECAPTCHA_ENABLED" in os.environ:
    RECAPTCHA_ENABLED = os.environ.get("RECAPTCHA_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
else:
    RECAPTCHA_ENABLED = bool(RECAPTCHA_SECRET_KEY)

SYSTEM_LOG_RETENTION_DAYS = int(os.environ.get("SYSTEM_LOG_RETENTION_DAYS", "90"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "database": {
            "class": "system_logs.logging.DatabaseLogHandler",
            "formatter": "standard",
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["console", "database"],
        "level": "INFO",
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "system_logs": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
