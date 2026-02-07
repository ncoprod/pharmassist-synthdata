from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .case_bundle import generate_case_bundle

Language = Literal["fr", "en"]
PhiMode = Literal["present", "free"]


def _sha256_12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _lines_for_pdf(*, seed: int, language: Language, phi_mode: PhiMode) -> list[str]:
    bundle = generate_case_bundle(seed=seed)
    case_ref = str(bundle.get("case_ref") or f"case_{seed:06d}")
    ocr = bundle.get("intake_text_ocr")
    if not isinstance(ocr, dict):
        raise ValueError("Missing intake_text_ocr in generated bundle")
    intake_text = ocr.get(language)
    if not isinstance(intake_text, str) or not intake_text.strip():
        raise ValueError("Missing OCR text for language")

    lines = [
        "PHARMASSIST SYNTHETIC PRESCRIPTION",
        f"case_ref: {case_ref}",
        f"language: {language}",
        f"seed: {seed}",
        "",
    ]

    if phi_mode == "present":
        if language == "fr":
            lines.extend(
                [
                    "Nom: Martin",
                    "Prenom: Lucie",
                    "Date de naissance: 14/06/1987",
                    "Adresse: 15 rue de Vaugirard, Paris 75015",
                    "Telephone: 0611223344",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "Name: Lucy Martin",
                    "Date of birth: 1987-06-14",
                    "Address: 15 Rue de Vaugirard, Paris 75015",
                    "Phone: +33611223344",
                    "",
                ]
            )

    lines.append("=== OCR-LIKE PRESCRIPTION TEXT ===")
    lines.extend(intake_text.splitlines())
    return lines


def _write_text_layer_pdf(*, path: Path, lines: list[str]) -> None:
    # invariant=1 makes reportlab output deterministic (no current-time stamps).
    c = canvas.Canvas(str(path), pagesize=A4, invariant=1, pageCompression=1)
    c.setTitle("PharmAssist Synthetic Prescription")
    c.setAuthor("pharmassist-synthdata")
    c.setSubject("Synthetic-only prescription sample")
    c.setFont("Helvetica", 11)

    width, height = A4
    x = 48
    y = height - 56
    line_step = 15
    page_count = 1
    for line in lines:
        if y < 64:
            c.setFont("Helvetica", 9)
            c.drawString(x, 40, f"Page {page_count}")
            c.showPage()
            page_count += 1
            c.setFont("Helvetica", 11)
            y = height - 56
        c.drawString(x, y, line[:160])
        y -= line_step

    c.setFont("Helvetica", 9)
    c.drawString(x, 40, f"Page {page_count}")
    c.save()


def _default_case_seeds(seed: int) -> tuple[int, ...]:
    # Keep default suite parity while letting callers shift the deterministic case set.
    return (seed, seed + 59, seed + 60)


def generate_prescription_pdf_suite(
    *,
    out_dir: Path,
    seed: int = 42,
    seeds: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    case_seeds = seeds or _default_case_seeds(seed)
    case_seeds = tuple(int(x) for x in case_seeds)
    if not case_seeds:
        raise ValueError("At least one case seed is required")

    for case_seed in case_seeds:
        bundle = generate_case_bundle(seed=case_seed)
        case_ref = str(bundle.get("case_ref") or f"case_{case_seed:06d}")
        intake = bundle.get("intake_extracted")
        expected_symptoms: list[str] = []
        expected_red_flags: list[str] = []
        if isinstance(intake, dict):
            for s in intake.get("symptoms") or []:
                if isinstance(s, dict) and isinstance(s.get("label"), str):
                    expected_symptoms.append(s["label"])
            for rf in intake.get("red_flags") or []:
                if isinstance(rf, str):
                    expected_red_flags.append(rf)

        for language in ("fr", "en"):
            for phi_mode in ("present", "free"):
                filename = f"rx_{phi_mode}_{language}_{case_ref}.pdf"
                path = out_dir / filename
                lines = _lines_for_pdf(seed=case_seed, language=language, phi_mode=phi_mode)
                _write_text_layer_pdf(path=path, lines=lines)
                data = path.read_bytes()

                files.append(
                    {
                        "doc_ref": f"doc_{phi_mode}_{language}_{case_ref}",
                        "filename": filename,
                        "language": language,
                        "case_ref": case_ref,
                        "seed": case_seed,
                        "phi_mode": phi_mode,
                        "expected_outcome": (
                            "fail_phi_boundary" if phi_mode == "present" else "schema_valid_intake"
                        ),
                        "expected_symptoms": expected_symptoms,
                        "expected_red_flags": expected_red_flags,
                        "sha256_12": _sha256_12(data),
                        "bytes": len(data),
                    }
                )

    manifest = {
        "schema_version": "0.0.0",
        "suite": "synthetic_prescription_pdf_v1",
        "seed": int(seed),
        "case_seeds": list(case_seeds),
        "files": sorted(files, key=lambda x: str(x.get("filename") or "")),
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
