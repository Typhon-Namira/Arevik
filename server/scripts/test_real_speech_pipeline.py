"""Actual CPU speech-to-speech integration smoke test.

Runs real Whisper STT, CT2 M2M100/MADLAD router and TTS; no mocks.
Outputs WAV and a JSON report, leaving the live API unchanged.
"""
import json
import subprocess
import time
from pathlib import Path

from app.ai.pipeline import pipeline
from app.config import settings

OUT = Path("/results")
CASES = [
    ("en", "hy", "Hello. I live in Yerevan.", "en-us"),
    ("hy", "en", "Ես ապրում եմ Երևանում։", "hy"),
    ("fa", "hy", "من در ایروان زندگی می‌کنم.", "fa"),
    ("hy", "fa", "Ես ապրում եմ Երևանում։", "hy"),
    ("en", "fa", "I need two tickets.", "en-us"),
    ("fa", "en", "من دو بلیت می‌خواهم.", "fa"),
]

def main():
    if settings.translation_engine != "ct2_quality":
        raise RuntimeError("Enable AREVIK_TRANSLATION_ENGINE=ct2_quality")
    OUT.mkdir(parents=True, exist_ok=True)
    reports = []
    for index, (source, target, phrase, voice) in enumerate(CASES, 1):
        audio = OUT / f"input_{index}_{source}.wav"
        output = OUT / f"output_{index}_{target}.wav"
        subprocess.run(["espeak-ng", "-v", voice, "-s", "140", "-w", str(audio), phrase], check=True)
        print(f"Case {index}: {source}->{target}", flush=True)
        try:
            t0 = time.perf_counter()
            result = pipeline.run(audio, output, source, target)
            report = result.to_dict()
            report["elapsed_wall_seconds"] = round(time.perf_counter() - t0, 2)
            report["expected_source"] = phrase
            report["audio_bytes"] = output.stat().st_size
            if report["audio_bytes"] <= 44:
                raise RuntimeError("Empty WAV output")
            reports.append({"case": index, "ok": True, **report})
            print(json.dumps(reports[-1], ensure_ascii=False), flush=True)
        except Exception as exc:
            reports.append({"case": index, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
            print(json.dumps(reports[-1], ensure_ascii=False), flush=True)
            break
        finally:
            (OUT / "report.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2))
    if len(reports) != len(CASES) or not all(item["ok"] for item in reports):
        raise SystemExit("End-to-end benchmark FAILED; do not deploy")
    print("All six speech directions produced audio. Human quality review remains pending.", flush=True)

if __name__ == "__main__":
    main()
