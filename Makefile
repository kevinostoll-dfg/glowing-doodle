.PHONY: dev test lint format migrate seed build

dev:
	docker-compose up --build

test:
	pytest tests/ -v --tb=short --cov=shared --cov=services

lint:
	ruff check .
	mypy shared/

format:
	ruff format .
	ruff check --fix .

migrate:
	alembic upgrade head

seed:
	python -m scripts.seed_shops

build:
	docker-compose build
