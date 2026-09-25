# 13 — Distil bge-reranker-v2-m3 into the retrieval stack

**Idea**

Use `bge-reranker-v2-m3` (568M, our best quality lever, 20 s/query on CPU) as a *teacher* offline: score (query, chunk) pairs over our own corpus and regress the scores into (a) the `multilingual-e5-small` bi-encoder (Margin-MSE / GPL recipe) and (b) the `mmarco-mMiniLMv2-L12` cross-encoder (pointwise MSE on teacher logits). Queries come from doc2query-style generation or BM25-mined pseudo-queries, so no labels are needed; the 133 human questions stay for evaluation only.

**Why it fits this project**

- Teacher cost, not quality, is the problem: distillation moves the 20 s/query into an offline queued job.
- We have a large unlabelled corpus (201k chunks in C) and a layman ↔ statute vocabulary gap the teacher already bridges; GPL targets exactly this regime.
- Everything is stock `sentence-transformers` (already used in exp 15/16).

**Evidence**

- Margin-MSE (Hofstätter 2020): teacher ensemble MRR@10 0.399; students with vs without KD: DistilBERT-dot 0.316→0.332, ColBERT 0.357→0.375; Margin-MSE beats pointwise MSE (0.370 vs 0.365) and RankNet (0.356). Students recover ~20–45 % of the gap to the teacher.
- TAS-B (2021): DistilBERT student, dual teachers, MRR@10 0.340, trained "under 48 h on a single 11 GB consumer GPU", batch 32.
- GPL (NAACL 2022): synthetic queries + cross-encoder soft labels, only the unlabelled corpus; up to +9.3 nDCG@10 over zero-shot (FiQA 25.4→34.5, BioASQ 33.1→41.2, TREC-COVID 36.1→43.8); gains already visible with 10k passages; default 140k steps ×32 (≈330 A100-hours in the paper).
- Score-Only Distillation (Jul 2026): students recover "roughly one-quarter to one-half of the base-to-teacher gap" with only 8.9k training rows; label-only contrastive control collapsed (0.304 vs 0.452 frozen base).
- Listwise CE distillation + synthetic data (May 2025): beats contrastive fine-tuning on BEIR with 56–200k LLM queries per corpus.
- Reproducing distillation for cross-encoders (Aug 2026, 162 runs, 17M–184M students): MarginMSE and InfoNCE are the top tier; "the quality of the negatives is at least as important as the loss"; changing objective ≈ moving up one backbone size.
- Ettin rerankers (May 2026): a 32M pointwise-MSE student beats bge-reranker-v2-m3 (0.578 vs 0.553 nDCG@10) — with 143M scored triples, English only.
- Stratified score sampling (SIGIR 2026): distil across the whole score spectrum, not only hard negatives.

**How we would implement it**

1. Queries: 3 per chunk on a 20k-chunk subset (≈60k queries) with `doc2query/msmarco-french-mt5-base-v1` (existence unverified this session; fallback: heading/title pseudo-queries + BM25-mined sentences; DeepSeek later).
2. Candidates: BM25 ∪ e5-small top-20, then *stratified* sample 8 per query (not only top-k).
3. Teacher: bge-reranker-v2-m3 at ≤512 tokens ≈0.3–0.7 s/pair → 480k pairs ≈ 40–90 h CPU; start with 10k queries (≈10 h).
4. Student A: e5-small, `MarginMSELoss` + `MultipleNegativesRankingLoss` (msmarco-margin-mse-mnrl recipe), batch 16, 256 tokens, 3–5k steps (≈15–25 s/step on 4 cores → 1–2 days); re-encode C (3.3 h).
5. Student B: mmarco-MiniLM-L12 with `CrossEncoder` MSE on teacher logits (same pairs), ≈45 s/step measured in exp 15 → 2k steps ≈ 1 day.
6. Evaluate on A/B/C with the harness; held-out questions stay unseen.

**Expected gain and cost**

- Dense leg C: 0.433 → ~0.50–0.55 (quarter-to-half of gap to 0.70); hybrid 0.62 → ~0.65.
- Small reranker on C: 0.593 → ~0.64–0.66 at 2 s/query instead of 20 s.
- Combined plausibly 0.66–0.68 at ~3 s/query; 0.70 still needs the teacher.
- Cost: ~2–4 CPU-days of queued jobs, no new infrastructure.

**Risks / open questions**

- The teacher itself is only 0.70 MRR on our questions: we distil its errors; noisy mT5 queries amplify them.
- CPU budget: literature uses 10⁵–10⁸ pairs; we can afford ~10⁴–10⁵. Gains may be marginal at that scale.
- Regional/yearly duplicates yield near-identical candidates (deduplicate first, topic 26).
- Tiny evaluation sets (29/40/64 questions): ±0.05 MRR noise.

**Verdict**

try-when-LLM — the recipe is mature and cheap in code, but the teacher-scoring and student-training budget on 4 cores is days, and DeepSeek-generated queries (topic 12/69) are what makes the pseudo-labels trustworthy; run a 10k-query pilot on student B first once a GPU or LLM is available.

**Sources**

- https://arxiv.org/abs/2010.02666 (Margin-MSE, 2020)
- https://arxiv.org/abs/2104.06967 (TAS-B, 2021)
- https://arxiv.org/abs/2112.07577 · https://github.com/UKPLab/gpl (GPL, 2022)
- https://arxiv.org/html/2607.11465v1 (Score-Only Distillation, Jul 2026)
- https://arxiv.org/html/2505.19274v1 (listwise CE distillation + synthetic data, 2025)
- https://arxiv.org/html/2603.03010 (distillation for cross-encoders reproduced, Aug 2026)
- https://arxiv.org/abs/2604.04734 (stratified score sampling, SIGIR 2026)
- https://huggingface.co/blog/ettin-reranker (May 2026)
- https://sbert.net/examples/cross_encoder/training/distillation/README.html
- https://arxiv.org/abs/2110.07367 (RocketQAv2, MRR@10 38.8)
