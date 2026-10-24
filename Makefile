PYTHON := python3
PORT ?= 8000
HOST ?= 127.0.0.1
VENV := backend/.venv
BACKEND := cd backend &&
FRONTEND := cd frontend &&

.PHONY: up down install migrate migrate-test run run-pipeline test test-perf lint sweep spike eval-architect eval-generators eval-security eval-validation
.PHONY: frontend-install frontend-dev frontend-build frontend-test test-e2e

up:
	docker compose up -d --wait

down:
	docker compose down

install:
	$(PYTHON) -m venv $(VENV)
	$(BACKEND) .venv/bin/python -m pip install -c requirements.lock -e ".[dev]"

migrate:
	$(BACKEND) .venv/bin/alembic upgrade head

migrate-test:
	$(BACKEND) .venv/bin/alembic -x database=test upgrade head

run:
	$(BACKEND) .venv/bin/python -m app.server --host $(HOST) --port $(PORT)

run-pipeline: export PIPELINE_TEXT = $(TEXT)
run-pipeline:
	$(BACKEND) .venv/bin/python scripts/run_pipeline.py

test: migrate-test
	$(BACKEND) .venv/bin/python -m scripts.run_verification pytest -q -m "not perf"

test-perf:
	$(BACKEND) .venv/bin/python -m scripts.measure_performance backend

lint:
	$(BACKEND) .venv/bin/ruff check scripts/phase9*.py scripts/traceability.py scripts/pytest_traceability.py scripts/secret_scan.py scripts/benchmark.py scripts/provider_schema.py scripts/seed_benchmark_package.py scripts/measure_performance.py scripts/run_phase9_benchmarks.py
	$(BACKEND) .venv/bin/ruff format --check scripts/phase9*.py scripts/traceability.py scripts/pytest_traceability.py scripts/secret_scan.py scripts/benchmark.py scripts/provider_schema.py scripts/seed_benchmark_package.py scripts/measure_performance.py scripts/run_phase9_benchmarks.py
	$(BACKEND) .venv/bin/ruff check app tests
	$(BACKEND) .venv/bin/ruff format --check app tests
	$(BACKEND) .venv/bin/mypy app
	$(FRONTEND) npm run lint

frontend-install:
	$(FRONTEND) npm ci --ignore-scripts

frontend-dev:
	$(FRONTEND) npm run dev

frontend-build:
	$(FRONTEND) npm run build

frontend-test:
	$(FRONTEND) npm test

test-e2e:
	$(BACKEND) .venv/bin/python -m scripts.run_verification e2e

sweep:
	$(BACKEND) .venv/bin/python -m app.cli sweep-packages

spike:
	$(BACKEND) .venv/bin/python scripts/spike_llm_timing.py $(SPIKE_ARGS)

eval-architect:
	$(BACKEND) .venv/bin/python scripts/eval_architect.py $(EVAL_ARGS)

eval-generators:
	$(BACKEND) .venv/bin/python scripts/eval_generators.py $(EVAL_ARGS)

eval-security:
	$(BACKEND) .venv/bin/python scripts/eval_security.py $(EVAL_ARGS)

eval-validation:
	$(BACKEND) .venv/bin/python -m scripts.eval_validation $(EVAL_ARGS)

.PHONY: providers
providers:
	$(BACKEND) .venv/bin/python -m scripts.mirror_providers

.PHONY: provider-schema
provider-schema:
	$(BACKEND) .venv/bin/python -m scripts.provider_schema

.PHONY: traceability
traceability:
	$(BACKEND) .venv/bin/python -m scripts.traceability

.PHONY: secret-scan
secret-scan:
	$(BACKEND) .venv/bin/python -m scripts.secret_scan

.PHONY: benchmark
benchmark:
	$(BACKEND) .venv/bin/python -m scripts.benchmark $(BENCH_ARGS)

.PHONY: test-ui-perf
test-ui-perf:
	$(BACKEND) .venv/bin/python -m scripts.measure_performance ui

BASE_URL ?= http://127.0.0.1:8000
RUNS_PER_SCENARIO ?= 2
MODE ?= real
.PHONY: bench-broad
bench-broad: export PHASE9_BASE_URL = $(BASE_URL)
bench-broad: export PHASE9_BUDGET = $(BUDGET)
bench-broad: export PHASE9_RUNS_PER_SCENARIO = $(RUNS_PER_SCENARIO)
bench-broad: export PHASE9_ARCHITECT_MODEL = $(ARCHITECT_MODEL)
bench-broad: export PHASE9_ARCHITECT_THINKING = $(ARCHITECT_THINKING)
bench-broad: export PHASE9_PROVIDER_PREFERENCE = $(PROVIDER_PREFERENCE)
bench-broad: export PHASE9_ARCHITECT_PROVIDER_PREFERENCE = $(ARCHITECT_PROVIDER_PREFERENCE)
bench-broad: export PHASE9_FORCE = $(FORCE)
bench-broad:
	$(BACKEND) .venv/bin/python -m scripts.run_phase9_benchmarks $(MODE) --broad

.PHONY: catalogue-snapshot catalogue-inspect experiment-estimate
catalogue-snapshot: export PHASE9_CATALOGUE_MODELS = $(CATALOGUE_MODELS)
catalogue-snapshot:
	$(BACKEND) .venv/bin/python -m scripts.phase9k_catalogue snapshot

catalogue-inspect:
	$(BACKEND) .venv/bin/python -m scripts.phase9k_catalogue inspect

experiment-estimate: export ARCHITECT_MODEL := $(ARCHITECT_MODEL)
experiment-estimate: export ARCHITECT_PROVIDER_PREFERENCE := $(ARCHITECT_PROVIDER_PREFERENCE)
experiment-estimate:
	$(BACKEND) .venv/bin/python -m scripts.phase9k_catalogue estimate

.PHONY: bench-stub bench-real
bench-stub: export PHASE9_BASE_URL = $(BASE_URL)
bench-stub: export PHASE9_MAX_RUNS = $(MAX_RUNS)
bench-stub: export PHASE9_BUDGET = $(BUDGET)
bench-stub:
	$(BACKEND) .venv/bin/python -m scripts.run_phase9_benchmarks stub

bench-real: export PHASE9_BASE_URL = $(BASE_URL)
bench-real: export PHASE9_MAX_RUNS = $(MAX_RUNS)
bench-real: export PHASE9_BUDGET = $(BUDGET)
bench-real:
	$(BACKEND) .venv/bin/python -m scripts.run_phase9_benchmarks real

.PHONY: bench-smoke
bench-smoke: export PHASE9_BASE_URL = $(BASE_URL)
bench-smoke: export PHASE9_BUDGET = $(BUDGET)
bench-smoke: export PHASE9_MAX_RUNS = $(MAX_RUNS)
bench-smoke:
	$(BACKEND) .venv/bin/python -m scripts.run_phase9_benchmarks real --smoke

.PHONY: rotate-credential-key
rotate-credential-key:
	$(BACKEND) .venv/bin/python -m scripts.rotate_credential_key

.PHONY: db-tools prepare-db-tools
prepare-db-tools:
	docker compose exec -T postgres sh /docker-entrypoint-initdb.d/02-inspection-role.sh

db-tools:
	docker compose --profile tools up -d --pull never pgadmin

.PHONY: eval-report
eval-report:
	$(BACKEND) .venv/bin/python -m scripts.phase9b_report $(EVAL_REPORT_ARGS)
