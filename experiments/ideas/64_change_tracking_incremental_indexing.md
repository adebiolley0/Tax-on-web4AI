# 64 — Change tracking and incremental re-indexing

**Idea**

Treat the index as a derived table that is *refreshed*, never rebuilt: consume the Fisconet+ monthly change feed, hash documents and chunks, give chunks stable content-addressed ids so unchanged chunks keep their embeddings, soft-delete superseded chunks, fold "same article, new edition" into topic 25's validity metadata instead of adding a copy, compact periodically, and gate every refresh with the eval harness.

**Why it fits this project**

- Fisconet+ ships a feed: `changes/searches?language=fr&month=8&year=2026` returned **1,612 rows / 1,346 GUIDs** (`status` New 1,207 / Updated 405; `version` "1.0"…"73.0"; `date`, `documentDate`), and `document/{guid}` adds `lastModified`. `get_monthly_changes()` exists in `fisconet/client.py` but nothing consumes it.
- The same month carried the yearly rollover: `CIR 92 - Revenus 2026` and `AR/CIR 92 - Revenus 2026` ×4 regions, 66 "Revenus 20xx" titles — mostly byte-identical to 2025 (idea 25 checked `Article 145^10` ×3). Re-embedding them is waste.
- CPU budget: e5-small = 3.3 h for 201k chunks; bge-m3 ~1 h/1k (EXPERIMENTS.md §3.3). At 100k documents a full rebuild is 16 h (e5-small) to weeks (bge-m3); a monthly delta of ~1.5k documents is minutes.
- `chunker.py` already computes `content_hash = sha256(chunk_text)`; `ingest.py` calls `upsert_chunks` — primitives exist, bookkeeping does not.

**Evidence**

- Fisconet+ feed probed live 2026-09-25; `pageFilters.publicationDates` lists 21 publication days, so a daily cursor is possible.
- LanceDB: `merge_insert(key).when_matched_update_all().when_not_matched_insert_all()` = upsert; deletes are soft and excluded from index segments; updated rows "are moved out of any existing index… still show up… not as fast"; every write advances `version`; `optimize()` compacts and cleans versions (7-day retention); `list_versions/checkout/restore` give rollback.
- SQLite FTS5 external-content tables: `'delete'` command / triggers sync the index; `'merge'`, `'automerge'`, `'optimize'`, `'rebuild'` for maintenance.
- Lucene `updateDocument()` "just deletes and then adds"; deletes are reclaimed on segment merge — the pattern we copy.
- dbt `materialized='incremental'`, `unique_key`, `is_incremental()` watermark, `--full-refresh`; Prefect cache keys `INPUTS + TASK_SOURCE` (re-embed only when text *or* chunker/model code changes).
- FiscalQA Pro (arXiv 2608.09393): 32,436 article-versions; version-aware index 98.3 % vs 2.7 % static — the target edition model.

**How we would implement it**

1. **Ledger** (SQLite): `document(guid, version, last_modified, doc_hash, status)`, `chunk(chunk_id, guid, canonical_id, chunk_hash, embed_key, valid_from, valid_to, deleted_at)`. `chunk_id = sha256(canonical_id | chunk_hash)[:16]`; `embed_key = sha256(chunk_hash | model | chunker_version)` — the embedding cache in `rag_eval/cache.py` becomes the source of truth.
2. **Refresh job** (monthly or daily): pull feed → skip known `(guid, version)` → `fetch_document` → filtering policy → normalise + `doc_hash`; unchanged → bump metadata only. Else chunk and diff hashes: unchanged → keep; new → embed (`run_queue.sh`); missing → set `deleted_at`.
3. **Edition folding**: for codes/AR derive `canonical_id` (`cir92:145/10`, region) from title/path; equal `chunk_hash` under a new edition GUID → append GUID to `source_guids`, extend `valid_to`; different hash → new version row (topic 25), old one closed.
4. **Store**: LanceDB `merge_insert("chunk_id")`, `delete(...)`, `optimize()` after each refresh; rebuild FTS/vector indexes when `index_stats().num_unindexed_rows` exceeds ~5 % (threshold unverified). Table version logged for rollback.
5. **Regression gate**: run A/B/C question sets after each refresh, append to `leaderboard.jsonl` with `refresh_id`; fail if MRR drops > 0.02 or an expected doc id disappears; `checkout(previous_version)` on failure. Keep a `--full-refresh` path for model/chunker changes.

**Expected gain and cost**

Monthly refresh falls from a full re-embed (3.3 h now, ~16 h at 100k docs, e5-small) to minutes for ~1.5k changed documents, most yearly editions hash-collapsing; index bloat drops (−30 % per idea 25). No retrieval-quality gain by itself — the gain is *not losing* quality while the corpus moves. Cost: ~3 days, no new models, no LLM.

**Risks / open questions**

- Feed semantics unverified: is `Updated` fired for metadata-only edits? Withdrawn documents are not exposed (only New/Updated seen) — a yearly full crawl may be needed as reconciliation.
- Hash the normalised article unit, not whole-code PDFs, or trivial header changes re-embed everything.
- Chunk-boundary drift: an inserted paragraph shifts later chunks; article-anchored chunking (exp 05) limits this.
- LanceDB unindexed-row slowdown and compaction timing on our box are untested.

**Verdict**

**try-now** — feed, hashes and upsert primitives already exist; a ledger plus a leaderboard gate is cheap insurance before the corpus reaches 100k documents.

**Sources**

- https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/changes/searches?language=fr&month=8&year=2026 (probed 2026-09-25)
- https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/document/858ce212-1485-4058-a1a0-13af78c8945d?language=fr (`lastModified`)
- https://docs.lancedb.com/tables/update
- https://lancedb.github.io/lancedb/python/python/ (Table API)
- https://www.sqlite.org/fts5.html
- https://lucene.apache.org/core/10_0_0/core/org/apache/lucene/index/IndexWriter.html
- https://docs.getdbt.com/docs/build/incremental-models
- https://docs.prefect.io/v3/concepts/caching
- https://arxiv.org/abs/2608.09393 (FiscalQA Pro)
- Local: `ingestion/src/tax_ingestion/fisconet/client.py`, `storage/chunker.py`, `experiments/EXPERIMENTS.md` §3.3, `ideas/25_temporal_versioned_indexing.md`
