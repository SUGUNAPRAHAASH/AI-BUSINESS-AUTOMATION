.PHONY: up down logs seed test demo lint clean

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f

seed:
	python scripts/seed_knowledge_base.py

test:
	pytest services/ai/tests -v

demo:
	python scripts/simulate_all.py

lint:
	ruff check . || true

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
