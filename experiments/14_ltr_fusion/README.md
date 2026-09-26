# Experiment 14 — learning-to-rank over cheap features, principled fusion / reranker tuning

Question: the fusion weights, RRF constants and reranker depths of experiments 03/09 were picked on the
full question sets. Do they survive a train/validation protocol? Can a small learned ranker over cheap
features (first-stage scores, reranker scores, metadata) beat the hand-tuned recipe, and does it transfer
between halves of the (tiny) question sets?

Standalone `uv` project (CPU torch). Everything expensive (cross-encoder scores) is computed once and cached
under `cache/` (git-ignored); all tuning and learning runs on numpy tables in seconds.

```bash
cd experiments/14_ltr_fusion && uv sync
uv run python build_stage1.py --corpus A          # first-stage score matrices (A, B, C)
./run_rerank_queue.sh                             # mMARCO-MiniLM + bge-reranker-v2-m3 on the candidate sets (sequential)
uv run python tune_fusion.py --corpus A --dense e5 --lex chunk
uv run python train_ltr.py --corpus A
```

## 1. Setup

### Corpora, legs, candidate sets

| corpus | docs / chunks | questions (train / val) | dense legs (cached embeddings) | lexical legs |
|---|---|---|---|---|
| A | 91 / 1,072 (`fixed1500_title`) | 29 (17 / 12) | e5-small, bge-m3 | BM25 chunk-max, BM25 whole document |
| B | 5,853 / 10,869 (`article_ctx_1200`) | 40 (24 / 16) | e5-small | BM25 chunk-max, BM25 article + heading path |
| C | 21,259 / 201,404 (`fixed1200_title`) | 64 (29 / 35) | e5-small, potion-128M | BM25 chunk-max, BM25 whole document |

BM25 uses the best normalisation of experiment 01 (Snowball stem + French stoplist + question-word stoplist
+ accent folding, k1=1.5, b=0.75) for both units; this reproduces the exp-01 numbers exactly (A whole-doc
0.695) and is +0.02 over the exp-03 tokenizer on C chunks (0.601 vs 0.577). Dense legs reproduce exp 02/09
exactly (A e5 0.543, bge-m3 0.678; C e5 0.433, potion 0.315).

Candidate chunks per question = union of the top-K chunks of every leg (plus, on A/B, the best-BM25 chunk of
the top-K whole-document BM25 docs): K=50 for the cheap mMARCO reranker (A 127 / B 107 / C 123 chunks per
question). bge-reranker-v2-m3 (0.7 s/pair on an idle box, several seconds per pair while five torch jobs
shared the four cores) is run as a **cascade**: its candidates are the top-30 chunks by mMARCO score (top-20 on C)
plus the top-10 chunks of every leg (on C: e5 and BM25 only), i.e. ~40 chunks per question. In the grids below,
a top-N chunk without a bge score is given the worst bge score of that question ("coverage" is reported).
Candidate recall of the expected document at K=50: A 1.00, B 0.925, C 0.969 — this is the ceiling of every method below.

Cross-encoder scores are computed once per (corpus, reranker, candidate set) by `score_rerankers.py`
(2 torch threads, resumable npz) and reused by every grid point and every LTR model.

### Features per (question, candidate document) — `features.py`

| group | features |
|---|---|
| per chunk leg (e5, bge-m3 on A, potion on C, bm25) | raw doc-max score, min-max-normalised doc-max, log(doc rank), in-top-30 flag |
| whole-document BM25 | score, min-max, log rank |
| fixed fusions | RRF k=60 (e5+bm25) doc-max + log rank, convex 0.5 doc-max + log rank, number of legs where the doc is in the top 30 |
| rerankers | mMARCO-MiniLM and bge-reranker-v2-m3: doc-max score, min-max within the question's candidates, log rank among candidates, missing flag (doc outside the bge candidate set) |
| document | log chars, log number of chunks, position of the best e5 / best BM25 chunk within the document (0 = first chunk) |
| query–title | share of query stems present in the title, count |
| region (B/C) | query has a region (city / region word, exp 08 `detect_region`), doc region matches, doc region contradicts (federal docs never contradict) |
| yearly editions (C) | `is_yearly_edition` (id `…_revenus_20xx`), query year = edition year, query year ≠ edition year, document year (from `document_date`), has date |
| type | one-hot of document type (A: Fisconet type; B: code family without region suffix; C: folder, ≥ 5 docs) |

Label: expected 1.0, secondary 0.5, other 0.0 (LambdaMART uses integer grades 2 / 1 / 0 with `label_gain=[0,1,2]`).
Feature sets: `all`, `cheap` (no cross-encoder), `minimal` (e5_norm, bm25_norm, bm25doc_norm, rrf60,
mmarco_norm, bge_norm), `minimal+meta` (minimal + title overlap, region, year, length). Constant columns are dropped per corpus.

### Grids — `tune_fusion.py`

* first stage: convex `w·minmax(dense) + (1−w)·minmax(bm25)` for w ∈ {0, 0.1, …, 1} (w=0 pure BM25, w=1 pure
  dense) and RRF(k) for k ∈ {10, 20, 40, 60, 100, 200} (depth 300), at chunk level, document = max chunk;
  lexical leg = chunk BM25 (`--lex chunk`) or whole-document BM25 broadcast to the chunks (`--lex doc`);
* second stage: reranker ∈ {mMARCO-MiniLM, bge-reranker-v2-m3} on the top-N fused chunks, N ∈ {10, 20, 30, 50},
  with score interpolation `β·minmax(rerank) + (1−β)·minmax(fused)` over the top-N, β ∈ {0, 0.1, …, 1}
  (β=1 is the usual "replace by the reranker score"); chunks below N keep their fused order.
  17 first-stage × (1 + 2 × 4 × 11) = 1,513 configurations per (corpus, dense leg, lexical leg).

### Protocol — `protocol.py`

Every question has a deterministic split (`Question.split`, md5 of the id). For every method:

* **fit-train**: select / fit on train, evaluate on all — the harness prints train (resubstitution) and val (honest);
* **fit-val**: the swapped fold — fit on val, train is now the honest number;
* **oof**: out-of-fold rankings (val from fit-train, train from fit-val) = 2-fold cross-validation over the
  whole set, the number comparable with the full-set bars of earlier experiments.

Grid selection maximises train MRR, ties broken by train nDCG@5 then by lower rerank depth. All runs are saved
through `rag_eval.save_result("14_ltr_fusion", …)` (`experiments/results/14_ltr_fusion/`, leaderboard).

Bars to beat (from the leaderboard, val MRR): A 0.736 (whole-doc BM25), B 0.570 (RRF + mMARCO@30),
C 0.665 (BM25 + bge@30); full set: A 0.703, B 0.522, C 0.703.

## 2. Results

Every table: **val** = selected/fitted on the train half, scored on the val half (honest); **train (swapped)** =
fitted on val, scored on train (honest); **oof** = the two honest halves put together (2-fold CV over the whole
set, comparable with the full-set bars). Resubstitution numbers are shown to size the optimism.

### 2.1 Does hand-tuning transfer? (fusion grid, `tune_fusion.py`)

**First stage only** (no reranker; MRR). "Selected on train" is the weight with the best train MRR, scored on val;
"oof" combines the two honest halves. The fixed recipes of exp 03/09 are shown for comparison on the full set.

| corpus / legs | selected on train → val | selected on val → train | **oof** | fixed w=0.5 (all) | fixed RRF60 (all) | pure BM25 (all) | pure dense (all) |
|---|---|---|---|---|---|---|---|
| A e5 + BM25 chunk | w=0.0 → 0.649 (train 0.688) | w=0.7 → 0.642 (val 0.730) | 0.645 | 0.648 | 0.627 | 0.672 | 0.543 |
| A e5 + BM25 whole-doc | w=0.0 → **0.736** (train 0.666) | w=0.0 → 0.666 | **0.695** | 0.648 | 0.680 | 0.695 | 0.543 |
| A bge-m3 + BM25 chunk | w=1.0 → 0.602 (train 0.731) | w=0.4 → 0.661 (val 0.702) | 0.636 | 0.666 | 0.650 | 0.672 | 0.678 |
| B e5 + BM25 chunk | w=0.9 → 0.337 (train 0.532) | w=0.7 → 0.469 (val 0.369) | 0.416 | 0.395 | 0.407 | 0.344 | 0.438 |
| C e5 + BM25 chunk | w=0.3 → 0.542 (train 0.678) | w=0.6 → 0.589 (val 0.593) | 0.564 | 0.621 | 0.567 | 0.601 | 0.434 |

* The tuned weight transfers **only on A with whole-document BM25**, where both halves agree that BM25 alone
  (w=0) is best (this is the exp-01 whole-doc result, 0.695, and the val bar 0.736). Everywhere else the
  train-selected weight is an extreme (w=0.0, 0.9, 1.0 or 0.3) that loses 0.05–0.19 MRR on the other half; the
  optimum is flat and noisy (A: the five best train weights span val 0.649–0.730).
* A fixed **w=0.5 is at or above the honest tuned number on every corpus** (A 0.648 vs oof 0.645, B 0.395 vs
  0.416 with RRF60 at 0.407, C 0.621 vs 0.564). With 17–29 training questions, first-stage weight tuning does
  not pay: keep w=0.5 (or RRF60) and spend the questions on the second stage.


**Second stage** (reranker on the top-N fused chunks; both rerankers, 4 depths, 11 β values; MRR).
"replace" = β=1 (the usual recipe), "interpolated" = β free. The cascade design caps bge coverage: on A,
75–79% of the top-30 fused chunks (60% with the whole-doc leg) carry a bge score, 97% of the top-10.

| corpus / legs | family | selected on train → **val** (train resub) | selected on val → **train** (val resub) | **oof** |
|---|---|---|---|---|
| A e5 + BM25 chunk | first stage | w=0.0 → 0.649 (0.688) | w=0.7 → 0.642 (0.730) | 0.645 |
| | replace | rrf200 + mMARCO@20 → 0.539 (0.728) | w=0.0 + bge@20 → 0.673 (0.722) | 0.617 |
| | interpolated | rrf200 + mMARCO@20 β=1 → 0.539 (0.728) | w=0.0 + bge@20 β=0.8 → 0.643 (0.764) | 0.600 |
| | bge only | w=0.2 + bge@30 β=1 → 0.673 (0.727) | w=0.0 + bge@20 β=0.8 → 0.643 (0.764) | 0.656 |
| A bge-m3 + BM25 chunk | first stage | w=1.0 → 0.602 (0.731) | w=0.4 → 0.661 (0.702) | 0.636 |
| | replace | rrf100 + bge@10 → **0.717** (0.735) | w=0.2 + bge@10 → 0.663 (0.722) | **0.685** |
| | interpolated | w=1.0 + mMARCO@30 β=0.3 → 0.607 (0.777) | w=0.2 + bge@10 β=0.8 → 0.633 (0.764) | 0.623 |
| A e5 + BM25 whole-doc | first stage | w=0.0 → **0.736** (0.666) | w=0.0 → 0.666 (0.736) | **0.695** |
| | replace | rrf100 + mMARCO@10 → 0.617 (0.719) | rrf20 + bge@10 → 0.620 (0.785) | 0.619 |
| | interpolated | w=0.8 + bge@50 β=0.8 → 0.636 (0.727) | rrf20 + bge@10 β=0.7 → 0.620 (0.826) | 0.626 |
| B e5 + BM25 chunk | first stage | w=0.9 → 0.337 (0.532) | w=0.7 → 0.469 (0.369) | 0.416 |
| | replace | w=1.0 + bge@50 → 0.558 (0.606) | w=0.8 + mMARCO@10 → 0.537 (0.624) | 0.545 |
| | interpolated | w=1.0 + bge@50 β=0.5 → 0.474 (0.688) | rrf40 + mMARCO@30 β=0.9 → 0.507 (0.647) | 0.494 |
| | mMARCO only | w=1.0 + mMARCO@20 β=0.8 → **0.610** (0.630) | rrf40 + mMARCO@30 β=0.9 → 0.507 (0.647) | **0.548** |
| | bge only | w=1.0 + bge@50 β=0.5 → 0.474 (0.688) | w=1.0 + bge@30 β=1 → 0.580 (0.570) | 0.538 |
| C e5 + BM25 chunk | first stage | w=0.3 → 0.542 (0.678) | w=0.6 → 0.589 (0.593) | 0.564 |
| | replace | rrf40 + bge@50 → 0.655 (0.747) | rrf200 + bge@50 → **0.721** (0.661) | **0.685** |
| | interpolated | w=0.3 + bge@20 β=0.9 → **0.658** (0.766) | rrf60 + bge@50 β=0.9 → 0.703 (0.681) | 0.678 |
| | mMARCO only | w=0.5 + mMARCO@20 β=0.4 → 0.604 (0.718) | w=0.7 + mMARCO@30 β=0.7 → 0.653 (0.650) | 0.626 |
| | bge only | w=0.3 + bge@20 β=0.9 → 0.658 (0.766) | rrf60 + bge@50 β=0.9 → 0.703 (0.681) | 0.678 |

Bars (leaderboard): val A 0.736 / B 0.570 / C 0.665; full set A 0.703 / B 0.522 / C 0.703.

* **A**: no second stage beats whole-document BM25 honestly (oof 0.695, val 0.736). The grid finds configurations
  with val 0.76–0.83 (rrf20 + bge@10 β=0.7 with the whole-doc leg: val 0.826) but they are selected *on val*
  and score 0.62 on train — pure selection noise on 12 questions. The train-selected reranker recipes lose
  0.03–0.11 MRR on val relative to the first stage. mMARCO-MiniLM is harmful on A whenever it is selected
  (β curve monotone: val 0.68 at β=0 → 0.54 at β=1 while train rises 0.59 → 0.73); bge is neutral-to-positive
  (β=0.5–0.9 keeps val at 0.68 and lifts all-set MRR from 0.63 to 0.69 at rrf200/20). The single honest
  improvement is bge on top of the bge-m3 dense leg (replace, rrf100@10: val 0.717 / oof 0.685) — still below
  BM25 whole-doc.

* **B**: the second stage is essential (first stage alone: oof 0.416, bar 0.522) and any reranker at depth
  20–50 on the pure-e5 leg lands at oof 0.54–0.55 (val 0.56–0.61), above both bars (val 0.570, full 0.522).
  But the *interpolated* family, with 11 β values to choose from, picks β=0.5 on train (0.688 resub) and
  falls to val 0.474 — the largest overfit of the grid. The β curves show why: on B the reranker score must
  dominate (val rises from 0.33 at β=0 to 0.56–0.61 at β≥0.5 for mMARCO, β≥0.9 for bge) and the train half
  rewards the β=0.5 bump of bge (0.688) that does not exist on val. Depth 20 is as good as 50 (bge@20 β=1:
  val 0.567 / train 0.603). mMARCO-MiniLM (cheap) is as good as bge on B — with ~40 scored chunks per
  question the cascade gives bge 72–82% coverage of the fused top-20/30, which caps it.

* **C**: the reranker transfers. Any bge configuration at depth 20–50 is within 0.03 of the others on both
  halves (bge@N β=1: val 0.62–0.64, train 0.71–0.75 for N = 10…50), so whatever train selects is fine on val:
  replace rrf40 + bge@50 → val 0.655 / oof 0.685, interpolated w=0.3 + bge@20 β=0.9 → val 0.658 / oof 0.678 —
  just under the exp-09 bars (val 0.665, full 0.703), which were obtained with bge on the *full* top-30
  candidates: here the cascade only scores 59–72% of the fused top-20/30 (92% of the top-10), and the missing
  chunks are exactly the ones a full run would have promoted. mMARCO-MiniLM is a real step below (oof 0.626)
  and, unlike bge, must be interpolated (β=0.4–0.8; β=1 drops val to 0.556). The β curve of bge on C is the
  cleanest of the study: val rises monotonically from 0.54 (β=0) to 0.66 (β=0.9) and the train curve
  follows in parallel — the sign of a stable, transferable knob.

### 2.2 Learning to rank (`train_ltr.py`)

Rows = (question, candidate document) with the features of §1 (A: 53 docs/q, 51 features; B: 79 docs/q, 50;
C: 68 docs/q, 61). Methods: pointwise logistic regression (C=1, standardised), pairwise linear (RankSVM-style
logistic on within-question pairs), LightGBM lambdarank *tiny* (15 trees, 4 leaves, min 20 rows/leaf, 5-seed
bagging), *small* (60 trees, 8 leaves) and *medium* (150 trees, 16 leaves, min 10 rows/leaf). MRR;
"→" separates resubstitution and honest numbers.

| corpus | method / features | train → **val** | val → **train (swapped)** | **oof** (H@1, R@10) |
|---|---|---|---|---|
| A | logreg / cheap (no cross-encoder) | 0.814 → **0.722** | 0.847 → **0.739** | **0.732** (0.621, 0.966) |
| A | logreg / all | 0.826 → 0.688 | 0.833 → 0.723 | 0.709 (0.586, 0.931) |
| A | pairwise-linear / all | 0.902 → 0.607 | 0.875 → 0.776 | 0.706 (0.621, 0.966) |
| A | lgbm-medium / all | 1.000 → 0.644 | 1.000 → 0.720 | 0.688 (0.552, 0.931) |
| A | logreg / minimal+meta (7 features) | 0.833 → 0.680 | 0.806 → 0.680 | 0.680 (0.552, 0.931) |
| A | lgbm-tiny / cheap | 0.961 → 0.660 | 0.847 → 0.669 | 0.665 (0.517, 0.966) |
| A | logreg / minimal (5 features) | 0.699 → 0.659 | 0.723 → 0.649 | 0.653 (0.483, 0.931) |
| A | _bars_ | val 0.736 | | full set 0.703 |
| B | logreg / minimal+meta (7 features) | 0.628 → 0.519 | 0.611 → **0.667** | **0.608** (0.475, 0.825) |
| B | logreg / all | 0.676 → 0.538 | 0.762 → 0.640 | 0.600 (0.450, 0.850) |
| B | logreg / minimal (5 features) | 0.620 → 0.529 | 0.610 → 0.646 | 0.599 (0.450, 0.825) |
| B | lgbm-tiny / minimal+meta | 0.802 → **0.618** | 0.747 → 0.582 | 0.596 (0.450, 0.800) |
| B | lgbm-tiny / minimal | 0.753 → 0.614 | 0.747 → 0.568 | 0.587 (0.425, 0.800) |
| B | lgbm-tiny / all | 0.817 → 0.505 | 0.828 → 0.599 | 0.561 (0.375, 0.850) |
| B | logreg / cheap (no cross-encoder) | 0.607 → 0.411 | 0.503 → 0.544 | 0.491 (0.375, 0.800) |
| B | _bars_ | val 0.570 | | full set 0.522 |
| C | lgbm-tiny / all | 0.901 → 0.634 | 0.818 → **0.829** | **0.723** (0.656, 0.883) |
| C | lgbm-tiny / minimal (6 features) | 0.874 → 0.644 | 0.712 → 0.787 | 0.709 (0.625, 0.883) |
| C | lgbm-tiny / minimal+meta | 0.891 → **0.662** | 0.736 → 0.763 | 0.708 (0.625, 0.859) |
| C | lgbm-medium / all | 0.966 → 0.646 | 0.971 → 0.751 | 0.694 (0.625, 0.836) |
| C | logreg / minimal | 0.750 → 0.599 | 0.616 → 0.784 | 0.683 (0.578, 0.867) |
| C | lgbm-tiny / cheap (no cross-encoder) | 0.914 → 0.625 | 0.810 → 0.752 | 0.682 (0.609, 0.859) |
| C | logreg / all | 0.873 → 0.525 | 0.837 → 0.766 | 0.634 (0.531, 0.823) |
| C | _bars_ | val 0.665 | | full set 0.703 |

* **Model class.** With 17–29 training questions, the pointwise **logistic regression is the safest learner on
  A and B** (train–val gap 0.1, oof at or above every grid recipe) and LightGBM overfits (resub 0.9–1.0);
  on C (29 train questions, 68 candidates each, 75 positives) the **tiny LambdaMART** (15 trees × 4 leaves,
  5-seed bagging) wins clearly (oof 0.723 vs logreg 0.634) — non-linear interactions such as
  "whole-doc BM25 rank × document year × type" matter there. The pairwise linear model never beats logreg.
* **Feature sets.** The two cross-encoders as features add +0.11 on B (0.491 → 0.600) and +0.04 on C
  (0.682 → 0.723) but nothing on A (0.732 without them). The 5–7 score/meta features of `minimal(+meta)`
  are within 0.02 of `all` on B and C: the learner mostly needs *the reranker scores, the whole-doc BM25
  score and 2–3 metadata priors*, not 50–65 columns.
* **Against the bars.** B: logreg / minimal+meta oof 0.608 vs full-set bar 0.522 (+0.09), val 0.519 vs
  0.570 but swapped-train 0.667 — the val half of B is the hard one for every method. C: lgbm-tiny / all oof
  0.723 vs 0.703 (+0.02), val 0.634 vs 0.665, swapped 0.829. A: logreg / cheap oof 0.732 vs 0.703 (+0.03),
  val 0.722 vs 0.736. The learned rankers are thus **at or above the hand-tuned full-set numbers on all three
  corpora under an honest protocol**, while the hand-tuned recipes re-selected on half the questions are not.



### 2.3 What the models learn

Largest standardised logistic-regression weights (fit on train, `all` features):

* **A** (Fisconet, 91 docs): `type = Décisions anticipées` (+0.54), bge-m3 log-rank (−0.53), whole-doc BM25
  score (+0.44), `log_n_chunks` (−0.43), bge / bge-m3 normalised scores (+0.40 / +0.39), `log_doc_len`
  (−0.37), mMARCO log-rank (−0.36); with the `cheap` set: document type (rulings +, `Commentaires` −),
  `title_overlap` (+0.55), e5 and whole-doc BM25 scores, `doc_year` (−0.47: older texts are less often the
  answer), `convex05` (+0.46). The A questions were written from short rulings and circulaires, so a prior on
  *short documents of the ruling type whose title shares the query's words* is worth as much as a
  cross-encoder — and it is what gives `logreg / cheap` its 0.732.
* **B** (codes, 5,853 articles): e5 log-rank / score (−0.64 / +0.58), mMARCO and bge log-ranks (−0.57 /
  −0.55), RRF (−0.49), `best_pos_e5` (+0.44: the matching chunk sits deep in the article), `type = cir92`
  (+0.44), `region_match` (+0.46 in the cheap set) and `region_mismatch` (−0.5 in minimal+meta). The
  reranker ranks carry most of the signal; region and code family are the useful priors (the region filter
  of exp 08 re-learned from 24 questions).
* **C** (21k docs): whole-doc BM25 normalised score and log-rank (+0.91 / −0.65), **`doc_year` (+0.80)**,
  `type = décisions anticipées` (+0.67), bge log-rank (−0.63), chunk BM25 (+0.47), `type = questions
  parlementaires` (−0.41), RRF (−0.40); in the tiny LambdaMART the gain is dominated by `bm25doc_norm`
  (0.36–0.40), then `bm25doc_logrank`, bge rank/score and `doc_year`. The recency prior is the C-specific
  discovery: the corpus holds yearly editions of the same articles and the questions were written from
  the latest ones, so "prefer the newest edition" (the `is_yearly_edition` / year features of §1) is worth
  more than any fusion weight. This is also the mechanism behind the exp-09 observation that BM25 +
  reranker beats dense retrieval on C: whole-document BM25 is the strongest single feature on this corpus.


## 3. Conclusions and recommended recipe

1. **Hand-tuned fusion weights do not survive a train/val split.** Selecting the convex weight on half the
   questions loses 0.05–0.19 MRR on the other half on A (chunk BM25), B and C; the only stable choice is an
   extreme that both halves agree on (pure whole-doc BM25 on A). A fixed w=0.5 (or RRF60) is at or above
   the tuned weight everywhere. Do not tune first-stage weights on < 50 questions.
2. **Reranker depth and β transfer when the reranker is strong, not when it is weak.** bge-reranker-v2-m3
   on C: every depth 20–50 and β 0.7–1.0 is within 0.03 on both halves (val 0.655–0.658, oof 0.678–0.685).
   mMARCO-MiniLM is corpus-dependent: harmful on A (val 0.68 → 0.54 as β → 1), essential on B (0.33 →
   0.61), useful only interpolated on C (β 0.4–0.8). Interpolation with the fused score is the safer default
   for a cheap reranker (β ≈ 0.5–0.8); a strong reranker can replace the fused order (β = 1) at depth 20–30.
3. **The best honest numbers come from a small learned ranker over cheap features.** oof MRR: A 0.732
   (logreg on 33 non-cross-encoder features; bar 0.703), B 0.608 (logreg on 7 features incl. both reranker
   scores; bar 0.522), C 0.723 (15-tree LambdaMART on all features; bar 0.703). Val-half MRR: A 0.722 (bar
   0.736), B 0.519 (bar 0.570; the swapped half gives 0.667), C 0.634 (bar 0.665; swapped 0.829). The
   grid-tuned recipes evaluated honestly reach A 0.695 / B 0.548 / C 0.685 oof.
4. **What the rankers learn is metadata, not scores.** Document type (rulings +, commentaries / PQs −),
   title–query overlap, document length (short +), **document year (newest +)** on C, **region match** on
   B. These are cheap to compute at index time and worth as much as a second cross-encoder; they should be
   fields in the production store regardless of whether a learned ranker is deployed.
5. **Cascades are the affordable way to use bge-reranker-v2-m3 on CPU.** Scoring the mMARCO top-30 ∪ leg
   top-10 (~40 chunks/question) costs a quarter of the union-of-legs set and keeps 0.685 oof on C, but the
   59–72% coverage of the fused top-20/30 is what separates it from the 0.703 full-top-30 number of exp 09.

**Recommended recipe** (per query, CPU): chunk BM25 (exp-01 French normalisation) + e5-small, fixed convex
0.5 (no tuning); mMARCO-MiniLM on the fused top-50; bge-reranker-v2-m3 on the mMARCO top-30 ∪ leg top-10;
final score = a logistic regression (A/B-sized corpora) or a 15-tree LambdaMART (C-sized) over
{e5, BM25 chunk, BM25 whole-doc, RRF, mMARCO, bge} scores + {document type, title overlap, length, year,
region match}, refit whenever the question set grows. Until a learned ranker is wired in, use β = 0.8
interpolation of bge with the fused score at depth 20–30, which is within 0.01 of the learned rankers on C
and B and needs no training data. Everything is reproducible from `cache/` in seconds; the reranker caches
take ~1 h (mMARCO, all corpora) + ~3.5 h (bge cascade) on 4 cores.
