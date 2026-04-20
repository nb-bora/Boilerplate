.PHONY: help dev run lint format test test-unit test-int audit migrate seed

UV := $(shell where uv 2>NUL)
ifeq ($(UV),)
RUN := python -m
else
RUN := uv run
endif

help: ## Affiche les commandes disponibles
	@echo "Targets:"
	@echo "  dev      - Lance l'API en dev (hot reload)"
	@echo "  run      - Lance l'API en mode run"
	@echo "  lint     - Ruff lint"
	@echo "  format   - Ruff format"
	@echo "  test     - Pytest"
	@echo "  test-unit - Tests unitaires"
	@echo "  test-int  - Tests d'integration (Testcontainers)"
	@echo "  audit    - Audit deps (pip-audit)"
	@echo "  migrate  - Alembic upgrade head"
	@echo "  seed     - (placeholder) seeds dev"

dev: ## Lance l'API en dev (hot reload)
	@if not "$(UV)"=="" (uv sync) else (python -m pip install -r requirements-dev.txt)
	fastapi dev app/main.py --host 0.0.0.0 --port 8000

run: ## Lance l'API en mode run
	@if not "$(UV)"=="" (uv sync) else (python -m pip install -r requirements.txt)
	fastapi run app/main.py --host 0.0.0.0 --port 8000

lint: ## Ruff lint
	$(RUN) ruff check .

format: ## Ruff format
	$(RUN) ruff format .

test: ## Pytest
	$(RUN) pytest

test-unit: ## Tests unitaires (sans infra)
	$(RUN) pytest tests/unit

test-int: ## Tests d'integration (Testcontainers)
	$(RUN) pytest tests/integration

audit: ## pip-audit (vulnérabilités deps)
	python -m pip install pip-audit
	python -m pip_audit

migrate: ## Alembic upgrade head
	$(RUN) alembic upgrade head

seed: ## Seeds dev (placeholder)
	@echo "TODO: add scripts/seeds/v1/dev.py"
