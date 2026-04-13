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

### Testing (`TESTING.md`)

`TESTING.md` documents how to run tests, the validation dataset structure, document selection criteria, and key quality metrics. Read it before modifying tests or the ingestion pipeline.

```bash
# Quick: run all tests
PYTHONPATH=src uv run python -m pytest tests/ -v

# Semantic search validation only (slower)
PYTHONPATH=src uv run python -m pytest tests/test_semantic_search_validation.py -v --tb=short
```

### Scraping documents from Fisconet+

Fisconet+ (`minfin.fgov.be`) exposes a **public REST API** — no authentication required. The key scripts and modules for downloading documents:

#### 1. Download validation dataset documents

```bash
# Downloads all documents listed in CANDIDATES → validation_dataset/md/*.md + manifest.json
PYTHONPATH=src uv run python scripts/download_validation_pdfs.py
```

Edit `scripts/download_validation_pdfs.py` to change which documents are downloaded. Each entry is `(guid, short_name, description)`.

#### 2. Search for document GUIDs

Use the Fisconet+ client (`src/fisconet/client.py`):

```python
import asyncio
from fisconet.client import search_documents

# Search by keyword (returns pageContents with metadata including GUIDs)
results = asyncio.run(search_documents(search_terms="rentes alimentaires"))

# Filter by document type GUID (e.g. Circulaires only)
CIRC_GUID = "184c188f-aa63-4b4a-b703-3a5f07a08869"
results = asyncio.run(search_documents(
    search_terms="voiture",
    document_types=[CIRC_GUID],
))
```

**Important**: The raw API returns results under the key `pageContents` (not `results`). The `search_documents()` client function returns the `data` envelope; iterate `data["pageContents"]` to get individual document metadata with GUIDs.

#### 3. Fetch a single document by GUID

```python
from fisconet.client import fetch_document
doc = asyncio.run(fetch_document("7cfec008-5ef5-4e2d-9367-213a0c66c627"))
print(doc.title, len(doc.content_text))
```

#### 4. Document type GUIDs (for filtering searches)

| Type | GUID |
|------|------|
| Circulaires | `184c188f-aa63-4b4a-b703-3a5f07a08869` |
| Code et législation | `ba081907-ca3d-4fe6-a16d-d1fc1c9599ba` |
| Commentaires | `c2d03ba9-fd69-4359-93dd-7e2eb73515b2` |
| Jurisprudence belge | `6e3b7e04-b338-419d-9b2f-427ca75ff0b0` |
| Questions parlementaires | `8e6de482-93c4-4428-a988-070824aa81cb` |
| Décisions anticipées | `d17d212c-c8a3-494d-ac40-367fbf7f8ffa` |
| Arrêtés royaux | `fb9baef6-d027-44ee-bf1d-54a7d5113250` |

#### 5. PDF download (alternative)

```python
from crawling.pdf_ingestion import download_fisconet_pdf, pdf_to_markdown
# Downloads PDF from Fisconet+ API → out/pdfs/
pdf_path = asyncio.run(download_fisconet_pdf("GUID", "fr"))
md = pdf_to_markdown(pdf_path)
```

**Note**: Most Fisconet+ PDFs are generic placeholders. Prefer the document API (base64 HTML) via `fetch_document()` or `download_validation_pdfs.py`.

### Key caveats

- **Xvfb required**: The crawler runs Chromium in headed (non-headless) mode. Xvfb must be running on `:1` before starting the MCP server or running any crawl scripts. On this VM it is typically already running; if not: `Xvfb :1 -screen 0 1280x1024x24 &`
- **Live internet required**: All crawl/search operations hit real Belgian government sites (`finances.belgium.be`, `fin.belgium.be`). There are no mocks.
- **No `.env` or secrets required** for the core MCP server flow.

### MCP Inspector

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) is available for debugging/testing the MCP server interactively in a browser:

```bash
DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector
```

Opens at `http://localhost:6274`. Connect using **Streamable HTTP** transport with URL `http://localhost:8000/mcp` (requires the MCP server to be running).
