from __future__ import annotations

import io
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.api import translate as module

client = TestClient(app)

def test_rejects_oversize_file_and_cleans_temp(tmp_path, monkeypatch):
    monkeypatch.setattr(module.settings, "temp_dir", tmp_path)
    response = client.post("/api/v1/translate/file", data={"source_language": "en", "target_language": "hy"}, files={"file": ("sample.wav", io.BytesIO(b"x" * (module.MAX_UPLOAD_BYTES + 1)), "audio/wav")})
    assert response.status_code == 413
    assert not list(tmp_path.iterdir())

def test_rejects_empty_audio_and_cleans_temp(tmp_path, monkeypatch):
    monkeypatch.setattr(module.settings, "temp_dir", tmp_path)
    response = client.post("/api/v1/translate/file", data={"source_language": "en", "target_language": "hy"}, files={"file": ("sample.wav", io.BytesIO(b""), "audio/wav")})
    assert response.status_code == 400
    assert not list(tmp_path.iterdir())

def test_success_removes_audio_files(tmp_path, monkeypatch):
    monkeypatch.setattr(module.settings, "temp_dir", tmp_path)
    def mock_pipeline(input_path, output_path, source_language, target_language):
        assert Path(input_path).exists()
        Path(output_path).write_bytes(b"RIFFfake")
        class FakeResult:
            def to_dict(self):
                return {"source_language": source_language, "target_language": target_language, "source_text": "hello", "translated_text": "barev"}
        return FakeResult()
    monkeypatch.setattr(module.pipeline, "run", mock_pipeline)
    response = client.post("/api/v1/translate/file", data={"source_language": "en", "target_language": "hy"}, files={"file": ("sample.wav", io.BytesIO(b"RIFFfake"), "audio/wav")})
    assert response.status_code == 200, response.text
    assert not list(tmp_path.iterdir())
