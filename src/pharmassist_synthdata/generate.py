from __future__ import annotations

import random
from typing import Any


def generate_case(seed: int = 0) -> dict[str, Any]:
    """Generate a small deterministic bundle.

    Day 1 stub: Day 2+ will expand realism (France-first), add catalog + OCR noise,
    and enforce stronger clinical/coherence constraints.
    """
    rng = random.Random(seed)

    sex = rng.choice(["F", "M"])
    age_years = rng.randint(18, 85)

    return {
        "schema_version": "0.0.0",
        "seed": seed,
        "patient": {
            # Synthetic internal identifier (NOT a real identifier).
            "patient_ref": f"pt_{seed:06d}",
            "sex": sex,
            "age_years": age_years,
        },
        "intake": {
            "free_text": "Patient reports mild seasonal allergy symptoms (synthetic).",
        },
        "catalog": {
            "products": [
                {
                    "sku": "SKU-0001",
                    "name": "Cetirizine 10mg (example)",
                    "category": "allergy",
                    "in_stock": True,
                }
            ]
        },
    }

