"""Standalone Eastern Armenian SpeechT5 CPU benchmark; not part of the live API.

Usage: python scripts/benchmark_armenian_tts.py --output-dir /tmp/arevik-tts-out
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import time
from pathlib import Path

MODEL_ID = "ArthurYeghinyan/armenian-speecht5-sota"
VOCODER_ID = "microsoft/speecht5_hifigan"
SAMPLES = (
    "Բարև ձեզ։ Ինչպե՞ս եք այսօր։",
    "Ես ապրում եմ Երևանում։",
    "Ներեցեք, որտե՞ղ է ավտոբուսի կանգառը։",
)

def run(output_dir: Path) -> None:
    import numpy as np
    import soundfile as sf
    import torch
    from huggingface_hub import hf_hub_download
    from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan

    torch.set_num_threads(2)
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    print("Loading processor/model/vocoder on CPU...", flush=True)
    processor = SpeechT5Processor.from_pretrained(MODEL_ID)
    model = SpeechT5ForTextToSpeech.from_pretrained(MODEL_ID).to("cpu").eval()
    vocoder = SpeechT5HifiGan.from_pretrained(VOCODER_ID).to("cpu").eval()
    speaker_file = hf_hub_download(MODEL_ID, "golden_speaker_embedding.pt")
    speaker = torch.load(speaker_file, map_location="cpu", weights_only=True)
    if speaker.ndim == 1:
        speaker = speaker.unsqueeze(0)
    if speaker.ndim != 2 or speaker.shape[1] != 512:
        raise ValueError(f"Unexpected speaker embedding shape: {tuple(speaker.shape)}")
    load_seconds = round(time.perf_counter() - started, 3)
    print(f"Loaded in {load_seconds}s", flush=True)

    records = []
    for i, text in enumerate(SAMPLES, 1):
        inputs = processor(text=text, return_tensors="pt")
        t0 = time.perf_counter()
        with torch.inference_mode():
            speech = model.generate_speech(inputs["input_ids"], speaker, vocoder=vocoder)
        inference_seconds = round(time.perf_counter() - t0, 3)
        samples = speech.detach().cpu().numpy().astype(np.float32)
        target = output_dir / f"armenian_{i:02d}.wav"
        sf.write(str(target), samples, samplerate=16000)
        duration = round(len(samples) / 16000, 3)
        result = {"text": text, "wav": str(target), "inference_s": inference_seconds,
                  "audio_s": duration,
                  "rtf": round(inference_seconds / duration, 3) if duration else None}
        records.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)

    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    summary = {"model": MODEL_ID, "load_s": load_seconds, "peak_rss_kib_linux": peak_rss, "samples": records}
    (output_dir / "benchmark.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print("Benchmark complete; listen to WAV files before selecting for MVP.", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="/tmp/arevik-tts-out")
    args = parser.parse_args()
    run(Path(args.output_dir))
