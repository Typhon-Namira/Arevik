"""CPU Armenian SpeechT5 with English/Persian eSpeak voices.

Production inference uses a persistent HF cache and a single worker.
"""
from __future__ import annotations
from functools import cached_property
from pathlib import Path
import shutil
import subprocess
from app.config import settings

class MultilingualTTS:
    @cached_property
    def armenian(self):
        import torch
        from huggingface_hub import hf_hub_download
        from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
        name = "ArthurYeghinyan/armenian-speecht5-sota"
        torch.set_num_threads(2)
        processor = SpeechT5Processor.from_pretrained(name)
        model = SpeechT5ForTextToSpeech.from_pretrained(name).eval()
        vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").eval()
        speaker = torch.load(hf_hub_download(name, "golden_speaker_embedding.pt"), map_location="cpu", weights_only=True)
        if speaker.ndim == 1:
            speaker = speaker.unsqueeze(0)
        if speaker.ndim != 2 or speaker.shape[1] != 512:
            raise RuntimeError("Unexpected Armenian speaker embedding")
        return processor, model, vocoder, speaker

    def synthesize(self, text: str, language: str, output_path: str | Path) -> Path:
        if not text.strip():
            raise ValueError("Empty TTS text")
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if language == "hy":
            import torch
            import numpy as np
            import soundfile as sf
            processor, model, vocoder, speaker = self.armenian
            inputs = processor(text=text, return_tensors="pt")
            with torch.inference_mode():
                audio = model.generate_speech(inputs["input_ids"], speaker, vocoder=vocoder)
            sf.write(str(path), audio.detach().cpu().numpy().astype(np.float32), samplerate=16000)
        elif language in {"en", "fa"}:
            voice = {"en": "en-us", "fa": "fa"}[language]
            binary = shutil.which("espeak-ng")
            if not binary:
                raise RuntimeError("eSpeak NG is missing")
            subprocess.run([binary, "-v", voice, "-s", str(settings.tts_rate), "-w", str(path), text],
                           check=True, capture_output=True)
        else:
            raise ValueError("Unsupported TTS language")
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError("TTS generated no audio")
        return path
