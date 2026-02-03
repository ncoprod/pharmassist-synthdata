from __future__ import annotations

import argparse
import json
import sys

from .generate import generate_case


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pharmassist-synthdata")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="Generate a deterministic synthetic case bundle (JSON).")
    gen.add_argument("--seed", type=int, default=0, help="Deterministic seed.")
    gen.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    gen.add_argument("--out", type=lambda p: __import__("pathlib").Path(p), help="Write output to file.")
    gen.set_defaults(func=_cmd_generate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

