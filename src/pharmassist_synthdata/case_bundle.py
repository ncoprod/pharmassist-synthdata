from __future__ import annotations

from typing import Any

from .catalog import generate_catalog
from .patient import generate_patient

SCHEMA_VERSION = "0.0.0"


def generate_intake_extracted_stub(seed: int) -> dict[str, Any]:
    # Minimal, schema-compliant structured intake (to be expanded later).
    if seed % 3 == 0:
        presenting = "Sneezing and itchy eyes for one week"
        symptoms = [
            {"label": "sneezing", "severity": "moderate", "duration_days": 7},
            {"label": "itchy eyes", "severity": "mild", "duration_days": 7},
        ]
    elif seed % 3 == 1:
        presenting = "Dry skin and mild itching"
        symptoms = [{"label": "dry skin", "severity": "mild", "duration_days": 14}]
    else:
        presenting = "Occasional bloating after meals"
        symptoms = [{"label": "bloating", "severity": "mild", "duration_days": 10}]

    return {
        "schema_version": SCHEMA_VERSION,
        "presenting_problem": presenting,
        "symptoms": symptoms,
        "red_flags": [],
    }


def generate_case_bundle(seed: int = 0) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "case_ref": f"case_{seed:06d}",
        "llm_context": generate_patient(seed),
        "intake_extracted": generate_intake_extracted_stub(seed),
        "products": generate_catalog(seed),
    }

