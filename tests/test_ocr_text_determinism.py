from pharmassist_synthdata.case_bundle import generate_case_bundle


def test_intake_text_ocr_is_deterministic():
    a = generate_case_bundle(seed=42)
    b = generate_case_bundle(seed=42)

    assert a["intake_text_ocr"] == b["intake_text_ocr"]
    assert isinstance(a["intake_text_ocr"]["fr"], str) and a["intake_text_ocr"]["fr"].strip()
    assert isinstance(a["intake_text_ocr"]["en"], str) and a["intake_text_ocr"]["en"].strip()

