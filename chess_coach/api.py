from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from chess_coach.pipeline import run_pipeline, get_game_report
from chess_coach.database import init_db, get_user_games
from chess_coach.stats import get_user_stats

app = FastAPI(title="Chess Coach API")


@app.on_event("startup")
def startup():
    init_db()


# --- Request/Response Models ---

class AnalyzeRequest(BaseModel):
    username: str
    max_games: int = 5
    depth: int = 10


# --- Endpoints ---

@app.get("/")
def root():
    return {"message": "Chess Coach API is running"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    Fetch and analyze recent games for a Chess.com username.
    Already-analyzed games are loaded from cache.
    """
    try:
        result = run_pipeline(
            username=req.username,
            max_games=req.max_games,
            depth=req.depth
        )
        return {
            "username": result["username"],
            "games_analyzed": result["games_analyzed"],
            "stats": result["stats"],
            "game_ids": [r.game_id for r in result["records"]],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/user/{username}/stats")
def user_stats(username: str):
    """Get overall stats for a user."""
    stats = get_user_stats(username)
    if not stats:
        raise HTTPException(status_code=404, detail="No analyzed games found for this user")
    return {"username": username, "stats": stats}


@app.get("/user/{username}/games")
def user_games(username: str):
    """List all analyzed games for a user."""
    games = get_user_games(username)
    if not games:
        raise HTTPException(status_code=404, detail="No games found for this user")
    return {"username": username, "games": games}


@app.get("/game/{game_id:path}")
def game_report(game_id: str):
    """Get the full report for a single analyzed game."""
    report = get_game_report(game_id)
    if not report:
        raise HTTPException(status_code=404, detail="Game not found or not yet analyzed")
    return report
