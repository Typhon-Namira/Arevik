"""Persistent, revocable user sessions for Arevik.

SQLite is suitable for one EC2 instance / one application worker.
Registration must be explicitly enabled; use HTTPS before serving accounts.
"""
from __future__ import annotations
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from pathlib import Path
from threading import Lock
from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel, Field

DB_PATH = Path(os.environ.get("AREVIK_AUTH_DB", "/opt/arevik/data/auth.sqlite3"))
_LOCK = Lock()
SESSION_SECONDS = 60 * 60 * 24 * 7

def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.execute("PRAGMA busy_timeout=10000")
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, salt BLOB NOT NULL, password_hash BLOB NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
    db.commit()
    return db

def _password(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=32)

def _session(db, user_id: int) -> str:
    token = secrets.token_urlsafe(48)
    db.execute("INSERT INTO sessions(token_hash,user_id,expires) VALUES (?,?,?)",
               (hashlib.sha256(token.encode()).hexdigest(), user_id, int(time.time()) + SESSION_SECONDS))
    return token

class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)

def register(creds: Credentials) -> dict:
    if os.environ.get("AREVIK_ALLOW_REGISTRATION", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Registration disabled")
    email = creds.email.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=422, detail="Invalid email")
    salt = secrets.token_bytes(16)
    with _LOCK:
        with _db() as db:
            try:
                cursor = db.execute("INSERT INTO users(email,salt,password_hash) VALUES (?,?,?)",
                                    (email, salt, _password(creds.password, salt)))
                token = _session(db, cursor.lastrowid)
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=409, detail="Account already exists")
    return {"access_token": token, "token_type": "bearer", "expires_in": SESSION_SECONDS}

def login(creds: Credentials) -> dict:
    email = creds.email.strip().lower()
    with _LOCK:
        with _db() as db:
            row = db.execute("SELECT id,salt,password_hash FROM users WHERE email=?", (email,)).fetchone()
            salt = row[1] if row else b"\x00" * 16
            calculated = _password(creds.password, salt)
            if not row or not hmac.compare_digest(calculated, row[2]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            token = _session(db, row[0])
    return {"access_token": token, "token_type": "bearer", "expires_in": SESSION_SECONDS}

def require_user(authorization: str | None = Header(default=None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[7:]
    if len(token) > 512:
        raise HTTPException(status_code=401, detail="Invalid session")
    fingerprint = hashlib.sha256(token.encode()).hexdigest()
    with _db() as db:
        row = db.execute("SELECT user_id FROM sessions WHERE token_hash=? AND revoked=0 AND expires>?",
                         (fingerprint, int(time.time()))).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return int(row[0])

def revoke(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    with _db() as db:
        db.execute("UPDATE sessions SET revoked=1 WHERE token_hash=?",
                   (hashlib.sha256(authorization[7:].encode()).hexdigest(),))
