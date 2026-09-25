# 02 – Open-weight embedding model × chunking sweep

Plain cosine retrieval in numpy (no vector DB) so that only the model and the chunking are measured.
Document score = max over its chunks. Embeddings are cached in `experiments/data/emb_cache/`
(keyed by model + chunk texts) and reused by experiments 03 and 09.

```bash
cd experiments/02_dense_sweep && uv sync
uv run python run_sweep.py --corpus A --models e5-base,bge-m3 --chunkers whole,fixed1500,fixed1500_title
uv run python run_sweep.py --corpus B --models e5-small --chunkers article_ctx_1200 --clean   # exp-08 cleanup
uv run python run_sweep.py --leaderboard --corpus A
```

`models.py` is the registry (HF id, query/passage prefixes, max_seq 512, loader kind).
Chunkers: `whole` (first 512 tokens of the document), `fixed1500[_title]` (heading-aware 1,500-char
chunks, 200 overlap, optional title prefix), `article_ctx[_1200]` (corpus B: article text prefixed with
code name + heading path; 2,000 or 1,200 chars).

## Results – corpus A (29 questions, 91 docs, 1,072 chunks)

| model | params | whole | fixed1500 | fixed1500_title | encode 1,072 chunks (4-core CPU, idle) |
|---|---:|---:|---:|---:|---:|
| BM25 reference (exp 01, whole doc) | – | **0.695** | 0.665 | 0.672 | – |
| potion-multilingual-128M (static, model2vec) | 128M | 0.382 | 0.454 | 0.460 | **1 s** |
| static-similarity-mrl-multilingual-v1 | 100M | 0.463 | 0.415 | 0.455 | 1 s |
| paraphrase-multilingual-MiniLM-L12-v2 (repo default) | 118M | 0.176 | 0.480 | 0.465 | ~100 s |
| multilingual-e5-small | 118M | 0.560 | 0.510 | 0.543 | ~120 s |
| multilingual-e5-base | 278M | 0.612 | 0.625 | **0.641** | 240 s |
| bge-m3 (dense) | 568M | 0.644 | – | **0.678** (R@10 0.966) | ~2.5 h under load (≈45 min idle) |
| multilingual-e5-large | 560M | 0.677 | – | – | whole-doc only |
| Solon-embeddings-large-0.1 (FR) | 560M | 0.674 | – | – | whole-doc only |
| snowflake-arctic-embed-l-v2.0 | 568M | 0.675 | – | – | whole-doc only |
| jina-embeddings-v3, Qwen3-Embedding-0.6B, nomic-v2-moe, bilingual-large | – | not run (queue stopped, see below) | | | |
| gte-multilingual-base, Fairly-Multilingual-ModernBERT-Embed-BE | – | **fail** on transformers 5.x (position-id overflow / missing tokenizer class) | | | |

Numbers are MRR at document level (`experiments/results/leaderboard.jsonl` has nDCG@5, hit@k, recall@10).

## Results – corpus B (40 questions, 5,853 articles)

| run | chunks | MRR | note |
|---|---:|---:|---|
| e5-small, article_ctx (2,000 chars) | 8,148 | 0.361 | 27 % of chunks > 512 tokens → truncated |
| e5-small, article_ctx, cleaned text (exp 08) | 8,148 | 0.342 | |
| e5-small, article_ctx_1200 (token-safe) | 10,869 | **0.438** | +0.08 from chunk length alone |
| e5-small, article_ctx_1200, cleaned | 10,555 | **0.466** | |
| e5-base, article_ctx (2,000 chars) | 8,148 | 0.357 | truncated |
| e5-base, article_ctx_1200, cleaned | 10,555 | **0.469** | 1,675 s to encode |
| LlamaIndex 128-token leaves, e5-small (exp 05) | 46,975 | **0.486** | best dense on B: short, token-safe leaves |

## Take-aways

1. **Model size matters more than anything else for dense retrieval on French legal text.**
   MiniLM (0.48) → e5-small (0.54) → e5-base (0.64) → bge-m3 / e5-large / Solon / arctic (0.68).
   Only the 560M-class models reach the tuned-BM25 level, and bge-m3 has by far the best recall@10 (0.97).
2. **Title / heading context prefix helps every transformer model** (+0.02 to +0.04 MRR) and is free.
3. **Chunk size must be counted in model tokens.** With 512-token encoders, 1,500-char chunks are fine
   for prose but article chunks with a heading prefix must stay ≤ ~1,200 chars (experiment 05 found 26 %
   truncation at 2,000 chars, which explains the low corpus-B numbers of experiments 02/04/06).
4. **Static embeddings (potion) are a serious speed option**: 1 s vs 240 s for e5-base, MRR 0.46 alone,
   and they fuse well with BM25 (experiment 09: BM25 + potion convex 0.3 = 0.595 on corpus C vs 0.577 BM25).
5. **CPU cost is the real constraint**: a 560M model needs ~1 h per 1,000 chunks (512 tokens) on this
   4-core box. On corpus C (201k chunks) that is impossible; e5-small (~3-4 h) is the largest model that
   can index it here. Running several torch jobs concurrently is counter-productive (OpenMP spin-waits:
   10-40× slowdowns were measured) – see `../run_queue.sh`.
6. Two candidate models (gte-multilingual-base, the Belgian ModernBERT) do not load with transformers 5.x;
   they would need a pinned older transformers – not worth it given the results above.
