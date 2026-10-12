PYTHON := python3
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
	$(BACKEND) .venv/bin/uvicorn app.main:app --workers 1

run-pipeline: export PIPELINE_TEXT = $(TEXT)
run-pipeline:
	$(BACKEND) .venv/bin/python scripts/run_pipeline.py

test test-perf migrate-test: export PYTHONPATH := $(abspath backend/tests/bootstrap):$(abspath backend):$(PYTHONPATH)

test test-perf: export LLM_PROVIDER := stub
test test-perf: export LLM_MODEL :=
test test-perf: export LLM_API_KEY :=
test test-perf: export API_KEY :=
test test-perf: export LLM_REASONING_EFFORT :=
test test-perf: export LLM_RESPONSE_FORMAT :=
test test-perf: export LLM_PROMPT_CACHE := off
test test-perf: export LLM_BASE_URL :=
test test-perf: export SECURITY_FIX_PROVIDER :=
test test-perf: export SECURITY_FIX_MODEL :=
test test-perf: export SECURITY_FIX_REASONING_EFFORT :=

test: migrate-test
	$(BACKEND) .venv/bin/pytest -q -m "not perf"

test-perf: migrate-test
	$(BACKEND) .venv/bin/pytest -q -m perf

lint:
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
	$(FRONTEND) npm run test:e2e

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
