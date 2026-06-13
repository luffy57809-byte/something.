from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chess_coach.pipeline import run_pipeline, get_game_report
from chess_coach.database import init_db, get_user_games
from chess_coach.stats import get_user_stats

app = FastAPI(title="Chess Coach API")


@app.on_event("startup")
def startup():
    init_db()


class AnalyzeRequest(BaseModel):
    username: str
    max_games: int = 5
    depth: int = 10
    source: str = "chesscom"


@app.get("/")
def root():
    return {"message": "Chess Coach API is running"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """Fetch and analyze recent games. source: 'chesscom' or 'lichess'"""
    if req.source not in ("chesscom", "lichess"):
        raise HTTPException(status_code=400, detail="source must be 'chesscom' or 'lichess'")
    try:
        result = run_pipeline(
            username=req.username,
            max_games=req.max_games,
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
def user_stats(username: str):
    stats = get_user_stats(username)
    if not stats:
        raise HTTPException(status_code=404, detail="No analyzed games found for this user")
    return {"username": username, "stats": stats}


@app.get("/user/{username}/games")
def user_games(username: str):
    games = get_user_games(username)
    if not games:
        raise HTTPException(status_code=404, detail="No games found for this user")
    return {"username": username, "games": games}


@app.get("/game/{game_id:path}")
def game_report(game_id: str):
    report = get_game_report(game_id)
    if not report:
        raise HTTPException(status_code=404, detail="Game not found or not yet analyzed")
    return report
