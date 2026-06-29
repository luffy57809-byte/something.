import json
import requests as http_requests
from sqlalchemy import text
from chess_coach.database import engine

PATTERN_TO_THEME = {
    "missed_fork": "fork",
    "missed_pin": "pin",
    "hanging_piece": "hangingPiece",
    "back_rank_weakness": "backRankMate",
}


def init_puzzles_table():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS puzzles (
                id SERIAL PRIMARY KEY,
                puzzle_id TEXT UNIQUE NOT NULL,
                fen TEXT NOT NULL,
                moves TEXT NOT NULL,
                rating INTEGER,
                themes TEXT,
                game_url TEXT,
                source TEXT DEFAULT 'lichess'
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS game_puzzles (
                id SERIAL PRIMARY KEY,
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
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS puzzle_attempts (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                puzzle_id TEXT NOT NULL,
                puzzle_source TEXT NOT NULL,
                solved INTEGER NOT NULL,
                attempted_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()


def extract_game_puzzles(record, chess_username: str) -> list[dict]:
    puzzles = []
    with engine.connect() as conn:
        for m in record.moves:
            if m.classification not in ("blunder", "mistake"):
                continue
            if not m.best_move_san:
                continue

            puzzle_id = f"{record.game_id}__move{m.move_number}_{m.color}"

            existing = conn.execute(
                text("SELECT id FROM game_puzzles WHERE puzzle_id = :pid"),
                {"pid": puzzle_id}
            ).fetchone()
            if existing:
                continue

            conn.execute(text("""
                INSERT INTO game_puzzles
                (puzzle_id, game_id, chess_username, move_number, color, fen,
                 best_move, classification, pattern_tags, explanation, source)
                VALUES (:puzzle_id, :game_id, :chess_username, :move_number,
                        :color, :fen, :best_move, :classification,
                        :pattern_tags, :explanation, 'game')
            """), {
                "puzzle_id": puzzle_id,
                "game_id": record.game_id,
                "chess_username": chess_username,
                "move_number": m.move_number,
                "color": m.color,
                "fen": m.fen_before,
                "best_move": m.best_move_san,
                "classification": m.classification,
                "pattern_tags": json.dumps(m.pattern_tags),
                "explanation": m.explanation
            })

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
    return puzzles


def fetch_lichess_puzzle(theme: str) -> dict | None:
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
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO puzzles (puzzle_id, fen, moves, rating, themes, game_url, source)
            VALUES (:puzzle_id, :fen, :moves, :rating, :themes, :game_url, 'lichess')
            ON CONFLICT (puzzle_id) DO NOTHING
        """), puzzle)
        conn.commit()


def get_themed_puzzle(theme: str) -> dict | None:
    puzzle = fetch_lichess_puzzle(theme)
    if puzzle:
        save_lichess_puzzle(puzzle)
    return puzzle


def get_training_puzzles(chess_username: str, app_username: str,
                         limit: int = 5) -> dict:
    from chess_coach.stats import get_user_stats

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT gp.*
            FROM game_puzzles gp
            WHERE gp.chess_username = :username
            AND gp.puzzle_id NOT IN (
                SELECT puzzle_id FROM puzzle_attempts
                WHERE username = :app_username AND solved = 1
            )
            ORDER BY gp.id DESC
            LIMIT :limit
        """), {
            "username": chess_username,
            "app_username": app_username,
            "limit": limit
        }).fetchall()

    game_puzzles = []
    for row in rows:
        game_puzzles.append({
            "id": row[0],
            "puzzle_id": row[1],
            "game_id": row[2],
            "chess_username": row[3],
            "move_number": row[4],
            "color": row[5],
            "fen_before": row[6],
            "best_move": row[7],
            "classification": row[8],
            "pattern_tags": json.loads(row[9] or "[]"),
            "explanation": row[10],
            "source": row[11],
        })

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
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO puzzle_attempts
            (username, puzzle_id, puzzle_source, solved)
            VALUES (:username, :puzzle_id, :puzzle_source, :solved)
        """), {
            "username": username,
            "puzzle_id": puzzle_id,
            "puzzle_source": puzzle_source,
            "solved": 1 if solved else 0
        })
        conn.commit()


def get_puzzle_stats(username: str) -> dict:
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT
                COUNT(*) as total_attempts,
                SUM(solved) as total_solved,
                COUNT(DISTINCT puzzle_id) as unique_puzzles
            FROM puzzle_attempts WHERE username = :username
        """), {"username": username}).fetchone()

    total = row[0] or 0
    solved = row[1] or 0
    return {
        "total_attempts": total,
        "total_solved": solved,
        "unique_puzzles": row[2] or 0,
        "solve_rate_pct": round((solved / total) * 100, 1) if total else 0
    }
