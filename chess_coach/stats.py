from chess_coach.database import get_connection


def get_user_stats(username: str) -> dict:
    """Compute overall stats across all analyzed games for a user."""
    conn = get_connection()
    c = conn.cursor()

    # Get all moves for this user's games
    c.execute("""
        SELECT m.classification, m.color, m.pattern_tags, m.eval_drop,
               g.white, g.result
        FROM moves m
        JOIN games g ON m.game_id = g.game_id
        WHERE g.username = ?
    """, (username,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return {}

    total_moves = len(rows)
    blunders = sum(1 for r in rows if r["classification"] == "blunder")
    mistakes = sum(1 for r in rows if r["classification"] == "mistake")
    inaccuracies = sum(1 for r in rows if r["classification"] == "inaccuracy")
    good_moves = sum(1 for r in rows if r["classification"] == "good")

    accuracy = round((good_moves / total_moves) * 100, 1) if total_moves else 0
    blunder_rate = round((blunders / total_moves) * 100, 1) if total_moves else 0

    # Pattern frequency
    pattern_counts = {}
    for r in rows:
        import json
        tags = json.loads(r["pattern_tags"] or "[]")
        for tag in tags:
            pattern_counts[tag] = pattern_counts.get(tag, 0) + 1

    # Most common problem
    top_pattern = max(pattern_counts, key=pattern_counts.get) if pattern_counts else None

    return {
        "total_moves": total_moves,
        "blunders": blunders,
        "mistakes": mistakes,
        "inaccuracies": inaccuracies,
        "good_moves": good_moves,
        "accuracy_pct": accuracy,
        "blunder_rate_pct": blunder_rate,
        "pattern_counts": pattern_counts,
        "top_weakness": top_pattern,
    }


def get_game_summary(game_id: str) -> dict:
    """Get stats for a single game."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT classification, color, pattern_tags, eval_drop
        FROM moves WHERE game_id = ?
    """, (game_id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return {}

    import json
    total = len(rows)
    blunders = sum(1 for r in rows if r["classification"] == "blunder")
    mistakes = sum(1 for r in rows if r["classification"] == "mistake")
    inaccuracies = sum(1 for r in rows if r["classification"] == "inaccuracy")
    good = sum(1 for r in rows if r["classification"] == "good")
    accuracy = round((good / total) * 100, 1) if total else 0

    white_errors = sum(1 for r in rows
                       if r["color"] == "white"
                       and r["classification"] in ("blunder", "mistake"))
    black_errors = sum(1 for r in rows
                       if r["color"] == "black"
                       and r["classification"] in ("blunder", "mistake"))

    return {
        "total_moves": total,
        "blunders": blunders,
        "mistakes": mistakes,
        "inaccuracies": inaccuracies,
        "accuracy_pct": accuracy,
        "white_errors": white_errors,
        "black_errors": black_errors,
    }
