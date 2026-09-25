# 03 – Hybrid fusion (dense + BM25) and cross-encoder reranking

Reads the cached dense embeddings of experiment 02, computes French-normalised BM25 on the same
chunks (bm25s + Snowball stemmer + stopwords + accent folding, as tuned in experiment 01), fuses them,
and optionally reranks the top-N fused chunks with a cross-encoder.

```bash
cd experiments/03_hybrid_rerank && uv sync
uv run python run_hybrid.py --corpus A --model bge-m3 --chunker fixed1500_title \
    --fusions dense,bm25,rrf,convex0.3,convex0.5,convex0.7 --rerankers bge-reranker-v2-m3 --rerank_top 30
```

Fusions: `rrf` (reciprocal rank fusion, k=60, top-200 of each leg), `convexW` (W·minmax(dense) +
(1-W)·minmax(bm25)). Rerankers: `BAAI/bge-reranker-v2-m3` (568M, multilingual), `BAAI/bge-reranker-base`,
`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (118M, multilingual), jina-reranker-v2 / mxbai-rerank-v2
(registered; need `trust_remote_code`, not validated on transformers 5).

## Results – corpus A (bge-m3, fixed1500_title chunks)

| run | MRR | nDCG@5 | H@1 | H@5 | R@10 | cost |
|---|---:|---:|---:|---:|---:|---|
| dense only | 0.678 | 0.736 | 0.552 | 0.862 | 0.966 | |
| BM25 only (same chunks) | 0.662 | 0.705 | 0.517 | 0.828 | 0.862 | |
| RRF | 0.645 | 0.736 | 0.483 | 0.897 | 0.931 | |
| convex 0.3 | 0.684 | 0.731 | 0.552 | 0.828 | 0.897 | |
| **convex 0.5** | **0.691** | **0.758** | 0.552 | 0.897 | 0.931 | ms |
| convex 0.7 | 0.670 | 0.742 | 0.517 | 0.897 | 0.931 | |
| RRF + mMARCO-MiniLM rerank @30 | 0.629 | 0.736 | 0.483 | 0.931 | 0.931 | 10 s/q (loaded box) |
| RRF + bge-reranker-v2-m3 @30 | 0.678 | 0.777 | 0.517 | 0.931 | 0.931 | 24 s/q (idle 4-core CPU) |
| convex0.5 + bge-reranker-v2-m3 @30 | 0.681 | **0.782** | 0.517 | **0.931** | 0.931 | 24 s/q |
| convex0.5 + bge-reranker-base @30 | not run (model not in the offline HF cache) | | | | | |

Reference (experiment 04, e5-small hybrid RRF + bge-reranker-v2-m3 @30): **0.703 / nDCG@5 0.797 / H@5 0.931 / R@10 0.966**.

## Results – corpus B (e5-small, article_ctx_1200 chunks, 40 questions)

| run | MRR | nDCG@5 | H@1 | H@5 | R@10 |
|---|---:|---:|---:|---:|---:|
| dense only | 0.438 | 0.394 | 0.300 | 0.575 | 0.700 |
| BM25 only (same chunks) | 0.341 | 0.309 | 0.200 | 0.525 | 0.600 |
| **RRF** | **0.457** | 0.409 | 0.300 | 0.625 | 0.750 |
| convex 0.3 / 0.5 / 0.7 | 0.355 / 0.381 / 0.428 | | | | |
| **RRF + mMARCO-MiniLM @30** | **0.522** | **0.488** | 0.350 | **0.775** | **0.825** |
| RRF + bge-reranker-v2-m3 @30 | 0.517 | 0.450 | **0.375** | 0.700 | 0.825 |

On B the BM25 leg is much weaker than the dense leg, so min-max convex fusion drags the result down while
RRF still helps; the cheap mMARCO reranker is as good as bge-reranker-v2-m3 here (short article chunks).

## Take-aways

* RRF is the safest fusion but never beats the stronger leg; convex fusion with min-max normalised
  scores does (+0.013 over dense on A), but the weight must be validated per corpus.
* A small multilingual cross-encoder (mMARCO MiniLM) is **not** good enough to rerank strong candidates:
  it lowers MRR on A while raising hit@5. bge-reranker-v2-m3 is the one that helps (experiment 04: +0.10 MRR
  over hybrid RRF), at ~2-4 s per query for 30 candidates on an idle 4-core CPU.
* When the first stage is already strong (bge-m3 convex 0.691 on A) the reranker no longer raises MRR
  (0.681) but improves nDCG@5 and hit@5 – it re-orders the top of the list.
* Reranking depth 30 is enough on these corpora (recall@10 of the candidate set is already 0.83-0.97).
* Experiment 09 shows the same pattern at scale (corpus C, 64 questions): e5-small convex 0.5 = 0.621 →
  + bge-reranker-v2-m3 = **0.703**.
