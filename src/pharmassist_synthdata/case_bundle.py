from __future__ import annotations

from typing import Any

from .catalog import generate_catalog
from .ocr_text import generate_intake_text_ocr
from .patient import generate_patient

SCHEMA_VERSION = "0.0.0"

_SPECIAL_CASE_REFS: dict[int, str] = {
    # Keep the numeric suffix aligned with the seed for reproducibility, while
    # allowing scenario-labeled fixtures for downstream triage/extraction tests.
    101: "case_redflag_000101",
    102: "case_lowinfo_000102",
}


def case_ref_for_seed(seed: int) -> str:
    return _SPECIAL_CASE_REFS.get(seed, f"case_{seed:06d}")


def generate_intake_extracted_stub(seed: int) -> dict[str, Any]:
    # Minimal, schema-compliant structured intake (to be expanded later).
    if seed == 101:
        presenting = "Dyspnea and chest pain"
        symptoms = [
            {"label": "dyspnea", "severity": "severe", "duration_days": 1},
            {"label": "chest pain", "severity": "severe", "duration_days": 1},
        ]
        red_flags = ["dyspnea", "chest_pain"]
    elif seed == 102:
        presenting = "Unspecified symptom"
        symptoms = [
            {
                "label": "unspecified symptom",
                "severity": "unknown",
                "notes": "Patient unable to describe symptom clearly; no additional details.",
            }
        ]
        red_flags = []
    elif seed % 3 == 0:
        presenting = "Sneezing and itchy eyes for one week"
        symptoms = [
            {"label": "sneezing", "severity": "moderate", "duration_days": 7},
            {"label": "itchy eyes", "severity": "mild", "duration_days": 7},
        ]
        red_flags = []
    elif seed % 3 == 1:
        presenting = "Dry skin and mild itching"
        symptoms = [{"label": "dry skin", "severity": "mild", "duration_days": 14}]
        red_flags = []
    else:
        presenting = "Occasional bloating after meals"
        symptoms = [{"label": "bloating", "severity": "mild", "duration_days": 10}]
        red_flags = []

    return {
        "schema_version": SCHEMA_VERSION,
        "presenting_problem": presenting,
        "symptoms": symptoms,
        "red_flags": red_flags,
    }


def generate_case_bundle(seed: int = 0) -> dict[str, Any]:
    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "case_ref": case_ref_for_seed(seed),
        "llm_context": generate_patient(seed),
        "intake_extracted": generate_intake_extracted_stub(seed),
        "products": generate_catalog(seed),
    }

    # Add an OCR-like untrusted text field derived from the structured ground truth.
    # This remains PHI-free by construction.
    bundle["intake_text_ocr"] = generate_intake_text_ocr(seed, bundle)

    return bundle
