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
| `hybrid_rrf+<ce>@30` | hybrid (50 + 50) RRF-fused, top-30 rescored by a sentence-transformers CrossEncoder (custom `TopKCrossEncoderReranker`; `--rerankers mmarco-minilm,bge-reranker-v2-m3`, `--ce_builtin` switches to LanceDB's own `CrossEncoderReranker`, see API notes) |
| `vector_ivf` | approximate search through an `IvfPq(cosine, num_sub_vectors=48)` index, `nprobes=10` |

Every run retrieves 50 chunks (30 for the cross-encoder runs), maps chunk hits to `doc_id`
(first occurrence wins) and scores at document level (`evaluate_rankings`). Results go to
`experiments/results/04_lancedb/<corpus>__<run>.json` and `experiments/results/leaderboard.jsonl`
under experiment `04_lancedb`. The LanceDB directory (`lancedb_data/`, gitignored) is reused
between invocations unless `--rebuild` is passed.

## Results

All numbers are document-level (`evaluate_rankings`), top-50 chunks retrieved (30 candidates
for the cross-encoder runs), e5-small embeddings for every run that uses vectors.
Latencies are wall-clock per query *including* LanceDB result materialisation
(`to_list()`), measured on a 4-core CPU box that was simultaneously running three other
experiments (load average 12–15), so absolute values are pessimistic by roughly 2–3×.

### Corpus A – 91 Fisconet+ documents, 1,072 chunks (`fixed_chunks(1500, 200, prefix_title=True)`), 29 questions

| run | MRR | nDCG@5 | nDCG@10 | hit@1 | hit@5 | hit@10 | recall@10 | query ms (mean / p95) | index / build |
|---|---|---|---|---|---|---|---|---|---|
BGE_ROW_A
| `lancedb__e5-small__fts_fr` | 0.645 | 0.690 | 0.730 | 0.517 | 0.759 | 0.862 | 0.862 | 7 / 12 | insert 0.05 s, FTS(fr) 0.17 s |
| `lancedb__e5-small__hybrid_rrf+mmarco-minilm@30` | 0.639 | 0.734 | 0.756 | 0.483 | 0.931 | 0.966 | 0.966 | 18,957 / 21,627 | reranker load 6 s |
| `lancedb__e5-small__hybrid_rrf` | 0.598 | 0.672 | 0.725 | 0.448 | 0.793 | 0.966 | 0.966 | 17 / 23 | – |
| `lancedb__e5-small__vector` | 0.541 | 0.629 | 0.663 | 0.379 | 0.759 | 0.862 | 0.862 | 8 / 10 | encode 133 s (cached from exp. 02) |
| `lancedb__e5-small__fts_en` | 0.539 | 0.616 | 0.636 | 0.379 | 0.724 | 0.793 | 0.793 | 8 / 12 | FTS(en) 0.15 s |
| `lancedb__e5-small__vector_ivf` | 0.532 | 0.583 | 0.636 | 0.379 | 0.724 | 0.828 | 0.828 | 8 / 11 | IVF_PQ 0.4 s |

Reference rows from the other experiments (same corpus / questions): hand-rolled bm25s with
French stemming + custom stop-list, whole documents – MRR 0.695 (exp. 01, best lexical);
`e5-small__fixed1500_title` numpy cosine – MRR 0.508 on 31 questions (exp. 02; the same
vectors give 0.541 here on the 29-question set, and txtai's `e5-small__dense` gives exactly
0.541 too, which confirms the LanceDB flat search is exact); txtai hybrid (w=0.7) – 0.607.

### Corpus B – 5,853 articles (default subset), 8,148 chunks (`article_chunks(2000, 150, prefix_context=True)`), 40 questions

| run | MRR | nDCG@5 | nDCG@10 | hit@1 | hit@5 | hit@10 | recall@10 | query ms (mean / p95) | index / build |
|---|---|---|---|---|---|---|---|---|---|
| `lancedb__e5-small__hybrid_rrf+mmarco-minilm@30` | 0.478 | 0.423 | 0.464 | 0.325 | 0.700 | 0.775 | 0.775 | 19,871 / 22,587 | reranker load 6 s |
| `lancedb__e5-small__hybrid_rrf` | 0.435 | 0.386 | 0.421 | 0.300 | 0.575 | 0.650 | 0.650 | 25 / 36 | – |
| `lancedb__e5-small__vector` | 0.361 | 0.328 | 0.380 | 0.225 | 0.550 | 0.700 | 0.700 | 28 / 108 | encode 3,970 s (≈ 66 min under load; ~15–20 min on an idle box), insert 0.43 s |
| `lancedb__e5-small__fts_fr` | 0.357 | 0.313 | 0.349 | 0.225 | 0.500 | 0.600 | 0.600 | 9 / 13 | FTS(fr) 1.3 s |
| `lancedb__e5-small__vector_ivf` | 0.342 | 0.314 | 0.342 | 0.225 | 0.425 | 0.525 | 0.525 | 7 / 16 | IVF_PQ 14 s |
| `lancedb__e5-small__fts_en` | 0.309 | 0.268 | 0.297 | 0.200 | 0.400 | 0.500 | 0.500 | 11 / 22 | FTS(en) 1.3 s |

Reference: bm25s `article+ctx|max|stem+stop+qstop+noaccent` – MRR 0.338 (exp. 01);
bm25 on the cleaned corpus with region filter – 0.374 (exp. 08). The bge-reranker-v2-m3 run
was not done on B: at ~2 min per query (30 pairs, 568 M parameters, CPU shared 4 ways) it
would have taken > 80 min; mMiniLM (118 M) costs ~20 s per query under the same load.

### Reading the numbers

* **French tokenizer is the single biggest FTS lever**: `language="French"` vs the default
  English tokenizer is +0.11 MRR on A and +0.05 on B, for one keyword argument. LanceDB's
  French FTS lands within 0.03 MRR of the tuned bm25s pipeline of experiment 01 on both
  corpora (0.645 vs 0.672 on the same chunking on A; 0.357 vs 0.338 on B) – the remaining
  gap on A is the extra interrogative stop-list (`custom_stop_words` would close it).
* **Hybrid RRF is the right default on the hard corpus**: on B it beats both legs by a wide
  margin (0.435 vs 0.361 vector / 0.357 FTS; recall@10 0.65) and is the best non-reranked
  configuration in the whole leaderboard for B. On A, where lexical overlap between the
  questions and the documents is high, RRF sits between the two legs in MRR but has the
  best recall@10 (0.966) – exactly the property a reranker needs.
* **A cheap multilingual cross-encoder on the RRF top-30 is worth it**: mMiniLM-L12 lifts
  hit@5 from 0.79 → 0.93 (A) and 0.58 → 0.70 (B), nDCG@5 +0.06 / +0.04. It costs ~20 s per
  query on the shared CPU here (≈ 5–8 s on an idle 2-thread box; with a GPU or ONNX this is
  sub-second) – acceptable for an MCP tool call, not for autocomplete.
* **Don't build a vector index at this scale**: IVF_PQ costs recall (MRR −0.01 on A, −0.02 on B,
  recall@10 −0.03 / −0.18) and saves nothing (flat search is 7–30 ms). Brute force is exact.
* Latency for pure vector / FTS / hybrid is 7–30 ms per query end-to-end, in-process,
  including pyarrow → Python conversion; the FTS index builds in 1.3 s for 8k chunks and the
  table in 0.4 s. Index build is therefore dominated entirely by embedding (see encode column).


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
  0.2 s (A) / 1.3 s (B). Query strings are tokenised with the index tokenizer, so raw
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
  (BM25 over an inverted index) exists, so a `tantivy` pip dependency is pointless (it was
  removed from `pyproject.toml` again). The native FTS does not support boolean `AND`/`OR` operators inside the query
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
* **The built-in `CrossEncoderReranker` is not usable as-is on CPU with a large model.** It
  scores the *union* of both legs (≤ 2 × `limit` rows, so 60 pairs at `limit(30)`), exposes
  no `max_length` / `batch_size` (it calls `CrossEncoder.predict(pairs)` with the defaults:
  batch 32, sequences up to the model's 8k `max_position_embeddings` for bge-v2-m3), and the
  hybrid `limit` also truncates the *output*, so "fetch 50, rerank 30" cannot be expressed.
  With `BAAI/bge-reranker-v2-m3` this took ~5 min per query on the shared box (7 queries in
  32 min – run aborted, log kept in `runA_ce_builtin_aborted.log`). The fix is a 25-line
  `Reranker` subclass (`TopKCrossEncoderReranker` in `run_lancedb.py`): RRF-fuse the two
  legs, keep the top 30, score with a `CrossEncoder(max_length=…)` in batches of 8, return
  a pyarrow table with `_relevance_score`. That is the whole plug-in contract
  (`rerank_hybrid(query, vector_results, fts_results)`), and it is what the
  `hybrid_rrf+<ce>@30` runs use. Good news: the contract is tiny; bad news: the shipped
  cross-encoder plug-in is tuned for GPU / small English models.
* `db.list_tables()` returns a `ListTablesResponse` object (namespace API) – `"chunks_A" in db.list_tables()`
  is silently `False`; use `db.table_names()`. Cost me one unintended table rebuild.
* `create_table(..., mode="overwrite")` and every `create_index` create a **new table
  version**; old versions stay on disk (`tbl.list_versions()`, the B table grew from 24 MB
  to 45 MB after two rewrites) until `tbl.optimize()` / `tbl.cleanup_old_versions()`. Handy
  for rollback, surprising for disk usage.
* Metadata pre-filtering on hybrid queries is noticeably slower than unfiltered on the
  8k-row table (`where code='cir92'`: hybrid 31–141 ms vs 25 ms; vector 26–48 ms vs 28 ms) –
  the filter is evaluated on the flat scan and again on the FTS leg. Fine for this size.
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
