import json
from pathlib import Path

from django.conf import settings
from django.utils import timezone


DEFAULT_MAINTENANCE_MESSAGE = "Estamos fazendo uma manutenção rápida para deixar a plataforma mais estável. Voltamos em breve."


def runtime_config_path():
    return Path(settings.ORYNTH_RUNTIME_CONFIG_PATH)


def default_platform_config():
    return {
        "maintenance_enabled": False,
        "maintenance_message": DEFAULT_MAINTENANCE_MESSAGE,
        "updated_at": "",
        "updated_by": "",
    }


def load_platform_config():
    path = runtime_config_path()
    defaults = default_platform_config()
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return defaults
    if not isinstance(data, dict):
        return defaults
    return {**defaults, **data}


def save_platform_config(data):
    current = load_platform_config()
    payload = {**current, **data, "updated_at": timezone.now().isoformat()}
    path = runtime_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)
    return payload


def maintenance_enabled():
    return bool(load_platform_config().get("maintenance_enabled"))
