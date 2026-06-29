import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import text
from jose import JWTError, jwt
from passlib.context import CryptContext
from chess_coach.database import engine

SECRET_KEY = os.environ.get("JWT_SECRET", "change-this-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def init_users_table():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                is_premium INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()


def _truncate_password(password: str) -> str:
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate_password(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate_password(plain), hashed)


def create_user(username: str, email: str, password: str) -> dict:
    with engine.connect() as conn:
        try:
            result = conn.execute(text("""
                INSERT INTO users (username, email, hashed_password)
                VALUES (:username, :email, :hashed_password)
                RETURNING id
            """), {
                "username": username,
                "email": email,
                "hashed_password": hash_password(password)
            })
            user_id = result.fetchone()[0]
            conn.commit()
        except Exception as e:
            if "username" in str(e):
                raise ValueError("Username already taken")
            if "email" in str(e):
                raise ValueError("Email already registered")
            raise
    return {"id": user_id, "username": username,
            "email": email, "is_premium": False}


def get_user_by_username(username: str) -> Optional[dict]:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()
    if not row:
        return None
    return {
        "id": row[0], "username": row[1], "email": row[2],
        "hashed_password": row[3], "is_premium": row[4]
    }


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
