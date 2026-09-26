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
| `antoinelouis/splade-max-camembert-base-mmarcoFR` (2024-05) | 111M | French SPLADE-max (mMARCO-fr), both sides encoded | ran on A (after re-tying the MLM decoder, see notes); B not run (first attempt with the untied decoder was OOM-killed) |
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
* **SPLADE-fr under transformers 5.3: the MLM decoder is not tied.** The 2024 checkpoint has no
  `lm_head.decoder.*` keys (transformers 4 tied them to the word embeddings / `lm_head.bias`); transformers
  5.3 reports them MISSING and leaves a random decoder and a zero bias, which silently yields 78 %-dense
  "sparse" vectors with random top tokens (val MRR 0.473). `run_sparse.py` re-ties the weights explicitly and the
  numbers below are from the corrected run; the uncorrected rows were overwritten in the results folder (the
  leaderboard keeps the latest row per run name).
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

## Results – corpus A (91 docs / 1,072 chunks, 29 questions: 17 train / 12 val)

MRR at document level; `all` = 29 questions. Val bar **0.736** (experiment-01 whole-doc BM25, shown here as
`bm25doc`), full-set bar 0.703 (e5-small RRF + bge-reranker-v2-m3). Full tables: `uv run python make_tables.py A`.

### Single legs (first-stage retrieval over all chunks, document = max chunk)

| leg | params | encode A (2 thr) | index | query cost | val MRR | train | all | nDCG@5 | H@1 | R@10 |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `bm25doc` (exp 01 whole-doc, reference) | – | 0.03 s | – | µs | **0.736** | 0.666 | 0.695 | 0.734 | 0.586 | 0.897 |
| `bm25` chunks (exp 03 tokenizer) | – | 0.1 s | – | µs | 0.640 | 0.677 | 0.662 | 0.705 | 0.517 | 0.862 |
| e5-base dense (cached, exp 02) | 278M | 231 s | 3 MB | ms | 0.612 | 0.662 | 0.641 | 0.692 | 0.517 | 0.931 |
| bge-m3 dense (cached, exp 02) | 568M | ~1 h | 4 MB | ms | 0.602 | 0.731 | 0.678 | 0.736 | 0.552 | 0.966 |
| **`sparse-opensearch`** (doc-only SPLADE, 105k vocab) | 160M | 3,468 s | 2.1 MB (249 nnz/doc) | **no query inference** (IDF lookup), 20 nnz/query, 0.2 ms | 0.648 | 0.698 | 0.678 | **0.768** | 0.483 | **0.966** |
| `sparse-bge-m3` (lexical head) | 568M | 3,235 s¹ | 0.8 MB (96 nnz/doc) | model forward (14 nnz/query) | 0.647 | 0.569 | 0.601 | 0.689 | 0.414 | 0.931 |
| `sparse-splade-fr` (CamemBERT SPLADE-max, decoder re-tied) | 111M | SPLADE_FR_ENC | SPLADE_FR_IDX | model forward | SPLADE_FR_ROW |
| **`colbert-fr`** (CamemBERT ColBERTv1, 128-d, PyLate) | 111M | 1,195 s | 162 MB fp32 (295 tok/chunk) | 0.6 s brute-force MaxSim | 0.676 | 0.676 | 0.676 | 0.768 | 0.483 | 0.931 |
| `colbert-bge-m3` (M3 multi-vector head, 1024-d) | 568M | 3,235 s¹ | 795 MB fp16 (362 tok/chunk) | 0.5 s | 0.636 | 0.730 | 0.691 | 0.747 | 0.552 | 0.966 |
| `colbert-jina-colbert-v2` (128-d, PyLate) | 560M | 3,734 s | 181 MB fp32 (330 tok/chunk) | 0.15 s | 0.508 | 0.617 | 0.572 | 0.674 | 0.414 | 0.897 |

¹ one forward pass gives the dense, sparse and ColBERT outputs of bge-m3 (dense CLS cosine vs the exp-02 cache = 1.000).
Timings were measured with 2 threads while three other experiments loaded the 4 cores (load 7–9); the
OpenSearch cost is dominated by the 105,879-way MLM projection, not by the backbone.

### Fusion legs (RRF k=60 on the top-200 chunks; convex = min-max, weight tuned on train only)

| run | val MRR | train | all | nDCG@5 | H@1 | R@10 |
|---|---:|---:|---:|---:|---:|---:|
| `bm25doc + e5-base` RRF (reference: no new technique) | 0.756 | 0.700 | 0.723 | 0.751 | 0.621 | 0.966 |
| **`sparse-opensearch + bm25doc` RRF** | **0.808** | 0.678 | 0.732 | 0.762 | 0.586 | 0.966 |
| `sparse-opensearch + bm25doc + e5-base` RRF | 0.808 | 0.676 | 0.731 | 0.779 | 0.586 | 0.966 |
| **`sparse-opensearch + colbert-fr + bm25doc` RRF** | 0.794 | 0.699 | **0.738** | 0.786 | **0.621** | 0.966 |
| `sparse-opensearch + colbert-bge-m3 + bm25doc` RRF | 0.779 | 0.709 | 0.738 | 0.783 | 0.621 | 0.966 |
| `colbert-bge-m3 + bm25doc + e5-base` RRF | 0.767 | 0.673 | 0.712 | 0.747 | 0.586 | 0.966 |
| `sparse-bge-m3 + bm25doc + e5-base` RRF | 0.757 | 0.711 | 0.730 | 0.788 | 0.586 | 0.966 |
| `colbert-fr + bm25doc + e5-base` RRF | 0.751 | 0.709 | 0.726 | 0.770 | 0.621 | 0.966 |
| `colbert-bge-m3 + bm25doc` RRF | 0.739 | 0.715 | 0.725 | 0.733 | 0.621 | **1.000** |
| `colbert-fr + bm25doc` RRF | 0.734 | 0.718 | 0.725 | 0.753 | 0.621 | 0.966 |
| `sparse-bge-m3 + bm25doc` RRF | 0.732 | 0.667 | 0.694 | 0.749 | 0.552 | 0.966 |
| `sparse-bge-m3 + colbert-bge-m3 + bm25doc` RRF | 0.728 | 0.726 | 0.727 | **0.799** | 0.586 | 0.966 |
| `sparse-opensearch + colbert-fr` convex 0.2 | 0.707 | 0.710 | 0.709 | 0.803 | 0.552 | 0.931 |
| `sparse-opensearch + bm25` (chunks) convex 0.8 | 0.704 | 0.664 | 0.680 | 0.784 | 0.483 | 0.966 |
| `bge-m3-all + bm25` RRF (dense+sparse+colbert+bm25) | 0.701 | 0.612 | 0.649 | 0.761 | 0.483 | 0.931 |
| `bge-m3-all` paper weights 1 / 0.3 / 1 | 0.614 | 0.708 | 0.669 | 0.753 | 0.517 | 0.966 |
| `colbert-jina-colbert-v2 + bm25doc` RRF | 0.696 | 0.679 | 0.686 | 0.727 | 0.552 | 0.966 |
| `sparse-splade-fr + bm25doc` RRF | SPLADE_FR_FUSION |

### ColBERT as a reranker (MaxSim restricted to the first stage's top-k chunks)

| run | val MRR | train | all | nDCG@5 | H@1 | R@10 | cost / query |
|---|---:|---:|---:|---:|---:|---:|---|
| exp 03: e5-small RRF + bge-reranker-v2-m3 @30 (reference) | 0.674² | 0.686² | 0.703 | 0.797 | – | – | 20–24 s (CPU) |
| **`colbert-fr` rerank `bm25`@50** | 0.722 | 0.711 | 0.715 | **0.801** | 0.552 | 0.931 | 65 s to encode 50 chunks (2 thr, loaded box); ~ms with pre-encoded tokens |
| `colbert-fr` rerank `bm25`@30 | 0.637 | 0.688 | 0.667 | 0.750 | 0.517 | 0.897 | |
| `colbert-fr` rerank RRF(e5-small, bm25)@50 | 0.681 | 0.681 | 0.681 | 0.778 | 0.483 | 0.931 | |
| `colbert-fr` rerank bge-m3 dense@50 | 0.678 | 0.689 | 0.684 | 0.782 | 0.483 | 0.966 | |
| `colbert-bge-m3` rerank `bm25`@50 | 0.681 | 0.718 | 0.703 | 0.763 | 0.586 | 0.931 | 181 s to encode 50 chunks |
| `colbert-bge-m3` rerank RRF(e5-small, bm25)@50 | 0.644 | 0.728 | 0.693 | 0.757 | 0.552 | 0.931 | |
| `colbert-jina-colbert-v2` rerank `bm25`@50 | 0.588 | 0.593 | 0.591 | 0.702 | 0.414 | 0.931 | 223 s to encode 50 chunks |

² the closest split-reported reference in `results/03_hybrid_rerank` is bge-m3 convex 0.5 + bge-reranker (val 0.674 / train 0.686).
Runs named `rerank_bm25doc@k` in the results folder are not meaningful: the whole-document BM25 leg gives every
chunk of a document the same score, so its "top-50 chunks" are the chunks of only 2–5 documents (recall@10 drops to
0.83); they are kept for completeness only.

## Results – corpus B (5,853 articles / 10,869 chunks, 40 questions: 24 train / 16 val)

Val bar **0.570** (e5-small RRF + mMARCO-MiniLM reranker @30; full-set 0.522). Without a reranker the exp-03
first stage (e5-small RRF) is val 0.420 / all 0.457. Only ≤ 300M models were run on B.

| run | encode B (2 thr) | index / query | val MRR | train | all | nDCG@5 | H@1 | R@10 |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| `bm25` chunks (article + heading context) | 2 s | – | 0.315 | 0.358 | 0.341 | 0.309 | 0.200 | 0.600 |
| `bm25doc` (bare article text) | 1 s | – | 0.262 | 0.283 | 0.275 | 0.240 | 0.175 | 0.525 |
| e5-small dense (cached) | 580 s | 16 MB / ms | 0.327 | 0.512 | 0.438 | 0.394 | 0.300 | 0.700 |
| **`sparse-opensearch`** | 8,105 s | 18 MB (211 nnz/doc) / no query inference, 2 ms | 0.383 | 0.448 | 0.422 | 0.391 | 0.300 | 0.625 |
| **`colbert-fr`** | 6,487 s | 1.2 GB fp32 (215 tok/chunk) / 2.0 s brute-force | 0.432 | 0.502 | **0.474** | 0.418 | 0.325 | **0.825** |
| `colbert-fr + bm25` RRF | | | **0.539** | 0.470 | 0.498 | 0.440 | 0.375 | 0.800 |
| `colbert-fr + e5-small` RRF | | | 0.509 | 0.534 | 0.524 | 0.489 | 0.350 | 0.825 |
| `colbert-fr + e5-small + bm25` RRF | | | 0.506 | 0.531 | 0.521 | 0.457 | 0.375 | 0.825 |
| `colbert-fr + e5-small` convex 0.5 (train-tuned) | | | 0.463 | 0.617 | **0.555** | **0.504** | **0.400** | 0.800 |
| `colbert-fr` rerank RRF(e5-small, bm25)@50 | | 37 s to encode 50 chunks | 0.498 | 0.484 | 0.489 | 0.450 | 0.350 | 0.800 |
| `colbert-fr` rerank `bm25`@30 | | | 0.462 | 0.445 | 0.452 | 0.414 | 0.350 | 0.700 |
| `sparse-opensearch + colbert-fr` convex 0.2 | | | 0.459 | 0.518 | 0.494 | 0.446 | 0.350 | 0.775 |
| `sparse-opensearch + e5-small` RRF | | | 0.389 | 0.545 | 0.483 | 0.438 | 0.350 | 0.700 |
| `sparse-opensearch + e5-small + bm25` RRF | | | 0.378 | 0.491 | 0.446 | 0.393 | 0.300 | 0.750 |
| `sparse-opensearch + bm25` convex 0.5 | | | 0.344 | 0.475 | 0.423 | 0.362 | 0.300 | 0.650 |
| exp 03 reference: e5-small RRF (+ mMARCO @30) | | | 0.420 (0.570) | 0.481 (0.490) | 0.457 (0.522) | | | |

Not run on B: `sparse-splade-fr` (the first attempt ran with the untied – random – decoder, produced 78 %-dense
vectors and was OOM-killed at 13 GB; with the fixed loader it is a ~2 h job on an idle box:
`uv run python run_sparse.py --corpus B --model splade-fr --dense e5-small`), the 560M-class models (budget).
Corpus C was out of scope for this experiment (CPU budget: 201k chunks × these encoders = days).

## Analysis

**Learned sparse.** The OpenSearch multilingual doc-only encoder is the surprise of the experiment: on A it is
the best *single* neural first stage (all 0.678 = bge-m3 dense, nDCG@5 0.768 and recall@10 0.966, the best of
any single leg), it needs **no query-time model** (tokeniser + IDF weights, 20 terms per query, 0.2 ms) and its
index is 2 MB for A / 18 MB for B (an inverted index like BM25's, 211–249 terms per chunk). It behaves like a
"BM25 with learned expansion": it recovers the layman ↔ statute vocabulary cases (*rentes alimentaires* ↔
*pension*, *voiture* ↔ *véhicule*) that hurt BM25, which is exactly why it fuses so well with the lexical leg:
`sparse-opensearch + bm25doc` RRF is val **0.808** (all 0.732) against the 0.736 bar, and adding `colbert-fr`
gives the best full-set number of this experiment (all 0.738, H@1 0.621, nDCG@5 0.786). Caveat: val is 12
questions; the train side of the same fusions is 0.68–0.71, i.e. the honest reading is "≈ +0.03–0.04 all-set
MRR over the best BM25 + dense pair (0.723)", not +0.07. On B it is the strongest single leg on val (0.383 vs
0.327 e5-small / 0.315 BM25) and equal to e5-small on the full set (0.422 vs 0.438), but its recall@10 (0.625)
is the lowest of the neural legs and its fusions with e5-small/BM25 do not beat the ColBERT ones. Cost is the
catch: the 105,879-way MLM projection makes document encoding 3× slower than a same-size dense encoder
(58 min per 1,000 chunks at 2 loaded threads; 12 min per 1,000 once the box was idle) – acceptable for an
offline index of 100k documents (a few CPU-days, or an hour on a GPU), and free at query time.
`sparse-bge-m3` (14 query terms, 96 doc terms) is weaker alone (all 0.601) and only useful inside M3's own
three-way combination; the M3 paper weights (1 / 0.3 / 1) do not transfer (0.669 all, below dense alone 0.678).
`sparse-splade-fr` SPLADE_FR_ANALYSIS

**Late interaction.** A *French* ColBERT (CamemBERT, 111M) is a good first stage on both corpora: A all 0.676
(= bge-m3 dense at 1/5 of the parameters, 3× faster to index) and **B all 0.474, the best single first stage
measured on B** (e5-base 0.469, e5-small 0.438, BM25 0.341) with recall@10 0.825. Fused with e5-small it gives
all **0.524–0.555** on B, i.e. the level of the exp-03 *reranked* pipeline (0.522) without a cross-encoder, and
`colbert-fr + bm25` RRF is val 0.539 (bar 0.570, mMARCO-reranked). As a reranker over BM25's top-50 chunks it
reaches all 0.715 / nDCG@5 0.801 on A – on par with bge-reranker-v2-m3 (0.703 / 0.797) – but only at k=50 (k=30
drops to 0.667: BM25's top-30 chunks miss the document too often, recall@10 of chunk-BM25 is 0.86). The
560M-class multilingual ColBERTs do **not** change the picture: bge-m3's ColBERT head (1024-d, 795 MB for
1,072 chunks!) is 0.691 all but 0.636 val, and `jina-colbert-v2` is the weakest neural leg of the experiment
(all 0.572, val 0.508, 0.591 as reranker) – on this French statute text and with 48-token expanded queries its
English-centric training shows; the repo's old fastembed ColBERT result (0.50) was not a ColBERT problem but
a *which* ColBERT problem. Practical costs: MaxSim over all chunks in memory is 0.15–0.6 s per query on A and
2 s on B at 2 threads (fine behind an MCP tool, and PyLate's PLAID/Voyager indexes bring it to ms), but the
multi-vector index is 100–500× a dense index (162 MB for A, 1.2 GB for B in fp32 with 128-d; 2-bit PLAID
compression divides that by ~10) and reranking *without* pre-encoded tokens costs 37–223 s per query on this
CPU, so ColBERT is only a reranker if the token embeddings are stored – at which point it is a first stage.

**What does not work.** RRF/convex of a learned leg with the *chunk* BM25 leg is consistently worse than with
the whole-document BM25 leg on A (0.68–0.70 vs 0.73–0.81 val): fusions should use the best unit of each leg, not
a shared chunking. Convex weights tuned on 17 train questions transfer badly (several convex runs are +0.05 on
train and −0.05 on val); RRF is the safer combinator at this question count. And the "everything" fusions
(4 legs) are never better than the best 2–3-leg one.

## Verdict / recommendation

1. **Learned sparse (OpenSearch multilingual v1) as a fusion leg: yes.** It is the cheapest way found so far to
   add vocabulary-expansion recall to the BM25 + dense stack (no query model, inverted-index storage, val 0.808
   / all 0.732 with whole-doc BM25 on A; all 0.738 with ColBERT-fr as a third leg). Index it offline (GPU or
   a CPU day for 100k docs) and store it as a second sparse field in LanceDB/Qdrant (both support sparse vectors).
2. **ColBERT-fr as a first-stage / fusion leg on the article corpus: yes, as the dense leg.** On B it beats
   every single-vector model and its fusion with e5-small matches the reranked pipeline; the cost is a 1.2 GB
   token index (PLAID-compressible) and PyLate as a dependency. jina-colbert-v2 and bge-m3's ColBERT head: no.
3. **ColBERT as a reranker: only with pre-encoded tokens** (then it equals bge-reranker-v2-m3 on A at ~0 cost per
   query); the cross-encoder stays the better *pure* reranker when tokens are not stored.
4. Everything above is 12/16 val questions; the ranking of techniques is stable across train/val/all
   (opensearch and colbert-fr are top-3 single legs on every split) but the absolute fusion gains are not.
   The next experiment should re-score the winning fusion (`bm25doc + opensearch + colbert-fr`) on corpus C
   (BM25 + opensearch needs one CPU-day of encoding; ColBERT-fr ~2 days or a GPU hour).
