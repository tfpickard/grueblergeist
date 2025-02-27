# assistant/config.py
import json
import os
from typing import Any, Dict, Optional

_CONFIG: Optional[Dict[str, Any]] = None


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Load config from a JSON file, caching the result.

    :param config_path: Path to the JSON configuration file.
    :return: Dictionary containing configuration data.
    :raises FileNotFoundError: If the config file is missing.
    """
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        _CONFIG = json.load(f)
    return _CONFIG


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Retrieve a value from the loaded config, with an optional default.

    :param key: The key to look up in the config.
    :param default: The default value if key not found.
    :return: The value from config if present, otherwise default.
    """
    config = load_config()
    return config.get(key, default)
