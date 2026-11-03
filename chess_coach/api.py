import re
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from chess_coach.pipeline import run_pipeline, get_game_report
from chess_coach.database import init_db, get_user_games
from chess_coach.stats import get_user_stats
from chess_coach.auth import (
    init_users_table, create_user, authenticate_user,
    create_access_token, decode_token, get_user_by_username
)
from chess_coach.analysis.engine import find_stockfish
from chess_coach.puzzles import (
    init_puzzles_table, get_training_puzzles,
    record_attempt, get_puzzle_stats
)

app = FastAPI(title="Chess Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    init_users_table()
    init_puzzles_table()


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


class AttemptRequest(BaseModel):
    puzzle_id: str
    puzzle_source: str
    solved: bool


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


@app.get("/")
def root():
    return {"message": "Chess Coach API is running"}


@app.post("/auth/register")
def register(req: RegisterRequest):
    if len(req.password) < 8 or len(req.password.encode()) > 72:
        raise HTTPException(status_code=400,
                            detail="Password must be between 8 and 72 characters")
    try:
        email = req.email.strip().lower()
        if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]{2,}", email):
            raise HTTPException(status_code=400, detail="Enter a valid email address")
        user = create_user(req.username, email, req.password)
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
    if req.source not in ("chesscom", "lichess"):
        raise HTTPException(status_code=400,
                            detail="source must be 'chesscom' or 'lichess'")
    max_games = req.max_games
    if max_games < 1:
        max_games = 1
    if max_games > 100:
        max_games = 100
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
            "puzzles_generated": result.get("puzzles_generated", 0),
            "stats": result["stats"],
            "game_ids": [r.game_id for r in result["records"]],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/user/{username}/stats")
def user_stats(username: str, current_user: dict = Depends(get_current_user)):
    stats = get_user_stats(username.lower())
    if not stats:
        raise HTTPException(status_code=404,
                            detail="No analyzed games found for this user")
    return {"username": username, "stats": stats}


@app.get("/user/{username}/games")
def user_games(username: str, current_user: dict = Depends(get_current_user)):
    games = get_user_games(username.lower())
    if not games:
        raise HTTPException(status_code=404,
                            detail="No games found for this user")
    return {"username": username, "games": games}


@app.get("/game/{game_id:path}")
def game_report(game_id: str, current_user: dict = Depends(get_current_user)):
    report = get_game_report(game_id)
    if not report:
        raise HTTPException(status_code=404,
                            detail="Game not found or not yet analyzed")
    return report


@app.get("/puzzles/training")
def training_puzzles(chess_username: str,
                     current_user: dict = Depends(get_current_user)):
    puzzles = get_training_puzzles(
        chess_username=chess_username.lower(),
        app_username=current_user["username"],
        limit=5
    )
    return puzzles


@app.post("/puzzles/attempt")
def submit_attempt(req: AttemptRequest,
                   current_user: dict = Depends(get_current_user)):
    record_attempt(
        username=current_user["username"],
        puzzle_id=req.puzzle_id,
        puzzle_source=req.puzzle_source,
        solved=req.solved
    )
    return {"recorded": True}


@app.get("/puzzles/stats")
def puzzle_stats(current_user: dict = Depends(get_current_user)):
    stats = get_puzzle_stats(current_user["username"])
    return {"username": current_user["username"], "puzzle_stats": stats}




@app.delete("/user/{username}/cache")
def clear_cache(username: str, current_user: dict = Depends(get_current_user)):
    """Clear cached games for a chess username so they get re-analyzed."""
    username = username.lower()
    from chess_coach.database import get_connection
    conn = get_connection()
    from sqlalchemy import text as _sql_text
    conn.execute(_sql_text("DELETE FROM moves WHERE game_id IN (SELECT game_id FROM games WHERE username = :u)"), {"u": username})
    conn.execute(_sql_text("DELETE FROM games WHERE username = :u"), {"u": username})
    conn.commit()
    conn.execute(_sql_text("DELETE FROM game_puzzles WHERE chess_username = :u"), {"u": username})
    conn.commit()
    conn.close()
    return {"cleared": True, "username": username}


# --- Cheat Detection ---

class DetectRequest(BaseModel):
    chess_username: str
    max_games: int = 5
    source: str = "chesscom"


@app.post("/detect")
def detect_cheating(req: DetectRequest, current_user: dict = Depends(get_current_user)):
    """Run cheat detection on a player's recent games."""
    try:
        import sys
        sys.path.insert(0, '/opt/render/project/src')

        from chess_detector.fetcher import get_chesscom_games
        from chess_detector.core.analyzer import analyze_pgn as detect_analyze_pgn
        from chess_detector.scorer import SuspicionScorer

        scorer = SuspicionScorer()
        reports = []

        if req.source == "chesscom":
            pgns = get_chesscom_games(req.chess_username, max_games=req.max_games)
        else:
            from chess_detector.fetcher import get_lichess_games
            pgns = get_lichess_games(req.chess_username, max_games=req.max_games)

        if not pgns:
            raise HTTPException(status_code=404, detail="No games found for this user")

        for pgn_text in pgns[:req.max_games]:
            try:
                analysis = detect_analyze_pgn(pgn_text, req.chess_username)
                if analysis is None:
                    continue
                color = analysis.player_color
                report = scorer.score(
                    analysis,
                    req.chess_username,
                    color,
                    pgn_text=pgn_text
                )
                reports.append({
                    "game_id": report.game_id,
                    "color": report.color,
                    "overall_score": report.overall_score,
                    "verdict": report.verdict,
                    "features": [
                        {
                            "name": f.name,
                            "score": f.score,
                            "note": f.note,
                            "weight": f.weight,
                        }
                        for f in report.features
                    ],
                    "flagged_moves": report.flagged_moves,
                })
            except Exception as e:
                print(f"Skipping game: {e}")
                continue

        if not reports:
            raise HTTPException(status_code=400, detail="Could not analyze any games")

        avg_score = round(sum(r["overall_score"] for r in reports) / len(reports), 1)
        if avg_score < 30:
            overall_verdict = "clean"
        elif avg_score < 60:
            overall_verdict = "suspicious"
        else:
            overall_verdict = "likely cheating"

        return {
            "username": req.chess_username,
            "games_analyzed": len(reports),
            "average_score": avg_score,
            "overall_verdict": overall_verdict,
            "reports": reports,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
