# 84 — Incremental index updates and zero-downtime reindexing in embedded stores

**Idea**

Apply idea 64's monthly delta to the *store* without stopping the MCP server: write into a new **immutable snapshot** (LanceDB version, Tantivy commit, or a blue/green directory), flip to it atomically after eval gating, and keep lexical, vector and metadata in one consistency boundary — a single SQLite ledger row says "snapshot N is live".

**Why it fits this project**

- The server is a single in-process FastMCP reader (`exp 04` opens the table once); refresh is a monthly batch job on the same box (~1.5k documents): *one* writer, *one* long-lived reader — the easiest case for every store.
- Three legs (BM25, vectors, SQL metadata) must agree on the chunk set, or fusion silently degrades.
- A bad refresh (broken Dutch bodies, idea 62; hash collapse bugs, idea 25) must be reversible in seconds.

**Evidence**

- LanceDB: every `add`/`update`/`delete`/`merge_insert` **creates a new version**; `merge_insert` = `when_matched_update_all / when_not_matched_insert_all / when_not_matched_by_source_delete`; deletes are soft (deletion files), updated rows are "moved out of any existing index" and flat-searched until `optimize()`, which compacts, prunes versions older than 7 days (default) and folds new rows into vector/scalar/FTS indexes. **Tagged versions are exempt from cleanup**. `read_consistency_interval` unset = "no automatic cross-process refresh"; 0 = check every read; else eventual; or explicit `checkout_latest`.
- Lance pitfalls: #6607 (open, 2026) `cleanup_old_versions` deletes files under a checked-out reader → `NotFound` mid-scan; workaround: a temporary tag. #5194 (open) commits slow down as fragments accumulate; #7941 proposes hierarchical manifests because opens/commits are O(total fragments). LanceDB #1065 (open): consistency reloads run on the read path.
- Tantivy: `commit()` publishes and persists; `rollback()` returns to the last commit; one `IndexWriter` (lockfile, can go stale after a panic); `IndexReader` default `OnCommitWithDelay`, "the same searcher must be used for a given query" (segment snapshot); `garbage_collect_files()` explicit.
- SQLite WAL: readers never block the single writer; a checkpoint stops at any active reader's snapshot, so permanent readers → "WAL file will grow without bound" unless `wal_checkpoint(TRUNCATE)`; same host only. FTS5 external-content: the user keeps index and content consistent (triggers; delete FTS row *before* content row); `'rebuild'` discards and rebuilds; `'optimize'` "can take a long time", `'merge', N` splits it; `crisismerge` (16) can stall one insert. sqlite-vec `vec0`: brute-force KNN, no ANN (pre-v1).

**How we would implement it**

1. **Snapshot directory per refresh**: `store/2026-09/` = LanceDB table (or Tantivy index + sqlite-vec file) + `ledger.sqlite`, built from idea 64's delta with `merge_insert` on `chunk_id`.
2. **Atomic flip**: `store/current` symlink swapped with `os.replace` after the eval harness passes; the server watches the symlink and re-opens the table between requests (in-flight queries finish on the old handle). Keep N−1 for instant rollback.
3. **In-place variant (LanceDB only)**: `merge_insert` → `optimize()` → `tag("2026-09")`; server keeps `read_consistency_interval=None` and calls `checkout_latest` only when the ledger's `live_version` advances. Tag before cleanup (#6607); `optimize()` monthly, not per commit (#5194).
4. **Consistency boundary**: one SQLite transaction commits `(snapshot_id, lance_version, tantivy_opstamp, chunk_count, eval_mrr)`; the server refuses a snapshot whose three counts disagree.
5. **Backup**: the snapshot directory *is* the backup (Lance files are immutable; `sqlite3 .backup` for the ledger); `rsync` off-box; restore = repoint `current`.

**Expected gain and cost**

Zero-downtime refresh with second-level rollback; refresh cost bounded by idea 64's delta (minutes). Disk ≈ 2× live corpus — a few GB at 200k chunks. Engineering: ~2 days for flip + ledger, +1 day for in-place LanceDB versioning. Retrieval quality unchanged by construction; the gain is operational.

**Risks / open questions**

- LanceDB flat-scan latency on unindexed rows between `merge_insert` and `optimize()` — small at 1.5k docs/month, measure.
- Version bloat if a daily cursor commits often (#5194/#7941); blue/green sidesteps it.
- Symlink swap and SQLite WAL both assume local disk; no NFS.
- Stale Tantivy lockfile after a crash needs manual removal.
- Can FastMCP re-open a handle safely mid-stream? Test it.

**Verdict**

**try-now** — blue/green snapshot directories with an atomic symlink flip and a one-row SQLite ledger give zero-downtime refresh and rollback with any of the three stores, in ~2 days, and avoid every documented Lance/FTS5 pitfall.

**Sources**

- https://docs.lancedb.com/tables/versioning.md
- https://docs.lancedb.com/tables/update.md
- https://docs.lancedb.com/tables/consistency.md
- https://docs.lancedb.com/indexing/reindexing.md
- https://docs.lancedb.com/performance.md
- https://github.com/lancedb/lance/issues/6607
- https://github.com/lancedb/lance/issues/5194
- https://github.com/lancedb/lance/issues/7941
- https://github.com/lancedb/lancedb/issues/1065
- https://docs.rs/tantivy/0.26.2/tantivy/indexer/struct.IndexWriter.html
- https://docs.rs/tantivy/latest/tantivy/struct.IndexReader.html
- https://www.sqlite.org/wal.html
- https://www.sqlite.org/fts5.html
- https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/index.html (brute-force claim, from memory, unverified)
