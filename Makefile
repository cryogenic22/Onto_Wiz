# Onto_Wiz Development Makefile
# Usage: make <target>

.PHONY: install install-packages dev test test-packages lint lint-packages boundaries format quality ck clean help

# ─── Setup ───────────────────────────────────────────────────────

install: ## Install all dependencies (editable mode + dev extras)
	pip install -e ".[dev]"
	pre-commit install --install-hooks
	@echo "✓ Installed. Pre-commit hooks active."

install-packages: ## Editable-install the monorepo packages (deps already present)
	pip install -e packages/ontowiz-spec --no-deps
	pip install -e packages/ontowiz-ctx --no-deps
	pip install -e packages/ontowiz-runtime --no-deps
	pip install -e packages/ontowiz-core --no-deps
	pip install -e packages/ontowiz-factory --no-deps
	@echo "✓ Packages installed (editable)."

# ─── Development ─────────────────────────────────────────────────

dev: ## Start backend + frontend dev servers
	@echo "Starting backend on :8000 and frontend on :3000..."
	start /B python -m uvicorn src.api.server:app --reload --port 8000
	cd frontend && npm run dev

backend: ## Start backend only
	python -m uvicorn src.api.server:app --reload --port 8000

frontend: ## Start frontend only
	cd frontend && npm run dev

# ─── Testing ─────────────────────────────────────────────────────

test: ## Run all tests with coverage
	python -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

test-fast: ## Run tests without coverage (faster)
	python -m pytest tests/ -v --tb=short

test-core: ## Run core model tests only
	python -m pytest tests/test_core.py -v

test-api: ## Run API integration tests only
	python -m pytest tests/test_api.py -v

test-reasoning: ## Run reasoning engine tests only
	python -m pytest tests/test_reasoning.py -v

test-gold: ## Run gold-set regression tests only
	python -m pytest tests/ -v -m gold_set

test-coverage: ## Run tests with coverage report and threshold check
	python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html:htmlcov --cov-fail-under=70

test-packages: ## Run monorepo package tests with coverage on our new code (>=85%)
	python -m pytest packages/ -p no:cacheprovider --tb=short \
		--cov=ontowiz_spec --cov=ontowiz_runtime \
		--cov-report=term-missing --cov-fail-under=85

# ─── Code Quality ────────────────────────────────────────────────

lint: ## Run linters (ruff + mypy)
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

format: ## Auto-format code
	ruff format src/ tests/
	ruff check --fix src/ tests/

quality: ## Run quality gate on all files
	python quality-gate/quality_gate.py --root . --report

quality-staged: ## Run quality gate on staged files only (pre-commit mode)
	python quality-gate/quality_gate.py --staged --root .

quality-audit: ## Run quality gate in audit mode (detailed report)
	python quality-gate/quality_gate.py --root . --mode audit --json

# ─── Architecture Governance ─────────────────────────────────────

ck: ## Run Cathedral Keeper full analysis
	python cathedral-keeper/ck.py analyze --root . \
		--out-md .quality-reports/cathedral-keeper/report.md \
		--out-json .quality-reports/cathedral-keeper/report.json

ck-diff: ## Run Cathedral Keeper on changed files only
	python cathedral-keeper/ck.py analyze --root . --mode diff

boundaries: ## Enforce the Tier A -> Tier B IP boundary (must be clean)
	python tools/check_boundaries.py

lint-packages: ## Lint our monorepo packages (ruff + mypy, excludes vendored CTX)
	ruff check packages/ontowiz-spec packages/ontowiz-runtime packages/ontowiz-serve packages/ontowiz-core packages/ontowiz-factory
	mypy packages/ontowiz-spec/ontowiz_spec packages/ontowiz-runtime/ontowiz_runtime --ignore-missing-imports

# ─── Cleanup ─────────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info .coverage coverage.xml

# ─── Help ────────────────────────────────────────────────────────

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
