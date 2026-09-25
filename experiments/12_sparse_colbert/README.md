# Experiment 12 – learned sparse retrieval and late interaction (ColBERT)

Question: on this French legal corpus, do *learned sparse* encoders (SPLADE-style, BGE-M3's lexical
head) or *late-interaction* models (ColBERT MaxSim, via PyLate) beat or usefully complement the
French-normalised BM25 + dense + cross-encoder stack of experiments 01–03 and 09?

Protocol: every question has a deterministic `train` / `val` split (`Question.split`); fusion weights are
tuned on **train only**; every table reports train and val MRR separately (plus "all"). Bars to beat
(val MRR): **A 0.736** (tuned BM25, whole documents; full-set best 0.703 e5-small RRF + bge-reranker),
**B 0.570** (e5-small RRF + mMARCO reranker; full-set 0.522). All runs are saved through the shared harness
(`save_result("12_sparse_colbert", …)` → `experiments/results/12_sparse_colbert/`, `leaderboard.jsonl`).

## Setup

Standalone `uv` project (not a workspace member), CPU-only torch:

```bash
cd experiments/12_sparse_colbert && uv sync
./queue.sh            # opensearch A → colbert-fr A → opensearch B → colbert-fr B → bge-m3 heads A → jina-colbert-v2 A
./queue2.sh           # splade-fr A, B (added once the disk was freed)
uv run python make_tables.py A   # README tables from the saved results
```

Versions (resolved 2026-09-25): torch 2.11.0+cpu, transformers 5.3.0, sentence-transformers 5.3.0,
**pylate 1.6.0** (fast-plaid 1.4.6, voyager via usearch 2.26), bm25s 0.3.11, PyStemmer, scipy 1.18.1,
einops 0.8.2 (needed by jina's remote code), rag-eval (editable, `../common`).

CPU etiquette: `torch.set_num_threads(2)` (`EXP12_THREADS`), one encoder at a time (`queue.sh`), corpora A
(1,072 chunks `fixed_chunks(1500, 200, prefix_title)`) and B (10,869 chunks `article_chunks(1200, 100,
prefix_context)`, default code subset) only. The box was shared with three other experiments during the
runs (load average 7–9 on 4 cores), so absolute timings below are pessimistic.

### Files

| file | role |
|---|---|
| `common12.py` | corpora/chunkers (identical to exp 02/03), BM25 leg (exp 03 tokenizer), cached dense legs (exp 02 `EmbeddingCache` keys; queries encoded once per model and memoised), RRF / min-max convex fusion, **train-only weight tuning** (`tuned_convex`), `fusion_suite` |
| `run_sparse.py` | learned sparse: `opensearch` (ST `SparseEncoder`, doc-side inference only) and `splade-fr` (transformers MLM head, `amax(log1p(relu(logits)))`, L2-normalised as in the model card); scipy CSR dot products; score matrix cached under `cache/` |
| `maxsim.py` | exact in-memory MaxSim over all chunks (torch, batched, masked padding) and `rerank_scores` (ColBERT restricted to the top-k of another retriever) |
| `run_colbert.py` | PyLate `models.ColBERT` encoders (`colbert-fr`, `jina-colbert-v2`); full retrieval, reranking of BM25 / RRF / dense candidates, fusion battery, optional Voyager (HNSW) probe |
| `run_bgem3.py` | BGE-M3's **sparse and ColBERT heads from one forward pass** (FlagEmbedding formulas re-implemented on transformers: `sparse_linear.pt`, `colbert_linear.pt`), M3 "all" combinations |
| `make_tables.py` | README tables from the saved results |

## Models: what ran, what did not

| model | params | role | status |
|---|---:|---|---|
| `opensearch-project/opensearch-neural-sparse-encoding-multilingual-v1` (rev 1e0f096, 2025-06) | 160M | learned sparse, **inference-free queries** (tokeniser + IDF table), 105,879-dim | ran on A and B |
| `antoinelouis/splade-max-camembert-base-mmarcoFR` (2024-05) | 111M | French SPLADE-max (mMARCO-fr), both sides encoded | ran on A and B |
| `BAAI/bge-m3` sparse head | 568M | lexical weights `relu(W·h)`, max per token id | ran on A (560M-class → A only) |
| `BAAI/bge-m3` ColBERT head | 568M | 1024-d multi-vector, MaxSim (mean over query tokens) | ran on A |
| `antoinelouis/colbertv1-camembert-base-mmarcoFR` (2024-03) | 111M | French ColBERTv1, 128-d, via PyLate | ran on A and B |
| `jinaai/jina-colbert-v2` (rev a9dc5cd) | 560M | multilingual ColBERT, 128-d, via PyLate (`[QueryMarker]`/`[DocumentMarker]`, `trust_remote_code`) | ran on A only |
| `naver/splade-v3` | 110M | English SPLADE control | **not run**: gated repository (`gated: auto`), HTTP 401 without a HF token; no token in this environment |
| `antoinelouis/colbert-xm` | 277M active | multilingual modular ColBERT (X-MOD) | **not run**: the checkpoint is a 3.41 GB safetensors (all 81 language adapters) and the disk had < 3 GB free when models were fetched; it also needs `set_default_language("fr_XX")` on the X-MOD backbone, which PyLate does not expose |
| `LiquidAI/LFM2.5-ColBERT-350M` | 350M | 2026 multilingual ColBERT (ST-native) | not run: above the 300M budget for B, remote code untested on transformers 5, disk |

Practical notes (worth knowing before reusing any of this):

* **PyLate + Stanford CamemBERT checkpoints.** `artifact.metadata` says `query_token_id="[unused0]"`,
  `doc_token_id="[unused1]"`; those tokens do not exist in the CamemBERT vocabulary, so `colbert-ai`
  silently mapped both markers to `<unk>` (id 4) at training time. PyLate instead *adds* the two tokens
  and resizes the embedding matrix off by one (`IndexError: index out of range` on the first encode).
  Fix used here: `query_prefix="<unk>", document_prefix="<unk>"` (reproduces training).
* **jina-colbert-v2** loads under transformers 5.3 with `trust_remote_code=True` once `einops` is installed
  (the flash-implementation remote code imports it); PyLate warns that the tokenizer cannot be resized but
  the marker tokens already exist (ids 250002/250003), so nothing is lost.
* **OpenSearch sparse encoder memory.** `SparseEncoder.encode_document` materialises MLM logits of shape
  `(batch, 512, 105,879)` in fp32: batch 16 = 3.5 GB and the process was OOM-killed at 5.3 GB RSS in the
  session cgroup. Batch 4 and slicing the corpus into 256-document CSR blocks keep it at ~1.4 GB.
* **BGE-M3 heads without FlagEmbedding**: `AutoModel` + the two tiny `.pt` linear layers from the repo; the
  dense CLS vectors recomputed in the same pass agree with the experiment-02 cache (cosine reported in
  the run config) which validates tokenisation / sequence length.
* Disk: the shared disk was at 99 % during this experiment (a coordinator later freed 12 GB), so token
  embeddings are kept in memory only (fp16) and only the `(n_questions, n_chunks)` score matrices are
  cached (`cache/*.npz`, a few hundred KB). No Voyager/PLAID index was persisted; the "index size" column
  is the fp32 size of the token embeddings that an in-memory index has to hold.

RESULTS_PLACEHOLDER
