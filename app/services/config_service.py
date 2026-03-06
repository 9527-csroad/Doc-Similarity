import json
import os
from typing import Optional
from app.config import get_settings

THRESHOLD_KEY = "threshold"


def _get_config_path() -> str:
    path = get_settings().CONFIG_FILE_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    return path


def get_threshold() -> float:
    path = _get_config_path()
    default = get_settings().DEFAULT_THRESHOLD
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            data = json.load(f)
            return float(data.get(THRESHOLD_KEY, default))
    except Exception:
        return default


def set_threshold(value: float) -> None:
    path = _get_config_path()
    data = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            pass
    data[THRESHOLD_KEY] = value
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
