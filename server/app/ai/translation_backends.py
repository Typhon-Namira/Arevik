"""Lazy CTranslate2 adapters for the two already benchmarked engines.

Models are loaded only when selected. Not wired into the production API by default.
"""
from __future__ import annotations
from functools import cached_property
from pathlib import Path

import ctranslate2
from transformers import M2M100Tokenizer, T5Tokenizer

class M2M100CT2:
    def __init__(self, path: str | Path, threads: int = 2) -> None:
        self.path, self.threads = str(path), threads

    @cached_property
    def resources(self):
        tokenizer = M2M100Tokenizer.from_pretrained(self.path, local_files_only=True)
        model = ctranslate2.Translator(self.path, device="cpu", compute_type="int8", inter_threads=1, intra_threads=self.threads)
        return tokenizer, model

    def __call__(self, text: str, source: str, target: str) -> str:
        tokenizer, model = self.resources
        tokenizer.src_lang = source
        tokens = tokenizer.convert_ids_to_tokens(tokenizer(text).input_ids)
        result = model.translate_batch([tokens], target_prefix=[[tokenizer.lang_code_to_token[target]]], beam_size=2, max_decoding_length=128)
        output = result[0].hypotheses[0]
        return tokenizer.decode(tokenizer.convert_tokens_to_ids(output), skip_special_tokens=True).strip()

class MadladCT2:
    def __init__(self, path: str | Path, threads: int = 2) -> None:
        self.path, self.threads = str(path), threads

    @cached_property
    def resources(self):
        tokenizer = T5Tokenizer.from_pretrained(self.path, local_files_only=True)
        model = ctranslate2.Translator(self.path, device="cpu", compute_type="int8", inter_threads=1, intra_threads=self.threads)
        return tokenizer, model

    def __call__(self, text: str, source: str, target: str) -> str:
        tokenizer, model = self.resources
        tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(f"<2{target}> " + text))
        result = model.translate_batch([tokens], beam_size=2, max_decoding_length=128)
        return tokenizer.decode(tokenizer.convert_tokens_to_ids(result[0].hypotheses[0]), skip_special_tokens=True).strip()
