"""Deterministic offline regression fixtures; no inference required.

Human review is necessary before treating fixtures as translation-quality scores.
"""
from __future__ import annotations
from dataclasses import dataclass
from app.ai.quality import assess

@dataclass(frozen=True)
class Case:
    source: str
    target: str
    source_lang: str
    target_lang: str
    category: str

CASES = (
    Case("I live in Yerevan.", "Ես ապրում եմ Երևանում։", "en", "hy", "place"),
    Case("Ես ապրում եմ Երևանում։", "I live in Yerevan.", "hy", "en", "place"),
    Case("I need 15 tickets.", "من ۱۵ بلیت می‌خواهم.", "en", "fa", "number"),
    Case("قیمت ۵۰ دلار است.", "The price is 50 dollars.", "fa", "en", "number"),
    Case("Ես ուզում եմ ۳ տոմս։", "من ۳ بلیت می‌خواهم.", "hy", "fa", "number"),
    Case("من ۲ بلیت می‌خواهم.", "Ես ուզում եմ ۲ տոմս։", "fa", "hy", "number"),
    Case("I am learning Armenian.", "Ես հայերեն եմ սովորում։", "en", "hy", "language"),
)

def fixture_checks() -> list[tuple[Case, tuple[str, ...]]]:
    return [(case, assess(case.source, case.target, case.source_lang, case.target_lang)) for case in CASES]
