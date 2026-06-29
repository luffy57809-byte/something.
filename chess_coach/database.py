import os
import json
from chess_coach.models import GameRecord, MoveAnalysis
from sqlalchemy import create_engine, text

# Use Supabase PostgreSQL in production, SQLite locally
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///chess_coach.db"
)

# Fix for SQLAlchemy + PostgreSQL URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)


def get_connection():
    return engine.connect()


def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
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
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS moves (
                id SERIAL PRIMARY KEY,
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
        """))
        conn.commit()


def save_game(record: GameRecord, username: str):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO games
            (game_id, username, pgn, white, black, result, time_control, date, analyzed)
            VALUES (:game_id, :username, :pgn, :white, :black, :result,
                    :time_control, :date, 1)
            ON CONFLICT (game_id) DO UPDATE SET analyzed = 1
        """), {
            "game_id": record.game_id, "username": username,
            "pgn": record.pgn, "white": record.white,
            "black": record.black, "result": record.result,
            "time_control": record.time_control, "date": record.date
        })

        conn.execute(text("DELETE FROM moves WHERE game_id = :game_id"),
                     {"game_id": record.game_id})

        for m in record.moves:
            conn.execute(text("""
                INSERT INTO moves
                (game_id, move_number, color, move_san, fen_before, fen_after,
                 eval_before, eval_after, best_move_san, eval_drop,
                 classification, pattern_tags, explanation)
                VALUES (:game_id, :move_number, :color, :move_san, :fen_before,
                        :fen_after, :eval_before, :eval_after, :best_move_san,
                        :eval_drop, :classification, :pattern_tags, :explanation)
            """), {
                "game_id": record.game_id,
                "move_number": m.move_number,
                "color": m.color,
                "move_san": m.move_san,
                "fen_before": m.fen_before,
                "fen_after": m.fen_after,
                "eval_before": m.eval_before,
                "eval_after": m.eval_after,
                "best_move_san": m.best_move_san,
                "eval_drop": m.eval_drop,
                "classification": m.classification,
                "pattern_tags": json.dumps(m.pattern_tags),
                "explanation": m.explanation
            })
        conn.commit()


def game_exists(game_id: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT analyzed FROM games WHERE game_id = :game_id"),
            {"game_id": game_id}
        ).fetchone()
        return result is not None and result[0] == 1


def load_game(game_id: str) -> GameRecord | None:
    with engine.connect() as conn:
        game_row = conn.execute(
            text("SELECT * FROM games WHERE game_id = :game_id"),
            {"game_id": game_id}
        ).fetchone()

        if not game_row:
            return None

        move_rows = conn.execute(
            text("SELECT * FROM moves WHERE game_id = :game_id ORDER BY id"),
            {"game_id": game_id}
        ).fetchall()

    record = GameRecord(
        game_id=game_row[0],
        pgn=game_row[2],
        white=game_row[3],
        black=game_row[4],
        result=game_row[5],
        time_control=game_row[6],
        date=game_row[7],
    )

    for row in move_rows:
        m = MoveAnalysis(
            move_number=row[2],
            color=row[3],
            move_san=row[4],
            fen_before=row[5],
            fen_after=row[6],
            eval_before=row[7],
            eval_after=row[8],
            best_move_san=row[9],
            eval_drop=row[10],
            classification=row[11],
            pattern_tags=json.loads(row[12] or "[]"),
            explanation=row[13],
        )
        record.moves.append(m)

    return record


def get_user_games(username: str) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT game_id, white, black, result, date, time_control
            FROM games WHERE username = :username
            ORDER BY date DESC
        """), {"username": username}).fetchall()

    return [
        {
            "game_id": r[0], "white": r[1], "black": r[2],
            "result": r[3], "date": r[4], "time_control": r[5]
        }
        for r in rows
    ]


def get_connection_raw():
    """For backward compatibility with code using raw connections."""
    return engine.connect()
