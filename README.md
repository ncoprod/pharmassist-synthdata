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

## License
MIT (see `LICENSE`).
