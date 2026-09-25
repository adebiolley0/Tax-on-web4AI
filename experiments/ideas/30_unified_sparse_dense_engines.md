# 30 — Unified sparse+dense engines vs two-index Python fusion

**Idea**

Store learned-sparse impact vectors in an inverted index next to HNSW dense vectors inside one engine and fuse server-side in a single query (Vespa `wand`+`nearestNeighbor`, OpenSearch/Elasticsearch `sparse_vector`+`knn`, Qdrant `prefetch`+fusion, Milvus `hybrid_search`, Infinity), instead of bm25s + numpy + scipy-CSR fused in Python.

**Why it fits this project**

- Exp 12 adds a third (SPLADE-style) leg; three in-process indexes at 1M chunks (bm25s, 3 GB fp32 matrix, 105k-dim CSR) are memory-heavy, and brute-force dense scoring becomes the latency floor (*unverified*: >100 ms/query on 4 cores).
- A unified engine gives persistence, filters (doc type, year, language) inside both legs, WAND/MaxScore pruning and one round-trip.
- The fusion itself is not the problem: convex/RRF over ≤300 candidates costs microseconds, and exp 03/14 tune weights and LTR offline — something most engines cannot express.

**Evidence** (checked 2026-09-25; *unverified* where marked)

| Engine | Sparse storage | One-query hybrid | Latency evidence |
|---|---|---|---|
| Vespa | `weightedset<int>`, `wand`, `rawScore` | YQL `OR`/`rank()`; phased ranking, `reciprocal_rank`, `normalize_linear`, free expressions | WAND scores ~2.2 % of MS MARCO vs 89 % for OR; no ms published [1][2][3] |
| OpenSearch 3.3 | `rank_features` (exact) or `sparse_vector` (SEISMIC ANN) | `hybrid` + normalization processor | two-phase P99 doc-only 198→124 ms, bi-encoder 617→122 ms (2.7–5.4M docs, 3×m5.4xlarge, Jun 2025); SEISMIC on 1.29 B docs: P50 11 ms vs exact 109 vs BM25 28, recall@10 90 %, ~1 GB RAM/1M docs (Oct 2025) [4][5] |
| Elasticsearch 9.1 | `sparse_vector`, 9-bit weights, pruning default on | `bool`+boost, `rrf`/`linear` retrievers | pruning 3–4× p99 gain; nDCG@100 0.51→0.37 unless rescored [6][7] |
| Qdrant ≥1.10 | exact inverted index, IDF modifier, u8/f16, memory tiers | `prefetch` + RRF (weighted 1.17) / DBSF / `formula` 1.14 | sparse leg adds +0.6–1.5 ms median (size unstated) [8][9] |
| Milvus 3.0 | DAAT_MAXSCORE/WAND, BLOCK_MAX, SINDI, `drop_ratio_search` | `hybrid_search` + RRF/Weighted ranker | none published [10][11] |
| Infinity | block forward + inverted | RRF / weighted / ColBERT rerank | embedded SDK 0.5.2 (Dec 2024, Linux only); MLDR 200k: three-way+ColBERT best [12][13] |
| Pyserini/Anserini | Lucene impact index (quantised weights), JVM | none | 8.8M, k=1000, 1 thread: SPLADE++ 5.1 qps vs BM25 29.8 (≈196 / 34 ms); 12 threads 48.8 / 278.9 qps [14] |
| PISA / Seismic | exact block-max WAND / approximate | none | 8.8M, 1 thread: SPLADE ~80 ms → 7 ms (BERT-tiny, sparser), BM25 ~4 ms; Seismic 0.2–0.5 ms at 90–97 % accuracy vs PISA ~100 ms [15][16] |
| LanceDB / pgvector | none (issue #1930 open) / `sparsevec` ≥0.7.0 | — | no SPLADE-scale numbers [17][18] |

Extrapolating from 8.8M, an exact impact index over 1M chunks should answer in ~10–40 ms single-threaded (*unverified*); latency is driven by posting density, hence every engine's pruning knobs.

**How we would implement it**

1. Only if exp 12 shows the sparse leg pays: Qdrant (single Rust binary) with `text_dense` (e5-base, HNSW) + `text_sparse` (SPLADE-fr, no IDF modifier) + payload filters; BM25 with French stemming stays in Tantivy/bm25s.
2. One `prefetch` per leg (limit 100–300, filters inside), weighted RRF or `formula`; compare with Python fusion on the leaderboard.
3. Vespa only if in-engine rank expressions (BM25 + rawScore + closeness + LTR) are wanted, at the price of a JVM/C++ container.

**Expected gain and cost**

- Quality: none from the engine — fusion parity at best; pruning/approximation can lose recall (ES −0.14 nDCG@100 without rescore).
- Latency/memory: HNSW replaces brute-force dense, WAND replaces CSR — real at 1M chunks, but Tantivy + an ANN index (ideas 16–18) give the same without a server.
- Cost: a service to run, three representations to re-ingest, 2–4 dev days; Vespa/OpenSearch clusters are oversized for a 4-core box.

**Risks / open questions**

- Fusion locked to engine primitives; tuned convex weights and exp 14 LTR stay in Python anyway.
- Qdrant sparse is exact but has no French analyser, so BM25 remains a second system.
- Infinity is Linux-only and stale; LanceDB has no sparse type; pgvector `sparsevec` HNSW on 30–105k-dim SPLADE is unbenchmarked.
- ELSER/OpenSearch models are English/WordPiece; we always bring our own French weights.

**Verdict**

**skip** — Python-side fusion is not the bottleneck and the engines add no ranking quality; revisit Qdrant only if exp 12 proves a learned-sparse leg and 1M-chunk brute-force dense scoring is the measured floor.

**Sources**

1. https://blog.vespa.ai/redefining-hybrid-search-possibilities-with-vespa/ (2024-01-19)
2. https://docs.vespa.ai/en/using-wand-with-vespa.html
3. https://docs.vespa.ai/en/learn/tutorials/hybrid-search.html
4. https://opensearch.org/blog/Introducing-a-neural-sparse-two-phase-algorithm/ (2025-06-18)
5. https://opensearch.org/blog/scaling-neural-sparse-search-to-billions-of-vectors-with-approximate-search/ (2025-10-28)
6. https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-sparse-vector-query ; https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/sparse-vector
7. https://www.elastic.co/search-labs/blog/text-expansion-pruning (2024-04-02)
8. https://qdrant.tech/documentation/search/hybrid-queries/ ; https://qdrant.tech/documentation/concepts/indexing/
9. https://qdrant.tech/articles/before-tuning-a-qdrant-collection/
10. https://milvus.io/docs/sparse-inverted-index.md
11. https://milvus.io/docs/multi-vector-search.md
12. https://infiniflow.org/blog/multi-way-retrieval-evaluations-on-infinity-database (2024-07-29)
13. https://pypi.org/project/infinity-embedded-sdk/
14. https://arxiv.org/abs/2311.18503 (Anserini ONNX, Nov 2023, Table 2)
15. https://arxiv.org/abs/2207.03834 (SPLADE efficiency study, SIGIR 2022)
16. https://arxiv.org/html/2404.18812v1 (Seismic)
17. https://github.com/lancedb/lancedb/issues/1930
18. https://www.paradedb.com/blog/introducing-sparse (pgvector 0.7.0 `sparsevec`)
