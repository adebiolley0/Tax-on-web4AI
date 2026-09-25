# 18 — PostgreSQL as the single store (pgvector + FTS + hybrid in SQL)

**Idea**

One Postgres for chunks, embeddings, lexical index, metadata, users and ingestion state: `pgvector` (HNSW on `halfvec`) for the dense leg, French `tsvector`/GIN (or a BM25 extension) for the lexical leg, `pg_trgm` for article/code lookups and typos, Reciprocal Rank Fusion in a CTE. The Python reranker stays outside the DB.

**Why it fits this project**

Production needs Postgres anyway; a second store doubles ops and breaks transactional re-ingestion. Our recipe (e5-small + French BM25 → RRF → bge-reranker @30) is two CTEs. Hard filters (document type, tax year, language) become `WHERE` clauses. Throughput needs are tiny (reranker ≈ 20 s/query on CPU), so DB latency is noise. 1M × 384-dim `halfvec` ≈ 0.8 GB + HNSW graph, ~2 GB RAM (estimate).

**Evidence**

- pgvector 0.8.6 (Apache-2.0): `halfvec` indexable to 4,000 dims, `bit` for binary quantisation, iterative index scans since 0.8.0 (Nov 2024).
- 1M × 1536 dbpedia-openai, pgvector 0.7.0 (Apr 2024, r7gd.16xlarge): HNSW `halfvec` recall 96.8 % @ef_search=40, 578 QPS, p99 2.6 ms, index 3.9 GB (float32 7.7 GB, build 2.3× slower); binary+rerank 473 MB, recall 91.6 % @40 / 99.0 % @200.
- Filtered search, 10M × 384 (AWS, May 2025): iterative scan lifts category-filtered recall 10 % → 100 %; top-10 p99 123 → 13 ms.
- Postgres `french` config: Snowball stemmer + 195 stopwords, **no question words** (comment, quel, combien) — the list that mattered in exp 01; `ts_rank` has no IDF.
- ParadeDB `pg_search` (AGPL-3.0, Tantivy BM25, French stemmer/stopwords). Vendor benchmark, 1M rows, 4 cores/8 GB (Jun 2026): single term parity (~3.5k QPS); 40 rotating terms 3,373 vs 115 QPS, median 1.4 vs 109 ms.
- `pg_textsearch` 1.0 (Tiger Data, Mar 2026): native BM25 reusing Postgres text-search configs, OR-only, no phrases.
- Dedicated DBs, 1M × 1536 (dev.to compilation, unverified): Qdrant 1,240 QPS / p95 6.8 ms vs pgvector 0.7 420 QPS / 14.2 ms, both ≥97 % recall.

**How we would implement it**

```sql
CREATE TEXT SEARCH CONFIGURATION fr_tax (COPY = french);
ALTER TEXT SEARCH CONFIGURATION fr_tax ALTER MAPPING FOR asciiword, word, hword, hword_part
  WITH unaccent, fr_tax_stem;  -- snowball french + own stopword file

CREATE TABLE chunks (
  id bigserial PRIMARY KEY, doc_id text, doc_hash text, doc_type text, tax_year int,
  lang char(2), heading_path text, body text,
  tsv tsvector GENERATED ALWAYS AS (to_tsvector('fr_tax', heading_path||' '||body)) STORED,
  emb halfvec(384));
CREATE INDEX ON chunks USING gin (tsv);
CREATE INDEX ON chunks USING hnsw (emb halfvec_cosine_ops) WITH (m=16, ef_construction=128);
CREATE INDEX ON chunks (doc_type, tax_year, lang);
CREATE INDEX ON chunks USING gin (heading_path gin_trgm_ops);

SET hnsw.iterative_scan = relaxed_order;
WITH lex AS (SELECT id, row_number() OVER (ORDER BY ts_rank_cd(tsv, q) DESC) r
             FROM chunks, websearch_to_tsquery('fr_tax', $1) q
             WHERE tsv @@ q AND doc_type = ANY($3) LIMIT 50),
     sem AS (SELECT id, row_number() OVER (ORDER BY emb <=> $2::halfvec) r
             FROM chunks WHERE doc_type = ANY($3) ORDER BY emb <=> $2::halfvec LIMIT 50)
SELECT id, SUM(1.0/(60+r)) s FROM (SELECT * FROM lex UNION ALL SELECT * FROM sem) u
GROUP BY id ORDER BY s DESC LIMIT 30;  -- then bge-reranker in Python
```

Incremental updates: compare `doc_hash` per document; delete + insert its chunks in one transaction (HNSW/GIN accept inserts). Bulk load: insert, then build HNSW with `maintenance_work_mem` ≥ index size.

**Expected gain and cost**

Retrieval quality: neutral, slightly negative if `ts_rank_cd` replaces tuned BM25 (exp 01 BM25 MRR 0.695 on A; `ts_rank` unmeasured). Operational gain: one service, ACID re-ingestion, filters, joins with user tables. Cost: ~2–3 days (schema, FTS config, harness backend); HNSW build for 1M × 384 on 4 cores ≈ tens of minutes (extrapolated).

**Risks / open questions**

- French Snowball over-stems (Paris → pari; synonym dictionary fixes known cases). Does `ts_rank_cd` lose ≥0.02 MRR vs bm25s? If yes: `pg_textsearch` (needs `shared_preload_libraries`) or ParadeDB (AGPL, external index files, backup/replication caveats).
- Filtered HNSW recall on rare `doc_type` — verify iterative scan.
- A 1024-dim model (bge-m3) triples memory; managed-Postgres support for BM25 extensions is patchy.

**Verdict**

**try-now** — Postgres is already in the production plan, pgvector + French FTS + RRF reproduces our hybrid pipeline in one query, and the only real risk (lexical ranking quality) is a one-day A/B against bm25s on the existing harness.

**Sources**

- https://github.com/pgvector/pgvector (0.8.6, read 2026-09)
- https://jkatz05.com/post/postgres/pgvector-scalar-binary-quantization/ (2024-04)
- https://aws.amazon.com/blogs/database/supercharging-vector-search-performance-and-relevance-with-pgvector-0-8-0-on-amazon-aurora-postgresql (2025-05)
- https://www.postgresql.org/docs/current/textsearch-dictionaries.html ; https://www.postgresql.org/docs/current/pgtrgm.html
- https://raw.githubusercontent.com/postgres/postgres/master/src/backend/snowball/stopwords/french.stop
- https://www.paradedb.com/blog/hybrid-search-in-postgresql-the-missing-manual (2025-10) ; https://www.paradedb.com/blog/benchmarker-iteration (2026-06)
- https://www.tigerdata.com/blog/pg-textsearch-bm25-full-text-search-postgres (2026-03)
