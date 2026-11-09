import json
from pathlib import Path

STATS_FILE = Path(__file__).with_name("statistics.json")
DEFAULTS = {"wins": 0, "losses": 0, "draws": 0, "games": 0, "moves": 0}

def load_stats():
    try:
        data = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        return {**DEFAULTS, **data}
    except (OSError, ValueError, TypeError):
        return DEFAULTS.copy()

def record_result(result, move_count):
    stats = load_stats()
    stats["games"] += 1
    stats["moves"] += int(move_count)
    if result in ("win", "loss", "draw"):
        stats[{"win": "wins", "loss": "losses", "draw": "draws"}[result]] += 1
    try:
        STATS_FILE.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except OSError:
        pass
    return stats
