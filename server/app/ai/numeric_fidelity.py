"""Read-only numeric fidelity checks for multilingual translation.

Numbers, times, and ISO-style dates are checked without rewriting prose.
Do not insert a missing number blindly: nearby units and negation matter.
"""
from __future__ import annotations
import re
from collections import Counter
from decimal import Decimal, InvalidOperation

# Avoid interpreting digits embedded inside names or identifiers.
NUMERIC = re.compile(r"(?<![\w])(?:[0-9۰-۹٠-٩]+(?:[.,٫٬][0-9۰-۹٠-٩]+)*)(?![\w])")
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def numeric_tokens(text: str) -> tuple[str, ...]:
    results = []
    for match in NUMERIC.finditer(text):
        raw = match.group().translate(DIGITS)
        # Grouping separators are accepted only when consistent with 3 digits.
        value = raw.replace("٬", ",").replace("٫", ".")
        if "," in value and "." in value:
            decimal_symbol = "," if value.rfind(",") > value.rfind(".") else "."
            grouping = "." if decimal_symbol == "," else ","
            value = value.replace(grouping, "").replace(decimal_symbol, ".")
        elif "," in value:
            groups = value.split(",")
            value = value.replace(",", "") if len(groups) > 1 and all(len(g) == 3 for g in groups[1:]) else value.replace(",", ".")
        try:
            results.append(str(Decimal(value).normalize()))
        except InvalidOperation:
            results.append(raw)
    return tuple(results)

def number_warnings(source: str, output: str) -> tuple[str, ...]:
    expected = Counter(numeric_tokens(source))
    observed = Counter(numeric_tokens(output))
    if not expected and not observed:
        return ()
    warnings = []
    if expected - observed:
        warnings.append("numeric_value_missing_or_changed")
    if observed - expected:
        warnings.append("numeric_value_added_or_changed")
    return tuple(warnings)
