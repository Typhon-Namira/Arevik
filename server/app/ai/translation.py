from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import torch
from transformers import MarianMTModel, MarianTokenizer

from app.config import settings


@dataclass(frozen=True)
class TranslationPair:
    source: str
    target: str
    model_id: str


class LocalTranslator:
    def __init__(self) -> None:
        self._pairs = {
            ("en", "hy"): TranslationPair("en", "hy", settings.translation_en_hy),
            ("hy", "en"): TranslationPair("hy", "en", settings.translation_hy_en),
        }

    def supported(self, source: str, target: str) -> bool:
        return (source, target) in self._pairs

    @lru_cache(maxsize=4)
    def _load(self, model_id: str) -> tuple[MarianTokenizer, MarianMTModel]:
        tokenizer = MarianTokenizer.from_pretrained(model_id)
        model = MarianMTModel.from_pretrained(model_id)
        model.eval()
        return tokenizer, model

    def translate(self, text: str, source: str, target: str) -> str:
        clean = text.strip()
        if not clean:
            return ""

        pair = self._pairs.get((source, target))
        if pair is None:
            raise ValueError(f"Unsupported translation pair: {source}->{target}")

        tokenizer, model = self._load(pair.model_id)
        batch = tokenizer(
            [clean],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )

        with torch.inference_mode():
            generated = model.generate(
                **batch,
                max_new_tokens=256,
                num_beams=2,
                do_sample=False,
            )

        result = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
        return result.strip()


translator = LocalTranslator()
