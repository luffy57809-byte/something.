import json
from sqlalchemy import text
from chess_coach.database import engine


def get_user_stats(username: str) -> dict:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT m.classification, m.color, m.pattern_tags, m.eval_drop
            FROM moves m
            JOIN games g ON m.game_id = g.game_id
            WHERE g.username = :username
        """), {"username": username}).fetchall()

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


def get_stats_for_games(game_ids: list) -> dict:
    if not game_ids:
        return {}

    with engine.connect() as conn:
        placeholders = ','.join([f':id{i}' for i in range(len(game_ids))])
        params = {f'id{i}': gid for i, gid in enumerate(game_ids)}
        rows = conn.execute(text(f"""
            SELECT classification, color, pattern_tags, eval_drop
            FROM moves WHERE game_id IN ({placeholders})
        """), params).fetchall()

    if not rows:
        return {}

    return _compute_stats(rows)


def _compute_stats(rows) -> dict:
    total = len(rows)
    blunders = sum(1 for r in rows if r[0] == "blunder")
    mistakes = sum(1 for r in rows if r[0] == "mistake")
    inaccuracies = sum(1 for r in rows if r[0] == "inaccuracy")
    good = sum(1 for r in rows if r[0] == "good")
    accuracy = round((good / total) * 100, 1) if total else 0
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
