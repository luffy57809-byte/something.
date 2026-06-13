from chess_coach.importers.lichess import get_recent_games

if __name__ == "__main__":
    games = get_recent_games("DrNykterstein", max_games=2)
    for g in games:
        print("=== GAME ===")
        print("URL:", g["url"])
        print("PGN preview:")
        print(repr(g["pgn"][:500]))
        print()
