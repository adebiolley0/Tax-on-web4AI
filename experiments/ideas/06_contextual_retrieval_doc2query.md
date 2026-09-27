# 06 — Contextual retrieval, doc2query and pseudo-titles

## Idea

Enrich the **index side** once, offline, so everyday French matches statute chunks:

1. **Contextual retrieval** (Anthropic 2024): an LLM sees the document plus one chunk and writes a 50–100-token situating context (code/article, tax, year/region), prepended for BM25 and embeddings.
2. **doc2query / doc2query--**: generate 5–30 *layman* questions per chunk, filter with a relevance model, index the survivors.
3. **Pseudo-titles**: a one-line title for topic-less documents (rulings, parliamentary questions).

Generated text is retrieval scaffolding only, never shown to users or the answering LLM.

## Why it fits this project

- doc2query puts layman phrasing *into the BM25 index*, our strongest leg (0.577 vs e5-small 0.433 on C) — squarely at the dominant vocabulary-gap failure.
- Pseudo-titles directly fix the topic-less-title failure mode.
- Our title + heading-path prefix (+0.02–0.04) is already a poor man's contextual retrieval, so the residual gain is below Anthropic's headline.
- Index-time cost only; query latency unchanged.

## Evidence

- Anthropic (2024-09): top-20 failure 5.7 % → 3.7 % (contextual embeddings) → 2.9 % (+ contextual BM25) → 1.9 % (+ reranker); $1.02 per M document tokens with caching.
- Independent reproduction, ConTEB (2025-05, Qwen2.5-7B writer): avg nDCG@10 52.0 baseline → 61.0 late chunking → **72.4** contextual, at 1,891 vs 16 ms/doc.
- Small writer (2025-04, Phi-3.5-mini, NFCorpus): nDCG@5 0.303 → 0.317.
- Legal (SAC, 2025-10, LegalBench-RAG, GPT-4o-mini, one ~150-char summary per document): document-level mismatch roughly halved; *generic* summaries beat expert-guided ones.
- Doc2Query-- (2023): relevance filtering improves doc2query up to 16 %, cuts index size 33 %. On BSARD (Belgian statutes) docT5query lifted BM25 R@100 49.3 → 51.7 (exp 10 notes).
- Doc2Query++ (2025-10, Llama-3.1-8B): appending queries to text **hurts dense retrieval**; a separate, fused query index fixes it.
- French non-LLM generator: `doc2query/msmarco-french-mt5-base-v1` (mT5-base).
- DeepSeek official pricing (2026): deepseek-flash off-peak $0.15/M input, $0.003/M cache hit, $0.60/M output; V4-Pro $0.66/$0.022/$1.98.

## How we would implement it

Corpus C: 201,404 chunks ≈ 65 M tokens (~320/chunk); ~21k documents, ~3k tokens each, long tail (cap context at 8k tokens).

| step | model | cost, 200k chunks |
|---|---|---|
| Context, 100 tok | deepseek-flash, cached document prefix | 80 M miss $12 + 16 M output $10 + cache hits $2–5 ≈ **$25–30** off-peak (V4-Pro ≈ $110); ~8 h wall |
| doc2query, 8 questions/chunk | deepseek-flash | ≈ **$30** |
| Pseudo-titles, 21k docs | deepseek-flash | < $2 |
| doc2query, 5 queries/chunk | mT5-base-fr, 4 cores | ~2–5 s/chunk [unverified] → 1–2 weeks; corpus B (9.8k articles) ≈ 1 day |
| Context | Qwen3-0.6B, llama.cpp, 3k-token prompt | ~15–30 s/chunk [extrapolated] → months |

Design: generated text goes into **separate `bm25s` fields** (BM25F weights) and a **second dense index** of question embeddings fused with the chunk index. Filter questions doc2query--style with the existing bge-reranker (keep ~50 %); cache by content hash. Prompt: "only from the chunk; no amounts, years, regions or articles absent from the text; phrase as a taxpayer would". LLM needed for everything except the mT5 pilot.

## Expected gain and cost

- doc2query on the BM25 leg: +0.02–0.05 MRR on C (BSARD prior, doc2query-- ceiling).
- Context over the existing prefix: +0.01–0.03; more for long circulars.
- Pseudo-titles: targeted fix for rulings/PQs.
- Combined, after fusion + reranker: 0.70 → ~0.73–0.76 [estimate]; ≈ $60–100 once, ~1 day engineering, +30–50 % index size.

## Risks / open questions

- **Hallucinated legal facts** (amounts, years, regions, article numbers): acceptable only under a strict index-only rule, every hit re-scored by the reranker on the *original* chunk.
- Near-duplicate yearly/regional editions get identical expansions, reinforcing the duplicate cluster — dedup (topic 26) first.
- Evaluation circularity with LLM-style eval questions; keep human-written sets, report per document class.
- Small models write poor French legal context (Phi-3.5: +0.014); mT5-mMARCO on statute text untested; concatenation hurts dense retrieval, so the dual index is mandatory.

## Verdict

**try-when-LLM** — cheap (~$60–100 with deepseek-flash) and aimed squarely at the vocabulary gap, but needs a capable LLM, separate indices, relevance filtering and index-only use; an mT5-fr doc2query pilot on corpus B can run now.

## Sources

- https://www.anthropic.com/engineering/contextual-retrieval (2024-09)
- https://arxiv.org/abs/2505.24782 (ConTEB, 2025-05)
- https://arxiv.org/abs/2504.19754 (2025-04)
- https://arxiv.org/abs/2510.06999 (SAC, 2025-10)
- https://arxiv.org/abs/2301.03266 (Doc2Query--, 2023)
- https://arxiv.org/abs/2510.09557 (Doc2Query++, 2025-10)
- https://huggingface.co/doc2query/msmarco-french-mt5-base-v1
- https://api-docs.deepseek.com/quick_start/pricing
- experiments/10_alternatives_research/README.md §1.5
