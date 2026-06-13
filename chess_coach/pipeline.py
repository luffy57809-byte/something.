from chess_coach.importers.chesscom import get_recent_games
from chess_coach.analysis.game_analyzer import analyze_pgn
from chess_coach.coaching.templates import generate_explanation
from chess_coach.database import init_db, save_game, game_exists, load_game, get_user_games
from chess_coach.stats import get_user_stats, get_game_summary


def run_pipeline(username: str, max_games: int = 10, depth: int = 10) -> dict:
    """
    Full pipeline: fetch games, analyze new ones, return stats + reports.
    Already-analyzed games are loaded from DB instantly.
    """
    init_db()

    print(f"Fetching recent games for {username}...")
    raw_games = get_recent_games(username, max_games=max_games)

    records = []
    for raw in raw_games:
        game_id = raw["url"]

        if game_exists(game_id):
            print(f"  Loading cached: {game_id}")
            record = load_game(game_id)
        else:
            print(f"  Analyzing new game: {game_id}")
            record = analyze_pgn(raw["pgn"], depth=depth)
            for m in record.moves:
                m.explanation = generate_explanation(m)
            save_game(record, username)

        records.append(record)

    stats = get_user_stats(username)

    return {
        "username": username,
        "games_analyzed": len(records),
        "stats": stats,
        "records": records,
    }


def get_game_report(game_id: str) -> dict | None:
    """Get the full report for a single game by ID."""
    record = load_game(game_id)
    if not record:
        return None

    summary = get_game_summary(game_id)
    flagged = [
        {
            "move_number": m.move_number,
            "color": m.color,
            "move_san": m.move_san,
            "classification": m.classification,
            "best_move_san": m.best_move_san,
            "eval_drop": m.eval_drop,
            "pattern_tags": m.pattern_tags,
            "explanation": m.explanation,
            "fen_before": m.fen_before,
        }
        for m in record.moves
        if m.classification in ("blunder", "mistake", "inaccuracy")
    ]

    return {
        "game_id": game_id,
        "white": record.white,
        "black": record.black,
        "result": record.result,
        "date": record.date,
        "summary": summary,
        "flagged_moves": flagged,
    }
