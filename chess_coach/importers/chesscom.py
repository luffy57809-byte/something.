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
    # Walk back through monthly archives (newest first) until we have enough games
    archives = get_archives(username)
    games = []
    for archive_url in list(reversed(archives))[:6]:
        month_games = get_games_from_archive(archive_url)
        games.extend(g for g in month_games if g.get("rules", "chess") == "chess")
        if len(games) >= max_games:
            break

    # Newest first
    games.sort(key=lambda g: g.get("end_time", 0), reverse=True)
    return games[:max_games]
