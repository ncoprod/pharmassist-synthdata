from pharmassist_synthdata.case_bundle import generate_case_bundle
from pharmassist_synthdata.validate import validate_case_bundle


def test_generated_case_bundle_matches_vendored_schemas():
    bundle = generate_case_bundle(seed=42)
    issues = validate_case_bundle(bundle)
    assert issues == []

