# 15 — Hybrid fusion: theory and practice

**Idea**

Stop choosing RRF vs convex per corpus by trial and error. Use one first stage: z-score (or theoretical-min-max) normalised convex fusion, its single weight chosen by cross-validation with shrinkage towards 0.5 and optimised for *recall@30* (the reranker's input), plus a "weakest-link" gate that falls back to RRF when one leg is weak. Extend the same linear form to more legs (bge-m3 sparse, late-interaction, metadata prior). Do **not** invest in query-dependent weighting yet.

**Why it fits this project**

Our data replicate the literature: convex beats RRF when both legs are decent (A, C), RRF wins when one is weak (B), tuned weights did not transfer from a ~30-question split, and the reranker adds most. Theory says why: rank fusion discards score-distribution information (Bruch et al.); equal-weight score fusion breaks when one leg is domain-tuned or weak (Louis et al., on *Belgian French law*). With ~60 questions and a reranker downstream, the target is a robust candidate set, not a fine-tuned MRR.

**Evidence**

- Bruch, Gai, Ingber (TOIS 2023): convex (TM2C2) beats RRF on all datasets, in- and out-of-domain; MS MARCO NDCG@1000 0.454 vs 0.425. α∈[0.6, 0.8] (dense weight) consistently good; α converges with <5 % of training queries; tuned RRF(k) generalises poorly; bounded linear normalisations are rank-equivalent up to re-parametrised α. https://arxiv.org/abs/2210.11934
- Louis, van Dijck, Spanakis, "Know When to Fuse" (2024), LLeQA (27,942 Belgian articles, French): zero-shot, 82 % of 88 combinations beat the best single model (R@10 0.232 → 0.323 with BM25+SPLADE+ColBERT, z-score, equal weights fine); in-domain, ~70 % of combinations *hurt* unless weights are tuned (DPR-lex 0.595 → 0.619 two-leg, 0.629 three-leg; four legs ≈ three). z-score > min-max > percentile. https://arxiv.org/abs/2409.01357
- Elastic (2023), ELSER+BM25 on BEIR: RRF +1.4 % nDCG@10 over ELSER, tuned linear +6 %; ≈40 annotated queries suffice for linear to beat RRF. https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid
- OpenSearch (2025): z-score vs min-max +2.08 % nDCG@10 on five BEIR sets (but "marginally worse" in one production benchmark). https://opensearch.org/blog/introducing-the-z-score-normalization-technique-for-hybrid-search/
- BGE-M3 (2024), MIRACL-fr nDCG@10: dense 58.3, dense+sparse 58.0, dense+sparse+multi-vector 61.2 (weights 1/0.3/1). https://arxiv.org/abs/2402.03216
- "Balancing the Blend" (2025, 11 datasets): a weak leg degrades the fusion ("weakest link"). https://arxiv.org/abs/2508.01405
- Dynamic fusion: DAT (2025) +3.3 % P@1 on SQuAD with a GPT-4o judge, one LLM call/query. https://arxiv.org/abs/2503.23013 — but on FinDER (2026) the per-query oracle shows +21.8 % headroom and *none* of three lightweight routers reliably beats a fixed blend; untuned RRF beat the equal-weight blend. https://arxiv.org/abs/2608.00183
- Qdrant: DBSF (z-score-style) beat RRF on 3/5 datasets. Cormack et al. (2009): RRF beat CombMNZ on 3/4 TREC runs.

**How we would implement it**

1. In `14_ltr_fusion`, add normalisers: z-score over each leg's top-300, and theoretical-min-max (BM25 min = 0). Keep min-max for comparison.
2. Fusion = `w·dense + (1−w)·bm25` (+ `w_s·sparse`, `w_m·colbert` later), doc = max chunk.
3. **Weight choice with ~60 questions**: grid w∈{0.3,…,0.7}; repeated 5×2 or leave-one-out CV; objective = out-of-fold *recall@30* (smoother than MRR at n=60); pick the weight closest to 0.5 within one bootstrap SE of the best. Never trust a weight from <40 questions.
4. **Gate**: if a leg's standalone recall@30 < 0.7× the other's, use RRF (k=60) or the strong leg only; otherwise convex.
5. Optional metadata prior `λ·log prior(doc type/year)` only if it moves OOF recall; log all runs to `leaderboard.jsonl`.

**Expected gain and cost**

First-stage recall@30 +2–5 points, MRR +0.01–0.03 before reranking; after `bge-reranker-v2-m3` probably ≤ +0.02 MRR, the main return being stability across corpora and 100k-document growth. Cost: a day of scripting, no runtime cost, no new models. A third leg (bge-m3 sparse) costs one extra index and may add +1–3 points (BGE-M3, Louis).

**Risks / open questions**

- With 60 questions, CV noise may swamp a 0.1 change in w; the shrinkage rule is a guess.
- z-score's edge is dataset-dependent (OpenSearch production result); theory says normalisation is second-order once w is re-tuned.
- Truncated-list fusion ≠ complete-list fusion (EAHR 2026); depth 300 may be shallow at 100k docs.
- Dynamic weighting via a DeepSeek judge is plausible later but unproven outside QA benchmarks.

**Verdict**

try-now — cheap, addresses the observed RRF-vs-convex instability with a defensible weight-selection protocol; expect robustness more than a headline MRR jump.

**Sources**

URLs inline above, plus: https://qdrant.tech/documentation/search-tuning/how-to-tune-hybrid-search/ · https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf · EAHR https://arxiv.org/abs/2608.07152 · https://arxiv.org/abs/2309.04981 (abstract only, unverified)
