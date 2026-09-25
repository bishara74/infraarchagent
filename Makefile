PYTHON := python3
VENV := backend/.venv
BACKEND := cd backend &&

.PHONY: up down install migrate migrate-test run test lint sweep

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
	$(BACKEND) .venv/bin/uvicorn app.main:app --reload

test: migrate-test
	$(BACKEND) .venv/bin/pytest -q

lint:
	$(BACKEND) .venv/bin/ruff check app tests
	$(BACKEND) .venv/bin/ruff format --check app tests
	$(BACKEND) .venv/bin/mypy app

sweep:
	$(BACKEND) .venv/bin/python -m app.cli sweep-packages
