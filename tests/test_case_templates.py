from pharmassist_synthdata.case_bundle import generate_case_bundle
from pharmassist_synthdata.validate import validate_case_bundle


def test_case_redflag_000101_template():
    bundle = generate_case_bundle(seed=101)
    assert bundle["case_ref"] == "case_redflag_000101"

    symptoms = bundle["intake_extracted"]["symptoms"]
    labels = {s.get("label") for s in symptoms if isinstance(s, dict)}
    assert {"dyspnea", "chest pain"} <= labels

    red_flags = bundle["intake_extracted"]["red_flags"]
    assert "dyspnea" in red_flags
    assert "chest_pain" in red_flags

    assert validate_case_bundle(bundle) == []


def test_case_lowinfo_000102_template():
    bundle = generate_case_bundle(seed=102)
    assert bundle["case_ref"] == "case_lowinfo_000102"

    symptoms = bundle["intake_extracted"]["symptoms"]
    assert len(symptoms) == 1
    assert symptoms[0]["label"] == "unspecified symptom"
    assert symptoms[0]["severity"] == "unknown"
    assert "duration_days" not in symptoms[0]

    assert bundle["intake_extracted"]["red_flags"] == []
    assert validate_case_bundle(bundle) == []

