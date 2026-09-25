# 75 — Learning-to-rank with very few queries

**Idea**

Treat the 133 questions as the *tiny* LETOR set they are and use the model class the literature recommends for that regime: a **regularised linear pairwise/listwise ranker over ≤ 10 per-query-normalised features**, selected and reported with nested cross-validation. LambdaMART stays a diagnostic until we have several hundred labelled queries. The cross-encoder score enters as *one feature* (plus a missing-flag), not as the final score.

**Why it fits this project**

- Exp 14 already shows the predicted pattern: logistic regression on cheap features reaches OOF MRR 0.73 on A (≈ whole-doc BM25, no cross-encoder), while LambdaMART goes 0.96 train → 0.66 val on 17 questions.
- Our features are few and mostly monotone (higher score ⇒ more relevant; region contradiction ⇒ less): ~10 readable coefficients.
- `protocol.py` already has train/val/swapped/OOF; it lacks per-query normalisation and an inner loop for C / feature-set choice, so 0.73 is mildly optimistic.

**Evidence**

- Learning-curve studies on web LTR (Macdonald, Santos & Ounis 2013) found tree/listwise learners need hundreds–thousands of queries to beat linear models. [from memory, unverified]
- LETOR 3.0/4.0 apply **query-level min-max normalisation** to every feature (Qin & Liu 2013; 1700 + 800 queries). Raw BM25/dense scores are not comparable across queries; the global `StandardScaler` in `train_ltr.py` leaks query difficulty.
- RankSVM (Joachims 2002) and coordinate ascent on a linear feature model (Metzler & Croft 2007) were built for tens of features and 50–150 TREC topics; coordinate ascent optimises MRR/nDCG directly (RankLib).
- LambdaMART (Burges 2010) is evaluated on "hundreds of thousands of training queries". LightGBM's small-data levers (verified on the docs page): `num_leaves`, `min_data_in_leaf`, `lambda_l2`, `min_gain_to_split`, `feature_fraction`, `extra_trees`, `path_smooth`, `monotone_constraints`, `linear_tree`. `lgbm-tiny` already has leaves=3, λ₂=5; the missing levers are monotone constraints and far fewer features.
- Reranker as a feature: Zhang, Yates & Lin 2021 add monoBERT/monoT5 scores to LambdaMART over BM25/metadata and beat the reranker alone on MS MARCO; BM25–BERT interpolation (Wang, Zhuang & Zuccon 2021) shows the same with one weight. [from memory; fetch failed]
- Nested CV: Cawley & Talbot 2010 show selecting hyper-parameters on the folds you report from gives sizeable optimistic bias on small data.
- Sanity: ~133 positive instances; a 10-weight linear model (≈ 13 positives/parameter) is at the edge, 50 features is not.

**How we would implement it**

1. `features.py`: per-question min-max (or floored z-score) on every score feature; keep log-ranks and flags.
2. `train_ltr.py`: keep `pairwise-linear` (RankSVM-like); add ListNet-style softmax over ≤ 10 weights (`scipy.optimize`, L2 1–10) and coordinate ascent on MRR (10 restarts).
3. Feature set: e5_qnorm, bm25_qnorm, bm25doc_qnorm, rrf60, title_overlap, region_match, region_contradict, year_match, is_yearly_edition, bge_qnorm + bge_missing. Drop one-hot types (17 questions cannot support them).
4. Nested protocol: outer = existing swapped 2-fold + OOF; inner = leave-one-question-out over C ∈ {0.03…3} × {minimal, minimal+meta}. Report OOF MRR with a per-question bootstrap CI.
5. Transfer: fit on A+B, evaluate on C (all permutations). Per-query normalisation makes the weights corpus-agnostic; this is the real generalisation test.
6. `lgbm-tiny` + `monotone_constraints` only to confirm trees still lose.

**Expected gain and cost**

- Quality: A stays ≈ 0.73 (honest number may drop 0.01–0.02 after nesting); +0.02–0.05 on B/C where region/year flags and bge-as-feature help. Main value is a *trustworthy, transferable* fusion rule, not a big lever.
- Cost: half a day; seconds per run on the exp-14 caches.

**Risks / open questions**

- ±0.05 MRR eval noise at 30–60 questions: only cross-corpus consistency counts as evidence.
- Per-query min-max squashes score gaps and is undefined for one-candidate lists; compare with floored z-score.
- Past ~300 questions, revisit tiny monotone LambdaMART.

**Verdict**

**try-now** — a regularised linear pairwise/listwise ranker on ≤ 10 per-query-normalised features, chosen by nested CV and tested across corpora, is the textbook answer to 17-question folds, costs half a day on existing caches, and turns 0.73 into a number we can trust and ship.

**Sources**

- https://arxiv.org/abs/1306.2597 (LETOR 4.0)
- https://lightgbm.readthedocs.io/en/latest/Parameters.html
- https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/MSR-TR-2010-82.pdf (RankNet→LambdaMART)
- https://www.jmlr.org/papers/volume11/cawley10a/cawley10a.pdf (nested CV)
- https://www.cs.cornell.edu/people/tj/publications/joachims_02c.pdf (RankSVM) [URL unverified]
- https://ciir.cs.umass.edu/pubfiles/ir-486.pdf (Metzler & Croft 2007) [URL unverified]
- https://sourceforge.net/p/lemur/wiki/RankLib/
- https://aclanthology.org/2021.sustainlp-1.14/ (Zhang, Yates, Lin 2021) [unverified]
- https://arxiv.org/abs/2010.10469 (Wang, Zhuang, Zuccon 2021) [ID unverified]
- Macdonald, Santos, Ounis 2013, "The whens and hows of learning to rank for web search", Information Retrieval 16(5) [not fetched]
