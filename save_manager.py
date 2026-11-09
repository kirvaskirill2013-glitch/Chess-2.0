import json
from pathlib import Path

SAVE_FILE = Path(__file__).with_name("saved_game.json")

def save_game(board, move_history, mode, difficulty, human_color, clocks):
    payload = {
        "fen": board.fen(),
        "moves": list(move_history),
        "uci_moves": [move.uci() for move in board.move_stack],
        "mode": mode,
        "difficulty": difficulty,
        "human_color": human_color,
        "clocks": clocks
    }
    try:
        SAVE_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True
    except OSError:
        return False

def load_game():
    try:
        data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        required = {"fen", "moves", "mode", "difficulty", "human_color", "clocks"}
        if not required.issubset(data):
            return None
        return data
    except (OSError, ValueError, TypeError):
        return None

def has_saved_game():
    return SAVE_FILE.exists()
