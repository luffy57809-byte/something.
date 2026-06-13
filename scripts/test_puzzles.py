import requests

BASE = "http://127.0.0.1:8000"

resp = requests.post(f"{BASE}/auth/login", json={
    "username": "testuser",
    "password": "password123"
})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== ANALYZE ===")
resp = requests.post(f"{BASE}/analyze", headers=headers, json={
    "chess_username": "Walid_150",
    "max_games": 3
})
data = resp.json()
print(f"Games analyzed: {data['games_analyzed']}")
print(f"Puzzles generated: {data['puzzles_generated']}")

print("\n=== TRAINING PUZZLES ===")
resp = requests.get(f"{BASE}/puzzles/training?chess_username=Walid_150",
                    headers=headers)
data = resp.json()
print(f"Game puzzles: {len(data['game_puzzles'])}")
for p in data["game_puzzles"][:3]:
    print(f"  [{p['classification'].upper()}] Move {p['move_number']} "
          f"({p['color']}): best was {p['best_move']}")
    print(f"  Tags: {p['pattern_tags']}")
    print(f"  {p['explanation'][:80]}...")

print(f"\nLichess puzzles: {len(data['lichess_puzzles'])}")
for p in data["lichess_puzzles"]:
    print(f"  [{p.get('pattern')}] {p['puzzle_id']} "
          f"rating {p['rating']} - {p['themes'][:50]}")

print("\n=== SUBMIT ATTEMPT ===")
if data["game_puzzles"]:
    puzzle_id = data["game_puzzles"][0]["puzzle_id"]
    resp = requests.post(f"{BASE}/puzzles/attempt", headers=headers, json={
        "puzzle_id": puzzle_id,
        "puzzle_source": "game",
        "solved": True
    })
    print(resp.json())

print("\n=== PUZZLE STATS ===")
resp = requests.get(f"{BASE}/puzzles/stats", headers=headers)
print(resp.json())
