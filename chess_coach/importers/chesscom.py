import requests

BASE_URL = "https://api.chess.com/pub/player"


def get_archives(username: str) -> list[str]:
    url = f"{BASE_URL}/{username}/games/archives"
    headers = {"User-Agent": "ChessCoachApp/1.0 (contact: youremail@example.com)"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()["archives"]


def get_games_from_archive(archive_url: str) -> list[dict]:
    headers = {"User-Agent": "ChessCoachApp/1.0 (contact: youremail@example.com)"}
    resp = requests.get(archive_url, headers=headers)
    resp.raise_for_status()
    return resp.json()["games"]


def get_recent_games(username: str, max_games: int = 10) -> list[dict]:
    """Get the most recent games strictly by end_time."""
    archives = get_archives(username)
    if not archives:
        return []

    all_games = []

    # Only look at the 2 most recent archives to avoid mixing old games
    for archive_url in reversed(archives[-2:]):
        monthly_games = get_games_from_archive(archive_url)
        all_games.extend(monthly_games)

    # Sort all games by end_time descending — newest first
    all_games.sort(key=lambda g: g.get("end_time", 0), reverse=True)

    # Filter to only standard chess
    all_games = [g for g in all_games if g.get("rules", "chess") == "chess"]

    return all_games[:max_games]
