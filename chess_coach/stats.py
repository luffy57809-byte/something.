import json
import math
from sqlalchemy import text
from chess_coach.database import engine

_COLS = "m.classification, m.color, m.pattern_tags, m.eval_drop, m.eval_before, m.eval_after"

# Only count moves made by the user, never the opponent's
_ONLY_USER_MOVES = """
    AND ((m.color = 'white' AND lower(g.white) = lower(:u))
      OR (m.color = 'black' AND lower(g.black) = lower(:u)))
"""


def get_user_stats(username: str) -> dict:
    with engine.connect() as conn:
        rows = conn.execute(text(f"""
            SELECT {_COLS}
            FROM moves m
            JOIN games g ON m.game_id = g.game_id
            WHERE lower(g.username) = lower(:u)
            {_ONLY_USER_MOVES}
        """), {"u": username}).fetchall()

    if not rows:
        return {}

    return _compute_stats(rows)


def get_game_summary(game_id: str) -> dict:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT classification, color, pattern_tags, eval_drop
            FROM moves WHERE game_id = :game_id
        """), {"game_id": game_id}).fetchall()

    if not rows:
        return {}

    total = len(rows)
    blunders = sum(1 for r in rows if r[0] == "blunder")
    mistakes = sum(1 for r in rows if r[0] == "mistake")
    inaccuracies = sum(1 for r in rows if r[0] == "inaccuracy")
    good = sum(1 for r in rows if r[0] == "good")
    accuracy = round((good / total) * 100, 1) if total else 0

    white_errors = sum(1 for r in rows
                       if r[1] == "white"
                       and r[0] in ("blunder", "mistake"))
    black_errors = sum(1 for r in rows
                       if r[1] == "black"
                       and r[0] in ("blunder", "mistake"))

    return {
        "total_moves": total,
        "blunders": blunders,
        "mistakes": mistakes,
        "inaccuracies": inaccuracies,
        "accuracy_pct": accuracy,
        "white_errors": white_errors,
        "black_errors": black_errors,
    }


def get_stats_for_games(game_ids: list, username: str = None) -> dict:
    if not game_ids:
        return {}

    placeholders = ','.join([f':id{i}' for i in range(len(game_ids))])
    params = {f'id{i}': gid for i, gid in enumerate(game_ids)}
    user_filter = ""
    if username:
        user_filter = _ONLY_USER_MOVES
        params["u"] = username

    with engine.connect() as conn:
        rows = conn.execute(text(f"""
            SELECT {_COLS}
            FROM moves m
            JOIN games g ON m.game_id = g.game_id
            WHERE m.game_id IN ({placeholders})
            {user_filter}
        """), params).fetchall()

    if not rows:
        return {}

    return _compute_stats(rows)


def _win_pct(cp: int) -> float:
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def _move_accuracy(eval_before, eval_after, eval_drop) -> float:
    """Per-move accuracy (0-100) from the win-chance lost, modeled on Lichess's curve."""
    if not eval_drop or eval_before is None or eval_after is None:
        return 100.0
    drop = max(0.0, _win_pct(eval_before) - _win_pct(eval_after))
    acc = 103.1668 * math.exp(-0.04354 * drop) - 3.1669
    return max(0.0, min(100.0, acc))


def _compute_stats(rows) -> dict:
    total = len(rows)
    blunders = sum(1 for r in rows if r[0] == "blunder")
    mistakes = sum(1 for r in rows if r[0] == "mistake")
    inaccuracies = sum(1 for r in rows if r[0] == "inaccuracy")
    good = sum(1 for r in rows if r[0] == "good")
    accuracy = round(sum(_move_accuracy(r[4], r[5], r[3]) for r in rows) / total, 1) if total else 0
    blunder_rate = round((blunders / total) * 100, 1) if total else 0

    pattern_counts = {}
    for r in rows:
        tags = json.loads(r[2] or "[]")
        for tag in tags:
            pattern_counts[tag] = pattern_counts.get(tag, 0) + 1

    top_pattern = max(pattern_counts, key=pattern_counts.get) if pattern_counts else None

    return {
        "total_moves": total,
        "blunders": blunders,
        "mistakes": mistakes,
        "inaccuracies": inaccuracies,
        "good_moves": good,
        "accuracy_pct": accuracy,
        "blunder_rate_pct": blunder_rate,
        "pattern_counts": pattern_counts,
        "top_weakness": top_pattern,
    }
