from chess_coach.importers.chesscom import get_recent_games
from chess_coach.analysis.game_analyzer import analyze_pgn
from chess_coach.coaching.explain import explain_move

if __name__ == "__main__":
    username = "magnus"
    games = get_recent_games(username, max_games=1)
    pgn_text = games[0]["pgn"]

    print("Analyzing game...")
    record = analyze_pgn(pgn_text, depth=10)

    # Find the first blunder or mistake
    flagged = [m for m in record.moves if m.classification in ("blunder", "mistake")]

    if not flagged:
        print("No mistakes found!")
    else:
        m = flagged[0]
        print(f"Move {m.move_number} ({m.color}): {m.move_san} -> {m.classification.upper()}")
        print(f"Best was: {m.best_move_san}")
        print()
        print("Generating explanation...")
        explanation = explain_move(m, record.white, record.black)
        print()
        print(explanation)
