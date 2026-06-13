import requests
import json

BASE_URL = "https://lichess.org/api"


def get_recent_games(username: str, max_games: int = 10) -> list[dict]:
    """
    Fetch recent games for a Lichess user.
    Returns a list of dicts with 'pgn', 'url', 'time_control' keys
    to match the Chess.com importer format.
    """
    url = f"{BASE_URL}/games/user/{username}"
    headers = {
        "Accept": "application/x-ndjson",
        "User-Agent": "ChessCoachApp/1.0"
    }
    params = {
        "max": max_games,
        "pgnInJson": "true",  # explicitly request PGN inside JSON
        "opening": "false",
        "clocks": "false",
        "evals": "false",
    }

    resp = requests.get(url, headers=headers, params=params, stream=True)
    resp.raise_for_status()

    games = []
    for line in resp.iter_lines():
        if line:
            game = json.loads(line)
            games.append(game)

    return _normalize(games)


def _normalize(raw_games: list[dict]) -> list[dict]:
    """
    Convert Lichess game format to match our internal format.
    """
    normalized = []
    for g in raw_games:
        players = g.get("players", {})
        white = players.get("white", {}).get("user", {}).get("name", "?")
        black = players.get("black", {}).get("user", {}).get("name", "?")

        clock = g.get("clock", {})
        time_control = str(clock.get("initial", "?")) if clock else "?"

        pgn = g.get("pgn", "")

        normalized.append({
            "url": f"https://lichess.org/{g['id']}",
            "pgn": pgn,
            "white": white,
            "black": black,
            "time_control": time_control,
            "end_time": g.get("lastMoveAt", ""),
            "source": "lichess",
        })

    return normalized
