from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AREVIK_",
        case_sensitive=False,
        extra="ignore",
    )

    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000

    stt_model: str = "small"
    stt_compute_type: str = "int8"
    stt_cpu_threads: int = 4

    translation_en_hy: str = "Helsinki-NLP/opus-mt-en-hy"
    translation_hy_en: str = "Helsinki-NLP/opus-mt-hy-en"
    translation_engine: str = "ct2_quality"
    m2m100_model_dir: str = "/opt/arevik/cache/huggingface/converted/m2m100-418m-int8"
    madlad_model_dir: str = ""

    tts_engine: str = "espeak"
    tts_rate: int = 165

    temp_dir: Path = Path("/tmp/arevik")


settings = Settings()
settings.temp_dir.mkdir(parents=True, exist_ok=True)
