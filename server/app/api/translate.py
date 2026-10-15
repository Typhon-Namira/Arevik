from __future__ import annotations

import base64
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.ai.pipeline import pipeline
from app.config import settings

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024

router = APIRouter(prefix="/api/v1/translate", tags=["Translation"])


@router.post("/file")
async def translate_file(
    file: UploadFile = File(...),
    source_language: str = Form(...),
    target_language: str = Form(...),
) -> dict:
    if source_language not in {"en", "hy"} or target_language not in {"en", "hy"}:
        raise HTTPException(status_code=400, detail="V1 supports only en and hy")
    if source_language == target_language:
        raise HTTPException(status_code=400, detail="Source and target must differ")

    request_id = uuid.uuid4().hex
    suffix = Path(file.filename or "input.wav").suffix or ".wav"
    request_dir = settings.temp_dir / request_id
    request_dir.mkdir(parents=True, exist_ok=True)
    input_path = request_dir / f"input{suffix}"
    output_path = request_dir / "translated.wav"

    try:
        received = 0
        with input_path.open("wb") as destination:
            while chunk := await file.read(UPLOAD_CHUNK_BYTES):
                received += len(chunk)
                if received > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="Audio file exceeds 15 MiB limit")
                destination.write(chunk)
        if received == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        result = await run_in_threadpool(
            pipeline.run,
            input_path,
            output_path,
            source_language,
            target_language,
        )
        audio_b64 = base64.b64encode(output_path.read_bytes()).decode("ascii")

        return {
            "request_id": request_id,
            **result.to_dict(),
            "audio": {
                "encoding": "base64",
                "content_type": "audio/wav",
                "data": audio_b64,
            },
        }
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()
        shutil.rmtree(request_dir, ignore_errors=True)
