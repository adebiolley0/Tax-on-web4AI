## 4. Part 3 — learned ranker on real labels

Full tables: `runs/part3_<corpus>.md` (unweighted) and `runs/part3_<corpus>__bal.md` (training questions weighted
by 1 / n(source) so the verbatim slices do not dominate; the two differ by ≤ 0.01 everywhere, so the balanced
runs are quoted). Candidate recall of the expected document in the ranker's candidate set: B human 0.975 /
mined 0.849, C human 0.984 / mined 0.839 — the ceiling of every row. Every logreg was "stable" by the rule
(half-fit val-MRR sd 0.001–0.014 ≤ 0.02), so LightGBM tiny was run for every feature set; coefficient sign
agreement across half-fits was only 0.55–0.67 for the `cheap` set (49 / 56 collinear features) and 0.78–1.00
for the small sets.

### 4.1 Numbers (MRR; fit on mined train, 145 / 352 questions)

| corpus | features | method | mined **val** | val per source | train resub | swapped fold (val → train) | oof mined | **human all** (H@1 / R@10) | human val | fit on all mined → human |
|---|---|---|--:|---|--:|--:|--:|---|--:|--:|
| B | cheap (49) | logreg C=3 | 0.444 | pq 0.262 · ruling 0.668 | 0.450 | 0.442 | 0.443 | 0.332 (0.200 / 0.500) | 0.315 | 0.352 |
| B | cheap | **lgbm-tiny** | **0.487** | pq 0.301 · ruling 0.716 | 0.483 | 0.426 | 0.458 | **0.427** (0.325 / 0.625) | 0.371 | 0.411 |
| B | minimal+meta (13) | logreg C=0.1 | 0.445 | pq 0.282 · ruling 0.646 | 0.414 | 0.429 | 0.437 | 0.395 (0.250 / 0.650) | 0.346 | 0.406 |
| B | minimal+meta | lgbm-tiny | 0.471 | pq 0.299 · ruling 0.683 | 0.473 | 0.412 | 0.443 | 0.404 (0.275 / 0.650) | 0.345 | 0.398 |
| B | legs-only (6) | logreg C=0.3 | 0.426 | pq 0.262 · ruling 0.628 | 0.389 | 0.410 | 0.418 | 0.430 (0.325 / 0.650) | 0.365 | 0.416 |
| B | legs-only | lgbm-tiny | 0.456 | pq 0.283 · ruling 0.669 | 0.436 | 0.390 | 0.425 | 0.416 (0.300 / 0.650) | 0.361 | 0.410 |
| C | cheap (56) | logreg C=1 | 0.720 | pq 0.140 · ruling 0.901 · faq 0.947 | 0.762 | 0.755 | 0.738 | 0.440 (0.359 / 0.594) | 0.418 | 0.474 |
| C | cheap | **lgbm-tiny** | **0.743** | pq 0.159 · ruling 0.934 · faq 0.950 | 0.802 | 0.789 | 0.766 | **0.671** (0.594 / 0.859) | 0.609 | 0.676 |
| C | minimal+meta (13) | logreg C=0.03 | 0.682 | pq 0.066 · ruling 0.873 · faq 0.923 | 0.735 | 0.731 | 0.706 | 0.578 (0.438 / 0.844) | 0.550 | 0.588 |
| C | minimal+meta | lgbm-tiny | 0.725 | pq 0.100 · ruling 0.932 · faq 0.945 | 0.796 | 0.780 | 0.753 | 0.674 (0.578 / 0.818) | 0.614 | 0.666 |
| C | legs-only (6) | logreg C=0.03 | 0.691 | pq 0.047 · ruling 0.892 · faq 0.941 | 0.733 | 0.731 | 0.711 | 0.552 (0.391 / 0.859) | 0.552 | 0.552 |
| C | legs-only | lgbm-tiny | 0.717 | pq 0.049 · ruling 0.934 · faq 0.957 | 0.772 | 0.753 | 0.735 | 0.652 (0.562 / 0.812) | 0.570 | 0.668 |

Reference rows on the same questions: first stages (Part 1) B mined val convex05 0.401 / exp13_lex 0.428, human
convex05 0.395 / exp13_lex 0.391; C mined val convex05 0.703 / exp13_lex 0.708, human convex05 0.622 /
exp13_lex 0.683. Round-1 bars on the human sets: B 0.522 all / 0.570 val, C 0.696 all / 0.665 val (0.703 full-set
best). Exp-14 oof on the human sets: B logreg-7 0.608, C lgbm-tiny-all 0.723 (both use mMARCO + bge features),
exp-14 logreg-cheap oof B 0.491, C 0.603.

### 4.2 Paired tests (Δ = LTR lgbm-tiny `cheap` − reference)

**Mined val split** (the first honest positive results of the project at n = 159 / 345):

| corpus | reference | slice | n | Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 |
|---|---|---|--:|:--|--:|--:|:--|--:|
| B | convex05 | pooled | 159 | **+0.086** [+0.054, +0.126] | 0.000 | 0.000 | 53/25/81 | +0.107 |
| B | convex05 | pq | 86 | **+0.054** [+0.015, +0.102] | 0.016 | 0.014 | 28/17/41 | +0.058 |
| B | convex05 | ruling | 72 | **+0.125** [+0.074, +0.195] | 0.000 | 0.000 | 25/8/39 | +0.167 |
| B | exp13_lex | pooled | 159 | **+0.059** [+0.024, +0.095] | 0.002 | 0.001 | 52/22/85 | +0.088 |
| B | bm25_tok01 | pooled | 159 | **+0.110** [+0.072, +0.154] | 0.000 | 0.000 | 70/11/78 | +0.132 |
| C | convex05 | pooled | 345 | **+0.039** [+0.021, +0.061] | 0.000 | 0.000 | 40/11/294 | +0.032 |
| C | convex05 | pq (diagnostic) | 87 | **+0.114** [+0.070, +0.180] | 0.000 | 0.000 | 22/2/63 | +0.081 |
| C | convex05 | ruling | 174 | **+0.025** [+0.003, +0.052] | 0.049 | 0.046 | 16/6/152 | +0.029 |
| C | convex05 | faq | 84 | −0.009 [−0.047, +0.010] | 0.526 | 0.625 | 2/3/79 | −0.012 |
| C | exp13_lex | pooled | 345 | **+0.034** [+0.018, +0.054] | 0.000 | 0.000 | 36/7/302 | +0.026 |
| C | exp13_lex | pq | 87 | **+0.109** [+0.067, +0.173] | 0.000 | 0.000 | 23/1/63 | +0.081 |

The logreg rows are smaller but same-signed (B pooled +0.043 vs convex05, p = 0.02; C pooled +0.017, p = 0.07,
C pq +0.095, p < 0.001).

**Human sets** (true held-out; nothing here entered a fit):

| corpus | reference (MRR) | split | n | Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 |
|---|---|---|--:|:--|--:|--:|:--|--:|
| B | round-1 bar e5 RRF + mMARCO@30 (0.522) | all | 40 | −0.095 [−0.225, +0.037] | 0.169 | 0.168 | 11/18/11 | −0.025 |
| B | same bar (0.570) | val | 16 | −0.200 [−0.432, +0.011] | 0.112 | 0.118 | 3/8/5 | −0.188 |
| B | exp-14 logreg-7 oof (0.608; mMARCO + bge features) | all | 40 | **−0.180** [−0.312, −0.053] | 0.011 | 0.010 | 8/19/13 | −0.150 |
| B | exp-14 logreg-cheap oof (0.491) | all | 40 | −0.064 [−0.163, +0.028] | 0.208 | 0.211 | 7/18/15 | −0.050 |
| B | convex05 (0.395) | all | 40 | +0.033 [−0.071, +0.135] | 0.538 | 0.544 | 17/13/10 | +0.075 |
| B | exp13_lex (0.391) | all | 40 | +0.036 [−0.038, +0.128] | 0.402 | 0.404 | 19/8/13 | +0.025 |
| C | round-1 bar BM25 + bge@30 (0.696) | all | 64 | −0.025 [−0.100, +0.039] | 0.466 | 0.466 | 12/15/37 | +0.000 |
| C | same bar (0.665) | val | 35 | −0.056 [−0.150, +0.018] | 0.209 | 0.220 | 6/10/19 | −0.029 |
| C | exp-14 lgbm-tiny-all oof (0.723; mMARCO + bge features) | all | 64 | −0.052 [−0.120, +0.008] | 0.120 | 0.121 | 8/18/38 | −0.062 |
| C | exp-14 logreg-cheap oof (0.603) | all | 64 | **+0.068** [+0.016, +0.138] | 0.036 | 0.037 | 19/12/33 | +0.109 |
| C | exp-17 lex13 → bge@20 (0.719) | all | 64 | −0.048 [−0.126, +0.018] | 0.183 | 0.186 | 9/15/40 | −0.031 |
| C | convex05 (0.622) | all | 64 | +0.049 [+0.004, +0.107] | 0.068 | 0.064 | 16/13/35 | +0.094 |
| C | exp13_lex (0.683) | all | 64 | −0.012 [−0.052, +0.032] | 0.568 | 0.576 | 6/14/44 | +0.000 |

### 4.3 Reading

1. **On the mined val split the learned ranker is the first system in this project to beat its first stage at
   p < 0.001**: B +0.086 over convex 0.5 (53 / 25 / 81) and +0.059 over exp-13 lexical; C +0.039 over convex 0.5
   (40 / 11 / 294) and +0.034 over exp-13 lexical. It is also reproducible across folds (swapped fold and oof
   within 0.03 of the val number; half-fit sd ≤ 0.014), which the 16 / 35-question val halves of round 2 never
   were. Where the gain sits matters: on B it is +0.125 on rulings and +0.054 on PQs; on C it is +0.114 on the
   PQ → statute diagnostic (the ranker learns that the labelled answer is a `code_et_legislation` article and
   pushes articles above the PQs / circulars that lexical systems return first), +0.025 on rulings and nothing
   on FAQ headings (79 of 84 ties).
2. **It does not transfer to the human sets as a gain over the round-1 bars**: B −0.095 (11 / 18 / 11) against
   the reranked bar, C −0.025 (12 / 15 / 37) — both undecidable at n = 40 / 64, both negative, and the ranker has
   no cross-encoder while the bars do. Against the un-reranked fusion it is +0.033 on B (p = 0.54) and +0.049
   on C (16 / 13 / 35, p = 0.07): the same "learned ranker ≈ +0.03–0.05 over its first stage" size that exp 14
   measured, now with real labels and a truly held-out test, and still not significant on 64 questions.
3. **The exp-14 oof numbers (B 0.608, C 0.723) are not reproduced by a mined-trained ranker** (−0.180 on B,
   p = 0.01; −0.052 on C, p = 0.12). Two reasons, in order: exp-14's best oof models used mMARCO / bge scores
   as features (the `cheap` variant of exp 14 is at 0.491 / 0.603, and the mined-trained ranker is −0.064 / **+0.068**
   against it — a wash on B, a win on C), and exp 14 fitted on the human questions' own other half, i.e. on the
   same question style and label scheme it was scored on. Section 5 adds the reranker-feature variants on the
   questions Part 2 scored.
4. **Label-domain shift is the main obstacle, and it is visible in the coefficients.** The C logreg on all 56
   features learns `type=code_et_legislation +1.7`, `type=questions_parlementaires −1.5`, `convex05 +3.1`, and
   scores 0.72 on mined val but **0.44 on the human set** (−0.165 vs its own first stage, p = 0.002): the mined
   labels are statute articles, rulings and FAQ documents, the human labels are mostly circulars, FAQs and
   commentaries. Trees are less exposed because their first split is `lex13_norm` (gain share 0.43–0.62) with
   `title_overlap` and `bm25doc_norm` next, which transfer. Re-weighting sources (`--balance`) changes nothing
   (≤ 0.01), so the shift is in *which documents are labelled*, not in the source mix. Any production ranker
   trained on mined labels needs a document-type prior that is not learned from the mined set — or human /
   pooled labels for the types the mined set never labels (idea 80).
5. **LightGBM tiny beats logreg on every held-out number** (mined val +0.02–0.04, human +0.03–0.23) with 145–352
   training questions; the exp-14 warning "LightGBM overfits on A/B" was a 17–24-question effect. Train
   resubstitution is 0.05–0.08 above val for the trees — mild, and the swapped fold agrees with the val fold.
6. **Feature sets**: the 6-feature `legs-only` tree (e5, BM25 chunk, BM25 doc, RRF, convex, exp-13 lexical) is
   within 0.03 of the 56-feature tree on both mined val and human C (0.652 vs 0.671), and on B the 13-feature
   `minimal+meta` logreg is the best *linear* model on the human set (0.395 = convex05). Metadata (region, year)
   never enters the top features on B; on C `is_yearly_edition` and `log_doc_len` do, as in exp 14.
