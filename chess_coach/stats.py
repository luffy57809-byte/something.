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
    """Summary for the user's side of the game, with the opponent's numbers alongside."""
    with engine.connect() as conn:
        game = conn.execute(
            text("SELECT username, white, black FROM games WHERE game_id = :g"),
            {"g": game_id}
        ).fetchone()
        rows = conn.execute(text(f"""
            SELECT {_COLS} FROM moves m WHERE m.game_id = :g ORDER BY m.id
        """), {"g": game_id}).fetchall()

    if not rows:
        return {}

    my_color = None
    if game:
        me = (game[0] or "").lower()
        if (game[1] or "").lower() == me:
            my_color = "white"
        elif (game[2] or "").lower() == me:
            my_color = "black"

    mine = [r for r in rows if r[1] == my_color] if my_color else rows
    summary = _compute_stats(mine)

    if my_color:
        theirs = [r for r in rows if r[1] != my_color]
        if theirs:
            opp = _compute_stats(theirs)
            summary["opponent"] = {k: opp[k] for k in
                                   ("accuracy_pct", "blunders", "mistakes", "inaccuracies")}
    summary["player_color"] = my_color
    summary["white_errors"] = sum(1 for r in rows if r[1] == "white" and r[0] in ("blunder", "mistake"))
    summary["black_errors"] = sum(1 for r in rows if r[1] == "black" and r[0] in ("blunder", "mistake"))
    return summary


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


def _progress_from_rows(rows, limit=60):
    """Group per-move rows into one summary per game (the user's own moves only)."""
    by_game = {}
    for r in rows:
        by_game.setdefault(r[0], []).append(r)

    games = []
    for game_id, grows in by_game.items():
        first = grows[0]
        color, date, white, black, result = first[2], first[7], first[8], first[9], first[10]
        n = len(grows)
        accuracy = sum(_move_accuracy(r[5], r[6], r[4]) for r in grows) / n
        if result == "1/2-1/2":
            outcome = "draw"
        elif (result == "1-0" and color == "white") or (result == "0-1" and color == "black"):
            outcome = "win"
        elif result in ("1-0", "0-1"):
            outcome = "loss"
        else:
            outcome = "unknown"
        games.append({
            "game_id": game_id,
            "date": date,
            "color": color,
            "opponent": black if color == "white" else white,
            "outcome": outcome,
            "result": result,
            "accuracy_pct": round(accuracy, 1),
            "blunders": sum(1 for r in grows if r[1] == "blunder"),
            "mistakes": sum(1 for r in grows if r[1] == "mistake"),
            "inaccuracies": sum(1 for r in grows if r[1] == "inaccuracy"),
            "moves": n,
        })

    games.sort(key=lambda g: (g["date"] or "", g["game_id"]))
    games = games[-limit:]
    keep = {g["game_id"] for g in games}
    pattern_counts = {}
    for r in rows:
        if r[0] in keep:
            for tag in json.loads(r[3] or "[]"):
                pattern_counts[tag] = pattern_counts.get(tag, 0) + 1
    return {"games": games, "pattern_counts": pattern_counts}


def get_user_progress(username: str, limit: int = 60) -> dict:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT m.game_id, m.classification, m.color, m.pattern_tags,
                   m.eval_drop, m.eval_before, m.eval_after,
                   g.date, g.white, g.black, g.result
            FROM moves m
            JOIN games g ON m.game_id = g.game_id
            WHERE lower(g.username) = lower(:u)
              AND ((m.color = 'white' AND lower(g.white) = lower(:u))
                OR (m.color = 'black' AND lower(g.black) = lower(:u)))
            ORDER BY m.game_id, m.id
        """), {"u": username}).fetchall()
    return _progress_from_rows(rows, limit)
