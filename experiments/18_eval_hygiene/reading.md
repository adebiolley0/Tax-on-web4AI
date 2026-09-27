
## (d) Reading: which round-2 claims survive

**Short answer: none at conventional significance, on any corpus, on either split, with or without the
multiplicity correction.** Across the six (corpus × split) families above, ~1,000 eligible round-2 runs were
paired against a bar; the number with Δ > 0 *and* raw p < 0.05 is zero, so the max-T correction never even
had to bite on a positive result. What the paired view adds is a ranking of the claims by how *consistent*
their direction is, which is the only thing these question sets can measure.

### A (bar: BM25 whole doc, val 0.736 on 12 questions, SE 0.11)

* 68 of the 328 round-2 runs on A are **rank-identical to the bar** on the val half (the exp-13 tokenizer /
  field / cue variants); a further 213 distinct rank vectors mostly lose. Only 18 have Δ > 0.
* The headline **exp-12 OpenSearch sparse + BM25 RRF, val 0.808** is +0.072 from **3 wins / 0 losses / 9 ties**.
  With three non-tied questions the exact sign-flip test cannot go below p = 0.25 in any direction. Its
  bootstrap CI ([+0.014, +0.189]) excludes zero only because BCa is being asked to summarise three positive
  numbers and nine zeros; **ignore CIs when W + L < ~8, read the exact p.** On the full set the same run is
  +0.037 [+0.008, +0.092], 7 / 1 / 21, p_perm = 0.070: the most direction-consistent round-2 result on A and
  the one worth re-testing. The colbert-fr variant ("best full-set number on A, 0.738") is +0.043, 6 / 2 / 21,
  p = 0.17 against the BM25 bar and +0.035, 7 / 4 / 18, p = 0.48 against the e5 + bge full-set best.
* **exp-13 k1/b on whole docs (val 0.756)**: +0.019, 2 / 1 / 9 — EXPERIMENTS.md already called this "two
  questions; noise"; confirmed.
* **exp-14 logreg on cheap features, oof 0.732 ("best honest number on A")**: +0.029 vs the 0.703 full-set
  best, 7 / 5 / 17, p = 0.57; on the val half it is −0.014. A coin flip.

### B (bar: e5-small RRF + mMARCO@30, val 0.570 on 16 questions, SE 0.11)

* Only 7 of 246 distinct round-2 rank vectors beat the bar on val at all. The top three (exp-14 LambdaMART /
  interpolated mMARCO, val 0.610–0.617) are +0.04–0.05 with 4 / 4 / 8 or 4 / 2 / 10, p ≈ 0.5–0.7.
* **exp-14 "pure e5 + mMARCO@20, β = 0.8", val 0.610**: +0.040 on val (4 / 2 / 10, p = 0.53), +0.026 on the
  full set [−0.012, +0.079], 7 / 2 / 31, p = 0.30. Direction consistent, magnitude undetectable.
* **exp-11 graph-expanded → mMARCO, val 0.592**: +0.022 on val (3 / 2 / 11), **−0.001 on the full set**
  (7 / 5 / 28). The README's own "one question" reading was right.
* **exp-14 logreg on 7 features, oof 0.608 vs bar 0.522**: the largest and most consistent round-2 effect
  anywhere, +0.086 [−0.020, +0.196], 13 / 6 / 21, p = 0.14, Δ hit@1 +0.125 — and still not significant at
  n = 40 (minimum detectable Δ at sd_d 0.34 is ≈ 0.15). Worse, the gain is **entirely on the train half**:
  the val half is −0.052 (2 / 5 / 9), so the train half — ranked by the model fitted on the 16 val questions —
  must be ≈ +0.18. "oof" averages two folds that disagree in sign; report both.
* **exp-17 lexical → bge@30, val 0.440 vs 0.570**: −0.131 is 4 / 5 / 7 with p = 0.28, and −0.008 on the full
  set (11 / 10 / 19). The "three validation questions never enter the lexical top-50" story is three
  questions; the lexical-only first stage is not shown to be worse on B either, only not better.

### C (bar: BM25 chunks + bge-reranker@30, val 0.665 on 35 questions, SE 0.07)

* Only 5 of 276 distinct round-2 rank vectors beat the bar on val. **exp-17 lex13 → bge@20, val 0.688** is
  +0.023 with **4 / 1 / 30**, p_t = 0.19, exact p = 0.31; full set +0.023 [−0.005, +0.066], 7 / 3 / 54, p = 0.24;
  bge@30 is 2 / 0 / 33. The two systems rank the first expected document identically on 30 of 35 val
  questions: behind bge-reranker-v2-m3 the first stage barely matters, which is exactly what `ideas/README.md`
  §1(2) predicted and what the "+0.05 over the bar" wording obscures.
* **exp-13 lexical upgrades, val 0.536 → 0.616** was a lexical-vs-lexical claim (14 / 3 on val, plausible);
  against the *reranked* bar the same run is −0.031 (6 / 8 / 21). The upgrade is real as a cheap first stage,
  not as a replacement for the reranker.
* **exp-14 LambdaMART 15 trees, oof 0.723 vs 0.703**: +0.026 on the full set, 15 / 11 / 38, p = 0.46, and
  **−0.030 on the val half** (7 / 10 / 18): the same fold asymmetry as on B.

### Pooled A + B + C (133 questions)

The exp-14 learned-ranker recipe (per-corpus best oof learner) vs the round-1 full-set bests: **+0.042
[−0.009, +0.093], p_t = 0.11, 34 / 22 / 77, Δ hit@1 +0.075.** This is the closest thing round 2 produced to a
detectable effect, and it is optimistic twice over: the learner per corpus was chosen on the same oof numbers,
and the gain sits on the train folds. It is the right candidate for a pre-registered re-test (one learner,
one feature set, fresh questions). Note that the round-1 validation bars scored on the full set and the
round-1 full-set bests are statistically the same system (−0.007, 12 / 7 / 74).

### What the sets *can* detect

The only max-T-significant results in the six families are **losses**: RM3 pseudo-relevance feedback is
−0.28 on B and −0.31 on C (adjusted p ≤ 0.005), one graph-expansion variant is −0.38 on B (adjusted p = 0.02),
the BSARD-tuned mMARCO −0.17 on A (raw p = 0.01, adjusted 0.40). With 12–64 questions and sd_d ≈ 0.2–0.35
the minimum detectable paired delta is 0.10–0.27 on a single split and ≈ 0.05–0.07 pooled (table (c)). A
+0.03 improvement — the size of every positive round-2 claim — needs 370–800 paired questions
(idea 73's 600–900 mined questions is the right order of magnitude), or ≈ 130 questions if it is a
reranker-preserving change with sd_d ≈ 0.2.

### Surprises

1. Not one of the ~1,000 round-2 run/split comparisons beats its bar at raw p < 0.05, so the leaderboard's
   "best val MRR" ordering is ordering noise; the exp-14 `__fit-val` rows at the top of `rag_eval.splits`'s
   leaderboard (val MRR 1.000 on A, 0.875 on B, 0.971 on C) are in-sample and should be hidden by default.
2. Bootstrap CIs that exclude zero at n = 12 (A) and n = 35 with 30 ties (C) are artefacts of BCa on a handful
   of non-zero deltas; the exact sign-flip p is the honest statistic when ties dominate, and ties dominate
   whenever two systems share a reranker.
3. The exp-14 "oof" gains on B and C come entirely from the train fold; the val fold is negative on both.
   Two-fold oof should be reported per fold, or replaced by repeated CV.
4. Ties are the norm: on C the top round-2 systems agree with the bar on 85–95 % of questions. Growing the
   question set matters more than any first-stage idea in tier A of `ideas/README.md`.

### Rules this report implies for EXPERIMENTS.md and round 3

* Every claimed improvement is reported as Δ vs a named bar run with n, exact p (or `~` Monte-Carlo p), the
  bootstrap CI *and* W / L / T; a claim with W + L < 8 is "untestable", not "a win".
* A val-split number is a selection number. Promotion needs the pooled A + B + C paired CI to exclude zero,
  or the same sign on all three corpora with Δ ≥ 0.03 and W > 2 L on each.
* `rag_eval.stats.compare_many` (max-T) is the leaderboard's significance column when a family of configs is
  scanned; Bonferroni over 300 runs would be far more conservative than the correlation-aware max-T already
  is, and even max-T finds nothing positive here.
* Report the two oof folds separately; treat fold-sign disagreement as overfitting.
* Provenance is now stamped on every new run (commit, time, host, harness version, question-file hash,
  corpus fingerprint); comparisons across different `questions_sha256` or `corpus_ids_sha256` are invalid.
