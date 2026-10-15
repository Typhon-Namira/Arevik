"""Opt-in text translation gateway; leaves legacy speech pipeline untouched."""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from threading import BoundedSemaphore

from app.ai.quality import QualityRouter, QualityResult
from app.config import settings

# One inference request at a time on a two-vCPU test host.
_GATE = BoundedSemaphore(value=1)

@lru_cache(maxsize=1)
def _router() -> QualityRouter:
    if settings.translation_engine != "ct2_quality":
        raise RuntimeError("CT2 quality translation is disabled")
    from app.ai.translation_backends import M2M100CT2, MadladCT2
    m2m = Path(settings.m2m100_model_dir)
    madlad = Path(settings.madlad_model_dir)
    if not (m2m / "model.bin").is_file() or not (madlad / "model.bin").is_file():
        raise RuntimeError("Configured CT2 model directories are unavailable")
    return QualityRouter(
        engines={"m2m100": M2M100CT2(m2m), "madlad": MadladCT2(madlad)},
        direct_engine="m2m100", fallback_engine="madlad"
    )

def translate_text(text: str, source: str, target: str) -> QualityResult:
    if settings.translation_engine != "ct2_quality":
        raise RuntimeError("CT2 quality translation is disabled")
    if not _GATE.acquire(blocking=False):
        raise RuntimeError("Translation server is busy")
    try:
        return _router().translate(text, source, target)
    finally:
        _GATE.release()
