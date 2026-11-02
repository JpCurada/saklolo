.PHONY: help install fmt lint test eval demo demo-offline demo-web plan api-types tokens ui-check hooks notebooks

API := api
WEB := web
INFRA := infra

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

demo: ## Local demo API on :8000 (cached model calls); POST /replay to load the dev split
	cd $(API) && uv run python -m saklolo.handlers.demo_api --call-cache

demo-offline: ## Demo API without AWS: recorded calls from demo/cache
	cd $(API) && uv run python -m saklolo.handlers.demo_api --offline

demo-web: ## Dashboard on :3000 with the demo tools (replay, /resident phones)
	cd $(WEB) && NEXT_PUBLIC_DEMO_MODE=true npm run build && npx next start --port 3000

plan: ## terraform plan for infra/
	terraform -chdir=$(INFRA) init -backend-config=backend.hcl
	terraform -chdir=$(INFRA) plan -var-file=terraform.tfvars

ui-check: ## Lint, types, tokens, build, screenshots, visual regression
	cd $(WEB) && npm run ui:check

hooks: ## Enable the repo's git hooks in this clone
	git config core.hooksPath .githooks

tokens: ## Build design tokens and check WCAG AA contrast
	cd $(WEB) && npm run tokens

api-types: ## Regenerate the web client's types from the API schema
	cd $(API) && uv run python -m saklolo.handlers.openapi_export ../$(WEB)/lib/api/openapi.json
	cd $(WEB) && npm run gen:api

notebooks: ## Install notebook dependencies into api/.venv
	cd $(API) && uv sync --group notebooks
