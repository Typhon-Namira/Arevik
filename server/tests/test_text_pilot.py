from fastapi.testclient import TestClient
from app.main import app
from app.auth import require_user
app.dependency_overrides[require_user] = lambda: 1
from app.config import settings

client = TestClient(app)

def test_pilot_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "translation_engine", "opus")
    response = client.post("/api/v1/translate/text", json={
        "text": "Hello", "source_language": "en", "target_language": "hy"
    })
    assert response.status_code == 404

def test_invalid_pair_rejected_before_model_load(monkeypatch):
    monkeypatch.setattr(settings, "translation_engine", "ct2_quality")
    response = client.post("/api/v1/translate/text", json={
        "text": "Hello", "source_language": "en", "target_language": "en"
    })
    assert response.status_code == 400

def test_text_size_limit(monkeypatch):
    monkeypatch.setattr(settings, "translation_engine", "ct2_quality")
    response = client.post("/api/v1/translate/text", json={
        "text": "x" * 2001, "source_language": "en", "target_language": "hy"
    })
    assert response.status_code == 422
