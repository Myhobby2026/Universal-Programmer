from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.theme import Theme


class SettingsStore:
    """Small recoverable JSON store used alongside Qt's window-state bytes."""

    DEFAULTS: dict[str, Any] = {
        "theme": Theme.DARK.value, "accent": "#43a7e8", "font_size": 13,
        "serial_port": "", "baud_rate": 115200, "timeout_ms": 1000,
        "log_level": "INFO", "default_path": "", "confirm_destructive": True,
        "recent_files": [], "workspaces": {}, "window_state": "", "window_geometry": "",
    }

    def __init__(self, path: Path | None = None):
        self.path = path or Path.home() / ".universal_programmer_studio" / "settings.json"
        self.values = dict(self.DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                for key, default in self.DEFAULTS.items():
                    value = loaded.get(key, default)
                    if isinstance(default, bool) and isinstance(value, bool):
                        self.values[key] = value
                    elif isinstance(default, (int, float)) and isinstance(value, type(default)) and not isinstance(value, bool):
                        self.values[key] = value
                    elif isinstance(default, str) and isinstance(value, str):
                        self.values[key] = value
                    elif isinstance(default, list) and isinstance(value, list):
                        self.values[key] = value
                    elif isinstance(default, dict) and isinstance(value, dict):
                        self.values[key] = value
        except (OSError, ValueError, TypeError):
            self.values = dict(self.DEFAULTS)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.values, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if key in self.DEFAULTS:
            self.values[key] = value
