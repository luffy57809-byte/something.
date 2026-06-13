from chess_coach.stats import get_user_stats, get_game_summary

if __name__ == "__main__":
    username = "magnus"

    print("=== USER STATS ===")
    stats = get_user_stats(username)
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print()
    print("=== GAME SUMMARY ===")
    game_id = "https://www.chess.com/game/daily/4536331"
    summary = get_game_summary(game_id)
    for k, v in summary.items():
        print(f"  {k}: {v}")
