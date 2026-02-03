from pharmassist_synthdata.generate import generate_case


def test_generate_case_is_deterministic():
    a = generate_case(seed=42)
    b = generate_case(seed=42)
    assert a == b


def test_generate_case_has_expected_shape():
    payload = generate_case(seed=1)
    assert payload["schema_version"] == "0.0.0"
    assert "patient" in payload
    assert "catalog" in payload

