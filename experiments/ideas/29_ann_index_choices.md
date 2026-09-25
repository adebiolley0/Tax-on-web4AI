# 29 — ANN index choice at 200k–1M chunks on a 4-core CPU

**Idea**

Keep the dense leg **exact** (brute-force matmul over an int8/fp16 matrix) up to ~1M chunks, applying metadata filters as a boolean mask *before* the scan. Move to a graph index (usearch/hnswlib HNSW, or LanceDB `IVF_HNSW_SQ`) only if p95 retrieval must fall below ~20 ms at 1M rows. Never IVF-PQ at 384-d.

**Why it fits this project**

Our measured 30 ms for 200k×384 sits far below the pipeline's real cost (query embedding, BM25 leg, cross-encoder rerank of 30 candidates = seconds). Exact search gives recall@10 = 1.0 by construction, needs no build, tuning or re-index when Fisconet+ adds chunks, and makes filters (region, year, doc type, FR/NL) free and exact — precisely where ANN indexes break. The LanceDB IVF-PQ loss at 8k rows was the PQ code, not IVF; LanceDB itself now steers IVF_PQ to "dimension ≤ 256".

**Evidence**

- Extrapolating our 30 ms/200k: 1M×384 fp32 ≈ 150 ms single-thread numpy; faiss `IndexFlatIP` on 4 threads ≈ 50–80 ms (estimate). Memory 1.5 GB fp32, 0.38 GB int8. Faiss wiki: only `IndexFlat*` "can guarantee exact results"; HNSW costs `(d·4 + M·2·4)` B/vector → 1.7 GB per 1M at 384-d/M=16 (0.5 GB with int8).
- USearch benchmarks (64-core Graviton3, 256-d): i8 vs f32 = 275k vs 172k QPS at recall@1 98.9 % vs 99.1 % — "almost no quantization loss".
- ann-benchmarks glove-100 (1.18M×100): hnswlib recall 0.95 at ~28k QPS, 0.985 at ~16k QPS single-thread — ~1000× a flat scan, relevant only once the scan is the bottleneck.
- "Bang for the Buck" (arXiv 2505.07621, May 2025, 8 vCPU): flat scans and IVF are memory-bandwidth-bound; Sapphire Rapids sequential-access latency was ~2× Zen and ~4× Graviton, so flat-scan time varies 2–4× by CPU.
- LanceDB docs (2026): `IVF_HNSW_SQ` "best recall/latency trade-off" (~1/4 raw); "if your vector search frequently includes metadata filters, use IVF_RQ or IVF_PQ" since HNSW-backed indexes "can show higher latency variance"; `bypass_vector_index()` gives the exact scan. Medium (2023): a 30k-row IVF_PQ table plateaued at 70 % recall with all partitions probed; `refine_factor=5` restored 100 %.
- Filtered ANN: arXiv 2602.11443 (Feb 2026) — post-filtering fails at low selectivity because the `efSearch` pool holds too few valid candidates; Milvus switches to brute force when a filter removes >93 % of vectors; Qdrant's filterable HNSW adds payload-aware edges and full-scans below 10 KB. Weaviate ACORN (Nov 2024): at 20 % selectivity plain HNSW has half ACORN's QPS; at 50 % plain wins. arXiv 2509.07789 (Sep 2025, 10 methods, 66 datasets): pre-filter brute force stays competitive whenever the filter is restrictive.
- Chunked-corpus caveat (NornicDB #425, Sep 2026, 487k×1024): HNSW at M=16/ef=50 matched exact search on only ~53 % of hits, 83 % at ef=2000 — attributed to chunk→document collapsing, i.e. our multi-chunk-per-article layout.
- DiskANN/Vamana (SSD-resident, "billion-scale on 64 GB RAM"), SPANN and ScaNN target 100M+ vectors; ScaNN's edge is SIMD 4-bit PQ, which faiss `PQ4fs` matches. None pays off at ≤1M in-RAM vectors.

**How we would implement it**

1. One contiguous `np.int8` (or fp16) matrix, `np.memmap`-backed; `(X @ q).argpartition(k)` with 4 BLAS threads; rescore top-50 in float if int8.
2. Filters: SQL/DuckDB → row-id mask → masked matmul (`X[mask] @ q` when selectivity <10 %).
3. Benchmark N ∈ {200k, 500k, 1M} × {fp32, int8} × threads {1, 4}; log p50/p95 to `leaderboard.jsonl`.
4. Escape hatch if p95 > 100 ms at 1M: `usearch` HNSW (i8, M=16, ef_construction=128, ef=64–128; build ≈ minutes on 4 cores, unverified; 0.5 GB) or LanceDB `IVF_HNSW_SQ` with `nprobes` ≈ 5–10 % of partitions plus `refine_factor`. Validate recall@10 against exact on sets A/B/C.

**Expected gain and cost**

Quality: 0 (exact). Latency: 30 → ~60–150 ms at 1M, invisible next to the reranker. Cost: half a day for the int8 + mask path; no build or maintenance. HNSW escape: 1–2 days, −0.5–2 % recall@10, +0.5 GB RAM, rebuild on bulk ingest.

**Risks / open questions**

- Box is ~13/15 GB used: 1M fp32 (1.5 GB) may not fit; int8/fp16 is mandatory at that size.
- Concurrent MCP clients multiply 100 ms scans; a graph index scales QPS far better.
- Near-duplicate FR/NL chunks and hubness can make HNSW recall worse than benchmark curves — must measure.
- All latency figures above come from other hardware; flat scans are bandwidth-bound.

**Verdict**

**try-now** — at 200k chunks brute force is simply right (exact, filter-friendly, zero maintenance); the only work worth doing is the int8/masked scan plus a 1M-row timing run, with usearch HNSW as the pre-validated escape hatch.

**Sources**

- https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index ; https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
- https://docs.lancedb.com/indexing/vector-index ; https://medium.com/etoai/benchmarking-lancedb-92b01032874a
- https://github.com/unum-cloud/usearch/blob/main/BENCHMARKS.md ; https://github.com/nmslib/hnswlib
- https://ann-benchmarks.com/ ; https://issues.apache.org/jira/browse/LUCENE-9937 (hnswlib glove-100 numbers)
- https://arxiv.org/html/2505.07621v1 (Bang for the Buck, May 2025)
- https://arxiv.org/html/2602.11443 (filtered ANN systems, Feb 2026) ; https://arxiv.org/html/2509.07789v1 (FANNS benchmark, Sep 2025)
- https://weaviate.io/blog/speed-up-filtered-vector-search ; https://qdrant.tech/articles/vector-search-filtering/ ; https://qdrant.tech/documentation/manage-data/indexing/
- https://github.com/orneryd/NornicDB/issues/425 (Sep 2026, chunked-corpus HNSW recall)
- https://zvec.org/en/blog/2026-08-04-zvec-diskann/ ; https://medium.com/@kumon/similarity-search-scann-and-4-bit-pq-ab98766b32bd
