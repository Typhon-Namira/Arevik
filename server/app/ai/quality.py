"""Conservative, model-independent translation quality controls.

These checks detect some failures; they cannot establish semantic correctness.
No automatic rewriting of proper nouns or factual content is performed.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable

LANGUAGES = frozenset({"en", "hy", "fa"})
# This is deliberately small and curated. Expand only with human-reviewed entries.
GLOSSARY: dict[str, dict[str, str]] = {
    "yerevan": {"en": "Yerevan", "hy": "Երևան", "fa": "ایروان"},
    "armenia": {"en": "Armenia", "hy": "Հայաստան", "fa": "ارمنستان"},
    "armenian language": {"en": "Armenian language", "hy": "հայերեն", "fa": "زبان ارمنی"},
    "persian language": {"en": "Persian language", "hy": "պարսկերեն", "fa": "زبان فارسی"},
    "english language": {"en": "English language", "hy": "անգլերեն", "fa": "زبان انگلیسی"},
}
# Inflected locations are not blindly compared with exact stem matching.
SOURCE_ALIASES: dict[str, dict[str, tuple[str, ...]]] = {
    "yerevan": {"en": ("Yerevan",), "hy": ("Երևան", "Երևանում", "Երեւան", "Երեւանում"), "fa": ("ایروان",)},
    "armenia": {"en": ("Armenia",), "hy": ("Հայաստան", "Հայաստանում"), "fa": ("ارمنستان",)},
    "armenian language": {"en": ("Armenian language", "speak Armenian", "learning Armenian", "learn Armenian"), "hy": ("հայերեն",), "fa": ("زبان ارمنی",)},
    "persian language": {"en": ("Persian language", "speak Persian", "learning Persian"), "hy": ("պարսկերեն",), "fa": ("زبان فارسی",)},
    "english language": {"en": ("English language", "speak English", "learning English"), "hy": ("անգլերեն",), "fa": ("زبان انگلیسی",)},
}
TARGET_ALIASES: dict[str, dict[str, tuple[str, ...]]] = {
    "yerevan": {"en": ("Yerevan",), "hy": ("Երևան", "Երեւան", "Երեվան"), "fa": ("ایروان", "یروان")},
    "armenia": {"en": ("Armenia",), "hy": ("Հայաստան",), "fa": ("ارمنستان",)},
    "armenian language": {"en": ("Armenian",), "hy": ("հայերեն",), "fa": ("ارمنی",)},
    "persian language": {"en": ("Persian",), "hy": ("պարսկերեն",), "fa": ("فارسی",)},
    "english language": {"en": ("English",), "hy": ("անգլերեն",), "fa": ("انگلیسی",)},
}

def normalize(text: str, language: str) -> str:
    if language not in LANGUAGES:
        raise ValueError("Unsupported language")
    result = unicodedata.normalize("NFC", text).strip()
    result = re.sub(r"[ \t]+", " ", result)
    if language == "fa":
        result = result.replace("\u064a", "\u06cc").replace("\u0643", "\u06a9")
    if language == "hy":
        # Only unambiguous spellings, not blanket language/dialect conversion.
        result = result.replace("Երեւան", "Երևան").replace("Բարեւ", "Բարև")
    return result

def _has(text: str, alias: str, language: str) -> bool:
    # Word boundaries only for Latin; Unicode strings can have inflectional suffixes.
    if language == "en":
        return re.search(r"(?<![a-z])" + re.escape(alias.casefold()) + r"(?![a-z])", text.casefold()) is not None
    return alias.casefold() in text.casefold()

def required_entities(source: str, source_lang: str) -> tuple[str, ...]:
    return tuple(
        term for term, mapping in SOURCE_ALIASES.items()
        if any(_has(source, alias, source_lang) for alias in mapping.get(source_lang, ()))
    )

@dataclass(frozen=True)
class QualityResult:
    text: str
    model: str
    route: str
    agreement: bool | None = None
    warnings: tuple[str, ...] = ()
    needs_review: bool = False

def assess(source: str, output: str, source_lang: str, target_lang: str) -> tuple[str, ...]:
    warnings: list[str] = []
    if source.strip() and not output.strip():
        warnings.append("empty_output")
    if source.strip() and len(output.strip()) < max(2, int(len(source.strip()) * .12)):
        warnings.append("very_short_output")
    for term in required_entities(source, source_lang):
        aliases = TARGET_ALIASES[term].get(target_lang, ())
        if aliases and not any(_has(output, a, target_lang) for a in aliases):
            warnings.append("missing_entity:" + term)
    # Distinguish a detectable error from an uncertain translation.
    if source_lang != target_lang and source.strip() == output.strip():
        warnings.append("unchanged_output")
    return tuple(dict.fromkeys(warnings))

Translator = Callable[[str, str, str], str]

@dataclass
class QualityRouter:
    engines: dict[str, Translator]
    direct_engine: str = "m2m100"
    fallback_engine: str | None = "madlad"
    allow_pivot: bool = False
    pivot_lang: str = "en"

    def translate(self, text: str, source: str, target: str) -> QualityResult:
        if source not in LANGUAGES or target not in LANGUAGES or source == target:
            raise ValueError("Expected two distinct languages from en, hy, fa")
        if self.direct_engine not in self.engines:
            raise RuntimeError("Configured direct engine is unavailable")
        clean = normalize(text, source)
        if not clean:
            return QualityResult("", self.direct_engine, "direct")
        candidates: list[QualityResult] = []
        def evaluate(engine: str, route: str, output: str) -> None:
            normalized = normalize(output, target)
            warns = assess(clean, normalized, source, target)
            candidates.append(QualityResult(normalized, engine, route, warns, bool(warns)))

        primary = self.engines[self.direct_engine]
        evaluate(self.direct_engine, "direct", primary(clean, source, target))
        if candidates[0].warnings and self.fallback_engine and self.fallback_engine in self.engines and self.fallback_engine != self.direct_engine:
            try:
                evaluate(self.fallback_engine, "direct", self.engines[self.fallback_engine](clean, source, target))
            except Exception:
                pass
        if self.allow_pivot and source != self.pivot_lang and target != self.pivot_lang and candidates[0].warnings:
            try:
                intermediate = primary(clean, source, self.pivot_lang)
                if intermediate.strip():
                    evaluate(self.direct_engine, "via_en", primary(intermediate, self.pivot_lang, target))
            except Exception:
                pass
        # Heuristic selection only: never call this proof of semantic accuracy.
        selected = min(candidates, key=lambda c: (len(c.warnings), c.route != "direct", c.model != self.direct_engine))
        # A known missing entity is never cleared by a tie between flawed models.
        # Keep the diagnostic and expose conflicting translations explicitly.
        if len(candidates) > 1:
            normalized_outputs = {c.text.casefold().strip() for c in candidates}
            agreement = len(normalized_outputs) == 1
            extra = ("model_disagreement",) if not agreement else ()
            selected = QualityResult(
                text=selected.text,
                model=selected.model,
                route=selected.route,
                agreement=agreement,
                warnings=tuple(dict.fromkeys((*selected.warnings, *extra))),
                needs_review=bool(selected.warnings or extra),
            )
        return selected
