# Eastern Armenian SpeechT5 CPU evaluation

Candidate: [ArthurYeghinyan/armenian-speecht5-sota](https://huggingface.co/ArthurYeghinyan/armenian-speecht5-sota) (model card reports Apache-2.0). Vocoder: microsoft/speecht5_hifigan. Inspect upstream licenses and dependencies before commercial release.

This is an **offline evaluation**, not a change to the live TTS engine.
Requires CPU resources and model downloads. Benchmarks first load plus three short phrases;
judge intelligibility and pronunciation with an Eastern Armenian native speaker.
The author's reported Whisper-based CER/WER does **not** establish human-grade accuracy.

Run in a disposable Docker container with persistent HF cache and output directory.
The model card documents a 16 kHz output sample rate.

```sh
cd ~/projects/Arevik
mkdir -p tts-evaluation
sudo docker run --rm \
  --mount type=bind,source="$PWD/server",target=/app,readonly \
  --mount type=bind,source="$PWD/tts-evaluation",target=/results \
  --mount type=volume,source=arevik_arevik-models,target=/opt/arevik/cache/huggingface \
  -e HF_HOME=/opt/arevik/cache/huggingface \
  -e OMP_NUM_THREADS=2 \
  --cpus=2 --memory=5g --memory-swap=5g \
  -w /app --entrypoint sh arevik-arevik-api \
  -c 'python -m pip install -q soundfile && python -u scripts/benchmark_armenian_tts.py --output-dir /results'
```

If the command fails, stop and inspect the error rather than changing container resources blindly.
Listen to the three WAV outputs, check `benchmark.json`, and record cold-start
and real-time factor. Do not place the test results into the API until validated.

The active `arevik-api` container and `main` branch remain unchanged.
