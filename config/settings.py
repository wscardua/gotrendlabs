import os
from pathlib import Path

from config.env import load_env_file

BASE_DIR = Path(__file__).resolve().parent.parent
load_env_file(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-gotrendlabs-django-fixtures")
DEBUG = os.environ.get("DJANGO_DEBUG", "1").strip().lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("GOTRENDLABS_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("GOTRENDLABS_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
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
    "agents",
    "system_logs",
    "communications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core.middleware.MaintenanceModeMiddleware",
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

if os.environ.get("GOTRENDLABS_USE_SQLITE") == "1":
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
            "NAME": os.environ.get("DJANGO_POSTGRES_DB") or os.environ.get("POSTGRES_DB", "gotrendlabs"),
            "USER": os.environ.get("DJANGO_POSTGRES_USER") or os.environ.get("POSTGRES_USER", "gotrendlabs"),
            "PASSWORD": os.environ.get("DJANGO_POSTGRES_PASSWORD") or os.environ.get("POSTGRES_PASSWORD", "gotrendlabs_dev_password"),
            "HOST": os.environ.get("DJANGO_POSTGRES_HOST") or os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DJANGO_POSTGRES_PORT") or os.environ.get("POSTGRES_PORT", "5432"),
        }
    }

LANGUAGE_CODE = "pt-br"
LANGUAGES = [("pt-br", "Portuguese"), ("en", "English")]
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "0").strip().lower() in {"1", "true", "yes", "on"}
SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SESSION_COOKIE_SECURE", "0").strip().lower() in {"1", "true", "yes", "on"}
CSRF_COOKIE_SECURE = os.environ.get("DJANGO_CSRF_COOKIE_SECURE", "0").strip().lower() in {"1", "true", "yes", "on"}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:8001")
PUBLIC_SHARE_BASE_URL = os.environ.get("GOTRENDLABS_PUBLIC_BASE_URL", "").rstrip("/")
RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")
if "RECAPTCHA_ENABLED" in os.environ:
    RECAPTCHA_ENABLED = os.environ.get("RECAPTCHA_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
else:
    RECAPTCHA_ENABLED = bool(RECAPTCHA_SECRET_KEY)

SYSTEM_LOG_RETENTION_DAYS = int(os.environ.get("SYSTEM_LOG_RETENTION_DAYS", "90"))
GOTRENDLABS_RUNTIME_CONFIG_PATH = os.environ.get("GOTRENDLABS_RUNTIME_CONFIG_PATH", str(BASE_DIR / ".runtime" / "platform_config.json"))
GOTRENDLABS_SMTP_PASSWORD = os.environ.get("GOTRENDLABS_SMTP_PASSWORD", "")
GOTRENDLABS_SMTP_API_KEY = os.environ.get("GOTRENDLABS_SMTP_API_KEY", "")
GOTRENDLABS_SES_PRODUCTION_ACCESS = os.environ.get("GOTRENDLABS_SES_PRODUCTION_ACCESS", "0").strip().lower() in {"1", "true", "yes", "on"}
GOTRENDLABS_EMAIL_SANDBOX_ALLOWLIST = {
    email.strip().lower()
    for email in os.environ.get("GOTRENDLABS_EMAIL_SANDBOX_ALLOWLIST", "success@simulator.amazonses.com").split(",")
    if email.strip()
}
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
AWS_BEARER_TOKEN_BEDROCK = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "")

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
