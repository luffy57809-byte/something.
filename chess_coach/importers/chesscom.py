import requests

BASE_URL = "https://api.chess.com/pub/player"


def get_archives(username: str) -> list[str]:
    """Get list of monthly archive URLs for a Chess.com user."""
    url = f"{BASE_URL}/{username}/games/archives"
    headers = {"User-Agent": "ChessCoachApp/1.0 (contact: youremail@example.com)"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()["archives"]


def get_games_from_archive(archive_url: str) -> list[dict]:
    """Fetch all games from a single monthly archive."""
    headers = {"User-Agent": "ChessCoachApp/1.0 (contact: youremail@example.com)"}
    resp = requests.get(archive_url, headers=headers)
    resp.raise_for_status()
    return resp.json()["games"]


def get_recent_games(username: str, max_games: int = 10) -> list[dict]:
    """Get the most recent games for a user, newest first."""
    archives = get_archives(username)
    games = []

    for archive_url in reversed(archives):
        monthly_games = get_games_from_archive(archive_url)
        games.extend(reversed(monthly_games))
        if len(games) >= max_games:
            break

    return games[:max_games]
