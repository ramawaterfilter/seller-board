.PHONY: setup dev test lint migrate
setup:
	uv sync --locked
dev:
	uv run uvicorn app.main:app --app-dir api/src --host 127.0.0.1 --reload
test:
	uv run pytest -q
lint:
	uv run ruff check api/src api/tests api/alembic
migrate:
	uv run alembic -c api/alembic.ini upgrade head
