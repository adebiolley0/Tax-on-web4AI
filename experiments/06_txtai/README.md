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
uv run python run_txtai.py --corpus A     # ~6 min build + ~2 min rerank on 4 vCPU
TXTAI_THREADS=4 uv run python run_txtai.py --corpus B --no-rerank
```

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
* Index build uses the vector model's batch loop with `torch.set_num_threads(2)`; txtai's
  sentence-transformers path was ~2.5x slower than experiment 02's direct
  `SentenceTransformer.encode` on the same 1,072 chunks (334 s vs 134 s) mostly because of the
  thread cap; corpus B was run with `TXTAI_THREADS=4`.
* SQL `where ... and similar()` queries: txtai fetches the `similar()` candidates first and
  applies the WHERE clause afterwards, so a selective filter needs a large candidate count
  (3rd arg) or it silently returns fewer rows than `limit`.

## Results
RESULTS_PLACEHOLDER
