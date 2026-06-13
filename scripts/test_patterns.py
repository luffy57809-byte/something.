from chess_coach.importers.chesscom import get_recent_games
from chess_coach.analysis.game_analyzer import analyze_pgn
from chess_coach.coaching.templates import generate_explanation

if __name__ == "__main__":
    username = "Walid_150"
    games = get_recent_games(username, max_games=1)
    pgn_text = games[0]["pgn"]

    print("Analyzing game...")
    record = analyze_pgn(pgn_text, depth=10)

    print(f"{record.white} vs {record.black} - {record.result}")
    print()

    for m in record.moves:
        if m.classification in ("blunder", "mistake") and m.pattern_tags:
            print(f"Move {m.move_number} ({m.color}): {m.move_san} -> {m.classification.upper()}")
            print(f"  Tags: {m.pattern_tags}")
            print(f"  {generate_explanation(m)}")
            print()
