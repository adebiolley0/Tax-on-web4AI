# 23 — Graph-RAG family: evidence review

## Idea
Build an entity/relation graph at index time (LLM-extracted: MS GraphRAG, LightRAG, nano-graphrag, KAG, Graphiti/Zep; embedding+PPR: HippoRAG 1/2; NLP-only: LazyGraphRAG/FastGraphRAG, LinearRAG) and retrieve via graph walks, communities or paths on top of BM25+dense+reranker.

## Why it fits this project
Tax law is densely cross-referenced (CIR92 article → AR/CIR → circulaire → ruling); multi-hop questions ("which circulaire interprets art. 90, 1° for crypto?") need linking, which graphs promise. But our target metric is *precise article citation*, the one task where published evidence says graphs do not help.

## Evidence
- **GraphRAG-Bench (ICLR'26, arXiv 2506.05690, Jun 2025):** fact retrieval: vanilla RAG 60.9 % vs 49.3–60.1 % for MS-GraphRAG, HippoRAG(2), LightRAG, Fast/Lazy-GraphRAG, RAPTOR; graphs win only on complex reasoning (50.9–53.4 vs 42.9) and summarisation. Context relevance 36.9–54.6 % (graph) vs 62.9 % (RAG). Indexing tokens (medical subset): MS-GraphRAG 331k, LightRAG ~100k, HippoRAG2 ~1k, RAG 954.
- **RAG vs GraphRAG (arXiv 2502.11371, Feb 2025):** NQ F1: RAG 64.8, GraphRAG-local 63.0, global 54.5. MultiHop-RAG: RAG 67.0, HippoRAG2 70.3, GraphRAG-local 69.0. Construction 135 s (RAG) vs 5,560–7,702 s; KG methods miss ~34 % of answer entities.
- **HippoRAG 2 (arXiv 2502.14802, Feb 2025):** vs NV-Embed-v2: Recall@5 avg 78.2 vs 73.4; MuSiQue F1 48.6 vs 45.7; NQ 63.3 vs 61.9. Same table: MS GraphRAG 46.9 on NQ, LightRAG 16.6 (collapse). Indexing tokens (MuSiQue, Llama-3.3-70B): HippoRAG2 9.2 M, LightRAG 68.5 M, GraphRAG 115.5 M. Gain is essentially all multi-hop.
- **Legal benchmark (CEUR Vol-4079 paper 6, 2025; EU directives + Indonesian regulations):** KG-only variants (nano-graphrag, LightRAG, HippoRAG2) lose to hybrids; "KG-only approaches struggle due to abstraction and loss of contextual nuance". LegalGraphRAG (arXiv 2605.28120, May 2026) beats HippoRAG2/RAPTOR only with a hand-built 3-layer legal ontology, on charge prediction (not citation).
- **LazyGraphRAG (MS Research blog, Nov 2024):** NLP noun-phrase indexing, LLM only at query time; 0.1 % of GraphRAG indexing cost. Still not in the open-source library (discussion #1490, silent since Dec 2024; `graphrag index --method fast` is the closest shipped variant).
- **PathRAG, KAG, Zep/Graphiti:** evaluated with LLM-judged win-rates or on conversational memory (DMR 94.8 vs 93.4); no independent citation-retrieval evidence. LightRAG's own claims are GPT-4o win rates, not recall.
- **"Structure pricing" (arXiv 2609.18099, Sep 2026):** graph RAG must be judged on quality *and* cost; a lightweight passage-locating graph beats LightRAG-hybrid at 4× lower cost.

## How we would implement it
Only HippoRAG 2 is worth a trial: one DeepSeek extraction call per chunk (OpenIE triples + NER), phrase and passage nodes, synonym edges via our e5 embeddings, PPR at query time seeded from dense retrieval; the article stays the retrieval unit, so citations survive. Feed its ranked passages into the existing fusion before bge-reranker. Rough cost for 200k chunks (from 9.2 M tokens / ~11.6k MuSiQue passages ≈ 800 tokens/chunk): ~160 M tokens ≈ **$45–90 on DeepSeek-Flash** (off-peak $0.15/M in, $0.60/M out), ~$170–340 on V4-Pro. LightRAG ≈ 7×, MS GraphRAG ≈ 12× (≈2 B tokens, $600–2,000). CPU-only extraction is infeasible at this scale. Zero-LLM alternative: a deterministic citation graph from the explicit "art. X CIR92" references in the texts, used as a re-rank prior.

## Expected gain and cost
Single-article citation MRR: 0 to +0.02 (literature shows parity or loss). Multi-hop/linking questions: +5–10 recall points possible. Engineering: 1–2 weeks plus $50–300 API spend, storage ~+30 %, small query latency (PPR is cheap).

## Risks / open questions
French legal text with codes ("art. 171, 1°, a)") is a poor fit for generic NER/OpenIE; entity coverage gaps (~34 % missed) hurt directly. Graph noise lowers context relevance, which the reranker cannot fully undo. Re-extraction needed on each Fisconet+ update. Our validation set is mostly single-hop; a multi-hop subset is required to even observe a gain.

## Verdict
**try-when-LLM (HippoRAG 2 only; skip MS GraphRAG, LightRAG, KAG, Graphiti):** independent evidence consistently shows graphs do not improve precise citation retrieval over a strong hybrid+reranker, so run HippoRAG 2 as a cheap gated A/B once DeepSeek is available and keep it only if a multi-hop subset shows recall gains.

## Sources
- GraphRAG-Bench: https://arxiv.org/abs/2506.05690 · https://github.com/GraphRAG-Bench/GraphRAG-Benchmark
- RAG vs GraphRAG: https://arxiv.org/abs/2502.11371 · HippoRAG 2: https://arxiv.org/abs/2502.14802
- Legal KG-RAG benchmark: https://ceur-ws.org/Vol-4079/paper6.pdf · LegalGraphRAG: https://arxiv.org/abs/2605.28120 · SAT-Graph (conceptual, no numbers): https://arxiv.org/abs/2505.00039
- LazyGraphRAG: https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/ · https://github.com/microsoft/graphrag/discussions/1490 · https://microsoft.github.io/graphrag/index/methods/
- PathRAG https://arxiv.org/abs/2502.14902 · KAG https://arxiv.org/abs/2409.13731 · Zep https://arxiv.org/abs/2501.13956 · LinearRAG https://arxiv.org/abs/2510.10114 · structure pricing https://arxiv.org/abs/2609.18099
- DeepSeek pricing (Sep 2026): https://api-docs.deepseek.com/quick_start/pricing — cost figures above are my derivations, unverified
