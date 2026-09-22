# Arevik

Arevik is a real-time, two-person AI interpreter. Each participant uses their own phone and headset, speaks naturally in their own language, and hears the other person translated into their language.

## V1 scope

The first production path is intentionally narrow:

- English ↔ Armenian
- two users per conversation
- one phone + one headset per user
- local/self-hosted AI inference on an AWS CPU server wherever practical
- mobile apps for iOS and Android
- a separate marketing website
- no accounts, payments, history, dashboard, or social features in the first technical prototype

## Repository layout

```text
Arevik/
├── apps/
│   ├── mobile/          # Flutter app (next phase)
│   └── web/             # Marketing website (next phase)
├── server/              # Python/FastAPI + local AI
├── infra/               # Docker / AWS deployment assets
└── docs/                # Architecture and engineering decisions
```

## Phase 1: local speech-to-speech pipeline

The first milestone is a CPU-only file pipeline:

```text
input.wav
  → faster-whisper (local STT)
  → OPUS-MT (local EN↔HY translation)
  → eSpeak NG (local baseline TTS)
  → translated.wav
```

The TTS adapter is deliberately replaceable. eSpeak NG is used only to prove the complete no-API pipeline; higher-quality Armenian TTS will be benchmarked behind the same interface.

### Run locally

Requirements:

- Python 3.11+
- `espeak-ng`
- `ffmpeg` recommended

On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y espeak-ng ffmpeg libsndfile1
cd server
python -m venv .venv
source .venv/bin/activate

# CPU-only PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[dev]"
```

Run the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Check health:

```bash
curl http://localhost:8000/health
```

Run an English → Armenian file test:

```bash
python scripts/translate_wav.py ./samples/english.wav ./out/armenian.wav --source en --target hy
```

Run Armenian → English:

```bash
python scripts/translate_wav.py ./samples/armenian.wav ./out/english.wav --source hy --target en
```

The first run downloads the selected open model weights from Hugging Face and caches them on the server. Inference itself is local and does not require a paid inference API.

## Design rule

The core translation engine must stay provider-agnostic. STT, translation, and TTS are separate adapters so that we can benchmark or replace one layer without rewriting the mobile app or realtime session layer.
