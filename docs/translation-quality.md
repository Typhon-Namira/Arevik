# Shared translation quality layer (experimental)

This change introduces opt-in adapters for the two locally benchmarked translation engines:
M2M100 418M CTranslate2 INT8 and MADLAD-400 3B CTranslate2 INT8.

It does **not** replace the existing OPUS-MT production path. No server or EC2
configuration is changed by this branch. SMaLL-100 is intentionally out of scope.

## Controls
- Conservative NFC / whitespace normalization and minimal spelling fixes.
- Curated multilingual entity aliases for Yerevan, Armenia and language names.
- Missing-entity, empty and suspiciously short output warnings.
- Optional fallback to the other engine **only when checks flag a potential issue**.
- Optional English-pivot routing for hy/fa, disabled by default.
- Lazy model loading for CPU; do not start both engines without monitoring RAM.
- The output retains warnings and which model/route produced it.

This is not a semantic verifier. A fluent but wrong translation can pass checks.
Entity checks may produce false positives, especially around inflection.
No unconditional replacements of source factual content, language names or arbitrary
target words are performed. No model fine-tuning. No privacy-sensitive persistent logs.

## Usage (inside the existing arevik-server Python environment)

```python
from app.ai.translation_backends import M2M100CT2, MadladCT2
from app.ai.quality import QualityRouter

router = QualityRouter(engines={
    "m2m100": M2M100CT2("/opt/arevik/cache/converted/m2m100-418m-int8"),
    "madlad": MadladCT2("/path/to/ct2/madlad/model"),
}, direct_engine="m2m100", fallback_engine="madlad")

result = router.translate("Ես ապրում եմ Երևանում։", "hy", "en")
print(result.text, result.warnings, result.model)
```

The actual MADLAD path on your EC2 was downloaded via Hugging Face and
must be resolved from the pinned snapshot path. Do not paste an invented path.

## Acceptance before enabling in API
1. Execute `pytest -q server/tests/test_translation_quality.py` with the server package installed.
2. Verify each adapter with the exact pinned model snapshots on the EC2.
3. Benchmark all six directions with human-reviewed Eastern Armenian and Persian references,
   including proper names, numbers, negation, long and multi-sentence text.
4. Measure p50/p95 total latency and peak RSS with concurrent users on 2 vCPU/8 GiB.
5. Only then switch a feature flag; keep rollback to OPUS-MT.

Do not claim high translation accuracy from these rule-based checks alone.
