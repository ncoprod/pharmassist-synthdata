from __future__ import annotations

import random
from typing import Any

SCHEMA_VERSION = "0.0.0"


def generate_catalog(seed: int) -> list[dict[str, Any]]:
    """Generate a small OTC/parapharmacy catalog (products list)."""
    rng = random.Random(seed + 12345)

    products: list[dict[str, Any]] = [
        {
            "schema_version": SCHEMA_VERSION,
            "sku": "SKU-0001",
            "name": "Cetirizine 10mg (example)",
            "brand": "ExampleBrand",
            "category": "allergy",
            "ingredients": ["cetirizine"],
            "contraindication_tags": ["pregnancy_unknown"],
            "price_eur": 4.99,
            "in_stock": True,
            "stock_qty": 12,
        },
        {
            "schema_version": SCHEMA_VERSION,
            "sku": "SKU-0002",
            "name": "Saline nasal spray (example)",
            "brand": "ExampleBrand",
            "category": "allergy",
            "ingredients": ["sodium_chloride"],
            "contraindication_tags": [],
            "price_eur": 3.5,
            "in_stock": True,
            "stock_qty": 8,
        },
        {
            "schema_version": SCHEMA_VERSION,
            "sku": "SKU-0003",
            "name": "Moisturizing cream (example)",
            "brand": "ExampleBrand",
            "category": "derm",
            "ingredients": ["glycerin"],
            "contraindication_tags": [],
            "price_eur": 7.9,
            "in_stock": True,
            "stock_qty": 5,
        },
    ]

    # Deterministic stock variation.
    for p in products:
        if rng.random() < 0.1:
            p["in_stock"] = False
            p["stock_qty"] = 0

    return products

