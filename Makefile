-include .env
export

.PHONY: up down init-db install ingest-last-hour ingest-last-24h ingest-sample-hour psql status

up:
	docker compose up -d

down:
	docker compose down

install:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

init-db:
	docker compose exec -T postgres psql -U "$${POSTGRES_USER:-github}" -d "$${POSTGRES_DB:-github_dw_analysis}" -f /dev/stdin < sql/schema/001_create_github_event.sql
	docker compose exec -T postgres psql -U "$${POSTGRES_USER:-github}" -d "$${POSTGRES_DB:-github_dw_analysis}" -f /dev/stdin < sql/metrics/github_event_metrics.sql

ingest-last-hour:
	.venv/bin/python scripts/ingest_github_archive.py --last-hours 1

ingest-last-24h:
	.venv/bin/python scripts/ingest_github_archive.py --last-hours 24

ingest-sample-hour:
	.venv/bin/python scripts/ingest_github_archive.py --hour 2024-01-01-0

psql:
	docker compose exec postgres psql -U "$${POSTGRES_USER:-github}" -d "$${POSTGRES_DB:-github_dw_analysis}"

status:
	docker compose ps
