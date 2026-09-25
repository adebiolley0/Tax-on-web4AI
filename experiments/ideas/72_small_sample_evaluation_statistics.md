# 72 — Statistics for small-sample IR evaluation (CIs, paired tests, multiplicity, nested CV)

**Idea**

Stop reading the leaderboard as point estimates. Every comparison becomes a *paired, per-question* delta with a bootstrap CI and a paired t / permutation p-value; selection among many configs (fusion grids, LTR) is done inside nested cross-validation or corrected with a max-T permutation, and results are pooled across corpora before any claim.

**Why it fits this project**

- n = 29 / 40 / 64 questions, halves of 12–35. Per-question RR has sd ≈ 0.35–0.45 at MRR 0.70, so a single-corpus MRR is really **0.70 ± 0.10–0.15** (95 %). Paired deltas (sd_d ≈ 0.2–0.3 for related systems) need `n ≈ (1.96+0.84)²·sd_d²/Δ²`: Δ = 0.05 → 125–280 questions; Δ = 0.03 → 350–780. With 29 questions the minimum detectable paired delta at 80 % power is ≈ 0.10–0.16; with 64, ≈ 0.07–0.10; pooled 133, ≈ 0.05–0.07.
- A 1,500-config grid picked on 12–35 questions is a textbook winner's curse: the max of ~1,500 noisy estimates (SE ≈ 0.06) is optimistic by roughly 0.1 MRR. `train MRR vs val MRR` in `splits.py` already hints at this; it does not quantify it.
- Per-question ranks are already stored in every result JSON (`per_question[qid].rr`), so the statistics are free post-hoc.

**Evidence**

- Urbano, Lim & Hanjalic, SIGIR 2019 (500 M simulated p-values over AP/nDCG/RR/P@10/ERR, topic sets 25–100): t-test and permutation test keep Type I at α; bootstrap-shift and Wilcoxon are anti-conservative (bootstrap 0.059 at α = 0.05), sign test is worst; recommendation: **paired t-test, permutation test as the alternative**. https://arxiv.org/abs/1905.11096 (read).
- Fuhr, SIGIR Forum 2017: MRR is not interval-scaled (a 1→2 rank drop costs 0.5, 2→3 costs 0.17), so report mean rank / hit@k beside it; report CIs (bootstrap), never plain holdout; Bonferroni when testing many features. https://sigir.org/wp-content/uploads/2018/01/p032.pdf (read).
- Smucker, Allan & Carterette, CIKM 2007: t-test, bootstrap and randomisation agree; Wilcoxon/sign disagree — not fetched (ACM 403), from memory.
- Carterette, TOIS 2012 "Multiple testing in statistical analysis of systems-based IR experiments": many TREC "significant" pairs vanish under Tukey/max-T-style correction — not fetched, unverified.
- Boytsov, Belova & Westerveld, SIGIR 2013: closed-test/max-T permutation adjusts for multiplicity with far less power loss than Bonferroni/Holm — not fetched, unverified.
- Sakai, IRJ 2016 "Topic set size design" (t-test-power, CI-width and ANOVA formulas; needs a pilot variance estimate); Webber, Moffat & Zobel, SIGIR 2008 "Statistical power in retrieval experimentation" — not fetched, unverified; formulas above are the standard paired-power ones.
- scipy: `bootstrap(..., paired=True, method='BCa')`, `permutation_test(..., permutation_type='samples')` (exact enumeration when 2ⁿ ≤ n_resamples), `ttest_rel`; sklearn nested-CV pattern (`GridSearchCV` inside `cross_val_score`) — docs read.

**How we would implement it**

`experiments/common/rag_eval/stats.py` (numpy + scipy only):

```python
d = rr_b - rr_a                                  # per-question, same qids
ci = bootstrap((rr_a, rr_b), lambda x, y, axis=-1: np.mean(y - x, axis=axis),
               paired=True, method="BCa", n_resamples=9999).confidence_interval
p_t = ttest_rel(rr_b, rr_a).pvalue
p_perm = permutation_test((rr_a, rr_b), lambda x, y, axis=-1: np.mean(y - x, axis=axis),
                          permutation_type="samples", n_resamples=2**16).pvalue
d_z = d.mean() / d.std(ddof=1)                   # effect size; W/T/L = (d>0, d==0, d<0).sum()
```

- **Max-T for the grid**: matrix `D[n_questions, K configs]` of deltas vs baseline; for 10⁴ sign-flip permutations take `max_k |t_k|`; adjusted `p_k = P(max ≥ |t_k|)`. ~20 lines; handles the correlation between 1,500 configs that Bonferroni ignores. Holm for ≤ 10 pre-registered comparisons: `statsmodels.stats.multitest.multipletests(method="holm")`.
- **Nested CV** for fusion/LTR: outer 5-fold over questions (stratified by corpus), inner grid on the 4 training folds only; report the outer-fold mean ± CI and *which* config each fold picked (instability = overfitting signal). Fusion is post-hoc on cached leg rankings, so 1,500 × 5 folds costs seconds.
- **Reporting rules** (add to `EXPERIMENTS.md`): (1) every row = Δ vs named baseline with 95 % CI and W/T/L; (2) pooled A+B+C (133 q) is the primary number, per-corpus is secondary; (3) also show mean rank and hit@1/@5 (Fuhr); (4) promote a change only if pooled CI excludes 0 *or* the sign agrees on all three corpora with Δ ≥ 0.03; (5) the val halves are selection sets, not test sets — the leaderboard itself is a multiple comparison.

**Expected gain and cost**

No MRR gain by construction; the gain is not shipping regressions dressed as +0.02 and not chasing noise. Expect several current "wins" of 0.01–0.04 to turn out non-significant, and the grid-search val optimum to shrink by ~0.05–0.1 under nested CV. Cost: ~1 day for `stats.py` + leaderboard columns; no LLM, no GPU.

**Risks / open questions**

- Power stays low: pooled 133 questions detect Δ ≈ 0.05–0.07 only; anything smaller is undecidable until the question sets grow (ideally to 200–300, cf. Sakai/Webber).
- MRR is not interval-scaled; the t-test on RR is standard practice (Urbano simulated RR) but pair it with hit@k.
- Questions are not exchangeable across corpora (different difficulty); pooling should block by corpus (fixed effect) rather than treat all 133 as i.i.d.
- Exact permutation on 12-question halves has 4,096 outcomes; the smallest attainable p is 0.0005 but power is negligible.

**Verdict**

**try-now** — one day of numpy/scipy, zero compute, and it changes how every other idea in this folder gets judged.

**Sources**

- https://arxiv.org/abs/1905.11096 (Urbano et al. 2019; PDF read)
- https://sigir.org/wp-content/uploads/2018/01/p032.pdf (Fuhr 2017; PDF read)
- https://doi.org/10.1145/1321440.1321528 (Smucker et al. 2007; not fetched)
- https://doi.org/10.1145/2094072.2094076 (Carterette 2012; not fetched)
- https://doi.org/10.1145/2484028.2484034 (Boytsov et al. 2013; not fetched)
- https://doi.org/10.1007/s10791-015-9273-z (Sakai 2016, topic set size design; not fetched)
- https://doi.org/10.1145/1390334.1390402 (Webber et al. 2008; not fetched)
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html
- https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html
