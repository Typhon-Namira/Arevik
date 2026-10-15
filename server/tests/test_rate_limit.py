from fastapi.testclient import TestClient
from app.main import app
from app import auth
from app.rate_limit import LIMITS

def test_login_throttling(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DB_PATH", tmp_path / "auth.sqlite3")
    app.dependency_overrides.clear()
    client = TestClient(app)
    for i in range(LIMITS["/api/v1/auth/login"][0]):
        res = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.org", "password": "not a valid password"
        })
        assert res.status_code == 401
    blocked = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.org", "password": "not a valid password"
    })
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
