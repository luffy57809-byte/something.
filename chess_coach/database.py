import sqlite3
import json
import os
from chess_coach.models import GameRecord, MoveAnalysis

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "chess_coach.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            game_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            pgn TEXT NOT NULL,
            white TEXT NOT NULL,
            black TEXT NOT NULL,
            result TEXT NOT NULL,
            time_control TEXT,
            date TEXT,
            analyzed INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            move_number INTEGER NOT NULL,
            color TEXT NOT NULL,
            move_san TEXT NOT NULL,
            fen_before TEXT NOT NULL,
            fen_after TEXT NOT NULL,
            eval_before INTEGER,
            eval_after INTEGER,
            best_move_san TEXT,
            eval_drop INTEGER,
            classification TEXT,
            pattern_tags TEXT,
            explanation TEXT,
            FOREIGN KEY (game_id) REFERENCES games (game_id)
        )
    """)

    conn.commit()
    conn.close()


def save_game(record: GameRecord, username: str):
    """Save a fully analyzed game to the database."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT OR REPLACE INTO games
        (game_id, username, pgn, white, black, result, time_control, date, analyzed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (record.game_id, username, record.pgn, record.white,
          record.black, record.result, record.time_control, record.date))

    c.execute("DELETE FROM moves WHERE game_id = ?", (record.game_id,))

    for m in record.moves:
        c.execute("""
            INSERT INTO moves
            (game_id, move_number, color, move_san, fen_before, fen_after,
             eval_before, eval_after, best_move_san, eval_drop,
             classification, pattern_tags, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.game_id, m.move_number, m.color, m.move_san,
            m.fen_before, m.fen_after, m.eval_before, m.eval_after,
            m.best_move_san, m.eval_drop, m.classification,
            json.dumps(m.pattern_tags), m.explanation
        ))

    conn.commit()
    conn.close()


def game_exists(game_id: str) -> bool:
    """Check if a game has already been analyzed and saved."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT analyzed FROM games WHERE game_id = ?", (game_id,))
    row = c.fetchone()
    conn.close()
    return row is not None and row["analyzed"] == 1


def load_game(game_id: str) -> GameRecord | None:
    """Load a fully analyzed game from the database."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM games WHERE game_id = ?", (game_id,))
    game_row = c.fetchone()
    if not game_row:
        conn.close()
        return None

    c.execute("SELECT * FROM moves WHERE game_id = ? ORDER BY id", (game_id,))
    move_rows = c.fetchall()
    conn.close()

    record = GameRecord(
        game_id=game_row["game_id"],
        pgn=game_row["pgn"],
        white=game_row["white"],
        black=game_row["black"],
        result=game_row["result"],
        time_control=game_row["time_control"],
        date=game_row["date"],
    )

    for row in move_rows:
        m = MoveAnalysis(
            move_number=row["move_number"],
            color=row["color"],
            move_san=row["move_san"],
            fen_before=row["fen_before"],
            fen_after=row["fen_after"],
            eval_before=row["eval_before"],
            eval_after=row["eval_after"],
            best_move_san=row["best_move_san"],
            eval_drop=row["eval_drop"],
            classification=row["classification"],
            pattern_tags=json.loads(row["pattern_tags"] or "[]"),
            explanation=row["explanation"],
        )
        record.moves.append(m)

    return record


def get_user_games(username: str) -> list[dict]:
    """Get summary of all analyzed games for a user."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT game_id, white, black, result, date, time_control
        FROM games WHERE username = ?
        ORDER BY date DESC
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
