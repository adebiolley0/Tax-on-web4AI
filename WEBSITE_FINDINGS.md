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
