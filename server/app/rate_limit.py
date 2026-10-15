"""Single-instance persistent rate limiter for authentication and inference.

Uses SQLite atomic counters; for horizontally scaled deployment use a shared
rate-limit service. Client IP is taken from socket peer, never X-Forwarded-For.
"""
import sqlite3
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from app.auth import _db

LIMITS = {
    "/api/v1/auth/login": (8, 300),
    "/api/v1/auth/register": (3, 3600),
    "/api/v1/translate/file": (12, 60),
    "/api/v1/translate/text": (30, 60),
}

async def rate_limit(request: Request, call_next):
    path = request.url.path
    limit = LIMITS.get(path)
    if request.method != "POST" or not limit:
        return await call_next(request)
    # At the reverse proxy all peers may share an internal address. This
    # conservative global bucket protects server capacity, not per-user fairness.
    count, window = limit
    bucket = int(time.time()) // window
    key = f"{path}:{bucket}"
    with _db() as db:
        db.execute("CREATE TABLE IF NOT EXISTS rate_counters (bucket TEXT PRIMARY KEY, requests INTEGER NOT NULL)")
        db.execute("INSERT INTO rate_counters(bucket,requests) VALUES (?,1) ON CONFLICT(bucket) DO UPDATE SET requests=requests+1", (key,))
        current = db.execute("SELECT requests FROM rate_counters WHERE bucket=?", (key,)).fetchone()[0]
        if current > count:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(window)})
    return await call_next(request)
