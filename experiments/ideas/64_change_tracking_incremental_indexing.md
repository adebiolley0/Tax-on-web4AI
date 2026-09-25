# 64 — Change tracking and incremental re-indexing

**Idea**

Treat the index as a derived table that is *refreshed*, never rebuilt: consume the Fisconet+ monthly change feed, hash at document and chunk level, give chunks stable content-addressed ids so unchanged chunks keep their embeddings, soft-delete superseded chunks, fold "same article, new edition" into the validity metadata of topic 25 instead of adding a copy, compact the store periodically, and gate every refresh with the eval harness.

**Why it fits this project**

- Fisconet+ ships a feed: `changes/searches?language=fr&month=8&year=2026` returned **1,612 rows / 1,346 GUIDs** (`status` New 1,207 / Updated 405; `version` "1.0"…"73.0"; `date`, `documentDate`, `created`), and `document/{guid}` adds `lastModified`. `get_monthly_changes()` already exists in `ingestion/src/tax_ingestion/fisconet/client.py` but nothing consumes it.
- The same month carried the yearly rollover: `CIR 92 - Revenus 2026 (PDF)` ×4 regions, `AR/CIR 92 - Revenus 2026` ×4, 66 "Revenus 20xx" titles — mostly byte-identical to the 2025 edition (idea 25 checked `Article 145^10` ×3). Re-embedding them is pure waste.
- CPU budget: e5-small = 3.3 h for 201k chunks; e5-base 240 s/1k; bge-m3 ~1 h/1k (EXPERIMENTS.md §3.3). At 100k documents (~1M chunks) a full rebuild is 16 h (e5-small) to weeks (bge-m3); a monthly delta of ~1.5k documents is minutes.
- `chunker.py` already computes `content_hash = sha256(chunk_text)`; `ingest.py` calls `upsert_chunks` — the primitives exist, the bookkeeping does not.

**Evidence**

- Fisconet+ feed structure: probed live 2026-09-25 (see above); `pageFilters.publicationDates` lists 21 publication days per month, so a daily cursor is possible.
- LanceDB (docs.lancedb.com/tables/update): `merge_insert(key).when_matched_update_all().when_not_matched_insert_all()` = upsert; deletes are soft ("marked for deletion") and excluded from index segments; updated rows "are moved out of any existing index… still show up… not as fast"; every write advances `version`; `optimize()` compacts and cleans versions (default 7-day retention); `list_versions/checkout/restore` allow rollback of a bad refresh.
- SQLite FTS5 external-content tables: `'delete'` command / triggers keep the index in sync; `'merge'`, `'automerge'`, `'optimize'`, `'rebuild'` for maintenance (sqlite.org/fts5.html).
- Search engines: Lucene `updateDocument()` "just deletes and then adds", deletes are per-segment and reclaimed on merge (`forceMerge`) — the soft-delete + compaction pattern we copy.
- Pipelines: dbt `materialized='incremental'`, `unique_key`, `is_incremental()` watermark, `--full-refresh` escape hatch; Prefect cache keys from `INPUTS + TASK_SOURCE` (re-run embedding only when text *or* chunker/model code changes).
- FiscalQA Pro (arXiv 2608.09393): 32,436 article-versions; version-aware index 98.3 % vs 2.7 % static — the target data model for editions.

**How we would implement it**

1. **Ledger** (SQLite, alongside the store): `document(guid, version, last_modified, doc_hash, status, seen_in_feed)`, `chunk(chunk_id, guid, canonical_id, chunk_hash, embed_key, valid_from, valid_to, deleted_at)`. `chunk_id = sha256(canonical_id | chunk_hash)[:16]`; `embed_key = sha256(chunk_hash | model | chunker_version)` (Prefect-style key) — the embedding cache in `rag_eval/cache.py` becomes the source of truth.
2. **Refresh job** (monthly, or daily via `publicationDates`): pull feed → skip rows whose `(guid, version)` is known → `fetch_document` → apply filtering policy → normalise + `doc_hash`; if unchanged, only bump metadata. Else chunk, diff chunk hashes against the ledger: unchanged → keep row; new → embed (queued, `run_queue.sh`); missing → set `deleted_at`.
3. **Edition folding**: for `Code et législation` / `Arrêtés royaux`, derive `canonical_id` (`cir92:145/10`, region) from title/path; equal `chunk_hash` under a new edition GUID → append GUID to `source_guids`, extend `valid_to`; different hash → new version row (topic 25 schema), old one closed.
4. **Store**: LanceDB `merge_insert("chunk_id")` for upserts, `delete("chunk_id IN (...)")`, then `optimize()` after each refresh and a rebuild of FTS/vector indexes when `index_stats().num_unindexed_rows` exceeds ~5 % (threshold unverified). Table version recorded in the ledger for rollback.
5. **Regression gate**: run corpora A/B/C question sets through the harness after each refresh, append to `leaderboard.jsonl` with `refresh_id`; fail if MRR drops > 0.02 or any expected doc id disappears; `checkout(previous_version)` on failure. A `--full-refresh` path (dbt) remains for model/chunker changes.

**Expected gain and cost**

Monthly refresh cost falls from a full re-embed (3.3 h → ~16 h at 100k docs, e5-small) to minutes for ~1.5k changed documents, of which the 66+ yearly-edition PDFs mostly hash-collapse. Index bloat from editions drops (−30 % per idea 25). No retrieval-quality gain by itself; the gain is *not losing* quality while the corpus moves. Cost: ~3 days (ledger, feed consumer, folding heuristics, gate), no new models, no LLM.

**Risks / open questions**

- Feed semantics unverified: is `Updated` fired for metadata-only edits? Are deletions/withdrawn documents exposed at all (only New/Updated seen) — a yearly full crawl may still be needed as reconciliation.
- Whole-document text dumps (`CIR 92 PDF`) vs per-article documents: hashing must run on the normalised article unit, or trivial header changes re-embed everything.
- Chunk-boundary drift: one inserted paragraph shifts all later chunks; article-anchored chunking (exp 05) limits this.
- LanceDB unindexed-row slowdown and compaction timing on the 4-core box are untested.

**Verdict**

**try-now** — the feed, hashes and upsert primitives already exist; wiring a ledger and a leaderboard gate is cheap insurance before the corpus grows to 100k documents.

**Sources**

- https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/changes/searches?language=fr&month=8&year=2026 (probed 2026-09-25)
- https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/document/858ce212-1485-4058-a1a0-13af78c8945d?language=fr
- https://docs.lancedb.com/tables/update
- https://lancedb.github.io/lancedb/python/python/ (Table.merge_insert, optimize, cleanup_old_versions, list_versions, checkout, restore, index_stats)
- https://www.sqlite.org/fts5.html
- https://lucene.apache.org/core/10_0_0/core/org/apache/lucene/index/IndexWriter.html
- https://docs.getdbt.com/docs/build/incremental-models
- https://docs.prefect.io/v3/concepts/caching
- https://arxiv.org/abs/2608.09393 (FiscalQA Pro)
- Local: `ingestion/src/tax_ingestion/fisconet/client.py`, `ingestion/src/tax_ingestion/storage/chunker.py`, `experiments/EXPERIMENTS.md` §3.3/§3.9, `experiments/ideas/25_temporal_versioned_indexing.md`
