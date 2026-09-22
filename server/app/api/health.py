from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "arevik-server",
        "mode": "cpu-local",
        "languages": ["en", "hy"],
        "stt": {
            "provider": "faster-whisper",
            "model": settings.stt_model,
            "compute_type": settings.stt_compute_type,
        },
        "translation": {
            "provider": "local-opus-mt",
            "pairs": ["en->hy", "hy->en"],
        },
        "tts": {
            "provider": settings.tts_engine,
            "quality": "baseline",
        },
    }
