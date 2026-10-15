from fastapi import FastAPI
from app.api.auth import router as auth_router

from app.api.health import router as health_router
from app.api.translate import router as translate_router
from app.api.text_translate import router as text_router

app = FastAPI(
    title="Arevik Realtime Translation Engine",
    version="0.1.0",
    description="CPU-first English ↔ Armenian speech translation backend.",
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(translate_router)
app.include_router(text_router)


@app.get("/")
def root() -> dict:
    return {
        "service": "Arevik",
        "version": "0.1.0",
        "status": "online",
        "docs": "/docs",
    }
