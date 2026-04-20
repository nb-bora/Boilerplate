.PHONY: help dev run lint format test

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
