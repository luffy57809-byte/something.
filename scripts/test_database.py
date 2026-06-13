from chess_coach.database import init_db, save_game, game_exists, load_game, get_user_games
from chess_coach.importers.chesscom import get_recent_games
from chess_coach.analysis.game_analyzer import analyze_pgn
from chess_coach.coaching.templates import generate_explanation

if __name__ == "__main__":
    username = "magnus"
    init_db()

    games = get_recent_games(username, max_games=1)
    game_data = games[0]
    game_id = game_data["url"]

    if game_exists(game_id):
        print("Game already analyzed - loading from database...")
        record = load_game(game_id)
    else:
        print("Analyzing game...")
        record = analyze_pgn(game_data["pgn"], depth=10)
        for m in record.moves:
            m.explanation = generate_explanation(m)
        save_game(record, username)
        print("Saved to database.")

    print(f"{record.white} vs {record.black} - {record.result}")
    print(f"Total moves: {len(record.moves)}")
    print()

    for m in record.moves:
        if m.classification in ("blunder", "mistake"):
            print(f"Move {m.move_number} ({m.color}): {m.move_san} -> {m.classification.upper()}")
            print(f"  {m.explanation}")
            print()

    print("User games in DB:", get_user_games(username))
