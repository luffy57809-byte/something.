from chess_coach.pipeline import run_pipeline, get_game_report
import json

if __name__ == "__main__":
    username = "magnus"

    result = run_pipeline(username, max_games=3, depth=10)

    print(f"Username: {result['username']}")
    print(f"Games processed: {result['games_analyzed']}")
    print()
    print("=== STATS ===")
    for k, v in result["stats"].items():
        print(f"  {k}: {v}")

    print()
    print("=== FIRST GAME REPORT ===")
    game_id = result["records"][0].game_id
    report = get_game_report(game_id)
    print(f"{report['white']} vs {report['black']} - {report['result']}")
    print(f"Flagged moves: {len(report['flagged_moves'])}")
    for move in report["flagged_moves"]:
        if move["classification"] in ("blunder", "mistake"):
            print(f"  Move {move['move_number']} ({move['color']}): "
                  f"{move['move_san']} -> {move['classification'].upper()}")
            print(f"    {move['explanation']}")
