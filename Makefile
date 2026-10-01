PYTHON := python3
VENV := backend/.venv
BACKEND := cd backend &&

.PHONY: up down install migrate migrate-test run run-pipeline test lint sweep spike eval-architect eval-generators eval-security

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

test: migrate-test
	$(BACKEND) .venv/bin/pytest -q

lint:
	$(BACKEND) .venv/bin/ruff check app tests
	$(BACKEND) .venv/bin/ruff format --check app tests
	$(BACKEND) .venv/bin/mypy app

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
