.PHONY: verify browser demo serve worker
verify:
	uv lock --check
	uv sync --frozen
	uv run python manage.py check
	uv run python manage.py makemigrations --check --dry-run
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy config investigations
	uv run pytest
	uv run python manage.py evaluate
browser:
	RUN_BROWSER=1 uv run pytest tests/test_browser.py -q
demo:
	uv run python manage.py demo
serve:
	uv run python manage.py runserver 127.0.0.1:8103 --noreload
worker:
	uv run python manage.py worker
