import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import auth
from app.auth import require_user

@pytest.fixture
def auth_client(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "DB_PATH", tmp_path / "auth.sqlite3")
    monkeypatch.setenv("AREVIK_ALLOW_REGISTRATION", "true")
    app.dependency_overrides.pop(require_user, None)
    yield TestClient(app)
    app.dependency_overrides[require_user] = lambda: 1

def test_register_login_me_logout(auth_client):
    credentials = {"email": "hello@example.com", "password": "correct horse battery staple"}
    res = auth_client.post("/api/v1/auth/register", json=credentials)
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert auth_client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert auth_client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert auth_client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert auth_client.post("/api/v1/auth/login", json=credentials).status_code == 200

def test_auth_inference_requires_user(auth_client):
    res = auth_client.post("/api/v1/translate/file")
    assert res.status_code == 401

def test_duplicate_registration_and_invalid_password(auth_client):
    c = {"email": "hello@example.com", "password": "correct horse battery staple"}
    assert auth_client.post("/api/v1/auth/register", json=c).status_code == 200
    assert auth_client.post("/api/v1/auth/register", json=c).status_code == 409
    c["password"] = "incorrect passphrase"
    assert auth_client.post("/api/v1/auth/login", json=c).status_code == 401

def test_registration_disabled(auth_client, monkeypatch):
    monkeypatch.setenv("AREVIK_ALLOW_REGISTRATION", "false")
    res = auth_client.post("/api/v1/auth/register",
        json={"email":"x@example.com", "password":"correct horse battery staple"})
    assert res.status_code == 403
