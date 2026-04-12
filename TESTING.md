# Testing Guide

## Running Tests

All tests use **pytest** with `PYTHONPATH=src`:

```bash
# Run all tests
PYTHONPATH=src uv run python -m pytest tests/ -v

# Run a specific test file
PYTHONPATH=src uv run python -m pytest tests/test_content_cleaner.py -v

# Run semantic search validation (slower — embeds documents)
PYTHONPATH=src uv run python -m pytest tests/test_semantic_search_validation.py -v --tb=short
```

Syntax-only check (no dependencies needed):
```bash
uv run python -m py_compile src/storage/content_cleaner.py
```

## Test Structure

```
tests/
├── conftest.py                         # Shared fixtures
├── test_chunker.py                     # Document chunking logic
├── test_content_cleaner.py             # Pre-ingestion content cleaning (unit tests)
├── test_content_extractor.py           # HTML-to-markdown extraction
├── test_embedder.py                    # Embedding model
├── test_fisconet_client.py             # Fisconet+ API client
├── test_qdrant_store.py                # Vector DB operations
└── test_semantic_search_validation.py  # End-to-end search quality (integration)
```

## Semantic Search Validation Dataset

Located in `validation_dataset/`:

```
validation_dataset/
├── md/                   # 20 markdown documents (source material)
├── sample_extra/         # Extra documents used to verify cleaning patterns
├── manifest.json         # Metadata for all downloaded documents
├── questions.json        # 10 test questions with ground truth
└── search_results_report.json  # Latest search results (auto-generated)
```

### What the validation test does

1. **Ingests** all documents from `validation_dataset/md/` into an in-memory Qdrant instance
2. Applies the **content cleaner** (removes index sections, boilerplate, ToC)
3. **Chunks** documents (1500 char max, 200 char overlap)
4. **Embeds** chunks with `paraphrase-multilingual-MiniLM-L12-v2` (384D)
5. Runs **10 tax-return questions** and checks that expected documents rank in the top results
6. Reports **aggregate metrics**: Recall@10, MRR, average cosine similarity scores

### Document selection criteria

Only documents with **legal value or practical information** should be in the validation dataset:

| Include | Skip |
|---------|------|
| Circulaires (binding administrative interpretations) | Aperçu documentaire (index pages listing references) |
| FAQs (practical tax filing guidance) | Table-of-contents documents |
| Legislation text (CIR 92 articles) | "Cours professionnels" (training materials) |
| Royal decrees (legally binding) | Pure reference lists |
| Advance rulings (detailed reasoning) | Help/navigation pages |

See `WEBSITE_FINDINGS.md` § 5 for the full classification of Fisconet+ document types.

### Ground truth format (`questions.json`)

```json
[
  {
    "id": "Q1",
    "question": "French-language question a taxpayer might ask",
    "topic": "snake_case_topic_name",
    "expected_docs": ["doc_id_1", "doc_id_2"],
    "secondary_docs": ["doc_id_3"],
    "expected_keywords": ["term1", "term2"]
  }
]
```

- `expected_docs`: Documents that MUST appear in top-10 results (primary relevance)
- `secondary_docs`: Documents that may also appear (acceptable but not required)
- `expected_keywords`: Terms that should be present in the relevant document content

### Known limitations (marked `xfail`)

| Question | Issue | Root cause |
|----------|-------|------------|
| Q1 (vehicle expenses) | Expected docs are index pages with no content | Need to replace with a substantive circular about vehicle expense deduction |
| Q5 (charitable donations) | Synonym gap: query uses "dons", doc uses "libéralités" | MiniLM cannot bridge French synonym gap; needs query expansion |
| Q10 (alimony) | Expected docs are index pages | Need substantive alimony content document |

### Adding new documents

1. Find the document GUID on Fisconet+ (use `POST /search` endpoint)
2. Add it to `scripts/download_validation_pdfs.py` CANDIDATES list
3. Run the download script: `PYTHONPATH=src uv run python scripts/download_validation_pdfs.py`
4. Update `questions.json` ground truth if needed
5. Re-run validation: `PYTHONPATH=src uv run python -m pytest tests/test_semantic_search_validation.py -v`

## Content Cleaner Tests (`test_content_cleaner.py`)

Unit tests for each cleaning function using synthetic inputs that mirror real Fisconet+ document patterns:

- `TestStripIndexSections` — Verifies removal of `## Législation`, `## Circulaires`, etc. while preserving document titles and `## Commentaire` sections
- `TestStripToc` — Table-of-contents removal
- `TestStripBoilerplate` — SPF headers, Numac, signatures, metadata lines
- `TestStripDecreePreamble` — Royal decree formulaic blocks (Vu..., Considérant que...)
- `TestStripKeywordLines` — Semicolon-separated tag lines
- `TestNormalization` — Whitespace collapsing
- `TestCleanForIndexing` — Integration tests for the full pipeline

## Key Metrics

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Recall@10 | >= 7/10 | Questions with expected doc in top-10 |
| MRR | >= 0.3 | Mean Reciprocal Rank across all questions |
| Avg best-match score | >= 0.35 | Average cosine similarity of best expected-doc hit |
| Top score per question | >= 0.3 | Each question's #1 result must exceed this |
