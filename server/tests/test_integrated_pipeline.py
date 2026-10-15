from pathlib import Path
from app.ai import pipeline as module

def test_pipeline_uses_quality_router_and_new_tts(tmp_path, monkeypatch):
    class STT:
        def transcribe(self, path, language):
            return "I live in Yerevan."
    class Quality:
        text = "Ես ապրում եմ Երևանում։"
    class TTS:
        def synthesize(self, text, language, output):
            assert text == Quality.text
            assert language == "hy"
            Path(output).write_bytes(b"RIFF")
            return Path(output)
    monkeypatch.setattr(module, "stt", STT())
    monkeypatch.setattr(module, "translate_text", lambda text, src, dst: Quality())
    worker = module.SpeechToSpeechPipeline()
    worker._tts = TTS()
    result = worker.run(tmp_path / "input.wav", tmp_path / "out.wav", "en", "hy")
    assert result.translated_text == Quality.text
    assert result.output_audio.endswith("out.wav")

def test_pipeline_supports_persian_direction(tmp_path, monkeypatch):
    class STT:
        def transcribe(self, path, language):
            return "من فارسی یاد می‌گیرم."
    class Quality:
        text = "I am learning Persian."
    class TTS:
        def synthesize(self, text, language, output):
            assert language == "en"
            Path(output).write_bytes(b"RIFF")
            return Path(output)
    monkeypatch.setattr(module, "stt", STT())
    monkeypatch.setattr(module, "translate_text", lambda text, src, dst: Quality())
    worker = module.SpeechToSpeechPipeline()
    worker._tts = TTS()
    result = worker.run(tmp_path / "input.wav", tmp_path / "out.wav", "fa", "en")
    assert result.translated_text == Quality.text
