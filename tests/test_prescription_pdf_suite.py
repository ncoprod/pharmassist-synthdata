from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pharmassist_synthdata.prescription_pdf import _lines_for_pdf, generate_prescription_pdf_suite


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generate_prescription_pdf_suite_writes_manifest_and_pdfs(tmp_path: Path):
    out_dir = tmp_path / "rx_pdf_suite"
    manifest = generate_prescription_pdf_suite(out_dir=out_dir, seed=42)

    files = manifest.get("files")
    assert isinstance(files, list)
    assert len(files) == 12  # 3 case seeds x 2 languages x 2 phi modes

    manifest_path = out_dir / "manifest.json"
    assert manifest_path.exists()
    on_disk = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert on_disk.get("suite") == "synthetic_prescription_pdf_v1"
    assert on_disk.get("case_seeds") == [42, 101, 102]
    assert len(on_disk.get("files") or []) == 12

    for row in on_disk["files"]:
        pdf_path = out_dir / row["filename"]
        assert pdf_path.exists()
        assert pdf_path.suffix.lower() == ".pdf"
        assert row["bytes"] > 500
        assert row["expected_outcome"] in {"fail_phi_boundary", "schema_valid_intake"}


def test_generate_prescription_pdf_suite_is_deterministic(tmp_path: Path):
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    manifest_a = generate_prescription_pdf_suite(out_dir=out_a, seed=42)
    manifest_b = generate_prescription_pdf_suite(out_dir=out_b, seed=42)

    files_a = sorted(manifest_a["files"], key=lambda x: x["filename"])
    files_b = sorted(manifest_b["files"], key=lambda x: x["filename"])
    assert [f["filename"] for f in files_a] == [f["filename"] for f in files_b]

    for left, right in zip(files_a, files_b, strict=True):
        assert left["sha256_12"] == right["sha256_12"]
        assert _sha256(out_a / left["filename"]) == _sha256(out_b / right["filename"])


def test_generate_prescription_pdf_suite_seed_changes_case_set(tmp_path: Path):
    out_a = tmp_path / "seed_42"
    out_b = tmp_path / "seed_43"
    manifest_a = generate_prescription_pdf_suite(out_dir=out_a, seed=42)
    manifest_b = generate_prescription_pdf_suite(out_dir=out_b, seed=43)

    assert manifest_a["case_seeds"] == [42, 101, 102]
    assert manifest_b["case_seeds"] == [43, 102, 103]

    names_a = {f["filename"] for f in manifest_a["files"]}
    names_b = {f["filename"] for f in manifest_b["files"]}
    assert names_a != names_b


def test_phi_mode_only_includes_identity_block_when_present():
    present_lines = _lines_for_pdf(seed=42, language="en", phi_mode="present")
    free_lines = _lines_for_pdf(seed=42, language="en", phi_mode="free")

    present_blob = "\n".join(present_lines)
    free_blob = "\n".join(free_lines)
    assert "Name: Lucy Martin" in present_blob
    assert "Name: Lucy Martin" not in free_blob
