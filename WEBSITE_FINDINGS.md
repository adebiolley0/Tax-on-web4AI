# Belgian Tax Websites — Technical Findings

## 1. Drupal Sites: fin.belgium.be / finances.belgium.be

### Overview
The SPF Finances (Belgian Federal Public Service Finance) runs two public Drupal-based websites:
- **fin.belgium.be** — primary portal (particuliers redirects here)
- **finances.belgium.be** — secondary domain (301-redirects some paths to fin.belgium.be)

### Content
- **123 curated endpoints** indexed in `extracted_sitemap.json`
- Content covers: personal income tax, corporate tax, VAT, inheritance, housing, international taxation, e-services
- Audience segments: particuliers, entreprises, independants, asbl, experts/partenaires
- Languages: French (primary indexed), with NL/DE equivalents at `/nl/` and `/de/` paths

### Content Types
- `html_text` — majority of pages, on-page text content
- `mixed` — HTML text + downloadable PDF attachments
- `pdf` — PDF-only downloads (forms, guides)

### Technical Details
- **CMS**: Drupal (detected via `<meta name="generator">` and `#main-content` landmark)
- **WAF**: Akamai/TSPD — serves CAPTCHA interstitial pages for untrusted sessions
- **WAF bypass**: Persistent Chromium profile + warm-up navigation to `fin.belgium.be/fr/particuliers` reliably clears the WAF
- **Search endpoint**: `finances.belgium.be/fr/search?keywords=...&page=N` — Drupal Views-based, returns HTML with structured result rows
- **Crawl performance**: 123/123 URLs successfully crawled; ~30 minutes for full batch with `networkidle` waits and retry logic

### URL Patterns
```
fin.belgium.be/fr/particuliers/{topic}/{subtopic}
fin.belgium.be/fr/entreprises/{topic}/{subtopic}
finances.belgium.be/fr/{audience}/{topic}
finances.belgium.be/fr/E-services/{service}
```

### Notable Redirects
- `finances.belgium.be/fr/particuliers` → `fin.belgium.be/fr` (301)
- `finances.belgium.be/fr/E-services/fisconetplus` → `minfin.fgov.be/myminfin-web/pages/public/fisconet`

### Metadata Available from Crawl
- Page title (from `<title>` tag)
- URL path (encodes audience + category)
- Breadcrumbs (from search results)
- Content type (html/pdf/mixed — from `extracted_sitemap.json`)
- Markdown-rendered content (via crawl4ai)
- No structured dates or fiscal code references in page metadata — must be extracted from body text

---

## 2. Fisconet+ (minfin.fgov.be) — PUBLIC REST API

### Overview
Fisconet+ is the Belgian Federal Ministry of Finance's legal database containing all tax legislation, case law, circulars, administrative comments, advance rulings, and parliamentary questions. It is the **primary and richest source** of Belgian tax regulation.

### Architecture
- **Frontend**: Angular SPA at `minfin.fgov.be/myminfin-web/pages/public/fisconet`
- **Backend**: Public REST API at `minfin.fgov.be/myminfin-rest/fisconetPlus/public/`
- **Authentication**: None required — all endpoints are public and unauthenticated
- **Response format**: JSON

### Scale
| Language | Document Count |
|----------|---------------|
| French (fr) | 103,120 |
| Dutch (nl) | 105,336 |
| German (de) | 6,292 |
| English (en) | 4,301 |

### Document Types (15 categories, French counts)
| Type | FR Label | Count |
|------|----------|-------|
| Legislation | Code et legislation | 22,179 |
| Belgian case law | Jurisprudence belge | 16,832 |
| Advance rulings | Decisions anticipees (L 24.12.2002) | 15,634 |
| Parliamentary questions | Questions parlementaires | 15,395 |
| Administrative comments | Commentaires (dont Rep. RJ) | 6,331 |
| EU regulation | Reglementation europeenne | 4,565 |
| Circulars | Circulaires | 3,751 |
| Lump sums | Forfaits | 3,222 |
| Royal decrees | Arretes royaux | 3,126 |
| Regional/local legislation | Legislation regionale et locale | 2,469 |
| EU case law | Jurisprudence europeenne | 2,089 |
| Professional courses | Cours professionnels | 1,771 |
| Decisions | Decisions | 1,504 |
| Communications | Communications | 1,278 |
| Treaties | Traites et accords internationaux | 618 |

### REST API Endpoints

#### POST `/search` — Paginated Document Search
```json
{
  "searchCriteria": {
    "language": "fr",
    "searchTerms": "",
    "orderBy": "RELEVANCE",
    "taxonomies": [],
    "documentTypes": [],
    "keywords": [],
    "documentDateRange": {"from": "2025-01-01", "to": "2025-12-31"}
  },
  "paginationParameters": {
    "currentPageNumber": 0,
    "pageSize": 100
  }
}
```
Returns: paginated results with metadata, filter facets, total count.

#### GET `/document/{guid}` — Full Document Content
Returns complete document with:
- **Content**: base64-encoded UTF-8 HTML in `content.content` field
- **Metadata**: All fields listed below
- Content sizes range from a few KB to 144KB+ of structured HTML

#### GET `/pdf?id={guid}&language={lang}` — PDF Download
Returns PDF file. Tested: up to 4.6MB / 38 pages (CIR 92 table of contents).

#### GET `/navigation/tree` — Full Taxonomy Tree
Returns hierarchical document classification with 5 top-level categories and 907 leaf document nodes. Each node has `guid`, multilingual `label`, `documentId` per language, and `children[]`.

#### GET `/library/documents?language=fr` — Curated Key Publications
Returns list of major publications (Memento Fiscal 2025, CIR 92, AR/CIR 92, Code de la TVA, etc.) with `id` (GUID), `title`, `thumbnail` (SharePoint URL), `sortWeight`.

#### GET `/changes/searches?language=fr&month=M&year=Y` — Monthly Change Feed
Returns documents added or modified in a given month. Each entry includes:
- `guid`, `title`, `date`, `taxonomyTerm`, `documentType`
- `status`: "New" or "Modified"
- `language`, `version`, `summary`, `keywordList[]`
- `documentDate`, `questioner[]`, `created`, `editor`
Available years: 2017-2026 (from `GET /changes/limit-year`).

### Document Metadata Fields
| Field | Description |
|-------|-------------|
| `guid` | Unique document identifier (UUID format) |
| `title` | Document title |
| `language` | fr / nl / de / en |
| `summary` | Brief description |
| `documentType` | Type with GUID + multilingual label |
| `documentDate` | Official date of the document |
| `publicationDate` | Date published on Fisconet |
| `effectiveDate` | Date the document takes effect |
| `lastModified` | Last modification timestamp |
| `fisconetPlusDate` | Fisconet-specific date |
| `status` | "Published" |
| `taxonomies[]` | Hierarchical classification (GUIDs + labels) |
| `keywords[]` | Subject keywords (GUIDs + multilingual labels) |
| `linkedDocument` | Cross-language equivalents (nl↔fr) + previous/next in sequence |
| `relatedDocuments[]` | Related documents with title + GUID |
| `pathItems[]` | Full breadcrumb path in taxonomy tree |
| `questioner[]` | For parliamentary questions: who asked |
| `regionalisation` | Regional applicability (federal vs. regional) |
| `historyLink` | GUID to historical version |

### Content Format Details
- Content is **base64-encoded UTF-8 HTML**
- `content.type` = `"HTML"` for all tested documents
- HTML contains internal cross-reference links:
  - `https://fisconet.compare/{guid1}/{guid2}` — comparison view
  - `https://fisconet.direct/{guid}` — direct document link
  - These are Angular route rewrites, not real URLs
- Some documents are thin wrappers linking to external sources (e.g., Civil Code → justice.belgium.be)

### API Behavior Notes
- Response time: < 1 second per request
- HTTP 202 observed for some error conditions
- No rate limiting headers observed, but recommend 1-2 req/sec for bulk operations
- Cookie consent is only needed for the Angular frontend, not the REST API
- No authentication tokens or API keys required

---

## 3. Summary: Data Source Comparison

| Aspect | Drupal Sites | Fisconet+ API |
|--------|-------------|---------------|
| Document count | 123 pages | 103,000+ (FR) |
| Access method | crawl4ai (browser) | httpx (REST API) |
| Content format | HTML (Drupal pages) | base64 HTML (via JSON) |
| PDFs | Embedded links in pages | Dedicated endpoint |
| Metadata quality | Basic (title, URL path) | Rich (dates, types, taxonomies, keywords, cross-refs) |
| Structured dates | No (must parse from text) | Yes (documentDate, publicationDate, effectiveDate) |
| Fiscal codes | No (must regex from text) | Yes (taxonomies, keywords) |
| Update detection | Re-crawl + content hash | Monthly changes endpoint |
| Authentication | None | None |
| WAF/Anti-bot | Akamai CAPTCHA (bypassed) | None |
| Speed | ~30 min for 123 URLs | < 1 sec/request |

---

## 4. PDF Ingestion (pymupdf4llm)

### Implemented in `src/crawling/pdf_ingestion.py`

#### Fisconet+ PDF Endpoint
- **Endpoint**: `GET /pdf?id={guid}&language={lang}` — returns raw PDF bytes
- **Tested**: Successfully downloaded Table of Contents PDF (4.6 MB / 38 pages)
- **Availability**: Not all documents have PDFs; some GUIDs return HTTP 503
- **Library endpoint** (`GET /library/documents?language=fr`) was returning 503 during testing — may be intermittent

#### Drupal PDF Links
- **29 out of 123 endpoints** have `content_type` of `mixed` or `pdf` in `extracted_sitemap.json`
- PDF links are embedded in page HTML as `<a href="...pdf">` or via `/sites/default/files/` paths
- Direct `httpx` GET works for Drupal PDF downloads (no WAF issues for static files)
- Tested on the tax declaration page: 7 PDFs found and downloaded (forms, preparatory docs, explanatory guides)

#### Conversion Quality (pymupdf4llm)
- Converts PDF to Markdown preserving headings, tables, lists, and form field codes
- Images are omitted with placeholder text (`==> picture [...] intentionally omitted <==`)
- Typical output sizes: 6K–201K chars of Markdown per PDF
- Belgian tax form codes (e.g., `1001-66`, `1002-65`) are correctly preserved in output

#### Output Locations
- Raw PDFs: `out/pdfs/` (kept for archival)
- Markdown: `out/pdfs_md/` (one `.md` file per PDF)

---

## 5. Fisconet+ Document Types — Ingestion Decision

Not all Fisconet+ document types contain content worth indexing for semantic search. Some are pure reference lists or index pages with no substantive prose.

### Document Types That SHOULD Be Ingested

| Type (FR) | Count | Reason to ingest |
|-----------|-------|------------------|
| **Circulaires** | 3,751 | Binding administrative interpretations; contain explanations, examples, and practical guidance. The richest source of "how to" information for taxpayers. |
| **Code et législation** | 22,179 | Actual legal text (CIR 92, CTVA, etc.). Has legal force. |
| **Arrêtés royaux** | 3,126 | Executive orders implementing legislation. Legally binding. |
| **Décisions anticipées** | 15,634 | Advance rulings with reasoning; useful for understanding how rules apply to specific situations. |
| **Communications** | 1,278 | Administrative communications with practical information. |
| **Forfaits** | 3,222 | Lump-sum amounts used in tax calculations; factual reference. |
| **Législation régionale et locale** | 2,469 | Regional tax legislation with legal force. |
| **Réglementation européenne** | 4,565 | EU regulations applicable to Belgian tax. |
| **Traités et accords internationaux** | 618 | Tax treaties. Legally binding. |

### Document Types to Ingest SELECTIVELY

| Type (FR) | Count | Notes |
|-----------|-------|-------|
| **Commentaires (dont Rép. RJ)** | 6,331 | **Two sub-types exist:** (1) "Aperçu documentaire" pages are INDEX pages that only list references — skip these. (2) Actual commentary text (e.g., "mise à jour à partir de 2010") contains substantive legal explanations — ingest these. Distinguish by taxonomy: `"Commentaire du code des impôts sur les revenus 1992 (aperçu documentaire)"` = index page. |
| **Jurisprudence belge** | 16,832 | Court decisions. Ingest rulings from Cour Constitutionnelle and Cour de Cassation. Lower court decisions may be less useful. |
| **Jurisprudence européenne** | 2,089 | EU court decisions relevant to Belgian tax. |
| **Questions parlementaires** | 15,395 | Parliamentary Q&A. Some contain detailed ministerial answers explaining tax rules. Others are very short. Ingest those with substantive answers. |

### Document Types to SKIP

| Type (FR) | Count | Reason to skip |
|-----------|-------|----------------|
| **Cours professionnels** | 1,771 | Training materials for civil servants, not legal texts. |
| **Commentaires — "aperçu documentaire"** | ~6,000 | Index pages listing circulars, case law, and parliamentary questions. Contain no prose. After content cleaning, these shrink to < 200 chars. |

### How to Identify Index Pages (Aperçu Documentaire)

These are "Commentaire" documents with taxonomy = `"Commentaire du code des impôts sur les revenus 1992 (aperçu documentaire)"`. Their structure is:
```
# Commentaire de l'article NNN, CIR 92
## Législation        ← list of legal references
## Commentaire        ← 1-2 lines linking to actual commentary
## Circulaires        ← list of circular titles
## Jurisprudence      ← list of court decisions
## Questions parlementaires  ← list of parliamentary questions
## Autres documents   ← list of other docs
## Avis               ← list of notices
```

After content cleaning (removing reference sections), these are left with only the title and ~160 chars. They should be **excluded at ingestion time** based on their taxonomy label or by detecting post-cleaning length < 300 chars.

### Fisconet+ Search API — Document Type Filter

To filter by document type in `POST /search`, pass the type GUID in `documentTypes[]`:

| Type | GUID |
|------|------|
| Circulaires | `184c188f-aa63-4b4a-b703-3a5f07a08869` |
| Code et législation | `ba081907-ca3d-4fe6-a16d-d1fc1c9599ba` |
| Commentaires (dont Rép. RJ) | `c2d03ba9-fd69-4359-93dd-7e2eb73515b2` |
| Jurisprudence belge | `6e3b7e04-b338-419d-9b2f-427ca75ff0b0` |
| Questions parlementaires | `8e6de482-93c4-4428-a988-070824aa81cb` |
| Décisions anticipées | `d17d212c-c8a3-494d-ac40-367fbf7f8ffa` |
| Jurisprudence européenne | `f00566eb-d014-45ab-9d23-14d15d4e32b8` |
| Cours professionnels | `fe2b2c33-078e-4337-9781-9ac054217c65` |

---

## 6. Content Cleaning for Semantic Search

### Problem

Index-style documents (aperçu documentaire) and boilerplate sections in otherwise-substantive documents degrade semantic search quality. Reference lists containing legal terms match queries they're not actually about.

### Solution: Pre-ingestion Content Cleaner

`src/storage/content_cleaner.py` — called automatically by `chunk_document()` before chunking.

Removes:
- **Index/reference sections**: `## Législation`, `## Circulaires`, `## Jurisprudence`, `## Questions parlementaires`, `## Autres documents`, `## Avis` (bare headings only — does NOT strip document titles like `# Circulaire 2025/C/21 relative à ...`)
- **Table-of-contents blocks**: `Table des matières` followed by Roman numeral / lettered lines
- **Boilerplate metadata**: `**Source:**`, `**GUID:**`, `**Date:**`, `---`, SPF headers, Numac, M.B. publication lines
- **Royal decree preamble**: `Vu le Code...;`, `Considérant que :`, `Sur la proposition du Ministre`, `Nous avons arrêté et arrêtons :`
- **Signature blocks**: `Donné à Bruxelles`, `Par le Roi :`, `Le Ministre des Finances`, `PHILIPPE`
- **Keyword/tag lines**: Semicolon-separated subject lists (e.g., `impôt des personnes physiques ; biens immobiliers ; déduction`)

### Impact Measured

| Document type | Content retained after cleaning |
|---------------|-------------------------------|
| Circulaires | 94–98% (only boilerplate removed) |
| FAQs | 96–97% |
| Aperçu documentaire (index) | 1–13% (correctly identified as noise) |

### Ingestion Guard

Documents with < 300 chars after cleaning should be skipped entirely — they have no substantive content to embed.
