from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path

from app.ai.stt import stt
from app.ai.translation import translator
from app.ai.tts import EspeakTTS


@dataclass
class StageTimings:
    stt_ms: int
    translation_ms: int
    tts_ms: int
    total_ms: int


@dataclass
class SpeechTranslationResult:
    source_language: str
    target_language: str
    source_text: str
    translated_text: str
    output_audio: str
    timings: StageTimings

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["timings"] = asdict(self.timings)
        return payload


class SpeechToSpeechPipeline:
    def __init__(self) -> None:
        self._tts: EspeakTTS | None = None

    @property
    def tts(self) -> EspeakTTS:
        if self._tts is None:
            self._tts = EspeakTTS()
        return self._tts

    def run(
        self,
        input_audio: str | Path,
        output_audio: str | Path,
        source_language: str,
        target_language: str,
    ) -> SpeechTranslationResult:
        if source_language == target_language:
            raise ValueError("Source and target languages must be different")
        if not translator.supported(source_language, target_language):
            raise ValueError(
                f"Unsupported language pair: {source_language}->{target_language}"
            )

        started = time.perf_counter()

        stage = time.perf_counter()
        source_text = stt.transcribe(input_audio, source_language)
        stt_ms = round((time.perf_counter() - stage) * 1000)
        if not source_text:
            raise ValueError("No speech was detected in the input audio")

        stage = time.perf_counter()
        translated_text = translator.translate(
            source_text,
            source_language,
            target_language,
        )
        translation_ms = round((time.perf_counter() - stage) * 1000)
        if not translated_text:
            raise RuntimeError("Translation returned empty text")

        stage = time.perf_counter()
        output_path = self.tts.synthesize(
            translated_text,
            target_language,
            output_audio,
        )
        tts_ms = round((time.perf_counter() - stage) * 1000)

        total_ms = round((time.perf_counter() - started) * 1000)

        return SpeechTranslationResult(
            source_language=source_language,
            target_language=target_language,
            source_text=source_text,
            translated_text=translated_text,
            output_audio=str(output_path),
            timings=StageTimings(
                stt_ms=stt_ms,
                translation_ms=translation_ms,
                tts_ms=tts_ms,
                total_ms=total_ms,
            ),
        )


pipeline = SpeechToSpeechPipeline()
