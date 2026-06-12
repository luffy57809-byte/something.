from chess_coach.importers.chesscom import get_recent_games
from chess_coach.analysis.game_analyzer import analyze_pgn
from chess_coach.coaching.templates import generate_explanation

if __name__ == "__main__":
    username = "magnus"
    games = get_recent_games(username, max_games=1)
    pgn_text = games[0]["pgn"]

    print("Analyzing game...")
    record = analyze_pgn(pgn_text, depth=10)

    print(f"{record.white} vs {record.black} - {record.result}")
    print(f"Total moves: {len(record.moves)}")
    print()

    for m in record.moves:
        if m.classification in ("blunder", "mistake"):
            print(f"Move {m.move_number} ({m.color}): {m.move_san} "
                  f"-> {m.classification.upper()} "
                  f"(eval drop: {m.eval_drop}, best was {m.best_move_san})")
            print(f"  Tags: {m.pattern_tags}")
            print(f"  Explanation: {generate_explanation(m)}")
            print()
