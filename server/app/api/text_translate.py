"""Local-only experimental text translation endpoint (disabled by default).

Do not expose without authentication and transport protection.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.auth import require_user
from pydantic import BaseModel, Field
from app.ai.quality_gateway import translate_text
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["Experimental translation"])

class TextTranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    source_language: str
    target_language: str

@router.post("/translate/text")
def translate_text_endpoint(payload: TextTranslationRequest, user_id: int = Depends(require_user)):
    if settings.translation_engine != "ct2_quality":
        raise HTTPException(status_code=404, detail="Experimental translation disabled")
    if payload.source_language not in {"en", "hy", "fa"} or payload.target_language not in {"en", "hy", "fa"} or payload.source_language == payload.target_language:
        raise HTTPException(status_code=400, detail="Unsupported language pair")
    try:
        result = translate_text(payload.text, payload.source_language, payload.target_language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        if str(exc) == "Translation server is busy":
            raise HTTPException(status_code=503, detail="Translation capacity temporarily unavailable") from exc
        raise HTTPException(status_code=503, detail="Translation engine unavailable") from exc
    return {
        "translated_text": result.text,
        "engine": result.model,
        "route": result.route,
        "needs_review": result.needs_review,
        "warnings": result.warnings,
        "repairs": result.repairs,
    }
