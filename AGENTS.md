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

## Document filtering policy

Only documents with **legal or substantive informational value** should be ingested, indexed, or used in tests. Consult `MYFIN_ARBORESCENCE.md` § "Classification" for the full table; the rules below are the essentials.

### Ingest ✅
- **Legislation text**: CIR 92, AR/CIR 92, regional codes (CfF, CBPF), Code TVA, etc.
- **Royal decrees** (arrêtés royaux d'exécution)
- **Circulaires** — binding administrative interpretations issued by the SPF Finances
- **Jurisprudence** (Belgian courts, CJEU)
- **Décisions anticipées** (advance rulings)
- **Parliamentary questions** (questions parlementaires) — official ministerial interpretations
- **European legislation** (directives, regulations) when relevant to Belgian tax
- **International conventions** (double-taxation treaties)
- **Official FAQs** — only if they contain substantive developed content (not navigation pages)
- **Preparatory documents** for the tax declaration (documents préparatoires IPP)

### Do NOT ingest ❌
- **"Aperçu documentaire" / Commentaire CIR 92 index pages** — Fisconet+ pages that merely *list* the circulars, case-law and parliamentary questions linked to an article without embedding their text. The actual commentary text is absent (shown as `N/A`). These are navigation indexes, not legal content.
- **Cours professionnels** — internal SPF Finances training materials, not legally binding
- **Compétences et formulaires** — portal navigation pages listing downloadable forms
- **Guide utilisateur** — MyMinfin portal usage documentation
- **Veille documentaire / Lettres d'information** — documentary monitoring bulletins
- **Mémento fiscal** — didactic summary, not legally binding (useful for human reference only)
- **Working Papers / Briefing Notes** — internal service notes, no direct legal authority
- **Table-of-contents documents** and pure reference lists (Répertoire RJ index pages)
- **Help / navigation pages** of any kind

### Recognition heuristics
An "aperçu documentaire" page can be identified by:
1. Its Fisconet+ section label contains "aperçu documentaire"
2. Its `## Commentaire` section is empty or marked `(N/A)`
3. The document body is composed almost entirely of `## Circulaires`, `## Jurisprudence`, `## Questions parlementaires` reference lists with no substantive prose

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
