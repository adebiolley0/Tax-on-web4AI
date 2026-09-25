# 75 — Learning-to-rank with very few queries

**Idea**

Treat the 133 questions as what they are — a *tiny* LETOR set — and use the model class the LETOR literature recommends for that regime: a **regularised linear pairwise/listwise ranker over ≤ 10 per-query-normalised features**, selected and reported with nested cross-validation. Tree ensembles (LambdaMART) stay as a diagnostic, not a candidate, until we have several hundred labelled queries. The cross-encoder score enters as *one feature* (with a missing-flag) rather than replacing the ranking.

**Why it fits this project**

- Exp 14 already shows the pattern the literature predicts: logistic regression on cheap features reaches OOF MRR 0.73 on A (≈ whole-doc BM25's 0.736 without any cross-encoder), while LambdaMART goes 0.96 train → 0.66 val on 17 questions — classic variance blow-up.
- Our features are few and mostly monotone (score higher ⇒ more relevant; region contradiction ⇒ less), which a linear model expresses with ~10 coefficients we can read and sanity-check.
- Train/val/OOF (`protocol.py`) is already the right skeleton; it lacks per-query normalisation and an inner loop for C / feature-set choice, so the reported 0.73 is mildly optimistic.

**Evidence**

- Learning-curve studies on web LTR (Macdonald, Santos & Ounis 2013, IRJ, *whens and hows*) found tree/listwise learners need hundreds to thousands of queries before beating linear models; linear learners saturate after tens of queries. [from memory; numbers unverified]
- LETOR 3.0/4.0 apply **query-level min-max normalisation** of every feature before learning (Qin & Liu 2013, 1700 + 800 queries in MQ2007/8); raw BM25/dense scores are not comparable across queries and a global `StandardScaler` (what `train_ltr.py` does) leaks query difficulty into the score.
- Linear pairwise models: RankSVM (Joachims 2002) and coordinate ascent on a linear feature model (Metzler & Croft 2007) were designed for tens of features and small TREC topic sets (50–150 queries); coordinate ascent directly optimises MRR/nDCG and is in RankLib.
- LambdaMART overview (Burges 2010) is evaluated on "hundreds of thousands of training queries"; LightGBM's own regularisers for small data are `num_leaves`, `min_data_in_leaf`, `lambda_l2`, `min_gain_to_split`, `feature_fraction`, `extra_trees`, `path_smooth`, `monotone_constraints`, `linear_tree` (verified on the docs page). Exp 14 `lgbm-tiny` already uses leaves=3, λ₂=5; the missing lever is *monotone constraints* + far fewer features.
- Neural score as a feature: Zhang, Yates & Lin 2021 ("LTR in the age of Muppets", SustaiNLP) add monoBERT/monoT5 scores to LambdaMART over BM25/metadata features and gain over the reranker alone on MS MARCO; BM25–BERT interpolation gains (Wang, Zhuang & Zuccon 2021) show the same for a single weight. [both from memory, could not fetch]
- Nested CV / selection bias: Cawley & Talbot 2010 (JMLR) show that choosing hyper-parameters on the same folds you report from gives a sizeable optimistic bias on small datasets; the fix is an inner loop for selection, outer loop for reporting.
- Sample-size sanity: with ~2 relevant docs per query, 133 queries ≈ 133 positive instances; a 10-feature linear model at ≈ 13 positives/parameter is at the edge; 50 features is not.

**How we would implement it**

1. `features.py`: add a `qnorm` transform — per-question min-max (or z-score) on every score feature; keep ranks/log-ranks and flags as is.
2. `train_ltr.py`: methods `pairwise-linear` (already RankSVM-like) and a **listwise softmax** (ListNet-style, `scipy.optimize` on ≤ 10 weights, L2 ≈ 1–10); add coordinate ascent on MRR as a third (RankLib-equivalent, 20 lines).
3. Feature set `minimal+meta` pruned to: e5_qnorm, bm25_qnorm, bm25doc_qnorm, rrf60, title_overlap, region_match, region_contradict, year_match, is_yearly_edition, bge_qnorm + bge_missing. Drop one-hot types (17 questions cannot support them) except a single "is circulaire/code" bit if stable.
4. Nested protocol: outer = the existing swapped 2-fold (fit-train/fit-val/OOF); inner = leave-one-question-out over C ∈ {0.03, 0.1, 0.3, 1, 3} and feature subset ∈ {minimal, minimal+meta}. Report OOF MRR with a bootstrap CI over questions.
5. Transfer test: fit on A+B, evaluate on C (and each permutation) with per-query normalisation — the coefficients are corpus-agnostic by construction, so this is the real generalisation test.
6. LambdaMART only as `lgbm-tiny` + `monotone_constraints` on all score features, to confirm it still cannot beat linear.

**Expected gain and cost**

- Quality: linear OOF MRR ≈ current 0.73 on A (honest number may drop 0.01–0.02 after nesting); +0.02–0.05 on B/C where region/year flags matter and where bge-as-feature can rescue bge's misses. Not a large lever; the value is a *trustworthy, transferable* fusion rule.
- Cost: half a day; runs in seconds on the cached tables.

**Risks / open questions**

- Eval noise ±0.05 MRR at 30–60 questions: only cross-corpus consistency, not any single delta, is evidence.
- Per-query min-max is undefined for single-candidate lists and squashes gaps; z-score with a floor may be better — test both.
- Coordinate ascent optimises MRR directly but is non-convex; use 10 restarts.
- Once the question set grows past ~300, revisit tiny LambdaMART with monotone constraints.

**Verdict**

**try-now** — a regularised linear pairwise/listwise ranker on ≤ 10 per-query-normalised features, selected by nested CV and tested across corpora, is the textbook answer to 17-question training folds, costs half a day on the exp-14 caches, and turns the 0.73 into a number we can trust and ship.

**Sources**

- https://arxiv.org/abs/1306.2597 (LETOR 4.0, Qin & Liu 2013)
- https://lightgbm.readthedocs.io/en/latest/Parameters.html (regularisation, monotone_constraints, lambdarank_*)
- https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/MSR-TR-2010-82.pdf (RankNet→LambdaMART)
- https://www.jmlr.org/papers/volume11/cawley10a/cawley10a.pdf (nested CV, selection bias)
- https://www.cs.cornell.edu/people/tj/publications/joachims_02c.pdf (RankSVM) [unverified URL]
- https://ciir.cs.umass.edu/pubfiles/ir-486.pdf (Metzler & Croft 2007, coordinate ascent) [unverified URL]
- https://sourceforge.net/p/lemur/wiki/RankLib/ (coordinate ascent, LambdaMART implementations)
- https://aclanthology.org/2021.sustainlp-1.14/ (Zhang, Yates, Lin — LTR in the age of Muppets) [fetch returned wrong PDF; unverified]
- https://arxiv.org/abs/2010.10469 (Wang, Zhuang, Zuccon — BERT rerankers need BM25 interpolation) [unverified ID]
- Macdonald, Santos, Ounis 2013, "The whens and hows of learning to rank for web search", Information Retrieval 16(5) [not fetched]
