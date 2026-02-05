import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from pharmassist_synthdata.sim_year import generate_pharmacy_year
from pharmassist_synthdata.validate import validate_instance


def _read_jsonl_gz(path: Path) -> list[Any]:
    out: list[Any] = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def _has_forbidden_identifier_keys(obj: Any) -> bool:
    forbidden = {
        "phi",
        "surname",
        "first_name",
        "last_name",
        "full_name",
        "patient_name",
        "patient_first_name",
        "patient_last_name",
        "email",
        "phone",
        "address",
        "street",
        "city",
        "postal_code",
        "zip",
        "dob",
        "date_of_birth",
        "nir",
        "ssn",
        # French common variants
        "nom",
        "prenom",
        "adresse",
        "telephone",
        "téléphone",
        "mail",
        "code_postal",
        "ville",
        "date_naissance",
    }

    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in forbidden:
                return True
            if _has_forbidden_identifier_keys(v):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if _has_forbidden_identifier_keys(item):
                return True
    return False


def test_sim_year_mini_outputs_exist_and_are_schema_compatible():
    with TemporaryDirectory() as td:
        out_dir = Path(td)
        generate_pharmacy_year(seed=42, pharmacy="paris15", year=2025, out_dir=out_dir, mode="mini")

        patients = _read_jsonl_gz(out_dir / "patients.jsonl.gz")
        visits = _read_jsonl_gz(out_dir / "visits.jsonl.gz")
        events = _read_jsonl_gz(out_dir / "events.jsonl.gz")
        inventory = _read_jsonl_gz(out_dir / "inventory.jsonl.gz")

        assert len(patients) == 20
        assert len(visits) == 60
        assert len(events) >= 60
        assert len(inventory) > 0

        assert not _has_forbidden_identifier_keys(patients)
        assert not _has_forbidden_identifier_keys(visits)
        assert not _has_forbidden_identifier_keys(events)

        patient_refs = {p["patient_ref"] for p in patients}
        assert len(patient_refs) == 20

        for p in patients:
            assert validate_instance(p["llm_context"], schema_name="llm_context") == []

        for v in visits:
            assert v["patient_ref"] in patient_refs
            assert validate_instance(v["intake_extracted"], schema_name="intake_extracted") == []

        for p in inventory:
            assert validate_instance(p, schema_name="product") == []

