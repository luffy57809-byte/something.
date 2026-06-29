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
    """Get the most recent games from the latest archive only."""
    archives = get_archives(username)
    if not archives:
        return []

    # Only use the most recent archive
    latest_archive = archives[-1]
    games = get_games_from_archive(latest_archive)

    # Sort by end_time descending — newest first
    games.sort(key=lambda g: g.get("end_time", 0), reverse=True)

    # Filter to standard chess only
    games = [g for g in games if g.get("rules", "chess") == "chess"]

    return games[:max_games]
