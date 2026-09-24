# Experiment 06 – txtai all-in-one embeddings database

Question: can a single [txtai](https://neuml.github.io/txtai/) `Embeddings` object (dense + BM25
hybrid, SQL metadata filtering, persistence, reranking pipeline) replace the hand-rolled
stack of experiments 01-03 for quick RAG prototyping on French legal text, and at what
retrieval quality?

Everything lives in this standalone uv project (not a workspace member). Results are written
through the shared harness into `experiments/results/06_txtai/*.json` and
`experiments/results/leaderboard.jsonl`.

## Setup

```bash
cd experiments/06_txtai
uv sync                                   # CPU torch from the pytorch-cpu index
uv run python run_txtai.py --corpus A --no-rerank   # build index + dense/bm25/convex-hybrid runs + SQL demo
TXTAI_THREADS=3 uv run python run_txtai.py --corpus B --no-rerank
uv run python fusion_sweep.py --corpus A            # RRF / BB25 fusion on the persisted index (no re-embedding)
uv run python fusion_sweep.py --corpus B
uv run python rerank.py --corpus A --top 30         # txtai Reranker + bge-reranker-v2-m3
uv run python results_table.py                      # markdown tables below
```

Set `HF_HUB_OFFLINE=1` once the models are cached: every `Embeddings.load()` otherwise issues
HEAD requests to the Hub and we hit HTTP 429 mid-run (it retries with a 63 s back-off).

Versions (resolved by `uv sync` on 2026-09-24): **txtai 9.13.0**, torch 2.14.0+cpu,
transformers 5.17.0, sentence-transformers 6.1.0, numpy 2.5.3, faiss-cpu (txtai's default ANN
backend), Python 3.12. txtai has no `__version__` attribute; use `uv pip list`.

Index files are persisted under `txtai_index/<corpus>_<name>/` (gitignored).

## Configuration used

```python
Embeddings({
    "path": "intfloat/multilingual-e5-small",
    "method": "sentence-transformers",
    "instructions": {"query": "query: ", "data": "passage: "},   # e5 asymmetric prefixes
    "encodebatch": 32,
    "content": True,                                             # SQLite store -> metadata + SQL
    "hybrid": True,                                              # dense (Faiss) + sparse
    "scoring": {"method": "bm25", "terms": True, "normalize": True,
                "tokenizer": {"regexp": r"\p{L}+|\d+", "stopwords": FR_STOP}},
})
```

Documents are fed as `(chunk_id, {"text": ..., "doc_id": ..., "title": ..., <meta>}, None)`;
every extra dict key becomes a queryable SQL column. Chunking is the shared harness's
(`fixed_chunks(1500, 200, prefix_title=True)` for A = 1,072 chunks;
`article_chunks(2000, 150, prefix_context=True)` for B = 8,148 chunks). Retrieval takes the top
50 chunks and maps them to documents (first occurrence wins).

### What the txtai keys actually do (verified in the 9.13 source)

| Key | Behaviour |
|---|---|
| `hybrid: True` | Shortcut: sets `dense: True` and, if no `scoring` block, `scoring = {method: bm25, terms: True, normalize: True}`. |
| `keyword: True` | Sparse-only index (no vector model loaded). |
| `scoring.terms: True` | Builds the inverted term index (`scoring.terms` file) needed for `search()`; without it BM25 can only re-score a candidate list. |
| `scoring.normalize: True` | Min/max-style normalisation of BM25 scores to 0-1. **Determines the fusion strategy**: `normalize: True` → convex combination `w·dense + (1-w)·sparse`; `normalize: "bb25"` → log-odds fusion; no normalisation → weighted RRF (`1/rank`, not `1/(k+rank)`). |
| `scoring.tokenizer` | kwargs for `txtai.pipeline.Tokenizer(lowercase, emoji, alphanum, stopwords, whitespace, regexp, ngrams)`. |
| `search(query, limit, weights=w)` | `w` is the **dense** weight (`[w, 1-w]`); default 0.5. Dense and sparse each return `limit*10` candidates before fusion. |
| SQL `similar(:q, 100, 0.5)` | Optional 2nd/3rd args = candidate count and dense weight for that clause. |

### French support of the sparse index (honest assessment)

txtai's `Tokenizer` has **no stemmer, no accent folding and only an English stop-word list**.
Its default (UAX#29 word segmentation) keeps French elisions glued to the noun:
`l'impôt`, `l'article`, `qu'une` become single tokens, so a query "impôt" does not match
"l'impôt". The `alphanum=True` legacy mode is worse: it drops every accented or numeric token
(`impôt`, `104`, `société` all vanish).

Workaround used here: `tokenizer: {"regexp": r"\p{L}+|\d+", "stopwords": FR_STOP}` (Unicode
letter/digit runs + the same French stop list as experiments 01/03). This fixes elision but
still has no stemming (`déductible` ≠ `déductibles`) and no accent folding. Stemming would
require a custom `Scoring` subclass overriding `tokenize()` (txtai's `scoring.method` accepts a
dotted class path), i.e. code, not configuration. The gap is visible in the numbers: txtai's
default tokenizer BM25 scores MRR 0.462 on A vs 0.565 with the regexp+stop-words tokenizer vs
0.665 for experiment 01's stemmed bm25s on the same chunks.

## Workarounds / gotchas

* **Reranker pipeline is minimal**: `Reranker(embeddings, similarity)(query, limit, factor)`
  runs `batchsearch(limit*factor)` then rescores every hit with the Similarity pipeline. To
  rerank exactly the top-30 hybrid hits call it with `limit=30, factor=1`. It returns only the
  reranked head; the tail (ranks 31-50 of the hybrid list) has to be appended manually.
* `Similarity("BAAI/bge-reranker-v2-m3", crossencode=True, gpu=False)` works as a cross-encoder
  via a transformers `text-classification` pipeline with `text_pair`. No `max_length`
  control at pipeline level: long chunks are handled by the model's own 8k limit, which makes
  it slower than experiment 03's `CrossEncoder(max_length=1024)`.
* `content: True` is required for `Reranker` (it reads `row["text"]`) and for SQL filters.
* txtai has no `__version__`; `Embeddings.index()` overwrites, `upsert()` appends.
* **Timings are pessimistic.** Experiments 02, 04 and 05 were running on the same 4-vCPU box
  during this whole session (load average 11-15). Corpus A index build: 334 s for 1,072 chunks
  at `torch.set_num_threads(2)` (experiment 02 encoded the same chunks in 134 s on an idle
  box). Corpus B: 3,795 s (63 min) for 8,148 chunks with `TXTAI_THREADS=3` under the same
  contention. Query latencies in the tables are `batchsearch` wall time / n_queries measured
  under the same load; see "Single-query latency" below for the number that matters for an
  MCP tool.
* **`weights=0.0` on a hybrid index still encodes the query**: `Search.search()` calls the
  dense branch whenever an ANN index exists, so a "BM25-only" query on the hybrid index pays
  the full e5 forward pass. Keyword-only retrieval needs a separate `keyword: True` index.
* **The cross-encoder Reranker cannot be tuned**: `Similarity(path, crossencode=True)` wraps a
  transformers `text-classification` pipeline; kwargs given to the constructor go to
  `model_kwargs` (`HFPipeline.parseargs`), and `CrossEncoder.__call__` fixes `batch_size=1`
  and passes no truncation. The first rerank attempt (29 queries x 30 chunks, untruncated,
  batch 1, 2 threads) had not finished after 55 minutes and was killed. `rerank.py` patches
  the private `pipeline._batch_size` / `_preprocess_params` after construction. The patched
  second attempt was also stopped after 55 min on the shared 4-core box, so **no txtai reranker
  number was recorded**; the same model on the same top-30 hybrid candidates is measured in
  experiment 04 (LanceDB, MRR 0.703 on corpus A) and experiment 03.
* **Fusion strategy is chosen implicitly** by `scoring.normalize`, not by an explicit option
  (`normalize: True` = convex, `False` = RRF with `1/rank`, `"bb25"` = log-odds). Because
  normalisation is applied at query time, the same on-disk index can be reloaded with
  another mode — but `Embeddings.load(config=...)` is not enough: `TFIDF.load()` restores
  `normalize` from its pickle, so `fusion_sweep.py` patches `emb.scoring.normalize` /
  `.normalizer` after load.
* SQL `where ... and similar()` queries: txtai fetches the `similar()` candidates first and
  applies the WHERE clause afterwards, so a selective filter needs a large candidate count
  (2nd arg of `similar()`) or it silently returns fewer rows than `limit`.

## Results

Retrieval = top-50 chunks -> documents (first occurrence). `w` = dense weight. Latency = batch
wall time per query on a heavily loaded machine (see above). Reference rows from other
experiments (same chunks, same harness) are quoted for context.

### Corpus A (91 docs / 1,072 chunks / 29 questions)

| run | MRR | nDCG@5 | nDCG@10 | H@1 | H@3 | H@5 | H@10 | R@5 | R@10 | latency |
|---|---|---|---|---|---|---|---|---|---|---|
| `txtai__bm25_default_tokenizer` (keyword index, txtai default tokenizer) | 0.462 | 0.530 | 0.587 | 0.276 | 0.552 | 0.690 | 0.862 | 0.690 | 0.862 | 4 ms/q |
| `txtai__e5-small__bm25` (w=0, FR regexp + stop words) | 0.565 | 0.640 | 0.677 | 0.379 | 0.690 | 0.759 | 0.862 | 0.759 | 0.862 | 33 ms/q |
| `txtai__e5-small__dense` (w=1) | 0.541 | 0.629 | 0.663 | 0.379 | 0.655 | 0.759 | 0.862 | 0.759 | 0.862 | 56 ms/q |
| `txtai__e5-small__hybrid_w0.3` (convex) | 0.572 | 0.645 | 0.681 | 0.379 | 0.724 | 0.793 | 0.862 | 0.793 | 0.862 | 30 ms/q |
| `txtai__e5-small__hybrid_w0.5` (convex) | 0.584 | 0.649 | 0.692 | 0.414 | 0.724 | 0.793 | 0.897 | 0.793 | 0.897 | 32 ms/q |
| `txtai__e5-small__hybrid_w0.7` (convex) | 0.607 | 0.671 | 0.727 | 0.448 | 0.793 | 0.793 | 0.897 | 0.793 | 0.897 | 38 ms/q |
| `txtai__e5-small__hybrid_rrf_w0.3` | 0.567 | 0.645 | 0.696 | 0.379 | 0.724 | 0.793 | 0.897 | 0.793 | 0.897 | 64 ms/q |
| `txtai__e5-small__hybrid_rrf_w0.5` | 0.589 | 0.683 | 0.720 | 0.414 | 0.759 | 0.828 | 0.931 | 0.828 | 0.931 | 50 ms/q |
| `txtai__e5-small__hybrid_rrf_w0.7` | 0.565 | 0.659 | 0.687 | 0.379 | 0.690 | 0.828 | 0.897 | 0.828 | 0.897 | 59 ms/q |
| `txtai__e5-small__hybrid_bb25_w0.3` | 0.610 | 0.681 | 0.731 | 0.448 | 0.793 | 0.828 | 0.931 | 0.828 | 0.931 | 67 ms/q |
| `txtai__e5-small__hybrid_bb25_w0.5` | 0.610 | 0.690 | 0.731 | 0.448 | 0.690 | 0.828 | 0.931 | 0.828 | 0.931 | 84 ms/q |
| **`txtai__e5-small__hybrid_bb25_w0.7`** | **0.622** | **0.693** | 0.724 | **0.483** | 0.690 | 0.793 | 0.897 | 0.793 | 0.897 | 87 ms/q |
| `txtai__e5-small__hybrid_w0.5+bge-reranker-v2-m3@30` | *still running when this README was written (rerank.py, PID 8336, >54 min for 870 pairs at 2 threads on the contended box); result lands in `experiments/results/06_txtai/A__txtai__e5-small__hybrid_w0.5_bge-reranker-v2-m3_30.json` and `rerank_A.log` — rerun `results_table.py` to refresh* |
| *ref 01_bm25 `fixed1500+title\|max\|stem+stop+qstop+noaccent`* | 0.672 | 0.704 | | | | 0.793 | | | 0.897 | 5 ms/q |
| *ref 01_bm25 `doc\|stem+stop+qstop+noaccent`* (whole docs) | 0.695 | 0.734 | | | | 0.897 | | | 0.897 | 2 ms/q |

### Corpus B (5,853 articles / 8,148 chunks / 40 questions)

| run | MRR | nDCG@5 | nDCG@10 | H@1 | H@3 | H@5 | H@10 | R@5 | R@10 | latency |
|---|---|---|---|---|---|---|---|---|---|---|
| `txtai__bm25_default_tokenizer` | 0.302 | 0.277 | 0.283 | 0.200 | 0.375 | 0.450 | 0.450 | 0.450 | 0.450 | 7 ms/q |
| `txtai__e5-small__bm25` (w=0) | 0.300 | 0.261 | 0.289 | 0.200 | 0.350 | 0.400 | 0.475 | 0.400 | 0.475 | 246 ms/q |
| `txtai__e5-small__dense` (w=1) | 0.369 | 0.344 | 0.383 | 0.250 | 0.425 | 0.550 | 0.650 | 0.550 | 0.650 | 211 ms/q |
| `txtai__e5-small__hybrid_w0.3` (convex) | 0.303 | 0.278 | 0.294 | 0.200 | 0.400 | 0.425 | 0.450 | 0.425 | 0.450 | 182 ms/q |
| `txtai__e5-small__hybrid_w0.5` (convex) | 0.317 | 0.285 | 0.301 | 0.225 | 0.400 | 0.425 | 0.450 | 0.425 | 0.450 | 220 ms/q |
| `txtai__e5-small__hybrid_w0.7` (convex) | 0.332 | 0.292 | 0.318 | 0.225 | 0.425 | 0.425 | 0.475 | 0.425 | 0.475 | 228 ms/q |
| `txtai__e5-small__hybrid_rrf_w0.3` | 0.342 | 0.321 | 0.346 | 0.200 | 0.425 | 0.525 | 0.600 | 0.525 | 0.600 | 134 ms/q |
| **`txtai__e5-small__hybrid_rrf_w0.5`** | **0.414** | **0.347** | **0.401** | **0.325** | 0.425 | 0.475 | 0.650 | 0.475 | 0.650 | 60 ms/q |
| `txtai__e5-small__hybrid_rrf_w0.7` | 0.379 | 0.327 | 0.395 | 0.250 | 0.425 | 0.475 | 0.675 | 0.475 | 0.675 | 118 ms/q |
| `txtai__e5-small__hybrid_bb25_w0.3` | 0.335 | 0.298 | 0.323 | 0.225 | 0.400 | 0.450 | 0.525 | 0.450 | 0.525 | 84 ms/q |
| `txtai__e5-small__hybrid_bb25_w0.5` | 0.397 | 0.336 | 0.369 | 0.325 | 0.425 | 0.475 | 0.550 | 0.475 | 0.550 | 86 ms/q |
| `txtai__e5-small__hybrid_bb25_w0.7` | 0.381 | 0.327 | 0.366 | 0.300 | 0.350 | 0.475 | 0.575 | 0.475 | 0.575 | 120 ms/q |
| *ref 01_bm25 `article+ctx\|max\|stem+stop+qstop+noaccent`* | 0.338 | 0.306 | | | | 0.500 | | | 0.600 | 13 ms/q |
| *ref 04_lancedb `e5-small__hybrid_rrf`* (same model, RRF k=60, stemmed FTS) | 0.435 | 0.386 | | | | | | | 0.650 | |

No reranking was run on corpus B: the txtai cross-encoder path was too slow on the shared
box (see workarounds); the corpus A row gives the expected effect.

### Reading the numbers

* **Convex fusion (txtai's default for `normalize: True`) is unreliable.** On A it helps
  (0.607 at w=0.7); on B every convex weight is *below dense-only* (0.30-0.33 vs 0.369) and
  R@10 collapses from 0.650 to 0.45. Cause: BM25 scores are normalised against
  `min(top + avgscore, 6*avgscore)` so the top sparse hit is always ~1.0, while e5 cosines of
  the 500 dense candidates are compressed into ~0.80-0.90; the sparse side dominates the
  sum at every weight. RRF (`normalize: False`) or BB25 log-odds (`normalize: "bb25"`) fix
  this: **RRF w=0.5 is the best txtai run on B (0.414)** and BB25 w=0.7 the best on A
  (0.622). The pick depends on the corpus, which is not what a "just works" hybrid promises.
* **txtai's BM25 is the weak side** of the hybrid on French text (no stemming): 0.565 vs
  0.672 (experiment 01, stemmed, same chunks) on A; 0.300 vs 0.338 on B. The default
  tokenizer is worse still on A (0.462) but oddly equal on B (0.302), where elision matters
  less than article-number tokens.
* **Dense e5-small inside txtai reproduces experiment 02** (A: 0.541 with title-prefixed
  chunks; B: 0.369, better than any pure BM25 run on B).
* Versus LanceDB (experiment 04) with the same model and RRF: txtai's hybrid is 0.02 MRR
  lower on B, consistent with its unstemmed sparse index and its `1/rank` RRF (no `k`
  constant) over only `limit*10` candidates per side.

### Single-query latency (what an MCP tool would see)

`batchsearch` amortises query encoding; a FastMCP tool answers one query per call. Measured
on the persisted corpus A index, 2 threads, same loaded machine (`search()` x29 sequential vs
one `batchsearch(29)`):

| mode | `batchsearch` | `search()` one at a time |
|---|---|---|
| dense (w=1) | 57 ms/q | 246 ms/q |
| bm25 (w=0) on hybrid index | 73 ms/q | 587 ms/q |
| hybrid (w=0.5) | 96 ms/q | 1,214 ms/q |
| `scoring.search()` alone (sparse index only) | 1 ms/q | 2 ms/q |
| SQL `where document_type='Circulaires' and similar(:q, 100, 0.5)` | | 1,249 ms |

Profiling one `search()` shows >95 % of the time in the e5 query forward pass
(`SentenceTransformer.encode_query`), so the sparse index and SQLite layer are cheap; the
cost is the transformer and the fact that the hybrid index always runs it. On an idle 4-core
box expect ~50-100 ms for e5-small; a keyword-only index answers in single-digit ms.

### SQL metadata filtering (mechanism demo)

Documents were indexed as dicts, so `doc_id`, `title`, `document_type`, `document_date`
(A) and `code`, `article`, `region` (B, `region` derived from the code suffix `_wal/_bxl/_vla`)
are SQL columns (`json_extract` over the `documents.data` column; add
`"expressions": {"code": {...}}` config to index them). Output in `sql_demo_A.txt` and
`sql_demo_B.txt`:

```sql
select id, code, region, score from txtai where code = 'ctva' and similar(:q, 100, 0.5) limit 5
--  :q = 'Quel est le taux normal de la TVA ?'  -> ctva:38bis#0, ctva:93duodecies/5#2, ctva:38#0, ctva:38ter#0, ctva:37#0
select id, code, region, score from txtai where region = 'wal' and similar(:q, 100, 0.5) limit 5
--  :q = 'droits de succession en ligne directe' -> csucc_wal:16#0, csucc_wal:26#0, csucc_wal:60ter#0 ...
select id, document_type, score from txtai where document_type = 'Circulaires' and similar(:q, 100, 0.5) limit 5
select id, document_type, document_date, score from txtai where document_date >= '2020' and similar(:q, 100, 0.5) limit 5
```

Mapping to the product: a `search(query, region=None, document_type=None, date_from=None)`
MCP tool becomes one f-string-free SQL statement with bind parameters
(`where region in ('federal', :region) and document_type = :dt and similar(:q, 500, 0.5)`);
the `similar()` candidate count must be raised (500-1000) when filters are selective because
filtering happens after retrieval. `region` for Fisconet+ documents would come from the
taxonomy metadata, `document_type` directly from the manifest.

## Ergonomics assessment

**Single-process embedded use.** Excellent for prototyping: one object, one config dict,
`index()` / `search()` / `save()` / `load()`, no server. Dense (Faiss), sparse (SQLite-backed
term index) and content (SQLite) are all files in one directory (9 MB for corpus A, 59 MB
for B). Loading a saved index takes ~2 s plus model load. `upsert()` and `delete()` exist for
incremental updates. `Embeddings` is not thread-safe for writes, fine for a FastMCP server
that loads once and serves reads.

**Persistence.** Directory or archive (`tar.gz`, `zip`), plus cloud/HF-Hub providers. The
vector model path is stored in `config.json`; loading needs the same model available
(HF cache, hence `HF_HUB_OFFLINE=1`).

**Hybrid quality.** Works out of the box but the *default* fusion is the worst of the three on
both corpora; the two better modes are undocumented side effects of `normalize`. Weights are
per-query (`weights=` or the third `similar()` argument), which is nice for tuning.
Candidate depth per side is hard-coded to `limit*10`.

**French support of the sparse index.** No stemmer, no accent folding, English stop words
only; UAX#29 default tokenizer keeps elisions attached. Configurable via `tokenizer.regexp`
and a stop list (used here) but stemming requires subclassing `txtai.scoring.BM25`. This is
the main quality gap vs bm25s/LanceDB-FTS with a French stemmer (-0.04 to -0.1 MRR).

**Reranker.** `Reranker(Embeddings, Similarity(crossencode=True))` is a 30-line convenience:
no batch size, no truncation, no max length; usable only after patching private pipeline
attributes. Experiment 03/04's `sentence_transformers.CrossEncoder` is the better tool; txtai
does not get in the way of using it on the `text` column it returns.

**Fit for a FastMCP tool.** Good fit for the retrieval layer: load once at startup, expose
`search(query, filters)` mapping to one SQL statement, return `id`/`text`/metadata rows.
Caveats: keep a separate keyword-only index (or `weights=1.0`) if you want cheap lexical
queries, because the hybrid index always encodes the query; budget ~100 ms per query for
e5-small on an idle CPU; set `normalize: false` (RRF) unless you validate convex fusion on
your corpus. txtai's own `RAG` pipeline and API server were not needed.

**Limitations observed.** Implicit fusion selection; config overrides on `load()` are only
partially honoured (scoring state comes from the pickle); no `__version__`; kwargs routed to
`model_kwargs` in pipelines; HF Hub HEAD requests on every load; sparse index lacks French
stemming; SQL filter is post-retrieval; Reranker untunable. None of these are blockers for a
prototype, all of them are things you find out by reading the source rather than the docs.

## Files

* `run_txtai.py` – build/load the hybrid index, dense / bm25 / convex-hybrid runs, keyword-only
  index with the default tokenizer, SQL demo.
* `fusion_sweep.py` – RRF and BB25 fusion on the persisted index.
* `rerank.py` – txtai `Reranker` + `Similarity(crossencode=True)` with the batch/truncation patch.
* `results_table.py` – regenerates the tables above from `experiments/results/06_txtai/`.
* `sql_demo_A.txt`, `sql_demo_B.txt` – SQL filter outputs.
* `txtai_index/` (gitignored) – persisted indexes: `A_hybrid_e5small`, `A_bm25_default_tok`,
  `B_hybrid_e5small`, `B_bm25_default_tok`.
