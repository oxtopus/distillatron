.PHONY: install lint fmt test build up tui kernel notebook docker-build docker-up clean

install:
	uv sync

lint:
	uv run ruff check src tests

fmt:
	uv run ruff format src tests

test:
	uv run pytest -v

build:
	uv run python -m distillatron.ingest

up:
	uv run uvicorn distillatron.main:app --host 127.0.0.1 --port 8000 --reload

tui:
	uv run python -m distillatron.ui.app

kernel:
	uv run ipython kernel install --user --name=distillatron --display-name="Python (distillatron)"

notebook:
	uv run jupyter notebook notebooks/

docker-build:
	docker build -t distillatron -f docker/Dockerfile .

docker-up:
	docker compose -f docker/docker-compose.yml up

clean:
	rm -rf data/ .venv/ __pycache__/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
