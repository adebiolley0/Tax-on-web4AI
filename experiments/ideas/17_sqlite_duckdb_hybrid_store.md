# 17 — SQLite FTS5 + sqlite-vec (or DuckDB FTS + VSS) as a single-file hybrid store

**Idea**

Replace the LanceDB directory with **one SQLite file**: a `chunks` table (text + metadata), an FTS5 external-content index with French Snowball stemming, and a `sqlite-vec` `vec0` table holding embeddings with metadata/partition columns. Lexical, vector and metadata queries are plain SQL; fusion is 10 lines of Python. DuckDB (FTS + VSS) is the analytical variant.

**Why it fits this project**

Zero-ops won LanceDB exp 04; SQLite goes further: stdlib, one file, `cp` is a backup, WAL gives one writer + many readers, and chunk + FTS row + vector insert atomically. Filters (region, document type, income year) become `WHERE` clauses on either leg. French stemming/stop-words (+0.25 MRR on A in exp 01) are available through FTS5 tokenizers. At 1M chunks a brute-force scan stays two orders of magnitude cheaper than the cross-encoder we already accept (20–24 s/query).

**Evidence**

- sqlite-vec v0.1.0 (Aug 2024, author's benchmark): SIFT1M (1M×128, k=20) `vec0` 33 ms vs faiss 10, DuckDB 46, numpy 136 ms; GIST 500k×960: 41 ms vs faiss 50, DuckDB 307 ms; 1M×3072 float32 8.5 s, binary 124 ms. Scan is linear in bytes: 1M×384 float32 = 1.5 GB ≈ 100–200 ms/query, 1M×1024 ≈ 300–500 ms on 4 cores (extrapolation, unverified); int8 ÷4, binary ÷32 (~95 % recall claimed).
- arXiv 2505.07621 (May 2025): full scan of 2.25M×768 on 8 vCPU = 1.5–4.9 QPS; HNSW (usearch) 212–298 QPS.
- sqlite-vec v0.1.6 (Nov 2024): metadata columns in KNN `WHERE` (=, <, IN), `partition key` pre-filter (3× faster), `+aux` columns. v0.1.7–0.1.9 (Mar 2026): real DELETE, Linux x86-64/arm64 wheels. v0.1.10-alpha.1–4 (Mar–May 2026): first ANN (`rescore`, DiskANN; IVF disabled), "docs coming soon".
- FTS5: `unicode61 remove_diacritics 2` folds accents; `porter` is English-only; French stemming via `fts5-snowball` (C, BSD, 22 commits) or a Python tokenizer `apsw.fts5.TransformTokenizer(snowballstemmer.stemmer("french").stemWord)`; `trigram` for substring/typo matching; `bm25()` with column weights; `detail=column` cut an index 743→340 MB in SQLite's test.
- DuckDB FTS: `stemmer='french'`, `strip_accents`, English stop-list only, and **the index is not updated on insert — rebuild required**. DuckDB VSS: HNSW in-memory unless `hnsw_enable_experimental_persistence` ("data loss or corruption" on crash), index must fit RAM, and `WHERE` is applied *after* the index: a 1 %-selective filter returned 0/10 rows (cigrainger, Mar 2026; `hnsw_acorn` community extension fixes it). Single writer process.

**How we would implement it**

```sql
CREATE TABLE chunks(id INTEGER PRIMARY KEY, doc_id, doc_type, region, year INT, title, body);
CREATE VIRTUAL TABLE chunks_fts USING fts5(title, body, content='chunks', content_rowid='id',
  tokenize="snowball french unicode61 remove_diacritics 2", detail=column);  -- + 3 sync triggers
CREATE VIRTUAL TABLE chunks_vec USING vec0(id INTEGER PRIMARY KEY,
  emb float[768] distance_metric=cosine, doc_type TEXT PARTITION KEY, region TEXT, year INT);
```

```sql
WITH lex AS (SELECT rowid id, bm25(chunks_fts, 3.0, 1.0) s FROM chunks_fts
             WHERE chunks_fts MATCH :q ORDER BY s LIMIT 50),
     vec AS (SELECT id, distance d FROM chunks_vec
             WHERE emb MATCH :q_emb AND k = 50 AND doc_type = :dt AND region = :r)
SELECT c.*, lex.s, vec.d FROM chunks c LEFT JOIN lex USING(id) LEFT JOIN vec USING(id)
WHERE lex.id IS NOT NULL OR vec.id IS NOT NULL;
```
Python: min-max normalise, convex fuse (0.3–0.5, exp 03), rerank top-30. One `BEGIN…COMMIT` per document; `sqlite3` needs `enable_load_extension` (OK under uv's Python) or `apsw`.

**Expected gain and cost**

Gain: one dependency-free file, transactional incremental re-indexing (idea 64), SQL filters on both legs, quality equal to bm25s + numpy (same BM25/stemmer/exact kNN). Cost: 1–2 days; ~2 GB at 1M×384 (+FTS); 0.1–0.5 s/query at 1M; compiling `fts5-snowball` or a slower Python tokenizer at ingest.

**Risks / open questions**

sqlite-vec is a one-maintainer project with alpha, undocumented ANN; if 1M×1024 brute force is too slow, fall back to int8/binary + rescore or `vectorlite` (HNSW in SQLite). vec0 metadata bugs surfaced as late as v0.1.9. FTS5 query syntax must be sanitised. DuckDB: rebuild-only FTS and experimental HNSW persistence rule it out as primary store.

**Verdict**

**try-now** (SQLite + FTS5 + sqlite-vec; skip DuckDB) — it removes the last non-stdlib storage dependency, and a one-day port of exp 04 onto corpus C (~200k chunks) will show whether brute-force latency is acceptable before any ANN decision.

**Sources**

- https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/index.html
- https://alexgarcia.xyz/blog/2024/sqlite-vec-metadata-release/index.html
- https://github.com/asg017/sqlite-vec/releases · https://pypi.org/project/sqlite-vec/
- https://sqlite.org/fts5.html · https://github.com/abiliojr/fts5-snowball · https://rogerbinns.github.io/apsw/textsearch.html
- https://duckdb.org/docs/current/core_extensions/full_text_search · https://duckdb.org/docs/current/core_extensions/vss
- https://cigrainger.com/blog/duckdb-hnsw-acorn/ · https://duckdb.org/docs/current/connect/concurrency
- https://arxiv.org/html/2505.07621v1 · https://github.com/1yefuwang1/vectorlite
