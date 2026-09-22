from __future__ import annotations

from functools import cached_property
from pathlib import Path

from faster_whisper import WhisperModel

from app.config import settings


class LocalWhisperSTT:
    """CPU-only Whisper adapter.

    The model is loaded lazily so health checks and imports stay cheap.
    """

    @cached_property
    def model(self) -> WhisperModel:
        return WhisperModel(
            settings.stt_model,
            device="cpu",
            compute_type=settings.stt_compute_type,
            cpu_threads=settings.stt_cpu_threads,
        )

    def transcribe(self, audio_path: str | Path, language: str) -> str:
        if language not in {"en", "hy"}:
            raise ValueError(f"Unsupported STT language: {language}")

        segments, _ = self.model.transcribe(
            str(audio_path),
            language=language,
            beam_size=1,
            best_of=1,
            vad_filter=True,
            condition_on_previous_text=False,
            word_timestamps=False,
        )
        text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
        return text.strip()


stt = LocalWhisperSTT()
