### Experiment 24 – corpus B: pooled-label ranker

Coverage: `{"human_train": {"n": 24, "bge_full_top20": 24, "bge_any": 24, "mean_top20_coverage": 1.0, "q_verbatim_gt0.2": 0, "words_median": 20.0}, "human_val": {"n": 16, "bge_full_top20": 16, "bge_any": 16, "mean_top20_coverage": 1.0, "q_verbatim_gt0.2": 0, "words_median": 20.5}, "mined_train": {"n": 145, "bge_full_top20": 68, "bge_any": 68, "mean_top20_coverage": 0.469, "q_verbatim_gt0.2": 2, "words_median": 79.0}, "mined_val": {"n": 159, "bge_full_top20": 82, "bge_any": 82, "mean_top20_coverage": 0.516, "q_verbatim_gt0.2": 4, "words_median": 78.0}}`; bge sources `{"exp21_cache_pairs": 3800, "exp22_pairs": 2800, "exp22_added": 1690, "merged_pairs": 5490}`; candidate recall human 0.975 / mined 0.849

| pool | features | method | n pool (human) | w_h / C (nested CV crit: mined / human) | human **val** MRR (H@1 / R@10) | human oof all | human oof (all mined) | human train resub | mined val (scored) | mined val per source | mined train resub | post-hoc human val per w |
|---|---|---|--:|---|---|--:|--:|--:|---|---|--:|---|
| mined | notype | lgbm-tiny | 145 (0) | 1 / – (0.436: 0.436 / nan) | **0.442** (0.312 / 0.562) | **0.534** | nan | 0.511 | 0.478 (0.585) | pq 0.294, ruling 0.704, faq 0.000 | 0.494 |  |
| pooled | notype | lgbm-tiny | 169 (24) | 5 / – (0.545: 0.438 / 0.652) | **0.497** (0.312 / 0.875) | **0.577** | 0.612 | 0.800 | 0.452 (0.548) | pq 0.269, ruling 0.677, faq 0.000 | 0.475 | w=1.0 0.496, w=5.0 0.497, w=10.0 0.531 |

Nested-CV grid (criterion = mean of held-out mined and held-out human-train MRR):

* `lgbm-tiny__notype__pooled`: w=1.0: 0.521 (0.428/0.615); w=5.0: 0.545 (0.438/0.652); w=10.0: 0.527 (0.410/0.643)

Top features (fit A):

* `lgbm-tiny__notype__mined`: lex13_logrank +0.240, lex13_norm +0.183, title_overlap_n +0.099, rrf60_logrank +0.077, log_doc_len +0.066, title_overlap +0.056, rrf60 +0.053, e5_logrank +0.039, log_n_chunks +0.025, bge_norm +0.024
* `lgbm-tiny__notype__pooled`: bge_logrank +0.170, e5_norm +0.160, lex13_norm +0.115, bge_norm +0.110, e5_logrank +0.102, lex13_logrank +0.077, rrf60_logrank +0.060, bge_norm_x_loglen +0.051, title_overlap_n +0.038, n_legs_top30 +0.025

Length-gate diagnostics (fit A, tree-SHAP contribution of the bge features; scored questions, human + mined val):

| model | words | n rows (q) | mean abs bge contrib | share of abs contrib | slope on bge_norm | Spearman | PD(bge_norm 0→1) | PD range |
|---|---|--:|--:|--:|--:|--:|---|--:|
| lgbm-tiny__notype__pooled | 0–25 | 825 (37) | 0.649 | 0.308 | +1.516 | +0.84 | -0.74 / -0.67 / -0.67 / -0.67 / 0.02 | +0.759 |
| lgbm-tiny__notype__pooled | 26–50 | 446 (19) | 0.567 | 0.285 | +1.585 | +0.81 | -0.66 / -0.59 / -0.59 / -0.59 / 0.03 | +0.692 |
| lgbm-tiny__notype__pooled | 51–100 | 822 (40) | 0.728 | 0.328 | +1.526 | +0.86 | -0.23 / -0.16 / -0.16 / -0.16 / 0.45 | +0.685 |
| lgbm-tiny__notype__pooled | 101–∞ | 577 (26) | 0.656 | 0.297 | +1.558 | +0.88 | -0.18 / -0.11 / -0.11 / -0.11 / 0.50 | +0.679 |

**Human VAL half – paired tests (Δ = exp-24 fit A − reference)**

| run | reference  Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 | Δ H@10 |
|---|---|:--|--:|--:|:--|--:|--:|
| ltr24__lgbm-tiny__notype__mined | vs bar_val (n=16, ref 0.570 → 0.442) | -0.129 [-0.369, +0.084] | 0.306 | 0.311 | 5/7/4 | -0.125 | -0.250 |
| ltr24__lgbm-tiny__notype__mined | vs bar_full (n=16, ref 0.570 → 0.442) | -0.129 [-0.369, +0.084] | 0.306 | 0.311 | 5/7/4 | -0.125 | -0.250 |
| ltr24__lgbm-tiny__notype__mined | vs exp14 (n=16, ref 0.519 → 0.442) | -0.077 [-0.322, +0.165] | 0.555 | 0.560 | 5/7/4 | -0.062 | -0.250 |
| ltr24__lgbm-tiny__notype__mined | vs exp14_cheap (n=16, ref 0.411 → 0.442) | +0.030 [-0.136, +0.228] | 0.760 | 0.766 | 4/6/6 | +0.000 | -0.125 |
| ltr24__lgbm-tiny__notype__mined | vs lex13 (n=16, ref 0.326 → 0.442) | +0.116 [-0.009, +0.279] | 0.142 | 0.150 | 9/2/5 | +0.062 | -0.062 |
| ltr24__lgbm-tiny__notype__mined | vs bm25_01 (n=16, ref 0.290 → 0.442) | +0.151 [+0.015, +0.288] | 0.053 | 0.043 | 11/1/4 | +0.188 | +0.000 |
| ltr24__lgbm-tiny__notype__mined | vs convex05 (n=16, ref 0.319 → 0.442) | +0.123 [-0.077, +0.310] | 0.248 | 0.251 | 9/5/2 | +0.125 | +0.000 |
| ltr24__lgbm-tiny__notype__mined | vs convex05+bge@20 (n=16, ref 0.468 → 0.442) | -0.026 [-0.210, +0.170] | 0.799 | 0.841 | 6/7/3 | -0.062 | -0.062 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.442) | +0.045 [-0.064, +0.204] | 0.519 | 0.543 | 6/4/6 | +0.062 | -0.062 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap (n=16, ref 0.371 → 0.442) | +0.071 [+0.025, +0.174] | 0.054 | 0.008 | 8/1/7 | +0.062 | +0.000 |
| ltr24__lgbm-tiny__notype__mined | vs exp22 gate T25 (n=16, ref 0.613 → 0.442) | -0.172 [-0.355, +0.009] | 0.098 | 0.102 | 2/9/5 | -0.125 | -0.375 |
| ltr24__lgbm-tiny__notype__pooled | vs bar_val (n=16, ref 0.570 → 0.497) | -0.073 [-0.271, +0.161] | 0.524 | 0.547 | 3/6/7 | -0.125 | +0.062 |
| ltr24__lgbm-tiny__notype__pooled | vs bar_full (n=16, ref 0.570 → 0.497) | -0.073 [-0.271, +0.161] | 0.524 | 0.547 | 3/6/7 | -0.125 | +0.062 |
| ltr24__lgbm-tiny__notype__pooled | vs exp14 (n=16, ref 0.519 → 0.497) | -0.022 [-0.132, +0.022] | 0.546 | 0.719 | 4/3/9 | -0.062 | +0.062 |
| ltr24__lgbm-tiny__notype__pooled | vs exp14_cheap (n=16, ref 0.411 → 0.497) | +0.086 [-0.065, +0.263] | 0.337 | 0.346 | 7/3/6 | +0.000 | +0.188 |
| ltr24__lgbm-tiny__notype__pooled | vs lex13 (n=16, ref 0.326 → 0.497) | +0.171 [-0.083, +0.407] | 0.212 | 0.213 | 9/3/4 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled | vs bm25_01 (n=16, ref 0.290 → 0.497) | +0.207 [+0.021, +0.421] | 0.070 | 0.071 | 9/3/4 | +0.188 | +0.312 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05 (n=16, ref 0.319 → 0.497) | +0.178 [+0.032, +0.360] | 0.057 | 0.051 | 10/2/4 | +0.125 | +0.312 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05+bge@20 (n=16, ref 0.468 → 0.497) | +0.029 [-0.119, +0.229] | 0.750 | 0.773 | 4/4/8 | -0.062 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.497) | +0.101 [-0.062, +0.294] | 0.295 | 0.308 | 8/4/4 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap (n=16, ref 0.371 → 0.497) | +0.126 [-0.057, +0.341] | 0.245 | 0.252 | 9/3/4 | +0.062 | +0.312 |
| ltr24__lgbm-tiny__notype__pooled | vs exp22 gate T25 (n=16, ref 0.613 → 0.497) | -0.116 [-0.262, +0.110] | 0.239 | 0.245 | 2/10/4 | -0.125 | -0.062 |
| ltr24__lgbm-tiny__notype__pooled | vs exp24 mined-only (same features) (n=16, ref 0.442 → 0.497) | +0.055 [-0.167, +0.271] | 0.634 | 0.630 | 7/4/5 | +0.000 | +0.312 |

**Human full set – paired tests (Δ = exp-24 oof − reference)**

| run | reference  Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 | Δ H@10 |
|---|---|:--|--:|--:|:--|--:|--:|
| ltr24__lgbm-tiny__notype__mined | vs bar_val (n=40, ref 0.522 → 0.534) | +0.012 [-0.113, +0.125] | 0.847 | ~0.846 | 15/13/12 | +0.075 | -0.125 |
| ltr24__lgbm-tiny__notype__mined | vs bar_full (n=40, ref 0.522 → 0.534) | +0.012 [-0.113, +0.125] | 0.847 | ~0.846 | 15/13/12 | +0.075 | -0.125 |
| ltr24__lgbm-tiny__notype__mined | vs exp14 (n=40, ref 0.608 → 0.534) | -0.074 [-0.191, +0.036] | 0.216 | ~0.219 | 11/14/15 | -0.050 | -0.125 |
| ltr24__lgbm-tiny__notype__mined | vs exp14_cheap (n=40, ref 0.491 → 0.534) | +0.043 [-0.037, +0.137] | 0.341 | ~0.349 | 13/11/16 | +0.050 | -0.100 |
| ltr24__lgbm-tiny__notype__mined | vs lex13 (n=40, ref 0.391 → 0.534) | **+0.142** [+0.057, +0.246] | 0.006 | ~0.005 | 22/4/14 | +0.125 | +0.100 |
| ltr24__lgbm-tiny__notype__mined | vs bm25_01 (n=40, ref 0.339 → 0.534) | **+0.195** [+0.114, +0.286] | 0.000 | ~0.000 | 28/1/11 | +0.225 | +0.100 |
| ltr24__lgbm-tiny__notype__mined | vs convex05 (n=40, ref 0.395 → 0.534) | **+0.139** [+0.045, +0.236] | 0.008 | ~0.007 | 22/8/10 | +0.175 | +0.075 |
| ltr24__lgbm-tiny__notype__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.534) | +0.039 [-0.055, +0.134] | 0.434 | ~0.444 | 17/10/13 | +0.025 | +0.025 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.534) | +0.061 [-0.009, +0.143] | 0.120 | ~0.123 | 17/6/17 | +0.075 | +0.000 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.534) | **+0.106** [+0.042, +0.187] | 0.006 | ~0.004 | 20/3/17 | +0.100 | +0.075 |
| ltr24__lgbm-tiny__notype__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.534) | -0.095 [-0.216, +0.011] | 0.117 | ~0.117 | 8/17/15 | -0.025 | -0.200 |
| ltr24__lgbm-tiny__notype__pooled | vs bar_val (n=40, ref 0.522 → 0.577) | +0.055 [-0.050, +0.167] | 0.340 | ~0.341 | 15/9/16 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled | vs bar_full (n=40, ref 0.522 → 0.577) | +0.055 [-0.050, +0.167] | 0.340 | ~0.341 | 15/9/16 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled | vs exp14 (n=40, ref 0.608 → 0.577) | -0.031 [-0.107, +0.028] | 0.374 | 0.386 | 9/9/22 | -0.025 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled | vs exp14_cheap (n=40, ref 0.491 → 0.577) | **+0.086** [+0.014, +0.173] | 0.040 | ~0.033 | 16/5/19 | +0.075 | +0.075 |
| ltr24__lgbm-tiny__notype__pooled | vs lex13 (n=40, ref 0.391 → 0.577) | **+0.185** [+0.053, +0.317] | 0.010 | ~0.010 | 21/5/14 | +0.150 | +0.275 |
| ltr24__lgbm-tiny__notype__pooled | vs bm25_01 (n=40, ref 0.339 → 0.577) | **+0.238** [+0.135, +0.357] | 0.000 | ~0.000 | 25/3/12 | +0.250 | +0.275 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05 (n=40, ref 0.395 → 0.577) | **+0.182** [+0.095, +0.291] | 0.001 | ~0.000 | 24/5/11 | +0.200 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05+bge@20 (n=40, ref 0.495 → 0.577) | +0.082 [-0.007, +0.194] | 0.115 | ~0.119 | 14/8/18 | +0.050 | +0.200 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.577) | +0.105 [+0.011, +0.211] | 0.051 | ~0.051 | 18/7/15 | +0.100 | +0.175 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap (n=40, ref 0.427 → 0.577) | **+0.149** [+0.040, +0.267] | 0.014 | ~0.016 | 22/5/13 | +0.125 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled | vs exp22 gate T25 (n=40, ref 0.628 → 0.577) | -0.052 [-0.155, +0.055] | 0.355 | ~0.356 | 9/16/15 | +0.000 | -0.025 |
| ltr24__lgbm-tiny__notype__pooled | vs exp24 mined-only (same features) (n=40, ref 0.534 → 0.577) | +0.043 [-0.049, +0.145] | 0.388 | ~0.396 | 13/8/19 | +0.025 | +0.175 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.612) | +0.090 [-0.022, +0.202] | 0.130 | ~0.133 | 16/7/17 | +0.150 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.612) | +0.090 [-0.022, +0.202] | 0.130 | ~0.133 | 16/7/17 | +0.150 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.612) | +0.005 [-0.082, +0.083] | 0.915 | 0.917 | 11/9/20 | +0.025 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.612) | **+0.121** [+0.050, +0.211] | 0.005 | ~0.003 | 18/6/16 | +0.125 | +0.075 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.612) | **+0.221** [+0.112, +0.343] | 0.001 | ~0.000 | 23/3/14 | +0.200 | +0.275 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.612) | **+0.273** [+0.178, +0.388] | 0.000 | ~0.000 | 26/0/14 | +0.300 | +0.275 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.612) | **+0.218** [+0.132, +0.323] | 0.000 | ~0.000 | 23/4/13 | +0.250 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.612) | **+0.117** [+0.021, +0.233] | 0.036 | ~0.034 | 16/8/16 | +0.100 | +0.200 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.612) | **+0.140** [+0.065, +0.240] | 0.003 | ~0.002 | 18/3/19 | +0.150 | +0.175 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.612) | **+0.185** [+0.097, +0.294] | 0.001 | ~0.000 | 21/2/17 | +0.175 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.612) | -0.016 [-0.124, +0.090] | 0.771 | ~0.770 | 11/12/17 | +0.050 | -0.025 |

**Mined val split – paired tests (Δ = exp-24 fit A − reference)**

| run | reference  Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 | Δ H@10 |
|---|---|:--|--:|--:|:--|--:|--:|
| ltr24__lgbm-tiny__notype__mined | vs convex05 (n=159, ref 0.401 → 0.478) | **+0.077** [+0.048, +0.115] | 0.000 | ~0.000 | 58/19/82 | +0.088 | +0.063 |
| ltr24__lgbm-tiny__notype__mined | vs exp13_lex (n=159, ref 0.428 → 0.478) | **+0.050** [+0.015, +0.087] | 0.008 | ~0.007 | 52/23/84 | +0.069 | +0.044 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.585) | +0.035 [-0.002, +0.081] | 0.101 | ~0.102 | 22/8/52 | +0.024 | +0.049 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.478) | -0.009 [-0.025, +0.000] | 0.144 | ~0.153 | 24/17/118 | -0.019 | +0.006 |
| ltr24__lgbm-tiny__notype__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.585) | **+0.073** [+0.025, +0.127] | 0.007 | ~0.006 | 29/9/44 | +0.098 | +0.024 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05 (n=159, ref 0.401 → 0.452) | **+0.051** [+0.017, +0.089] | 0.006 | ~0.005 | 51/27/81 | +0.057 | +0.057 |
| ltr24__lgbm-tiny__notype__pooled | vs exp13_lex (n=159, ref 0.428 → 0.452) | +0.024 [-0.014, +0.062] | 0.218 | ~0.217 | 45/37/77 | +0.038 | +0.038 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.548) | -0.002 [-0.033, +0.029] | 0.914 | ~0.913 | 15/13/54 | -0.024 | +0.061 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.452) | **-0.035** [-0.065, -0.007] | 0.018 | ~0.017 | 18/50/91 | -0.050 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.548) | +0.036 [-0.007, +0.086] | 0.133 | ~0.137 | 24/13/45 | +0.049 | +0.037 |
| ltr24__lgbm-tiny__notype__pooled | vs exp24 mined-only (same features) (n=159, ref 0.478 → 0.452) | **-0.026** [-0.051, -0.004] | 0.036 | ~0.033 | 18/47/94 | -0.031 | -0.006 |
