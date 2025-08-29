.PHONY: help dev run ingest prewarm diag test clean test-places smoke-places test-redis ci-places run-factory kill-port

PORT ?= 8000

help: ## Show this help message
	@echo "Week Planner - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Install packages in editable mode
	.venv/bin/pip install -e packages/wp_core -e packages/wp_models -e packages/wp_cache -e packages/wp_tags -e packages/wp_events -e packages/wp_places -e packages/wp_services -e packages/wp_extract

run: ## Start the FastAPI server using app factory
	python -m apps.api

kill-port: ## Kill processes on specified port
	lsof -ti:$(PORT) | xargs kill -9 || true

# DEPRECATED: Old run-factory command
run-factory: ## Start the FastAPI server using app factory (DEPRECATED)
	.venv/bin/uvicorn apps.api.app_factory:create_app --factory --reload

ingest: ## Run event ingestion
	.venv/bin/python apps/cli/ingest_events.py --days-ahead 14 --days-back 7 --city bangkok

prewarm: ## Run cache prewarming
	.venv/bin/python apps/cli/prewarm.py

diag: ## Run diagnostics
	.venv/bin/python apps/cli/diag_verify.py --date $(shell date +%F) --days 7 --flags "markets,food_dining"

test: ## Run unit tests
	python3 -m pytest -q tests/app/test_shutdown_simple.py tests/cache/test_cache_simple.py tests/app/test_port_conflict_simple.py tests/test_integration_complete.py

warm-cache: ## Warm up cache with sample requests
	curl -s "http://localhost:$(PORT)/api/places/recommend?mood=lazy_outdoor" >/dev/null || true
	curl -s "http://localhost:$(PORT)/api/places/recommend?mood=relaxed" > /dev/null || true
	curl -s "http://localhost:$(PORT)/api/places/recommend?mood=energetic" > /dev/null || true
	curl -s "http://localhost:$(PORT)/api/places/recommend?mood=romantic" > /dev/null || true
	@echo "Cache warmed up with sample requests"

lint: ## ruff/mypy/pyright (what you use)
	@echo "Checking for ruff..."
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check .; \
		echo "Linting completed with ruff"; \
	elif command -v black >/dev/null 2>&1; then \
		black --check packages/ tests/ || true; \
		echo "Linting completed with black"; \
	else \
		echo "⚠️ No linting tools found (ruff/black)"; \
		echo "Install with: pip install ruff or pip install black"; \
	fi

guard: ## block deprecated
	@FOUND=$$(git ls-files | grep -E '(DEPRECATED_.*\.py|^core/|^src/)' | grep -v '^archive/' || true); \
	if [ -n "$$FOUND" ]; then echo "❌ Deprecated found:"; echo "$$FOUND"; exit 1; fi

dev-test: ## Quick development test run
	python3 -m pytest -q tests/app/test_shutdown_simple.py tests/app/test_port_conflict_simple.py tests/test_integration_complete.py

dev-run: ## Start dev server with auto-reload
	python3 -m apps.api --reload

start-server: ## Start server in background (always running)
	@./start_server.sh

stop-server: ## Stop background server
	@echo "🛑 Останавливаю сервер..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "Сервер не запущен"
	@echo "✅ Сервер остановлен"

check: ## Quick health check
	curl -s "http://localhost:$(PORT)/health" || echo "Server not running on port $(PORT)"

format: ## Format code with black
	python3 -m black packages/ tests/

test-verbose: ## Run tests with verbose output
	.venv/bin/pytest -v

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

install-deps: ## Install dependencies
	.venv/bin/pip install -r requirements.txt

setup-env: ## Setup environment variables
	source setup_env.sh

full-setup: setup-env install-deps dev ## Full setup: env + deps + dev packages

test-places: ## Test Places functionality with events disabled
	WP_DISABLE_EVENTS=1 python3 -m pytest -q -k "places or redis or flags" --ignore-glob="tests/e2e/*" --ignore-glob="tests/test_*.py" --ignore-glob="test_*.py" --ignore="tests/unit/test_places_single_api.py" --ignore="tests/unit/test_places_cache_wrapper.py"

test-redis: ## Test Redis functionality with events disabled
	WP_DISABLE_EVENTS=1 python3 -m pytest -q -k "redis or circuit_breaker" --ignore-glob="tests/e2e/*" --ignore-glob="tests/test_*.py" --ignore-glob="test_*.py" --ignore="tests/unit/test_places_single_api.py"

ci-places: ## CI: Run all safe Places tests with events disabled
	WP_DISABLE_EVENTS=1 python3 -m pytest -q -k "places or redis or flags" --ignore-glob="tests/e2e/*" --ignore-glob="tests/test_*.py" --ignore-glob="test_*.py" --ignore="tests/unit/test_places_single_api.py" --ignore="tests/unit/test_places_cache_wrapper.py"

smoke-places: ## Smoke test Places functionality with events disabled
	WP_DISABLE_EVENTS=1 python3 -c "from packages.wp_places.service import PlacesService; from packages.wp_tags import mapper; s = PlacesService(); assert s is not None; cats = mapper.flags_canonical; assert len(cats) >= 6; print('SMOKE OK: PlacesService + tags')"
