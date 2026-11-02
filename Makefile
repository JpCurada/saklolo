.PHONY: help install fmt lint test eval demo plan notebooks video-capture

API := api
WEB := web
INFRA := infra
VIDEO := video

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Install API and web dependencies
	cd $(API) && uv sync
	@if [ -f $(WEB)/package.json ]; then cd $(WEB) && npm install; fi

fmt: ## Format all code
	cd $(API) && uv run ruff format . && uv run ruff check --fix .
	terraform -chdir=$(INFRA) fmt -recursive
	@if [ -f $(WEB)/package.json ]; then cd $(WEB) && npm run format; fi

lint: ## Lint and type-check all code
	cd $(API) && uv run ruff format --check . && uv run ruff check . && uv run mypy src
	cd $(API) && uv run ruff check --config pyproject.toml ../notebooks
	terraform -chdir=$(INFRA) fmt -check -recursive
	terraform -chdir=$(INFRA) validate
	@if [ -f $(WEB)/package.json ]; then cd $(WEB) && npm run lint && npm run typecheck; fi

test: ## Unit tests (no network, no AWS)
	cd $(API) && uv run pytest

eval: ## Run evals against Bedrock (costs money)
	cd $(API) && uv run python -m saklolo.eval --split eval --out ../eval/runs

demo: ## Local end-to-end demo with synthetic data
	cd $(API) && uv run python -m saklolo.demo

plan: ## terraform plan for infra/
	terraform -chdir=$(INFRA) init -backend-config=backend.hcl
	terraform -chdir=$(INFRA) plan -var-file=terraform.tfvars

notebooks: ## Install notebook dependencies into api/.venv
	cd $(API) && uv sync --group notebooks

video-capture: ## Record product footage with Playwright (run `make demo` first)
	cd $(VIDEO) && npx playwright test
