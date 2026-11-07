import re
import threading
import time
import html as _html
import os as _os
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from chess_coach.pipeline import run_pipeline, get_game_report
from chess_coach.database import init_db, get_user_games
from chess_coach.stats import get_user_stats
from chess_coach.auth import (
    init_users_table, create_user, authenticate_user,
    create_access_token, decode_token, get_user_by_username,
    create_purpose_token, decode_purpose_token, password_fingerprint,
    get_user_by_email, mark_email_verified, set_password
)
from chess_coach.email_service import send_email, email_enabled
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


# --- Protect the heavy endpoints (Stockfish is slow and the server is small) ---
_HEAVY_SLOT = threading.Semaphore(1)   # one analysis at a time
_LAST_HEAVY = {}
HEAVY_COOLDOWN_SECONDS = 20


def heavy_job_guard(current_user: dict = Depends(get_current_user)):
    if email_enabled() and not current_user.get("email_verified", True):
        raise HTTPException(status_code=403,
                            detail="Please verify your email first. Check your inbox for the link.")
    now = time.time()
    uid = current_user["id"]
    wait = HEAVY_COOLDOWN_SECONDS - (now - _LAST_HEAVY.get(uid, 0))
    if wait > 0:
        raise HTTPException(status_code=429,
                            detail=f"Please wait {int(wait) + 1} seconds before starting another analysis.")
    if not _HEAVY_SLOT.acquire(blocking=False):
        raise HTTPException(status_code=429,
                            detail="The server is busy with another analysis. Please try again in a minute.")
    _LAST_HEAVY[uid] = now
    try:
        yield
    finally:
        _HEAVY_SLOT.release()


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    """For the uptime monitor: also touches the database so it stays awake."""
    from sqlalchemy import text as _t
    from chess_coach.database import get_connection
    conn = get_connection()
    try:
        conn.execute(_t("SELECT 1"))
    finally:
        conn.close()
    return {"status": "ok"}


@app.post("/auth/register")
def register(req: RegisterRequest, background: BackgroundTasks):
    if len(req.password) < 8 or len(req.password.encode()) > 72:
        raise HTTPException(status_code=400,
                            detail="Password must be between 8 and 72 characters")
    try:
        email = req.email.strip().lower()
        if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]{2,}", email):
            raise HTTPException(status_code=400, detail="Enter a valid email address")
        user = create_user(req.username, email, req.password)
        background.add_task(send_verification_email, user)
        token = create_access_token({"sub": user["username"]})
        user["email_verified"] = _verified(user)
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
            "is_premium": bool(user["is_premium"]),
            "email_verified": _verified(user)
        }
    }


# --- Email verification and password reset ---

FRONTEND_URL = _os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")
_LAST_MAIL = {}


class TokenRequest(BaseModel):
    token: str


class EmailRequest(BaseModel):
    email: str


class ResetRequest(BaseModel):
    token: str
    password: str


def _mail_throttled(key: str, seconds: int = 60) -> bool:
    now = time.time()
    if now - _LAST_MAIL.get(key, 0) < seconds:
        return True
    _LAST_MAIL[key] = now
    return False


def _verified(user: dict) -> bool:
    return bool(user.get("email_verified", True)) or not email_enabled()


def send_verification_email(user: dict):
    if not email_enabled():
        return
    token = create_purpose_token(user["username"], "verify", 60 * 24)
    link = f"{FRONTEND_URL}/verify?token={token}"
    name = _html.escape(user["username"])
    send_email(
        user["email"], "Verify your Chesslytic email",
        f"<p>Hi {name},</p><p>Confirm your email address to start analyzing games:</p>"
        f'<p><a href="{link}">Verify my email</a></p>'
        "<p>The link works for 24 hours. If you did not create an account, ignore this email.</p>",
    )


def send_reset_email(user: dict):
    if not email_enabled():
        return
    token = create_purpose_token(user["username"], "reset", 60,
                                 {"pwv": password_fingerprint(user["hashed_password"])})
    link = f"{FRONTEND_URL}/reset-password?token={token}"
    name = _html.escape(user["username"])
    send_email(
        user["email"], "Reset your Chesslytic password",
        f"<p>Hi {name},</p><p>Use this link to choose a new password:</p>"
        f'<p><a href="{link}">Reset my password</a></p>'
        "<p>The link works for one hour and only once. If you did not ask for this, ignore this email.</p>",
    )


@app.post("/auth/verify-email")
def verify_email(req: TokenRequest):
    payload = decode_purpose_token(req.token, "verify")
    if not payload:
        raise HTTPException(status_code=400, detail="This verification link is invalid or has expired.")
    mark_email_verified(payload["sub"])
    return {"verified": True}


@app.post("/auth/resend-verification")
def resend_verification(background: BackgroundTasks,
                        current_user: dict = Depends(get_current_user)):
    if _verified(current_user):
        return {"sent": False}
    if _mail_throttled(f"verify:{current_user['id']}"):
        raise HTTPException(status_code=429, detail="Please wait a minute before requesting another email.")
    background.add_task(send_verification_email, current_user)
    return {"sent": True}


@app.post("/auth/forgot-password")
def forgot_password(req: EmailRequest, background: BackgroundTasks):
    email = req.email.strip().lower()
    user = get_user_by_email(email)
    if user and not _mail_throttled(f"reset:{email}"):
        background.add_task(send_reset_email, user)
    return {"sent": True}  # same answer whether or not the account exists


@app.post("/auth/reset-password")
def reset_password(req: ResetRequest):
    payload = decode_purpose_token(req.token, "reset")
    user = get_user_by_username(payload["sub"]) if payload else None
    if not user or payload.get("pwv") != password_fingerprint(user["hashed_password"]):
        raise HTTPException(status_code=400, detail="This reset link is invalid, expired, or already used.")
    if len(req.password) < 8 or len(req.password.encode()) > 72:
        raise HTTPException(status_code=400, detail="Password must be between 8 and 72 characters")
    set_password(user["username"], req.password)
    mark_email_verified(user["username"])  # they proved they control this address
    return {"reset": True}


@app.get("/auth/me")
def me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "is_premium": bool(current_user["is_premium"]),
        "email_verified": _verified(current_user)
    }


@app.post("/analyze", dependencies=[Depends(heavy_job_guard)])
def analyze(req: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    if req.source not in ("chesscom", "lichess"):
        raise HTTPException(status_code=400,
                            detail="source must be 'chesscom' or 'lichess'")
    max_games = req.max_games
    if max_games < 1:
        max_games = 1
    if max_games > 20:
        max_games = 20
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


@app.post("/detect", dependencies=[Depends(heavy_job_guard)])
def detect_cheating(req: DetectRequest, current_user: dict = Depends(get_current_user)):
    """Run cheat detection on a player's recent games."""
    req.max_games = max(1, min(req.max_games, 10))
    try:
        import sys
        sys.path.insert(0, '/opt/render/project/src')

        from chess_detector.fetcher import get_chesscom_games
        from chess_detector.core.analyzer import analyze_pgn as detect_analyze_pgn
        from chess_detector.scorer import SuspicionScorer

        scorer = SuspicionScorer()
        reports = []

        if req.source == "chesscom":
            pgns = get_chesscom_games(req.chess_username, max_games=min(req.max_games * 4, 40))
        else:
            from chess_detector.fetcher import get_lichess_games
            pgns = get_lichess_games(req.chess_username, max_games=min(req.max_games * 4, 40))

        if not pgns:
            raise HTTPException(status_code=404, detail="No games found for this user")

        # bullet games are too short and premove-heavy to judge fairly
        import re as _re

        def _base_seconds(pgn):
            m = _re.search(r'\[TimeControl "(\d+)', pgn)
            return int(m.group(1)) if m else 0

        pgns = [g for g in pgns if _base_seconds(g) >= 180]
        if not pgns:
            raise HTTPException(status_code=404,
                                detail="No blitz or longer games found (bullet games are too short to judge)")

        last_error = None
        for pgn_text in pgns[:req.max_games * 2]:
            if len(reports) >= req.max_games:
                break
            try:
                analysis = detect_analyze_pgn(pgn_text, depth=12)
                if analysis is None:
                    continue
                color = ('white' if analysis.white_username.lower() == req.chess_username.lower()
                         else 'black' if analysis.black_username.lower() == req.chess_username.lower()
                         else None)
                if color is None:
                    continue  # username not found in this game
                report = scorer.score(
                    analysis,
                    req.chess_username,
                    color,
                    pgn_text=pgn_text
                )
                if report.features and report.features[0].name == "Sample size":
                    continue  # too few analyzable moves to judge this game
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
                last_error = str(e)
                continue

        if not reports:
            raise HTTPException(status_code=400, detail=(f"Analysis failed: {last_error[:200]}" if last_error else "Not enough analyzable moves to judge fairly (the games may be too short or decided early)"))

        avg_score = round(sum(r["overall_score"] for r in reports) / len(reports), 1)
        if avg_score < 30:
            overall_verdict = "clean"
        elif avg_score < 60:
            overall_verdict = "suspicious"
        else:
            overall_verdict = "likely cheating"

        if len(reports) < 3 and overall_verdict == "likely cheating":
            overall_verdict = "suspicious"  # too few games for the strongest verdict

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
