from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional

from chess_coach.pipeline import run_pipeline, get_game_report
from chess_coach.database import init_db, get_user_games
from chess_coach.stats import get_user_stats
from chess_coach.auth import (
    init_users_table, create_user, authenticate_user,
    create_access_token, decode_token, get_user_by_username
)

app = FastAPI(title="Chess Coach API")


@app.on_event("startup")
def startup():
    init_db()
    init_users_table()


# --- Request Models ---

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AnalyzeRequest(BaseModel):
    chess_username: str
    max_games: int = 5
    depth: int = 10
    source: str = "chesscom"


# --- Auth dependency ---

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_username(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_premium(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user["is_premium"]:
        raise HTTPException(status_code=403, detail="Premium subscription required")
    return current_user


# --- Endpoints ---

@app.get("/")
def root():
    return {"message": "Chess Coach API is running"}


@app.post("/auth/register")
def register(req: RegisterRequest):
    if len(req.password) < 8 or len(req.password.encode()) > 72:
        raise HTTPException(status_code=400, detail="Password must be between 8 and 72 characters")
    try:
        user = create_user(req.username, req.email, req.password)
        token = create_access_token({"sub": user["username"]})
        return {"access_token": token, "token_type": "bearer", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": user["username"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "is_premium": bool(user["is_premium"])
        }
    }


@app.get("/auth/me")
def me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "is_premium": bool(current_user["is_premium"])
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    """Analyze recent games. Requires authentication."""
    if req.source not in ("chesscom", "lichess"):
        raise HTTPException(status_code=400, detail="source must be 'chesscom' or 'lichess'")

    # Free users limited to 5 games, premium unlimited
    max_games = req.max_games
    if not current_user["is_premium"] and max_games > 5:
        max_games = 5

    try:
        result = run_pipeline(
            username=req.chess_username,
            max_games=max_games,
            depth=req.depth,
            source=req.source,
        )
        return {
            "username": result["username"],
            "source": result["source"],
            "games_analyzed": result["games_analyzed"],
            "stats": result["stats"],
            "game_ids": [r.game_id for r in result["records"]],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/user/{username}/stats")
def user_stats(username: str, current_user: dict = Depends(get_current_user)):
    stats = get_user_stats(username)
    if not stats:
        raise HTTPException(status_code=404, detail="No analyzed games found for this user")
    return {"username": username, "stats": stats}


@app.get("/user/{username}/games")
def user_games(username: str, current_user: dict = Depends(get_current_user)):
    games = get_user_games(username)
    if not games:
        raise HTTPException(status_code=404, detail="No games found for this user")
    return {"username": username, "games": games}


@app.get("/game/{game_id:path}")
def game_report(game_id: str, current_user: dict = Depends(get_current_user)):
    report = get_game_report(game_id)
    if not report:
        raise HTTPException(status_code=404, detail="Game not found or not yet analyzed")
    return report
