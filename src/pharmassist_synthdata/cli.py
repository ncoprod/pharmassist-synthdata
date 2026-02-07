from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .generate import generate_case
from .prescription_pdf import generate_prescription_pdf_suite
from .sim_year import generate_pharmacy_year
from .validate import validate_case_bundle


def _cmd_generate(args: argparse.Namespace) -> int:
    payload = generate_case(seed=args.seed)

    if args.pretty:
        out = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    else:
        out = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    if args.out:
        args.out.write_text(out + "\n", encoding="utf-8")
    else:
        sys.stdout.write(out + "\n")

    return 0


def _cmd_sim_year(args: argparse.Namespace) -> int:
    generate_pharmacy_year(
        seed=args.seed,
        pharmacy=args.pharmacy,
        year=args.year,
        out_dir=args.out,
        mode=args.mode,
    )
    sys.stdout.write(f"OK: wrote dataset to {args.out}\n")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    payload = json.loads(args.in_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        sys.stderr.write("Input must be a JSON object\n")
        return 1

    issues = validate_case_bundle(payload)
    if issues:
        for i in issues:
            sys.stderr.write(f"[INVALID] {i.schema_name} {i.json_path}: {i.message}\n")
        return 1

    sys.stdout.write("OK\n")
    return 0


def _cmd_gen_rx_pdf_suite(args: argparse.Namespace) -> int:
    manifest = generate_prescription_pdf_suite(
        out_dir=args.out,
        seed=args.seed,
    )
    sys.stdout.write(
        f"OK: wrote {len(manifest.get('files') or [])} PDFs + manifest to {args.out}\n"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pharmassist-synthdata")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="Generate a deterministic synthetic case bundle (JSON).")
    gen.add_argument("--seed", type=int, default=0, help="Deterministic seed.")
    gen.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    gen.add_argument("--out", type=Path, help="Write output to file.")
    gen.set_defaults(func=_cmd_generate)

    sim = sub.add_parser(
        "sim-year",
        help="Generate a synthetic 1-year pharmacy dataset (JSONL.gz).",
    )
    sim.add_argument("--seed", type=int, default=0, help="Deterministic seed.")
    sim.add_argument(
        "--pharmacy",
        type=str,
        default="paris15",
        help="Pharmacy preset (v1: paris15).",
    )
    sim.add_argument("--year", type=int, default=2025, help="Calendar year to simulate (YYYY).")
    sim.add_argument(
        "--mode",
        type=str,
        choices=["full", "mini"],
        default="full",
        help="Dataset size preset (full=year simulation, mini=CI subset).",
    )
    sim.add_argument("--out", type=Path, required=True, help="Output directory.")
    sim.set_defaults(func=_cmd_sim_year)

    val = sub.add_parser("validate", help="Validate a case bundle JSON against vendored schemas.")
    val.add_argument("--in", dest="in_path", type=Path, required=True, help="Input JSON file.")
    val.set_defaults(func=_cmd_validate)

    pdf = sub.add_parser(
        "gen-rx-pdf-suite",
        help="Generate deterministic synthetic prescription PDFs (text-layer) + manifest.",
    )
    pdf.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic base seed used to derive suite case seeds.",
    )
    pdf.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for PDFs + manifest.",
    )
    pdf.set_defaults(func=_cmd_gen_rx_pdf_suite)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
