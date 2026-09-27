# 72 — Statistics for small-sample IR evaluation (CIs, paired tests, multiplicity, nested CV)

**Idea**

Stop reading the leaderboard as point estimates. Every comparison becomes a *paired, per-question* delta with a bootstrap CI and a paired t / permutation p-value; selection among many configs (fusion grids, LTR) happens inside nested cross-validation or is corrected with a max-T permutation; corpora are pooled before any claim.

**Why it fits this project**

- n = 29 / 40 / 64 questions, halves of 12–35. Per-question RR has sd ≈ 0.35–0.45 at MRR 0.70, so a single-corpus MRR is really **0.70 ± 0.10–0.15** (95 %). Paired deltas (sd_d ≈ 0.2–0.3 for related systems) need `n ≈ (1.96+0.84)²·sd_d²/Δ²`: Δ = 0.05 → 125–280 questions; Δ = 0.03 → 350–780. Minimum detectable paired delta at 80 % power: ≈ 0.10–0.16 with 29 questions, 0.07–0.10 with 64, 0.05–0.07 with all 133 pooled.
- A 1,500-config grid picked on 12–35 questions is a textbook winner's curse: the max of ~1,500 noisy estimates (SE ≈ 0.06) is optimistic by roughly 0.1 MRR.
- Per-question ranks are already stored in every result JSON, so the statistics are free post-hoc.

**Evidence**

- Urbano, Lim & Hanjalic, SIGIR 2019 (simulation, AP/nDCG/RR/P@10, 25–100 topics): t-test and permutation test hold Type I at α; bootstrap-shift (0.059 at α = 0.05) and Wilcoxon are anti-conservative, sign test worst. Recommendation: **paired t-test, permutation as alternative**. https://arxiv.org/abs/1905.11096 (PDF read).
- Fuhr, SIGIR Forum 2017: MRR is not interval-scaled (rank 1→2 costs 0.5, 2→3 costs 0.17), so also report mean rank / hit@k; give CIs (bootstrap); Bonferroni when testing many variants. https://sigir.org/wp-content/uploads/2018/01/p032.pdf (PDF read).
- Smucker, Allan & Carterette, CIKM 2007 (t, bootstrap, randomisation agree; Wilcoxon/sign do not); Carterette, TOIS 2012 (many TREC "significant" pairs vanish under Tukey/max-T correction); Boytsov et al., SIGIR 2013 (closed-test/max-T loses far less power than Bonferroni/Holm); Sakai, IRJ 2016 topic-set-size design (t-power / CI-width / ANOVA formulas); Webber, Moffat & Zobel, SIGIR 2008 (statistical power, add topics until powered) — **not fetched (ACM/Springer 403), from memory, unverified**.
- scipy `bootstrap(paired=True, method='BCa')`, `permutation_test(permutation_type='samples')`, `ttest_rel`; sklearn nested-CV pattern — docs read.

**How we would implement it**

`experiments/common/rag_eval/stats.py` (numpy + scipy only):

```python
d = rr_b - rr_a                                  # per-question, aligned qids
diff = lambda x, y, axis=-1: np.mean(y - x, axis=axis)
ci = bootstrap((rr_a, rr_b), diff, paired=True, method="BCa", n_resamples=9999).confidence_interval
p_t = ttest_rel(rr_b, rr_a).pvalue
p_perm = permutation_test((rr_a, rr_b), diff, permutation_type="samples", n_resamples=2**16).pvalue
d_z = d.mean() / d.std(ddof=1)                   # effect size; W/T/L = (d>0, d==0, d<0).sum()
```

- **Max-T for grids**: matrix `D[n_questions, K]` of deltas vs baseline; 10⁴ sign-flip permutations, record `max_k |t_k|`; adjusted `p_k = P(max ≥ |t_k|)`. ~20 lines; respects the correlation between configs that Bonferroni ignores. Holm (`statsmodels.stats.multitest.multipletests(method="holm")`) only for ≤ 10 pre-registered comparisons.
- **Nested CV** for fusion/LTR: outer 5-fold over questions (stratified by corpus), inner grid on the 4 training folds; report outer-fold mean ± CI and *which* config each fold chose (instability = overfitting). Fusion reuses cached leg rankings, so 1,500 × 5 folds costs seconds.
- **Reporting rules** for `EXPERIMENTS.md`: (1) every row = Δ vs a named baseline with 95 % CI and W/T/L; (2) pooled A+B+C (133 q, corpus as blocking factor) is the primary number; (3) show mean rank and hit@1/@5 beside MRR; (4) promote a change only if the pooled CI excludes 0 *or* the sign agrees on all three corpora with Δ ≥ 0.03; (5) val halves are selection sets, not test sets — the leaderboard itself is a multiple comparison.

**Expected gain and cost**

No MRR gain by construction; the gain is not shipping noise dressed as +0.02. Expect several current 0.01–0.04 "wins" to become non-significant and the grid-search val optimum to shrink by ~0.05–0.1 under nested CV. Cost: ~1 day for `stats.py` + leaderboard columns; no LLM, no GPU.

**Risks / open questions**

- Power stays low: even pooled, Δ < 0.05 is undecidable until question sets grow to 200–300.
- t-test on RR is standard (Urbano simulated RR) but MRR's scale problem means hit@k must accompany it.
- Questions differ in difficulty across corpora; pool with a corpus fixed effect, not as 133 i.i.d. draws.

**Verdict**

**try-now** — one day of numpy/scipy, zero compute, and it changes how every other idea in this folder gets judged.

**Sources**

- https://arxiv.org/abs/1905.11096 · https://sigir.org/wp-content/uploads/2018/01/p032.pdf (read)
- https://doi.org/10.1145/1321440.1321528 · https://doi.org/10.1145/2094072.2094076 · https://doi.org/10.1145/2484028.2484034 · https://doi.org/10.1007/s10791-015-9273-z · https://doi.org/10.1145/1390334.1390402 (not fetched)
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html · https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html · https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html
