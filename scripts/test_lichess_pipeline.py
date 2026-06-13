from chess_coach.pipeline import run_pipeline

if __name__ == "__main__":
    result = run_pipeline("DrNykterstein", max_games=2, depth=10, source="lichess")
    print(f"Username: {result['username']}")
    print(f"Source: {result['source']}")
    print(f"Games processed: {result['games_analyzed']}")
    print()
    print("=== STATS ===")
    for k, v in result["stats"].items():
        print(f"  {k}: {v}")
