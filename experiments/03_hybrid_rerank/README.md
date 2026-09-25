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
| RRF + bge-reranker-v2-m3 @30 | *pending (queue)* | | | | | |
| convex0.5 + bge-reranker-v2-m3 @30 | *pending (queue)* | | | | | |

Reference (experiment 04, e5-small hybrid RRF + bge-reranker-v2-m3 @30): **0.703 / nDCG@5 0.797 / H@5 0.931 / R@10 0.966**.

## Results – corpus B (e5-small, article_ctx_1200)

*pending (queue)* – fusions and both rerankers.

## Take-aways

* RRF is the safest fusion but never beats the stronger leg; convex fusion with min-max normalised
  scores does (+0.013 over dense on A), but the weight must be validated per corpus.
* A small multilingual cross-encoder (mMARCO MiniLM) is **not** good enough to rerank strong candidates:
  it lowers MRR on A while raising hit@5. bge-reranker-v2-m3 is the one that helps (experiment 04: +0.10 MRR
  over hybrid RRF), at ~2-4 s per query for 30 candidates on an idle 4-core CPU.
* Reranking depth 30 is enough on these corpora (recall@10 of the candidate set is already 0.93-0.97).
