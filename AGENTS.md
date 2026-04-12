# Agents Guide

## Project purpose

This project builds an **MCP server** that citizens, companies, and accountants can use — together with an AI assistant — to:

- quickly find information about Belgian tax law (personal and corporate)
- determine how taxes should be declared and filed
- eventually automate tax filing workflows

All data scraping, ingestion, and indexing must serve this goal. Documents sourced from government websites (Fisconet+/MyMinfin, finances.belgium.be, etc.) must contain **truthful, legally meaningful information**. When in doubt about whether to ingest a document, ask: *would a citizen or accountant rely on this to make a tax decision?*

## Document filtering policy

Only ingest documents with **legal or substantive informational value**. See `MYFIN_ARBORESCENCE.md` § "Classification" for the full per-section breakdown. The key rule: if a document does not contain citable legal text (legislation, circulaire, ruling, court decision, treaty, official FAQ), do not ingest it.

Common exclusions: Fisconet+ *aperçu documentaire* index pages (body is purely a list of circulaires/jurisprudence references, `## Commentaire` section is empty or `N/A`), training materials (*cours professionnels*), portal navigation pages (*compétences et formulaires*, *guide utilisateur*), newsletters, the *Mémento fiscal*, and any table-of-contents or help page.

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

### Belgian tax administrative codes (`codes-administratifs.md`)

`codes-administratifs.md` contains the SPF Finances reference for administrative codes used in personal tax filings (avertissement-extrait de rôle). Consult it when working with tax assessment data or interpreting code fields.

### Belgian tax websites (`WEBSITE_FINDINGS.md`)

`WEBSITE_FINDINGS.md` is a **living document**: it holds everything the project has learned so far about Belgian tax websites (behavior, structure, quirks, and extraction notes).

Before you work on **interacting with those sites**, **data extraction**, or **scraping**, read `WEBSITE_FINDINGS.md` first so you reuse known facts and avoid repeating mistakes.

Whenever you discover something new about those sites, **append or update `WEBSITE_FINDINGS.md`** so the knowledge stays centralized.

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

### MCP Inspector

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) is available for debugging/testing the MCP server interactively in a browser:

```bash
DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector
```

Opens at `http://localhost:6274`. Connect using **Streamable HTTP** transport with URL `http://localhost:8000/mcp` (requires the MCP server to be running).
