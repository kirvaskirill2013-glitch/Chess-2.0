import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).with_name("settings.json")
DEFAULTS = {
    "minutes": 10,
    "sound": True,
    "show_coordinates": True,
    "board_theme": "classic"
}

def load_settings():
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return {**DEFAULTS, **data}
    except (OSError, ValueError, TypeError):
        return DEFAULTS.copy()

def save_settings(settings):
    try:
        SETTINGS_FILE.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except OSError:
        pass
