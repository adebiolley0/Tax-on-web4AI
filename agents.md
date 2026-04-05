# Agents Guide

## Dependency Management

Dependencies are managed by **UV** (`uv`). Do NOT use `pip install` directly.

## Cursor Cloud specific instructions

- **Python version**: The project requires Python >=3.13 (see `.python-version`). UV manages this automatically via `uv sync` / `uv run`.
- **Run the app**: `uv run python main.py`
- **Lint**: No ruff/pytest are configured as project dev-dependencies yet. Use `uvx ruff check .` for linting.
- **Tests**: No test framework is configured in `pyproject.toml` yet. If tests are added, run via `uv run pytest`.
- **No external services required**: The app currently has no database or external service dependencies needed at runtime for development.
