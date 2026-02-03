from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


def _schemas_dir() -> Path:
    return Path(__file__).resolve().parent / "schemas"


def load_schema_by_name(schema_name: str) -> dict[str, Any]:
    """Load vendored schema by basename (without `.schema.json`)."""
    path = _schemas_dir() / f"{schema_name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def _schemas_by_id() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in sorted(_schemas_dir().glob("*.schema.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        schema_id = doc.get("$id")
        if not schema_id:
            raise ValueError(f"Schema missing $id: {path}")
        out[str(schema_id)] = doc
    return out


@lru_cache
def schema_registry() -> Registry:
    reg = Registry()
    for schema_id, doc in _schemas_by_id().items():
        reg = reg.with_resource(
            schema_id, Resource.from_contents(doc, default_specification=DRAFT202012)
        )
    return reg

