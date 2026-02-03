.PHONY: help setup lint test gen-sample

PYTHON ?= python3
VENV_DIR := .venv

help:
\t@echo "Targets:"
\t@echo "  setup      - Create venv + install dev deps"
\t@echo "  lint       - Ruff lint"
\t@echo "  test       - Pytest"
\t@echo "  gen-sample - Generate a sample fixture to stdout"

$(VENV_DIR):
\t$(PYTHON) -m venv $(VENV_DIR)

setup: $(VENV_DIR)
\t$(VENV_DIR)/bin/pip install --upgrade pip
\t$(VENV_DIR)/bin/pip install -e ".[dev]"

lint: $(VENV_DIR)
\t$(VENV_DIR)/bin/ruff check src tests

test: $(VENV_DIR)
\t$(VENV_DIR)/bin/pytest -q

gen-sample: $(VENV_DIR)
\t$(VENV_DIR)/bin/pharmassist-synthdata generate --seed 42 --pretty

