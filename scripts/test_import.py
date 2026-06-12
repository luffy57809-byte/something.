from chess_coach.importers.chesscom import get_recent_games

if __name__ == "__main__":
    username = "Walid_150"
    games = get_recent_games(username, max_games=3)
    print(f"Fetched {len(games)} games")
    for g in games:
        print(g["url"], "-", g.get("time_control"), "-", g.get("end_time"))
