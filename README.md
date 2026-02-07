# pharmassist-synthdata

Realistic **synthetic-only** generators for:
- pharmacy patient profiles (France-first)
- symptoms + intake forms
- OTC/parapharmacy product catalog + inventory snapshots
- OCR-like noisy text derived from structured ground truth (for extraction benchmarks)

Goals:
- zero PHI
- deterministic (seeded) outputs for reproducibility
- clinically coherent constraints (no nonsense records)

Status: scaffolding (implementation coming next).

## Quick start

```bash
make setup
make gen-sample
```

CLI:

```bash
pharmassist-synthdata generate --seed 42 --pretty
```

Pharmacy-year dataset:

```bash
pharmassist-synthdata sim-year --seed 42 --pharmacy paris15 --year 2025 --out ./out
```

Prescription PDF suite (text-layer, deterministic):

```bash
pharmassist-synthdata gen-rx-pdf-suite --seed 42 --out ./out/rx_pdf_suite
```

`--seed` controls the deterministic case set (`seed`, `seed+59`, `seed+60`) and therefore the generated PDF filenames/hashes.

## Validation

```bash
make lint
make test
make gen-rx-pdf-suite
```

## License
MIT (see `LICENSE`).
