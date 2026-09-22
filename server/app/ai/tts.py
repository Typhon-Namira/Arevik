from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.config import settings


VOICE_MAP = {
    "en": "en-us",
    "hy": "hy",
}


class EspeakTTS:
    """Zero-API baseline TTS.

    This intentionally prioritizes a complete local pipeline over final voice
    quality. The adapter will later be replaced/augmented by a higher-quality
    Armenian local model without changing callers.
    """

    def __init__(self) -> None:
        binary = shutil.which("espeak-ng")
        if not binary:
            raise RuntimeError(
                "espeak-ng is not installed. On Ubuntu: "
                "sudo apt-get install -y espeak-ng"
            )
        self.binary = binary

    def synthesize(self, text: str, language: str, output_path: str | Path) -> Path:
        clean = text.strip()
        if not clean:
            raise ValueError("Cannot synthesize empty text")

        voice = VOICE_MAP.get(language)
        if not voice:
            raise ValueError(f"Unsupported TTS language: {language}")

        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            [
                self.binary,
                "-v",
                voice,
                "-s",
                str(settings.tts_rate),
                "-w",
                str(destination),
                clean,
            ],
            check=True,
            capture_output=True,
        )

        if not destination.exists() or destination.stat().st_size == 0:
            raise RuntimeError("TTS did not produce an audio file")

        return destination
