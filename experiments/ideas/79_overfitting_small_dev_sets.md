# 79 — Measuring and reducing overfitting to a small dev set

**Idea**

Treat the 133 questions as a scarce, contaminable resource. Stop selecting pipeline variants on numbers that were also used to pick them: nested/out-of-fold selection for anything with free parameters, leave-one-corpus-out for anything claimed to be "general", a one-SE / shrink-to-default rule for choices, pre-registered decision rules per experiment, a leaderboard that only records changes above a noise threshold, and a periodic *fresh* blind question set.

**Why it fits this project**

Per-question reciprocal rank has SD ≈ 0.4, so a 35-question fold has SE ≈ 0.07 MRR. Experiment 14 scanned 1,513 configurations per (corpus, legs); the expected "winner's curse" of the best of k noisy estimates is roughly SE·√(2 ln k) ≈ 0.2 MRR if independent (less when configs are correlated, but still larger than any real effect we have measured). This is exactly why tuned fusion weights failed to transfer between folds while fixed defaults held. Most of what the leaderboard calls "+0.02" is indistinguishable from noise unless the protocol says otherwise. We already have the ingredients (deterministic `Question.split`, `fold_report` fit-train/fit-val/oof, three corpora A/B/C with 29/40/64 questions) — what is missing is discipline about *when* each number may be looked at.

**Evidence** (URLs)

- Recht, Roelofs, Schmidt, Shankar (ICML 2019): new ImageNet/CIFAR-10 test sets → accuracy drops of 11–14 / 3–15 points; yet ranking of models was preserved, and drops were attributed to harder images rather than adaptivity. Lesson for us: a fresh test set tells us whether *ordering* survives, which is what we need. https://arxiv.org/abs/1902.10811
- Dwork et al., "Generalization in adaptive data analysis and holdout reuse" (NeurIPS 2015) and "Preserving statistical validity in adaptive data analysis" (STOC 2015): a holdout answered naively supports only ~linear-in-n adaptive queries; Thresholdout (noise + report only when train/holdout differ by more than a threshold) supports exponentially many. https://arxiv.org/abs/1506.02629 · https://arxiv.org/abs/1411.2664
- Blum & Hardt, "The Ladder" (2015): a leaderboard that only updates when the new score beats the incumbent by a step size resists overfitting through repeated submissions; parameter-free variant validated on Kaggle data. https://arxiv.org/abs/1502.04585
- Cawley & Talbot (JMLR 2010): over-fitting *the model-selection criterion* costs as much as differences between algorithms; low-variance selection criteria matter; nested CV removes the selection bias. https://jmlr.org/papers/v11/cawley10a.html
- Varma & Simon (BMC Bioinformatics 2006): plain CV after model selection is optimistically biased; nested CV is nearly unbiased (unverified this session). https://link.springer.com/article/10.1186/1471-2105-7-91
- IR topic-set-size work (Voorhees & Buckley SIGIR 2002; Webber, Moffat, Zobel CIKM 2008; Sakai's topic-set-size design): ~50 topics give error rates of several percent for MAP-style measures; differences < 0.05 on 25–50 topics are rarely significant (from memory, unverified).

**How we would implement it**

1. **Roles.** Train fold = free exploration. Val fold = read at most once per experiment folder, for the comparison written in the README *before* running (`preregistered: true` in `save_result` config). Cross-corpus (A/B/C) = the "held-out corpus" check: any recipe chosen on two corpora is reported on the third untouched.
2. **Selection rule** in `protocol.select_best`: pick the *default* (RRF k=60, w=0.5, rerank@30, β=1) unless the candidate beats it out-of-fold by > 1 paired-bootstrap SE (one-SE rule); for grids > 50 points, repeated 5×2 CV instead of the single 2-fold.
3. **Ladder leaderboard.** `rag_eval.results` marks a run as "improvement" only if its OOF MRR exceeds the incumbent by ≥ 0.03 (≈ half an SE on 64 questions, one SE on 133); otherwise it is logged as a tie. Paired bootstrap CI printed next to every metric.
4. **Leave-one-topic-out** for anything that uses metadata (region, year, doc type): fold by topic tag, not by question hash, so a rule cannot memorise the three regional codes.
5. **Fresh set v2.** Every ~10 experiments, write ≈ 40 new questions (different author or LLM-drafted, human-checked, disjoint documents where possible), score the top-5 incumbents blind once, and record old-vs-new deltas per method. Retire v1 to "train" afterwards.
6. **Budget log.** A `val_reads.jsonl` counting val/fresh-set evaluations per experiment; more than one read per hypothesis needs a written reason.

**Expected gain and cost**

No MRR gain — the gain is fewer false "wins" and fewer regressions when the corpus grows to 100k docs. Likely effect: several leaderboard entries downgraded to ties; recommendations converge on defaults + reranker. Cost: one day on `protocol.py`/`results.py`, plus ~half a day per fresh question set.

**Risks / open questions**

- Thresholds (0.03, one-SE) are judgement calls; too strict and we never adopt anything on 133 questions — the remedy is more questions, not a looser rule.
- Fresh questions written by the same person share style bias (Recht's "harder images" effect works both ways).
- Thresholdout-style noise addition is overkill for a two-person project; the Ladder rule and pre-registration capture most of the value.
- With LLM-drafted questions, contamination of the question style by the retriever's own vocabulary is possible.

**Verdict**

try-now — cheap process change that directly explains the exp-14 non-transfer and prevents the next ten experiments from chasing noise.

**Sources**

URLs inline above; project files `experiments/14_ltr_fusion/protocol.py`, `experiments/14_ltr_fusion/README.md`, `experiments/ideas/15_hybrid_fusion_theory.md`.
