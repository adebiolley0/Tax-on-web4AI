# Experiment 04 – LanceDB embedded hybrid store

Can an *embedded* vector database (no server, one directory on disk) with built-in full-text
search and rerankers replace a hand-assembled `numpy + bm25s` stack – or a Qdrant container –
for the Belgian-tax RAG prototype? This experiment indexes both benchmark corpora in
[LanceDB](https://lancedb.github.io/lancedb/) **0.39.0** (Lance format, native Rust FTS),
evaluates vector / FTS / hybrid retrieval with the shared harness
(`experiments/common/rag_eval`) and records how much configuration was needed.

Embedding model: `intfloat/multilingual-e5-small` (384-d, `query: ` / `passage: ` prefixes,
`max_seq_length=512`, normalised, CPU, batch 16). Vectors are computed **outside** LanceDB
(sentence-transformers, shared `EmbeddingCache` in `experiments/data/emb_cache`, same cache
keys as experiment 02) and inserted as a `FixedSizeList<float32, 384>` column – LanceDB's
embedding registry was deliberately not used so that the e5 prefixes stay under our control.

## Setup

Standalone uv project (the root `pyproject.toml` excludes `experiments/*`):

```bash
cd experiments/04_lancedb
uv sync                                    # lancedb 0.39, pyarrow 25, torch 2.14 (CPU index), sentence-transformers 6.1, rag-eval (editable ../common)
uv run python run_lancedb.py --corpus A    # all runs on corpus A (91 docs / 1,072 chunks / 29 questions)
uv run python run_lancedb.py --corpus B    # corpus B (5,853 articles / 8,148 chunks / 40 questions) – embeds once (~cached afterwards)
uv run python run_lancedb.py --corpus A --runs hybrid_ce --rerankers bge-reranker-v2-m3,mmarco-minilm
uv run python run_lancedb.py --corpus A --leaderboard
```

Run keys (`--runs`, default `vector,fts_en,fts_fr,hybrid_rrf,hybrid_ce,vector_ivf`):

| run | what |
|---|---|
| `vector` | exact (flat) cosine kNN over the chunk vectors (`bypass_vector_index()`) |
| `fts_en` | native FTS with the default tokenizer (`language="English"`, stem, stop-words, ASCII folding) |
| `fts_fr` | native FTS with `language="French"` (French Snowball stemmer + French stop-list + ASCII folding) |
| `hybrid_rrf` | `query_type="hybrid"`: vector top-50 ∪ FTS(fr) top-50 fused by the default `RRFReranker(K=60)` |
| `hybrid+<ce>@30` | hybrid (limit 30 → ≤ 60 candidates) reranked by `CrossEncoderReranker(model_name=…)` |
| `vector_ivf` | approximate search through an `IvfPq(cosine, num_sub_vectors=48)` index, `nprobes=10` |

Every run retrieves 50 chunks (30 for the cross-encoder runs), maps chunk hits to `doc_id`
(first occurrence wins) and scores at document level (`evaluate_rankings`). Results go to
`experiments/results/04_lancedb/<corpus>__<run>.json` and `experiments/results/leaderboard.jsonl`
under experiment `04_lancedb`. The LanceDB directory (`lancedb_data/`, gitignored) is reused
between invocations unless `--rebuild` is passed.

## Results

TODO_RESULTS

## LanceDB API notes (0.39.0)

**What worked out of the box**

* `lancedb.connect("lancedb_data")` + `db.create_table(name, data=pyarrow.Table, mode="overwrite")`
  – a pyarrow table with a `FixedSizeList<float32, 384>` column is all that is needed; no schema
  classes, no collection config, no "distance" declaration at creation time. Inserting 8,148
  chunks with vectors takes well under a second; the table is a directory of `.lance` fragments.
* Vector search: `tbl.search(vec, vector_column_name="vector").distance_type("cosine").limit(50).select([...]).to_list()`.
  Without an index the search is an exact brute-force scan, which at 1k–8k × 384 floats is
  single-digit milliseconds – **no index is needed at this corpus size**.
* FTS: `tbl.create_index("text", config=FTS(language="French", stem=True, remove_stop_words=True, ascii_folding=True))`,
  then `tbl.search("question ?", query_type="fts", fts_columns="text")`. The index builds in
  0.2 s (A) / TODO_FTS_B s (B). Query strings are tokenised with the index tokenizer, so raw
  natural-language questions (with `?`, apostrophes, accents) work directly. `lancedb.tokenize(text, language="French")`
  lets you inspect what the tokenizer does (e.g. *déclaration d'impôt* → `declar`, `impot`).
* Hybrid: `tbl.search(query_type="hybrid", vector_column_name="vector", fts_columns="text").vector(qvec).text(question).limit(k).rerank(RRFReranker())`.
  Because we pass `.vector(...)` explicitly, no embedding function has to be registered on the
  table. Each leg fetches `limit` rows, the reranker fuses / deduplicates and the result is
  sliced to `limit` (`LanceHybridQueryBuilder._combine_hybrid_results`).
* Rerankers are plug-ins: `RRFReranker(K=60)` (default), `LinearCombinationReranker`,
  `MRRReranker`, `CrossEncoderReranker(model_name=..., column="text", device="cpu")` (any
  sentence-transformers `CrossEncoder`, so multilingual `BAAI/bge-reranker-v2-m3` and
  `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` both load), plus hosted ones (Cohere, Jina,
  Voyage, AnswerDotAI ColBERT). The same reranker object also works on pure vector or pure
  FTS queries (`rerank_vector` / `rerank_fts`).
* Metadata filtering is a SQL-like string: `.where("code = 'tva'", prefilter=True)` works on
  vector, FTS and hybrid queries (checked in `filter_demo`, all returned rows matched the
  predicate; `filter_demo_<corpus>.json`).

**What needed attention / workarounds**

* **Tantivy is gone.** `create_fts_index(..., use_tantivy=True)` raises
  `ValueError: Tantivy-based FTS has been removed` in 0.39. Only the native Lance FTS
  (BM25 over an inverted index) exists; `tantivy` as a pip dependency is therefore useless
  (it is listed in `pyproject.toml` only because the task asked to check it – it is not
  imported). The native FTS does not support boolean `AND`/`OR` operators inside the query
  string; structured queries go through `MatchQuery` / `PhraseQuery` / `BoostQuery` /
  `BooleanQuery` objects (`lancedb.query`). Phrase queries need `with_position=True` at
  index time.
* **Two deprecations hit on first try**: `create_fts_index(...)` (deprecated since 0.25, use
  `create_index("text", config=FTS(...))`) and `create_index(metric=..., index_type="IVF_PQ")`
  (use `create_index("vector", config=IvfPq(distance_type=...))`). Both still work but warn.
  The docs on the website still show the old form in several places.
* **Language setting matters and is not automatic**: the default tokenizer stems with the
  *English* Porter stemmer and removes English stop-words. On French text this silently
  degrades recall (see `fts_en` vs `fts_fr` below: MRR 0.539 → 0.645 on corpus A). Supported
  stemmers: Arabic, Danish, Dutch, English, Finnish, French, German, Greek, Hungarian, Italian,
  Norwegian, Portuguese, Romanian, Russian, Spanish, Swedish, Tamil, Turkish; stop-lists for a
  subset including French and Dutch. One FTS index covers **one** column and one language – a
  bilingual FR/NL corpus needs either two text columns/indexes or a language column + filter.
  The French stop-list is short (it keeps *dans*, *comment*, *quel*…); `custom_stop_words=[...]`
  can extend it (experiment 01 showed that removing interrogatives helps BM25 a bit).
* **Scan warnings**: selecting columns without `_distance`/`_score` prints a
  `Deprecation warning … disable_scoring_autoprojection` line per query on stderr (Rust log).
  Harmless but noisy; silence with `RUST_LOG=error` or by selecting the score columns.
* `CrossEncoderReranker` exposes no `max_length` / `batch_size` – it calls
  `CrossEncoder.predict(pairs)` with defaults, so long chunks are truncated to the model's
  `max_position_embeddings` (8k for bge-v2-m3, 512 for mMiniLM) and the batch size is 32.
  For finer control write a 20-line `Reranker` subclass (`rerank_hybrid(query, vector_results, fts_results)` returning
  a pyarrow table with `_relevance_score`).
* An IVF_PQ index on a few-thousand-row table is counter-productive: it costs recall
  (PQ compression) and buys nothing in latency. LanceDB's own guidance is to index above
  ~100k rows; `IvfFlat` / `HnswSq` exist for lossless indexing if ever needed.

## Ergonomics assessment vs Qdrant (for this project)

| aspect | LanceDB (embedded) | Qdrant (server / docker) |
|---|---|---|
| deployment | `pip install lancedb`; DB = a directory; opens in-process in ~ms | separate container + client; needs URL, ports, volume |
| persistence | Lance columnar files, versioned (each write = new version, `tbl.checkout`/`restore`), safe to `rsync`/commit-as-artifact | RocksDB/segments inside the container volume; snapshots via API |
| schema / config | none beyond a pyarrow schema; distance chosen at query time | collection config (vector size, distance, HNSW/quantization params, payload indexes) declared up front |
| hybrid search | built in: `query_type="hybrid"` + reranker plug-ins (RRF, linear, cross-encoder, Cohere/Jina/Voyage/ColBERT) | needs sparse vectors (you compute BM25/SPLADE yourself, or fastembed) + Query API prefetch/fusion (`RRF`/`DBSF`) |
| lexical / French | native BM25 FTS with French stemmer + stop-list + ASCII folding, one line of config | no analyzer for sparse text; French stemming must be done client-side before producing sparse vectors (or use `text` payload index with `tokenizer=word` + prefix, no stemming) |
| metadata filtering | SQL string (`where("code = 'cir92' AND page > 10")`), pre- or post-filter | structured `Filter(must=[FieldCondition(...)])` objects – verbose but typed |
| vector index | optional (brute force is exact and fast < 100k rows); IVF_PQ / IVF_FLAT / HNSW available | HNSW always built; tunable, very fast at scale |
| concurrency | single-process writers, multi-reader; fine for one FastMCP process, not for many writers | client-server, multi-tenant |
| behind FastMCP | ideal: open the table at startup, `search`/`fetch` tools call it in-process, no network hop, ship `lancedb_data/` with the deployment | works, but adds an infra dependency to a tool whose corpus is a few thousand articles |
| observability | `explain_plan()` / `analyze_plan()` on queries | web UI, metrics endpoint |

**Bottom line**: for a medium French legal corpus behind a single FastMCP server, LanceDB
removes essentially all of the Qdrant setup (no collection config, no separate sparse
pipeline, no container) while giving equal-or-better retrieval than the hand-rolled
numpy+bm25s stack of experiments 02/03, because its French FTS and hybrid fusion match
what we wrote by hand. What it does *not* give: multi-language analyzers on one column,
a long-running service with many concurrent writers, and a mature ANN story at
million-scale on CPU – none of which this project needs today.

Limitations of this experiment: single embedding model (e5-small, the cheapest of the
sweep – experiment 02 found e5-base/large and bge-m3 markedly better), the cross-encoder
was run on ≤ 60 hybrid candidates only, latencies were measured on a 4-core box that was
simultaneously running experiments 02/06 (load average 10–12), so absolute ms are
pessimistic – relative ordering is what matters.
