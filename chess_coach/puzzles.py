import json
import requests as http_requests
from chess_coach.database import get_connection


PATTERN_TO_THEME = {
    "missed_fork": "fork",
    "missed_pin": "pin",
    "hanging_piece": "hangingPiece",
    "back_rank_weakness": "backRankMate",
}


def init_puzzles_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS puzzles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puzzle_id TEXT UNIQUE NOT NULL,
            fen TEXT NOT NULL,
            moves TEXT NOT NULL,
            rating INTEGER,
            themes TEXT,
            game_url TEXT,
            source TEXT DEFAULT 'lichess'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS game_puzzles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puzzle_id TEXT UNIQUE,
            game_id TEXT NOT NULL,
            chess_username TEXT NOT NULL,
            move_number INTEGER NOT NULL,
            color TEXT NOT NULL,
            fen TEXT NOT NULL,
            best_move TEXT NOT NULL,
            classification TEXT NOT NULL,
            pattern_tags TEXT NOT NULL,
            explanation TEXT,
            source TEXT DEFAULT 'game'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS puzzle_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            puzzle_id TEXT NOT NULL,
            puzzle_source TEXT NOT NULL,
            solved INTEGER NOT NULL,
            attempted_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def extract_game_puzzles(record, chess_username: str) -> list[dict]:
    """Turn blunders and mistakes from an analyzed game into puzzles."""
    conn = get_connection()
    c = conn.cursor()
    puzzles = []

    for m in record.moves:
        if m.classification not in ("blunder", "mistake"):
            continue
        if not m.best_move_san:
            continue

        puzzle_id = f"{record.game_id}__move{m.move_number}_{m.color}"

        c.execute("SELECT id FROM game_puzzles WHERE puzzle_id = ?", (puzzle_id,))
        if c.fetchone():
            continue

        c.execute("""
            INSERT INTO game_puzzles
            (puzzle_id, game_id, chess_username, move_number, color, fen,
             best_move, classification, pattern_tags, explanation, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'game')
        """, (
            puzzle_id, record.game_id, chess_username,
            m.move_number, m.color, m.fen_before, m.best_move_san,
            m.classification, json.dumps(m.pattern_tags), m.explanation
        ))

        puzzles.append({
            "puzzle_id": puzzle_id,
            "fen": m.fen_before,
            "best_move": m.best_move_san,
            "classification": m.classification,
            "pattern_tags": m.pattern_tags,
            "explanation": m.explanation,
            "move_number": m.move_number,
            "color": m.color,
            "source": "game",
        })

    conn.commit()
    conn.close()
    return puzzles


def fetch_lichess_puzzle(theme: str) -> dict | None:
    """Fetch a single puzzle from Lichess for a given theme."""
    url = "https://lichess.org/api/puzzle/next"
    resp = http_requests.get(url, params={"angle": theme})
    if resp.status_code != 200:
        return None
    data = resp.json()
    puzzle = data["puzzle"]
    game = data.get("game", {})
    return {
        "puzzle_id": puzzle["id"],
        "fen": puzzle.get("fen", game.get("fen", "")),
        "moves": " ".join(puzzle["solution"]),
        "rating": puzzle["rating"],
        "themes": " ".join(puzzle["themes"]),
        "game_url": game.get("id", ""),
    }


def save_lichess_puzzle(puzzle: dict):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT OR IGNORE INTO puzzles
            (puzzle_id, fen, moves, rating, themes, game_url, source)
            VALUES (?, ?, ?, ?, ?, ?, 'lichess')
        """, (
            puzzle["puzzle_id"], puzzle["fen"], puzzle["moves"],
            puzzle["rating"], puzzle["themes"], puzzle["game_url"]
        ))
        conn.commit()
    finally:
        conn.close()


def get_themed_puzzle(theme: str) -> dict | None:
    puzzle = fetch_lichess_puzzle(theme)
    if puzzle:
        save_lichess_puzzle(puzzle)
    return puzzle


def get_training_puzzles(chess_username: str, app_username: str,
                         limit: int = 5) -> dict:
    """
    Return a mix of game-based puzzles and Lichess puzzles
    matched to the user's weaknesses.
    """
    from chess_coach.stats import get_user_stats

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT gp.*
        FROM game_puzzles gp
        WHERE gp.chess_username = ?
        AND gp.puzzle_id NOT IN (
            SELECT puzzle_id FROM puzzle_attempts
            WHERE username = ? AND solved = 1
        )
        ORDER BY gp.id DESC
        LIMIT ?
    """, (chess_username, app_username, limit))
    game_puzzles = [dict(r) for r in c.fetchall()]
    conn.close()

    # Parse pattern_tags back to list
    for p in game_puzzles:
        p["pattern_tags"] = json.loads(p["pattern_tags"] or "[]")

    # Get weaknesses and fetch matching Lichess puzzles
    stats = get_user_stats(chess_username)
    pattern_counts = stats.get("pattern_counts", {})

    lichess_puzzles = []
    for pattern, count in sorted(pattern_counts.items(),
                                  key=lambda x: x[1], reverse=True):
        theme = PATTERN_TO_THEME.get(pattern)
        if not theme:
            continue
        puzzle = get_themed_puzzle(theme)
        if puzzle:
            puzzle["pattern"] = pattern
            lichess_puzzles.append(puzzle)
        if len(lichess_puzzles) >= 3:
            break

    return {
        "game_puzzles": game_puzzles,
        "lichess_puzzles": lichess_puzzles,
    }


def record_attempt(username: str, puzzle_id: str,
                   puzzle_source: str, solved: bool):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO puzzle_attempts
        (username, puzzle_id, puzzle_source, solved)
        VALUES (?, ?, ?, ?)
    """, (username, puzzle_id, puzzle_source, 1 if solved else 0))
    conn.commit()
    conn.close()


def get_puzzle_stats(username: str) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT
            COUNT(*) as total_attempts,
            SUM(solved) as total_solved,
            COUNT(DISTINCT puzzle_id) as unique_puzzles
        FROM puzzle_attempts WHERE username = ?
    """, (username,))
    row = dict(c.fetchone())
    conn.close()
    total = row["total_attempts"] or 0
    solved = row["total_solved"] or 0
    row["solve_rate_pct"] = round((solved / total) * 100, 1) if total else 0
    return row
