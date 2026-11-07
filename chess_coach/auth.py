import os
import hashlib
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                email_verified INTEGER DEFAULT 0
            )
        """))
        conn.commit()

        # Existing databases: add the column once; accounts that already exist count as verified
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0"))
            conn.execute(text("UPDATE users SET email_verified = 1"))
            conn.commit()
        except Exception:
            conn.rollback()


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
            "email": email, "is_premium": False, "email_verified": False}


def get_user_by_username(username: str) -> Optional[dict]:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()
    if not row:
        return None
    m = row._mapping
    return {
        "id": row[0], "username": row[1], "email": row[2],
        "hashed_password": row[3], "is_premium": row[4],
        "email_verified": bool(m.get("email_verified", 1)),
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


def _purpose_key(purpose: str) -> str:
    # A separate signing key per purpose, so emailed links can never work as login tokens
    return f"{SECRET_KEY}:{purpose}"


def password_fingerprint(hashed_password: str) -> str:
    return hashlib.sha256(hashed_password.encode()).hexdigest()[:16]


def create_purpose_token(username: str, purpose: str, minutes: int,
                         extra: Optional[dict] = None) -> str:
    data = {"sub": username, "purpose": purpose,
            "exp": datetime.utcnow() + timedelta(minutes=minutes)}
    if extra:
        data.update(extra)
    return jwt.encode(data, _purpose_key(purpose), algorithm=ALGORITHM)


def decode_purpose_token(token: str, purpose: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, _purpose_key(purpose), algorithms=[ALGORITHM])
    except JWTError:
        return None
    return payload if payload.get("purpose") == purpose else None


def get_user_by_email(email: str) -> Optional[dict]:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE lower(email) = lower(:e)"),
            {"e": email}
        ).fetchone()
    if not row:
        return None
    m = row._mapping
    return {
        "id": m["id"], "username": m["username"], "email": m["email"],
        "hashed_password": m["hashed_password"], "is_premium": m["is_premium"],
        "email_verified": bool(m.get("email_verified", 1)),
    }


def mark_email_verified(username: str) -> None:
    with engine.connect() as conn:
        conn.execute(text("UPDATE users SET email_verified = 1 WHERE username = :u"),
                     {"u": username})
        conn.commit()


def set_password(username: str, new_password: str) -> None:
    with engine.connect() as conn:
        conn.execute(text("UPDATE users SET hashed_password = :h WHERE username = :u"),
                     {"h": hash_password(new_password), "u": username})
        conn.commit()
