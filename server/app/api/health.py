from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "arevik-server",
        "mode": "cpu-local",
        "languages": ["en", "hy", "fa"],
        "stt": {
            "provider": "faster-whisper",
            "model": settings.stt_model,
            "compute_type": settings.stt_compute_type,
        },
        "translation": {
            "provider": "m2m100-madlad-ct2-quality",
            "pairs": ["en->hy", "hy->en", "en->fa", "fa->en", "hy->fa", "fa->hy"],
        },
        "tts": {
            "provider": "speecht5-hy/espeak-en-fa",
            "quality": "experimental-voice-not-reviewed",
        },
    }
