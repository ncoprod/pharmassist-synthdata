from __future__ import annotations

from typing import Any

from .case_bundle import generate_case_bundle


def generate_case(seed: int = 0) -> dict[str, Any]:
    """Generate a deterministic case bundle (schema-aligned)."""
    return generate_case_bundle(seed=seed)
