import json
from pathlib import Path

from pharmassist_synthdata.validate import validate_case_bundle


def test_committed_ocr_suite_fixtures_validate():
    root = Path(__file__).resolve().parent.parent
    suite_dir = root / "fixtures" / "ocr_suite"
    msg = "fixtures/ocr_suite must be committed for reproducible extraction tests"
    assert suite_dir.exists(), msg

    paths = sorted(suite_dir.glob("case_*.json"))
    assert paths, "expected at least one ocr_suite fixture"

    for p in paths:
        payload = json.loads(p.read_text(encoding="utf-8"))
        issues = validate_case_bundle(payload)
        assert issues == [], f"{p.name} invalid: {issues}"
