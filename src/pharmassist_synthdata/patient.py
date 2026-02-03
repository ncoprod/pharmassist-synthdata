from __future__ import annotations

import random
from typing import Any

SCHEMA_VERSION = "0.0.0"


def generate_patient(seed: int) -> dict[str, Any]:
    """Generate a PHI-free llm_context-compatible patient bundle."""
    rng = random.Random(seed)

    sex = rng.choice(["F", "M"])
    age_years = rng.randint(18, 85)

    allergies: list[dict[str, Any]] = []
    conditions: list[dict[str, Any]] = []

    # Simple coherent case templates (expanded later).
    if seed % 3 == 0:
        allergies.append({"substance": "pollen", "reaction": "rhinitis", "severity": "mild"})
        conditions.append({"label": "seasonal allergic rhinitis"})
    elif seed % 3 == 1:
        conditions.append({"label": "dry skin"})
    else:
        conditions.append({"label": "mild digestive discomfort"})

    meds_pool = [
        {"name": "paracetamol", "is_prescription": False},
        {"name": "ibuprofen", "is_prescription": False},
        {"name": "metformin", "is_prescription": True},
        {"name": "levothyroxine", "is_prescription": True},
    ]
    current_medications = [meds_pool[rng.randrange(len(meds_pool))]]

    return {
        "schema_version": SCHEMA_VERSION,
        "demographics": {"age_years": age_years, "sex": sex},
        "allergies": allergies,
        "conditions": conditions,
        "current_medications": current_medications,
    }

