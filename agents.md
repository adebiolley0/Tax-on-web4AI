# Agents Guide

## SDKs and documentation

When working with SDKs or libraries, always consult the **latest official documentation** for the version in use (for example [FastMCP](https://gofastmcp.com/) and the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)) rather than relying only on older examples or memory.

## Dependency Management

Dependencies are managed by **UV** (`uv`). Do NOT use `pip install` directly.

## Playwright (crawl4ai)

Crawl4ai uses Playwright's Chromium. After `uv sync`, install browser binaries once:

```bash
uv run playwright install chromium
```

Use `uv run playwright install` if you need all bundled browsers. Without this step, crawls fail with "Executable doesn't exist" under `~/.cache/ms-playwright/`.

## Cursor Cloud specific instructions

### Services overview

The main service is a **FastMCP server** (`mcp_server.py`) that exposes `search` and `fetch` tools for querying Belgian tax documentation. It wraps `search.py` (crawl4ai-based web scraping).

### Running the MCP server

```bash
DISPLAY=:1 uv run fastmcp run mcp_server.py --transport streamable-http --host 0.0.0.0 --port 8000
```

The server listens on port 8000 and responds to MCP protocol requests at `/mcp`.

### Key caveats

- **Xvfb required**: The crawler runs Chromium in headed (non-headless) mode. Xvfb must be running on `:1` before starting the MCP server or running any crawl scripts. On this VM it is typically already running; if not: `Xvfb :1 -screen 0 1280x1024x24 &`
- **No lint/test/build scripts**: The project has no configured linter, test suite, or build step. Syntax can be verified with `uv run python -m py_compile <file>.py`.
- **Live internet required**: All crawl/search operations hit real Belgian government sites (`finances.belgium.be`, `fin.belgium.be`). There are no mocks.
- **No `.env` or secrets required** for the core MCP server flow.
