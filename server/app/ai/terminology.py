"""Narrow, auditable repairs for explicit spoken language-learning phrases.

Never perform unrestricted dictionary substitution: foreign-language words may
occur legitimately in quotations, comparisons, or multi-language utterances.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

# Target-word spellings, including a common wrong language output.
LANGUAGE_WORDS = {
    "en": {"armenian": "Armenian", "english": "English", "persian": "Persian", "azerbaijani": "Azerbaijani"},
    "hy": {"armenian": "հայերեն", "english": "անգլերեն", "persian": "պարսկերեն", "azerbaijani": "ադրբեջաներեն"},
    "fa": {"armenian": "ارمنی", "english": "انگلیسی", "persian": "فارسی", "azerbaijani": "آذربایجانی"},
}
# Full-sentence and single-language intent only: intentionally conservative.
EN_LEARNING = re.compile(r"^\s*I\s+am\s+learning\s+(Armenian|English|Persian)\s*[.!?]?\s*$", re.I)
HY_LEARNING = re.compile(r"^\s*Ես\s+(?:սովորում\s+եմ|(?:հայերեն|անգլերեն|պարսկերեն)\s+եմ\s+սովորում)\s+(հայերեն|անգլերեն|պարսկերեն)\s*[։.!?]?\s*$", re.I)

@dataclass(frozen=True)
class Repair:
    text: str
    applied: bool = False
    reason: str | None = None

def learning_intent(text: str, source: str) -> str | None:
    if source != "en":
        return None
    match = EN_LEARNING.fullmatch(text)
    return match.group(1).casefold() if match else None

def repair_language_learning(source_text: str, output: str, source: str, target: str) -> Repair:
    """Replace a *single* confidently identified wrong language token.

    Only applies to an exact English 'I am learning X' utterance translated to
    Armenian or Persian. Does not change sentence structure or fabricate verbs.
    """
    expected = learning_intent(source_text, source)
    if not expected or target not in ("hy", "fa"):
        return Repair(output)
    words = LANGUAGE_WORDS[target]
    correct = words[expected]
    # Already correct: no editing, even if the output also contains another name.
    if re.search(r"(?<!\w)" + re.escape(correct) + r"(?!\w)", output, re.I):
        return Repair(output)
    matches = [
        (key, list(re.finditer(r"(?<!\w)" + re.escape(word) + r"(?!\w)", output, re.I)))
        for key, word in words.items() if key != expected
    ]
    found = [(key, match) for key, entries in matches for match in entries]
    if len(found) != 1:
        return Repair(output)
    _, match = found[0]
    updated = output[:match.start()] + correct + output[match.end():]
    return Repair(updated, True, "single_language_term_repaired")
