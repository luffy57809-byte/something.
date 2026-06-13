from chess_coach.importers.lichess import get_recent_games

if __name__ == "__main__":
    username = "DrNykterstein"
    games = get_recent_games(username, max_games=3)
    print(f"Fetched {len(games)} games")
    for g in games:
        print(g["url"], "-", g["time_control"], "-", g["white"], "vs", g["black"])
