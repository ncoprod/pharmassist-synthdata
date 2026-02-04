from __future__ import annotations

import random
import re
import unicodedata
from typing import Any, Literal


def _strip_accents(text: str) -> str:
    # OCR outputs often lose accents; keep output mostly ASCII for reproducible parsing.
    norm = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in norm if not unicodedata.combining(ch))


def render_intake_text(bundle: dict[str, Any], language: Literal["fr", "en"]) -> str:
    """Render a PHI-free intake text (note-like) from structured synthetic ground truth."""
    llm_context = bundle.get("llm_context") or {}
    intake = bundle.get("intake_extracted") or {}

    demographics = llm_context.get("demographics") or {}
    age = demographics.get("age_years", "?")
    sex = demographics.get("sex", "?")

    presenting = str(intake.get("presenting_problem") or "").strip()
    symptoms = intake.get("symptoms") or []

    # Small deterministic localization for our current templates (keeps FR demo coherent).
    fr_presenting_map = {
        "Sneezing and itchy eyes for one week": (
            "Eternuements et yeux qui grattent depuis 1 semaine"
        ),
        "Dry skin and mild itching": "Peau seche et demangeaisons legeres",
        "Occasional bloating after meals": "Ballonnements occasionnels apres les repas",
        "Dyspnea and chest pain": "Essoufflement et douleur thoracique",
        "Unspecified symptom": "Symptome non specifie",
    }
    if language == "fr" and presenting in fr_presenting_map:
        presenting = fr_presenting_map[presenting]

    lines: list[str] = []
    if language == "fr":
        lines.append("NOTE PATIENT (OCR)")
        lines.append(f"Age: {age} ans")
        lines.append(f"Sexe: {sex}")
        if presenting:
            lines.append(f"Motif: {presenting}")
        lines.append("Symptomes:")
    else:
        lines.append("PATIENT NOTE (OCR)")
        lines.append(f"Age: {age} years")
        lines.append(f"Sex: {sex}")
        if presenting:
            lines.append(f"Chief complaint: {presenting}")
        lines.append("Symptoms:")

    # Symptoms list (kept simple so A1 can parse it reliably).
    for s in symptoms:
        if not isinstance(s, dict):
            continue
        label = str(s.get("label") or "").strip()
        if not label:
            continue

        sev = str(s.get("severity") or "unknown")
        dur = s.get("duration_days")
        if isinstance(dur, int):
            dur_part = f"{dur}d" if language == "en" else f"{dur}j"
        else:
            dur_part = "?"

        lines.append(f"- {label} ({sev}, {dur_part})")

    # Minimal contextual block (still PHI-free).
    allergies = llm_context.get("allergies") or []
    conditions = llm_context.get("conditions") or []
    meds = llm_context.get("current_medications") or []

    if language == "fr":
        lines.append("Contexte:")
        if allergies:
            lines.append("Allergies: " + ", ".join(_compact_allergy(a) for a in allergies))
        if conditions:
            lines.append("Antecedents: " + ", ".join(_compact_label(c) for c in conditions))
        if meds:
            lines.append("Traitements: " + ", ".join(_compact_med(m) for m in meds))
    else:
        lines.append("Context:")
        if allergies:
            lines.append("Allergies: " + ", ".join(_compact_allergy(a) for a in allergies))
        if conditions:
            lines.append("Conditions: " + ", ".join(_compact_label(c) for c in conditions))
        if meds:
            lines.append("Current meds: " + ", ".join(_compact_med(m) for m in meds))

    return "\n".join(lines).strip() + "\n"


def apply_ocr_noise(
    text: str, seed: int, level: Literal["mild", "medium", "hard"] = "medium"
) -> str:
    """Apply deterministic OCR-like noise. This is intentionally simple and reproducible."""
    rng = random.Random(seed)
    base = _strip_accents(text)

    # Reduce excessive whitespace first (OCR tends to create odd spacing later).
    base = re.sub(r"[ \t]+", " ", base)

    if level == "mild":
        p_drop, p_swap, p_dup, p_space, p_nl = 0.01, 0.02, 0.005, 0.01, 0.005
    elif level == "hard":
        p_drop, p_swap, p_dup, p_space, p_nl = 0.05, 0.08, 0.02, 0.03, 0.02
    else:
        p_drop, p_swap, p_dup, p_space, p_nl = 0.02, 0.04, 0.01, 0.02, 0.01

    swap_map = {
        "o": "0",
        "O": "0",
        "l": "1",
        "I": "1",
        "i": "1",
        "s": "5",
        "S": "5",
        "e": "3",
        "E": "3",
    }

    out: list[str] = []
    for ch in base:
        # Skip some chars.
        if rng.random() < p_drop and ch not in "\n":
            continue

        # Swap some chars.
        if ch in swap_map and rng.random() < p_swap:
            ch = swap_map[ch]

        out.append(ch)

        # Duplicate (rare).
        if rng.random() < p_dup and ch.isalnum():
            out.append(ch)

        # Insert odd spacing/newlines.
        if rng.random() < p_nl:
            out.append("\n")
        elif rng.random() < p_space:
            out.append(" " if rng.random() < 0.7 else "  ")

    noisy = "".join(out)
    noisy = re.sub(r"\n{3,}", "\n\n", noisy)
    noisy = re.sub(r"[ \t]{3,}", "  ", noisy)

    # Guard rails: ensure non-empty and sane size.
    noisy = noisy.strip()
    if len(noisy) < 20:
        noisy = base.strip()
    if len(noisy) > 4000:
        noisy = noisy[:4000]

    return noisy + "\n"


def generate_intake_text_ocr(seed: int, bundle: dict[str, Any]) -> dict[str, str]:
    """Generate deterministic FR/EN OCR-like texts aligned with a synthetic case bundle."""
    fr_clean = render_intake_text(bundle, language="fr")
    en_clean = render_intake_text(bundle, language="en")

    return {
        "fr": apply_ocr_noise(fr_clean, seed=seed * 10 + 1, level="medium"),
        "en": apply_ocr_noise(en_clean, seed=seed * 10 + 2, level="medium"),
    }


def _compact_label(obj: Any) -> str:
    if isinstance(obj, dict):
        label = obj.get("label")
        if isinstance(label, str) and label.strip():
            return label.strip()
    return "unknown"


def _compact_allergy(obj: Any) -> str:
    if isinstance(obj, dict):
        substance = str(obj.get("substance") or "").strip()
        reaction = str(obj.get("reaction") or "").strip()
        if substance and reaction:
            return f"{substance} ({reaction})"
        if substance:
            return substance
    return "unknown"


def _compact_med(obj: Any) -> str:
    if isinstance(obj, dict):
        name = str(obj.get("name") or "").strip()
        is_rx = obj.get("is_prescription")
        if name:
            return f"{name} ({'Rx' if is_rx else 'OTC'})" if isinstance(is_rx, bool) else name
    return "unknown"
