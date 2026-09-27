# 24 — Pooled-label ranker: mined train split + human TRAIN half

Status: complete (cache-only; no reranker pair was scored). 400 runs saved in `experiments/results/24_pooled_ranker/`
(`<slice>__ltr24__<method>__<features>__<pool>__<fit>`), tables in `runs/train24_<c>.md` / `gate_check_<c>.md`,
every number below is in `runs/train24_<c>.json`.

## 1. Setup

Round-3 follow-up of `21_mined_eval` §4–5: the exp-21 ranker trained on mined labels beats bge-as-reranker on the
mined validation split but lands *on*, not above, the round-1 bars on the human sets, because the mined labels
teach "answers are statute articles / verbatim sources". This experiment pools the human **train** half into the
training set, adds the gate features of exps 21/22 (query length, verbatim overlap) and the bge document score as a
feature, and asks whether the human **val** half — the only honest held-out set for citizen questions — moves above
the bars. Run with the exp-14 venv: `cd experiments/14_ltr_fusion && uv run python ../24_pooled_ranker/{features24,train24,gate_check}.py --corpus B|C`.

**Feature table.** The exp-21 table (`21_mined_eval/cache/<c>_features.npz`, same candidates = top-50 docs of every
leg ∪ whole-doc BM25 ∪ exp-13 lexical, minus the `exclude` list; same labels) with the mMARCO and bge columns dropped,
plus `features24.py`:
* **gate features**: `q_len_words`, `q_log_len`; `ov8_max` / `ov3_max` = fraction of the query's word 8-grams /
  3-grams present in the candidate document's best e5 / BM25 / convex chunk (max of the three), `ov8_any`,
  `q_verbatim` = question-level max of `ov8_max` over the candidates ("is this query pasted from a document?");
* **bge features** recomputed from *every* existing cache on the exp-14 chunk universe: the exp-21 cache (own scoring
  + the exp-14 / exp-17 human pairs) and, on B, exp 22's `B_bge22.npz` (same chunk universe, asserted; 1,690 new
  (question, chunk) pairs but **no new question** — exp 22's subsample-100 lies inside exp 21's 150): `bge_max`,
  `bge_norm` (min-max within the question), `bge_logrank`, `bge_missing` (document level), `bge_qcov`
  (question-level share of the convex top-20 that is scored);
* explicit interactions for the linear model: `bge_norm × q_log_len`, `× q_verbatim`, `× ov8_max`.

**Coverage (honest).** Human sets 100 % (B 40, C 64: full convex top-20 scored). Mined B train 68 / 145 and val 82 /
159 fully scored; mined C 106 / 352 and 94 / 345. An unscored question carries `bge_missing = 1` on every candidate
(the model falls back to the first-stage features); the `pooled-scored` pool trains on scored mined questions only.
Words per question: human median B 20 / C 33 (max 28 / 60), mined 78 / 72. `q_verbatim > 0.2`: C mined 280 / 352 train
vs human 0 / 29 (the verbatim feature separates the populations on C); B mined 2 / 145 (nothing to gate on B except length).

**Feature sets.** `withtype` (all, incl. document-type one-hot), `notype` (no `type=*`), `notype-nogate` (no
length / overlap / interaction features), `notype-nobge` (no cross-encoder), `small` (18: six leg scores, title overlap,
doc length, yearly-edition, bge ×4, q_len, ov8, q_verbatim, three interactions).

**Pools and weights.** `mined` = mined train only (145 / 352; the exp-24 replication of the mined-only ranker with
identical features), `pooled` = mined train + human train (B 145 + 24, C 352 + 29), `pooled-scored` = scored mined
train + human train (B 68 + 24, C 106 + 29). Human sample weight w ∈ {1, 5, 10} (and logreg C ∈ {0.03 … 3}) chosen by
5-fold grouped CV inside the training pool (human and mined questions spread separately over folds; criterion = mean
of held-out mined MRR and held-out human-train MRR). The human val half enters no selection; the post-hoc column of
`runs/train24_<c>.md` shows human val under the other weights for transparency only.

**Fits.** A = pool → human val (honest) / mined val (honest); B = mined train + human val → human train; `oof-human` =
A on human val ∪ B on human train (all 40 / 64 honest); C / D = the same with *all* mined questions
(`oof-human-allmined`). Models: LightGBM LambdaMART tiny (3 leaves, 100 trees, 5-seed bag, exp-14 settings) and
standardised L2 logreg. Statistics: `rag_eval.stats` paired t / sign-flip / BCa CI via `common21.paired`.

## 2. Results

### 2.1 Main numbers (MRR; human val = fit A, human all = oof; mined val = fit A)

| corpus | pool | features | method | w_h | human **val** MRR (H@1 / R@10) | human all (oof) | oof, all mined | mined val (scored ∩ val) | mined val per source |
|---|---|---|---|--:|---|--:|--:|---|---|
| B | mined | notype | lgbm-tiny | – | 0.442 (0.312 / 0.562) | 0.483 | – | 0.478 (0.585) | pq 0.29 · ruling 0.70 |
| B | pooled | notype | lgbm-tiny | 5 | 0.497 (0.312 / 0.875) | 0.577 | 0.612 | 0.452 (0.548) | pq 0.27 · ruling 0.68 |
| B | pooled | withtype | lgbm-tiny | 5 | 0.490 (0.312 / 0.875) | 0.588 | 0.591 | 0.454 (0.544) | pq 0.27 · ruling 0.68 |
| B | pooled | notype-nogate | lgbm-tiny | 5 | 0.498 | 0.566 | 0.614 | 0.450 (0.549) | |
| B | pooled | notype-nobge | lgbm-tiny | 1 | 0.305 | 0.401 | 0.420 | 0.467 (0.569) | |
| B | pooled | small | lgbm-tiny | 5 | 0.530 (0.375 / 0.812) | **0.623** | 0.618 | 0.451 (0.541) | pq 0.28 · ruling 0.66 |
| B | pooled | small | logreg C=0.1 | 10 | 0.506 | 0.550 | 0.541 | 0.427 (0.525) | |
| B | pooled-scored | notype | lgbm-tiny | 1 | 0.542 (0.375 / 0.875) | 0.601 | 0.554 | 0.441 (0.550) | pq 0.27 · ruling 0.65 |
| B | pooled-scored | notype-nogate | lgbm-tiny | 5 | **0.576** (0.438 / 0.875) | 0.620 | 0.614 | 0.409 (0.515) | pq 0.25 · ruling 0.60 |
| B | pooled-scored | small | lgbm-tiny | 1 | 0.510 | 0.597 | 0.551 | 0.437 (0.551) | |
| C | mined | notype | lgbm-tiny | – | 0.604 (0.486 / 0.795) | 0.659 | – | **0.759** (0.736) | pq 0.10 · ruling 0.98 · faq 0.99 |
| C | pooled | notype | lgbm-tiny | 5 | 0.644 (0.543 / 0.914) | 0.703 | 0.684 | 0.749 (0.724) | pq 0.10 · ruling 0.97 · faq 0.97 |
| C | pooled | withtype | lgbm-tiny | 10 | 0.647 (0.543 / 0.900) | 0.699 | 0.705 | 0.745 (0.717) | pq 0.11 · ruling 0.96 · faq 0.96 |
| C | pooled | notype-nogate | lgbm-tiny | 5 | 0.644 | 0.707 | 0.698 | 0.729 (0.694) | |
| C | pooled | notype-nobge | lgbm-tiny | 10 | 0.653 | 0.701 | 0.697 | 0.741 (0.719) | |
| C | pooled | small | lgbm-tiny | 5 | 0.647 | 0.694 | 0.665 | 0.748 (0.731) | |
| C | pooled | notype | logreg C=0.03 | 10 | 0.660 | 0.692 | 0.687 | 0.748 (0.735) | |
| C | pooled | small | logreg C=0.03 | 10 | **0.670** (0.571 / 0.852) | 0.682 | 0.684 | 0.745 (0.735) | pq 0.07 · ruling 0.98 · faq 0.96 |
| C | pooled-scored | notype | lgbm-tiny | 5 | 0.667 (0.571 / 0.900) | **0.711** | 0.684 | 0.730 (0.705) | pq 0.09 · ruling 0.95 · faq 0.94 |
| C | pooled-scored | notype-nogate | lgbm-tiny | 5 | 0.654 | 0.710 | 0.698 | 0.723 (0.697) | |

Bars: B val **0.570** / full **0.522** (exp 03, e5 RRF + mMARCO@30); C val **0.665** / full **0.703** (exp 09; 0.696 for the
val-bar run). Other references on the same questions: convex 0.5 → bge@20 (exp 21) B 0.468 val / 0.495 all, C 0.649 /
0.695; exp-22 gate T = 25 B 0.613 val / 0.628 all; exp-21 mined-only ranker `cheap+bge` B 0.396 val / 0.472 all,
C 0.623 / 0.680; exp-17 lex13 → bge@20 C 0.719 all. All 30 configurations per corpus are in `runs/train24_<c>.md`.

### 2.2 Paired tests on the human sets (Δ = exp 24 − reference; val = fit A on the val half, all = oof)

| corpus | exp-24 run | reference | split | n | Δ MRR [95 % CI] | p_t | W/L/T |
|---|---|---|---|--:|:--|--:|:--|
| B | lgbm notype-nogate pooled-scored | round-1 bar (0.570) | val | 16 | +0.005 [−0.180, +0.219] | 0.96 | 4/3/9 |
| B | lgbm notype pooled-scored | bar | val | 16 | −0.029 [−0.219, +0.199] | 0.80 | 4/5/7 |
| B | lgbm small pooled | bar | val | 16 | −0.040 [−0.248, +0.199] | 0.74 | 5/6/5 |
| B | lgbm notype pooled | bar | val | 16 | −0.073 [−0.271, +0.161] | 0.52 | 3/6/7 |
| B | lgbm notype-nogate pooled-scored | bar (0.522) | all | 40 | +0.098 [−0.000, +0.199] | 0.066 | 17/4/19 |
| B | lgbm small pooled | bar | all | 40 | +0.101 [−0.015, +0.220] | 0.11 | 17/9/14 |
| B | lgbm notype pooled-scored | bar | all | 40 | +0.079 [−0.022, +0.181] | 0.15 | 18/6/16 |
| B | lgbm notype pooled | bar | all | 40 | +0.055 [−0.050, +0.167] | 0.34 | 15/9/16 |
| B | lgbm notype pooled (all-mined oof, 0.612) | bar | all | 40 | +0.090 [−0.022, +0.202] | 0.13 | 16/7/17 |
| B | lgbm small pooled | convex05 → bge@20 (0.495) | all | 40 | **+0.128** [+0.041, +0.240] | **0.015** | 17/6/17 |
| B | lgbm notype pooled-scored | convex05 → bge@20 | all | 40 | **+0.105** [+0.040, +0.197] | **0.011** | 14/5/21 |
| B | lgbm notype-nogate pooled-scored | convex05 → bge@20 | all | 40 | **+0.125** [+0.034, +0.240] | **0.023** | 17/6/17 |
| B | lgbm notype-nogate pooled-scored | convex05 → bge@20 (0.468) | val | 16 | +0.108 [−0.020, +0.302] | 0.21 | 5/4/7 |
| B | lgbm small pooled | exp-21 mined-only ranker (0.472) | all | 40 | **+0.150** [+0.071, +0.256] | **0.003** | 17/6/17 |
| B | lgbm notype pooled-scored | exp-21 ranker | all | 40 | **+0.128** [+0.031, +0.232] | **0.018** | 17/6/17 |
| B | lgbm notype pooled | exp-21 ranker | all | 40 | +0.105 [+0.011, +0.211] | 0.051 | 18/7/15 |
| B | lgbm small pooled | exp-24 mined-only, same features (0.477) | all | 40 | **+0.145** [+0.063, +0.249] | **0.004** | 21/2/17 |
| B | lgbm notype pooled-scored | exp-24 mined-only (0.483) | all | 40 | **+0.117** [+0.005, +0.224] | **0.048** | 19/5/16 |
| B | lgbm small pooled | exp-22 gate T25 (0.628) | all | 40 | −0.006 [−0.115, +0.102] | 0.92 | 10/15/15 |
| B | lgbm notype-nogate pooled-scored | exp-22 gate | all | 40 | −0.009 [−0.093, +0.084] | 0.85 | 8/13/19 |
| B | lgbm notype-nogate pooled-scored | exp-22 gate (0.613) | val | 16 | −0.037 [−0.169, +0.171] | 0.67 | 2/7/7 |
| B | lgbm notype pooled | exp-22 gate | val | 16 | −0.116 [−0.262, +0.110] | 0.24 | 2/10/4 |
| C | lgbm notype pooled-scored | round-1 bar (0.665) | val | 35 | +0.002 [−0.097, +0.077] | 0.96 | 9/6/20 |
| C | logreg small pooled | bar | val | 35 | +0.005 [−0.064, +0.095] | 0.90 | 6/8/21 |
| C | lgbm notype pooled | bar | val | 35 | −0.021 [−0.109, +0.047] | 0.60 | 7/9/19 |
| C | lgbm withtype pooled | bar | val | 35 | −0.018 [−0.111, +0.051] | 0.67 | 9/8/18 |
| C | lgbm notype pooled-scored | bar (0.696) | all | 64 | +0.014 [−0.051, +0.069] | 0.64 | 16/10/38 |
| C | lgbm notype pooled | bar | all | 64 | +0.006 [−0.056, +0.056] | 0.83 | 14/12/38 |
| C | lgbm notype pooled-scored | convex05 → bge@20 (0.695) | all | 64 | +0.016 [−0.049, +0.070] | 0.60 | 16/10/38 |
| C | lgbm notype pooled-scored | exp-17 lex13 → bge@20 (0.719) | all | 64 | −0.008 [−0.084, +0.054] | 0.81 | 16/10/38 |
| C | lgbm notype pooled-scored | exp-21 mined-only ranker (0.680) | all | 64 | +0.031 [−0.034, +0.091] | 0.34 | 19/7/38 |
| C | lgbm notype pooled-scored | exp-21 ranker (0.623) | val | 35 | +0.044 [−0.058, +0.138] | 0.39 | 12/5/18 |
| C | lgbm withtype pooled | exp-24 mined-only, same features (0.638) | all | 64 | **+0.061** [+0.015, +0.115] | **0.019** | 22/7/35 |
| C | lgbm withtype pooled | exp-24 mined-only (0.583) | val | 35 | **+0.064** [+0.019, +0.129] | **0.028** | 13/5/17 |
| C | lgbm notype pooled | exp-24 mined-only (0.659) | all | 64 | +0.043 [+0.007, +0.095] | 0.053 | 19/5/40 |
| C | logreg small pooled | exp-24 mined-only logreg (0.566) | all | 64 | **+0.117** [+0.054, +0.197] | **0.002** | 27/5/32 |

### 2.3 Paired tests on the mined val split (fit A; n = 159 / 345, scored ∩ val 82 / 94)

| corpus | exp-24 run | reference | n | Δ MRR [95 % CI] | p_t | W/L/T |
|---|---|---|--:|:--|--:|:--|
| B | lgbm notype pooled | convex 0.5 (0.401) | 159 | **+0.051** [+0.017, +0.089] | 0.006 | 51/27/81 |
| B | lgbm notype pooled | exp-24 mined-only, same features (0.478) | 159 | **−0.026** [−0.051, −0.004] | 0.036 | 18/47/94 |
| B | lgbm notype pooled | exp-21 mined-only `cheap+bge` (0.550) | 82 | −0.002 [−0.033, +0.029] | 0.91 | 15/13/54 |
| B | lgbm notype pooled | convex 0.5 → bge@20 (sub ∩ val, 0.512) | 82 | +0.036 [−0.007, +0.086] | 0.13 | 24/13/45 |
| B | lgbm notype-nogate pooled-scored | exp-24 mined-only | 159 | **−0.071** [−0.113, −0.033] | 0.001 | 21/58/80 |
| B | lgbm notype mined (exp-24) | exp-21 `cheap+bge` | 82 | +0.035 [−0.002, +0.081] | 0.10 | 22/8/52 |
| C | lgbm notype mined (exp-24) | convex 0.5 (0.703) | 345 | **+0.055** [+0.036, +0.078] | < 0.001 | 44/9/292 |
| C | lgbm notype mined (exp-24) | exp-21 `cheap+bge` (0.708) | 94 | **+0.029** [+0.010, +0.064] | 0.025 | 8/3/83 |
| C | lgbm notype pooled | convex 0.5 | 345 | **+0.046** [+0.029, +0.066] | < 0.001 | 44/8/293 |
| C | lgbm notype pooled | exp-24 mined-only (0.759) | 345 | −0.010 [−0.022, +0.001] | 0.11 | 6/21/318 |
| C | lgbm withtype pooled | exp-24 mined-only (0.769) | 345 | **−0.024** [−0.041, −0.010] | 0.003 | 3/29/313 |
| C | lgbm notype pooled-scored | exp-24 mined-only | 345 | **−0.029** [−0.046, −0.015] | < 0.001 | 6/32/307 |
| C | lgbm small pooled | exp-21 `cheap+bge` | 94 | **+0.023** [+0.006, +0.053] | 0.046 | 8/5/81 |

### 2.4 Feature importances (LightGBM gain share; logreg standardised coefficients) — fit A

| corpus | model | top features |
|---|---|---|
| B | lgbm notype **mined** | lex13_logrank 0.24, lex13_norm 0.18, title_overlap_n 0.10, rrf60_logrank 0.08, log_doc_len 0.07, … bge_norm **0.03** |
| B | lgbm notype **pooled** | bge_logrank 0.17, e5_norm 0.16, lex13_norm 0.12, bge_norm 0.11, e5_logrank 0.10, lex13_logrank 0.08, rrf60_logrank 0.06, bge_norm×loglen 0.05 |
| B | lgbm notype pooled-scored | bge_logrank 0.30, bge_norm 0.19, bge_norm×loglen 0.15, e5_logrank 0.10, bge_max 0.07, log_doc_len 0.04 |
| B | lgbm small pooled | e5_norm 0.26, bge_norm 0.21, lex13_norm 0.20, bge_norm×loglen 0.16, bge_max 0.05, convex05 0.04 |
| B | lgbm withtype pooled | as notype; first `type=` feature (`arcir92`) at 0.013 |
| B | logreg small pooled | convex05 +0.78, bm25_norm −0.73, lex13_norm +0.53, bge_norm +0.36, bge_max −0.26, q_len +0.22 (question-constant), e5_norm +0.20 |
| C | lgbm notype **mined** | lex13_norm 0.33, **ov8_max 0.19**, convex05_logrank 0.11, ov3_max 0.10, title_overlap 0.06, title_overlap_n 0.06 |
| C | lgbm notype **pooled** | lex13_norm 0.41, convex05_logrank 0.17, bm25doc_logrank 0.11, title_overlap_n 0.08, lex13_logrank 0.07, bm25doc_norm 0.07 (bge features ≤ 0.02) |
| C | lgbm notype pooled-scored | lex13_norm 0.25, bm25doc_logrank 0.22, bm25doc_norm 0.15, bge_norm 0.12, convex05_logrank 0.06, doc_year 0.02 |
| C | lgbm withtype pooled | lex13_norm 0.33, convex05_logrank 0.16, bm25doc_logrank 0.14, bm25doc_norm 0.10, … `type=code_et_legislation` 0.016 |
| C | logreg small pooled | ov8_max +0.75, **bge_norm +0.62, bge_norm×q_verbatim −0.53**, e5_norm +0.43, is_yearly_edition +0.41, bm25doc_norm +0.37, title_overlap +0.31 |
| C | logreg notype pooled | title_overlap_n +0.89, ov8_max +0.76, convex05/bm25doc/e5/lex13 logranks −0.45 to −0.49, is_yearly_edition +0.44, bge_norm +0.40 |

(Question-constant features — `q_len_words`, `q_verbatim`, `bge_qcov` — cannot change a linear within-question ranking;
only their interactions can. Their logreg coefficients are listed for completeness only.)

### 2.5 Did the model learn the length gate?  (a) tree-SHAP contribution of the bge features per query-length bin

`pred_contrib` of the 5-seed bag summed over all `bge*` columns (incl. the interactions), scored questions of the human
sets + mined val; "slope" = OLS slope of that contribution on `bge_norm` inside the bin; PD range = mean prediction at
`bge_norm` = 1 minus at 0, other features fixed.

| corpus | model | words | n rows (q) | share of abs. contribution | slope on bge_norm | Spearman | PD range |
|---|---|---|--:|--:|--:|--:|--:|
| B | lgbm notype pooled | 0–25 | 825 (37) | 0.31 | +1.52 | +0.84 | +0.76 |
| B | same | 26–50 | 446 (19) | 0.29 | +1.59 | +0.81 | +0.69 |
| B | same | 51–100 | 822 (40) | 0.33 | +1.53 | +0.86 | +0.69 |
| B | same | > 100 | 577 (26) | 0.30 | +1.56 | +0.88 | +0.68 |
| B | lgbm notype pooled-scored | 0–25 / 26–50 / 51–100 / > 100 | | 0.49 / 0.46 / 0.52 / 0.51 | +1.99 / +2.20 / +1.99 / +1.98 | +0.90 | +0.92 / +0.91 / +0.94 / +0.94 |
| C | lgbm notype pooled | 0–25 | 151 (16) | 0.04 | +0.28 | +0.89 | +0.33 |
| C | same | 26–50 | 849 (75) | 0.05 | +0.30 | +0.91 | +0.35 |
| C | same | 51–100 | 792 (46) | 0.07 | +0.29 | +0.88 | +0.35 |
| C | same | > 100 | 341 (21) | 0.07 | +0.31 | +0.91 | +0.35 |
| C | lgbm withtype pooled | 0–25 … > 100 | | 0.06 / 0.07 / 0.10 / 0.10 | +0.47 / +0.49 / +0.48 / +0.51 | +0.93 | +0.57 / +0.58 / +0.59 / +0.57 |
| C | lgbm notype pooled-scored | 0–25 … > 100 | | 0.13 / 0.13 / 0.16 / 0.16 | +0.91 / +0.90 / +0.84 / +0.87 | +0.93 | +0.90 / +0.91 / +0.91 / +0.91 |

**No tree learned a length-dependent use of the cross-encoder**: slope, share and PD range are flat across the bins on
both corpora (the `bge_norm × q_log_len` interaction gets 0.05–0.16 of the gain on B but is used as a monotone
rescaling, not as a switch). What differs between corpora is the *level*: on B the pooled trees give bge 30–50 % of
the total contribution (the mined-only tree gave it 3 %), on C 4–16 %. The linear model on C is the one that learned
the gate explicitly: `bge_norm +0.62` with `bge_norm × q_verbatim −0.53` — trust the cross-encoder unless the query
is pasted from a document — and it has the highest human-val number on C (0.670).

### 2.6 (b) … and in outcome terms (`runs/gate_check_<c>.md`; Δ vs convex 0.5 / vs convex 0.5 → bge@20)

| corpus | slice | n | convex05 | → bge@20 | lgbm notype pooled | lgbm notype pooled-scored | lgbm notype mined | logreg notype pooled |
|---|---|--:|--:|--:|---|---|---|---|
| B | human val (all ≤ 25 words) | 16 | 0.319 | 0.468 | 0.497 (+0.18 / +0.03) | 0.542 (+0.22 / +0.07) | 0.442 (+0.12 / −0.03) | 0.423 (+0.10 / −0.05) |
| B | human oof, ≤ 25 words | 35 | 0.385 | 0.498 | 0.594 (+0.21 / +0.10) | 0.619 (+0.23 / +0.12) | 0.501 (+0.12 / +0.00) | 0.531 (+0.15 / +0.03) |
| B | human oof, > 25 words | 5 | 0.464 | 0.475 | 0.459 (−0.01 / −0.02) | 0.471 (+0.01 / −0.00) | 0.361 (−0.10 / −0.11) | 0.475 (+0.01 / +0.00) |
| B | mined val ∩ scored, 26–50 words | 14 | 0.259 | 0.342 | 0.326 (+0.07 / −0.02) | 0.349 (+0.09 / +0.01) | 0.315 (+0.06 / −0.03) | 0.327 (+0.07 / −0.02) |
| B | mined val ∩ scored, > 50 words | 66 | 0.558 | 0.563 | 0.610 (+0.05 / +0.05) | 0.607 (+0.05 / +0.04) | 0.660 (+0.10 / +0.10) | 0.588 (+0.03 / +0.03) |
| C | human val, ≤ 25 words | 4 | 0.636 | 0.561 | 0.648 | 0.646 | 0.638 | 0.625 |
| C | human val, > 25 words | 31 | 0.584 | 0.660 | 0.643 (+0.06 / −0.02) | 0.670 (+0.09 / +0.01) | 0.600 (+0.02 / −0.06) | 0.665 (+0.08 / +0.01) |
| C | human oof, > 25 words | 59 | 0.625 | 0.699 | 0.701 (+0.08 / +0.00) | 0.710 (+0.09 / +0.01) | 0.655 (+0.03 / −0.04) | 0.692 (+0.07 / −0.01) |
| C | mined val ∩ scored, 26–50 words | 19 | 0.602 | 0.645 | 0.695 (+0.09 / +0.05) | 0.666 (+0.06 / +0.02) | 0.686 (+0.08 / +0.04) | 0.693 (+0.09 / +0.05) |
| C | mined val ∩ scored, > 50 words | 64 | 0.635 | **0.431** | 0.685 (+0.05 / **+0.25**) | 0.666 (+0.03 / +0.24) | 0.706 (+0.07 / +0.28) | 0.702 (+0.07 / +0.27) |
| C | mined val ∩ scored, verbatim > 0.2 | 72 | 0.845 | 0.675 | 0.904 (+0.06 / +0.23) | 0.886 (+0.04 / +0.21) | 0.912 (+0.07 / +0.24) | 0.925 (+0.08 / +0.25) |
| C | mined val ∩ scored, verbatim ≤ 0.2 (PQ → statute) | 22 | 0.101 | 0.101 | 0.133 | 0.114 | 0.160 | 0.114 |

So the pooled models *behave* like the gate without having learned a switch: on the long / verbatim C questions where
bge-as-reranker collapses (0.635 → 0.431) they stay +0.03 to +0.07 above the first stage, and on the short human
questions they match or beat bge-as-reranker. They do it by keeping the first-stage evidence next to a modestly
weighted bge score — the exp-21 §5 mechanism — not by a learned length interaction. On B there is nothing to gate for
bge (it is +0.005 on long mined questions); the exp-22 gate is about mMARCO, which is not in this feature set.

## 3. Reading

1. **Pooling the human train half does move the rankers, and it is the human labels, not the features, that do it.**
   With identical features, pooled vs mined-only on the human sets: B +0.04 to +0.15 (oof; `small` +0.145
   [+0.063, +0.249], 21 / 2 / 17, p 0.004; `notype pooled-scored` +0.117, p 0.048), C +0.035 to +0.06 (`withtype`
   +0.061, p 0.019 on all 64 and +0.064, p 0.028 on the val half; `notype` +0.043, p 0.053). Against exp 21's
   mined-only `cheap+bge` ranker: B +0.10 to +0.15 (p 0.003–0.05), C +0.02 to +0.04 (n.s.). The exp-21 gap
   *below* the bars is gone on both corpora (B 0.427 → 0.58–0.62 all, C 0.680 → 0.69–0.71 all).
2. **But nothing is above the bars at p < 0.05, and on the human val half nothing is above them at all.** Best val
   numbers: B 0.576 vs 0.570 (+0.005, 4 / 3 / 9, p 0.96; `notype-nogate pooled-scored`), C 0.667 vs 0.665 (+0.002,
   9 / 6 / 20, p 0.96; `notype pooled-scored`) and 0.670 (logreg `small`, +0.005). The other pooled configurations
   are −0.02 to −0.07 on val. On the full sets the B rankers are directionally above the bar in every pooled tree
   configuration (0.55–0.62 vs 0.522; best +0.098 [−0.000, +0.199], 17 / 4 / 19, p 0.066) while C is level
   (+0.001 to +0.014). "Directionally on both corpora" therefore holds only on the full-set oof, and only at
   +0.01 on C; on the val halves the answer is a tie on both. The B val half has 16 questions (minimum detectable
   Δ ≈ 0.2) and the B numbers are also the least stable ones: the nested CV picks w = 5 while w = 10 would have
   been 0.03–0.06 better on val for four of the ten B pooled trees (post-hoc column) — that is selection noise at
   n = 24, not a result.
3. **What the pooled ranker does beat at p < 0.05 on the human sets is bge-as-reranker on B** (`convex 0.5 → bge@20`
   0.495 → 0.60–0.62 all: +0.105 [+0.040, +0.197], p 0.011; +0.128, p 0.015; +0.125, p 0.023) — the first B ranker
   with a p-value against the reranked recipe — and the round-1 bar's mMARCO pipeline is behind it by 0.05–0.10
   (p 0.07–0.34). On C it ties bge-as-reranker (+0.016) and exp 17's lexical → bge@20 (−0.008).
4. **It ties, and does not beat, exp 22's length-gated B pipeline**: −0.006 to −0.009 on all 40 (p 0.85–0.92) and
   −0.04 to −0.12 on the val half (2 / 7–10 wins / losses). The gate is still the best corpus-B system on the val
   half; the pooled ranker is the best B system that uses bge only (no mMARCO, no reception field) and it does so as
   one model with no threshold.
5. **Cost on the mined side.** Pooling is −0.02 to −0.04 MRR on the mined val split (B `notype pooled` −0.026
   [−0.051, −0.004], p 0.036; C `pooled-scored` −0.029, p < 0.001) and the `pooled-scored` trees, trained on 68 / 106
   mined questions, lose the most (B `notype-nogate pooled-scored` −0.071, p 0.001). Every pooled tree still beats
   the first stage on mined val at p ≤ 0.006 (B +0.05, C +0.03–0.05). A production ranker faces a trade: the
   human-weighted tree gives up 0.02–0.03 on statute / ruling lookups for +0.05–0.15 on citizen questions.
6. **Mechanism of the transfer, per corpus.** On B the mined labels never taught the tree to use bge (gain share 0.03:
   bge is only +0.04 on mined B); 24 human questions with weight 5 raise it to 0.28–0.49 and the human numbers
   follow — without the bge feature pooling does nothing (`notype-nobge pooled` 0.30 val / 0.40 all, below the
   mined-only tree). On C bge stays marginal (0.02–0.16) and the gain comes from re-weighting the lexical features
   (`bm25doc_logrank` 0.11–0.22, `lex13_norm` down from 0.41 to 0.25 in `pooled-scored`); the no-bge pooled tree is
   as good as the bge one (0.653 / 0.701). So exp 21's "bge is the quality ceiling on paraphrased questions" holds on
   B, while on C the ceiling is the lexical evidence and the human labels only tune its weighting.
7. **The document-type prior does not matter for the trees once the human half is pooled** (`withtype` vs `notype`:
   B 0.490 vs 0.497 val / 0.588 vs 0.577 all; C 0.647 vs 0.644 / 0.699 vs 0.703; `type=` features ≤ 0.016 of the
   gain). It still hurts the linear model on C (`withtype` logreg 0.581 val vs `notype` 0.660): with 29 human
   questions against 352 mined ones the pooled logreg keeps a `code_et_legislation` prior, so the exp-21 advice
   "keep the type prior out of the linear ranker" stands even with pooled labels.
8. **The gate features are not what carries the transfer.** `notype-nogate` ≈ `notype` on the human sets (B 0.498 /
   0.566 vs 0.497 / 0.577; C 0.644 / 0.707 vs 0.644 / 0.703) and the trees use bge uniformly over query length
   (§2.5). The verbatim feature is instead a *mined-set* feature: `ov8_max` is the second feature of the C mined-only
   tree (0.19) and lifts mined val to 0.759 (exp 21's `cheap` tree: 0.743; +0.029 over its `cheap+bge` tree on the
   scored questions, p 0.025). The linear C model uses `bge_norm × q_verbatim` as an explicit gate (§2.4) and is
   the best val number on C, but its full-set oof (0.682) is below the trees.

## 4. Verdict

* **Does pooling the human train half fix the domain shift?** It removes the exp-21 deficit: the pooled trees are
  +0.04 to +0.15 over the same ranker trained on mined labels only (p 0.004–0.5 on B, 0.02–0.1 on C) and land on
  the bars on both corpora instead of below them. It does not fix it for free: −0.02 to −0.03 on mined val, and the
  linear model still needs the type prior removed.
* **Is there now a ranker above the bars on the human val half at p < 0.05?** No. Best val: B 0.576 vs 0.570, C
  0.667–0.670 vs 0.665 — ties. **Directionally on both corpora?** Only on the full-set oof (B +0.05 to +0.10, C
  +0.00 to +0.014), i.e. yes on B, level on C. The one p < 0.05 human-set result is B vs bge-as-reranker (+0.11 to
  +0.13). Exp 22's gated pipeline remains the reference on B (tie on 40, ahead on the val 16).
* Recommendation for the stack: train the LightGBM-tiny ranker on pooled labels with the human questions weighted
  ×5, without the type one-hot, with the bge document score (B) — expect bar-level citizen-question quality plus the
  mined-set gain, minus 0.02–0.03 on verbatim lookups. The lever that is still missing is more citizen-style labels:
  24 / 29 questions move the tree from below the bar to the bar; a few hundred (idea 80, pooled judging) is what an
  above-the-bar result at p < 0.05 would need, since the human val halves cannot decide a Δ below ≈ 0.10–0.20.

## 5. Files

```
24_pooled_ranker/
  features24.py   exp-21 table + gate features + bge from every cache (no scoring)   → cache/<c>_extra.{npz,json}
  train24.py      pools × weights (nested CV) × feature sets × {lgbm-tiny, logreg}; fits A–D, oof; paired tests;
                  importances; tree-SHAP gate diagnostics                           → runs/train24_<c>.{json,md}, results/24_pooled_ranker/
  gate_check.py   outcome-level gate check on the saved runs (length / verbatim slices) → runs/gate_check_<c>.{md,json}
  summarize.py    compact console digest of runs/train24_<c>.json
  logs/           features_C.log, train_B.log (511 s), train_C.log (1,083 s)
```
