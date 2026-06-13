import requests

BASE = "http://127.0.0.1:8000"

# Register
print("=== REGISTER ===")
resp = requests.post(f"{BASE}/auth/register", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
})
print(resp.json())
token = resp.json().get("access_token")

# Login
print("\n=== LOGIN ===")
resp = requests.post(f"{BASE}/auth/login", json={
    "username": "testuser",
    "password": "password123"
})
print(resp.json())
token = resp.json().get("access_token")

# Me
print("\n=== ME ===")
resp = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
print(resp.json())

# Try analyze without token
print("\n=== ANALYZE WITHOUT TOKEN ===")
resp = requests.post(f"{BASE}/analyze", json={"chess_username": "Walid_150"})
print(resp.status_code, resp.json())

# Analyze with token
print("\n=== ANALYZE WITH TOKEN ===")
resp = requests.post(f"{BASE}/analyze",
    headers={"Authorization": f"Bearer {token}"},
    json={"chess_username": "Walid_150", "max_games": 3}
)
print(resp.status_code, resp.json())
