.PHONY: help setup lint test gen gen-sample

PYTHON ?= python3
VENV_DIR := .venv

help:
	@echo "Targets:"
	@echo "  setup      - Create venv + install dev deps"
	@echo "  lint       - Ruff lint"
	@echo "  test       - Pytest"
	@echo "  gen        - Generate deterministic fixtures (and validate them)"
	@echo "  gen-sample - Generate a sample fixture to stdout"

$(VENV_DIR):
	$(PYTHON) -m venv $(VENV_DIR)

setup: $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -e ".[dev]"

lint: $(VENV_DIR)
	$(VENV_DIR)/bin/ruff check src tests

test: $(VENV_DIR)
	$(VENV_DIR)/bin/pytest -q

gen-sample: $(VENV_DIR)
	$(VENV_DIR)/bin/pharmassist-synthdata generate --seed 42 --pretty

gen: $(VENV_DIR)
	mkdir -p fixtures
	$(VENV_DIR)/bin/pharmassist-synthdata generate --seed 42 --pretty --out fixtures/seed_000042.json
	$(VENV_DIR)/bin/pharmassist-synthdata validate --in fixtures/seed_000042.json
	$(VENV_DIR)/bin/pharmassist-synthdata generate --seed 43 --pretty --out fixtures/seed_000043.json
	$(VENV_DIR)/bin/pharmassist-synthdata validate --in fixtures/seed_000043.json
	$(VENV_DIR)/bin/pharmassist-synthdata generate --seed 44 --pretty --out fixtures/seed_000044.json
	$(VENV_DIR)/bin/pharmassist-synthdata validate --in fixtures/seed_000044.json
