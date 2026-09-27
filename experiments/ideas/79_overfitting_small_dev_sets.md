# 79 — Measuring and reducing overfitting to a small dev set

**Idea**

Treat the 133 questions as a scarce, contaminable resource. Select pipeline variants only out-of-fold (nested CV), test "general" claims leave-one-corpus-out, shrink choices toward defaults (one-SE rule), pre-register each experiment's decision rule, record leaderboard improvements only above a noise threshold (Ladder), and periodically add a fresh blind question set.

**Why it fits this project**

Per-question reciprocal rank has SD ≈ 0.4, so a 35-question fold has SE ≈ 0.07 MRR. Experiment 14 scanned 1,513 configurations per (corpus, legs); the expected winner's-curse inflation of the best of k noisy estimates is roughly SE·√(2 ln k) ≈ 0.2 MRR if independent (less for correlated configs, still larger than any effect we have measured). This is why tuned fusion weights did not transfer between folds while fixed defaults did. Most "+0.02" leaderboard entries are indistinguishable from noise. The ingredients exist (deterministic `Question.split`, `fold_report` fit-train/fit-val/oof, corpora A/B/C with 29/40/64 questions); what is missing is discipline about *when* each number may be looked at.

**Evidence** (URLs)

- Recht et al. (ICML 2019): fresh ImageNet/CIFAR-10 test sets → accuracy drops of 11–14 / 3–15 points, but model *ordering* preserved; drops attributed to harder images, not adaptivity. A fresh set tells us whether ordering survives, which is what we need. https://arxiv.org/abs/1902.10811
- Dwork et al. (2015): a naively reused holdout supports only ~linear-in-n adaptive queries; Thresholdout (noise + report only when train/holdout differ beyond a threshold) supports exponentially many. https://arxiv.org/abs/1506.02629 · https://arxiv.org/abs/1411.2664
- Blum & Hardt, "The Ladder" (2015): a leaderboard that updates only when a submission beats the incumbent by a step size resists overfitting from repeated submissions; parameter-free variant validated on Kaggle data. https://arxiv.org/abs/1502.04585
- Cawley & Talbot (JMLR 2010): over-fitting the *selection criterion* costs as much as differences between algorithms; nested CV removes the bias. https://jmlr.org/papers/v11/cawley10a.html
- Varma & Simon (2006): plain CV after model selection is optimistically biased; nested CV nearly unbiased (unverified). https://link.springer.com/article/10.1186/1471-2105-7-91
- IR topic-set-size work (Voorhees & Buckley 2002; Webber, Moffat, Zobel 2008; Sakai): with 25–50 topics, differences < 0.05 in MAP-style measures are rarely significant (from memory, unverified).

**How we would implement it**

1. **Roles.** Train fold = free exploration. Val fold = read once per experiment folder, for the comparison written in the README *before* running (`preregistered: true` in `save_result` config). Recipes chosen on two corpora are reported on the third, untouched.
2. **Selection rule** in `protocol.select_best`: keep the default (RRF k=60, w=0.5, rerank@30, β=1) unless a candidate beats it out-of-fold by > 1 paired-bootstrap SE; grids > 50 points use repeated 5×2 CV instead of a single 2-fold.
3. **Ladder leaderboard.** `rag_eval.results` flags "improvement" only if OOF MRR exceeds the incumbent by ≥ 0.03; otherwise "tie". Paired-bootstrap CI printed beside every metric.
4. **Leave-one-topic-out** for anything using metadata (region, year, doc type): fold by topic tag, so a rule cannot memorise the three regional codes.
5. **Fresh set v2.** Every ~10 experiments, write ≈ 40 new questions (different author or LLM-drafted, human-checked, disjoint documents where possible); score the top-5 incumbents blind once; log old-vs-new deltas; then retire v1 to "train".
6. **Budget log.** `val_reads.jsonl` counts val/fresh-set reads per experiment; a second read per hypothesis needs a written reason.

**Expected gain and cost**

No MRR gain; the gain is fewer false wins and fewer regressions at 100k documents. Likely effect: several leaderboard entries downgraded to ties, recommendations converging on defaults + reranker. Cost: one day on `protocol.py`/`results.py`, plus ~half a day per fresh question set.

**Risks / open questions**

- Thresholds (0.03, one-SE) are judgement calls; if nothing ever passes, the remedy is more questions, not a looser rule.
- Fresh questions from the same author share style bias (Recht's "harder images" effect cuts both ways).
- Thresholdout-style noise is overkill here; the Ladder rule plus pre-registration captures most of the value.
- LLM-drafted questions may echo the retriever's own vocabulary.

**Verdict**

try-now — a cheap process change that explains the exp-14 non-transfer and stops the next ten experiments from chasing noise.

**Sources**

URLs inline above; `experiments/14_ltr_fusion/protocol.py`, `experiments/14_ltr_fusion/README.md`, `experiments/ideas/15_hybrid_fusion_theory.md`.
