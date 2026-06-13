import requests
import csv
import io
import gzip

# Themes we care about - matching our pattern tags
TARGET_THEMES = {
    "fork", "pin", "hangingPiece", "backRankMate",
    "discoveredAttack", "skewer", "doubleCheck"
}

PUZZLE_URL = "https://database.lichess.org/lichess_db_puzzle.csv.zst"

# We'll use the smaller sample instead
SAMPLE_URL = "https://raw.githubusercontent.com/lichess-org/chess-puzzles/main/README.md"

print("Downloading Lichess puzzles via API (no huge download needed)...")

def get_puzzles_by_theme(theme: str, max_puzzles: int = 50) -> list[dict]:
    """Fetch puzzles for a specific theme from Lichess puzzle API."""
    url = f"https://lichess.org/api/puzzle/next"
    puzzles = []
    seen = set()

    for _ in range(max_puzzles):
        resp = requests.get(url, params={"angle": theme})
        if resp.status_code != 200:
            break
        data = resp.json()
        puzzle_id = data["puzzle"]["id"]
        if puzzle_id in seen:
            continue
        seen.add(puzzle_id)

        puzzles.append({
            "puzzle_id": puzzle_id,
            "fen": data["game"]["fen"] if "fen" in data.get("game", {}) else data["puzzle"].get("fen", ""),
            "moves": " ".join(data["puzzle"]["solution"]),
            "rating": data["puzzle"]["rating"],
            "themes": " ".join(data["puzzle"]["themes"]),
            "game_url": data["game"].get("id", ""),
        })

    return puzzles

# Test with one theme
puzzles = get_puzzles_by_theme("fork", max_puzzles=5)
print(f"Fetched {len(puzzles)} fork puzzles")
for p in puzzles:
    print(f"  {p['puzzle_id']} - rating {p['rating']} - themes: {p['themes']}")
