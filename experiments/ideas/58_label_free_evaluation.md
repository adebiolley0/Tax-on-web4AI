# 58 — Retrieval evaluation without (many) labels: LLM judges, synthetic collections, calibration

**Idea**

Stop treating the 133 hand-written questions (29 A + 40 B + 64 C) as the only ground truth. Grow the evaluation set to 500+ questions by (1) generating document-grounded questions whose source document is a free positive label, (2) pooling the top-k of several retrievers and letting an LLM judge (UMBRELA-style graded prompt) mark *additional* relevant documents, and (3) calibrating the judge against a small stratified human sample so that reported MRR/nDCG carry corrected estimates and confidence intervals (prediction-powered inference, as in ARES).

**Why it fits this project**

- Our bottleneck is measurement, not models: with n≈130 the MRR standard error is ≈0.04–0.05, so most ideas in this folder (+0.02…+0.05) are undetectable. n=500 halves the noise; n=1,000 makes ±0.03 significant.
- Several C questions already admit multiple acceptable ids (yearly/regional editions); unjudged near-duplicates are false negatives that penalise dense/reranked runs unfairly. Pooled judging fixes exactly this.
- Questions were written from documents with descriptive titles (EXPERIMENTS.md §5), which favours BM25. A generator prompted for layman phrasing, region/year slots and topic-less doc types (rulings, PQs) rebalances the set.
- The corpus is public and the judge only needs French legal reading comprehension, which DeepSeek handles; no user data is involved.

**Evidence**

- Thomas et al. (Bing), *LLMs can accurately predict searcher preferences*: LLM labels as accurate as human labellers, better than crowd workers, at a fraction of the cost; prompt wording (even paraphrases) changes accuracy.
- UMBRELA (Upadhyay et al. 2024): open-source GPT-4o reproduction of that prompt; LLM judgments correlate highly with human-based system rankings on TREC DL 2019–2023; adopted by TREC 2024 RAG. Follow-up large-scale study (77 runs, 19 teams): high system-ranking correlation for nDCG@20/100 and R@100; humans judged *more strictly* than the LLM; human-in-the-loop variants did not improve correlation.
- SynDL: fully synthetic relevance labels over 1,900 TREC DL queries yield system rankings highly correlated with human ones.
- Clarke & Dietz, *LLM-based relevance assessment still can't replace human relevance assessment*: circularity when systems and judge share an LLM, "narcissism" toward LLM-like text, and a deliberately gamed run that inflated automatic scores. Soboroff, *Don't use LLMs to make relevance judgments* (2409.15133, not fetched) argues the same for benchmark collections.
- Faggioli et al., *Perspectives on LLMs for relevance judgment*: human–machine collaboration spectrum; recommends keeping humans on a verification tier rather than removing them.
- ARES: lightweight LM judges plus PPI with "a few hundred" human annotations give unbiased RAG metrics with confidence intervals, robust to domain shift.
- Promptagator / InPars: 8-shot LLM query generation with consistency filtering trains retrievers that beat ColBERTv2; the same generator serves evaluation-set growth.

**How we would implement it**

1. *Generation (DeepSeek, once available)*: sample 600 documents stratified by document type and topic (doc-type counts from `myfin_docs/`), excluding TOC/index pages per the filtering policy. Prompt with 8 of our own questions as exemplars; ask for one taxpayer-style question per document, with an evidence quote, and for layman wording in 50 % of cases. Reject questions whose quote is not found verbatim in the document.
2. *Pooling*: run BM25-fr, e5/bge dense, hybrid and hybrid+reranker; pool top-20 per system (~40 unique docs/question).
3. *Judging*: UMBRELA prompt translated to French, 0–3 scale, document title + first 1,500 tokens + the passage best matching the question (BM25 within-document). Use a **different model family from any reranker/rewriter in the pipeline** (e.g. judge with DeepSeek, rerank with bge-reranker-v2-m3, or the reverse); never judge with a model that is a pipeline component.
4. *Calibration*: humans label 150 (question, document) pairs stratified by judge grade and system; compute κ and per-grade precision; apply PPI to report corrected MRR/nDCG with intervals through `rag_eval`, tagging runs `label_source=llm_calibrated` in `leaderboard.jsonl`.
5. *Quality control*: 10 % human spot-check of generated questions (drop rate target < 15 %); judge self-consistency on 100 re-judged pairs (κ ≥ 0.7 else fix prompt); keep the 133 human questions as a held-out sanity set and require the same system ordering on both.

**Expected gain and cost**

No retrieval gain; a measurement gain: SE(MRR) from ≈0.05 to ≈0.025 at n=500, plus removal of false negatives (expect +0.02–0.04 absolute on dense/reranked runs once near-duplicate editions are judged). Cost: ~500 × 40 pairs × ~2k tokens ≈ 40M input tokens, roughly €10–20 at DeepSeek prices (unverified), one CPU day for pooling, ~6 h of human labelling for calibration and spot checks.

**Risks / open questions**

- Judge bias toward lexically matching or fluent text; humans judged more strictly in TREC RAG, so the LLM set will inflate absolute scores — use it for *relative* comparisons and report calibrated numbers.
- Document-grounded questions are "easy" by construction (the answer is in one document); multi-hop and clarification questions still need humans.
- Generated-question distribution drifts from real user questions; keep the human set as the anchor.
- Pseudo-labels from bge-reranker are circular for evaluating runs containing that reranker; use them only for hard-negative mining (idea 74), not evaluation.

**Verdict**

**try-when-LLM** — the single cheapest way to make the rest of this folder measurable; nothing to run until DeepSeek is available, but the pooling and calibration harness can be prepared now.

**Sources**

- https://arxiv.org/abs/2309.10621 (Thomas et al., Bing)
- https://arxiv.org/abs/2406.06519 (UMBRELA)
- https://arxiv.org/abs/2411.08275 (TREC 2024 RAG large-scale study)
- https://arxiv.org/abs/2408.16312 (SynDL)
- https://arxiv.org/abs/2412.17156 (Clarke & Dietz)
- https://arxiv.org/abs/2409.15133 (Soboroff; not fetched)
- https://arxiv.org/abs/2304.09161 (Faggioli et al.)
- https://arxiv.org/abs/2311.09476 (ARES, PPI)
- https://arxiv.org/abs/2209.11755 (Promptagator)
- https://github.com/castorini/umbrela
