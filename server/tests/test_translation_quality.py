from app.ai.quality import QualityRouter, assess, normalize, required_entities

def test_armenian_spelling():
    assert normalize("Ես ապրում եմ Երեւանում։", "hy") == "Ես ապրում եմ Երևանում։"

def test_persian_unicode():
    assert normalize("من كتاب عربي مي‌خوانم", "fa") == "من کتاب عربی می‌خوانم"

def test_entity_warning():
    warnings = assess("I live in Yerevan.", "I live in appearance.", "en", "en")
    assert "missing_entity:yerevan" in warnings

def test_preserves_arbitrary_city_without_guessing():
    router = QualityRouter(engines={"m2m100": lambda text, source, target: "I live in appearance."}, fallback_engine=None)
    result = router.translate("Ես ապրում եմ Երևանում։", "hy", "en")
    assert "missing_entity:yerevan" in result.warnings
    assert result.text == "I live in appearance."
    assert result.needs_review

def test_fallback_selects_better_entity_coverage():
    router = QualityRouter(
        engines={
            "m2m100": lambda t,s,d: "I live in appearance.",
            "madlad": lambda t,s,d: "I live in Yerevan.",
        }
    )
    r = router.translate("Ես ապրում եմ Երևանում։", "hy", "en")
    assert r.model == "madlad"
    assert r.text == "I live in Yerevan."

def test_no_fallback_when_primary_passes():
    called = []
    def fallback(*args):
        called.append(True)
        return "hello"
    router = QualityRouter(
        engines={"m2m100": lambda t,s,d: "I live in Yerevan.", "madlad": fallback}
    )
    router.translate("Ես ապրում եմ Երևանում։", "hy", "en")
    assert not called

def test_six_routes_accept():
    for src in ("en", "hy", "fa"):
        for dst in ("en", "hy", "fa"):
            if src != dst:
                q = QualityRouter(engines={"m2m100": lambda t,s,d: "hello"}, fallback_engine=None)
                assert q.translate("hello", src, dst).text == "hello"

def test_two_wrong_models_mark_disagreement_and_review():
    router = QualityRouter(engines={
        "m2m100": lambda text, source, target: "Ես սովորում եմ անգլերեն։",
        "madlad": lambda text, source, target: "Ես ադրբեջաներեն եմ սովորում։",
    })
    result = router.translate("I am learning Armenian.", "en", "hy")
    assert result.needs_review
    assert result.text == "Ես սովորում եմ հայերեն։"
    assert result.repairs == ("single_language_term_repaired",)
    assert "missing_entity:armenian language" not in result.warnings
    assert result.agreement is False

from app.ai.terminology import repair_language_learning

def test_madlad_wrong_azerbaijani_is_repaired_in_narrow_context():
    r = repair_language_learning("I am learning Armenian.", "Ես ադրբեջաներեն եմ սովորում։", "en", "hy")
    assert r.applied
    assert r.text == "Ես հայերեն եմ սովորում։"

def test_multi_language_source_is_not_automatically_rewritten():
    r = repair_language_learning("I am learning Armenian and English.", "Ես սովորում եմ անգլերեն։", "en", "hy")
    assert not r.applied

def test_quotation_is_not_automatically_rewritten():
    r = repair_language_learning('She said "I am learning Armenian".', "Ես սովորում եմ անգլերեն։", "en", "hy")
    assert not r.applied

def test_ambiguous_multiple_target_languages_is_not_rewritten():
    r = repair_language_learning("I am learning Armenian.", "Ես սովորում եմ անգլերեն և պարսկերեն։", "en", "hy")
    assert not r.applied

def test_correct_term_not_changed():
    r = repair_language_learning("I am learning Armenian.", "Ես հայերեն եմ սովորում։", "en", "hy")
    assert not r.applied

def test_persian_language_repair():
    r = repair_language_learning("I am learning Armenian.", "من انگلیسی یاد می گیرم.", "en", "fa")
    assert r.applied
    assert r.text == "من ارمنی یاد می گیرم."
