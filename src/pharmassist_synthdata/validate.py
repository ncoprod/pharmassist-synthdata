from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator

from .contracts import load_schema_by_name, schema_registry


@dataclass(frozen=True)
class SchemaIssue:
    schema_name: str
    json_path: str
    message: str


def validate_instance(instance: Any, *, schema_name: str) -> list[SchemaIssue]:
    schema = load_schema_by_name(schema_name)
    validator = Draft202012Validator(schema, registry=schema_registry())

    issues: list[SchemaIssue] = []
    for err in sorted(validator.iter_errors(instance), key=lambda e: str(e.json_path)):
        issues.append(
            SchemaIssue(
                schema_name=schema_name,
                json_path=str(err.json_path),
                message=err.message,
            )
        )
    return issues


def validate_case_bundle(bundle: dict[str, Any]) -> list[SchemaIssue]:
    issues: list[SchemaIssue] = []

    # Internal contract (not a shared JSON Schema): OCR-like text used to test extraction.
    intake_text_ocr = bundle.get("intake_text_ocr")
    if isinstance(intake_text_ocr, dict):
        fr = intake_text_ocr.get("fr")
        en = intake_text_ocr.get("en")
        if not (isinstance(fr, str) and fr.strip()):
            issues.append(
                SchemaIssue(
                    schema_name="intake_text_ocr",
                    json_path="$.intake_text_ocr.fr",
                    message="Missing or invalid FR intake_text_ocr (expected non-empty string)",
                )
            )
        if not (isinstance(en, str) and en.strip()):
            issues.append(
                SchemaIssue(
                    schema_name="intake_text_ocr",
                    json_path="$.intake_text_ocr.en",
                    message="Missing or invalid EN intake_text_ocr (expected non-empty string)",
                )
            )
    else:
        issues.append(
            SchemaIssue(
                schema_name="intake_text_ocr",
                json_path="$.intake_text_ocr",
                message="Missing or invalid intake_text_ocr object",
            )
        )

    llm_context = bundle.get("llm_context")
    if isinstance(llm_context, dict):
        issues.extend(validate_instance(llm_context, schema_name="llm_context"))
    else:
        issues.append(
            SchemaIssue(
                schema_name="llm_context",
                json_path="$.llm_context",
                message="Missing or invalid llm_context object",
            )
        )

    intake_extracted = bundle.get("intake_extracted")
    if isinstance(intake_extracted, dict):
        issues.extend(validate_instance(intake_extracted, schema_name="intake_extracted"))
    else:
        issues.append(
            SchemaIssue(
                schema_name="intake_extracted",
                json_path="$.intake_extracted",
                message="Missing or invalid intake_extracted object",
            )
        )

    products = bundle.get("products")
    if isinstance(products, list):
        for idx, p in enumerate(products):
            if not isinstance(p, dict):
                issues.append(
                    SchemaIssue(
                        schema_name="product",
                        json_path=f"$.products[{idx}]",
                        message="Invalid product item (expected object)",
                    )
                )
                continue
            issues.extend(validate_instance(p, schema_name="product"))
    else:
        issues.append(
            SchemaIssue(
                schema_name="product",
                json_path="$.products",
                message="Missing or invalid products list",
            )
        )

    return issues
