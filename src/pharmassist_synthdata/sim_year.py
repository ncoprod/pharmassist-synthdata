from __future__ import annotations

import gzip
import json
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Literal

from .catalog import SCHEMA_VERSION as PRODUCT_SCHEMA_VERSION
from .patient import SCHEMA_VERSION as LLM_CONTEXT_SCHEMA_VERSION
from .patient import generate_patient

Mode = Literal["full", "mini"]


@dataclass(frozen=True)
class PharmacyYearParams:
    pharmacy: str
    mu_base: float
    nb_k: float | None
    p_new_visit: float
    p_multi_intent: float
    initial_patients: int
    # Monday=0 ... Sunday=6
    dow_factors: dict[int, float]
    month_factors: dict[int, float]


def default_params(*, pharmacy: str) -> PharmacyYearParams:
    if pharmacy != "paris15":
        raise ValueError(f"Unsupported pharmacy: {pharmacy}")

    # v1 defaults are documented in the private plan repo (PharmAssist 2026):
    # - mu_base=210 (Paris 15e standard)
    # - Sunday closed (0)
    # - moderate overdispersion via NB(k=400)
    # - repeat customers: ~92% of visits are returning => p_new_visit ~ 0.08
    # - multi-intent: ~60%
    return PharmacyYearParams(
        pharmacy="paris15",
        mu_base=210.0,
        nb_k=400.0,
        p_new_visit=0.08,
        p_multi_intent=0.60,
        initial_patients=5250,  # ~25x mu_base => ~12–13 visits/patient/year
        dow_factors={0: 1.00, 1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 0.75, 6: 0.00},
        month_factors={
            1: 1.20,
            2: 1.15,
            3: 1.10,
            4: 1.00,
            5: 1.05,
            6: 0.95,
            7: 0.90,
            8: 0.85,
            9: 1.05,
            10: 1.10,
            11: 1.15,
            12: 1.20,
        },
    )


def _iter_dates(year: int) -> list[date]:
    d = date(year, 1, 1)
    out: list[date] = []
    while d.year == year:
        out.append(d)
        d += timedelta(days=1)
    return out


def _poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0

    # Knuth for small λ; normal approximation for large λ (deterministic + fast).
    if lam < 30:
        k = 0
        p = 1.0
        threshold = pow(2.718281828459045, -lam)
        while p > threshold:
            k += 1
            p *= rng.random()
        return max(0, k - 1)

    # Normal approximation.
    x = rng.gauss(lam, lam**0.5)
    return max(0, int(round(x)))


def _neg_binom(rng: random.Random, mu: float, k: float) -> int:
    if mu <= 0:
        return 0
    if k <= 0:
        return _poisson(rng, mu)

    lam = rng.gammavariate(k, mu / k)
    return _poisson(rng, lam)


def _domain_probs_by_month(month: int) -> list[tuple[str, float]]:
    # Lightweight seasonality. We keep labels aligned with the Kaggle question bank domains.
    # Returns pairs: (domain_id, weight)
    if month in (12, 1, 2):
        return [
            ("respiratory", 0.45),
            ("digestive", 0.20),
            ("pain", 0.15),
            ("skin", 0.10),
            ("allergy_ent", 0.05),
            ("urology", 0.03),
            ("eye", 0.02),
        ]
    if month in (3, 4, 5):
        return [
            ("allergy_ent", 0.45),
            ("respiratory", 0.20),
            ("digestive", 0.12),
            ("skin", 0.10),
            ("pain", 0.08),
            ("eye", 0.03),
            ("urology", 0.02),
        ]
    if month in (6, 7, 8):
        return [
            ("skin", 0.25),
            ("digestive", 0.20),
            ("pain", 0.18),
            ("respiratory", 0.15),
            ("eye", 0.12),
            ("allergy_ent", 0.06),
            ("urology", 0.04),
        ]
    return [
        ("respiratory", 0.35),
        ("allergy_ent", 0.20),
        ("digestive", 0.15),
        ("pain", 0.12),
        ("skin", 0.10),
        ("urology", 0.05),
        ("eye", 0.03),
    ]


def _choice_weighted(rng: random.Random, items: list[tuple[str, float]]) -> str:
    total = sum(w for _, w in items)
    if total <= 0:
        return items[0][0]
    r = rng.random() * total
    acc = 0.0
    for key, w in items:
        acc += w
        if r <= acc:
            return key
    return items[-1][0]


def _intake_extracted_for_domain(rng: random.Random, *, domain: str) -> dict[str, Any]:
    # Keep this strictly schema-compatible with intake_extracted.schema.json (no extra keys).
    # Use short labels; avoid free text that could invite PHI.
    if domain == "allergy_ent":
        days = rng.choice([3, 5, 7, 10, 14])
        return {
            "schema_version": "0.0.0",
            "presenting_problem": "Sneezing and itchy eyes",
            "symptoms": [
                {"label": "sneezing", "severity": "moderate", "duration_days": days},
                {"label": "itchy eyes", "severity": "mild", "duration_days": days},
            ],
            "red_flags": [],
        }
    if domain == "digestive":
        days = rng.choice([1, 2, 3, 5, 7, 10])
        return {
            "schema_version": "0.0.0",
            "presenting_problem": "Bloating after meals",
            "symptoms": [{"label": "bloating", "severity": "mild", "duration_days": days}],
            "red_flags": [],
        }
    if domain == "skin":
        days = rng.choice([7, 10, 14, 21])
        return {
            "schema_version": "0.0.0",
            "presenting_problem": "Dry skin and itching",
            "symptoms": [{"label": "dry skin", "severity": "mild", "duration_days": days}],
            "red_flags": [],
        }
    if domain == "pain":
        days = rng.choice([1, 2, 3, 5])
        sev = rng.choice(["mild", "moderate"])
        return {
            "schema_version": "0.0.0",
            "presenting_problem": "Headache",
            "symptoms": [{"label": "headache", "severity": sev, "duration_days": days}],
            "red_flags": [],
        }
    if domain == "eye":
        days = rng.choice([1, 2, 3])
        return {
            "schema_version": "0.0.0",
            "presenting_problem": "Eye irritation",
            "symptoms": [{"label": "eye irritation", "severity": "mild", "duration_days": days}],
            "red_flags": [],
        }
    if domain == "urology":
        days = rng.choice([1, 2, 3, 5])
        return {
            "schema_version": "0.0.0",
            "presenting_problem": "Burning urination",
            "symptoms": [
                {"label": "burning urination", "severity": "moderate", "duration_days": days}
            ],
            "red_flags": [],
        }

    # respiratory default
    days = rng.choice([1, 2, 3, 5, 7])
    return {
        "schema_version": "0.0.0",
        "presenting_problem": "Cough and sore throat",
        "symptoms": [
            {"label": "cough", "severity": "moderate", "duration_days": days},
            {"label": "sore throat", "severity": "mild", "duration_days": days},
        ],
        "red_flags": [],
    }


def _generate_inventory(seed: int, *, n_products: int) -> list[dict[str, Any]]:
    rng = random.Random(seed + 9999)

    base: list[dict[str, Any]] = [
        {
            "schema_version": "0.0.0",
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
            "schema_version": "0.0.0",
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
            "schema_version": "0.0.0",
            "sku": "SKU-0003",
            "name": "Moisturizing cream (example)",
            "brand": "ExampleBrand",
            "category": "dermatology",
            "ingredients": ["glycerin", "urea"],
            "contraindication_tags": [],
            "price_eur": 7.9,
            "in_stock": True,
            "stock_qty": 5,
        },
        {
            "schema_version": "0.0.0",
            "sku": "SKU-0004",
            "name": "Emollient balm (example)",
            "brand": "ExampleBrand",
            "category": "dermatology",
            "ingredients": ["emollient"],
            "contraindication_tags": [],
            "price_eur": 9.9,
            "in_stock": True,
            "stock_qty": 6,
        },
        {
            "schema_version": "0.0.0",
            "sku": "SKU-0005",
            "name": "Simethicone 80mg (example)",
            "brand": "ExampleBrand",
            "category": "digestion",
            "ingredients": ["simethicone"],
            "contraindication_tags": ["pregnancy_unknown"],
            "price_eur": 5.5,
            "in_stock": True,
            "stock_qty": 10,
        },
        {
            "schema_version": "0.0.0",
            "sku": "SKU-0006",
            "name": "Probiotic capsules (example)",
            "brand": "ExampleBrand",
            "category": "digestion",
            "ingredients": ["probiotic"],
            "contraindication_tags": [],
            "price_eur": 12.9,
            "in_stock": True,
            "stock_qty": 4,
        },
        {
            "schema_version": "0.0.0",
            "sku": "SKU-0007",
            "name": "Oral rehydration salts (example)",
            "brand": "ExampleBrand",
            "category": "digestion",
            "ingredients": ["oral_rehydration_salts"],
            "contraindication_tags": [],
            "price_eur": 6.2,
            "in_stock": True,
            "stock_qty": 7,
        },
        {
            "schema_version": "0.0.0",
            "sku": "SKU-0008",
            "name": "Vitamin D3 (example)",
            "brand": "ExampleBrand",
            "category": "general",
            "ingredients": ["vitamin_d3"],
            "contraindication_tags": [],
            "price_eur": 8.8,
            "in_stock": True,
            "stock_qty": 9,
        },
    ]

    products: list[dict[str, Any]] = []
    for i in range(max(n_products, len(base))):
        tmpl = base[i % len(base)]
        p = {**tmpl}
        p["schema_version"] = PRODUCT_SCHEMA_VERSION
        p["sku"] = f"SKU-{i + 1:04d}"
        if i >= len(base):
            p["name"] = f"{tmpl['name']} #{(i // len(base)) + 1}"
        if rng.random() < 0.08:
            p["in_stock"] = False
            p["stock_qty"] = 0
        else:
            p["in_stock"] = True
            p["stock_qty"] = int(rng.randint(1, 30))
        products.append(p)

    return products[:n_products]


def generate_pharmacy_year(
    *,
    seed: int,
    pharmacy: str,
    year: int,
    out_dir: Path,
    mode: Mode = "full",
) -> None:
    """Generate a synthetic pharmacy-year dataset.

    Outputs (gzipped JSONL):
    - patients.jsonl.gz
    - visits.jsonl.gz
    - events.jsonl.gz
    - inventory.jsonl.gz
    """
    params = default_params(pharmacy=pharmacy)
    rng = random.Random(seed)

    out_dir.mkdir(parents=True, exist_ok=True)
    patients_path = out_dir / "patients.jsonl.gz"
    visits_path = out_dir / "visits.jsonl.gz"
    events_path = out_dir / "events.jsonl.gz"
    inventory_path = out_dir / "inventory.jsonl.gz"

    def dumps(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    with (
        gzip.open(patients_path, "wt", encoding="utf-8") as patients_f,
        gzip.open(visits_path, "wt", encoding="utf-8") as visits_f,
        gzip.open(events_path, "wt", encoding="utf-8") as events_f,
        gzip.open(inventory_path, "wt", encoding="utf-8") as inventory_f,
    ):
        inv = _generate_inventory(seed, n_products=200 if mode == "full" else 50)
        for p in inv:
            inventory_f.write(dumps(p) + "\n")

        patient_counter = 0
        patient_refs: list[str] = []
        patient_weights: list[int] = []

        initial_patients = params.initial_patients if mode == "full" else 20
        for i in range(initial_patients):
            patient_ref = f"pt_{patient_counter:06d}"
            patient_counter += 1

            llm_context = generate_patient(seed=(seed * 100_000) + 1000 + i)
            if not isinstance(llm_context.get("schema_version"), str):
                llm_context["schema_version"] = LLM_CONTEXT_SCHEMA_VERSION

            patients_f.write(dumps({"patient_ref": patient_ref, "llm_context": llm_context}) + "\n")
            patient_refs.append(patient_ref)
            patient_weights.append(1)

        def pick_patient_ref() -> str:
            idx = rng.choices(range(len(patient_refs)), weights=patient_weights, k=1)[0]
            patient_weights[idx] += 1
            return patient_refs[idx]

        visit_counter = 0
        event_counter = 0

        def write_event(
            *,
            visit_ref: str,
            patient_ref: str,
            occurred_at: str,
            event_type: str,
            payload: Any,
        ) -> None:
            nonlocal event_counter
            ev_ref = f"ev_{event_counter:09d}"
            event_counter += 1
            events_f.write(
                dumps(
                    {
                        "event_ref": ev_ref,
                        "visit_ref": visit_ref,
                        "patient_ref": patient_ref,
                        "occurred_at": occurred_at,
                        "event_type": event_type,
                        "payload": payload,
                    }
                )
                + "\n"
            )

        if mode == "mini":
            visit_dates = [
                date(year, 1, 15),
                date(year, 3, 10),
                date(year, 5, 20),
                date(year, 9, 5),
                date(year, 11, 25),
            ]

            for i in range(60):
                d = visit_dates[i % len(visit_dates)]
                occurred_at = d.isoformat()
                patient_ref = patient_refs[i % len(patient_refs)]

                if i == 2:
                    intake_extracted = {
                        "schema_version": "0.0.0",
                        "presenting_problem": "Unspecified symptom",
                        "symptoms": [{"label": "unspecified symptom", "severity": "unknown"}],
                        "red_flags": [],
                    }
                    primary_domain = "other"
                elif i == 3:
                    intake_extracted = {
                        "schema_version": "0.0.0",
                        "presenting_problem": "Dyspnea and chest pain",
                        "symptoms": [
                            {"label": "dyspnea", "severity": "severe", "duration_days": 1},
                            {"label": "chest pain", "severity": "severe", "duration_days": 1},
                        ],
                        "red_flags": ["dyspnea", "chest_pain"],
                    }
                    primary_domain = "respiratory"
                else:
                    domain = _choice_weighted(rng, _domain_probs_by_month(d.month))
                    intake_extracted = _intake_extracted_for_domain(rng, domain=domain)
                    primary_domain = domain

                visit_ref = f"visit_{visit_counter:09d}"
                visit_counter += 1

                intents = ["symptom_advice"]
                if rng.random() < params.p_multi_intent:
                    intents.append("otc_purchase")

                visits_f.write(
                    dumps(
                        {
                            "visit_ref": visit_ref,
                            "patient_ref": patient_ref,
                            "occurred_at": occurred_at,
                            "primary_domain": primary_domain,
                            "intents": intents,
                            "intake_extracted": intake_extracted,
                        }
                    )
                    + "\n"
                )

                write_event(
                    visit_ref=visit_ref,
                    patient_ref=patient_ref,
                    occurred_at=occurred_at,
                    event_type="symptom_intake",
                    payload={"intake_extracted": intake_extracted},
                )
                if "otc_purchase" in intents:
                    items = [
                        {
                            "sku": inv[rng.randrange(len(inv))]["sku"],
                            "qty": int(rng.randint(1, 2)),
                        }
                    ]
                    write_event(
                        visit_ref=visit_ref,
                        patient_ref=patient_ref,
                        occurred_at=occurred_at,
                        event_type="otc_purchase",
                        payload={"items": items},
                    )

            return

        for d in _iter_dates(year):
            dow = d.weekday()
            f_dow = params.dow_factors.get(dow, 1.0)
            if f_dow <= 0:
                continue

            f_month = params.month_factors.get(d.month, 1.0)
            mu = params.mu_base * f_dow * f_month

            n = _poisson(rng, mu) if params.nb_k is None else _neg_binom(rng, mu, params.nb_k)

            for _ in range(n):
                occurred_at = d.isoformat()

                is_new = rng.random() < params.p_new_visit
                if is_new:
                    patient_ref = f"pt_{patient_counter:06d}"
                    patient_counter += 1

                    llm_context = generate_patient(seed=(seed * 100_000) + 1000 + patient_counter)
                    if not isinstance(llm_context.get("schema_version"), str):
                        llm_context["schema_version"] = LLM_CONTEXT_SCHEMA_VERSION

                    patients_f.write(
                        dumps({"patient_ref": patient_ref, "llm_context": llm_context}) + "\n"
                    )
                    patient_refs.append(patient_ref)
                    patient_weights.append(1)
                else:
                    patient_ref = pick_patient_ref()

                visit_ref = f"visit_{visit_counter:09d}"
                visit_counter += 1

                domain = _choice_weighted(rng, _domain_probs_by_month(d.month))
                intake_extracted = _intake_extracted_for_domain(rng, domain=domain)

                intents = ["symptom_advice"]
                if rng.random() < params.p_multi_intent:
                    intents.append("otc_purchase")
                if rng.random() < 0.18:
                    intents.append("prescription_added")

                visits_f.write(
                    dumps(
                        {
                            "visit_ref": visit_ref,
                            "patient_ref": patient_ref,
                            "occurred_at": occurred_at,
                            "primary_domain": domain,
                            "intents": intents,
                            "intake_extracted": intake_extracted,
                        }
                    )
                    + "\n"
                )

                write_event(
                    visit_ref=visit_ref,
                    patient_ref=patient_ref,
                    occurred_at=occurred_at,
                    event_type="symptom_intake",
                    payload={"intake_extracted": intake_extracted},
                )

                if "otc_purchase" in intents:
                    items = [
                        {
                            "sku": inv[rng.randrange(len(inv))]["sku"],
                            "qty": int(rng.randint(1, 3)),
                        }
                    ]
                    write_event(
                        visit_ref=visit_ref,
                        patient_ref=patient_ref,
                        occurred_at=occurred_at,
                        event_type="otc_purchase",
                        payload={"items": items},
                    )

                if "prescription_added" in intents:
                    rx_pool = ["metformin", "levothyroxine", "amlodipine", "atorvastatin"]
                    rx = rng.sample(rx_pool, k=1)
                    write_event(
                        visit_ref=visit_ref,
                        patient_ref=patient_ref,
                        occurred_at=occurred_at,
                        event_type="prescription_added",
                        payload={"rx_medications": rx},
                    )
