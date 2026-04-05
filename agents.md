# Agents Guide

## Dependency Management

Dependencies are managed by **UV** (`uv`). Do NOT use `pip install` directly.

- Add dependencies: `uv add <package>`
- Remove dependencies: `uv remove <package>`
- Sync/install all deps: `uv sync`
- Run a script: `uv run python <script.py>`
- The virtual environment is at `.venv/`; activate with `source .venv/bin/activate` or prefix commands with `uv run`
