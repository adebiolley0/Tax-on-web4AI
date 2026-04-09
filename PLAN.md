# Ingestion System Plan: Belgian Tax Semantic Search (Qdrant)

## Current State

**What exists:**
- `extracted_sitemap.json`: 123 curated Belgian tax endpoints (fin.belgium.be + finances.belgium.be) with metadata (title, description, content_type, audience, category)
- `search.py`: crawl4ai-based scraper with Akamai WAF bypass, persistent Chromium profiles, batch fetching (123/123 success rate)
- `out/fetch_sitemap_results.json`: validated crawl results with markdown excerpts (max 2000 chars)
- `docker-compose.yml`: Qdrant v1.16.3 on ports 6333/6334
- `mcp_server.py`: FastMCP server with `search` and `fetch` tools (not yet connected to Qdrant)

**What's missing:**
- Full-text content extraction (current excerpts are truncated to 2000 chars)
- Fisconet+ document extraction (SPA at minfin.fgov.be, dynamic content, separate from Drupal sites)
- Embedding generation + Qdrant vector storage
- Metadata extraction (dates, fiscal codes, tax categories)
- Update/freshness tracking
- Semantic search query pipeline

---

## Architecture Overview

```
                                  +-------------------+
                                  |   Data Sources    |
                                  +-------------------+
                                  |                   |
                      +-----------+----------+  +-----+-----------+
                      | fin.belgium.be       |  | Fisconet+ REST  |
                      | finances.belgium.be  |  | API (103K+ docs)|
                      | (Drupal, 123 URLs)   |  | (minfin-rest)   |
                      +-----------+----------+  +-----+-----------+
                                  |                    |
                      +-----------v----------+  +------v-------+
                      | crawl4ai             |  | httpx        |
                      | (existing pipeline)  |  | (REST calls) |
                      +-----------+----------+  +------+-------+
                                  |                    |
                                  +--------+-----------+
                                           |
                                  +--------v---------+
                                  |  Content Parser  |
                                  |  (HTML + PDF)    |
                                  +--------+---------+
                                           |
                                  +--------v---------+
                                  |   Chunker        |
                                  |  (semantic split)|
                                  +--------+---------+
                                           |
                                  +--------v---------+
                                  |  Embedding Model |
                                  |  (sentence-      |
                                  |   transformers)  |
                                  +--------+---------+
                                           |
                                  +--------v---------+
                                  |     Qdrant       |
                                  |  (vector store)  |
                                  +------------------+
```

---

## Data Sources

### Source 1: Drupal Sites (fin.belgium.be / finances.belgium.be)
- **123 endpoints** already cataloged in `extracted_sitemap.json`
- Content types: `html_text` (majority), `mixed` (HTML + PDF downloads), `pdf` (PDF-only)
- Existing crawl4ai pipeline works reliably (123/123 success)
- **Action needed**: Extract full markdown (not truncated), extract embedded PDF links, download and parse PDFs

### Source 2: Fisconet+ (minfin.fgov.be) — PUBLIC REST API DISCOVERED

**Base URL:** `https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/`

The Angular SPA is backed by a **fully public, unauthenticated REST API** returning JSON. No browser automation needed.

**Scale:**
- **FR: 103,120 documents** | NL: 105,336 | DE: 6,292 | EN: 4,301
- 15 document types: legislation (22K), case law (16K), advance rulings (15K), parliamentary questions (15K), circulars (3.7K), etc.

**Key endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/search` | POST | Paginated search with filters (type, taxonomy, date range, keywords). pageSize up to 100. |
| `/document/{guid}` | GET | Full document: base64-encoded HTML content + all metadata |
| `/pdf?id={guid}&language={lang}` | GET | PDF download |
| `/navigation/tree` | GET | Complete taxonomy hierarchy (907 leaf nodes) |
| `/library/documents?language=fr` | GET | Curated key publications (Memento Fiscal, CIR 92, etc.) |
| `/changes/searches?language=fr&month=M&year=Y` | GET | Monthly change feed (2017-2026) — ideal for incremental updates |
| `/changes/limit-year` | GET | Available year range for changes |

**Metadata per document:**
- `guid`, `title`, `language`, `summary`
- `documentDate`, `publicationDate`, `effectiveDate`, `lastModified`, `fisconetPlusDate`
- `documentType` (with GUID + multilingual label)
- `taxonomies[]` (hierarchical classification with GUIDs)
- `keywords[]` (subject keywords with GUIDs + labels)
- `linkedDocument` (cross-language equivalents NL/FR, previous/next in sequence)
- `relatedDocuments[]` (title + GUID)
- `pathItems[]` (breadcrumb in taxonomy tree)
- `questioner[]` (for parliamentary questions)
- `regionalisation` (regional scope)
- `status` ("Published")

**Content format:** base64-encoded UTF-8 HTML in `content.content` field. Contains internal cross-reference links (`fisconet.compare/{guid1}/{guid2}`, `fisconet.direct/{guid}`).

**Action needed:** Direct HTTP calls via `httpx` — paginate through search results, fetch each document by GUID, decode base64 HTML, strip to text for embedding.

---

## Implementation Steps

### Step 1: Enhance Content Extraction Pipeline

**File: `content_extractor.py` (new)**

```python
# Responsibilities:
# 1. Full markdown extraction (no 2000-char truncation)
# 2. PDF link discovery from HTML pages
# 3. PDF download + text extraction
# 4. Metadata extraction from page content
```

**Tasks:**
1. Modify `search.py` `_markdown_excerpt()` to optionally return full content (add `full=True` param or new function)
2. Add PDF extraction using `pymupdf` (fitz) or `pdfplumber`:
   - Discover PDF links in crawled HTML (`<a href="...pdf">`)
   - Download PDFs via httpx
   - Extract text content from PDFs
3. Extract metadata from page content:
   - **Document date**: Parse from page headers, breadcrumbs, or meta tags (look for patterns like `dd/mm/yyyy`, `exercice d'imposition YYYY`)
   - **Fiscal codes**: Regex for article references (`art. XXX CIR 92`, `art. XXX CTVA`, `art. XXX C.Enr.`)
   - **Tax category**: Map from URL path + `extracted_sitemap.json` category field
   - **Language**: Detect from URL path (`/fr/`, `/nl/`, `/de/`)

**New dependencies:** `pymupdf` (for PDF parsing)

### Step 2: Fisconet+ REST API Client

**File: `fisconet_client.py` (new)**

No browser automation needed — the Fisconet+ Angular SPA is backed by a public REST API.

**Tasks:**
1. **Build document index** via `POST /search`:
   - Paginate through all ~103K FR documents (pageSize=100, ~1,032 pages)
   - Store metadata: guid, title, documentType, taxonomies, keywords, dates, summary
   - Optionally repeat for NL (105K) — same content, different language
   - Rate limit: 1-2 req/sec with exponential backoff on errors
2. **Fetch full document content** via `GET /document/{guid}`:
   - Decode base64 HTML from `content.content`
   - Strip HTML tags to extract plain text for embedding
   - Preserve internal cross-references (`fisconet.direct/{guid}`) as metadata
   - Parse `relatedDocuments[]` for link graph
3. **Download PDFs** for library documents:
   - Fetch curated list from `GET /library/documents?language=fr`
   - Download PDFs via `GET /pdf?id={guid}&language=fr`
   - Parse with pymupdf
4. **Fetch taxonomy tree** via `GET /navigation/tree`:
   - Build hierarchical category mapping (guid → label path)
   - Use for enriching chunk metadata with full taxonomy breadcrumb

**Actual Fisconet document metadata** (confirmed from API):
- `documentType`: Code et legislation, Jurisprudence belge, Decisions anticipees, Questions parlementaires, Commentaires, Circulaires, Forfaits, Arretes royaux, etc. (15 types)
- `documentDate`, `publicationDate`, `effectiveDate`, `lastModified`
- `taxonomies[]`: hierarchical fiscal domain classification
- `keywords[]`: subject tags with multilingual labels
- `linkedDocument`: cross-language equivalents + previous/next in legislative sequence
- `regionalisation`: federal vs. regional scope
- `questioner[]`: for parliamentary questions

### Step 3: Document Chunking

**File: `chunker.py` (new)**

Tax documents need intelligent chunking to preserve context. Strategy:

1. **Hierarchical splitting**: Respect document structure (headings, articles, sections)
   - Split on `##` / `###` markdown headings first
   - Fall back to paragraph splitting for flat content
   - Keep chunks between 512-1024 tokens (optimal for embedding models)
2. **Overlap**: 128-token overlap between adjacent chunks to preserve cross-boundary context
3. **Metadata inheritance**: Each chunk inherits the parent document's metadata + gets:
   - `chunk_index`: position within parent document
   - `section_heading`: nearest heading above the chunk
   - `parent_document_id`: link back to source document

**Implementation**: Use `langchain-text-splitters` `RecursiveCharacterTextSplitter` with markdown-aware separators, or a custom splitter.

**New dependency:** `langchain-text-splitters` (lightweight, no full langchain needed)

### Step 4: Embedding Generation

**File: `embedder.py` (new)**

**Embedding model choice**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Multilingual (French, Dutch, German - all Belgian official languages)
- 384-dimension vectors (good balance of quality vs. storage)
- Fast inference, runs locally on CPU
- Alternative for higher quality: `intfloat/multilingual-e5-large` (1024-dim, but slower)

**Tasks:**
1. Load model via `sentence-transformers`
2. Batch-embed chunks (batch size ~64 for CPU)
3. Return (chunk_text, embedding_vector, metadata) tuples

**New dependencies:** `sentence-transformers`, `torch`

### Step 5: Qdrant Integration

**File: `qdrant_store.py` (new)**

**Collection schema:**

```
Collection: "belgian_tax_docs"
  Vector: 384 dimensions (or 1024 for e5-large), cosine distance

  Payload fields (indexed):
    - source_url: str              # original page URL
    - source_domain: str           # "fin.belgium.be" | "finances.belgium.be" | "minfin.fgov.be"
    - source_type: str             # "drupal_page" | "fisconet_document" | "pdf"
    - document_title: str          # page/document title
    - document_date: str|null      # ISO date if available (for freshness checks)
    - last_crawled: str            # ISO datetime of last successful crawl
    - content_hash: str            # SHA-256 of chunk text (for dedup + change detection)
    - audience: str|null           # "particuliers" | "entreprises" | "independants" | "asbl" | "tous"
    - tax_category: str|null       # "declaration" | "revenus" | "tva" | "isoc" | "habitation" ...
    - fiscal_codes: list[str]      # ["art. 7 CIR 92", "art. 171 CIR 92", ...]
    - document_type: str|null      # "loi" | "circulaire" | "ruling" | "commentaire" | "page_info"
    - language: str                # "fr" | "nl" | "de"
    - chunk_index: int             # position within parent document
    - section_heading: str|null    # nearest heading for this chunk
    - chunk_text: str              # full text of the chunk (stored for retrieval)
```

**Tasks:**
1. Connect to Qdrant (localhost:6333 from docker-compose)
2. Create/recreate collection with schema above
3. Upsert points in batches (~100 per upsert call)
4. Build payload indexes on: `source_domain`, `tax_category`, `audience`, `document_type`, `language`, `fiscal_codes`
5. Implement `content_hash`-based deduplication: skip re-upserting unchanged chunks

**New dependency:** `qdrant-client`

### Step 6: Ingestion Orchestrator

**File: `ingest.py` (new) — the main entry point**

```python
async def ingest_all():
    """Full ingestion pipeline."""
    # Phase 1: Crawl Drupal sites
    drupal_docs = await crawl_drupal_sites()      # enhanced fetch_all_sitemap_urls
    
    # Phase 2: Crawl Fisconet+
    fisconet_docs = await crawl_fisconet()         # new SPA scraper
    
    # Phase 3: Download + parse any PDFs
    all_docs = drupal_docs + fisconet_docs
    all_docs = await extract_pdfs(all_docs)
    
    # Phase 4: Extract metadata
    all_docs = extract_metadata(all_docs)
    
    # Phase 5: Chunk documents
    chunks = chunk_documents(all_docs)
    
    # Phase 6: Generate embeddings
    embedded_chunks = embed_chunks(chunks)
    
    # Phase 7: Upsert to Qdrant
    await upsert_to_qdrant(embedded_chunks)
    
    # Phase 8: Log summary
    log_ingestion_summary()
```

**CLI interface:**
```bash
uv run python ingest.py                    # full ingestion
uv run python ingest.py --source drupal    # only Drupal sites
uv run python ingest.py --source fisconet  # only Fisconet+
uv run python ingest.py --update           # only crawl docs newer than last_crawled
```

### Step 7: Update/Freshness Tracking

**File: `freshness.py` (new)**

For future automatic update detection:

1. Store `last_crawled` timestamp + `content_hash` per source URL/GUID in a local SQLite DB (`ingestion_state.db`)
2. **Fisconet+ incremental updates** (preferred path):
   - Use `GET /changes/searches?language=fr&month=M&year=Y` to get new/modified documents since last run
   - Each entry has `status: "New"` or `status: "Modified"` — fetch only those GUIDs
   - Available from 2017 onwards — covers full history
   - Run monthly or on-demand
3. **Drupal site updates** (content-hash based):
   - Re-crawl all 123 source URLs
   - Compare `content_hash` of new content vs. stored hash
   - If changed: re-chunk, re-embed, replace old vectors in Qdrant (delete by `source_url` filter, then upsert new)
   - If unchanged: skip
4. Track per-source crawl/fetch history (date, hash, success/failure) for debugging

**New dependency:** none (stdlib `sqlite3`)

### Step 8: Wire Semantic Search into MCP Server

**File: `mcp_server.py` (modify existing)**

Add a new `semantic_search` tool:

```python
@mcp.tool(name="semantic_search")
async def semantic_search_tool(
    query: str,
    tax_category: str | None = None,
    audience: str | None = None,
    language: str = "fr",
    limit: int = 10,
) -> str:
    """Semantic search over Belgian tax regulation documents."""
    # 1. Embed the query
    # 2. Search Qdrant with optional payload filters
    # 3. Return ranked results with chunk text + metadata
```

---

## New Dependencies Summary

Add to `pyproject.toml`:
```toml
"pymupdf>=1.25.0",           # PDF text extraction
"qdrant-client>=1.14.0",     # Qdrant vector DB client
"sentence-transformers>=4.0", # Embedding model
"langchain-text-splitters>=0.3", # Document chunking
```

---

## File Structure After Implementation

```
Tax-on-web4AI/
├── ingest.py                  # Main entry point / orchestrator
├── content_extractor.py       # Full HTML + PDF content extraction
├── fisconet_client.py         # Fisconet+ REST API client (httpx, no browser)
├── chunker.py                 # Semantic document chunking
├── embedder.py                # Embedding generation (sentence-transformers)
├── qdrant_store.py            # Qdrant collection management + upsert
├── freshness.py               # Update tracking (SQLite state DB)
├── models.py                  # Shared Pydantic models for documents/chunks
├── search.py                  # (existing) crawl4ai scraper
├── mcp_server.py              # (enhanced) MCP server with semantic_search tool
├── build_sitemap.py           # (existing) endpoint catalog builder
├── extracted_sitemap.json     # (existing) 123 endpoint definitions
├── docker-compose.yml         # (existing) Qdrant service
├── ingestion_state.db         # (generated) SQLite freshness tracking
└── out/                       # (existing) crawl results
```

---

## Execution Order

| Phase | Step | Description | Depends on |
|-------|------|-------------|------------|
| 1 | Step 5 | Qdrant collection setup + `qdrant_store.py` | docker-compose up |
| 2 | Step 2 | Fisconet+ REST API client (`fisconet_client.py`) | httpx (already installed) |
| 3 | Step 1 | Enhanced Drupal content extraction (full text + PDFs) | existing search.py |
| 4 | Step 4 | Embedding pipeline | - |
| 5 | Step 3 | Document chunker | - |
| 6 | Step 6 | Ingestion orchestrator (both sources) | Steps 1-5 |
| 7 | Step 7 | Freshness tracking (Fisconet changes API + Drupal hashes) | Step 6 |
| 8 | Step 8 | MCP semantic search tool | Steps 5,4 |

**Phase 1-2**: Qdrant + Fisconet client first — the REST API is the largest and cleanest data source (103K+ docs with rich metadata, no browser needed).
**Phase 3-6**: Drupal extraction + chunking + embeddings + orchestration.
**Phase 7-8**: Incremental updates + MCP semantic search.

---

## Key Design Decisions

1. **Multilingual embeddings**: Belgian tax docs exist in FR/NL/DE. Using `paraphrase-multilingual-MiniLM-L12-v2` handles all three without separate models.

2. **Chunk-level vectors, document-level metadata**: Each chunk is a separate Qdrant point, but carries full parent document metadata for filtering. This allows precise retrieval while maintaining context.

3. **Content-hash deduplication**: Avoids re-embedding unchanged content on updates. Critical for the ~30-minute crawl cycle.

4. **Fisconet via REST API (no browser)**: The public REST API at `minfin.fgov.be/myminfin-rest` provides full document content (base64 HTML) and rich metadata (dates, types, taxonomies, keywords) via simple HTTP calls. This is dramatically simpler, faster, and more reliable than browser automation. ~103K French documents available.

5. **Local embeddings**: No external API dependency. Runs on CPU (sentence-transformers with MiniLM is fast enough for ~10K chunks). Can upgrade to GPU or API-based embeddings later if needed.
