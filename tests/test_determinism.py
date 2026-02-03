from pharmassist_synthdata.case_bundle import generate_case_bundle


def test_generate_case_bundle_is_deterministic():
    a = generate_case_bundle(seed=42)
    b = generate_case_bundle(seed=42)
    assert a == b

