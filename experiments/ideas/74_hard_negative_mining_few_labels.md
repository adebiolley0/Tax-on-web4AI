# 74 — Hard-negative mining and contrastive fine-tuning with few labels

**Idea**

Treat the *negatives*, not the 70 questions, as the scarce resource: mine them from our hybrid retriever (BM25 ∪ e5), filter false negatives with a positive-anchored margin plus a cross-encoder, and fine-tune e5-small with MNRL under a low-LR, one-epoch regime that keeps the multilingual base intact. The same triplets feed the exp 15 cross-encoder job.

**Why it fits this project**

- Exp 15 used "top BM25 chunks of non-expected docs" as negatives and gave no gain (A 0.604, B 0.494, C 0.593). Literature says naive top-k negatives are the worst option.
- Yearly editions and regional variants make a top-k negative often a *correct* answer from another year/region — the false-negative failure RocketQA measured (70 % of unlabeled top passages were positives; MRR@10 32.4 → 26.0 before denoising).
- Stock `sentence-transformers` (`mine_hard_negatives`, `CachedMultipleNegativesRankingLoss`), CPU-feasible.

**Evidence**

- Sample efficiency: BSARD fine-tuned a bi-encoder on **886** French legal questions with in-batch negatives only (batch 22, lr 2e-5, 100 epochs): R@100 51.3 → 74.8, MAP@100 16.0 → 35.7 vs BM25. SetFit works from 8 examples/class by expanding each into R=20 contrastive pairs; Promptagator's 8 examples work *because* an LLM expands them (topic 12). We know no study showing gains from <100 raw queries without expansion (unverified).
- Negative quality: ANCE MS MARCO MRR@10 — in-batch 0.256, random 0.261, BM25 negatives 0.299, self-mined refreshed every 10k batches 0.330. NV-Retriever: naive top-k 0.541 → top-k shifted by 10 0.570 → TopK-MarginPos (0.05) 0.584 → **TopK-PercPos (95 % of positive score) 0.586** nDCG@10; bigger teachers mine better negatives. RocketQA: denoised hard negatives (CE score < 0.1 kept as negative, > 0.9 relabelled positive) 36.4 vs 26.0 undenoised. SimANS: sample negatives ranked *near* the positive, not the very top. DRAGON: negatives drawn uniformly from ranks 45–50; CE-only labels did not help.
- Losses: sbert marks MNRL / CachedMNRL the default for (anchor, positive, negative…) rows; GISTEmbed drops in-batch false negatives with a guide model ("significant enhancements for smaller models"); GradCache/CachedMNRL gives large batches at constant memory. Margin-MSE needs teacher scores (topic 13); CoSENT is for graded similarity, not retrieval.
- Regimes: BSARD lr 2e-5; sbert examples 1 epoch, warmup 0.1, `NO_DUPLICATES`; NV-Retriever: `relative_margin=0.05, num_negatives≤10`.

**How we would implement it**

1. *Candidates*: hybrid top-50 chunks (BM25 ∪ e5-small) per train question, gold document excluded.
2. *Dedup gate (critical)*: drop candidates sharing the gold document's canonical id (topic 26: same title stem, other year/region) or with shingle Jaccard > 0.6 to the positive.
3. *False-negative filter*: `mine_hard_negatives(relative_margin=0.05, range_min=3, range_max=40, num_negatives=8, sampling_strategy="random", cross_encoder=bge-reranker-v2-m3)`; drop candidates the CE scores ≥ 0.9 (RocketQA) or relabel them as positives after a manual glance.
4. *Expand pairs*: every gold chunk of a document is a positive (~300–600 rows); add 3k BSARD rows (exp 16 loader) as legal "replay" against forgetting.
5. *Train*: e5-small, CachedMNRL (effective batch 128, mini-batch 16), lr 1e-5, 1 epoch, warmup 0.1, `NO_DUPLICATES`, max_seq 256; ≈ 1–2 h CPU. One ANCE-style refresh: re-mine with the tuned model, second epoch.
6. *Cross-encoder*: reuse the same triplets in exp 15 (`BinaryCrossEntropyLoss`), replacing the current unfiltered BM25 negatives.
7. Evaluate on the held-out split; report train vs val MRR to expose memorisation.

**Expected gain and cost**

Dense leg on B/C +0.02–0.05 MRR at best, likely invisible after bge-reranker; the cross-encoder retrain may turn exp 15's 0.0 into +0.02–0.04. Cost: ~1 day engineering, 2–4 h CPU per run, no LLM. The step change (+0.05–0.10) needs 1–3k in-domain pairs → topic 12.

**Risks / open questions**

- 70 queries: the val split (12–35 questions) has ±0.05–0.08 MRR noise; only large effects will register.
- Margin filtering on weak e5-small scores may discard most candidates; fall back to CE-only filtering.
- BSARD replay is CC-BY-NC-SA (research use only) and general law, not tax.
- Duplicates missed by the dedup heuristic still poison negatives; over-training may degrade Dutch/German bodies (monitor a Dutch-body subset).

**Verdict**

**try-now** — cheap and it fixes a known defect in exp 15's negatives (yearly/regional false negatives), but treat it as hygiene ahead of synthetic-data fine-tuning rather than the source of a headline gain.

**Sources**

- https://sbert.net/docs/package_reference/util/hard_negatives.html (`mine_hard_negatives`, NV-Retriever defaults)
- https://sbert.net/docs/sentence_transformer/loss_overview.html · https://sbert.net/docs/cross_encoder/training_overview.html
- https://arxiv.org/abs/2407.15831 (NV-Retriever, positive-aware mining)
- https://arxiv.org/abs/2010.08191 (RocketQA, denoised negatives)
- https://arxiv.org/abs/2007.00808 (ANCE)
- https://arxiv.org/abs/2210.11773 (SimANS) · https://arxiv.org/abs/2302.07452 (DRAGON)
- https://arxiv.org/abs/2402.16829 (GISTEmbed) · https://arxiv.org/abs/2101.06983 (GradCache)
- https://arxiv.org/abs/2108.11792 (BSARD, 886 train questions)
- https://arxiv.org/abs/2209.11055 (SetFit) · https://arxiv.org/abs/2209.11755 (Promptagator)
- https://arxiv.org/abs/2403.18684 (scaling laws for dense retrieval; power law in annotations)
- In-repo: `experiments/15_finetune/{data.py,ft_mmarco.log}`, `experiments/16_legal_models/bsard_data.py`, ideas 12, 13, 26
