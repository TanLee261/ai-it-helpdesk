.PHONY: backend-dev backend-test db-up db-down db-upgrade seed-tickets

backend-dev:
	cd backend && uvicorn app.main:app --reload

backend-test:
	cd backend && pytest

db-up:
	docker compose -f infra/docker-compose.yml up -d postgres

db-down:
	docker compose -f infra/docker-compose.yml down

db-upgrade:
	cd backend && alembic upgrade head

seed-tickets:
	python3 scripts/seed_db.py
