### Experiment 24 – corpus C: pooled-label ranker

Coverage: `{"human_train": {"n": 29, "bge_full_top20": 29, "bge_any": 29, "mean_top20_coverage": 1.0, "q_verbatim_gt0.2": 0, "words_median": 33.0}, "human_val": {"n": 35, "bge_full_top20": 35, "bge_any": 35, "mean_top20_coverage": 1.0, "q_verbatim_gt0.2": 0, "words_median": 32.0}, "mined_train": {"n": 352, "bge_full_top20": 106, "bge_any": 106, "mean_top20_coverage": 0.301, "q_verbatim_gt0.2": 280, "words_median": 77.5}, "mined_val": {"n": 345, "bge_full_top20": 94, "bge_any": 94, "mean_top20_coverage": 0.272, "q_verbatim_gt0.2": 262, "words_median": 67.0}}`; bge sources `{"exp21_cache_pairs": 6525, "merged_pairs": 6525}`; candidate recall human 0.984 / mined 0.839

| pool | features | method | n pool (human) | w_h / C (nested CV crit: mined / human) | human **val** MRR (H@1 / R@10) | human oof all | human oof (all mined) | human train resub | mined val (scored) | mined val per source | mined train resub | post-hoc human val per w |
|---|---|---|--:|---|---|--:|--:|--:|---|---|--:|---|
| mined | notype | lgbm-tiny | 352 (0) | 1 / – (0.804: 0.804 / nan) | **0.604** (0.486 / 0.795) | **0.659** | nan | 0.726 | 0.759 (0.736) | pq 0.102, ruling 0.977, faq 0.988 | 0.815 |  |
| mined | notype | logreg | 352 (0) | 1 / 0.03 (0.792: 0.792 / nan) | **0.601** (0.486 / 0.871) | **0.620** | nan | 0.642 | 0.744 (0.731) | pq 0.080, ruling 0.976, faq 0.949 | 0.799 |  |
| mined | withtype | lgbm-tiny | 352 (0) | 1 / – (0.811: 0.811 / nan) | **0.583** (0.457 / 0.829) | **0.638** | nan | 0.705 | 0.769 (0.746) | pq 0.143, ruling 0.976, faq 0.988 | 0.832 |  |
| mined | withtype | logreg | 352 (0) | 1 / 0.03 (0.806: 0.806 / nan) | **0.477** (0.343 / 0.729) | **0.502** | nan | 0.532 | 0.759 (0.751) | pq 0.141, ruling 0.973, faq 0.958 | 0.812 |  |
| mined | notype-nogate | lgbm-tiny | 352 (0) | 1 / – (0.775: 0.775 / nan) | **0.608** (0.486 / 0.795) | **0.671** | nan | 0.748 | 0.730 (0.704) | pq 0.100, ruling 0.941, faq 0.946 | 0.792 |  |
| mined | notype-nogate | logreg | 352 (0) | 1 / 1.0 (0.743: 0.743 / nan) | **0.622** (0.514 / 0.857) | **0.662** | nan | 0.709 | 0.696 (0.675) | pq 0.075, ruling 0.902, faq 0.914 | 0.746 |  |
| mined | notype-nobge | lgbm-tiny | 352 (0) | 1 / – (0.803: 0.803 / nan) | **0.610** (0.486 / 0.795) | **0.655** | nan | 0.708 | 0.760 (0.742) | pq 0.101, ruling 0.979, faq 0.988 | 0.817 |  |
| mined | notype-nobge | logreg | 352 (0) | 1 / 0.03 (0.794: 0.794 / nan) | **0.520** (0.400 / 0.795) | **0.532** | nan | 0.546 | 0.744 (0.733) | pq 0.083, ruling 0.975, faq 0.950 | 0.796 |  |
| mined | small | lgbm-tiny | 352 (0) | 1 / – (0.804: 0.804 / nan) | **0.583** (0.457 / 0.843) | **0.635** | nan | 0.699 | 0.749 (0.745) | pq 0.095, ruling 0.976, faq 0.955 | 0.822 |  |
| mined | small | logreg | 352 (0) | 1 / 0.1 (0.800: 0.800 / nan) | **0.579** (0.486 / 0.771) | **0.566** | nan | 0.550 | 0.736 (0.727) | pq 0.062, ruling 0.974, faq 0.942 | 0.798 |  |
| pooled | notype | lgbm-tiny | 381 (29) | 5 / – (0.786: 0.789 / 0.784) | **0.644** (0.543 / 0.914) | **0.703** | 0.684 | 0.816 | 0.749 (0.724) | pq 0.100, ruling 0.965, faq 0.973 | 0.804 | w=1.0 0.608, w=5.0 0.644, w=10.0 0.653 |
| pooled | notype | logreg | 381 (29) | 10 / 0.03 (0.776: 0.793 / 0.758) | **0.660** (0.543 / 0.886) | **0.692** | 0.687 | 0.781 | 0.748 (0.735) | pq 0.071, ruling 0.981, faq 0.969 | 0.795 | w=1.0 0.659, w=5.0 0.644, w=10.0 0.660 |
| pooled | withtype | lgbm-tiny | 381 (29) | 10 / – (0.782: 0.782 / 0.782) | **0.647** (0.543 / 0.900) | **0.699** | 0.705 | 0.831 | 0.745 (0.717) | pq 0.109, ruling 0.957, faq 0.964 | 0.793 | w=1.0 0.600, w=5.0 0.638, w=10.0 0.647 |
| pooled | withtype | logreg | 381 (29) | 10 / 0.03 (0.757: 0.802 / 0.711) | **0.581** (0.457 / 0.843) | **0.645** | 0.636 | 0.797 | 0.759 (0.743) | pq 0.107, ruling 0.981, faq 0.975 | 0.803 | w=1.0 0.592, w=5.0 0.590, w=10.0 0.581 |
| pooled | notype-nogate | lgbm-tiny | 381 (29) | 5 / – (0.777: 0.774 / 0.781) | **0.644** (0.543 / 0.914) | **0.707** | 0.698 | 0.797 | 0.729 (0.694) | pq 0.106, ruling 0.931, faq 0.955 | 0.787 | w=1.0 0.609, w=5.0 0.644, w=10.0 0.645 |
| pooled | notype-nogate | logreg | 381 (29) | 10 / 0.03 (0.754: 0.752 / 0.756) | **0.633** (0.514 / 0.857) | **0.683** | 0.681 | 0.764 | 0.702 (0.689) | pq 0.064, ruling 0.914, faq 0.924 | 0.754 | w=1.0 0.643, w=5.0 0.635, w=10.0 0.633 |
| pooled | notype-nobge | lgbm-tiny | 381 (29) | 10 / – (0.780: 0.778 / 0.782) | **0.653** (0.543 / 0.900) | **0.701** | 0.697 | 0.824 | 0.741 (0.719) | pq 0.105, ruling 0.954, faq 0.959 | 0.793 | w=1.0 0.613, w=5.0 0.645, w=10.0 0.653 |
| pooled | notype-nobge | logreg | 381 (29) | 10 / 0.03 (0.765: 0.786 / 0.745) | **0.611** (0.486 / 0.886) | **0.674** | 0.659 | 0.804 | 0.748 (0.731) | pq 0.073, ruling 0.978, faq 0.973 | 0.790 | w=1.0 0.593, w=5.0 0.634, w=10.0 0.611 |
| pooled | small | lgbm-tiny | 381 (29) | 5 / – (0.772: 0.790 / 0.754) | **0.647** (0.543 / 0.886) | **0.694** | 0.665 | 0.809 | 0.748 (0.731) | pq 0.094, ruling 0.976, faq 0.955 | 0.802 | w=1.0 0.599, w=5.0 0.647, w=10.0 0.655 |
| pooled | small | logreg | 381 (29) | 10 / 0.03 (0.769: 0.791 / 0.748) | **0.670** (0.571 / 0.852) | **0.682** | 0.684 | 0.714 | 0.745 (0.735) | pq 0.066, ruling 0.982, faq 0.957 | 0.790 | w=1.0 0.638, w=5.0 0.676, w=10.0 0.670 |
| pooled-scored | notype | lgbm-tiny | 135 (29) | 5 / – (0.775: 0.782 / 0.767) | **0.667** (0.571 / 0.900) | **0.711** | 0.684 | 0.854 | 0.730 (0.705) | pq 0.093, ruling 0.948, faq 0.939 | 0.783 | w=1.0 0.643, w=5.0 0.667, w=10.0 0.658 |
| pooled-scored | notype | logreg | 135 (29) | 10 / 0.1 (0.797: 0.787 / 0.807) | **0.653** (0.543 / 0.914) | **0.691** | 0.689 | 0.809 | 0.742 (0.734) | pq 0.046, ruling 0.976, faq 0.980 | 0.783 | w=1.0 0.670, w=5.0 0.659, w=10.0 0.653 |
| pooled-scored | withtype | lgbm-tiny | 135 (29) | 5 / – (0.780: 0.783 / 0.777) | **0.635** (0.514 / 0.914) | **0.693** | 0.684 | 0.860 | 0.733 (0.706) | pq 0.098, ruling 0.951, faq 0.939 | 0.786 | w=1.0 0.648, w=5.0 0.635, w=10.0 0.648 |
| pooled-scored | withtype | logreg | 135 (29) | 1 / 0.03 (0.788: 0.827 / 0.750) | **0.605** (0.486 / 0.871) | **0.663** | 0.605 | 0.758 | 0.754 (0.743) | pq 0.108, ruling 0.974, faq 0.969 | 0.800 | w=1.0 0.605, w=5.0 0.613, w=10.0 0.589 |
| pooled-scored | notype-nogate | lgbm-tiny | 135 (29) | 5 / – (0.779: 0.780 / 0.778) | **0.654** (0.543 / 0.914) | **0.710** | 0.698 | 0.854 | 0.723 (0.697) | pq 0.092, ruling 0.936, faq 0.936 | 0.771 | w=1.0 0.642, w=5.0 0.654, w=10.0 0.660 |
| pooled-scored | notype-nogate | logreg | 135 (29) | 10 / 0.03 (0.774: 0.746 / 0.802) | **0.641** (0.514 / 0.871) | **0.699** | 0.681 | 0.786 | 0.712 (0.689) | pq 0.056, ruling 0.936, faq 0.927 | 0.750 | w=1.0 0.654, w=5.0 0.663, w=10.0 0.641 |
| pooled-scored | notype-nobge | lgbm-tiny | 135 (29) | 1 / – (0.771: 0.809 / 0.733) | **0.629** (0.514 / 0.933) | **0.676** | 0.659 | 0.788 | 0.750 (0.728) | pq 0.104, ruling 0.972, faq 0.959 | 0.799 | w=1.0 0.629, w=5.0 0.643, w=10.0 0.645 |
| pooled-scored | notype-nobge | logreg | 135 (29) | 10 / 0.03 (0.799: 0.795 / 0.804) | **0.604** (0.457 / 0.900) | **0.671** | 0.659 | 0.807 | 0.747 (0.724) | pq 0.058, ruling 0.982, faq 0.974 | 0.787 | w=1.0 0.625, w=5.0 0.614, w=10.0 0.604 |
| pooled-scored | small | lgbm-tiny | 135 (29) | 10 / – (0.775: 0.798 / 0.753) | **0.644** (0.514 / 0.914) | **0.691** | 0.696 | 0.860 | 0.722 (0.693) | pq 0.073, ruling 0.942, faq 0.938 | 0.769 | w=1.0 0.617, w=5.0 0.648, w=10.0 0.644 |
| pooled-scored | small | logreg | 135 (29) | 5 / 0.1 (0.784: 0.792 / 0.776) | **0.659** (0.543 / 0.895) | **0.683** | 0.674 | 0.777 | 0.741 (0.733) | pq 0.056, ruling 0.988, faq 0.939 | 0.780 | w=1.0 0.680, w=5.0 0.659, w=10.0 0.650 |

Nested-CV grid (criterion = mean of held-out mined and held-out human-train MRR):

* `lgbm-tiny__notype__pooled`: w=1.0: 0.765 (0.799/0.732); w=5.0: 0.786 (0.789/0.784); w=10.0: 0.779 (0.775/0.783)
* `logreg__notype__pooled`: w=1.0,C=0.03: 0.748 (0.794/0.702); w=1.0,C=0.1: 0.758 (0.792/0.725); w=1.0,C=0.3: 0.749 (0.787/0.710); w=1.0,C=1.0: 0.754 (0.787/0.722); w=1.0,C=3.0: 0.757 (0.786/0.729); w=5.0,C=0.03: 0.771 (0.795/0.747); w=5.0,C=0.1: 0.769 (0.793/0.745); w=5.0,C=0.3: 0.769 (0.790/0.748); w=5.0,C=1.0: 0.767 (0.786/0.748); w=5.0,C=3.0: 0.765 (0.782/0.748); w=10.0,C=0.03: 0.776 (0.793/0.758); w=10.0,C=0.1: 0.771 (0.784/0.757); w=10.0,C=0.3: 0.768 (0.779/0.757); w=10.0,C=1.0: 0.770 (0.783/0.756); w=10.0,C=3.0: 0.770 (0.783/0.757)
* `lgbm-tiny__withtype__pooled`: w=1.0: 0.781 (0.809/0.752); w=5.0: 0.778 (0.793/0.763); w=10.0: 0.782 (0.782/0.782)
* `logreg__withtype__pooled`: w=1.0,C=0.03: 0.735 (0.805/0.664); w=1.0,C=0.1: 0.728 (0.802/0.654); w=1.0,C=0.3: 0.709 (0.798/0.620); w=1.0,C=1.0: 0.698 (0.798/0.598); w=1.0,C=3.0: 0.694 (0.797/0.592); w=5.0,C=0.03: 0.754 (0.797/0.710); w=5.0,C=0.1: 0.730 (0.796/0.664); w=5.0,C=0.3: 0.725 (0.796/0.654); w=5.0,C=1.0: 0.715 (0.795/0.636); w=5.0,C=3.0: 0.715 (0.798/0.632); w=10.0,C=0.03: 0.757 (0.802/0.711); w=10.0,C=0.1: 0.741 (0.797/0.684); w=10.0,C=0.3: 0.744 (0.793/0.695); w=10.0,C=1.0: 0.730 (0.792/0.668); w=10.0,C=3.0: 0.729 (0.791/0.668)
* `lgbm-tiny__notype-nogate__pooled`: w=1.0: 0.766 (0.778/0.755); w=5.0: 0.777 (0.774/0.781); w=10.0: 0.774 (0.765/0.782)
* `logreg__notype-nogate__pooled`: w=1.0,C=0.03: 0.734 (0.738/0.729); w=1.0,C=0.1: 0.732 (0.736/0.727); w=1.0,C=0.3: 0.732 (0.738/0.726); w=1.0,C=1.0: 0.730 (0.733/0.726); w=1.0,C=3.0: 0.729 (0.732/0.726); w=5.0,C=0.03: 0.740 (0.749/0.731); w=5.0,C=0.1: 0.737 (0.743/0.731); w=5.0,C=0.3: 0.734 (0.740/0.729); w=5.0,C=1.0: 0.732 (0.736/0.728); w=5.0,C=3.0: 0.732 (0.735/0.728); w=10.0,C=0.03: 0.754 (0.752/0.756); w=10.0,C=0.1: 0.746 (0.749/0.743); w=10.0,C=0.3: 0.741 (0.740/0.741); w=10.0,C=1.0: 0.738 (0.735/0.740); w=10.0,C=3.0: 0.737 (0.735/0.740)
* `lgbm-tiny__notype-nobge__pooled`: w=1.0: 0.766 (0.799/0.734); w=5.0: 0.776 (0.788/0.763); w=10.0: 0.780 (0.778/0.782)
* `logreg__notype-nobge__pooled`: w=1.0,C=0.03: 0.728 (0.791/0.664); w=1.0,C=0.1: 0.727 (0.789/0.664); w=1.0,C=0.3: 0.715 (0.783/0.646); w=1.0,C=1.0: 0.723 (0.783/0.662); w=1.0,C=3.0: 0.725 (0.783/0.667); w=5.0,C=0.03: 0.761 (0.790/0.732); w=5.0,C=0.1: 0.756 (0.784/0.729); w=5.0,C=0.3: 0.755 (0.782/0.728); w=5.0,C=1.0: 0.750 (0.779/0.722); w=5.0,C=3.0: 0.751 (0.780/0.722); w=10.0,C=0.03: 0.765 (0.786/0.745); w=10.0,C=0.1: 0.764 (0.783/0.745); w=10.0,C=0.3: 0.761 (0.782/0.740); w=10.0,C=1.0: 0.759 (0.781/0.737); w=10.0,C=3.0: 0.759 (0.782/0.736)
* `lgbm-tiny__small__pooled`: w=1.0: 0.750 (0.798/0.702); w=5.0: 0.772 (0.790/0.754); w=10.0: 0.770 (0.784/0.757)
* `logreg__small__pooled`: w=1.0,C=0.03: 0.745 (0.802/0.688); w=1.0,C=0.1: 0.740 (0.798/0.682); w=1.0,C=0.3: 0.741 (0.799/0.682); w=1.0,C=1.0: 0.741 (0.799/0.682); w=1.0,C=3.0: 0.740 (0.799/0.681); w=5.0,C=0.03: 0.754 (0.804/0.705); w=5.0,C=0.1: 0.754 (0.804/0.704); w=5.0,C=0.3: 0.754 (0.804/0.704); w=5.0,C=1.0: 0.753 (0.802/0.704); w=5.0,C=3.0: 0.754 (0.803/0.704); w=10.0,C=0.03: 0.769 (0.791/0.748); w=10.0,C=0.1: 0.768 (0.791/0.746); w=10.0,C=0.3: 0.768 (0.790/0.746); w=10.0,C=1.0: 0.768 (0.790/0.746); w=10.0,C=3.0: 0.768 (0.790/0.746)
* `lgbm-tiny__notype__pooled-scored`: w=1.0: 0.769 (0.804/0.735); w=5.0: 0.775 (0.782/0.767); w=10.0: 0.762 (0.764/0.760)
* `logreg__notype__pooled-scored`: w=1.0,C=0.03: 0.783 (0.817/0.750); w=1.0,C=0.1: 0.781 (0.808/0.754); w=1.0,C=0.3: 0.777 (0.805/0.748); w=1.0,C=1.0: 0.768 (0.800/0.736); w=1.0,C=3.0: 0.767 (0.798/0.736); w=5.0,C=0.03: 0.781 (0.795/0.767); w=5.0,C=0.1: 0.778 (0.797/0.759); w=5.0,C=0.3: 0.786 (0.797/0.775); w=5.0,C=1.0: 0.786 (0.796/0.775); w=5.0,C=3.0: 0.788 (0.800/0.775); w=10.0,C=0.03: 0.796 (0.788/0.804); w=10.0,C=0.1: 0.797 (0.787/0.807); w=10.0,C=0.3: 0.794 (0.793/0.796); w=10.0,C=1.0: 0.782 (0.787/0.778); w=10.0,C=3.0: 0.776 (0.791/0.760)
* `lgbm-tiny__withtype__pooled-scored`: w=1.0: 0.771 (0.812/0.731); w=5.0: 0.780 (0.783/0.777); w=10.0: 0.772 (0.766/0.778)
* `logreg__withtype__pooled-scored`: w=1.0,C=0.03: 0.788 (0.827/0.750); w=1.0,C=0.1: 0.771 (0.829/0.714); w=1.0,C=0.3: 0.751 (0.818/0.684); w=1.0,C=1.0: 0.737 (0.815/0.658); w=1.0,C=3.0: 0.750 (0.814/0.687); w=5.0,C=0.03: 0.784 (0.809/0.760); w=5.0,C=0.1: 0.776 (0.803/0.750); w=5.0,C=0.3: 0.778 (0.808/0.748); w=5.0,C=1.0: 0.766 (0.807/0.725); w=5.0,C=3.0: 0.767 (0.807/0.727); w=10.0,C=0.03: 0.786 (0.798/0.774); w=10.0,C=0.1: 0.782 (0.800/0.764); w=10.0,C=0.3: 0.770 (0.795/0.745); w=10.0,C=1.0: 0.769 (0.796/0.743); w=10.0,C=3.0: 0.769 (0.794/0.745)
* `lgbm-tiny__notype-nogate__pooled-scored`: w=1.0: 0.764 (0.792/0.737); w=5.0: 0.779 (0.780/0.778); w=10.0: 0.762 (0.764/0.761)
* `logreg__notype-nogate__pooled-scored`: w=1.0,C=0.03: 0.764 (0.768/0.761); w=1.0,C=0.1: 0.758 (0.762/0.753); w=1.0,C=0.3: 0.748 (0.761/0.736); w=1.0,C=1.0: 0.737 (0.739/0.735); w=1.0,C=3.0: 0.734 (0.734/0.735); w=5.0,C=0.03: 0.771 (0.760/0.783); w=5.0,C=0.1: 0.760 (0.759/0.761); w=5.0,C=0.3: 0.760 (0.760/0.760); w=5.0,C=1.0: 0.759 (0.760/0.758); w=5.0,C=3.0: 0.757 (0.755/0.758); w=10.0,C=0.03: 0.774 (0.746/0.802); w=10.0,C=0.1: 0.773 (0.758/0.788); w=10.0,C=0.3: 0.769 (0.757/0.781); w=10.0,C=1.0: 0.768 (0.757/0.780); w=10.0,C=3.0: 0.767 (0.757/0.777)
* `lgbm-tiny__notype-nobge__pooled-scored`: w=1.0: 0.771 (0.809/0.733); w=5.0: 0.761 (0.787/0.734); w=10.0: 0.756 (0.767/0.746)
* `logreg__notype-nobge__pooled-scored`: w=1.0,C=0.03: 0.761 (0.810/0.712); w=1.0,C=0.1: 0.757 (0.802/0.711); w=1.0,C=0.3: 0.762 (0.798/0.726); w=1.0,C=1.0: 0.756 (0.788/0.725); w=1.0,C=3.0: 0.758 (0.790/0.725); w=5.0,C=0.03: 0.779 (0.802/0.757); w=5.0,C=0.1: 0.779 (0.795/0.763); w=5.0,C=0.3: 0.776 (0.796/0.756); w=5.0,C=1.0: 0.772 (0.792/0.753); w=5.0,C=3.0: 0.778 (0.790/0.766); w=10.0,C=0.03: 0.799 (0.795/0.804); w=10.0,C=0.1: 0.786 (0.795/0.777); w=10.0,C=0.3: 0.788 (0.795/0.781); w=10.0,C=1.0: 0.780 (0.784/0.776); w=10.0,C=3.0: 0.778 (0.785/0.770)
* `lgbm-tiny__small__pooled-scored`: w=1.0: 0.767 (0.808/0.726); w=5.0: 0.773 (0.793/0.754); w=10.0: 0.775 (0.798/0.753)
* `logreg__small__pooled-scored`: w=1.0,C=0.03: 0.753 (0.812/0.695); w=1.0,C=0.1: 0.755 (0.814/0.696); w=1.0,C=0.3: 0.753 (0.812/0.695); w=1.0,C=1.0: 0.755 (0.814/0.696); w=1.0,C=3.0: 0.751 (0.805/0.696); w=5.0,C=0.03: 0.783 (0.793/0.774); w=5.0,C=0.1: 0.784 (0.792/0.776); w=5.0,C=0.3: 0.783 (0.788/0.778); w=5.0,C=1.0: 0.780 (0.782/0.778); w=5.0,C=3.0: 0.778 (0.779/0.778); w=10.0,C=0.03: 0.782 (0.784/0.780); w=10.0,C=0.1: 0.781 (0.779/0.783); w=10.0,C=0.3: 0.773 (0.779/0.766); w=10.0,C=1.0: 0.767 (0.769/0.766); w=10.0,C=3.0: 0.767 (0.768/0.765)

Top features (fit A):

* `lgbm-tiny__notype__mined`: lex13_norm +0.327, ov8_max +0.193, convex05_logrank +0.105, ov3_max +0.098, title_overlap +0.064, title_overlap_n +0.063, log_doc_len +0.039, lex13_logrank +0.036, bm25_logrank +0.024, log_n_chunks +0.014
* `logreg__notype__mined`: ov8_max +0.890, title_overlap_n +0.686, q_verbatim -0.650, is_yearly_edition +0.525, log_doc_len -0.503, e5_logrank -0.388, log_n_chunks -0.310, lex13_logrank -0.305, convex05 +0.302, convex05_logrank -0.276
* `lgbm-tiny__withtype__mined`: lex13_norm +0.262, ov8_max +0.190, convex05_logrank +0.118, ov3_max +0.112, type=code_et_legislation +0.109, bm25_logrank +0.041, lex13_logrank +0.039, title_overlap +0.038, log_doc_len +0.025, title_overlap_n +0.024
* `logreg__withtype__mined`: type=code_et_legislation +1.022, ov8_max +0.886, q_verbatim -0.481, type=decisions_anticipees_l_24_12_2002 -0.417, e5_logrank -0.408, title_overlap_n +0.398, log_doc_len -0.364, type=questions_parlementaires -0.345, convex05 +0.337, lex13_logrank -0.334
* `lgbm-tiny__notype-nogate__mined`: lex13_norm +0.452, convex05_logrank +0.152, bm25doc_norm +0.072, title_overlap_n +0.065, title_overlap +0.063, lex13_logrank +0.048, log_doc_len +0.045, bm25_norm +0.031, bm25_logrank +0.030, bm25doc_logrank +0.012
* `logreg__notype-nogate__mined`: convex05 +2.316, log_doc_len -1.803, lex13_logrank -1.314, e5_logrank -1.256, n_legs_top30 -1.219, log_n_chunks +1.131, rrf60 -1.067, bm25_norm +0.917, bm25doc_logrank -0.853, e5_norm -0.795
* `lgbm-tiny__notype-nobge__mined`: lex13_norm +0.294, ov8_max +0.198, convex05_logrank +0.110, ov3_max +0.108, title_overlap +0.067, title_overlap_n +0.059, log_doc_len +0.046, bm25_logrank +0.039, lex13_logrank +0.033, log_n_chunks +0.008
* `logreg__notype-nobge__mined`: ov8_max +0.861, title_overlap_n +0.677, q_verbatim -0.641, is_yearly_edition +0.535, log_doc_len -0.507, e5_logrank -0.409, lex13_logrank -0.330, convex05 +0.322, log_n_chunks -0.307, convex05_logrank -0.280
* `lgbm-tiny__small__mined`: lex13_norm +0.389, ov8_max +0.327, title_overlap +0.119, bm25_norm +0.065, log_doc_len +0.055, convex05 +0.025, bm25doc_norm +0.011, e5_norm +0.004, is_yearly_edition +0.002, bge_norm_x_verbatim +0.001
* `logreg__small__mined`: ov8_max +1.103, q_verbatim -0.968, log_doc_len -0.883, convex05 +0.797, is_yearly_edition +0.695, bge_norm +0.669, title_overlap +0.536, bge_norm_x_loglen -0.445, bm25doc_norm -0.358, bm25_norm +0.323
* `lgbm-tiny__notype__pooled`: lex13_norm +0.406, convex05_logrank +0.165, bm25doc_logrank +0.108, title_overlap_n +0.080, lex13_logrank +0.066, bm25doc_norm +0.065, bm25_norm +0.018, title_overlap +0.018, log_doc_len +0.017, ov3_max +0.013
* `logreg__notype__pooled`: title_overlap_n +0.889, ov8_max +0.761, q_verbatim -0.495, convex05_logrank -0.492, bm25doc_logrank -0.461, e5_logrank -0.453, lex13_logrank -0.450, is_yearly_edition +0.439, bge_norm +0.404, bm25doc_norm +0.358
* `lgbm-tiny__withtype__pooled`: lex13_norm +0.330, convex05_logrank +0.156, bm25doc_logrank +0.141, bm25doc_norm +0.096, lex13_logrank +0.067, title_overlap_n +0.062, bm25_norm +0.034, type=code_et_legislation +0.016, bm25_logrank +0.016, bge_norm +0.013
* `logreg__withtype__pooled`: title_overlap_n +0.798, ov8_max +0.737, type=questions_parlementaires -0.557, bm25doc_logrank -0.501, convex05_logrank -0.482, lex13_logrank -0.472, type=code_et_legislation +0.458, q_verbatim -0.448, bge_norm_x_verbatim -0.431, bge_norm +0.417
* `lgbm-tiny__notype-nogate__pooled`: lex13_norm +0.392, convex05_logrank +0.186, bm25doc_logrank +0.107, title_overlap_n +0.083, bm25doc_norm +0.072, lex13_logrank +0.047, bm25_norm +0.021, title_overlap +0.017, log_doc_len +0.016, convex05 +0.015
* `logreg__notype-nogate__pooled`: title_overlap_n +0.762, lex13_logrank -0.721, bm25doc_logrank -0.645, e5_logrank -0.597, convex05_logrank -0.518, bm25_norm +0.514, is_yearly_edition +0.471, convex05 +0.451, rrf60 -0.434, bm25doc_score -0.428
* `lgbm-tiny__notype-nobge__pooled`: lex13_norm +0.348, bm25doc_logrank +0.182, convex05_logrank +0.145, bm25doc_norm +0.081, title_overlap_n +0.070, lex13_logrank +0.069, bm25_norm +0.021, doc_year +0.017, bm25_logrank +0.010, log_doc_len +0.009
* `logreg__notype-nobge__pooled`: title_overlap_n +0.908, ov8_max +0.659, lex13_logrank -0.585, e5_logrank -0.574, convex05_logrank -0.509, bm25doc_logrank -0.497, q_verbatim -0.485, ov8_any -0.438, bm25doc_norm +0.432, bm25doc_score -0.403
* `lgbm-tiny__small__pooled`: lex13_norm +0.511, bm25doc_norm +0.161, bm25_norm +0.090, title_overlap +0.083, convex05 +0.063, log_doc_len +0.026, bge_norm +0.018, ov8_max +0.017, e5_norm +0.016, bge_max +0.009
* `logreg__small__pooled`: q_verbatim -0.757, ov8_max +0.752, bge_norm +0.618, bge_norm_x_verbatim -0.526, e5_norm +0.433, is_yearly_edition +0.405, bm25doc_norm +0.367, title_overlap +0.313, bge_missing +0.270, bge_qcov -0.255
* `lgbm-tiny__notype__pooled-scored`: lex13_norm +0.245, bm25doc_logrank +0.217, bm25doc_norm +0.148, bge_norm +0.115, convex05_logrank +0.063, lex13_logrank +0.046, title_overlap_n +0.044, doc_year +0.023, bge_max +0.023, bm25_norm +0.015
* `logreg__notype__pooled-scored`: title_overlap_n +0.938, bm25doc_norm +0.919, q_len_words +0.837, bge_norm +0.747, convex05_logrank -0.733, bge_norm_x_verbatim -0.690, bm25doc_logrank -0.661, rrf60 -0.618, doc_year +0.557, ov8_max +0.503
* `lgbm-tiny__withtype__pooled-scored`: lex13_norm +0.241, bm25doc_logrank +0.215, bm25doc_norm +0.145, bge_norm +0.093, lex13_logrank +0.087, convex05_logrank +0.049, title_overlap_n +0.042, bge_max +0.029, doc_year +0.021, e5_max +0.013
* `logreg__withtype__pooled-scored`: type=code_et_legislation +0.557, bge_norm_x_verbatim -0.453, title_overlap_n +0.447, ov8_max +0.436, bge_logrank -0.323, q_verbatim -0.315, type=questions_parlementaires -0.292, lex13_logrank -0.287, log_doc_len -0.278, e5_logrank -0.271
* `lgbm-tiny__notype-nogate__pooled-scored`: lex13_norm +0.237, bm25doc_logrank +0.198, bm25doc_norm +0.162, bge_norm +0.119, lex13_logrank +0.073, convex05_logrank +0.060, title_overlap_n +0.046, doc_year +0.020, bge_max +0.020, e5_max +0.012
* `logreg__notype-nogate__pooled-scored`: title_overlap_n +0.668, bm25doc_logrank -0.614, bm25doc_norm +0.578, convex05_logrank -0.460, bge_logrank -0.425, best_pos_bm25 -0.425, doc_year +0.406, bge_norm +0.386, lex13_logrank -0.374, bm25_top30 -0.366
* `lgbm-tiny__notype-nobge__pooled-scored`: lex13_norm +0.361, convex05_logrank +0.171, title_overlap_n +0.087, bm25doc_norm +0.075, lex13_logrank +0.071, bm25doc_logrank +0.063, bm25_logrank +0.058, bm25_norm +0.032, log_doc_len +0.029, ov3_max +0.020
* `logreg__notype-nobge__pooled-scored`: title_overlap_n +0.742, bm25doc_logrank -0.665, bm25doc_norm +0.639, convex05_logrank -0.571, lex13_logrank -0.487, doc_year +0.466, q_verbatim -0.463, best_pos_bm25 -0.430, e5_logrank -0.429, ov8_max +0.408
* `lgbm-tiny__small__pooled-scored`: bm25doc_norm +0.355, lex13_norm +0.298, bge_norm +0.149, bge_max +0.071, bge_norm_x_loglen +0.032, e5_norm +0.027, convex05 +0.023, title_overlap +0.023, log_doc_len +0.016, bm25_norm +0.003
* `logreg__small__pooled-scored`: bge_norm +1.071, bge_norm_x_verbatim -1.065, bm25doc_norm +0.735, e5_norm +0.604, bge_norm_x_ov8 +0.520, lex13_norm +0.428, q_len_words +0.353, q_verbatim -0.349, is_yearly_edition +0.297, title_overlap +0.281

Length-gate diagnostics (fit A, tree-SHAP contribution of the bge features; scored questions, human + mined val):

| model | words | n rows (q) | mean abs bge contrib | share of abs contrib | slope on bge_norm | Spearman | PD(bge_norm 0→1) | PD range |
|---|---|--:|--:|--:|--:|--:|---|--:|
| lgbm-tiny__notype__pooled | 0–25 | 151 (16) | 0.102 | 0.040 | +0.279 | +0.89 | -0.83 / -0.82 / -0.82 / -0.63 / -0.49 | +0.331 |
| lgbm-tiny__notype__pooled | 26–50 | 849 (75) | 0.116 | 0.048 | +0.303 | +0.91 | -0.93 / -0.92 / -0.92 / -0.72 / -0.58 | +0.348 |
| lgbm-tiny__notype__pooled | 51–100 | 792 (46) | 0.135 | 0.067 | +0.293 | +0.88 | -1.45 / -1.44 / -1.44 / -1.24 / -1.10 | +0.349 |
| lgbm-tiny__notype__pooled | 101–∞ | 341 (21) | 0.141 | 0.069 | +0.314 | +0.91 | -1.42 / -1.41 / -1.41 / -1.21 / -1.07 | +0.348 |
| lgbm-tiny__withtype__pooled | 0–25 | 151 (16) | 0.173 | 0.064 | +0.469 | +0.94 | -0.90 / -0.88 / -0.86 / -0.65 / -0.33 | +0.567 |
| lgbm-tiny__withtype__pooled | 26–50 | 849 (75) | 0.190 | 0.071 | +0.489 | +0.94 | -0.93 / -0.91 / -0.90 / -0.68 / -0.36 | +0.579 |
| lgbm-tiny__withtype__pooled | 51–100 | 792 (46) | 0.226 | 0.097 | +0.480 | +0.91 | -1.37 / -1.35 / -1.33 / -1.11 / -0.79 | +0.586 |
| lgbm-tiny__withtype__pooled | 101–∞ | 341 (21) | 0.238 | 0.101 | +0.511 | +0.93 | -1.11 / -1.09 / -1.07 / -0.84 / -0.54 | +0.573 |
| lgbm-tiny__notype__pooled-scored | 0–25 | 151 (16) | 0.365 | 0.134 | +0.913 | +0.95 | -1.07 / -1.05 / -1.03 / -0.72 / -0.17 | +0.903 |
| lgbm-tiny__notype__pooled-scored | 26–50 | 849 (75) | 0.370 | 0.134 | +0.900 | +0.94 | -1.04 / -1.03 / -1.01 / -0.71 / -0.14 | +0.905 |
| lgbm-tiny__notype__pooled-scored | 51–100 | 792 (46) | 0.416 | 0.164 | +0.837 | +0.91 | -1.30 / -1.28 / -1.27 / -0.96 / -0.39 | +0.911 |
| lgbm-tiny__notype__pooled-scored | 101–∞ | 341 (21) | 0.440 | 0.164 | +0.873 | +0.93 | -1.02 / -1.01 / -0.99 / -0.69 / -0.12 | +0.905 |
| lgbm-tiny__withtype__pooled-scored | 0–25 | 151 (16) | 0.391 | 0.141 | +0.960 | +0.94 | -1.05 / -1.05 / -1.04 / -0.74 / -0.17 | +0.881 |
| lgbm-tiny__withtype__pooled-scored | 26–50 | 849 (75) | 0.391 | 0.139 | +0.936 | +0.94 | -1.02 / -1.01 / -1.00 / -0.71 / -0.14 | +0.883 |
| lgbm-tiny__withtype__pooled-scored | 51–100 | 792 (46) | 0.434 | 0.168 | +0.856 | +0.92 | -1.29 / -1.28 / -1.27 / -0.97 / -0.40 | +0.894 |
| lgbm-tiny__withtype__pooled-scored | 101–∞ | 341 (21) | 0.463 | 0.171 | +0.881 | +0.93 | -0.96 / -0.95 / -0.94 / -0.64 / -0.08 | +0.878 |

**Human VAL half – paired tests (Δ = exp-24 fit A − reference)**

| run | reference  Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 | Δ H@10 |
|---|---|:--|--:|--:|:--|--:|--:|
| ltr24__lgbm-tiny__notype__mined | vs bar_val (n=35, ref 0.665 → 0.604) | -0.061 [-0.167, +0.020] | 0.216 | 0.222 | 8/10/17 | -0.057 | -0.057 |
| ltr24__lgbm-tiny__notype__mined | vs bar_full (n=35, ref 0.659 → 0.604) | -0.054 [-0.162, +0.026] | 0.269 | 0.276 | 9/10/16 | -0.057 | -0.057 |
| ltr24__lgbm-tiny__notype__mined | vs exp14 (n=35, ref 0.634 → 0.604) | -0.030 [-0.137, +0.064] | 0.563 | 0.571 | 9/9/17 | -0.057 | -0.057 |
| ltr24__lgbm-tiny__notype__mined | vs exp14_cheap (n=35, ref 0.519 → 0.604) | +0.085 [+0.013, +0.190] | 0.067 | 0.066 | 13/7/15 | +0.086 | +0.086 |
| ltr24__lgbm-tiny__notype__mined | vs exp17 (n=35, ref 0.688 → 0.604) | -0.084 [-0.188, -0.010] | 0.074 | 0.073 | 6/10/19 | -0.086 | -0.086 |
| ltr24__lgbm-tiny__notype__mined | vs lex13 (n=35, ref 0.617 → 0.604) | -0.012 [-0.072, +0.047] | 0.690 | 0.686 | 6/9/20 | +0.000 | -0.057 |
| ltr24__lgbm-tiny__notype__mined | vs bm25_01 (n=35, ref 0.546 → 0.604) | +0.058 [-0.019, +0.167] | 0.215 | 0.220 | 11/9/15 | +0.057 | -0.029 |
| ltr24__lgbm-tiny__notype__mined | vs convex05 (n=35, ref 0.590 → 0.604) | +0.014 [-0.036, +0.072] | 0.623 | 0.639 | 8/9/18 | +0.029 | -0.029 |
| ltr24__lgbm-tiny__notype__mined | vs convex05+bge@20 (n=35, ref 0.649 → 0.604) | -0.045 [-0.153, +0.043] | 0.385 | 0.392 | 9/10/16 | -0.029 | -0.029 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.604) | -0.019 [-0.096, +0.036] | 0.583 | 0.609 | 7/8/20 | -0.029 | -0.057 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap (n=35, ref 0.609 → 0.604) | -0.005 [-0.054, +0.022] | 0.790 | 0.807 | 7/7/21 | -0.029 | -0.029 |
| ltr24__logreg__notype__mined | vs bar_val (n=35, ref 0.665 → 0.601) | -0.064 [-0.172, +0.040] | 0.263 | 0.266 | 7/13/15 | -0.057 | +0.000 |
| ltr24__logreg__notype__mined | vs bar_full (n=35, ref 0.659 → 0.601) | -0.058 [-0.166, +0.046] | 0.304 | 0.308 | 7/13/15 | -0.057 | +0.000 |
| ltr24__logreg__notype__mined | vs exp14 (n=35, ref 0.634 → 0.601) | -0.034 [-0.158, +0.095] | 0.616 | ~0.619 | 10/11/14 | -0.057 | +0.000 |
| ltr24__logreg__notype__mined | vs exp14_cheap (n=35, ref 0.519 → 0.601) | +0.082 [-0.042, +0.213] | 0.223 | ~0.226 | 15/9/11 | +0.086 | +0.143 |
| ltr24__logreg__notype__mined | vs exp17 (n=35, ref 0.688 → 0.601) | -0.087 [-0.189, +0.013] | 0.110 | 0.111 | 5/14/16 | -0.086 | -0.029 |
| ltr24__logreg__notype__mined | vs lex13 (n=35, ref 0.617 → 0.601) | -0.015 [-0.084, +0.058] | 0.679 | 0.685 | 7/9/19 | +0.000 | +0.000 |
| ltr24__logreg__notype__mined | vs bm25_01 (n=35, ref 0.546 → 0.601) | +0.055 [-0.035, +0.166] | 0.306 | ~0.319 | 13/9/13 | +0.057 | +0.029 |
| ltr24__logreg__notype__mined | vs convex05 (n=35, ref 0.590 → 0.601) | +0.011 [-0.079, +0.100] | 0.818 | ~0.817 | 11/10/14 | +0.029 | +0.029 |
| ltr24__logreg__notype__mined | vs convex05+bge@20 (n=35, ref 0.649 → 0.601) | -0.048 [-0.160, +0.062] | 0.417 | ~0.428 | 9/12/14 | -0.029 | +0.029 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.601) | -0.022 [-0.118, +0.063] | 0.645 | 0.656 | 11/7/17 | -0.029 | +0.000 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap (n=35, ref 0.609 → 0.601) | -0.008 [-0.113, +0.089] | 0.879 | 0.877 | 13/6/16 | -0.029 | +0.029 |
| ltr24__lgbm-tiny__withtype__mined | vs bar_val (n=35, ref 0.665 → 0.583) | -0.082 [-0.177, -0.014] | 0.057 | 0.054 | 5/10/20 | -0.086 | -0.057 |
| ltr24__lgbm-tiny__withtype__mined | vs bar_full (n=35, ref 0.659 → 0.583) | -0.076 [-0.172, -0.008] | 0.080 | 0.079 | 6/10/19 | -0.086 | -0.057 |
| ltr24__lgbm-tiny__withtype__mined | vs exp14 (n=35, ref 0.634 → 0.583) | -0.052 [-0.166, +0.054] | 0.377 | 0.382 | 8/12/15 | -0.086 | -0.057 |
| ltr24__lgbm-tiny__withtype__mined | vs exp14_cheap (n=35, ref 0.519 → 0.583) | +0.064 [-0.022, +0.175] | 0.213 | ~0.214 | 13/9/13 | +0.057 | +0.086 |
| ltr24__lgbm-tiny__withtype__mined | vs exp17 (n=35, ref 0.688 → 0.583) | **-0.105** [-0.200, -0.050] | 0.007 | 0.001 | 2/12/21 | -0.114 | -0.086 |
| ltr24__lgbm-tiny__withtype__mined | vs lex13 (n=35, ref 0.617 → 0.583) | -0.034 [-0.102, +0.032] | 0.341 | 0.346 | 6/13/16 | -0.029 | -0.057 |
| ltr24__lgbm-tiny__withtype__mined | vs bm25_01 (n=35, ref 0.546 → 0.583) | +0.037 [-0.036, +0.130] | 0.387 | ~0.397 | 11/10/14 | +0.029 | -0.029 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05 (n=35, ref 0.590 → 0.583) | -0.007 [-0.063, +0.044] | 0.795 | 0.801 | 8/9/18 | +0.000 | -0.029 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05+bge@20 (n=35, ref 0.649 → 0.583) | -0.066 [-0.163, +0.011] | 0.148 | 0.155 | 7/10/18 | -0.057 | -0.029 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.583) | -0.040 [-0.102, -0.011] | 0.066 | 0.044 | 5/9/21 | -0.057 | -0.057 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap (n=35, ref 0.609 → 0.583) | -0.026 [-0.088, +0.003] | 0.219 | 0.315 | 4/8/23 | -0.057 | -0.029 |
| ltr24__logreg__withtype__mined | vs bar_val (n=35, ref 0.665 → 0.477) | **-0.188** [-0.311, -0.084] | 0.003 | ~0.003 | 4/17/14 | -0.200 | -0.143 |
| ltr24__logreg__withtype__mined | vs bar_full (n=35, ref 0.659 → 0.477) | **-0.182** [-0.305, -0.076] | 0.005 | ~0.004 | 5/17/13 | -0.200 | -0.143 |
| ltr24__logreg__withtype__mined | vs exp14 (n=35, ref 0.634 → 0.477) | -0.157 [-0.305, -0.004] | 0.057 | ~0.058 | 10/16/9 | -0.200 | -0.143 |
| ltr24__logreg__withtype__mined | vs exp14_cheap (n=35, ref 0.519 → 0.477) | -0.042 [-0.182, +0.103] | 0.578 | ~0.575 | 12/16/7 | -0.057 | +0.000 |
| ltr24__logreg__withtype__mined | vs exp17 (n=35, ref 0.688 → 0.477) | **-0.211** [-0.329, -0.118] | 0.001 | 0.000 | 3/17/15 | -0.229 | -0.171 |
| ltr24__logreg__withtype__mined | vs lex13 (n=35, ref 0.617 → 0.477) | **-0.139** [-0.242, -0.048] | 0.010 | ~0.008 | 5/16/14 | -0.143 | -0.143 |
| ltr24__logreg__withtype__mined | vs bm25_01 (n=35, ref 0.546 → 0.477) | -0.069 [-0.179, +0.045] | 0.242 | ~0.242 | 9/14/12 | -0.086 | -0.114 |
| ltr24__logreg__withtype__mined | vs convex05 (n=35, ref 0.590 → 0.477) | -0.113 [-0.228, -0.007] | 0.058 | ~0.060 | 8/15/12 | -0.114 | -0.114 |
| ltr24__logreg__withtype__mined | vs convex05+bge@20 (n=35, ref 0.649 → 0.477) | **-0.172** [-0.298, -0.062] | 0.009 | ~0.009 | 6/15/14 | -0.171 | -0.114 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.477) | **-0.146** [-0.268, -0.049] | 0.014 | 0.012 | 6/14/15 | -0.171 | -0.143 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap (n=35, ref 0.609 → 0.477) | **-0.132** [-0.260, -0.024] | 0.039 | ~0.039 | 8/13/14 | -0.171 | -0.114 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bar_val (n=35, ref 0.665 → 0.608) | -0.057 [-0.150, +0.009] | 0.171 | 0.179 | 7/10/18 | -0.057 | -0.057 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bar_full (n=35, ref 0.659 → 0.608) | -0.051 [-0.145, +0.014] | 0.219 | 0.231 | 7/9/19 | -0.057 | -0.057 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp14 (n=35, ref 0.634 → 0.608) | -0.027 [-0.132, +0.064] | 0.607 | 0.617 | 9/9/17 | -0.057 | -0.057 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp14_cheap (n=35, ref 0.519 → 0.608) | +0.089 [+0.017, +0.193] | 0.052 | 0.049 | 14/5/16 | +0.086 | +0.086 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp17 (n=35, ref 0.688 → 0.608) | **-0.080** [-0.173, -0.024] | 0.039 | 0.030 | 4/11/20 | -0.086 | -0.086 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs lex13 (n=35, ref 0.617 → 0.608) | -0.009 [-0.067, +0.050] | 0.779 | 0.749 | 6/8/21 | +0.000 | -0.057 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bm25_01 (n=35, ref 0.546 → 0.608) | +0.062 [+0.003, +0.149] | 0.098 | 0.090 | 13/4/18 | +0.057 | -0.029 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05 (n=35, ref 0.590 → 0.608) | +0.018 [-0.006, +0.067] | 0.302 | 0.360 | 8/5/22 | +0.029 | -0.029 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05+bge@20 (n=35, ref 0.649 → 0.608) | -0.041 [-0.135, +0.033] | 0.356 | 0.368 | 8/10/17 | -0.029 | -0.029 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.608) | -0.015 [-0.083, +0.037] | 0.633 | 0.653 | 8/8/19 | -0.029 | -0.057 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap (n=35, ref 0.609 → 0.608) | -0.001 [-0.052, +0.026] | 0.951 | 0.955 | 9/5/21 | -0.029 | -0.029 |
| ltr24__logreg__notype-nogate__mined | vs bar_val (n=35, ref 0.665 → 0.622) | -0.042 [-0.135, +0.031] | 0.332 | 0.344 | 7/11/17 | -0.029 | -0.029 |
| ltr24__logreg__notype-nogate__mined | vs bar_full (n=35, ref 0.659 → 0.622) | -0.036 [-0.129, +0.037] | 0.401 | 0.415 | 7/11/17 | -0.029 | -0.029 |
| ltr24__logreg__notype-nogate__mined | vs exp14 (n=35, ref 0.634 → 0.622) | -0.012 [-0.113, +0.079] | 0.812 | 0.816 | 9/9/17 | -0.029 | -0.029 |
| ltr24__logreg__notype-nogate__mined | vs exp14_cheap (n=35, ref 0.519 → 0.622) | **+0.104** [+0.028, +0.211] | 0.033 | ~0.033 | 15/6/14 | +0.114 | +0.114 |
| ltr24__logreg__notype-nogate__mined | vs exp17 (n=35, ref 0.688 → 0.622) | -0.065 [-0.157, -0.001] | 0.105 | 0.104 | 5/12/18 | -0.057 | -0.057 |
| ltr24__logreg__notype-nogate__mined | vs lex13 (n=35, ref 0.617 → 0.622) | +0.006 [-0.043, +0.063] | 0.829 | 0.845 | 8/9/18 | +0.029 | -0.029 |
| ltr24__logreg__notype-nogate__mined | vs bm25_01 (n=35, ref 0.546 → 0.622) | +0.076 [-0.004, +0.185] | 0.118 | 0.119 | 13/6/16 | +0.086 | +0.000 |
| ltr24__logreg__notype-nogate__mined | vs convex05 (n=35, ref 0.590 → 0.622) | +0.032 [-0.024, +0.096] | 0.307 | 0.317 | 9/8/18 | +0.057 | +0.000 |
| ltr24__logreg__notype-nogate__mined | vs convex05+bge@20 (n=35, ref 0.649 → 0.622) | -0.026 [-0.123, +0.055] | 0.567 | 0.577 | 9/10/16 | +0.000 | +0.000 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.622) | -0.000 [-0.048, +0.048] | 0.991 | 0.993 | 10/5/20 | +0.000 | -0.029 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap (n=35, ref 0.609 → 0.622) | +0.013 [-0.035, +0.060] | 0.582 | 0.591 | 10/6/19 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bar_val (n=35, ref 0.665 → 0.610) | -0.055 [-0.162, +0.024] | 0.262 | 0.270 | 8/9/18 | -0.057 | -0.057 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bar_full (n=35, ref 0.659 → 0.610) | -0.049 [-0.157, +0.031] | 0.322 | 0.330 | 9/9/17 | -0.057 | -0.057 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp14 (n=35, ref 0.634 → 0.610) | -0.024 [-0.127, +0.068] | 0.631 | 0.641 | 9/10/16 | -0.057 | -0.057 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp14_cheap (n=35, ref 0.519 → 0.610) | +0.091 [+0.018, +0.196] | 0.053 | 0.051 | 13/6/16 | +0.086 | +0.086 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp17 (n=35, ref 0.688 → 0.610) | -0.078 [-0.182, -0.005] | 0.095 | 0.097 | 6/9/20 | -0.086 | -0.086 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs lex13 (n=35, ref 0.617 → 0.610) | -0.006 [-0.067, +0.053] | 0.838 | 0.832 | 8/8/19 | +0.000 | -0.057 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bm25_01 (n=35, ref 0.546 → 0.610) | +0.064 [-0.014, +0.172] | 0.175 | 0.181 | 12/8/15 | +0.057 | -0.029 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05 (n=35, ref 0.590 → 0.610) | +0.020 [-0.030, +0.076] | 0.472 | 0.488 | 8/7/20 | +0.029 | -0.029 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05+bge@20 (n=35, ref 0.649 → 0.610) | -0.039 [-0.149, +0.047] | 0.449 | 0.458 | 9/9/17 | -0.029 | -0.029 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.610) | -0.013 [-0.093, +0.044] | 0.716 | 0.736 | 8/7/20 | -0.029 | -0.057 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap (n=35, ref 0.609 → 0.610) | +0.001 [-0.046, +0.034] | 0.961 | 0.968 | 8/6/21 | -0.029 | -0.029 |
| ltr24__logreg__notype-nobge__mined | vs bar_val (n=35, ref 0.665 → 0.520) | **-0.144** [-0.271, -0.019] | 0.037 | ~0.038 | 8/16/11 | -0.143 | -0.057 |
| ltr24__logreg__notype-nobge__mined | vs bar_full (n=35, ref 0.659 → 0.520) | **-0.138** [-0.266, -0.013] | 0.044 | ~0.045 | 8/16/11 | -0.143 | -0.057 |
| ltr24__logreg__notype-nobge__mined | vs exp14 (n=35, ref 0.634 → 0.520) | -0.114 [-0.254, +0.015] | 0.113 | ~0.117 | 9/15/11 | -0.143 | -0.057 |
| ltr24__logreg__notype-nobge__mined | vs exp14_cheap (n=35, ref 0.519 → 0.520) | +0.001 [-0.135, +0.138] | 0.984 | ~0.984 | 13/14/8 | +0.000 | +0.086 |
| ltr24__logreg__notype-nobge__mined | vs exp17 (n=35, ref 0.688 → 0.520) | **-0.168** [-0.289, -0.048] | 0.012 | ~0.011 | 5/18/12 | -0.171 | -0.086 |
| ltr24__logreg__notype-nobge__mined | vs lex13 (n=35, ref 0.617 → 0.520) | **-0.096** [-0.188, -0.021] | 0.034 | ~0.032 | 8/14/13 | -0.086 | -0.057 |
| ltr24__logreg__notype-nobge__mined | vs bm25_01 (n=35, ref 0.546 → 0.520) | -0.026 [-0.141, +0.092] | 0.679 | ~0.675 | 11/14/10 | -0.029 | -0.029 |
| ltr24__logreg__notype-nobge__mined | vs convex05 (n=35, ref 0.590 → 0.520) | -0.070 [-0.182, +0.027] | 0.202 | ~0.199 | 9/15/11 | -0.057 | -0.029 |
| ltr24__logreg__notype-nobge__mined | vs convex05+bge@20 (n=35, ref 0.649 → 0.520) | -0.129 [-0.260, +0.003] | 0.071 | ~0.072 | 9/16/10 | -0.114 | -0.029 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.520) | -0.102 [-0.217, +0.003] | 0.080 | ~0.078 | 8/14/13 | -0.114 | -0.057 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap (n=35, ref 0.609 → 0.520) | -0.089 [-0.209, +0.016] | 0.137 | ~0.136 | 10/11/14 | -0.114 | -0.029 |
| ltr24__lgbm-tiny__small__mined | vs bar_val (n=35, ref 0.665 → 0.583) | -0.082 [-0.187, -0.007] | 0.085 | 0.085 | 7/11/17 | -0.086 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs bar_full (n=35, ref 0.659 → 0.583) | -0.076 [-0.181, -0.002] | 0.108 | 0.109 | 7/11/17 | -0.086 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs exp14 (n=35, ref 0.634 → 0.583) | -0.052 [-0.159, +0.045] | 0.338 | 0.346 | 9/11/15 | -0.086 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs exp14_cheap (n=35, ref 0.519 → 0.583) | +0.064 [-0.013, +0.168] | 0.183 | ~0.188 | 12/9/14 | +0.057 | +0.143 |
| ltr24__lgbm-tiny__small__mined | vs exp17 (n=35, ref 0.688 → 0.583) | **-0.105** [-0.209, -0.039] | 0.019 | 0.013 | 6/11/18 | -0.114 | -0.029 |
| ltr24__lgbm-tiny__small__mined | vs lex13 (n=35, ref 0.617 → 0.583) | -0.034 [-0.101, +0.032] | 0.330 | 0.335 | 6/12/17 | -0.029 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs bm25_01 (n=35, ref 0.546 → 0.583) | +0.036 [-0.033, +0.127] | 0.374 | 0.382 | 9/10/16 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__small__mined | vs convex05 (n=35, ref 0.590 → 0.583) | -0.008 [-0.055, +0.038] | 0.749 | 0.752 | 7/8/20 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__small__mined | vs convex05+bge@20 (n=35, ref 0.649 → 0.583) | -0.066 [-0.173, +0.015] | 0.187 | 0.192 | 9/10/16 | -0.057 | +0.029 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.583) | -0.040 [-0.121, +0.020] | 0.281 | 0.294 | 7/9/19 | -0.057 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap (n=35, ref 0.609 → 0.583) | -0.027 [-0.087, +0.010] | 0.277 | 0.295 | 6/9/20 | -0.057 | +0.029 |
| ltr24__logreg__small__mined | vs bar_val (n=35, ref 0.665 → 0.579) | -0.086 [-0.199, +0.015] | 0.133 | 0.135 | 7/12/16 | -0.057 | -0.114 |
| ltr24__logreg__small__mined | vs bar_full (n=35, ref 0.659 → 0.579) | -0.080 [-0.191, +0.019] | 0.157 | 0.160 | 7/11/17 | -0.057 | -0.114 |
| ltr24__logreg__small__mined | vs exp14 (n=35, ref 0.634 → 0.579) | -0.056 [-0.207, +0.100] | 0.492 | ~0.493 | 11/12/12 | -0.057 | -0.114 |
| ltr24__logreg__small__mined | vs exp14_cheap (n=35, ref 0.519 → 0.579) | +0.060 [-0.097, +0.210] | 0.461 | ~0.472 | 16/9/10 | +0.086 | +0.029 |
| ltr24__logreg__small__mined | vs exp17 (n=35, ref 0.688 → 0.579) | **-0.109** [-0.219, -0.016] | 0.048 | 0.046 | 5/13/17 | -0.086 | -0.143 |
| ltr24__logreg__small__mined | vs lex13 (n=35, ref 0.617 → 0.579) | -0.038 [-0.159, +0.081] | 0.550 | 0.553 | 8/11/16 | +0.000 | -0.114 |
| ltr24__logreg__small__mined | vs bm25_01 (n=35, ref 0.546 → 0.579) | +0.033 [-0.086, +0.155] | 0.608 | ~0.606 | 14/9/12 | +0.057 | -0.086 |
| ltr24__logreg__small__mined | vs convex05 (n=35, ref 0.590 → 0.579) | -0.011 [-0.121, +0.099] | 0.846 | ~0.840 | 11/10/14 | +0.029 | -0.086 |
| ltr24__logreg__small__mined | vs convex05+bge@20 (n=35, ref 0.649 → 0.579) | -0.070 [-0.186, +0.036] | 0.238 | 0.241 | 9/11/15 | -0.029 | -0.086 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.579) | -0.044 [-0.179, +0.077] | 0.514 | ~0.518 | 12/9/14 | -0.029 | -0.114 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap (n=35, ref 0.609 → 0.579) | -0.030 [-0.168, +0.096] | 0.665 | ~0.663 | 11/10/14 | -0.029 | -0.086 |
| ltr24__lgbm-tiny__notype__pooled | vs bar_val (n=35, ref 0.665 → 0.644) | -0.021 [-0.109, +0.047] | 0.602 | 0.617 | 7/9/19 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled | vs bar_full (n=35, ref 0.659 → 0.644) | -0.015 [-0.103, +0.050] | 0.708 | 0.717 | 7/7/21 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled | vs exp14 (n=35, ref 0.634 → 0.644) | +0.009 [-0.077, +0.090] | 0.833 | 0.831 | 10/7/18 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled | vs exp14_cheap (n=35, ref 0.519 → 0.644) | **+0.125** [+0.061, +0.228] | 0.005 | 0.001 | 16/4/15 | +0.143 | +0.171 |
| ltr24__lgbm-tiny__notype__pooled | vs exp17 (n=35, ref 0.688 → 0.644) | -0.044 [-0.131, +0.016] | 0.244 | 0.259 | 6/10/19 | -0.029 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled | vs lex13 (n=35, ref 0.617 → 0.644) | +0.027 [-0.004, +0.088] | 0.215 | 0.267 | 7/4/24 | +0.057 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled | vs bm25_01 (n=35, ref 0.546 → 0.644) | **+0.098** [+0.029, +0.202] | 0.031 | 0.030 | 18/2/15 | +0.114 | +0.057 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05 (n=35, ref 0.590 → 0.644) | **+0.054** [+0.018, +0.120] | 0.036 | 0.021 | 12/3/20 | +0.086 | +0.057 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05+bge@20 (n=35, ref 0.649 → 0.644) | -0.005 [-0.097, +0.069] | 0.909 | 0.913 | 10/8/17 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.644) | +0.021 [-0.043, +0.078] | 0.495 | 0.515 | 10/4/21 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap (n=35, ref 0.609 → 0.644) | +0.035 [+0.006, +0.084] | 0.078 | 0.072 | 11/3/21 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__notype__pooled | vs exp24 mined-only (same features) (n=35, ref 0.604 → 0.644) | +0.040 [+0.005, +0.098] | 0.091 | 0.094 | 11/3/21 | +0.057 | +0.086 |
| ltr24__logreg__notype__pooled | vs bar_val (n=35, ref 0.665 → 0.660) | -0.005 [-0.079, +0.071] | 0.902 | 0.903 | 7/10/18 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled | vs bar_full (n=35, ref 0.659 → 0.660) | +0.001 [-0.072, +0.075] | 0.971 | 0.972 | 7/10/18 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled | vs exp14 (n=35, ref 0.634 → 0.660) | +0.025 [-0.073, +0.137] | 0.645 | 0.650 | 9/9/17 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled | vs exp14_cheap (n=35, ref 0.519 → 0.660) | **+0.141** [+0.055, +0.261] | 0.011 | 0.009 | 15/5/15 | +0.143 | +0.143 |
| ltr24__logreg__notype__pooled | vs exp17 (n=35, ref 0.688 → 0.660) | -0.028 [-0.099, +0.028] | 0.396 | 0.410 | 7/9/19 | -0.029 | -0.029 |
| ltr24__logreg__notype__pooled | vs lex13 (n=35, ref 0.617 → 0.660) | +0.043 [-0.016, +0.139] | 0.266 | 0.273 | 7/5/23 | +0.057 | +0.000 |
| ltr24__logreg__notype__pooled | vs bm25_01 (n=35, ref 0.546 → 0.660) | **+0.114** [+0.023, +0.233] | 0.042 | ~0.040 | 14/7/14 | +0.114 | +0.029 |
| ltr24__logreg__notype__pooled | vs convex05 (n=35, ref 0.590 → 0.660) | +0.070 [+0.004, +0.159] | 0.090 | 0.093 | 12/5/18 | +0.086 | +0.029 |
| ltr24__logreg__notype__pooled | vs convex05+bge@20 (n=35, ref 0.649 → 0.660) | +0.011 [-0.066, +0.091] | 0.781 | 0.785 | 9/8/18 | +0.029 | +0.029 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.660) | +0.037 [-0.030, +0.114] | 0.325 | 0.345 | 9/5/21 | +0.029 | +0.000 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap (n=35, ref 0.609 → 0.660) | +0.051 [-0.008, +0.141] | 0.185 | 0.197 | 9/5/21 | +0.029 | +0.029 |
| ltr24__logreg__notype__pooled | vs exp24 mined-only (same features) (n=35, ref 0.601 → 0.660) | +0.059 [-0.027, +0.159] | 0.228 | 0.233 | 9/7/19 | +0.057 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled | vs bar_val (n=35, ref 0.665 → 0.647) | -0.018 [-0.111, +0.051] | 0.669 | 0.682 | 9/8/18 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled | vs bar_full (n=35, ref 0.659 → 0.647) | -0.011 [-0.105, +0.055] | 0.778 | 0.785 | 9/8/18 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp14 (n=35, ref 0.634 → 0.647) | +0.013 [-0.076, +0.093] | 0.778 | 0.778 | 10/5/20 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp14_cheap (n=35, ref 0.519 → 0.647) | **+0.128** [+0.065, +0.230] | 0.004 | 0.000 | 17/2/16 | +0.143 | +0.171 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp17 (n=35, ref 0.688 → 0.647) | -0.041 [-0.133, +0.021] | 0.299 | 0.317 | 7/9/19 | -0.029 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled | vs lex13 (n=35, ref 0.617 → 0.647) | +0.031 [-0.002, +0.091] | 0.178 | 0.214 | 8/4/23 | +0.057 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled | vs bm25_01 (n=35, ref 0.546 → 0.647) | **+0.101** [+0.032, +0.204] | 0.026 | 0.026 | 16/3/16 | +0.114 | +0.057 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05 (n=35, ref 0.590 → 0.647) | **+0.057** [+0.018, +0.121] | 0.031 | 0.021 | 15/1/19 | +0.086 | +0.057 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05+bge@20 (n=35, ref 0.649 → 0.647) | -0.002 [-0.097, +0.073] | 0.971 | 0.973 | 11/7/17 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.647) | +0.024 [-0.040, +0.081] | 0.436 | 0.453 | 10/5/20 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap (n=35, ref 0.609 → 0.647) | +0.038 [+0.007, +0.087] | 0.060 | 0.052 | 10/4/21 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp24 mined-only (same features) (n=35, ref 0.583 → 0.647) | **+0.064** [+0.019, +0.129] | 0.028 | 0.025 | 13/5/17 | +0.086 | +0.086 |
| ltr24__logreg__withtype__pooled | vs bar_val (n=35, ref 0.665 → 0.581) | -0.083 [-0.178, -0.004] | 0.072 | 0.072 | 5/13/17 | -0.086 | -0.029 |
| ltr24__logreg__withtype__pooled | vs bar_full (n=35, ref 0.659 → 0.581) | -0.077 [-0.173, +0.001] | 0.095 | 0.097 | 5/12/18 | -0.086 | -0.029 |
| ltr24__logreg__withtype__pooled | vs exp14 (n=35, ref 0.634 → 0.581) | -0.053 [-0.171, +0.056] | 0.374 | ~0.375 | 9/12/14 | -0.086 | -0.029 |
| ltr24__logreg__withtype__pooled | vs exp14_cheap (n=35, ref 0.519 → 0.581) | +0.063 [-0.005, +0.159] | 0.144 | 0.148 | 12/7/16 | +0.057 | +0.114 |
| ltr24__logreg__withtype__pooled | vs exp17 (n=35, ref 0.688 → 0.581) | **-0.106** [-0.213, -0.029] | 0.030 | 0.027 | 6/12/17 | -0.114 | -0.057 |
| ltr24__logreg__withtype__pooled | vs lex13 (n=35, ref 0.617 → 0.581) | -0.035 [-0.139, +0.056] | 0.491 | 0.496 | 8/11/16 | -0.029 | -0.029 |
| ltr24__logreg__withtype__pooled | vs bm25_01 (n=35, ref 0.546 → 0.581) | +0.035 [-0.072, +0.151] | 0.542 | ~0.547 | 12/10/13 | +0.029 | +0.000 |
| ltr24__logreg__withtype__pooled | vs convex05 (n=35, ref 0.590 → 0.581) | -0.009 [-0.120, +0.091] | 0.874 | ~0.871 | 13/9/13 | +0.000 | +0.000 |
| ltr24__logreg__withtype__pooled | vs convex05+bge@20 (n=35, ref 0.649 → 0.581) | -0.067 [-0.167, +0.018] | 0.166 | 0.169 | 8/11/16 | -0.057 | +0.000 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.581) | -0.041 [-0.139, +0.023] | 0.312 | 0.327 | 7/8/20 | -0.057 | -0.029 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap (n=35, ref 0.609 → 0.581) | -0.028 [-0.131, +0.053] | 0.561 | 0.566 | 9/7/19 | -0.057 | +0.000 |
| ltr24__logreg__withtype__pooled | vs exp24 mined-only (same features) (n=35, ref 0.477 → 0.581) | +0.104 [-0.003, +0.225] | 0.084 | ~0.082 | 16/6/13 | +0.114 | +0.114 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bar_val (n=35, ref 0.665 → 0.644) | -0.021 [-0.109, +0.047] | 0.609 | 0.622 | 7/9/19 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bar_full (n=35, ref 0.659 → 0.644) | -0.014 [-0.103, +0.050] | 0.716 | 0.723 | 8/8/19 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp14 (n=35, ref 0.634 → 0.644) | +0.010 [-0.077, +0.091] | 0.826 | 0.823 | 10/7/18 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp14_cheap (n=35, ref 0.519 → 0.644) | **+0.125** [+0.062, +0.229] | 0.004 | 0.001 | 16/4/15 | +0.143 | +0.171 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp17 (n=35, ref 0.688 → 0.644) | -0.043 [-0.131, +0.016] | 0.249 | 0.265 | 6/10/19 | -0.029 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs lex13 (n=35, ref 0.617 → 0.644) | +0.028 [-0.003, +0.088] | 0.210 | 0.262 | 7/4/24 | +0.057 | +0.029 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bm25_01 (n=35, ref 0.546 → 0.644) | **+0.098** [+0.029, +0.202] | 0.030 | 0.029 | 18/2/15 | +0.114 | +0.057 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05 (n=35, ref 0.590 → 0.644) | **+0.054** [+0.018, +0.120] | 0.035 | 0.020 | 12/3/20 | +0.086 | +0.057 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05+bge@20 (n=35, ref 0.649 → 0.644) | -0.004 [-0.097, +0.070] | 0.917 | 0.920 | 10/8/17 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.644) | +0.022 [-0.043, +0.079] | 0.487 | 0.507 | 10/4/21 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap (n=35, ref 0.609 → 0.644) | +0.035 [+0.006, +0.084] | 0.076 | 0.069 | 11/3/21 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp24 mined-only (same features) (n=35, ref 0.608 → 0.644) | +0.036 [+0.008, +0.098] | 0.090 | 0.073 | 9/4/22 | +0.057 | +0.086 |
| ltr24__logreg__notype-nogate__pooled | vs bar_val (n=35, ref 0.665 → 0.633) | -0.031 [-0.121, +0.051] | 0.484 | 0.491 | 7/11/17 | -0.029 | -0.029 |
| ltr24__logreg__notype-nogate__pooled | vs bar_full (n=35, ref 0.659 → 0.633) | -0.025 [-0.114, +0.056] | 0.569 | 0.576 | 7/11/17 | -0.029 | -0.029 |
| ltr24__logreg__notype-nogate__pooled | vs exp14 (n=35, ref 0.634 → 0.633) | -0.001 [-0.100, +0.090] | 0.984 | 0.985 | 9/9/17 | -0.029 | -0.029 |
| ltr24__logreg__notype-nogate__pooled | vs exp14_cheap (n=35, ref 0.519 → 0.633) | **+0.115** [+0.038, +0.222] | 0.020 | 0.017 | 15/5/15 | +0.114 | +0.114 |
| ltr24__logreg__notype-nogate__pooled | vs exp17 (n=35, ref 0.688 → 0.633) | -0.054 [-0.139, +0.012] | 0.170 | 0.175 | 7/10/18 | -0.057 | -0.057 |
| ltr24__logreg__notype-nogate__pooled | vs lex13 (n=35, ref 0.617 → 0.633) | +0.017 [-0.034, +0.078] | 0.564 | 0.574 | 7/7/21 | +0.029 | -0.029 |
| ltr24__logreg__notype-nogate__pooled | vs bm25_01 (n=35, ref 0.546 → 0.633) | +0.087 [+0.004, +0.195] | 0.081 | 0.077 | 12/7/16 | +0.086 | +0.000 |
| ltr24__logreg__notype-nogate__pooled | vs convex05 (n=35, ref 0.590 → 0.633) | +0.043 [-0.016, +0.110] | 0.195 | 0.204 | 11/4/20 | +0.057 | +0.000 |
| ltr24__logreg__notype-nogate__pooled | vs convex05+bge@20 (n=35, ref 0.649 → 0.633) | -0.015 [-0.107, +0.071] | 0.744 | 0.748 | 9/9/17 | +0.000 | +0.000 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.633) | +0.011 [-0.053, +0.064] | 0.717 | 0.732 | 9/6/20 | +0.000 | -0.029 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap (n=35, ref 0.609 → 0.633) | +0.024 [-0.027, +0.075] | 0.366 | 0.378 | 9/6/20 | +0.000 | +0.000 |
| ltr24__logreg__notype-nogate__pooled | vs exp24 mined-only (same features) (n=35, ref 0.622 → 0.633) | +0.011 [-0.007, +0.043] | 0.366 | 0.399 | 6/5/24 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bar_val (n=35, ref 0.665 → 0.653) | -0.011 [-0.117, +0.057] | 0.795 | 0.797 | 9/5/21 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bar_full (n=35, ref 0.659 → 0.653) | -0.005 [-0.112, +0.061] | 0.903 | 0.917 | 9/5/21 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp14 (n=35, ref 0.634 → 0.653) | +0.019 [-0.058, +0.097] | 0.643 | 0.659 | 11/4/20 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp14_cheap (n=35, ref 0.519 → 0.653) | **+0.135** [+0.071, +0.239] | 0.003 | 0.000 | 17/2/16 | +0.143 | +0.171 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp17 (n=35, ref 0.688 → 0.653) | -0.034 [-0.141, +0.028] | 0.412 | 0.428 | 7/6/22 | -0.029 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs lex13 (n=35, ref 0.617 → 0.653) | +0.037 [-0.000, +0.096] | 0.130 | 0.138 | 10/4/21 | +0.057 | +0.029 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bm25_01 (n=35, ref 0.546 → 0.653) | **+0.107** [+0.035, +0.209] | 0.021 | 0.018 | 17/3/15 | +0.114 | +0.057 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05 (n=35, ref 0.590 → 0.653) | **+0.063** [+0.026, +0.129] | 0.016 | 0.004 | 13/1/21 | +0.086 | +0.057 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05+bge@20 (n=35, ref 0.649 → 0.653) | +0.005 [-0.104, +0.080] | 0.919 | 0.925 | 11/4/20 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.653) | +0.031 [-0.058, +0.090] | 0.405 | 0.432 | 12/4/19 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap (n=35, ref 0.609 → 0.653) | +0.044 [+0.005, +0.098] | 0.067 | 0.068 | 10/4/21 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp24 mined-only (same features) (n=35, ref 0.610 → 0.653) | +0.043 [+0.005, +0.105] | 0.088 | 0.091 | 10/4/21 | +0.057 | +0.086 |
| ltr24__logreg__notype-nobge__pooled | vs bar_val (n=35, ref 0.665 → 0.611) | -0.054 [-0.156, +0.035] | 0.283 | 0.288 | 7/12/16 | -0.057 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs bar_full (n=35, ref 0.659 → 0.611) | -0.048 [-0.149, +0.040] | 0.334 | 0.341 | 7/12/16 | -0.057 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs exp14 (n=35, ref 0.634 → 0.611) | -0.024 [-0.126, +0.070] | 0.644 | 0.649 | 9/10/16 | -0.057 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs exp14_cheap (n=35, ref 0.519 → 0.611) | **+0.092** [+0.019, +0.199] | 0.049 | 0.045 | 14/5/16 | +0.086 | +0.143 |
| ltr24__logreg__notype-nobge__pooled | vs exp17 (n=35, ref 0.688 → 0.611) | -0.077 [-0.175, -0.002] | 0.091 | 0.092 | 7/11/17 | -0.086 | -0.029 |
| ltr24__logreg__notype-nobge__pooled | vs lex13 (n=35, ref 0.617 → 0.611) | -0.006 [-0.070, +0.060] | 0.864 | 0.848 | 7/9/19 | +0.000 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs bm25_01 (n=35, ref 0.546 → 0.611) | +0.065 [-0.015, +0.175] | 0.181 | 0.181 | 10/8/17 | +0.057 | +0.029 |
| ltr24__logreg__notype-nobge__pooled | vs convex05 (n=35, ref 0.590 → 0.611) | +0.021 [-0.032, +0.084] | 0.495 | 0.509 | 10/6/19 | +0.029 | +0.029 |
| ltr24__logreg__notype-nobge__pooled | vs convex05+bge@20 (n=35, ref 0.649 → 0.611) | -0.038 [-0.143, +0.056] | 0.466 | 0.472 | 10/10/15 | -0.029 | +0.029 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.611) | -0.012 [-0.091, +0.031] | 0.686 | 0.736 | 7/7/21 | -0.029 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap (n=35, ref 0.609 → 0.611) | +0.002 [-0.051, +0.041] | 0.944 | 0.942 | 8/7/20 | -0.029 | +0.029 |
| ltr24__logreg__notype-nobge__pooled | vs exp24 mined-only (same features) (n=35, ref 0.520 → 0.611) | +0.090 [+0.003, +0.205] | 0.090 | ~0.090 | 16/7/12 | +0.086 | +0.057 |
| ltr24__lgbm-tiny__small__pooled | vs bar_val (n=35, ref 0.665 → 0.647) | -0.018 [-0.109, +0.049] | 0.657 | 0.671 | 7/8/20 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs bar_full (n=35, ref 0.659 → 0.647) | -0.012 [-0.102, +0.053] | 0.767 | 0.773 | 7/7/21 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs exp14 (n=35, ref 0.634 → 0.647) | +0.012 [-0.072, +0.093] | 0.779 | 0.779 | 12/5/18 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs exp14_cheap (n=35, ref 0.519 → 0.647) | **+0.128** [+0.065, +0.230] | 0.004 | 0.001 | 17/2/16 | +0.143 | +0.143 |
| ltr24__lgbm-tiny__small__pooled | vs exp17 (n=35, ref 0.688 → 0.647) | -0.041 [-0.131, +0.019] | 0.282 | 0.300 | 6/9/20 | -0.029 | -0.029 |
| ltr24__lgbm-tiny__small__pooled | vs lex13 (n=35, ref 0.617 → 0.647) | +0.030 [-0.001, +0.089] | 0.175 | 0.215 | 7/3/25 | +0.057 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs bm25_01 (n=35, ref 0.546 → 0.647) | **+0.101** [+0.030, +0.204] | 0.027 | 0.026 | 17/3/15 | +0.114 | +0.029 |
| ltr24__lgbm-tiny__small__pooled | vs convex05 (n=35, ref 0.590 → 0.647) | **+0.057** [+0.021, +0.122] | 0.028 | 0.012 | 14/2/19 | +0.086 | +0.029 |
| ltr24__lgbm-tiny__small__pooled | vs convex05+bge@20 (n=35, ref 0.649 → 0.647) | -0.002 [-0.096, +0.072] | 0.964 | 0.965 | 10/7/18 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.647) | +0.024 [-0.041, +0.081] | 0.440 | 0.456 | 11/4/20 | +0.029 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap (n=35, ref 0.609 → 0.647) | +0.038 [+0.008, +0.086] | 0.060 | 0.050 | 12/2/21 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__small__pooled | vs exp24 mined-only (same features) (n=35, ref 0.583 → 0.647) | **+0.064** [+0.027, +0.127] | 0.015 | 0.006 | 10/5/20 | +0.086 | +0.000 |
| ltr24__logreg__small__pooled | vs bar_val (n=35, ref 0.665 → 0.670) | +0.005 [-0.064, +0.095] | 0.898 | 0.902 | 6/8/21 | +0.029 | +0.000 |
| ltr24__logreg__small__pooled | vs bar_full (n=35, ref 0.659 → 0.670) | +0.011 [-0.055, +0.100] | 0.772 | 0.784 | 6/7/22 | +0.029 | +0.000 |
| ltr24__logreg__small__pooled | vs exp14 (n=35, ref 0.634 → 0.670) | +0.035 [-0.065, +0.149] | 0.524 | 0.532 | 11/8/16 | +0.029 | +0.000 |
| ltr24__logreg__small__pooled | vs exp14_cheap (n=35, ref 0.519 → 0.670) | **+0.151** [+0.075, +0.268] | 0.004 | 0.001 | 18/2/15 | +0.171 | +0.143 |
| ltr24__logreg__small__pooled | vs exp17 (n=35, ref 0.688 → 0.670) | -0.018 [-0.082, +0.066] | 0.637 | 0.650 | 5/9/21 | +0.000 | -0.029 |
| ltr24__logreg__small__pooled | vs lex13 (n=35, ref 0.617 → 0.670) | +0.053 [-0.014, +0.145] | 0.196 | 0.196 | 10/5/20 | +0.086 | +0.000 |
| ltr24__logreg__small__pooled | vs bm25_01 (n=35, ref 0.546 → 0.670) | **+0.124** [+0.043, +0.240] | 0.019 | 0.016 | 17/3/15 | +0.143 | +0.029 |
| ltr24__logreg__small__pooled | vs convex05 (n=35, ref 0.590 → 0.670) | **+0.080** [+0.028, +0.172] | 0.030 | 0.020 | 14/3/18 | +0.114 | +0.029 |
| ltr24__logreg__small__pooled | vs convex05+bge@20 (n=35, ref 0.649 → 0.670) | +0.021 [-0.053, +0.112] | 0.618 | 0.631 | 9/6/20 | +0.057 | +0.029 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.670) | +0.047 [-0.017, +0.141] | 0.249 | 0.264 | 11/4/20 | +0.057 | +0.000 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap (n=35, ref 0.609 → 0.670) | +0.061 [+0.007, +0.161] | 0.116 | 0.133 | 10/3/22 | +0.057 | +0.029 |
| ltr24__logreg__small__pooled | vs exp24 mined-only (same features) (n=35, ref 0.579 → 0.670) | +0.091 [+0.001, +0.217] | 0.105 | 0.108 | 13/5/17 | +0.086 | +0.114 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bar_val (n=35, ref 0.665 → 0.667) | +0.002 [-0.097, +0.077] | 0.961 | 0.958 | 9/6/20 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bar_full (n=35, ref 0.659 → 0.667) | +0.008 [-0.091, +0.081] | 0.852 | 0.859 | 9/5/21 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp14 (n=35, ref 0.634 → 0.667) | +0.033 [-0.039, +0.084] | 0.302 | 0.310 | 12/2/21 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp14_cheap (n=35, ref 0.519 → 0.667) | **+0.148** [+0.078, +0.254] | 0.002 | 0.000 | 18/2/15 | +0.171 | +0.171 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp17 (n=35, ref 0.688 → 0.667) | -0.021 [-0.133, +0.061] | 0.677 | 0.684 | 8/7/20 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs lex13 (n=35, ref 0.617 → 0.667) | +0.051 [-0.027, +0.134] | 0.232 | 0.245 | 11/5/19 | +0.086 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bm25_01 (n=35, ref 0.546 → 0.667) | **+0.121** [+0.042, +0.226] | 0.016 | 0.014 | 15/4/16 | +0.143 | +0.057 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05 (n=35, ref 0.590 → 0.667) | +0.077 [-0.002, +0.156] | 0.071 | 0.068 | 14/3/18 | +0.114 | +0.057 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05+bge@20 (n=35, ref 0.649 → 0.667) | +0.018 [-0.085, +0.097] | 0.699 | 0.705 | 11/5/19 | +0.057 | +0.057 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.667) | +0.044 [-0.058, +0.138] | 0.385 | 0.393 | 12/5/18 | +0.057 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap (n=35, ref 0.609 → 0.667) | +0.058 [-0.022, +0.150] | 0.199 | 0.203 | 11/6/18 | +0.057 | +0.057 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp24 mined-only (same features) (n=35, ref 0.604 → 0.667) | +0.063 [-0.017, +0.154] | 0.164 | 0.169 | 12/5/18 | +0.086 | +0.086 |
| ltr24__logreg__notype__pooled-scored | vs bar_val (n=35, ref 0.665 → 0.653) | -0.012 [-0.097, +0.056] | 0.758 | 0.769 | 7/9/19 | +0.000 | +0.029 |
| ltr24__logreg__notype__pooled-scored | vs bar_full (n=35, ref 0.659 → 0.653) | -0.006 [-0.093, +0.061] | 0.878 | 0.885 | 7/8/20 | +0.000 | +0.029 |
| ltr24__logreg__notype__pooled-scored | vs exp14 (n=35, ref 0.634 → 0.653) | +0.018 [-0.079, +0.127] | 0.737 | 0.741 | 9/8/18 | +0.000 | +0.029 |
| ltr24__logreg__notype__pooled-scored | vs exp14_cheap (n=35, ref 0.519 → 0.653) | **+0.134** [+0.050, +0.255] | 0.013 | 0.010 | 15/5/15 | +0.143 | +0.171 |
| ltr24__logreg__notype__pooled-scored | vs exp17 (n=35, ref 0.688 → 0.653) | -0.035 [-0.120, +0.022] | 0.328 | 0.352 | 6/9/20 | -0.029 | +0.000 |
| ltr24__logreg__notype__pooled-scored | vs lex13 (n=35, ref 0.617 → 0.653) | +0.036 [-0.021, +0.129] | 0.341 | 0.374 | 8/7/20 | +0.057 | +0.029 |
| ltr24__logreg__notype__pooled-scored | vs bm25_01 (n=35, ref 0.546 → 0.653) | +0.107 [+0.017, +0.224] | 0.052 | 0.052 | 13/5/17 | +0.114 | +0.057 |
| ltr24__logreg__notype__pooled-scored | vs convex05 (n=35, ref 0.590 → 0.653) | +0.062 [-0.002, +0.152] | 0.123 | 0.125 | 13/5/17 | +0.086 | +0.057 |
| ltr24__logreg__notype__pooled-scored | vs convex05+bge@20 (n=35, ref 0.649 → 0.653) | +0.004 [-0.084, +0.079] | 0.926 | 0.928 | 10/7/18 | +0.029 | +0.057 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.653) | +0.030 [-0.049, +0.100] | 0.446 | 0.457 | 10/4/21 | +0.029 | +0.029 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap (n=35, ref 0.609 → 0.653) | +0.043 [-0.011, +0.134] | 0.240 | 0.264 | 9/7/19 | +0.029 | +0.057 |
| ltr24__logreg__notype__pooled-scored | vs exp24 mined-only (same features) (n=35, ref 0.601 → 0.653) | +0.052 [-0.044, +0.150] | 0.317 | 0.321 | 10/8/17 | +0.057 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bar_val (n=35, ref 0.665 → 0.635) | -0.029 [-0.120, +0.030] | 0.441 | 0.454 | 7/8/20 | -0.029 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bar_full (n=35, ref 0.659 → 0.635) | -0.023 [-0.113, +0.035] | 0.536 | 0.552 | 7/8/20 | -0.029 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp14 (n=35, ref 0.634 → 0.635) | +0.001 [-0.090, +0.054] | 0.979 | 0.984 | 11/4/20 | -0.029 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp14_cheap (n=35, ref 0.519 → 0.635) | **+0.117** [+0.062, +0.198] | 0.002 | 0.000 | 17/2/16 | +0.114 | +0.171 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp17 (n=35, ref 0.688 → 0.635) | -0.052 [-0.154, +0.016] | 0.223 | 0.231 | 6/9/20 | -0.057 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs lex13 (n=35, ref 0.617 → 0.635) | +0.019 [-0.046, +0.073] | 0.538 | 0.557 | 9/6/20 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bm25_01 (n=35, ref 0.546 → 0.635) | **+0.089** [+0.025, +0.181] | 0.030 | 0.026 | 15/3/17 | +0.086 | +0.057 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05 (n=35, ref 0.590 → 0.635) | +0.045 [-0.022, +0.104] | 0.179 | 0.181 | 13/3/19 | +0.057 | +0.057 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05+bge@20 (n=35, ref 0.649 → 0.635) | -0.013 [-0.106, +0.054] | 0.745 | 0.751 | 9/7/19 | +0.000 | +0.057 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.635) | +0.013 [-0.078, +0.077] | 0.743 | 0.748 | 11/5/19 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap (n=35, ref 0.609 → 0.635) | +0.026 [-0.040, +0.077] | 0.381 | 0.401 | 11/6/18 | +0.000 | +0.057 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp24 mined-only (same features) (n=35, ref 0.583 → 0.635) | +0.052 [-0.022, +0.119] | 0.162 | 0.166 | 13/6/16 | +0.057 | +0.086 |
| ltr24__logreg__withtype__pooled-scored | vs bar_val (n=35, ref 0.665 → 0.605) | -0.060 [-0.151, +0.017] | 0.174 | 0.177 | 6/11/18 | -0.057 | +0.000 |
| ltr24__logreg__withtype__pooled-scored | vs bar_full (n=35, ref 0.659 → 0.605) | -0.054 [-0.147, +0.024] | 0.225 | 0.230 | 7/11/17 | -0.057 | +0.000 |
| ltr24__logreg__withtype__pooled-scored | vs exp14 (n=35, ref 0.634 → 0.605) | -0.029 [-0.148, +0.091] | 0.641 | ~0.645 | 9/12/14 | -0.057 | +0.000 |
| ltr24__logreg__withtype__pooled-scored | vs exp14_cheap (n=35, ref 0.519 → 0.605) | +0.086 [-0.001, +0.202] | 0.110 | ~0.112 | 13/8/14 | +0.086 | +0.143 |
| ltr24__logreg__withtype__pooled-scored | vs exp17 (n=35, ref 0.688 → 0.605) | **-0.083** [-0.172, -0.017] | 0.042 | 0.038 | 5/11/19 | -0.086 | -0.029 |
| ltr24__logreg__withtype__pooled-scored | vs lex13 (n=35, ref 0.617 → 0.605) | -0.011 [-0.082, +0.059] | 0.755 | 0.758 | 7/7/21 | +0.000 | +0.000 |
| ltr24__logreg__withtype__pooled-scored | vs bm25_01 (n=35, ref 0.546 → 0.605) | +0.059 [-0.041, +0.174] | 0.293 | ~0.298 | 13/8/14 | +0.057 | +0.029 |
| ltr24__logreg__withtype__pooled-scored | vs convex05 (n=35, ref 0.590 → 0.605) | +0.015 [-0.076, +0.104] | 0.755 | ~0.754 | 13/8/14 | +0.029 | +0.029 |
| ltr24__logreg__withtype__pooled-scored | vs convex05+bge@20 (n=35, ref 0.649 → 0.605) | -0.044 [-0.138, +0.040] | 0.346 | 0.350 | 9/9/17 | -0.029 | +0.029 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.605) | -0.018 [-0.087, +0.029] | 0.542 | 0.566 | 8/6/21 | -0.029 | +0.000 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap (n=35, ref 0.609 → 0.605) | -0.004 [-0.079, +0.067] | 0.914 | 0.945 | 10/6/19 | -0.029 | +0.029 |
| ltr24__logreg__withtype__pooled-scored | vs exp24 mined-only (same features) (n=35, ref 0.477 → 0.605) | **+0.128** [+0.060, +0.232] | 0.006 | 0.001 | 14/3/18 | +0.143 | +0.143 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bar_val (n=35, ref 0.665 → 0.654) | -0.011 [-0.107, +0.057] | 0.799 | 0.805 | 8/7/20 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bar_full (n=35, ref 0.659 → 0.654) | -0.004 [-0.101, +0.061] | 0.914 | 0.918 | 8/7/20 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp14 (n=35, ref 0.634 → 0.654) | +0.020 [-0.061, +0.062] | 0.507 | 0.555 | 11/2/22 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp14_cheap (n=35, ref 0.519 → 0.654) | **+0.135** [+0.072, +0.234] | 0.002 | 0.000 | 17/2/16 | +0.143 | +0.171 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp17 (n=35, ref 0.688 → 0.654) | -0.034 [-0.138, +0.041] | 0.466 | 0.475 | 7/8/20 | -0.029 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs lex13 (n=35, ref 0.617 → 0.654) | +0.038 [-0.030, +0.111] | 0.304 | 0.316 | 10/6/19 | +0.057 | +0.029 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bm25_01 (n=35, ref 0.546 → 0.654) | **+0.108** [+0.035, +0.205] | 0.019 | 0.017 | 15/4/16 | +0.114 | +0.057 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05 (n=35, ref 0.590 → 0.654) | +0.064 [-0.005, +0.129] | 0.077 | 0.075 | 14/3/18 | +0.086 | +0.057 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05+bge@20 (n=35, ref 0.649 → 0.654) | +0.005 [-0.092, +0.079] | 0.899 | 0.905 | 10/6/19 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.654) | +0.032 [-0.064, +0.117] | 0.496 | 0.505 | 12/5/18 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=35, ref 0.609 → 0.654) | +0.045 [-0.023, +0.122] | 0.236 | 0.248 | 11/6/18 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=35, ref 0.608 → 0.654) | +0.046 [-0.021, +0.118] | 0.205 | 0.208 | 12/5/18 | +0.057 | +0.086 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bar_val (n=35, ref 0.665 → 0.641) | -0.023 [-0.108, +0.057] | 0.585 | 0.591 | 7/11/17 | -0.029 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bar_full (n=35, ref 0.659 → 0.641) | -0.017 [-0.101, +0.063] | 0.683 | 0.687 | 7/11/17 | -0.029 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp14 (n=35, ref 0.634 → 0.641) | +0.007 [-0.102, +0.124] | 0.906 | 0.906 | 9/10/16 | -0.029 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp14_cheap (n=35, ref 0.519 → 0.641) | **+0.123** [+0.040, +0.244] | 0.022 | 0.019 | 13/6/16 | +0.114 | +0.143 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp17 (n=35, ref 0.688 → 0.641) | -0.046 [-0.128, +0.017] | 0.216 | 0.223 | 7/10/18 | -0.057 | -0.029 |
| ltr24__logreg__notype-nogate__pooled-scored | vs lex13 (n=35, ref 0.617 → 0.641) | +0.025 [-0.044, +0.120] | 0.553 | 0.570 | 7/8/20 | +0.029 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bm25_01 (n=35, ref 0.546 → 0.641) | +0.095 [+0.007, +0.215] | 0.080 | 0.078 | 12/7/16 | +0.086 | +0.029 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05 (n=35, ref 0.590 → 0.641) | +0.051 [-0.011, +0.143] | 0.197 | 0.204 | 11/4/20 | +0.057 | +0.029 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05+bge@20 (n=35, ref 0.649 → 0.641) | -0.007 [-0.097, +0.078] | 0.870 | 0.872 | 10/9/16 | +0.000 | +0.029 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.641) | +0.019 [-0.049, +0.091] | 0.605 | 0.599 | 7/5/23 | +0.000 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=35, ref 0.609 → 0.641) | +0.032 [-0.019, +0.125] | 0.362 | 0.410 | 7/7/21 | +0.000 | +0.029 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=35, ref 0.622 → 0.641) | +0.019 [-0.028, +0.114] | 0.568 | 0.629 | 6/7/22 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bar_val (n=35, ref 0.665 → 0.629) | -0.036 [-0.131, +0.039] | 0.420 | 0.431 | 9/9/17 | -0.029 | +0.057 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bar_full (n=35, ref 0.659 → 0.629) | -0.030 [-0.125, +0.043] | 0.500 | 0.511 | 9/9/17 | -0.029 | +0.057 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp14 (n=35, ref 0.634 → 0.629) | -0.005 [-0.101, +0.080] | 0.907 | 0.917 | 10/7/18 | -0.029 | +0.057 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp14_cheap (n=35, ref 0.519 → 0.629) | **+0.110** [+0.053, +0.214] | 0.008 | 0.001 | 15/2/18 | +0.114 | +0.200 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp17 (n=35, ref 0.688 → 0.629) | -0.059 [-0.153, +0.009] | 0.162 | 0.169 | 7/10/18 | -0.057 | +0.029 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs lex13 (n=35, ref 0.617 → 0.629) | +0.013 [-0.036, +0.069] | 0.643 | 0.674 | 8/6/21 | +0.029 | +0.057 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bm25_01 (n=35, ref 0.546 → 0.629) | +0.083 [+0.018, +0.189] | 0.056 | 0.060 | 15/2/18 | +0.086 | +0.086 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05 (n=35, ref 0.590 → 0.629) | +0.039 [+0.008, +0.099] | 0.082 | 0.079 | 12/1/22 | +0.057 | +0.086 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05+bge@20 (n=35, ref 0.649 → 0.629) | -0.020 [-0.119, +0.062] | 0.674 | 0.681 | 11/8/16 | +0.000 | +0.086 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.629) | +0.006 [-0.067, +0.053] | 0.830 | 0.842 | 10/3/22 | +0.000 | +0.057 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=35, ref 0.609 → 0.629) | +0.020 [-0.006, +0.048] | 0.161 | 0.169 | 10/4/21 | +0.000 | +0.086 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=35, ref 0.610 → 0.629) | +0.019 [-0.015, +0.067] | 0.359 | 0.386 | 9/4/22 | +0.029 | +0.114 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bar_val (n=35, ref 0.665 → 0.604) | -0.061 [-0.165, +0.030] | 0.237 | 0.241 | 7/12/16 | -0.086 | +0.029 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bar_full (n=35, ref 0.659 → 0.604) | -0.055 [-0.160, +0.036] | 0.284 | 0.289 | 7/12/16 | -0.086 | +0.029 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp14 (n=35, ref 0.634 → 0.604) | -0.030 [-0.137, +0.069] | 0.571 | 0.578 | 9/11/15 | -0.086 | +0.029 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp14_cheap (n=35, ref 0.519 → 0.604) | +0.085 [+0.005, +0.193] | 0.084 | 0.085 | 14/6/15 | +0.057 | +0.171 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp17 (n=35, ref 0.688 → 0.604) | -0.084 [-0.183, -0.007] | 0.073 | 0.073 | 7/12/16 | -0.114 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | vs lex13 (n=35, ref 0.617 → 0.604) | -0.013 [-0.084, +0.057] | 0.733 | 0.736 | 7/9/19 | -0.029 | +0.029 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bm25_01 (n=35, ref 0.546 → 0.604) | +0.058 [-0.030, +0.169] | 0.255 | 0.260 | 12/8/15 | +0.029 | +0.057 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05 (n=35, ref 0.590 → 0.604) | +0.014 [-0.051, +0.080] | 0.688 | 0.694 | 11/6/18 | +0.000 | +0.057 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05+bge@20 (n=35, ref 0.649 → 0.604) | -0.045 [-0.155, +0.050] | 0.401 | ~0.406 | 10/11/14 | -0.057 | +0.057 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.604) | -0.019 [-0.112, +0.029] | 0.582 | 0.629 | 8/5/22 | -0.057 | +0.029 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=35, ref 0.609 → 0.604) | -0.005 [-0.069, +0.042] | 0.857 | 0.859 | 8/6/21 | -0.057 | +0.057 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=35, ref 0.520 → 0.604) | +0.084 [-0.004, +0.197] | 0.112 | ~0.112 | 14/7/14 | +0.057 | +0.086 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bar_val (n=35, ref 0.665 → 0.644) | -0.021 [-0.098, +0.033] | 0.526 | 0.550 | 6/7/22 | -0.029 | +0.029 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bar_full (n=35, ref 0.659 → 0.644) | -0.015 [-0.092, +0.037] | 0.647 | 0.670 | 6/6/23 | -0.029 | +0.029 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp14 (n=35, ref 0.634 → 0.644) | +0.009 [-0.071, +0.070] | 0.794 | 0.806 | 10/5/20 | -0.029 | +0.029 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp14_cheap (n=35, ref 0.519 → 0.644) | **+0.125** [+0.065, +0.209] | 0.002 | 0.001 | 17/3/15 | +0.114 | +0.171 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp17 (n=35, ref 0.688 → 0.644) | -0.044 [-0.126, +0.016] | 0.233 | 0.243 | 6/9/20 | -0.057 | +0.000 |
| ltr24__lgbm-tiny__small__pooled-scored | vs lex13 (n=35, ref 0.617 → 0.644) | +0.028 [-0.026, +0.087] | 0.361 | 0.374 | 9/6/20 | +0.029 | +0.029 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bm25_01 (n=35, ref 0.546 → 0.644) | **+0.098** [+0.030, +0.190] | 0.023 | 0.019 | 15/3/17 | +0.086 | +0.057 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05 (n=35, ref 0.590 → 0.644) | +0.054 [-0.002, +0.117] | 0.098 | 0.098 | 11/5/19 | +0.057 | +0.057 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05+bge@20 (n=35, ref 0.649 → 0.644) | -0.005 [-0.080, +0.059] | 0.894 | 0.893 | 7/7/21 | +0.000 | +0.057 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.644) | +0.021 [-0.060, +0.085] | 0.573 | 0.584 | 11/7/17 | +0.000 | +0.029 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap (n=35, ref 0.609 → 0.644) | +0.035 [-0.021, +0.092] | 0.246 | 0.252 | 10/7/18 | +0.000 | +0.057 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp24 mined-only (same features) (n=35, ref 0.583 → 0.644) | +0.061 [+0.003, +0.131] | 0.080 | 0.081 | 11/6/18 | +0.057 | +0.029 |
| ltr24__logreg__small__pooled-scored | vs bar_val (n=35, ref 0.665 → 0.659) | -0.005 [-0.088, +0.084] | 0.905 | 0.902 | 7/7/21 | +0.000 | +0.029 |
| ltr24__logreg__small__pooled-scored | vs bar_full (n=35, ref 0.659 → 0.659) | +0.001 [-0.083, +0.088] | 0.985 | 0.986 | 7/7/21 | +0.000 | +0.029 |
| ltr24__logreg__small__pooled-scored | vs exp14 (n=35, ref 0.634 → 0.659) | +0.025 [-0.072, +0.140] | 0.650 | 0.656 | 12/8/15 | +0.000 | +0.029 |
| ltr24__logreg__small__pooled-scored | vs exp14_cheap (n=35, ref 0.519 → 0.659) | **+0.141** [+0.057, +0.258] | 0.009 | ~0.006 | 18/3/14 | +0.143 | +0.171 |
| ltr24__logreg__small__pooled-scored | vs exp17 (n=35, ref 0.688 → 0.659) | -0.028 [-0.108, +0.054] | 0.503 | 0.509 | 6/8/21 | -0.029 | +0.000 |
| ltr24__logreg__small__pooled-scored | vs lex13 (n=35, ref 0.617 → 0.659) | +0.043 [-0.028, +0.139] | 0.318 | 0.333 | 11/7/17 | +0.057 | +0.029 |
| ltr24__logreg__small__pooled-scored | vs bm25_01 (n=35, ref 0.546 → 0.659) | **+0.113** [+0.023, +0.230] | 0.038 | 0.037 | 16/3/16 | +0.114 | +0.057 |
| ltr24__logreg__small__pooled-scored | vs convex05 (n=35, ref 0.590 → 0.659) | +0.069 [+0.011, +0.159] | 0.072 | 0.062 | 14/1/20 | +0.086 | +0.057 |
| ltr24__logreg__small__pooled-scored | vs convex05+bge@20 (n=35, ref 0.649 → 0.659) | +0.011 [-0.077, +0.102] | 0.818 | 0.839 | 10/5/20 | +0.029 | +0.057 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap+bge (n=35, ref 0.623 → 0.659) | +0.037 [-0.045, +0.129] | 0.427 | 0.438 | 11/5/19 | +0.029 | +0.029 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap (n=35, ref 0.609 → 0.659) | +0.050 [-0.011, +0.152] | 0.220 | 0.247 | 10/6/19 | +0.029 | +0.057 |
| ltr24__logreg__small__pooled-scored | vs exp24 mined-only (same features) (n=35, ref 0.579 → 0.659) | +0.081 [-0.013, +0.194] | 0.141 | 0.144 | 14/5/16 | +0.057 | +0.143 |

**Human full set – paired tests (Δ = exp-24 oof − reference)**

| run | reference  Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 | Δ H@10 |
|---|---|:--|--:|--:|:--|--:|--:|
| ltr24__lgbm-tiny__notype__mined | vs bar_val (n=64, ref 0.696 → 0.659) | -0.037 [-0.113, +0.030] | 0.308 | ~0.311 | 14/16/34 | -0.031 | -0.047 |
| ltr24__lgbm-tiny__notype__mined | vs bar_full (n=64, ref 0.703 → 0.659) | -0.044 [-0.118, +0.021] | 0.220 | ~0.218 | 13/17/34 | -0.047 | -0.062 |
| ltr24__lgbm-tiny__notype__mined | vs exp14 (n=64, ref 0.723 → 0.659) | -0.063 [-0.136, -0.002] | 0.070 | ~0.067 | 9/17/38 | -0.094 | -0.062 |
| ltr24__lgbm-tiny__notype__mined | vs exp14_cheap (n=64, ref 0.603 → 0.659) | +0.056 [-0.004, +0.128] | 0.106 | ~0.110 | 17/14/33 | +0.078 | +0.047 |
| ltr24__lgbm-tiny__notype__mined | vs exp17 (n=64, ref 0.719 → 0.659) | -0.060 [-0.142, +0.008] | 0.119 | ~0.121 | 12/15/37 | -0.062 | -0.062 |
| ltr24__lgbm-tiny__notype__mined | vs lex13 (n=64, ref 0.683 → 0.659) | -0.024 [-0.068, +0.014] | 0.257 | ~0.258 | 9/14/41 | -0.031 | -0.047 |
| ltr24__lgbm-tiny__notype__mined | vs bm25_01 (n=64, ref 0.601 → 0.659) | +0.059 [-0.001, +0.130] | 0.088 | ~0.089 | 18/13/33 | +0.062 | -0.016 |
| ltr24__lgbm-tiny__notype__mined | vs convex05 (n=64, ref 0.622 → 0.659) | +0.038 [-0.019, +0.098] | 0.217 | ~0.221 | 15/16/33 | +0.062 | -0.047 |
| ltr24__lgbm-tiny__notype__mined | vs convex05+bge@20 (n=64, ref 0.695 → 0.659) | -0.036 [-0.111, +0.031] | 0.324 | ~0.325 | 12/18/34 | -0.031 | -0.031 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.659) | -0.021 [-0.075, +0.015] | 0.352 | ~0.367 | 9/13/42 | -0.031 | -0.047 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap (n=64, ref 0.671 → 0.659) | -0.012 [-0.055, +0.012] | 0.471 | 0.510 | 11/9/44 | -0.031 | -0.031 |
| ltr24__logreg__notype__mined | vs bar_val (n=64, ref 0.696 → 0.620) | -0.077 [-0.158, -0.003] | 0.058 | ~0.058 | 11/22/31 | -0.078 | -0.016 |
| ltr24__logreg__notype__mined | vs bar_full (n=64, ref 0.703 → 0.620) | **-0.083** [-0.161, -0.012] | 0.034 | ~0.032 | 9/23/32 | -0.094 | -0.031 |
| ltr24__logreg__notype__mined | vs exp14 (n=64, ref 0.723 → 0.620) | **-0.103** [-0.189, -0.018] | 0.024 | ~0.026 | 10/23/31 | -0.141 | -0.031 |
| ltr24__logreg__notype__mined | vs exp14_cheap (n=64, ref 0.603 → 0.620) | +0.016 [-0.071, +0.107] | 0.728 | ~0.732 | 18/20/26 | +0.031 | +0.078 |
| ltr24__logreg__notype__mined | vs exp17 (n=64, ref 0.719 → 0.620) | **-0.100** [-0.183, -0.025] | 0.017 | ~0.015 | 9/22/33 | -0.109 | -0.031 |
| ltr24__logreg__notype__mined | vs lex13 (n=64, ref 0.683 → 0.620) | **-0.064** [-0.130, -0.009] | 0.045 | ~0.043 | 10/15/39 | -0.078 | -0.016 |
| ltr24__logreg__notype__mined | vs bm25_01 (n=64, ref 0.601 → 0.620) | +0.019 [-0.060, +0.104] | 0.661 | ~0.660 | 20/16/28 | +0.016 | +0.016 |
| ltr24__logreg__notype__mined | vs convex05 (n=64, ref 0.622 → 0.620) | -0.002 [-0.076, +0.072] | 0.961 | ~0.961 | 16/19/29 | +0.016 | -0.016 |
| ltr24__logreg__notype__mined | vs convex05+bge@20 (n=64, ref 0.695 → 0.620) | -0.075 [-0.155, -0.002] | 0.061 | ~0.061 | 11/23/30 | -0.078 | +0.000 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.620) | -0.060 [-0.134, +0.003] | 0.092 | ~0.091 | 14/17/33 | -0.078 | -0.016 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap (n=64, ref 0.671 → 0.620) | -0.051 [-0.128, +0.019] | 0.181 | ~0.183 | 16/13/35 | -0.078 | +0.000 |
| ltr24__lgbm-tiny__withtype__mined | vs bar_val (n=64, ref 0.696 → 0.638) | -0.058 [-0.131, +0.004] | 0.094 | ~0.093 | 10/17/37 | -0.062 | -0.047 |
| ltr24__lgbm-tiny__withtype__mined | vs bar_full (n=64, ref 0.703 → 0.638) | -0.065 [-0.141, +0.000] | 0.074 | ~0.073 | 10/18/36 | -0.078 | -0.062 |
| ltr24__lgbm-tiny__withtype__mined | vs exp14 (n=64, ref 0.723 → 0.638) | **-0.084** [-0.161, -0.016] | 0.027 | ~0.025 | 8/22/34 | -0.125 | -0.062 |
| ltr24__lgbm-tiny__withtype__mined | vs exp14_cheap (n=64, ref 0.603 → 0.638) | +0.035 [-0.024, +0.106] | 0.303 | ~0.313 | 18/16/30 | +0.047 | +0.047 |
| ltr24__lgbm-tiny__withtype__mined | vs exp17 (n=64, ref 0.719 → 0.638) | **-0.081** [-0.162, -0.014] | 0.035 | ~0.032 | 7/18/39 | -0.094 | -0.062 |
| ltr24__lgbm-tiny__withtype__mined | vs lex13 (n=64, ref 0.683 → 0.638) | -0.045 [-0.098, +0.008] | 0.107 | ~0.108 | 8/19/37 | -0.062 | -0.047 |
| ltr24__lgbm-tiny__withtype__mined | vs bm25_01 (n=64, ref 0.601 → 0.638) | +0.037 [-0.014, +0.102] | 0.219 | ~0.221 | 16/15/33 | +0.031 | -0.016 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05 (n=64, ref 0.622 → 0.638) | +0.017 [-0.032, +0.076] | 0.556 | ~0.567 | 14/17/33 | +0.031 | -0.047 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05+bge@20 (n=64, ref 0.695 → 0.638) | -0.057 [-0.134, +0.010] | 0.124 | ~0.123 | 12/18/34 | -0.062 | -0.031 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.638) | **-0.042** [-0.088, -0.016] | 0.018 | ~0.009 | 6/16/42 | -0.062 | -0.047 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap (n=64, ref 0.671 → 0.638) | -0.033 [-0.078, -0.007] | 0.060 | 0.075 | 5/12/47 | -0.062 | -0.031 |
| ltr24__logreg__withtype__mined | vs bar_val (n=64, ref 0.696 → 0.502) | **-0.194** [-0.281, -0.117] | 0.000 | ~0.000 | 7/29/28 | -0.234 | -0.094 |
| ltr24__logreg__withtype__mined | vs bar_full (n=64, ref 0.703 → 0.502) | **-0.201** [-0.290, -0.122] | 0.000 | ~0.000 | 8/29/27 | -0.250 | -0.109 |
| ltr24__logreg__withtype__mined | vs exp14 (n=64, ref 0.723 → 0.502) | **-0.220** [-0.322, -0.114] | 0.000 | ~0.000 | 10/32/22 | -0.297 | -0.109 |
| ltr24__logreg__withtype__mined | vs exp14_cheap (n=64, ref 0.603 → 0.502) | **-0.101** [-0.197, -0.005] | 0.044 | ~0.043 | 13/27/24 | -0.125 | +0.000 |
| ltr24__logreg__withtype__mined | vs exp17 (n=64, ref 0.719 → 0.502) | **-0.217** [-0.309, -0.136] | 0.000 | ~0.000 | 8/28/28 | -0.266 | -0.109 |
| ltr24__logreg__withtype__mined | vs lex13 (n=64, ref 0.683 → 0.502) | **-0.181** [-0.264, -0.107] | 0.000 | ~0.000 | 9/28/27 | -0.234 | -0.094 |
| ltr24__logreg__withtype__mined | vs bm25_01 (n=64, ref 0.601 → 0.502) | **-0.099** [-0.184, -0.011] | 0.030 | ~0.030 | 17/24/23 | -0.141 | -0.062 |
| ltr24__logreg__withtype__mined | vs convex05 (n=64, ref 0.622 → 0.502) | **-0.119** [-0.208, -0.035] | 0.009 | ~0.009 | 15/27/22 | -0.141 | -0.094 |
| ltr24__logreg__withtype__mined | vs convex05+bge@20 (n=64, ref 0.695 → 0.502) | **-0.193** [-0.284, -0.111] | 0.000 | ~0.000 | 9/27/28 | -0.234 | -0.078 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.502) | **-0.178** [-0.267, -0.103] | 0.000 | ~0.000 | 9/27/28 | -0.234 | -0.094 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap (n=64, ref 0.671 → 0.502) | **-0.169** [-0.259, -0.086] | 0.000 | ~0.000 | 13/25/26 | -0.234 | -0.078 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bar_val (n=64, ref 0.696 → 0.671) | -0.025 [-0.098, +0.037] | 0.464 | ~0.466 | 14/15/35 | -0.016 | -0.031 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bar_full (n=64, ref 0.703 → 0.671) | -0.032 [-0.101, +0.027] | 0.340 | ~0.344 | 12/15/37 | -0.031 | -0.047 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp14 (n=64, ref 0.723 → 0.671) | -0.051 [-0.119, +0.006] | 0.120 | ~0.122 | 9/17/38 | -0.078 | -0.047 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp14_cheap (n=64, ref 0.603 → 0.671) | **+0.068** [+0.015, +0.138] | 0.035 | ~0.034 | 19/11/34 | +0.094 | +0.062 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp17 (n=64, ref 0.719 → 0.671) | -0.048 [-0.125, +0.016] | 0.181 | ~0.188 | 11/15/38 | -0.047 | -0.047 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs lex13 (n=64, ref 0.683 → 0.671) | -0.012 [-0.055, +0.032] | 0.604 | ~0.612 | 10/12/42 | -0.016 | -0.031 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bm25_01 (n=64, ref 0.601 → 0.671) | **+0.071** [+0.027, +0.132] | 0.011 | ~0.008 | 21/6/37 | +0.078 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05 (n=64, ref 0.622 → 0.671) | **+0.050** [+0.010, +0.106] | 0.045 | ~0.043 | 16/10/38 | +0.078 | -0.031 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05+bge@20 (n=64, ref 0.695 → 0.671) | -0.024 [-0.095, +0.038] | 0.490 | ~0.491 | 13/16/35 | -0.016 | -0.016 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.671) | -0.009 [-0.048, +0.019] | 0.609 | ~0.623 | 9/12/43 | -0.016 | -0.031 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap (n=64, ref 0.671 → 0.671) | +0.001 [-0.026, +0.016] | 0.960 | 0.964 | 12/6/46 | -0.016 | -0.016 |
| ltr24__logreg__notype-nogate__mined | vs bar_val (n=64, ref 0.696 → 0.662) | -0.035 [-0.100, +0.018] | 0.245 | ~0.253 | 12/16/36 | -0.031 | -0.016 |
| ltr24__logreg__notype-nogate__mined | vs bar_full (n=64, ref 0.703 → 0.662) | -0.041 [-0.108, +0.012] | 0.177 | ~0.175 | 11/18/35 | -0.047 | -0.031 |
| ltr24__logreg__notype-nogate__mined | vs exp14 (n=64, ref 0.723 → 0.662) | -0.061 [-0.131, +0.001] | 0.079 | ~0.078 | 9/19/36 | -0.094 | -0.031 |
| ltr24__logreg__notype-nogate__mined | vs exp14_cheap (n=64, ref 0.603 → 0.662) | +0.059 [+0.000, +0.128] | 0.081 | ~0.079 | 20/13/31 | +0.078 | +0.078 |
| ltr24__logreg__notype-nogate__mined | vs exp17 (n=64, ref 0.719 → 0.662) | -0.057 [-0.130, -0.001] | 0.085 | ~0.081 | 12/17/35 | -0.062 | -0.031 |
| ltr24__logreg__notype-nogate__mined | vs lex13 (n=64, ref 0.683 → 0.662) | -0.021 [-0.062, +0.017] | 0.299 | ~0.306 | 12/14/38 | -0.031 | -0.016 |
| ltr24__logreg__notype-nogate__mined | vs bm25_01 (n=64, ref 0.601 → 0.662) | +0.061 [-0.001, +0.134] | 0.084 | ~0.084 | 21/10/33 | +0.062 | +0.016 |
| ltr24__logreg__notype-nogate__mined | vs convex05 (n=64, ref 0.622 → 0.662) | +0.040 [-0.008, +0.097] | 0.143 | ~0.147 | 14/13/37 | +0.062 | -0.016 |
| ltr24__logreg__notype-nogate__mined | vs convex05+bge@20 (n=64, ref 0.695 → 0.662) | -0.033 [-0.101, +0.022] | 0.295 | ~0.294 | 13/17/34 | -0.031 | +0.000 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.662) | -0.018 [-0.064, +0.021] | 0.405 | ~0.416 | 13/12/39 | -0.031 | -0.016 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap (n=64, ref 0.671 → 0.662) | -0.009 [-0.055, +0.029] | 0.678 | ~0.681 | 16/10/38 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bar_val (n=64, ref 0.696 → 0.655) | -0.042 [-0.119, +0.027] | 0.261 | ~0.257 | 14/16/34 | -0.047 | -0.047 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bar_full (n=64, ref 0.703 → 0.655) | -0.048 [-0.124, +0.017] | 0.183 | ~0.184 | 13/17/34 | -0.062 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp14 (n=64, ref 0.723 → 0.655) | -0.068 [-0.141, -0.007] | 0.053 | ~0.051 | 9/19/36 | -0.109 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp14_cheap (n=64, ref 0.603 → 0.655) | +0.051 [-0.012, +0.126] | 0.153 | ~0.154 | 17/14/33 | +0.062 | +0.047 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp17 (n=64, ref 0.719 → 0.655) | -0.065 [-0.149, +0.004] | 0.098 | ~0.099 | 12/15/37 | -0.078 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs lex13 (n=64, ref 0.683 → 0.655) | -0.029 [-0.075, +0.012] | 0.208 | ~0.208 | 11/14/39 | -0.047 | -0.047 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bm25_01 (n=64, ref 0.601 → 0.655) | +0.054 [-0.007, +0.128] | 0.128 | ~0.131 | 19/13/32 | +0.047 | -0.016 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05 (n=64, ref 0.622 → 0.655) | +0.033 [-0.025, +0.095] | 0.292 | ~0.294 | 15/15/34 | +0.047 | -0.047 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05+bge@20 (n=64, ref 0.695 → 0.655) | -0.040 [-0.118, +0.028] | 0.275 | ~0.281 | 12/18/34 | -0.047 | -0.031 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.655) | -0.025 [-0.081, +0.014] | 0.290 | ~0.309 | 10/13/41 | -0.047 | -0.047 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap (n=64, ref 0.671 → 0.655) | -0.016 [-0.063, +0.012] | 0.379 | ~0.403 | 12/9/43 | -0.047 | -0.031 |
| ltr24__logreg__notype-nobge__mined | vs bar_val (n=64, ref 0.696 → 0.532) | **-0.164** [-0.261, -0.078] | 0.001 | ~0.001 | 11/27/26 | -0.188 | -0.078 |
| ltr24__logreg__notype-nobge__mined | vs bar_full (n=64, ref 0.703 → 0.532) | **-0.171** [-0.266, -0.084] | 0.001 | ~0.000 | 10/29/25 | -0.203 | -0.094 |
| ltr24__logreg__notype-nobge__mined | vs exp14 (n=64, ref 0.723 → 0.532) | **-0.191** [-0.287, -0.099] | 0.000 | ~0.000 | 9/31/24 | -0.250 | -0.094 |
| ltr24__logreg__notype-nobge__mined | vs exp14_cheap (n=64, ref 0.603 → 0.532) | -0.071 [-0.171, +0.025] | 0.163 | ~0.160 | 16/28/20 | -0.078 | +0.016 |
| ltr24__logreg__notype-nobge__mined | vs exp17 (n=64, ref 0.719 → 0.532) | **-0.187** [-0.285, -0.097] | 0.000 | ~0.000 | 9/29/26 | -0.219 | -0.094 |
| ltr24__logreg__notype-nobge__mined | vs lex13 (n=64, ref 0.683 → 0.532) | **-0.151** [-0.232, -0.086] | 0.000 | ~0.000 | 11/24/29 | -0.188 | -0.078 |
| ltr24__logreg__notype-nobge__mined | vs bm25_01 (n=64, ref 0.601 → 0.532) | -0.069 [-0.157, +0.021] | 0.148 | ~0.149 | 17/23/24 | -0.094 | -0.047 |
| ltr24__logreg__notype-nobge__mined | vs convex05 (n=64, ref 0.622 → 0.532) | **-0.089** [-0.174, -0.011] | 0.040 | ~0.038 | 12/26/26 | -0.094 | -0.078 |
| ltr24__logreg__notype-nobge__mined | vs convex05+bge@20 (n=64, ref 0.695 → 0.532) | **-0.163** [-0.261, -0.073] | 0.001 | ~0.001 | 11/30/23 | -0.188 | -0.062 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.532) | **-0.148** [-0.235, -0.068] | 0.001 | ~0.001 | 11/28/25 | -0.188 | -0.078 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap (n=64, ref 0.671 → 0.532) | **-0.139** [-0.228, -0.060] | 0.002 | ~0.002 | 13/22/29 | -0.188 | -0.062 |
| ltr24__lgbm-tiny__small__mined | vs bar_val (n=64, ref 0.696 → 0.635) | -0.061 [-0.135, +0.002] | 0.080 | ~0.083 | 11/17/36 | -0.062 | -0.016 |
| ltr24__lgbm-tiny__small__mined | vs bar_full (n=64, ref 0.703 → 0.635) | -0.068 [-0.143, -0.004] | 0.057 | ~0.056 | 10/19/35 | -0.078 | -0.031 |
| ltr24__lgbm-tiny__small__mined | vs exp14 (n=64, ref 0.723 → 0.635) | **-0.087** [-0.162, -0.024] | 0.017 | ~0.015 | 9/21/34 | -0.125 | -0.031 |
| ltr24__lgbm-tiny__small__mined | vs exp14_cheap (n=64, ref 0.603 → 0.635) | +0.032 [-0.028, +0.100] | 0.340 | ~0.350 | 16/17/31 | +0.047 | +0.078 |
| ltr24__lgbm-tiny__small__mined | vs exp17 (n=64, ref 0.719 → 0.635) | **-0.084** [-0.167, -0.016] | 0.030 | ~0.027 | 10/18/36 | -0.094 | -0.031 |
| ltr24__lgbm-tiny__small__mined | vs lex13 (n=64, ref 0.683 → 0.635) | **-0.048** [-0.096, -0.006] | 0.044 | ~0.046 | 7/19/38 | -0.062 | -0.016 |
| ltr24__lgbm-tiny__small__mined | vs bm25_01 (n=64, ref 0.601 → 0.635) | +0.035 [-0.019, +0.099] | 0.264 | ~0.272 | 13/15/36 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__small__mined | vs convex05 (n=64, ref 0.622 → 0.635) | +0.014 [-0.039, +0.072] | 0.628 | ~0.632 | 13/15/36 | +0.031 | -0.016 |
| ltr24__lgbm-tiny__small__mined | vs convex05+bge@20 (n=64, ref 0.695 → 0.635) | -0.060 [-0.135, +0.007] | 0.102 | ~0.104 | 12/19/33 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.635) | -0.045 [-0.101, -0.004] | 0.071 | ~0.071 | 8/16/40 | -0.062 | -0.016 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap (n=64, ref 0.671 → 0.635) | -0.036 [-0.083, -0.006] | 0.068 | 0.066 | 7/13/44 | -0.062 | +0.000 |
| ltr24__logreg__small__mined | vs bar_val (n=64, ref 0.696 → 0.566) | **-0.131** [-0.215, -0.056] | 0.002 | ~0.001 | 9/23/32 | -0.141 | -0.094 |
| ltr24__logreg__small__mined | vs bar_full (n=64, ref 0.703 → 0.566) | **-0.137** [-0.222, -0.063] | 0.001 | ~0.001 | 8/24/32 | -0.156 | -0.109 |
| ltr24__logreg__small__mined | vs exp14 (n=64, ref 0.723 → 0.566) | **-0.157** [-0.263, -0.054] | 0.005 | ~0.005 | 11/28/25 | -0.203 | -0.109 |
| ltr24__logreg__small__mined | vs exp14_cheap (n=64, ref 0.603 → 0.566) | -0.037 [-0.144, +0.071] | 0.495 | ~0.497 | 19/20/25 | -0.031 | +0.000 |
| ltr24__logreg__small__mined | vs exp17 (n=64, ref 0.719 → 0.566) | **-0.153** [-0.243, -0.075] | 0.001 | ~0.001 | 8/24/32 | -0.172 | -0.109 |
| ltr24__logreg__small__mined | vs lex13 (n=64, ref 0.683 → 0.566) | **-0.117** [-0.206, -0.032] | 0.011 | ~0.009 | 10/22/32 | -0.141 | -0.094 |
| ltr24__logreg__small__mined | vs bm25_01 (n=64, ref 0.601 → 0.566) | -0.035 [-0.134, +0.062] | 0.485 | ~0.488 | 20/19/25 | -0.047 | -0.062 |
| ltr24__logreg__small__mined | vs convex05 (n=64, ref 0.622 → 0.566) | -0.056 [-0.145, +0.032] | 0.225 | ~0.224 | 16/22/26 | -0.047 | -0.094 |
| ltr24__logreg__small__mined | vs convex05+bge@20 (n=64, ref 0.695 → 0.566) | **-0.129** [-0.215, -0.052] | 0.003 | ~0.003 | 10/25/29 | -0.141 | -0.078 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.566) | **-0.114** [-0.215, -0.021] | 0.025 | ~0.025 | 16/22/26 | -0.141 | -0.094 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap (n=64, ref 0.671 → 0.566) | **-0.105** [-0.208, -0.008] | 0.043 | ~0.043 | 16/21/27 | -0.141 | -0.078 |
| ltr24__lgbm-tiny__notype__pooled | vs bar_val (n=64, ref 0.696 → 0.703) | +0.006 [-0.056, +0.056] | 0.827 | ~0.833 | 14/12/38 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled | vs bar_full (n=64, ref 0.703 → 0.703) | -0.000 [-0.061, +0.046] | 0.992 | ~0.992 | 12/11/41 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled | vs exp14 (n=64, ref 0.723 → 0.703) | -0.020 [-0.077, +0.031] | 0.480 | ~0.491 | 10/13/41 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled | vs exp14_cheap (n=64, ref 0.603 → 0.703) | **+0.099** [+0.046, +0.168] | 0.002 | ~0.002 | 22/10/32 | +0.141 | +0.109 |
| ltr24__lgbm-tiny__notype__pooled | vs exp17 (n=64, ref 0.719 → 0.703) | -0.017 [-0.084, +0.035] | 0.585 | ~0.593 | 14/12/38 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled | vs lex13 (n=64, ref 0.683 → 0.703) | +0.019 [-0.010, +0.062] | 0.281 | 0.300 | 12/6/46 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled | vs bm25_01 (n=64, ref 0.601 → 0.703) | **+0.102** [+0.045, +0.177] | 0.004 | ~0.003 | 27/5/32 | +0.125 | +0.047 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05 (n=64, ref 0.622 → 0.703) | **+0.081** [+0.040, +0.143] | 0.002 | ~0.001 | 19/7/38 | +0.125 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05+bge@20 (n=64, ref 0.695 → 0.703) | +0.008 [-0.054, +0.059] | 0.788 | ~0.790 | 15/12/37 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.703) | +0.023 [-0.020, +0.064] | 0.300 | ~0.307 | 16/6/42 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap (n=64, ref 0.671 → 0.703) | +0.032 [+0.002, +0.069] | 0.069 | ~0.070 | 19/4/41 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__notype__pooled | vs exp24 mined-only (same features) (n=64, ref 0.659 → 0.703) | +0.043 [+0.007, +0.095] | 0.053 | ~0.051 | 19/5/40 | +0.062 | +0.062 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.684) | -0.012 [-0.075, +0.039] | 0.684 | ~0.691 | 13/15/36 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.684) | -0.018 [-0.081, +0.029] | 0.508 | ~0.518 | 11/15/38 | -0.016 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.684) | -0.038 [-0.101, +0.017] | 0.217 | ~0.221 | 9/15/40 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.684) | **+0.081** [+0.024, +0.151] | 0.015 | ~0.014 | 20/11/33 | +0.109 | +0.109 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.684) | -0.035 [-0.103, +0.018] | 0.255 | ~0.264 | 13/14/37 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.684) | +0.001 [-0.031, +0.033] | 0.939 | 0.938 | 11/6/47 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.684) | **+0.084** [+0.023, +0.160] | 0.020 | ~0.020 | 25/7/32 | +0.094 | +0.047 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.684) | **+0.063** [+0.015, +0.126] | 0.025 | ~0.022 | 19/8/37 | +0.094 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.684) | -0.010 [-0.074, +0.041] | 0.724 | ~0.731 | 14/14/36 | +0.000 | +0.031 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.684) | +0.004 [-0.044, +0.046] | 0.846 | ~0.852 | 14/8/42 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.684) | +0.014 [-0.027, +0.047] | 0.472 | ~0.484 | 18/4/42 | +0.000 | +0.031 |
| ltr24__logreg__notype__pooled | vs bar_val (n=64, ref 0.696 → 0.692) | -0.004 [-0.060, +0.049] | 0.888 | ~0.891 | 13/15/36 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled | vs bar_full (n=64, ref 0.703 → 0.692) | -0.011 [-0.065, +0.039] | 0.692 | ~0.697 | 11/16/37 | -0.016 | -0.016 |
| ltr24__logreg__notype__pooled | vs exp14 (n=64, ref 0.723 → 0.692) | -0.030 [-0.096, +0.041] | 0.397 | ~0.405 | 9/18/37 | -0.062 | -0.016 |
| ltr24__logreg__notype__pooled | vs exp14_cheap (n=64, ref 0.603 → 0.692) | **+0.089** [+0.025, +0.170] | 0.019 | ~0.018 | 21/11/32 | +0.109 | +0.094 |
| ltr24__logreg__notype__pooled | vs exp17 (n=64, ref 0.719 → 0.692) | -0.027 [-0.092, +0.024] | 0.363 | ~0.376 | 14/13/37 | -0.031 | -0.016 |
| ltr24__logreg__notype__pooled | vs lex13 (n=64, ref 0.683 → 0.692) | +0.009 [-0.032, +0.066] | 0.711 | 0.723 | 12/8/44 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled | vs bm25_01 (n=64, ref 0.601 → 0.692) | **+0.092** [+0.021, +0.179] | 0.028 | ~0.027 | 23/11/30 | +0.094 | +0.031 |
| ltr24__logreg__notype__pooled | vs convex05 (n=64, ref 0.622 → 0.692) | **+0.071** [+0.010, +0.144] | 0.042 | ~0.040 | 18/11/35 | +0.094 | +0.000 |
| ltr24__logreg__notype__pooled | vs convex05+bge@20 (n=64, ref 0.695 → 0.692) | -0.003 [-0.056, +0.050] | 0.929 | ~0.931 | 12/15/37 | +0.000 | +0.016 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.692) | +0.012 [-0.041, +0.067] | 0.662 | ~0.673 | 16/9/39 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap (n=64, ref 0.671 → 0.692) | +0.021 [-0.029, +0.082] | 0.451 | ~0.459 | 16/9/39 | +0.000 | +0.016 |
| ltr24__logreg__notype__pooled | vs exp24 mined-only (same features) (n=64, ref 0.620 → 0.692) | **+0.073** [+0.017, +0.144] | 0.027 | ~0.025 | 18/7/39 | +0.078 | +0.016 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.687) | -0.009 [-0.064, +0.045] | 0.742 | ~0.742 | 13/16/35 | -0.016 | +0.000 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.687) | -0.016 [-0.069, +0.035] | 0.554 | ~0.561 | 11/17/36 | -0.031 | -0.016 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.687) | -0.035 [-0.101, +0.027] | 0.291 | ~0.294 | 8/18/38 | -0.078 | -0.016 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.687) | **+0.084** [+0.021, +0.159] | 0.021 | ~0.019 | 20/12/32 | +0.094 | +0.094 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.687) | -0.032 [-0.096, +0.019] | 0.279 | ~0.286 | 14/14/36 | -0.047 | -0.016 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.687) | +0.004 [-0.038, +0.046] | 0.855 | ~0.858 | 13/8/43 | -0.016 | +0.000 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.687) | **+0.086** [+0.017, +0.168] | 0.030 | ~0.029 | 22/12/30 | +0.078 | +0.031 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.687) | **+0.066** [+0.007, +0.133] | 0.045 | ~0.043 | 17/12/35 | +0.078 | +0.000 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.687) | -0.008 [-0.061, +0.045] | 0.778 | ~0.783 | 11/18/35 | -0.016 | +0.016 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.687) | +0.007 [-0.042, +0.052] | 0.775 | ~0.777 | 15/9/40 | -0.016 | +0.000 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.687) | +0.016 [-0.033, +0.064] | 0.522 | ~0.525 | 18/8/38 | -0.016 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled | vs bar_val (n=64, ref 0.696 → 0.699) | +0.003 [-0.058, +0.051] | 0.911 | ~0.912 | 15/10/39 | +0.016 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled | vs bar_full (n=64, ref 0.703 → 0.699) | -0.004 [-0.062, +0.041] | 0.894 | ~0.898 | 13/11/40 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp14 (n=64, ref 0.723 → 0.699) | -0.023 [-0.082, +0.029] | 0.426 | ~0.438 | 11/12/41 | -0.047 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp14_cheap (n=64, ref 0.603 → 0.699) | **+0.096** [+0.045, +0.162] | 0.002 | ~0.001 | 22/8/34 | +0.125 | +0.109 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp17 (n=64, ref 0.719 → 0.699) | -0.020 [-0.084, +0.029] | 0.492 | ~0.504 | 14/11/39 | -0.016 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled | vs lex13 (n=64, ref 0.683 → 0.699) | +0.016 [-0.019, +0.060] | 0.417 | 0.424 | 14/6/44 | +0.016 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled | vs bm25_01 (n=64, ref 0.601 → 0.699) | **+0.099** [+0.044, +0.171] | 0.003 | ~0.002 | 26/4/34 | +0.109 | +0.047 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05 (n=64, ref 0.622 → 0.699) | **+0.078** [+0.040, +0.134] | 0.002 | ~0.000 | 22/4/38 | +0.109 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05+bge@20 (n=64, ref 0.695 → 0.699) | +0.005 [-0.058, +0.052] | 0.870 | ~0.872 | 15/11/38 | +0.016 | +0.031 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.699) | +0.019 [-0.027, +0.063] | 0.410 | ~0.412 | 17/8/39 | +0.016 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap (n=64, ref 0.671 → 0.699) | +0.029 [-0.007, +0.067] | 0.146 | ~0.154 | 18/6/40 | +0.016 | +0.031 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp24 mined-only (same features) (n=64, ref 0.638 → 0.699) | **+0.061** [+0.015, +0.115] | 0.019 | ~0.018 | 22/7/35 | +0.078 | +0.062 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.705) | +0.009 [-0.057, +0.059] | 0.772 | ~0.777 | 16/11/37 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.705) | +0.002 [-0.062, +0.050] | 0.943 | ~0.945 | 14/12/38 | +0.016 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.705) | -0.018 [-0.078, +0.034] | 0.545 | ~0.557 | 11/12/41 | -0.031 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.705) | **+0.102** [+0.048, +0.172] | 0.002 | ~0.001 | 22/8/34 | +0.141 | +0.125 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.705) | -0.014 [-0.081, +0.037] | 0.632 | ~0.644 | 14/12/38 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.705) | +0.022 [-0.009, +0.064] | 0.235 | 0.245 | 13/5/46 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.705) | **+0.104** [+0.046, +0.178] | 0.003 | ~0.002 | 24/6/34 | +0.125 | +0.062 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.705) | **+0.084** [+0.041, +0.146] | 0.003 | ~0.001 | 19/7/38 | +0.125 | +0.031 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.705) | +0.010 [-0.056, +0.063] | 0.739 | ~0.743 | 15/12/37 | +0.031 | +0.047 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.705) | +0.025 [-0.018, +0.067] | 0.267 | ~0.274 | 16/5/43 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.705) | +0.034 [+0.003, +0.072] | 0.060 | 0.059 | 17/3/44 | +0.031 | +0.047 |
| ltr24__logreg__withtype__pooled | vs bar_val (n=64, ref 0.696 → 0.645) | -0.051 [-0.119, +0.008] | 0.117 | ~0.117 | 11/19/34 | -0.062 | -0.016 |
| ltr24__logreg__withtype__pooled | vs bar_full (n=64, ref 0.703 → 0.645) | -0.058 [-0.123, -0.002] | 0.066 | ~0.067 | 9/18/37 | -0.078 | -0.031 |
| ltr24__logreg__withtype__pooled | vs exp14 (n=64, ref 0.723 → 0.645) | **-0.077** [-0.151, -0.007] | 0.040 | ~0.038 | 9/21/34 | -0.125 | -0.031 |
| ltr24__logreg__withtype__pooled | vs exp14_cheap (n=64, ref 0.603 → 0.645) | +0.042 [-0.017, +0.111] | 0.212 | ~0.215 | 18/13/33 | +0.047 | +0.078 |
| ltr24__logreg__withtype__pooled | vs exp17 (n=64, ref 0.719 → 0.645) | **-0.074** [-0.153, -0.012] | 0.043 | ~0.040 | 13/17/34 | -0.094 | -0.031 |
| ltr24__logreg__withtype__pooled | vs lex13 (n=64, ref 0.683 → 0.645) | -0.038 [-0.103, +0.018] | 0.223 | ~0.222 | 13/15/36 | -0.062 | -0.016 |
| ltr24__logreg__withtype__pooled | vs bm25_01 (n=64, ref 0.601 → 0.645) | +0.044 [-0.035, +0.131] | 0.308 | ~0.305 | 21/15/28 | +0.031 | +0.016 |
| ltr24__logreg__withtype__pooled | vs convex05 (n=64, ref 0.622 → 0.645) | +0.023 [-0.055, +0.103] | 0.570 | ~0.568 | 20/15/29 | +0.031 | -0.016 |
| ltr24__logreg__withtype__pooled | vs convex05+bge@20 (n=64, ref 0.695 → 0.645) | -0.050 [-0.117, +0.008] | 0.122 | ~0.125 | 11/19/34 | -0.062 | +0.000 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.645) | -0.035 [-0.101, +0.017] | 0.251 | ~0.258 | 14/13/37 | -0.062 | -0.016 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap (n=64, ref 0.671 → 0.645) | -0.026 [-0.094, +0.034] | 0.437 | ~0.446 | 16/12/36 | -0.062 | +0.000 |
| ltr24__logreg__withtype__pooled | vs exp24 mined-only (same features) (n=64, ref 0.502 → 0.645) | **+0.143** [+0.068, +0.225] | 0.001 | ~0.000 | 28/9/27 | +0.172 | +0.078 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.636) | -0.060 [-0.128, -0.003] | 0.064 | ~0.068 | 9/20/35 | -0.062 | -0.016 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.636) | **-0.067** [-0.134, -0.013] | 0.033 | ~0.030 | 7/18/39 | -0.078 | -0.031 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.636) | **-0.086** [-0.163, -0.017] | 0.025 | ~0.022 | 9/21/34 | -0.125 | -0.031 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.636) | +0.033 [-0.028, +0.101] | 0.332 | ~0.338 | 18/14/32 | +0.047 | +0.078 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.636) | **-0.083** [-0.160, -0.021] | 0.023 | ~0.023 | 10/18/36 | -0.094 | -0.031 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.636) | -0.047 [-0.115, +0.010] | 0.142 | ~0.148 | 13/16/35 | -0.062 | -0.016 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.636) | +0.036 [-0.046, +0.122] | 0.418 | ~0.418 | 22/13/29 | +0.031 | +0.016 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.636) | +0.015 [-0.063, +0.094] | 0.718 | ~0.722 | 18/17/29 | +0.031 | -0.016 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.636) | -0.059 [-0.127, -0.002] | 0.068 | ~0.067 | 9/20/35 | -0.062 | +0.000 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.636) | -0.044 [-0.112, +0.010] | 0.161 | ~0.163 | 14/15/35 | -0.062 | -0.016 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.636) | -0.035 [-0.104, +0.025] | 0.307 | ~0.315 | 17/13/34 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bar_val (n=64, ref 0.696 → 0.707) | +0.011 [-0.053, +0.060] | 0.716 | ~0.723 | 15/11/38 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bar_full (n=64, ref 0.703 → 0.707) | +0.004 [-0.058, +0.051] | 0.886 | ~0.887 | 14/11/39 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp14 (n=64, ref 0.723 → 0.707) | -0.016 [-0.074, +0.035] | 0.582 | ~0.590 | 11/13/40 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp14_cheap (n=64, ref 0.603 → 0.707) | **+0.103** [+0.049, +0.173] | 0.002 | ~0.001 | 22/10/32 | +0.141 | +0.109 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp17 (n=64, ref 0.719 → 0.707) | -0.012 [-0.076, +0.038] | 0.671 | ~0.680 | 14/12/38 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs lex13 (n=64, ref 0.683 → 0.707) | +0.024 [-0.007, +0.066] | 0.193 | 0.197 | 13/5/46 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bm25_01 (n=64, ref 0.601 → 0.707) | **+0.106** [+0.048, +0.180] | 0.003 | ~0.002 | 27/5/32 | +0.125 | +0.047 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05 (n=64, ref 0.622 → 0.707) | **+0.085** [+0.044, +0.148] | 0.002 | ~0.000 | 19/7/38 | +0.125 | +0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05+bge@20 (n=64, ref 0.695 → 0.707) | +0.012 [-0.051, +0.064] | 0.685 | ~0.690 | 15/12/37 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.707) | +0.027 [-0.017, +0.069] | 0.231 | ~0.235 | 16/6/42 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap (n=64, ref 0.671 → 0.707) | **+0.036** [+0.005, +0.074] | 0.048 | ~0.046 | 19/4/41 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp24 mined-only (same features) (n=64, ref 0.671 → 0.707) | +0.035 [+0.005, +0.078] | 0.060 | ~0.052 | 16/5/43 | +0.047 | +0.047 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.698) | +0.001 [-0.066, +0.059] | 0.969 | ~0.969 | 14/13/37 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.698) | -0.005 [-0.070, +0.050] | 0.860 | ~0.862 | 12/14/38 | +0.000 | -0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.698) | -0.025 [-0.087, +0.028] | 0.400 | ~0.407 | 10/15/39 | -0.047 | -0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.698) | **+0.094** [+0.042, +0.165] | 0.004 | ~0.002 | 20/9/35 | +0.125 | +0.094 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.698) | -0.021 [-0.089, +0.036] | 0.492 | ~0.497 | 12/13/39 | -0.016 | -0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.698) | +0.014 [-0.013, +0.046] | 0.341 | 0.352 | 12/5/47 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.698) | **+0.097** [+0.041, +0.172] | 0.005 | ~0.004 | 24/6/34 | +0.109 | +0.031 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.698) | **+0.076** [+0.030, +0.141] | 0.008 | ~0.006 | 20/7/37 | +0.109 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.698) | +0.003 [-0.065, +0.061] | 0.932 | ~0.930 | 14/13/37 | +0.016 | +0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.698) | +0.018 [-0.024, +0.057] | 0.404 | ~0.413 | 15/8/41 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.698) | +0.027 [-0.002, +0.060] | 0.103 | 0.105 | 17/3/44 | +0.016 | +0.016 |
| ltr24__logreg__notype-nogate__pooled | vs bar_val (n=64, ref 0.696 → 0.683) | -0.013 [-0.076, +0.042] | 0.660 | ~0.669 | 13/15/36 | +0.000 | -0.016 |
| ltr24__logreg__notype-nogate__pooled | vs bar_full (n=64, ref 0.703 → 0.683) | -0.020 [-0.080, +0.033] | 0.490 | ~0.500 | 11/16/37 | -0.016 | -0.031 |
| ltr24__logreg__notype-nogate__pooled | vs exp14 (n=64, ref 0.723 → 0.683) | -0.039 [-0.106, +0.019] | 0.229 | ~0.230 | 9/17/38 | -0.062 | -0.031 |
| ltr24__logreg__notype-nogate__pooled | vs exp14_cheap (n=64, ref 0.603 → 0.683) | **+0.080** [+0.017, +0.154] | 0.028 | ~0.024 | 21/12/31 | +0.109 | +0.078 |
| ltr24__logreg__notype-nogate__pooled | vs exp17 (n=64, ref 0.719 → 0.683) | -0.036 [-0.104, +0.017] | 0.245 | ~0.254 | 14/13/37 | -0.031 | -0.031 |
| ltr24__logreg__notype-nogate__pooled | vs lex13 (n=64, ref 0.683 → 0.683) | -0.000 [-0.035, +0.037] | 0.998 | 0.998 | 11/9/44 | +0.000 | -0.016 |
| ltr24__logreg__notype-nogate__pooled | vs bm25_01 (n=64, ref 0.601 → 0.683) | **+0.083** [+0.017, +0.162] | 0.032 | ~0.031 | 22/10/32 | +0.094 | +0.016 |
| ltr24__logreg__notype-nogate__pooled | vs convex05 (n=64, ref 0.622 → 0.683) | **+0.062** [+0.006, +0.126] | 0.048 | ~0.049 | 16/10/38 | +0.094 | -0.016 |
| ltr24__logreg__notype-nogate__pooled | vs convex05+bge@20 (n=64, ref 0.695 → 0.683) | -0.012 [-0.073, +0.043] | 0.693 | ~0.698 | 13/14/37 | +0.000 | +0.000 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.683) | +0.003 [-0.047, +0.045] | 0.895 | ~0.901 | 14/10/40 | +0.000 | -0.016 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap (n=64, ref 0.671 → 0.683) | +0.012 [-0.033, +0.054] | 0.588 | ~0.597 | 15/9/40 | +0.000 | +0.000 |
| ltr24__logreg__notype-nogate__pooled | vs exp24 mined-only (same features) (n=64, ref 0.662 → 0.683) | +0.021 [+0.003, +0.056] | 0.099 | 0.108 | 12/7/45 | +0.031 | +0.000 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.681) | -0.015 [-0.078, +0.039] | 0.613 | ~0.620 | 13/15/36 | +0.000 | -0.031 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.681) | -0.022 [-0.080, +0.031] | 0.444 | ~0.449 | 11/16/37 | -0.016 | -0.047 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.681) | -0.041 [-0.108, +0.019] | 0.213 | ~0.216 | 8/18/38 | -0.062 | -0.047 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.681) | **+0.078** [+0.015, +0.152] | 0.033 | ~0.031 | 20/12/32 | +0.109 | +0.062 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.681) | -0.038 [-0.105, +0.015] | 0.221 | ~0.230 | 14/13/37 | -0.031 | -0.047 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.681) | -0.002 [-0.039, +0.035] | 0.916 | ~0.921 | 12/9/43 | +0.000 | -0.031 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.681) | **+0.081** [+0.013, +0.159] | 0.037 | ~0.035 | 22/11/31 | +0.094 | +0.000 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.681) | +0.060 [+0.004, +0.125] | 0.058 | ~0.059 | 15/13/36 | +0.094 | -0.031 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.681) | -0.014 [-0.075, +0.041] | 0.644 | ~0.651 | 12/15/37 | +0.000 | -0.016 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.681) | +0.001 [-0.046, +0.043] | 0.960 | ~0.963 | 13/10/41 | +0.000 | -0.031 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.681) | +0.010 [-0.037, +0.052] | 0.655 | ~0.664 | 17/8/39 | +0.000 | -0.016 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bar_val (n=64, ref 0.696 → 0.701) | +0.005 [-0.063, +0.058] | 0.875 | ~0.880 | 14/7/43 | +0.016 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bar_full (n=64, ref 0.703 → 0.701) | -0.002 [-0.071, +0.053] | 0.956 | ~0.958 | 13/9/42 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp14 (n=64, ref 0.723 → 0.701) | -0.021 [-0.079, +0.028] | 0.446 | ~0.455 | 12/11/41 | -0.047 | +0.016 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp14_cheap (n=64, ref 0.603 → 0.701) | **+0.098** [+0.047, +0.164] | 0.002 | ~0.001 | 24/7/33 | +0.125 | +0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp17 (n=64, ref 0.719 → 0.701) | -0.018 [-0.091, +0.040] | 0.593 | ~0.606 | 14/9/41 | -0.016 | +0.016 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs lex13 (n=64, ref 0.683 → 0.701) | +0.018 [-0.011, +0.051] | 0.260 | ~0.266 | 15/6/43 | +0.016 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bm25_01 (n=64, ref 0.601 → 0.701) | **+0.101** [+0.045, +0.176] | 0.004 | ~0.003 | 25/6/33 | +0.109 | +0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05 (n=64, ref 0.622 → 0.701) | **+0.080** [+0.034, +0.144] | 0.005 | ~0.003 | 20/6/38 | +0.109 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05+bge@20 (n=64, ref 0.695 → 0.701) | +0.006 [-0.065, +0.065] | 0.847 | ~0.851 | 15/9/40 | +0.016 | +0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.701) | +0.021 [-0.033, +0.066] | 0.411 | ~0.417 | 19/7/38 | +0.016 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap (n=64, ref 0.671 → 0.701) | +0.030 [-0.009, +0.071] | 0.145 | ~0.151 | 18/6/40 | +0.016 | +0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp24 mined-only (same features) (n=64, ref 0.655 → 0.701) | **+0.047** [+0.009, +0.093] | 0.033 | ~0.032 | 18/6/40 | +0.062 | +0.078 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.697) | +0.000 [-0.064, +0.053] | 0.997 | ~0.998 | 12/10/42 | +0.016 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.697) | -0.006 [-0.071, +0.049] | 0.833 | ~0.838 | 12/12/40 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.697) | -0.026 [-0.085, +0.025] | 0.365 | ~0.382 | 11/13/40 | -0.047 | +0.016 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.697) | **+0.093** [+0.040, +0.159] | 0.003 | ~0.002 | 23/8/33 | +0.125 | +0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.697) | -0.023 [-0.092, +0.035] | 0.487 | ~0.491 | 13/13/38 | -0.016 | +0.016 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.697) | +0.013 [-0.014, +0.045] | 0.377 | 0.390 | 12/6/46 | +0.016 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.697) | **+0.096** [+0.039, +0.171] | 0.007 | ~0.005 | 24/5/35 | +0.109 | +0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.697) | **+0.075** [+0.027, +0.139] | 0.010 | ~0.007 | 19/6/39 | +0.109 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.697) | +0.002 [-0.065, +0.061] | 0.960 | ~0.960 | 14/13/37 | +0.016 | +0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.697) | +0.016 [-0.036, +0.062] | 0.519 | ~0.526 | 16/7/41 | +0.016 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.697) | +0.026 [-0.016, +0.064] | 0.226 | ~0.238 | 20/5/39 | +0.016 | +0.047 |
| ltr24__logreg__notype-nobge__pooled | vs bar_val (n=64, ref 0.696 → 0.674) | -0.023 [-0.093, +0.040] | 0.496 | ~0.507 | 12/16/36 | -0.016 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs bar_full (n=64, ref 0.703 → 0.674) | -0.029 [-0.100, +0.034] | 0.389 | ~0.385 | 11/18/35 | -0.031 | -0.016 |
| ltr24__logreg__notype-nobge__pooled | vs exp14 (n=64, ref 0.723 → 0.674) | -0.049 [-0.115, +0.010] | 0.138 | ~0.136 | 9/18/37 | -0.078 | -0.016 |
| ltr24__logreg__notype-nobge__pooled | vs exp14_cheap (n=64, ref 0.603 → 0.674) | **+0.070** [+0.016, +0.138] | 0.029 | ~0.029 | 20/10/34 | +0.094 | +0.094 |
| ltr24__logreg__notype-nobge__pooled | vs exp17 (n=64, ref 0.719 → 0.674) | -0.045 [-0.120, +0.020] | 0.201 | ~0.201 | 14/15/35 | -0.047 | -0.016 |
| ltr24__logreg__notype-nobge__pooled | vs lex13 (n=64, ref 0.683 → 0.674) | -0.010 [-0.048, +0.029] | 0.631 | ~0.641 | 11/11/42 | -0.016 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs bm25_01 (n=64, ref 0.601 → 0.674) | **+0.073** [+0.012, +0.148] | 0.043 | ~0.042 | 19/10/35 | +0.078 | +0.031 |
| ltr24__logreg__notype-nobge__pooled | vs convex05 (n=64, ref 0.622 → 0.674) | +0.052 [+0.000, +0.118] | 0.085 | ~0.086 | 17/11/36 | +0.078 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs convex05+bge@20 (n=64, ref 0.695 → 0.674) | -0.021 [-0.093, +0.045] | 0.545 | ~0.544 | 14/16/34 | -0.016 | +0.016 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.674) | -0.006 [-0.058, +0.034] | 0.787 | ~0.795 | 13/9/42 | -0.016 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap (n=64, ref 0.671 → 0.674) | +0.003 [-0.041, +0.042] | 0.897 | ~0.901 | 16/9/39 | -0.016 | +0.016 |
| ltr24__logreg__notype-nobge__pooled | vs exp24 mined-only (same features) (n=64, ref 0.532 → 0.674) | **+0.142** [+0.073, +0.229] | 0.001 | ~0.001 | 29/8/27 | +0.172 | +0.078 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.659) | -0.037 [-0.111, +0.025] | 0.281 | ~0.284 | 13/17/34 | -0.031 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.659) | -0.044 [-0.115, +0.015] | 0.186 | ~0.188 | 11/18/35 | -0.047 | -0.016 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.659) | -0.063 [-0.133, -0.000] | 0.069 | ~0.070 | 8/20/36 | -0.094 | -0.016 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.659) | +0.056 [-0.009, +0.132] | 0.129 | ~0.130 | 19/13/32 | +0.078 | +0.094 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.659) | -0.060 [-0.136, +0.001] | 0.086 | ~0.087 | 14/15/35 | -0.062 | -0.016 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.659) | -0.024 [-0.070, +0.018] | 0.291 | ~0.299 | 11/12/41 | -0.031 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.659) | +0.058 [-0.011, +0.140] | 0.139 | ~0.147 | 19/15/30 | +0.062 | +0.031 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.659) | +0.038 [-0.021, +0.104] | 0.245 | ~0.247 | 15/14/35 | +0.062 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.659) | -0.036 [-0.108, +0.026] | 0.297 | ~0.298 | 12/17/35 | -0.031 | +0.016 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.659) | -0.021 [-0.079, +0.023] | 0.421 | ~0.427 | 11/10/43 | -0.031 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.659) | -0.012 [-0.064, +0.030] | 0.625 | ~0.630 | 14/9/41 | -0.031 | +0.016 |
| ltr24__lgbm-tiny__small__pooled | vs bar_val (n=64, ref 0.696 → 0.694) | -0.003 [-0.065, +0.046] | 0.928 | ~0.927 | 12/11/41 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs bar_full (n=64, ref 0.703 → 0.694) | -0.009 [-0.070, +0.036] | 0.734 | ~0.743 | 10/11/43 | +0.000 | -0.016 |
| ltr24__lgbm-tiny__small__pooled | vs exp14 (n=64, ref 0.723 → 0.694) | -0.029 [-0.088, +0.025] | 0.328 | ~0.335 | 12/13/39 | -0.047 | -0.016 |
| ltr24__lgbm-tiny__small__pooled | vs exp14_cheap (n=64, ref 0.603 → 0.694) | **+0.090** [+0.038, +0.157] | 0.004 | ~0.003 | 22/8/34 | +0.125 | +0.094 |
| ltr24__lgbm-tiny__small__pooled | vs exp17 (n=64, ref 0.719 → 0.694) | -0.025 [-0.093, +0.024] | 0.398 | ~0.411 | 10/12/42 | -0.016 | -0.016 |
| ltr24__lgbm-tiny__small__pooled | vs lex13 (n=64, ref 0.683 → 0.694) | +0.011 [-0.025, +0.054] | 0.596 | 0.606 | 9/8/47 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs bm25_01 (n=64, ref 0.601 → 0.694) | **+0.093** [+0.039, +0.166] | 0.006 | ~0.004 | 24/7/33 | +0.109 | +0.031 |
| ltr24__lgbm-tiny__small__pooled | vs convex05 (n=64, ref 0.622 → 0.694) | **+0.072** [+0.034, +0.129] | 0.003 | ~0.002 | 21/6/37 | +0.109 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs convex05+bge@20 (n=64, ref 0.695 → 0.694) | -0.001 [-0.064, +0.048] | 0.970 | ~0.971 | 14/11/39 | +0.016 | +0.016 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.694) | +0.014 [-0.032, +0.057] | 0.556 | ~0.558 | 15/10/39 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap (n=64, ref 0.671 → 0.694) | +0.023 [-0.013, +0.061] | 0.235 | ~0.245 | 17/5/42 | +0.016 | +0.016 |
| ltr24__lgbm-tiny__small__pooled | vs exp24 mined-only (same features) (n=64, ref 0.635 → 0.694) | **+0.059** [+0.014, +0.113] | 0.023 | ~0.022 | 17/7/40 | +0.078 | +0.016 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.665) | -0.031 [-0.097, +0.021] | 0.294 | ~0.302 | 12/14/38 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.665) | -0.038 [-0.103, +0.009] | 0.182 | ~0.181 | 10/15/39 | -0.047 | -0.016 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.665) | -0.058 [-0.124, +0.000] | 0.079 | ~0.077 | 10/17/37 | -0.094 | -0.016 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.665) | +0.062 [+0.001, +0.133] | 0.075 | ~0.072 | 20/12/32 | +0.078 | +0.094 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.665) | -0.054 [-0.124, -0.002] | 0.084 | ~0.079 | 9/15/40 | -0.062 | -0.016 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.665) | -0.018 [-0.060, +0.019] | 0.377 | ~0.389 | 9/12/43 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.665) | +0.064 [+0.001, +0.139] | 0.078 | ~0.078 | 22/10/32 | +0.062 | +0.031 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.665) | +0.043 [-0.007, +0.099] | 0.114 | ~0.111 | 18/9/37 | +0.062 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.665) | -0.030 [-0.097, +0.021] | 0.319 | ~0.329 | 13/14/37 | -0.031 | +0.016 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.665) | -0.015 [-0.066, +0.027] | 0.534 | ~0.540 | 12/12/40 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.665) | -0.006 [-0.054, +0.036] | 0.801 | ~0.803 | 15/8/41 | -0.031 | +0.016 |
| ltr24__logreg__small__pooled | vs bar_val (n=64, ref 0.696 → 0.682) | -0.014 [-0.076, +0.047] | 0.661 | ~0.669 | 11/14/39 | +0.000 | +0.000 |
| ltr24__logreg__small__pooled | vs bar_full (n=64, ref 0.703 → 0.682) | -0.021 [-0.079, +0.037] | 0.498 | ~0.500 | 9/13/42 | -0.016 | -0.016 |
| ltr24__logreg__small__pooled | vs exp14 (n=64, ref 0.723 → 0.682) | -0.040 [-0.115, +0.034] | 0.307 | ~0.311 | 11/17/36 | -0.062 | -0.016 |
| ltr24__logreg__small__pooled | vs exp14_cheap (n=64, ref 0.603 → 0.682) | **+0.079** [+0.008, +0.162] | 0.048 | ~0.049 | 23/9/32 | +0.109 | +0.094 |
| ltr24__logreg__small__pooled | vs exp17 (n=64, ref 0.719 → 0.682) | -0.037 [-0.107, +0.025] | 0.281 | ~0.287 | 11/14/39 | -0.031 | -0.016 |
| ltr24__logreg__small__pooled | vs lex13 (n=64, ref 0.683 → 0.682) | -0.001 [-0.058, +0.058] | 0.978 | ~0.980 | 14/10/40 | +0.000 | +0.000 |
| ltr24__logreg__small__pooled | vs bm25_01 (n=64, ref 0.601 → 0.682) | +0.082 [+0.003, +0.169] | 0.063 | ~0.064 | 26/9/29 | +0.094 | +0.031 |
| ltr24__logreg__small__pooled | vs convex05 (n=64, ref 0.622 → 0.682) | +0.061 [-0.006, +0.134] | 0.094 | ~0.095 | 21/11/32 | +0.094 | +0.000 |
| ltr24__logreg__small__pooled | vs convex05+bge@20 (n=64, ref 0.695 → 0.682) | -0.012 [-0.074, +0.046] | 0.691 | ~0.697 | 11/14/39 | +0.000 | +0.016 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.682) | +0.002 [-0.062, +0.068] | 0.944 | ~0.945 | 17/9/38 | +0.000 | +0.000 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap (n=64, ref 0.671 → 0.682) | +0.012 [-0.051, +0.077] | 0.726 | ~0.728 | 17/8/39 | +0.000 | +0.016 |
| ltr24__logreg__small__pooled | vs exp24 mined-only (same features) (n=64, ref 0.566 → 0.682) | **+0.117** [+0.054, +0.197] | 0.002 | ~0.001 | 27/5/32 | +0.141 | +0.094 |
| ltr24__logreg__small__pooled | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.684) | -0.012 [-0.074, +0.049] | 0.700 | ~0.702 | 11/14/39 | +0.016 | -0.016 |
| ltr24__logreg__small__pooled | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.684) | -0.019 [-0.078, +0.038] | 0.534 | ~0.536 | 9/13/42 | +0.000 | -0.031 |
| ltr24__logreg__small__pooled | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.684) | -0.038 [-0.116, +0.046] | 0.365 | ~0.366 | 11/17/36 | -0.047 | -0.031 |
| ltr24__logreg__small__pooled | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.684) | +0.081 [+0.001, +0.172] | 0.069 | ~0.070 | 22/11/31 | +0.125 | +0.078 |
| ltr24__logreg__small__pooled | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.684) | -0.035 [-0.106, +0.027] | 0.304 | ~0.311 | 11/14/39 | -0.016 | -0.031 |
| ltr24__logreg__small__pooled | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.684) | +0.001 [-0.063, +0.066] | 0.981 | ~0.983 | 14/11/39 | +0.016 | -0.016 |
| ltr24__logreg__small__pooled | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.684) | +0.083 [-0.001, +0.179] | 0.079 | ~0.078 | 24/12/28 | +0.109 | +0.016 |
| ltr24__logreg__small__pooled | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.684) | +0.063 [-0.012, +0.145] | 0.121 | ~0.125 | 20/13/31 | +0.109 | -0.016 |
| ltr24__logreg__small__pooled | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.684) | -0.011 [-0.072, +0.050] | 0.731 | ~0.736 | 10/14/40 | +0.016 | +0.000 |
| ltr24__logreg__small__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.684) | +0.004 [-0.065, +0.073] | 0.911 | ~0.915 | 17/10/37 | +0.016 | -0.016 |
| ltr24__logreg__small__pooled | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.684) | +0.013 [-0.057, +0.087] | 0.723 | ~0.723 | 19/10/35 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bar_val (n=64, ref 0.696 → 0.711) | +0.014 [-0.051, +0.069] | 0.638 | ~0.650 | 16/10/38 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bar_full (n=64, ref 0.703 → 0.711) | +0.008 [-0.054, +0.060] | 0.789 | ~0.800 | 14/10/40 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp14 (n=64, ref 0.723 → 0.711) | -0.012 [-0.059, +0.027] | 0.597 | ~0.613 | 12/10/42 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp14_cheap (n=64, ref 0.603 → 0.711) | **+0.107** [+0.053, +0.178] | 0.001 | ~0.000 | 24/6/34 | +0.141 | +0.109 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp17 (n=64, ref 0.719 → 0.711) | -0.008 [-0.084, +0.054] | 0.812 | ~0.818 | 16/10/38 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs lex13 (n=64, ref 0.683 → 0.711) | +0.028 [-0.025, +0.084] | 0.328 | ~0.334 | 17/8/39 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bm25_01 (n=64, ref 0.601 → 0.711) | **+0.110** [+0.047, +0.189] | 0.004 | ~0.003 | 26/6/32 | +0.125 | +0.047 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05 (n=64, ref 0.622 → 0.711) | **+0.089** [+0.029, +0.155] | 0.008 | ~0.007 | 22/7/35 | +0.125 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05+bge@20 (n=64, ref 0.695 → 0.711) | +0.016 [-0.049, +0.070] | 0.602 | ~0.606 | 16/10/38 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.711) | +0.031 [-0.034, +0.091] | 0.340 | ~0.339 | 19/7/38 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap (n=64, ref 0.671 → 0.711) | +0.040 [-0.014, +0.100] | 0.178 | ~0.180 | 18/8/38 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp24 mined-only (same features) (n=64, ref 0.659 → 0.711) | +0.052 [-0.006, +0.116] | 0.106 | ~0.104 | 20/8/36 | +0.062 | +0.062 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.684) | -0.012 [-0.075, +0.039] | 0.684 | ~0.691 | 13/15/36 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.684) | -0.018 [-0.081, +0.029] | 0.508 | ~0.518 | 11/15/38 | -0.016 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.684) | -0.038 [-0.101, +0.017] | 0.217 | ~0.221 | 9/15/40 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.684) | **+0.081** [+0.024, +0.151] | 0.015 | ~0.014 | 20/11/33 | +0.109 | +0.109 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.684) | -0.035 [-0.103, +0.018] | 0.255 | ~0.264 | 13/14/37 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.684) | +0.001 [-0.031, +0.033] | 0.939 | 0.938 | 11/6/47 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.684) | **+0.084** [+0.023, +0.160] | 0.020 | ~0.020 | 25/7/32 | +0.094 | +0.047 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.684) | **+0.063** [+0.015, +0.126] | 0.025 | ~0.022 | 19/8/37 | +0.094 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.684) | -0.010 [-0.074, +0.041] | 0.724 | ~0.731 | 14/14/36 | +0.000 | +0.031 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.684) | +0.004 [-0.044, +0.046] | 0.846 | ~0.852 | 14/8/42 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.684) | +0.014 [-0.027, +0.047] | 0.472 | ~0.484 | 18/4/42 | +0.000 | +0.031 |
| ltr24__logreg__notype__pooled-scored | vs bar_val (n=64, ref 0.696 → 0.691) | -0.006 [-0.064, +0.044] | 0.836 | ~0.838 | 13/14/37 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled-scored | vs bar_full (n=64, ref 0.703 → 0.691) | -0.012 [-0.068, +0.034] | 0.640 | ~0.645 | 11/14/39 | -0.016 | -0.016 |
| ltr24__logreg__notype__pooled-scored | vs exp14 (n=64, ref 0.723 → 0.691) | -0.032 [-0.094, +0.037] | 0.351 | ~0.355 | 9/17/38 | -0.062 | -0.016 |
| ltr24__logreg__notype__pooled-scored | vs exp14_cheap (n=64, ref 0.603 → 0.691) | **+0.087** [+0.026, +0.168] | 0.019 | ~0.017 | 20/10/34 | +0.109 | +0.094 |
| ltr24__logreg__notype__pooled-scored | vs exp17 (n=64, ref 0.719 → 0.691) | -0.028 [-0.097, +0.022] | 0.336 | ~0.343 | 13/13/38 | -0.031 | -0.016 |
| ltr24__logreg__notype__pooled-scored | vs lex13 (n=64, ref 0.683 → 0.691) | +0.007 [-0.034, +0.061] | 0.760 | ~0.767 | 13/10/41 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled-scored | vs bm25_01 (n=64, ref 0.601 → 0.691) | **+0.090** [+0.018, +0.177] | 0.029 | ~0.027 | 24/8/32 | +0.094 | +0.031 |
| ltr24__logreg__notype__pooled-scored | vs convex05 (n=64, ref 0.622 → 0.691) | **+0.069** [+0.009, +0.143] | 0.045 | ~0.046 | 20/11/33 | +0.094 | +0.000 |
| ltr24__logreg__notype__pooled-scored | vs convex05+bge@20 (n=64, ref 0.695 → 0.691) | -0.004 [-0.059, +0.046] | 0.877 | ~0.880 | 13/14/37 | +0.000 | +0.016 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.691) | +0.011 [-0.046, +0.065] | 0.714 | ~0.726 | 16/8/40 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap (n=64, ref 0.671 → 0.691) | +0.020 [-0.030, +0.079] | 0.484 | ~0.502 | 16/11/37 | +0.000 | +0.016 |
| ltr24__logreg__notype__pooled-scored | vs exp24 mined-only (same features) (n=64, ref 0.620 → 0.691) | **+0.071** [+0.012, +0.144] | 0.037 | ~0.037 | 20/8/36 | +0.078 | +0.016 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.689) | -0.007 [-0.065, +0.045] | 0.793 | ~0.792 | 13/14/37 | +0.000 | -0.016 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.689) | -0.014 [-0.068, +0.037] | 0.600 | ~0.605 | 11/15/38 | -0.016 | -0.031 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.689) | -0.034 [-0.098, +0.026] | 0.300 | ~0.302 | 9/17/38 | -0.062 | -0.031 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.689) | **+0.086** [+0.022, +0.160] | 0.019 | ~0.018 | 22/12/30 | +0.109 | +0.078 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.689) | -0.030 [-0.095, +0.021] | 0.309 | ~0.316 | 14/12/38 | -0.031 | -0.031 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.689) | +0.006 [-0.032, +0.043] | 0.766 | ~0.778 | 14/8/42 | +0.000 | -0.016 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.689) | **+0.088** [+0.022, +0.167] | 0.023 | ~0.022 | 21/11/32 | +0.094 | +0.016 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.689) | **+0.068** [+0.012, +0.133] | 0.032 | ~0.031 | 16/12/36 | +0.094 | -0.016 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.689) | -0.006 [-0.061, +0.047] | 0.831 | ~0.835 | 11/16/37 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.689) | +0.009 [-0.038, +0.050] | 0.700 | ~0.705 | 14/9/41 | +0.000 | -0.016 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.689) | +0.018 [-0.030, +0.061] | 0.445 | ~0.454 | 17/8/39 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bar_val (n=64, ref 0.696 → 0.693) | -0.003 [-0.063, +0.047] | 0.913 | ~0.916 | 14/12/38 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bar_full (n=64, ref 0.703 → 0.693) | -0.010 [-0.068, +0.036] | 0.717 | ~0.722 | 12/13/39 | -0.016 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp14 (n=64, ref 0.723 → 0.693) | -0.029 [-0.084, +0.009] | 0.221 | ~0.233 | 11/12/41 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp14_cheap (n=64, ref 0.603 → 0.693) | **+0.090** [+0.043, +0.150] | 0.001 | ~0.001 | 23/6/35 | +0.109 | +0.109 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp17 (n=64, ref 0.719 → 0.693) | -0.026 [-0.097, +0.031] | 0.427 | ~0.426 | 14/12/38 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs lex13 (n=64, ref 0.683 → 0.693) | +0.010 [-0.036, +0.055] | 0.665 | ~0.670 | 15/9/40 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bm25_01 (n=64, ref 0.601 → 0.693) | **+0.093** [+0.035, +0.165] | 0.007 | ~0.005 | 25/6/33 | +0.094 | +0.047 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05 (n=64, ref 0.622 → 0.693) | **+0.072** [+0.018, +0.134] | 0.018 | ~0.017 | 21/7/36 | +0.094 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05+bge@20 (n=64, ref 0.695 → 0.693) | -0.002 [-0.061, +0.048] | 0.956 | ~0.957 | 14/12/38 | +0.000 | +0.031 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.693) | +0.013 [-0.045, +0.060] | 0.619 | ~0.632 | 18/7/39 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap (n=64, ref 0.671 → 0.693) | +0.022 [-0.024, +0.065] | 0.336 | ~0.344 | 18/8/38 | +0.000 | +0.031 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp24 mined-only (same features) (n=64, ref 0.638 → 0.693) | +0.055 [-0.001, +0.110] | 0.059 | ~0.060 | 22/8/34 | +0.062 | +0.062 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.684) | -0.012 [-0.077, +0.040] | 0.689 | ~0.696 | 14/13/37 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.684) | -0.018 [-0.082, +0.029] | 0.515 | ~0.528 | 12/14/38 | -0.016 | -0.016 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.684) | -0.038 [-0.103, +0.018] | 0.229 | ~0.230 | 10/15/39 | -0.062 | -0.016 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.684) | **+0.081** [+0.026, +0.152] | 0.015 | ~0.013 | 21/10/33 | +0.109 | +0.094 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.684) | -0.035 [-0.100, +0.016] | 0.240 | ~0.249 | 13/13/38 | -0.031 | -0.016 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.684) | +0.001 [-0.032, +0.034] | 0.941 | ~0.943 | 13/8/43 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.684) | **+0.084** [+0.024, +0.160] | 0.019 | ~0.020 | 20/10/34 | +0.094 | +0.031 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.684) | **+0.063** [+0.017, +0.126] | 0.024 | ~0.020 | 15/9/40 | +0.094 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.684) | -0.010 [-0.077, +0.043] | 0.732 | ~0.736 | 13/14/37 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.684) | +0.004 [-0.041, +0.046] | 0.843 | ~0.844 | 14/10/40 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.684) | +0.014 [-0.020, +0.049] | 0.448 | 0.458 | 15/4/45 | +0.000 | +0.016 |
| ltr24__logreg__withtype__pooled-scored | vs bar_val (n=64, ref 0.696 → 0.663) | -0.034 [-0.092, +0.022] | 0.260 | ~0.262 | 11/16/37 | -0.031 | -0.016 |
| ltr24__logreg__withtype__pooled-scored | vs bar_full (n=64, ref 0.703 → 0.663) | -0.040 [-0.097, +0.011] | 0.162 | ~0.169 | 10/17/37 | -0.047 | -0.031 |
| ltr24__logreg__withtype__pooled-scored | vs exp14 (n=64, ref 0.723 → 0.663) | -0.060 [-0.131, +0.017] | 0.129 | ~0.131 | 9/20/35 | -0.094 | -0.031 |
| ltr24__logreg__withtype__pooled-scored | vs exp14_cheap (n=64, ref 0.603 → 0.663) | +0.060 [-0.010, +0.141] | 0.131 | ~0.133 | 19/14/31 | +0.078 | +0.078 |
| ltr24__logreg__withtype__pooled-scored | vs exp17 (n=64, ref 0.719 → 0.663) | -0.056 [-0.126, -0.002] | 0.076 | ~0.073 | 11/15/38 | -0.062 | -0.031 |
| ltr24__logreg__withtype__pooled-scored | vs lex13 (n=64, ref 0.683 → 0.663) | -0.020 [-0.077, +0.035] | 0.484 | ~0.484 | 12/11/41 | -0.031 | -0.016 |
| ltr24__logreg__withtype__pooled-scored | vs bm25_01 (n=64, ref 0.601 → 0.663) | +0.062 [-0.020, +0.152] | 0.164 | ~0.163 | 23/13/28 | +0.062 | +0.016 |
| ltr24__logreg__withtype__pooled-scored | vs convex05 (n=64, ref 0.622 → 0.663) | +0.041 [-0.032, +0.122] | 0.298 | ~0.296 | 20/16/28 | +0.062 | -0.016 |
| ltr24__logreg__withtype__pooled-scored | vs convex05+bge@20 (n=64, ref 0.695 → 0.663) | -0.032 [-0.090, +0.021] | 0.275 | ~0.281 | 11/16/37 | -0.031 | +0.000 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.663) | -0.017 [-0.078, +0.039] | 0.570 | ~0.582 | 15/11/38 | -0.031 | -0.016 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap (n=64, ref 0.671 → 0.663) | -0.008 [-0.073, +0.057] | 0.812 | ~0.822 | 17/11/36 | -0.031 | +0.000 |
| ltr24__logreg__withtype__pooled-scored | vs exp24 mined-only (same features) (n=64, ref 0.502 → 0.663) | **+0.161** [+0.100, +0.238] | 0.000 | ~0.000 | 25/6/33 | +0.203 | +0.078 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.605) | **-0.091** [-0.170, -0.027] | 0.016 | ~0.015 | 10/20/34 | -0.109 | -0.047 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.605) | **-0.098** [-0.176, -0.031] | 0.011 | ~0.010 | 11/21/32 | -0.125 | -0.062 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.605) | **-0.117** [-0.203, -0.031] | 0.011 | ~0.011 | 8/23/33 | -0.172 | -0.062 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.605) | +0.002 [-0.073, +0.082] | 0.962 | ~0.960 | 16/19/29 | +0.000 | +0.047 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.605) | **-0.114** [-0.199, -0.046] | 0.005 | ~0.004 | 10/22/32 | -0.141 | -0.062 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.605) | **-0.078** [-0.147, -0.019] | 0.022 | ~0.022 | 10/19/35 | -0.109 | -0.047 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.605) | +0.004 [-0.079, +0.093] | 0.920 | ~0.921 | 17/17/30 | -0.016 | -0.016 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.605) | -0.016 [-0.094, +0.064] | 0.695 | ~0.701 | 16/19/29 | -0.016 | -0.047 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.605) | **-0.090** [-0.170, -0.021] | 0.022 | ~0.021 | 12/21/31 | -0.109 | -0.031 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.605) | **-0.075** [-0.144, -0.024] | 0.017 | ~0.015 | 10/17/37 | -0.109 | -0.047 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.605) | -0.066 [-0.135, -0.007] | 0.052 | ~0.054 | 14/13/37 | -0.109 | -0.031 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bar_val (n=64, ref 0.696 → 0.710) | +0.013 [-0.051, +0.063] | 0.646 | ~0.649 | 15/10/39 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bar_full (n=64, ref 0.703 → 0.710) | +0.007 [-0.055, +0.054] | 0.808 | ~0.810 | 13/11/40 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp14 (n=64, ref 0.723 → 0.710) | -0.013 [-0.065, +0.020] | 0.539 | 0.561 | 11/9/44 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp14_cheap (n=64, ref 0.603 → 0.710) | **+0.106** [+0.053, +0.175] | 0.001 | ~0.001 | 24/7/33 | +0.141 | +0.109 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp17 (n=64, ref 0.719 → 0.710) | -0.010 [-0.084, +0.048] | 0.774 | ~0.774 | 15/10/39 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs lex13 (n=64, ref 0.683 → 0.710) | +0.026 [-0.017, +0.076] | 0.276 | ~0.278 | 16/8/40 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bm25_01 (n=64, ref 0.601 → 0.710) | **+0.109** [+0.051, +0.183] | 0.002 | ~0.001 | 25/5/34 | +0.125 | +0.047 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05 (n=64, ref 0.622 → 0.710) | **+0.088** [+0.036, +0.149] | 0.003 | ~0.002 | 21/6/37 | +0.125 | +0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05+bge@20 (n=64, ref 0.695 → 0.710) | +0.015 [-0.049, +0.065] | 0.609 | ~0.614 | 15/10/39 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.710) | +0.029 [-0.028, +0.083] | 0.304 | ~0.316 | 20/6/38 | +0.031 | +0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=64, ref 0.671 → 0.710) | +0.039 [-0.006, +0.089] | 0.121 | ~0.123 | 19/7/38 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=64, ref 0.671 → 0.710) | +0.038 [-0.007, +0.086] | 0.115 | ~0.116 | 19/6/39 | +0.047 | +0.047 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.698) | +0.001 [-0.066, +0.059] | 0.969 | ~0.969 | 14/13/37 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.698) | -0.005 [-0.070, +0.050] | 0.860 | ~0.862 | 12/14/38 | +0.000 | -0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.698) | -0.025 [-0.087, +0.028] | 0.400 | ~0.407 | 10/15/39 | -0.047 | -0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.698) | **+0.094** [+0.042, +0.165] | 0.004 | ~0.002 | 20/9/35 | +0.125 | +0.094 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.698) | -0.021 [-0.089, +0.036] | 0.492 | ~0.497 | 12/13/39 | -0.016 | -0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.698) | +0.014 [-0.013, +0.046] | 0.341 | 0.352 | 12/5/47 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.698) | **+0.097** [+0.041, +0.172] | 0.005 | ~0.004 | 24/6/34 | +0.109 | +0.031 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.698) | **+0.076** [+0.030, +0.141] | 0.008 | ~0.006 | 20/7/37 | +0.109 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.698) | +0.003 [-0.065, +0.061] | 0.932 | ~0.930 | 14/13/37 | +0.016 | +0.016 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.698) | +0.018 [-0.024, +0.057] | 0.404 | ~0.413 | 15/8/41 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.698) | +0.027 [-0.002, +0.060] | 0.103 | 0.105 | 17/3/44 | +0.016 | +0.016 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bar_val (n=64, ref 0.696 → 0.699) | +0.002 [-0.050, +0.054] | 0.929 | ~0.933 | 13/14/37 | +0.016 | -0.016 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bar_full (n=64, ref 0.703 → 0.699) | -0.004 [-0.053, +0.044] | 0.868 | ~0.872 | 11/15/38 | +0.000 | -0.031 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp14 (n=64, ref 0.723 → 0.699) | -0.024 [-0.089, +0.045] | 0.494 | ~0.493 | 9/17/38 | -0.047 | -0.031 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp14_cheap (n=64, ref 0.603 → 0.699) | **+0.095** [+0.031, +0.177] | 0.013 | ~0.013 | 20/12/32 | +0.125 | +0.078 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp17 (n=64, ref 0.719 → 0.699) | -0.020 [-0.083, +0.028] | 0.467 | ~0.477 | 14/12/38 | -0.016 | -0.031 |
| ltr24__logreg__notype-nogate__pooled-scored | vs lex13 (n=64, ref 0.683 → 0.699) | +0.015 [-0.030, +0.076] | 0.570 | ~0.581 | 12/10/42 | +0.016 | -0.016 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bm25_01 (n=64, ref 0.601 → 0.699) | **+0.098** [+0.028, +0.183] | 0.018 | ~0.015 | 22/9/33 | +0.109 | +0.016 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05 (n=64, ref 0.622 → 0.699) | **+0.077** [+0.018, +0.152] | 0.026 | ~0.025 | 17/9/38 | +0.109 | -0.016 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05+bge@20 (n=64, ref 0.695 → 0.699) | +0.004 [-0.046, +0.055] | 0.882 | ~0.884 | 13/14/37 | +0.016 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.699) | +0.019 [-0.034, +0.076] | 0.516 | ~0.528 | 13/9/42 | +0.016 | -0.016 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=64, ref 0.671 → 0.699) | +0.028 [-0.021, +0.092] | 0.337 | ~0.343 | 13/10/41 | +0.016 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=64, ref 0.662 → 0.699) | +0.037 [+0.000, +0.098] | 0.133 | ~0.137 | 12/9/43 | +0.047 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.681) | -0.015 [-0.078, +0.039] | 0.613 | ~0.620 | 13/15/36 | +0.000 | -0.031 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.681) | -0.022 [-0.080, +0.031] | 0.444 | ~0.449 | 11/16/37 | -0.016 | -0.047 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.681) | -0.041 [-0.108, +0.019] | 0.213 | ~0.216 | 8/18/38 | -0.062 | -0.047 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.681) | **+0.078** [+0.015, +0.152] | 0.033 | ~0.031 | 20/12/32 | +0.109 | +0.062 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.681) | -0.038 [-0.105, +0.015] | 0.221 | ~0.230 | 14/13/37 | -0.031 | -0.047 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.681) | -0.002 [-0.039, +0.035] | 0.916 | ~0.921 | 12/9/43 | +0.000 | -0.031 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.681) | **+0.081** [+0.013, +0.159] | 0.037 | ~0.035 | 22/11/31 | +0.094 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.681) | +0.060 [+0.004, +0.125] | 0.058 | ~0.059 | 15/13/36 | +0.094 | -0.031 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.681) | -0.014 [-0.075, +0.041] | 0.644 | ~0.651 | 12/15/37 | +0.000 | -0.016 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.681) | +0.001 [-0.046, +0.043] | 0.960 | ~0.963 | 13/10/41 | +0.000 | -0.031 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.681) | +0.010 [-0.037, +0.052] | 0.655 | ~0.664 | 17/8/39 | +0.000 | -0.016 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bar_val (n=64, ref 0.696 → 0.676) | -0.020 [-0.088, +0.038] | 0.525 | ~0.531 | 14/13/37 | -0.016 | +0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bar_full (n=64, ref 0.703 → 0.676) | -0.027 [-0.096, +0.032] | 0.411 | ~0.419 | 13/15/36 | -0.031 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp14 (n=64, ref 0.723 → 0.676) | -0.046 [-0.115, +0.010] | 0.152 | ~0.154 | 11/15/38 | -0.078 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp14_cheap (n=64, ref 0.603 → 0.676) | **+0.073** [+0.025, +0.138] | 0.015 | ~0.014 | 21/7/36 | +0.094 | +0.141 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp17 (n=64, ref 0.719 → 0.676) | -0.043 [-0.116, +0.020] | 0.213 | ~0.211 | 14/15/35 | -0.047 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs lex13 (n=64, ref 0.683 → 0.676) | -0.007 [-0.045, +0.027] | 0.700 | ~0.713 | 12/9/43 | -0.016 | +0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bm25_01 (n=64, ref 0.601 → 0.676) | **+0.075** [+0.022, +0.145] | 0.020 | ~0.018 | 23/5/36 | +0.078 | +0.078 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05 (n=64, ref 0.622 → 0.676) | **+0.055** [+0.010, +0.111] | 0.035 | ~0.033 | 18/6/40 | +0.078 | +0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05+bge@20 (n=64, ref 0.695 → 0.676) | -0.019 [-0.090, +0.044] | 0.582 | ~0.580 | 15/15/34 | -0.016 | +0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.676) | -0.004 [-0.053, +0.034] | 0.859 | ~0.866 | 16/6/42 | -0.016 | +0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=64, ref 0.671 → 0.676) | +0.005 [-0.034, +0.035] | 0.764 | ~0.779 | 16/6/42 | -0.016 | +0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=64, ref 0.655 → 0.676) | +0.021 [-0.013, +0.060] | 0.251 | ~0.261 | 16/6/42 | +0.031 | +0.094 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.659) | -0.037 [-0.110, +0.021] | 0.262 | ~0.260 | 14/15/35 | -0.031 | -0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.659) | -0.044 [-0.115, +0.011] | 0.172 | ~0.174 | 12/15/37 | -0.047 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.659) | -0.063 [-0.132, -0.005] | 0.059 | ~0.057 | 9/17/38 | -0.094 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.659) | +0.056 [-0.003, +0.128] | 0.102 | ~0.100 | 19/13/32 | +0.078 | +0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.659) | -0.060 [-0.138, -0.001] | 0.087 | ~0.086 | 10/15/39 | -0.062 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.659) | -0.024 [-0.067, +0.015] | 0.249 | ~0.256 | 9/13/42 | -0.031 | -0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.659) | +0.059 [-0.003, +0.132] | 0.099 | ~0.099 | 18/14/32 | +0.062 | -0.016 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.659) | +0.038 [-0.011, +0.095] | 0.165 | ~0.170 | 15/13/36 | +0.062 | -0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.659) | -0.036 [-0.108, +0.022] | 0.278 | ~0.280 | 12/17/35 | -0.031 | -0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.659) | -0.021 [-0.073, +0.014] | 0.337 | ~0.352 | 9/13/42 | -0.031 | -0.047 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.659) | -0.012 [-0.054, +0.021] | 0.542 | ~0.558 | 12/9/43 | -0.031 | -0.031 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bar_val (n=64, ref 0.696 → 0.671) | -0.026 [-0.094, +0.040] | 0.449 | ~0.456 | 12/16/36 | -0.031 | +0.016 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bar_full (n=64, ref 0.703 → 0.671) | -0.032 [-0.102, +0.033] | 0.351 | ~0.353 | 11/18/35 | -0.047 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp14 (n=64, ref 0.723 → 0.671) | -0.052 [-0.122, +0.009] | 0.128 | ~0.129 | 9/18/37 | -0.094 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp14_cheap (n=64, ref 0.603 → 0.671) | **+0.067** [+0.009, +0.135] | 0.044 | ~0.043 | 20/12/32 | +0.078 | +0.109 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp17 (n=64, ref 0.719 → 0.671) | -0.048 [-0.122, +0.019] | 0.176 | ~0.178 | 14/16/34 | -0.062 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | vs lex13 (n=64, ref 0.683 → 0.671) | -0.013 [-0.055, +0.028] | 0.560 | ~0.569 | 11/11/42 | -0.031 | +0.016 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bm25_01 (n=64, ref 0.601 → 0.671) | +0.070 [+0.006, +0.147] | 0.060 | ~0.060 | 21/10/33 | +0.062 | +0.047 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05 (n=64, ref 0.622 → 0.671) | +0.049 [-0.008, +0.116] | 0.120 | ~0.120 | 18/11/35 | +0.062 | +0.016 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05+bge@20 (n=64, ref 0.695 → 0.671) | -0.024 [-0.097, +0.043] | 0.498 | ~0.502 | 14/17/33 | -0.031 | +0.031 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.671) | -0.009 [-0.066, +0.033] | 0.713 | ~0.724 | 14/8/42 | -0.031 | +0.016 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=64, ref 0.671 → 0.671) | -0.000 [-0.049, +0.041] | 0.996 | ~0.996 | 16/8/40 | -0.031 | +0.031 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=64, ref 0.532 → 0.671) | **+0.139** [+0.070, +0.226] | 0.001 | ~0.001 | 27/8/29 | +0.156 | +0.094 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.659) | -0.037 [-0.111, +0.025] | 0.281 | ~0.284 | 13/17/34 | -0.031 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.659) | -0.044 [-0.115, +0.015] | 0.186 | ~0.188 | 11/18/35 | -0.047 | -0.016 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.659) | -0.063 [-0.133, -0.000] | 0.069 | ~0.070 | 8/20/36 | -0.094 | -0.016 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.659) | +0.056 [-0.009, +0.132] | 0.129 | ~0.130 | 19/13/32 | +0.078 | +0.094 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.659) | -0.060 [-0.136, +0.001] | 0.086 | ~0.087 | 14/15/35 | -0.062 | -0.016 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.659) | -0.024 [-0.070, +0.018] | 0.291 | ~0.299 | 11/12/41 | -0.031 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.659) | +0.058 [-0.011, +0.140] | 0.139 | ~0.147 | 19/15/30 | +0.062 | +0.031 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.659) | +0.038 [-0.021, +0.104] | 0.245 | ~0.247 | 15/14/35 | +0.062 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.659) | -0.036 [-0.108, +0.026] | 0.297 | ~0.298 | 12/17/35 | -0.031 | +0.016 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.659) | -0.021 [-0.079, +0.023] | 0.421 | ~0.427 | 11/10/43 | -0.031 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.659) | -0.012 [-0.064, +0.030] | 0.625 | ~0.630 | 14/9/41 | -0.031 | +0.016 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bar_val (n=64, ref 0.696 → 0.691) | -0.005 [-0.060, +0.039] | 0.844 | ~0.847 | 11/10/43 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bar_full (n=64, ref 0.703 → 0.691) | -0.011 [-0.066, +0.029] | 0.627 | 0.639 | 9/10/45 | -0.016 | +0.000 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp14 (n=64, ref 0.723 → 0.691) | -0.031 [-0.089, +0.012] | 0.234 | ~0.244 | 10/13/41 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp14_cheap (n=64, ref 0.603 → 0.691) | **+0.088** [+0.038, +0.151] | 0.003 | ~0.002 | 22/8/34 | +0.109 | +0.109 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp17 (n=64, ref 0.719 → 0.691) | -0.028 [-0.096, +0.022] | 0.357 | ~0.363 | 11/11/42 | -0.031 | +0.000 |
| ltr24__lgbm-tiny__small__pooled-scored | vs lex13 (n=64, ref 0.683 → 0.691) | +0.008 [-0.034, +0.055] | 0.722 | ~0.727 | 12/10/42 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bm25_01 (n=64, ref 0.601 → 0.691) | **+0.091** [+0.038, +0.161] | 0.006 | ~0.004 | 23/6/35 | +0.094 | +0.047 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05 (n=64, ref 0.622 → 0.691) | **+0.070** [+0.026, +0.127] | 0.009 | ~0.008 | 17/10/37 | +0.094 | +0.016 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05+bge@20 (n=64, ref 0.695 → 0.691) | -0.004 [-0.060, +0.040] | 0.890 | ~0.892 | 11/11/42 | +0.000 | +0.031 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.691) | +0.011 [-0.044, +0.058] | 0.663 | ~0.667 | 14/13/37 | +0.000 | +0.016 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap (n=64, ref 0.671 → 0.691) | +0.021 [-0.022, +0.065] | 0.368 | ~0.372 | 15/10/39 | +0.000 | +0.031 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp24 mined-only (same features) (n=64, ref 0.635 → 0.691) | **+0.056** [+0.005, +0.113] | 0.049 | ~0.046 | 18/8/38 | +0.062 | +0.031 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.696) | -0.000 [-0.063, +0.048] | 0.999 | ~1.000 | 12/9/43 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.696) | -0.007 [-0.069, +0.038] | 0.806 | 0.812 | 10/9/45 | +0.000 | -0.016 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.696) | -0.026 [-0.082, +0.026] | 0.354 | ~0.359 | 11/13/40 | -0.047 | -0.016 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.696) | **+0.093** [+0.040, +0.160] | 0.004 | ~0.003 | 23/8/33 | +0.125 | +0.094 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.696) | -0.023 [-0.092, +0.027] | 0.450 | 0.460 | 10/10/44 | -0.016 | -0.016 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.696) | +0.013 [-0.023, +0.057] | 0.516 | 0.526 | 11/8/45 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.696) | **+0.096** [+0.041, +0.168] | 0.005 | ~0.003 | 24/7/33 | +0.109 | +0.031 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.696) | **+0.075** [+0.037, +0.131] | 0.002 | ~0.001 | 21/5/38 | +0.109 | +0.000 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.696) | +0.002 [-0.061, +0.050] | 0.958 | ~0.956 | 14/9/41 | +0.016 | +0.016 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.696) | +0.016 [-0.030, +0.060] | 0.493 | ~0.499 | 14/11/39 | +0.016 | +0.000 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.696) | +0.025 [-0.011, +0.064] | 0.198 | ~0.207 | 16/6/42 | +0.016 | +0.016 |
| ltr24__logreg__small__pooled-scored | vs bar_val (n=64, ref 0.696 → 0.683) | -0.013 [-0.077, +0.051] | 0.692 | ~0.696 | 13/13/38 | -0.016 | +0.016 |
| ltr24__logreg__small__pooled-scored | vs bar_full (n=64, ref 0.703 → 0.683) | -0.019 [-0.082, +0.040] | 0.535 | ~0.540 | 11/14/39 | -0.031 | +0.000 |
| ltr24__logreg__small__pooled-scored | vs exp14 (n=64, ref 0.723 → 0.683) | -0.039 [-0.109, +0.033] | 0.293 | ~0.297 | 12/17/35 | -0.078 | +0.000 |
| ltr24__logreg__small__pooled-scored | vs exp14_cheap (n=64, ref 0.603 → 0.683) | **+0.080** [+0.014, +0.163] | 0.039 | ~0.039 | 24/9/31 | +0.094 | +0.109 |
| ltr24__logreg__small__pooled-scored | vs exp17 (n=64, ref 0.719 → 0.683) | -0.036 [-0.108, +0.029] | 0.305 | ~0.303 | 13/13/38 | -0.047 | +0.000 |
| ltr24__logreg__small__pooled-scored | vs lex13 (n=64, ref 0.683 → 0.683) | +0.000 [-0.051, +0.059] | 0.995 | ~0.996 | 15/13/36 | -0.016 | +0.016 |
| ltr24__logreg__small__pooled-scored | vs bm25_01 (n=64, ref 0.601 → 0.683) | +0.083 [+0.007, +0.171] | 0.052 | ~0.053 | 25/9/30 | +0.078 | +0.047 |
| ltr24__logreg__small__pooled-scored | vs convex05 (n=64, ref 0.622 → 0.683) | +0.062 [-0.003, +0.137] | 0.082 | ~0.080 | 20/9/35 | +0.078 | +0.016 |
| ltr24__logreg__small__pooled-scored | vs convex05+bge@20 (n=64, ref 0.695 → 0.683) | -0.011 [-0.075, +0.052] | 0.724 | ~0.732 | 13/13/38 | -0.016 | +0.031 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.683) | +0.003 [-0.060, +0.070] | 0.920 | ~0.925 | 17/11/36 | -0.016 | +0.016 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap (n=64, ref 0.671 → 0.683) | +0.013 [-0.044, +0.078] | 0.688 | ~0.694 | 17/11/36 | -0.016 | +0.031 |
| ltr24__logreg__small__pooled-scored | vs exp24 mined-only (same features) (n=64, ref 0.566 → 0.683) | **+0.118** [+0.052, +0.195] | 0.002 | ~0.001 | 28/6/30 | +0.125 | +0.109 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs bar_val (n=64, ref 0.696 → 0.674) | -0.022 [-0.087, +0.041] | 0.503 | ~0.507 | 11/14/39 | +0.000 | -0.031 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs bar_full (n=64, ref 0.703 → 0.674) | -0.029 [-0.091, +0.030] | 0.363 | ~0.361 | 10/14/40 | -0.016 | -0.047 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs exp14 (n=64, ref 0.723 → 0.674) | -0.048 [-0.129, +0.039] | 0.269 | ~0.272 | 11/18/35 | -0.062 | -0.047 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs exp14_cheap (n=64, ref 0.603 → 0.674) | +0.071 [-0.013, +0.163] | 0.123 | ~0.123 | 22/13/29 | +0.109 | +0.062 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs exp17 (n=64, ref 0.719 → 0.674) | -0.045 [-0.117, +0.019] | 0.203 | ~0.206 | 10/14/40 | -0.031 | -0.047 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs lex13 (n=64, ref 0.683 → 0.674) | -0.009 [-0.075, +0.058] | 0.790 | ~0.794 | 13/12/39 | +0.000 | -0.031 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs bm25_01 (n=64, ref 0.601 → 0.674) | +0.073 [-0.015, +0.170] | 0.132 | ~0.130 | 23/14/27 | +0.094 | +0.000 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs convex05 (n=64, ref 0.622 → 0.674) | +0.053 [-0.025, +0.137] | 0.208 | ~0.208 | 19/15/30 | +0.094 | -0.031 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=64, ref 0.695 → 0.674) | -0.021 [-0.084, +0.042] | 0.526 | ~0.534 | 10/16/38 | +0.000 | -0.016 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=64, ref 0.680 → 0.674) | -0.006 [-0.079, +0.065] | 0.873 | ~0.875 | 15/13/36 | +0.000 | -0.031 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=64, ref 0.671 → 0.674) | +0.003 [-0.070, +0.079] | 0.933 | ~0.935 | 17/10/37 | +0.000 | -0.016 |

**Mined val split – paired tests (Δ = exp-24 fit A − reference)**

| run | reference  Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 | Δ H@10 |
|---|---|:--|--:|--:|:--|--:|--:|
| ltr24__lgbm-tiny__notype__mined | vs convex05 (n=345, ref 0.703 → 0.759) | **+0.055** [+0.036, +0.078] | 0.000 | ~0.000 | 44/9/292 | +0.070 | +0.029 |
| ltr24__lgbm-tiny__notype__mined | vs exp13_lex (n=345, ref 0.708 → 0.759) | **+0.050** [+0.034, +0.073] | 0.000 | ~0.000 | 38/7/300 | +0.064 | +0.035 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.736) | **+0.029** [+0.010, +0.064] | 0.025 | 0.018 | 8/3/83 | +0.043 | -0.011 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap (n=345, ref 0.743 → 0.759) | +0.016 [-0.001, +0.035] | 0.077 | ~0.077 | 20/15/310 | +0.038 | -0.017 |
| ltr24__lgbm-tiny__notype__mined | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.736) | **+0.196** [+0.139, +0.268] | 0.000 | ~0.000 | 32/2/60 | +0.245 | +0.106 |
| ltr24__logreg__notype__mined | vs convex05 (n=345, ref 0.703 → 0.744) | **+0.040** [+0.018, +0.063] | 0.001 | ~0.000 | 45/14/286 | +0.055 | +0.015 |
| ltr24__logreg__notype__mined | vs exp13_lex (n=345, ref 0.708 → 0.744) | **+0.035** [+0.016, +0.058] | 0.001 | ~0.001 | 37/15/293 | +0.049 | +0.020 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.731) | +0.023 [-0.005, +0.058] | 0.155 | 0.156 | 8/8/78 | +0.053 | -0.043 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap (n=345, ref 0.743 → 0.744) | +0.001 [-0.020, +0.022] | 0.920 | ~0.921 | 23/25/297 | +0.023 | -0.032 |
| ltr24__logreg__notype__mined | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.731) | **+0.191** [+0.126, +0.265] | 0.000 | ~0.000 | 31/4/59 | +0.255 | +0.074 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05 (n=345, ref 0.703 → 0.769) | **+0.066** [+0.045, +0.090] | 0.000 | ~0.000 | 47/5/293 | +0.078 | +0.043 |
| ltr24__lgbm-tiny__withtype__mined | vs exp13_lex (n=345, ref 0.708 → 0.769) | **+0.061** [+0.042, +0.086] | 0.000 | ~0.000 | 41/3/301 | +0.072 | +0.049 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.746) | **+0.039** [+0.016, +0.079] | 0.012 | 0.004 | 10/1/83 | +0.053 | +0.000 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap (n=345, ref 0.743 → 0.769) | **+0.027** [+0.012, +0.045] | 0.002 | ~0.001 | 21/6/318 | +0.046 | -0.003 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.746) | **+0.206** [+0.147, +0.279] | 0.000 | ~0.000 | 33/1/60 | +0.255 | +0.117 |
| ltr24__logreg__withtype__mined | vs convex05 (n=345, ref 0.703 → 0.759) | **+0.056** [+0.032, +0.081] | 0.000 | ~0.000 | 48/9/288 | +0.067 | +0.038 |
| ltr24__logreg__withtype__mined | vs exp13_lex (n=345, ref 0.708 → 0.759) | **+0.051** [+0.030, +0.075] | 0.000 | ~0.000 | 44/9/292 | +0.061 | +0.043 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.751) | **+0.043** [+0.011, +0.084] | 0.022 | 0.020 | 11/4/79 | +0.064 | -0.011 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap (n=345, ref 0.743 → 0.759) | +0.017 [-0.002, +0.036] | 0.075 | ~0.074 | 28/14/303 | +0.035 | -0.009 |
| ltr24__logreg__withtype__mined | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.751) | **+0.210** [+0.144, +0.287] | 0.000 | ~0.000 | 33/2/59 | +0.266 | +0.106 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05 (n=345, ref 0.703 → 0.730) | **+0.027** [+0.011, +0.046] | 0.002 | ~0.002 | 36/14/295 | +0.026 | +0.026 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp13_lex (n=345, ref 0.708 → 0.730) | **+0.022** [+0.008, +0.039] | 0.005 | ~0.004 | 32/14/299 | +0.020 | +0.032 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.704) | -0.004 [-0.022, +0.013] | 0.682 | 0.701 | 5/7/82 | +0.000 | -0.011 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap (n=345, ref 0.743 → 0.730) | **-0.012** [-0.026, -0.003] | 0.031 | ~0.028 | 5/18/322 | -0.006 | -0.020 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.704) | **+0.164** [+0.101, +0.236] | 0.000 | ~0.000 | 31/5/58 | +0.202 | +0.106 |
| ltr24__logreg__notype-nogate__mined | vs convex05 (n=345, ref 0.703 → 0.696) | -0.007 [-0.026, +0.009] | 0.433 | ~0.432 | 25/28/292 | -0.015 | +0.009 |
| ltr24__logreg__notype-nogate__mined | vs exp13_lex (n=345, ref 0.708 → 0.696) | -0.012 [-0.032, +0.006] | 0.218 | ~0.222 | 25/34/286 | -0.020 | +0.015 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.675) | **-0.033** [-0.067, -0.010] | 0.026 | 0.023 | 1/15/78 | -0.021 | -0.064 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap (n=345, ref 0.743 → 0.696) | **-0.046** [-0.067, -0.029] | 0.000 | ~0.000 | 5/45/295 | -0.046 | -0.038 |
| ltr24__logreg__notype-nogate__mined | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.675) | **+0.135** [+0.066, +0.209] | 0.001 | ~0.000 | 29/8/57 | +0.181 | +0.053 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05 (n=345, ref 0.703 → 0.760) | **+0.057** [+0.037, +0.080] | 0.000 | ~0.000 | 44/8/293 | +0.072 | +0.026 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp13_lex (n=345, ref 0.708 → 0.760) | **+0.052** [+0.035, +0.075] | 0.000 | ~0.000 | 39/7/299 | +0.067 | +0.032 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.742) | **+0.034** [+0.013, +0.069] | 0.014 | 0.009 | 9/3/82 | +0.053 | -0.011 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap (n=345, ref 0.743 → 0.760) | +0.018 [-0.000, +0.037] | 0.060 | ~0.058 | 21/14/310 | +0.041 | -0.020 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.742) | **+0.201** [+0.142, +0.274] | 0.000 | ~0.000 | 32/2/60 | +0.255 | +0.106 |
| ltr24__logreg__notype-nobge__mined | vs convex05 (n=345, ref 0.703 → 0.744) | **+0.041** [+0.018, +0.064] | 0.001 | ~0.000 | 45/14/286 | +0.055 | +0.012 |
| ltr24__logreg__notype-nobge__mined | vs exp13_lex (n=345, ref 0.708 → 0.744) | **+0.036** [+0.016, +0.058] | 0.001 | ~0.001 | 37/16/292 | +0.049 | +0.017 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.733) | +0.025 [-0.005, +0.060] | 0.131 | 0.135 | 9/7/78 | +0.053 | -0.032 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap (n=345, ref 0.743 → 0.744) | +0.002 [-0.019, +0.022] | 0.884 | ~0.887 | 23/25/297 | +0.023 | -0.035 |
| ltr24__logreg__notype-nobge__mined | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.733) | **+0.193** [+0.128, +0.266] | 0.000 | ~0.000 | 31/4/59 | +0.255 | +0.085 |
| ltr24__lgbm-tiny__small__mined | vs convex05 (n=345, ref 0.703 → 0.749) | **+0.045** [+0.024, +0.067] | 0.000 | ~0.000 | 41/12/292 | +0.058 | +0.023 |
| ltr24__lgbm-tiny__small__mined | vs exp13_lex (n=345, ref 0.708 → 0.749) | **+0.040** [+0.023, +0.061] | 0.000 | ~0.000 | 35/11/299 | +0.052 | +0.029 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.745) | **+0.037** [+0.016, +0.072] | 0.009 | 0.005 | 11/2/81 | +0.053 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap (n=345, ref 0.743 → 0.749) | +0.006 [-0.012, +0.025] | 0.510 | ~0.510 | 20/19/306 | +0.026 | -0.023 |
| ltr24__lgbm-tiny__small__mined | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.745) | **+0.205** [+0.145, +0.277] | 0.000 | ~0.000 | 32/1/61 | +0.255 | +0.117 |
| ltr24__logreg__small__mined | vs convex05 (n=345, ref 0.703 → 0.736) | **+0.033** [+0.009, +0.056] | 0.007 | ~0.006 | 41/17/287 | +0.052 | -0.009 |
| ltr24__logreg__small__mined | vs exp13_lex (n=345, ref 0.708 → 0.736) | **+0.028** [+0.007, +0.050] | 0.011 | ~0.010 | 37/16/292 | +0.046 | -0.003 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.727) | +0.020 [-0.010, +0.055] | 0.244 | 0.253 | 7/9/78 | +0.053 | -0.074 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap (n=345, ref 0.743 → 0.736) | -0.006 [-0.030, +0.016] | 0.581 | ~0.590 | 23/28/294 | +0.020 | -0.055 |
| ltr24__logreg__small__mined | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.727) | **+0.187** [+0.122, +0.261] | 0.000 | ~0.000 | 31/4/59 | +0.255 | +0.043 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05 (n=345, ref 0.703 → 0.749) | **+0.046** [+0.029, +0.066] | 0.000 | ~0.000 | 44/8/293 | +0.052 | +0.023 |
| ltr24__lgbm-tiny__notype__pooled | vs exp13_lex (n=345, ref 0.708 → 0.749) | **+0.041** [+0.026, +0.060] | 0.000 | ~0.000 | 39/4/302 | +0.046 | +0.029 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.724) | +0.016 [-0.006, +0.045] | 0.207 | 0.215 | 7/7/80 | +0.032 | -0.032 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap (n=345, ref 0.743 → 0.749) | +0.006 [-0.010, +0.024] | 0.442 | ~0.448 | 18/19/308 | +0.020 | -0.023 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.724) | **+0.183** [+0.124, +0.255] | 0.000 | ~0.000 | 32/3/59 | +0.234 | +0.085 |
| ltr24__lgbm-tiny__notype__pooled | vs exp24 mined-only (same features) (n=345, ref 0.759 → 0.749) | -0.010 [-0.022, +0.001] | 0.112 | ~0.110 | 6/21/318 | -0.017 | -0.006 |
| ltr24__logreg__notype__pooled | vs convex05 (n=345, ref 0.703 → 0.748) | **+0.045** [+0.025, +0.067] | 0.000 | ~0.000 | 43/12/290 | +0.067 | +0.012 |
| ltr24__logreg__notype__pooled | vs exp13_lex (n=345, ref 0.708 → 0.748) | **+0.040** [+0.024, +0.061] | 0.000 | ~0.000 | 39/11/295 | +0.061 | +0.017 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.735) | +0.028 [+0.004, +0.064] | 0.068 | 0.067 | 7/8/79 | +0.064 | -0.053 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap (n=345, ref 0.743 → 0.748) | +0.006 [-0.015, +0.026] | 0.563 | ~0.572 | 23/23/299 | +0.035 | -0.035 |
| ltr24__logreg__notype__pooled | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.735) | **+0.195** [+0.134, +0.270] | 0.000 | ~0.000 | 30/4/60 | +0.266 | +0.064 |
| ltr24__logreg__notype__pooled | vs exp24 mined-only (same features) (n=345, ref 0.744 → 0.748) | +0.005 [-0.005, +0.016] | 0.366 | ~0.378 | 15/15/315 | +0.012 | -0.003 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05 (n=345, ref 0.703 → 0.745) | **+0.042** [+0.024, +0.063] | 0.000 | ~0.000 | 46/8/291 | +0.046 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp13_lex (n=345, ref 0.708 → 0.745) | **+0.037** [+0.022, +0.056] | 0.000 | ~0.000 | 38/6/301 | +0.041 | +0.035 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.717) | +0.009 [-0.003, +0.034] | 0.300 | 0.342 | 5/7/82 | +0.021 | -0.021 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap (n=345, ref 0.743 → 0.745) | +0.003 [-0.011, +0.017] | 0.723 | ~0.725 | 15/20/310 | +0.015 | -0.017 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.717) | **+0.176** [+0.121, +0.246] | 0.000 | ~0.000 | 33/2/59 | +0.223 | +0.096 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp24 mined-only (same features) (n=345, ref 0.769 → 0.745) | **-0.024** [-0.041, -0.010] | 0.003 | ~0.001 | 3/29/313 | -0.032 | -0.015 |
| ltr24__logreg__withtype__pooled | vs convex05 (n=345, ref 0.703 → 0.759) | **+0.056** [+0.036, +0.079] | 0.000 | ~0.000 | 48/6/291 | +0.072 | +0.035 |
| ltr24__logreg__withtype__pooled | vs exp13_lex (n=345, ref 0.708 → 0.759) | **+0.051** [+0.033, +0.072] | 0.000 | ~0.000 | 43/7/295 | +0.067 | +0.041 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.743) | **+0.036** [+0.013, +0.071] | 0.017 | 0.013 | 10/5/79 | +0.064 | -0.021 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap (n=345, ref 0.743 → 0.759) | +0.017 [-0.003, +0.037] | 0.095 | ~0.099 | 26/20/299 | +0.041 | -0.012 |
| ltr24__logreg__withtype__pooled | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.743) | **+0.203** [+0.142, +0.277] | 0.000 | ~0.000 | 33/1/60 | +0.266 | +0.096 |
| ltr24__logreg__withtype__pooled | vs exp24 mined-only (same features) (n=345, ref 0.759 → 0.759) | -0.000 [-0.013, +0.012] | 0.966 | ~0.965 | 11/17/317 | +0.006 | -0.003 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05 (n=345, ref 0.703 → 0.729) | **+0.025** [+0.010, +0.044] | 0.003 | ~0.002 | 37/13/295 | +0.023 | +0.020 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp13_lex (n=345, ref 0.708 → 0.729) | **+0.021** [+0.007, +0.037] | 0.008 | ~0.007 | 32/12/301 | +0.017 | +0.026 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.694) | -0.013 [-0.033, -0.003] | 0.069 | 0.060 | 2/9/83 | -0.011 | -0.032 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap (n=345, ref 0.743 → 0.729) | **-0.014** [-0.027, -0.003] | 0.025 | ~0.022 | 8/24/313 | -0.009 | -0.026 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.694) | **+0.154** [+0.094, +0.225] | 0.000 | ~0.000 | 31/5/58 | +0.192 | +0.085 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp24 mined-only (same features) (n=345, ref 0.730 → 0.729) | -0.002 [-0.010, +0.010] | 0.738 | ~0.755 | 9/21/315 | -0.003 | -0.006 |
| ltr24__logreg__notype-nogate__pooled | vs convex05 (n=345, ref 0.703 → 0.702) | -0.001 [-0.018, +0.016] | 0.906 | ~0.906 | 32/24/289 | -0.012 | +0.012 |
| ltr24__logreg__notype-nogate__pooled | vs exp13_lex (n=345, ref 0.708 → 0.702) | -0.006 [-0.024, +0.011] | 0.492 | ~0.496 | 30/28/287 | -0.017 | +0.017 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.689) | **-0.019** [-0.040, -0.009] | 0.007 | 0.001 | 0/12/82 | -0.011 | -0.053 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap (n=345, ref 0.743 → 0.702) | **-0.040** [-0.061, -0.023] | 0.000 | ~0.000 | 10/38/297 | -0.043 | -0.035 |
| ltr24__logreg__notype-nogate__pooled | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.689) | **+0.148** [+0.087, +0.219] | 0.000 | ~0.000 | 29/7/58 | +0.192 | +0.064 |
| ltr24__logreg__notype-nogate__pooled | vs exp24 mined-only (same features) (n=345, ref 0.696 → 0.702) | +0.006 [-0.007, +0.020] | 0.379 | ~0.384 | 25/20/300 | +0.003 | +0.003 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05 (n=345, ref 0.703 → 0.741) | **+0.038** [+0.021, +0.057] | 0.000 | ~0.000 | 44/9/292 | +0.038 | +0.017 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp13_lex (n=345, ref 0.708 → 0.741) | **+0.033** [+0.018, +0.051] | 0.000 | ~0.000 | 35/8/302 | +0.032 | +0.023 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.719) | +0.011 [-0.009, +0.038] | 0.340 | 0.356 | 6/7/81 | +0.021 | -0.053 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap (n=345, ref 0.743 → 0.741) | -0.002 [-0.017, +0.012] | 0.838 | ~0.839 | 17/19/309 | +0.006 | -0.029 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.719) | **+0.178** [+0.121, +0.251] | 0.000 | ~0.000 | 32/3/59 | +0.223 | +0.064 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp24 mined-only (same features) (n=345, ref 0.760 → 0.741) | **-0.019** [-0.034, -0.006] | 0.009 | ~0.008 | 6/28/311 | -0.035 | -0.009 |
| ltr24__logreg__notype-nobge__pooled | vs convex05 (n=345, ref 0.703 → 0.748) | **+0.045** [+0.028, +0.065] | 0.000 | ~0.000 | 44/11/290 | +0.061 | +0.012 |
| ltr24__logreg__notype-nobge__pooled | vs exp13_lex (n=345, ref 0.708 → 0.748) | **+0.040** [+0.025, +0.060] | 0.000 | ~0.000 | 37/12/296 | +0.055 | +0.017 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.731) | +0.023 [+0.001, +0.058] | 0.106 | 0.109 | 6/8/80 | +0.053 | -0.064 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap (n=345, ref 0.743 → 0.748) | +0.006 [-0.014, +0.024] | 0.564 | ~0.568 | 22/22/301 | +0.029 | -0.035 |
| ltr24__logreg__notype-nobge__pooled | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.731) | **+0.190** [+0.131, +0.264] | 0.000 | ~0.000 | 30/4/60 | +0.255 | +0.053 |
| ltr24__logreg__notype-nobge__pooled | vs exp24 mined-only (same features) (n=345, ref 0.744 → 0.748) | +0.004 [-0.008, +0.017] | 0.506 | ~0.515 | 15/18/312 | +0.006 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs convex05 (n=345, ref 0.703 → 0.748) | **+0.045** [+0.027, +0.066] | 0.000 | ~0.000 | 41/10/294 | +0.055 | +0.026 |
| ltr24__lgbm-tiny__small__pooled | vs exp13_lex (n=345, ref 0.708 → 0.748) | **+0.040** [+0.025, +0.061] | 0.000 | ~0.000 | 34/8/303 | +0.049 | +0.032 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.731) | **+0.023** [+0.006, +0.053] | 0.046 | 0.048 | 8/5/81 | +0.043 | -0.011 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap (n=345, ref 0.743 → 0.748) | +0.006 [-0.011, +0.024] | 0.505 | ~0.509 | 16/21/308 | +0.023 | -0.020 |
| ltr24__lgbm-tiny__small__pooled | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.731) | **+0.190** [+0.132, +0.262] | 0.000 | ~0.000 | 32/1/61 | +0.245 | +0.106 |
| ltr24__lgbm-tiny__small__pooled | vs exp24 mined-only (same features) (n=345, ref 0.749 → 0.748) | -0.000 [-0.008, +0.009] | 0.940 | ~0.944 | 8/17/320 | -0.003 | +0.003 |
| ltr24__logreg__small__pooled | vs convex05 (n=345, ref 0.703 → 0.745) | **+0.042** [+0.022, +0.063] | 0.000 | ~0.000 | 38/15/292 | +0.061 | +0.000 |
| ltr24__logreg__small__pooled | vs exp13_lex (n=345, ref 0.708 → 0.745) | **+0.036** [+0.021, +0.057] | 0.000 | ~0.000 | 34/14/297 | +0.055 | +0.006 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.735) | +0.027 [+0.003, +0.063] | 0.079 | 0.077 | 7/8/79 | +0.064 | -0.064 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap (n=345, ref 0.743 → 0.745) | +0.002 [-0.019, +0.023] | 0.827 | ~0.828 | 22/25/298 | +0.029 | -0.046 |
| ltr24__logreg__small__pooled | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.735) | **+0.194** [+0.133, +0.269] | 0.000 | ~0.000 | 30/4/60 | +0.266 | +0.053 |
| ltr24__logreg__small__pooled | vs exp24 mined-only (same features) (n=345, ref 0.736 → 0.745) | +0.009 [-0.004, +0.023] | 0.189 | ~0.193 | 18/13/314 | +0.009 | +0.009 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05 (n=345, ref 0.703 → 0.730) | **+0.027** [+0.010, +0.046] | 0.004 | ~0.002 | 40/15/290 | +0.026 | +0.009 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp13_lex (n=345, ref 0.708 → 0.730) | **+0.022** [+0.005, +0.040] | 0.015 | ~0.012 | 34/13/298 | +0.020 | +0.015 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.705) | -0.003 [-0.021, +0.019] | 0.780 | 0.795 | 4/9/81 | +0.011 | -0.064 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap (n=345, ref 0.743 → 0.730) | -0.012 [-0.030, +0.003] | 0.131 | ~0.133 | 14/24/307 | -0.006 | -0.038 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.705) | **+0.164** [+0.110, +0.235] | 0.000 | ~0.000 | 30/4/60 | +0.213 | +0.053 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp24 mined-only (same features) (n=345, ref 0.759 → 0.730) | **-0.029** [-0.046, -0.015] | 0.000 | ~0.000 | 6/32/307 | -0.043 | -0.020 |
| ltr24__logreg__notype__pooled-scored | vs convex05 (n=345, ref 0.703 → 0.742) | **+0.039** [+0.021, +0.059] | 0.000 | ~0.000 | 37/16/292 | +0.055 | +0.003 |
| ltr24__logreg__notype__pooled-scored | vs exp13_lex (n=345, ref 0.708 → 0.742) | **+0.034** [+0.016, +0.054] | 0.001 | ~0.000 | 35/16/294 | +0.049 | +0.009 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.734) | +0.026 [+0.003, +0.064] | 0.081 | 0.081 | 7/8/79 | +0.064 | -0.064 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap (n=345, ref 0.743 → 0.742) | -0.000 [-0.024, +0.021] | 0.976 | ~0.977 | 23/25/297 | +0.023 | -0.043 |
| ltr24__logreg__notype__pooled-scored | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.734) | **+0.194** [+0.133, +0.269] | 0.000 | ~0.000 | 29/5/60 | +0.266 | +0.053 |
| ltr24__logreg__notype__pooled-scored | vs exp24 mined-only (same features) (n=345, ref 0.744 → 0.742) | -0.001 [-0.016, +0.013] | 0.845 | ~0.849 | 15/20/310 | +0.000 | -0.012 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05 (n=345, ref 0.703 → 0.733) | **+0.029** [+0.012, +0.049] | 0.002 | ~0.001 | 41/14/290 | +0.029 | +0.023 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp13_lex (n=345, ref 0.708 → 0.733) | **+0.024** [+0.007, +0.043] | 0.008 | ~0.007 | 35/11/299 | +0.023 | +0.029 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.706) | -0.002 [-0.020, +0.020] | 0.851 | 0.874 | 4/8/82 | +0.011 | -0.043 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap (n=345, ref 0.743 → 0.733) | -0.010 [-0.027, +0.005] | 0.232 | ~0.234 | 14/24/307 | -0.003 | -0.023 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.706) | **+0.165** [+0.111, +0.236] | 0.000 | ~0.000 | 31/3/60 | +0.213 | +0.074 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp24 mined-only (same features) (n=345, ref 0.769 → 0.733) | **-0.036** [-0.056, -0.021] | 0.000 | ~0.000 | 4/33/308 | -0.049 | -0.020 |
| ltr24__logreg__withtype__pooled-scored | vs convex05 (n=345, ref 0.703 → 0.754) | **+0.051** [+0.031, +0.073] | 0.000 | ~0.000 | 50/6/289 | +0.061 | +0.029 |
| ltr24__logreg__withtype__pooled-scored | vs exp13_lex (n=345, ref 0.708 → 0.754) | **+0.046** [+0.027, +0.068] | 0.000 | ~0.000 | 44/8/293 | +0.055 | +0.035 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.743) | **+0.035** [+0.013, +0.071] | 0.016 | 0.013 | 10/4/80 | +0.064 | -0.011 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap (n=345, ref 0.743 → 0.754) | +0.012 [-0.007, +0.031] | 0.224 | ~0.224 | 25/19/301 | +0.029 | -0.017 |
| ltr24__logreg__withtype__pooled-scored | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.743) | **+0.203** [+0.142, +0.277] | 0.000 | ~0.000 | 33/1/60 | +0.266 | +0.106 |
| ltr24__logreg__withtype__pooled-scored | vs exp24 mined-only (same features) (n=345, ref 0.759 → 0.754) | -0.005 [-0.015, +0.006] | 0.332 | ~0.339 | 8/17/320 | -0.006 | -0.009 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05 (n=345, ref 0.703 → 0.723) | **+0.020** [+0.004, +0.038] | 0.025 | ~0.024 | 38/17/290 | +0.017 | +0.012 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp13_lex (n=345, ref 0.708 → 0.723) | +0.015 [-0.002, +0.033] | 0.098 | ~0.099 | 32/16/297 | +0.012 | +0.017 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.697) | -0.011 [-0.027, +0.006] | 0.213 | 0.252 | 1/10/83 | +0.000 | -0.064 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=345, ref 0.743 → 0.723) | **-0.019** [-0.037, -0.004] | 0.020 | ~0.019 | 10/29/306 | -0.015 | -0.035 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.697) | **+0.157** [+0.102, +0.225] | 0.000 | ~0.000 | 30/3/61 | +0.202 | +0.053 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=345, ref 0.730 → 0.723) | -0.007 [-0.020, +0.007] | 0.285 | ~0.293 | 11/26/308 | -0.009 | -0.015 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05 (n=345, ref 0.703 → 0.712) | +0.009 [-0.009, +0.029] | 0.359 | ~0.364 | 29/27/289 | +0.006 | +0.003 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp13_lex (n=345, ref 0.708 → 0.712) | +0.004 [-0.014, +0.022] | 0.692 | ~0.694 | 27/27/291 | +0.000 | +0.009 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.689) | -0.018 [-0.045, +0.006] | 0.158 | 0.164 | 3/13/78 | -0.011 | -0.064 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=345, ref 0.743 → 0.712) | **-0.031** [-0.052, -0.013] | 0.002 | ~0.002 | 12/36/297 | -0.026 | -0.043 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.689) | **+0.149** [+0.093, +0.216] | 0.000 | ~0.000 | 29/6/59 | +0.192 | +0.053 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=345, ref 0.696 → 0.712) | +0.016 [-0.004, +0.038] | 0.140 | ~0.144 | 27/28/290 | +0.020 | -0.006 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05 (n=345, ref 0.703 → 0.750) | **+0.046** [+0.029, +0.067] | 0.000 | ~0.000 | 45/8/292 | +0.055 | +0.020 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp13_lex (n=345, ref 0.708 → 0.750) | **+0.041** [+0.024, +0.063] | 0.000 | ~0.000 | 38/7/300 | +0.049 | +0.026 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.728) | +0.021 [-0.003, +0.052] | 0.138 | 0.145 | 7/7/80 | +0.043 | -0.053 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=345, ref 0.743 → 0.750) | +0.007 [-0.010, +0.025] | 0.403 | ~0.404 | 20/16/309 | +0.023 | -0.026 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.728) | **+0.188** [+0.126, +0.261] | 0.000 | ~0.000 | 32/3/59 | +0.245 | +0.064 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=345, ref 0.760 → 0.750) | -0.010 [-0.023, +0.002] | 0.106 | ~0.102 | 9/20/316 | -0.017 | -0.006 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05 (n=345, ref 0.703 → 0.747) | **+0.043** [+0.029, +0.062] | 0.000 | ~0.000 | 39/9/297 | +0.061 | +0.009 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp13_lex (n=345, ref 0.708 → 0.747) | **+0.038** [+0.023, +0.058] | 0.000 | ~0.000 | 34/12/299 | +0.055 | +0.015 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.724) | +0.016 [-0.003, +0.050] | 0.215 | 0.226 | 5/8/81 | +0.043 | -0.053 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=345, ref 0.743 → 0.747) | +0.004 [-0.017, +0.024] | 0.675 | ~0.680 | 22/22/301 | +0.029 | -0.038 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.724) | **+0.184** [+0.127, +0.257] | 0.000 | ~0.000 | 31/3/60 | +0.245 | +0.064 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=345, ref 0.744 → 0.747) | +0.003 [-0.014, +0.020] | 0.748 | ~0.757 | 13/22/310 | +0.006 | -0.003 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05 (n=345, ref 0.703 → 0.722) | **+0.018** [+0.002, +0.037] | 0.039 | ~0.038 | 33/20/292 | +0.020 | +0.009 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp13_lex (n=345, ref 0.708 → 0.722) | +0.013 [-0.004, +0.033] | 0.151 | ~0.153 | 28/22/295 | +0.015 | +0.015 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.693) | -0.015 [-0.033, +0.002] | 0.095 | 0.095 | 1/12/81 | +0.000 | -0.074 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap (n=345, ref 0.743 → 0.722) | **-0.021** [-0.038, -0.006] | 0.012 | ~0.010 | 8/31/306 | -0.012 | -0.038 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.693) | **+0.152** [+0.095, +0.222] | 0.000 | ~0.000 | 30/5/59 | +0.202 | +0.043 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp24 mined-only (same features) (n=345, ref 0.749 → 0.722) | **-0.027** [-0.046, -0.009] | 0.005 | ~0.005 | 10/33/302 | -0.038 | -0.015 |
| ltr24__logreg__small__pooled-scored | vs convex05 (n=345, ref 0.703 → 0.741) | **+0.037** [+0.019, +0.058] | 0.000 | ~0.000 | 36/18/291 | +0.055 | -0.006 |
| ltr24__logreg__small__pooled-scored | vs exp13_lex (n=345, ref 0.708 → 0.741) | **+0.032** [+0.015, +0.052] | 0.001 | ~0.000 | 33/15/297 | +0.049 | +0.000 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap+bge (n=94, ref 0.708 → 0.733) | +0.025 [+0.001, +0.062] | 0.104 | 0.105 | 7/8/79 | +0.064 | -0.074 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap (n=345, ref 0.743 → 0.741) | -0.002 [-0.023, +0.018] | 0.864 | ~0.865 | 20/26/299 | +0.023 | -0.052 |
| ltr24__logreg__small__pooled-scored | vs convex05+bge@20 (sub) (n=94, ref 0.540 → 0.733) | **+0.192** [+0.131, +0.268] | 0.000 | ~0.000 | 29/5/60 | +0.266 | +0.043 |
| ltr24__logreg__small__pooled-scored | vs exp24 mined-only (same features) (n=345, ref 0.736 → 0.741) | +0.005 [-0.012, +0.023] | 0.594 | ~0.600 | 16/20/309 | +0.003 | +0.003 |
