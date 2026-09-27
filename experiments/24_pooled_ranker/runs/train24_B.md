### Experiment 24 – corpus B: pooled-label ranker

Coverage: `{"human_train": {"n": 24, "bge_full_top20": 24, "bge_any": 24, "mean_top20_coverage": 1.0, "q_verbatim_gt0.2": 0, "words_median": 20.0}, "human_val": {"n": 16, "bge_full_top20": 16, "bge_any": 16, "mean_top20_coverage": 1.0, "q_verbatim_gt0.2": 0, "words_median": 20.5}, "mined_train": {"n": 145, "bge_full_top20": 68, "bge_any": 68, "mean_top20_coverage": 0.469, "q_verbatim_gt0.2": 2, "words_median": 79.0}, "mined_val": {"n": 159, "bge_full_top20": 82, "bge_any": 82, "mean_top20_coverage": 0.516, "q_verbatim_gt0.2": 4, "words_median": 78.0}}`; bge sources `{"exp21_cache_pairs": 3800, "exp22_pairs": 2800, "exp22_added": 1690, "merged_pairs": 5490}`; candidate recall human 0.975 / mined 0.849

| pool | features | method | n pool (human) | w_h / C (nested CV crit: mined / human) | human **val** MRR (H@1 / R@10) | human oof all | human oof (all mined) | human train resub | mined val (scored) | mined val per source | mined train resub | post-hoc human val per w |
|---|---|---|--:|---|---|--:|--:|--:|---|---|--:|---|
| mined | notype | lgbm-tiny | 145 (0) | 1 / – (0.436: 0.436 / nan) | **0.442** (0.312 / 0.562) | **0.483** | nan | 0.511 | 0.478 (0.585) | pq 0.294, ruling 0.704, faq 0.000 | 0.494 |  |
| mined | notype | logreg | 145 (0) | 1 / 0.03 (0.438: 0.438 / nan) | **0.415** (0.312 / 0.625) | **0.499** | nan | 0.555 | 0.431 (0.529) | pq 0.252, ruling 0.651, faq 0.000 | 0.456 |  |
| mined | withtype | lgbm-tiny | 145 (0) | 1 / – (0.445: 0.445 / nan) | **0.433** (0.312 / 0.625) | **0.493** | nan | 0.534 | 0.483 (0.589) | pq 0.298, ruling 0.711, faq 0.000 | 0.498 |  |
| mined | withtype | logreg | 145 (0) | 1 / 0.03 (0.454: 0.454 / nan) | **0.416** (0.312 / 0.562) | **0.476** | nan | 0.516 | 0.446 (0.537) | pq 0.262, ruling 0.671, faq 0.000 | 0.475 |  |
| mined | notype-nogate | lgbm-tiny | 145 (0) | 1 / – (0.441: 0.441 / nan) | **0.448** (0.312 / 0.625) | **0.528** | nan | 0.582 | 0.479 (0.590) | pq 0.292, ruling 0.710, faq 0.000 | 0.493 |  |
| mined | notype-nogate | logreg | 145 (0) | 1 / 0.03 (0.443: 0.443 / nan) | **0.465** (0.375 / 0.625) | **0.524** | nan | 0.564 | 0.434 (0.531) | pq 0.248, ruling 0.662, faq 0.000 | 0.454 |  |
| mined | notype-nobge | lgbm-tiny | 145 (0) | 1 / – (0.431: 0.431 / nan) | **0.372** (0.250 / 0.562) | **0.432** | nan | 0.472 | 0.479 (0.589) | pq 0.287, ruling 0.716, faq 0.000 | 0.484 |  |
| mined | notype-nobge | logreg | 145 (0) | 1 / 0.3 (0.425: 0.425 / nan) | **0.255** (0.125 / 0.562) | **0.336** | nan | 0.390 | 0.440 (0.533) | pq 0.245, ruling 0.680, faq 0.000 | 0.450 |  |
| mined | small | lgbm-tiny | 145 (0) | 1 / – (0.413: 0.413 / nan) | **0.425** (0.250 / 0.625) | **0.477** | nan | 0.512 | 0.474 (0.585) | pq 0.291, ruling 0.700, faq 0.000 | 0.472 |  |
| mined | small | logreg | 145 (0) | 1 / 1.0 (0.457: 0.457 / nan) | **0.447** (0.375 / 0.562) | **0.469** | nan | 0.484 | 0.441 (0.538) | pq 0.271, ruling 0.650, faq 0.000 | 0.457 |  |
| pooled | notype | lgbm-tiny | 169 (24) | 5 / – (0.545: 0.438 / 0.652) | **0.497** (0.312 / 0.875) | **0.577** | 0.612 | 0.800 | 0.452 (0.548) | pq 0.269, ruling 0.677, faq 0.000 | 0.475 | w=1.0 0.496, w=5.0 0.497, w=10.0 0.531 |
| pooled | notype | logreg | 169 (24) | 5 / 0.1 (0.536: 0.448 / 0.624) | **0.423** (0.188 / 0.750) | **0.524** | 0.523 | 0.644 | 0.434 (0.530) | pq 0.253, ruling 0.656, faq 0.000 | 0.457 | w=1.0 0.430, w=5.0 0.423, w=10.0 0.451 |
| pooled | withtype | lgbm-tiny | 169 (24) | 5 / – (0.543: 0.427 / 0.659) | **0.490** (0.312 / 0.875) | **0.588** | 0.591 | 0.798 | 0.454 (0.544) | pq 0.273, ruling 0.676, faq 0.000 | 0.470 | w=1.0 0.475, w=5.0 0.490, w=10.0 0.521 |
| pooled | withtype | logreg | 169 (24) | 5 / 0.03 (0.541: 0.455 / 0.628) | **0.425** (0.188 / 0.750) | **0.530** | 0.524 | 0.672 | 0.443 (0.528) | pq 0.259, ruling 0.669, faq 0.000 | 0.478 | w=1.0 0.440, w=5.0 0.425, w=10.0 0.441 |
| pooled | notype-nogate | lgbm-tiny | 169 (24) | 5 / – (0.534: 0.427 / 0.641) | **0.498** (0.312 / 0.875) | **0.566** | 0.614 | 0.804 | 0.450 (0.549) | pq 0.266, ruling 0.676, faq 0.000 | 0.469 | w=1.0 0.496, w=5.0 0.498, w=10.0 0.562 |
| pooled | notype-nogate | logreg | 169 (24) | 5 / 0.1 (0.539: 0.442 / 0.635) | **0.413** (0.188 / 0.750) | **0.498** | 0.491 | 0.651 | 0.425 (0.527) | pq 0.246, ruling 0.645, faq 0.000 | 0.459 | w=1.0 0.441, w=5.0 0.413, w=10.0 0.418 |
| pooled | notype-nobge | lgbm-tiny | 169 (24) | 1 / – (0.458: 0.429 / 0.487) | **0.305** (0.125 / 0.562) | **0.401** | 0.420 | 0.611 | 0.467 (0.569) | pq 0.286, ruling 0.689, faq 0.000 | 0.488 | w=1.0 0.305, w=5.0 0.337, w=10.0 0.362 |
| pooled | notype-nobge | logreg | 169 (24) | 5 / 1.0 (0.472: 0.426 / 0.518) | **0.276** (0.062 / 0.625) | **0.393** | 0.382 | 0.605 | 0.444 (0.544) | pq 0.271, ruling 0.658, faq 0.000 | 0.425 | w=1.0 0.272, w=5.0 0.276, w=10.0 0.294 |
| pooled | small | lgbm-tiny | 169 (24) | 5 / – (0.557: 0.429 / 0.685) | **0.530** (0.375 / 0.812) | **0.623** | 0.618 | 0.813 | 0.451 (0.541) | pq 0.284, ruling 0.658, faq 0.000 | 0.450 | w=1.0 0.519, w=5.0 0.530, w=10.0 0.534 |
| pooled | small | logreg | 169 (24) | 10 / 0.1 (0.519: 0.434 / 0.604) | **0.506** (0.312 / 0.750) | **0.550** | 0.541 | 0.623 | 0.427 (0.525) | pq 0.270, ruling 0.621, faq 0.000 | 0.434 | w=1.0 0.449, w=5.0 0.494, w=10.0 0.506 |
| pooled-scored | notype | lgbm-tiny | 92 (24) | 1 / – (0.575: 0.502 / 0.648) | **0.542** (0.375 / 0.875) | **0.601** | 0.554 | 0.800 | 0.441 (0.550) | pq 0.268, ruling 0.653, faq 0.000 | 0.421 | w=1.0 0.542, w=5.0 0.587, w=10.0 0.503 |
| pooled-scored | notype | logreg | 92 (24) | 5 / 0.1 (0.603: 0.542 / 0.664) | **0.481** (0.250 / 0.812) | **0.560** | 0.523 | 0.667 | 0.391 (0.534) | pq 0.219, ruling 0.601, faq 0.000 | 0.402 | w=1.0 0.439, w=5.0 0.481, w=10.0 0.457 |
| pooled-scored | withtype | lgbm-tiny | 92 (24) | 1 / – (0.575: 0.509 / 0.642) | **0.510** (0.312 / 0.875) | **0.596** | 0.546 | 0.799 | 0.444 (0.549) | pq 0.277, ruling 0.649, faq 0.000 | 0.423 | w=1.0 0.510, w=5.0 0.525, w=10.0 0.534 |
| pooled-scored | withtype | logreg | 92 (24) | 5 / 0.1 (0.616: 0.568 / 0.664) | **0.454** (0.250 / 0.812) | **0.578** | 0.526 | 0.688 | 0.407 (0.539) | pq 0.234, ruling 0.619, faq 0.000 | 0.423 | w=1.0 0.507, w=5.0 0.454, w=10.0 0.460 |
| pooled-scored | notype-nogate | lgbm-tiny | 92 (24) | 5 / – (0.581: 0.524 / 0.639) | **0.576** (0.438 / 0.875) | **0.620** | 0.614 | 0.832 | 0.409 (0.515) | pq 0.253, ruling 0.600, faq 0.000 | 0.397 | w=1.0 0.540, w=5.0 0.576, w=10.0 0.576 |
| pooled-scored | notype-nogate | logreg | 92 (24) | 10 / 0.1 (0.599: 0.528 / 0.669) | **0.425** (0.188 / 0.812) | **0.530** | 0.508 | 0.681 | 0.391 (0.544) | pq 0.219, ruling 0.602, faq 0.000 | 0.373 | w=1.0 0.502, w=5.0 0.449, w=10.0 0.425 |
| pooled-scored | notype-nobge | lgbm-tiny | 92 (24) | 1 / – (0.508: 0.461 / 0.555) | **0.351** (0.188 / 0.688) | **0.446** | 0.420 | 0.680 | 0.436 (0.528) | pq 0.250, ruling 0.665, faq 0.000 | 0.443 | w=1.0 0.351, w=5.0 0.403, w=10.0 0.365 |
| pooled-scored | notype-nobge | logreg | 92 (24) | 5 / 0.03 (0.521: 0.460 / 0.582) | **0.316** (0.125 / 0.625) | **0.440** | 0.415 | 0.627 | 0.443 (0.528) | pq 0.264, ruling 0.662, faq 0.000 | 0.422 | w=1.0 0.311, w=5.0 0.316, w=10.0 0.357 |
| pooled-scored | small | lgbm-tiny | 92 (24) | 1 / – (0.591: 0.526 / 0.655) | **0.510** (0.312 / 0.875) | **0.597** | 0.551 | 0.764 | 0.437 (0.551) | pq 0.267, ruling 0.646, faq 0.000 | 0.423 | w=1.0 0.510, w=5.0 0.514, w=10.0 0.543 |
| pooled-scored | small | logreg | 92 (24) | 5 / 0.03 (0.555: 0.490 / 0.620) | **0.523** (0.375 / 0.750) | **0.592** | 0.537 | 0.676 | 0.427 (0.527) | pq 0.254, ruling 0.641, faq 0.000 | 0.418 | w=1.0 0.526, w=5.0 0.523, w=10.0 0.483 |

Nested-CV grid (criterion = mean of held-out mined and held-out human-train MRR):

* `lgbm-tiny__notype__pooled`: w=1.0: 0.521 (0.428/0.615); w=5.0: 0.545 (0.438/0.652); w=10.0: 0.527 (0.410/0.643)
* `logreg__notype__pooled`: w=1.0,C=0.03: 0.511 (0.450/0.572); w=1.0,C=0.1: 0.511 (0.447/0.575); w=1.0,C=0.3: 0.512 (0.447/0.577); w=1.0,C=1.0: 0.510 (0.447/0.572); w=1.0,C=3.0: 0.513 (0.447/0.579); w=5.0,C=0.03: 0.536 (0.441/0.631); w=5.0,C=0.1: 0.536 (0.448/0.624); w=5.0,C=0.3: 0.533 (0.441/0.626); w=5.0,C=1.0: 0.534 (0.449/0.619); w=5.0,C=3.0: 0.529 (0.438/0.621); w=10.0,C=0.03: 0.528 (0.435/0.620); w=10.0,C=0.1: 0.519 (0.425/0.612); w=10.0,C=0.3: 0.513 (0.420/0.607); w=10.0,C=1.0: 0.506 (0.411/0.601); w=10.0,C=3.0: 0.514 (0.414/0.615)
* `lgbm-tiny__withtype__pooled`: w=1.0: 0.517 (0.438/0.597); w=5.0: 0.543 (0.427/0.659); w=10.0: 0.532 (0.410/0.654)
* `logreg__withtype__pooled`: w=1.0,C=0.03: 0.523 (0.470/0.576); w=1.0,C=0.1: 0.513 (0.469/0.556); w=1.0,C=0.3: 0.500 (0.462/0.539); w=1.0,C=1.0: 0.497 (0.458/0.536); w=1.0,C=3.0: 0.494 (0.452/0.536); w=5.0,C=0.03: 0.541 (0.455/0.628); w=5.0,C=0.1: 0.532 (0.456/0.608); w=5.0,C=0.3: 0.513 (0.452/0.574); w=5.0,C=1.0: 0.506 (0.446/0.567); w=5.0,C=3.0: 0.505 (0.445/0.565); w=10.0,C=0.03: 0.532 (0.445/0.619); w=10.0,C=0.1: 0.509 (0.442/0.577); w=10.0,C=0.3: 0.498 (0.431/0.565); w=10.0,C=1.0: 0.487 (0.424/0.550); w=10.0,C=3.0: 0.482 (0.418/0.546)
* `lgbm-tiny__notype-nogate__pooled`: w=1.0: 0.514 (0.441/0.586); w=5.0: 0.534 (0.427/0.641); w=10.0: 0.524 (0.414/0.634)
* `logreg__notype-nogate__pooled`: w=1.0,C=0.03: 0.510 (0.448/0.573); w=1.0,C=0.1: 0.515 (0.445/0.585); w=1.0,C=0.3: 0.520 (0.446/0.594); w=1.0,C=1.0: 0.520 (0.450/0.590); w=1.0,C=3.0: 0.522 (0.454/0.591); w=5.0,C=0.03: 0.537 (0.442/0.632); w=5.0,C=0.1: 0.539 (0.442/0.635); w=5.0,C=0.3: 0.532 (0.441/0.623); w=5.0,C=1.0: 0.507 (0.433/0.580); w=5.0,C=3.0: 0.513 (0.441/0.585); w=10.0,C=0.03: 0.527 (0.434/0.621); w=10.0,C=0.1: 0.524 (0.431/0.617); w=10.0,C=0.3: 0.521 (0.430/0.613); w=10.0,C=1.0: 0.512 (0.414/0.610); w=10.0,C=3.0: 0.526 (0.416/0.637)
* `lgbm-tiny__notype-nobge__pooled`: w=1.0: 0.458 (0.429/0.487); w=5.0: 0.435 (0.396/0.473); w=10.0: 0.428 (0.384/0.472)
* `logreg__notype-nobge__pooled`: w=1.0,C=0.03: 0.430 (0.428/0.432); w=1.0,C=0.1: 0.432 (0.435/0.430); w=1.0,C=0.3: 0.434 (0.432/0.436); w=1.0,C=1.0: 0.432 (0.428/0.435); w=1.0,C=3.0: 0.433 (0.431/0.435); w=5.0,C=0.03: 0.461 (0.423/0.499); w=5.0,C=0.1: 0.471 (0.421/0.520); w=5.0,C=0.3: 0.469 (0.420/0.519); w=5.0,C=1.0: 0.472 (0.426/0.518); w=5.0,C=3.0: 0.471 (0.424/0.518); w=10.0,C=0.03: 0.460 (0.420/0.499); w=10.0,C=0.1: 0.470 (0.414/0.525); w=10.0,C=0.3: 0.467 (0.413/0.520); w=10.0,C=1.0: 0.468 (0.416/0.521); w=10.0,C=3.0: 0.469 (0.417/0.521)
* `lgbm-tiny__small__pooled`: w=1.0: 0.507 (0.423/0.592); w=5.0: 0.557 (0.429/0.685); w=10.0: 0.533 (0.414/0.652)
* `logreg__small__pooled`: w=1.0,C=0.03: 0.474 (0.439/0.509); w=1.0,C=0.1: 0.464 (0.440/0.487); w=1.0,C=0.3: 0.481 (0.445/0.517); w=1.0,C=1.0: 0.475 (0.439/0.511); w=1.0,C=3.0: 0.475 (0.438/0.511); w=5.0,C=0.03: 0.507 (0.445/0.568); w=5.0,C=0.1: 0.505 (0.440/0.570); w=5.0,C=0.3: 0.516 (0.440/0.592); w=5.0,C=1.0: 0.517 (0.441/0.592); w=5.0,C=3.0: 0.496 (0.441/0.551); w=10.0,C=0.03: 0.514 (0.429/0.599); w=10.0,C=0.1: 0.519 (0.434/0.604); w=10.0,C=0.3: 0.509 (0.434/0.584); w=10.0,C=1.0: 0.506 (0.432/0.581); w=10.0,C=3.0: 0.504 (0.427/0.581)
* `lgbm-tiny__notype__pooled-scored`: w=1.0: 0.575 (0.502/0.648); w=5.0: 0.572 (0.509/0.634); w=10.0: 0.567 (0.521/0.613)
* `logreg__notype__pooled-scored`: w=1.0,C=0.03: 0.581 (0.532/0.629); w=1.0,C=0.1: 0.581 (0.530/0.632); w=1.0,C=0.3: 0.581 (0.544/0.618); w=1.0,C=1.0: 0.573 (0.529/0.617); w=1.0,C=3.0: 0.556 (0.518/0.595); w=5.0,C=0.03: 0.595 (0.531/0.659); w=5.0,C=0.1: 0.603 (0.542/0.664); w=5.0,C=0.3: 0.596 (0.524/0.667); w=5.0,C=1.0: 0.576 (0.513/0.640); w=5.0,C=3.0: 0.572 (0.508/0.635); w=10.0,C=0.03: 0.593 (0.536/0.650); w=10.0,C=0.1: 0.595 (0.541/0.648); w=10.0,C=0.3: 0.581 (0.523/0.640); w=10.0,C=1.0: 0.579 (0.525/0.632); w=10.0,C=3.0: 0.578 (0.525/0.631)
* `lgbm-tiny__withtype__pooled-scored`: w=1.0: 0.575 (0.509/0.642); w=5.0: 0.574 (0.519/0.628); w=10.0: 0.573 (0.517/0.630)
* `logreg__withtype__pooled-scored`: w=1.0,C=0.03: 0.607 (0.562/0.651); w=1.0,C=0.1: 0.597 (0.561/0.632); w=1.0,C=0.3: 0.584 (0.575/0.594); w=1.0,C=1.0: 0.583 (0.567/0.598); w=1.0,C=3.0: 0.583 (0.567/0.599); w=5.0,C=0.03: 0.602 (0.560/0.643); w=5.0,C=0.1: 0.616 (0.568/0.664); w=5.0,C=0.3: 0.609 (0.565/0.653); w=5.0,C=1.0: 0.590 (0.552/0.627); w=5.0,C=3.0: 0.577 (0.557/0.598); w=10.0,C=0.03: 0.596 (0.565/0.627); w=10.0,C=0.1: 0.594 (0.570/0.619); w=10.0,C=0.3: 0.591 (0.568/0.613); w=10.0,C=1.0: 0.583 (0.567/0.599); w=10.0,C=3.0: 0.580 (0.565/0.595)
* `lgbm-tiny__notype-nogate__pooled-scored`: w=1.0: 0.575 (0.509/0.641); w=5.0: 0.581 (0.524/0.639); w=10.0: 0.564 (0.501/0.626)
* `logreg__notype-nogate__pooled-scored`: w=1.0,C=0.03: 0.579 (0.515/0.643); w=1.0,C=0.1: 0.574 (0.516/0.632); w=1.0,C=0.3: 0.578 (0.521/0.634); w=1.0,C=1.0: 0.574 (0.528/0.621); w=1.0,C=3.0: 0.575 (0.527/0.623); w=5.0,C=0.03: 0.585 (0.530/0.639); w=5.0,C=0.1: 0.590 (0.528/0.651); w=5.0,C=0.3: 0.589 (0.527/0.651); w=5.0,C=1.0: 0.573 (0.511/0.635); w=5.0,C=3.0: 0.574 (0.519/0.628); w=10.0,C=0.03: 0.590 (0.534/0.645); w=10.0,C=0.1: 0.599 (0.528/0.669); w=10.0,C=0.3: 0.573 (0.514/0.632); w=10.0,C=1.0: 0.572 (0.517/0.628); w=10.0,C=3.0: 0.572 (0.513/0.631)
* `lgbm-tiny__notype-nobge__pooled-scored`: w=1.0: 0.508 (0.461/0.555); w=5.0: 0.494 (0.441/0.548); w=10.0: 0.471 (0.425/0.518)
* `logreg__notype-nobge__pooled-scored`: w=1.0,C=0.03: 0.511 (0.473/0.550); w=1.0,C=0.1: 0.505 (0.484/0.526); w=1.0,C=0.3: 0.488 (0.473/0.502); w=1.0,C=1.0: 0.481 (0.467/0.495); w=1.0,C=3.0: 0.476 (0.459/0.493); w=5.0,C=0.03: 0.521 (0.460/0.582); w=5.0,C=0.1: 0.512 (0.465/0.558); w=5.0,C=0.3: 0.502 (0.458/0.547); w=5.0,C=1.0: 0.505 (0.443/0.566); w=5.0,C=3.0: 0.504 (0.443/0.566); w=10.0,C=0.03: 0.499 (0.452/0.547); w=10.0,C=0.1: 0.497 (0.448/0.547); w=10.0,C=0.3: 0.498 (0.427/0.570); w=10.0,C=1.0: 0.496 (0.424/0.567); w=10.0,C=3.0: 0.491 (0.424/0.559)
* `lgbm-tiny__small__pooled-scored`: w=1.0: 0.591 (0.526/0.655); w=5.0: 0.574 (0.507/0.640); w=10.0: 0.545 (0.503/0.588)
* `logreg__small__pooled-scored`: w=1.0,C=0.03: 0.537 (0.502/0.572); w=1.0,C=0.1: 0.536 (0.501/0.572); w=1.0,C=0.3: 0.553 (0.502/0.604); w=1.0,C=1.0: 0.553 (0.502/0.604); w=1.0,C=3.0: 0.555 (0.505/0.604); w=5.0,C=0.03: 0.555 (0.490/0.620); w=5.0,C=0.1: 0.536 (0.496/0.577); w=5.0,C=0.3: 0.525 (0.492/0.558); w=5.0,C=1.0: 0.541 (0.504/0.578); w=5.0,C=3.0: 0.541 (0.504/0.577); w=10.0,C=0.03: 0.546 (0.489/0.604); w=10.0,C=0.1: 0.542 (0.502/0.582); w=10.0,C=0.3: 0.539 (0.518/0.561); w=10.0,C=1.0: 0.549 (0.518/0.580); w=10.0,C=3.0: 0.538 (0.516/0.559)

Top features (fit A):

* `lgbm-tiny__notype__mined`: lex13_logrank +0.240, lex13_norm +0.183, title_overlap_n +0.099, rrf60_logrank +0.077, log_doc_len +0.066, title_overlap +0.056, rrf60 +0.053, e5_logrank +0.039, log_n_chunks +0.025, bge_norm +0.024
* `logreg__notype__mined`: lex13_logrank -0.670, e5_logrank -0.427, title_overlap_n +0.381, title_overlap +0.334, ov8_any -0.276, log_n_chunks -0.254, region_match -0.246, log_doc_len -0.229, q_verbatim -0.207, e5_top30 +0.184
* `lgbm-tiny__withtype__mined`: lex13_logrank +0.238, lex13_norm +0.180, title_overlap_n +0.091, rrf60_logrank +0.072, log_doc_len +0.072, title_overlap +0.053, rrf60 +0.040, bge_norm +0.031, e5_logrank +0.030, convex05_logrank +0.030
* `logreg__withtype__mined`: lex13_logrank -0.667, e5_logrank -0.411, type=vcf -0.371, title_overlap_n +0.336, type=arcir92 -0.290, title_overlap +0.272, ov8_any -0.261, region_match -0.248, log_n_chunks -0.241, type=cenr +0.229
* `lgbm-tiny__notype-nogate__mined`: lex13_logrank +0.245, lex13_norm +0.188, title_overlap_n +0.094, rrf60_logrank +0.077, log_doc_len +0.073, title_overlap +0.057, rrf60 +0.041, bge_norm +0.040, e5_logrank +0.030, e5_norm +0.025
* `logreg__notype-nogate__mined`: lex13_logrank -0.667, e5_logrank -0.418, title_overlap_n +0.326, log_n_chunks -0.255, region_match -0.233, log_doc_len -0.211, lex13_top30 +0.194, e5_top30 +0.193, bge_logrank -0.188, bge_norm +0.183
* `lgbm-tiny__notype-nobge__mined`: lex13_logrank +0.250, lex13_norm +0.193, title_overlap_n +0.102, rrf60_logrank +0.088, log_doc_len +0.077, title_overlap +0.064, e5_logrank +0.054, rrf60 +0.052, e5_norm +0.022, log_n_chunks +0.021
* `logreg__notype-nobge__mined`: lex13_logrank -1.096, e5_logrank -1.006, title_overlap_n +0.493, convex05_logrank -0.459, ov8_any -0.432, rrf60 -0.432, bm25doc_norm +0.427, log_n_chunks -0.415, title_overlap +0.393, convex05 -0.375
* `lgbm-tiny__small__mined`: lex13_norm +0.444, e5_norm +0.126, title_overlap +0.122, log_doc_len +0.084, convex05 +0.080, bge_norm +0.063, bge_norm_x_loglen +0.036, bm25doc_norm +0.027, bge_max +0.014, bm25_norm +0.003
* `logreg__small__mined`: lex13_norm +0.706, bge_norm_x_loglen +0.564, title_overlap +0.497, convex05 +0.483, log_doc_len -0.445, bm25_norm -0.370, bm25doc_norm +0.330, q_len_words +0.303, bge_qcov -0.227, bge_norm -0.215
* `lgbm-tiny__notype__pooled`: bge_logrank +0.170, e5_norm +0.160, lex13_norm +0.115, bge_norm +0.110, e5_logrank +0.102, lex13_logrank +0.077, rrf60_logrank +0.060, bge_norm_x_loglen +0.051, title_overlap_n +0.038, n_legs_top30 +0.025
* `logreg__notype__pooled`: e5_logrank -1.079, rrf60 -0.798, lex13_logrank -0.798, log_n_chunks -0.649, bge_logrank -0.592, title_overlap_n +0.461, bge_qcov -0.427, bge_max -0.403, ov8_any -0.347, bge_norm +0.325
* `lgbm-tiny__withtype__pooled`: bge_logrank +0.172, e5_norm +0.157, lex13_norm +0.126, bge_norm +0.123, e5_logrank +0.097, lex13_logrank +0.069, rrf60_logrank +0.056, bge_norm_x_loglen +0.047, title_overlap_n +0.036, log_doc_len +0.019
* `logreg__withtype__pooled`: e5_logrank -0.663, lex13_logrank -0.655, bge_logrank -0.461, rrf60 -0.413, log_n_chunks -0.359, bge_qcov -0.329, type=arcir92 -0.322, bge_norm +0.313, bge_max -0.309, type=vcf -0.290
* `lgbm-tiny__notype-nogate__pooled`: bge_logrank +0.187, e5_norm +0.167, bge_norm +0.144, lex13_norm +0.125, e5_logrank +0.112, lex13_logrank +0.071, title_overlap_n +0.040, rrf60_logrank +0.039, log_doc_len +0.022, n_legs_top30 +0.018
* `logreg__notype-nogate__pooled`: e5_logrank -1.064, rrf60 -0.790, lex13_logrank -0.776, log_n_chunks -0.668, bge_logrank -0.634, bge_qcov -0.447, bge_max -0.445, title_overlap_n +0.294, e5_max -0.284, q_has_region -0.280
* `lgbm-tiny__notype-nobge__pooled`: lex13_logrank +0.247, lex13_norm +0.202, e5_logrank +0.097, title_overlap_n +0.088, rrf60_logrank +0.077, e5_norm +0.072, log_doc_len +0.043, n_legs_top30 +0.042, rrf60 +0.031, title_overlap +0.028
* `logreg__notype-nobge__pooled`: e5_logrank -1.624, rrf60 -1.282, log_n_chunks -1.175, lex13_logrank -1.003, log_doc_len +0.639, q_has_region -0.572, rrf60_logrank -0.499, e5_norm -0.463, ov8_any -0.428, title_overlap_n +0.358
* `lgbm-tiny__small__pooled`: e5_norm +0.261, bge_norm +0.205, lex13_norm +0.196, bge_norm_x_loglen +0.164, bge_max +0.050, convex05 +0.044, log_doc_len +0.037, title_overlap +0.028, q_len_words +0.007, bm25doc_norm +0.005
* `logreg__small__pooled`: convex05 +0.777, bm25_norm -0.732, lex13_norm +0.534, bge_norm +0.363, bge_max -0.260, bge_qcov -0.244, q_verbatim -0.232, q_len_words +0.217, bge_missing -0.210, e5_norm +0.201
* `lgbm-tiny__notype__pooled-scored`: bge_logrank +0.304, bge_norm +0.189, bge_norm_x_loglen +0.151, e5_logrank +0.099, bge_max +0.072, log_doc_len +0.039, e5_norm +0.030, lex13_logrank +0.028, lex13_norm +0.020, title_overlap +0.014
* `logreg__notype__pooled-scored`: e5_logrank -1.206, rrf60 -0.776, lex13_logrank -0.771, log_n_chunks -0.615, bge_logrank -0.539, title_overlap_n +0.519, convex05_logrank +0.493, q_verbatim -0.490, ov8_any -0.415, bge_max +0.336
* `lgbm-tiny__withtype__pooled-scored`: bge_logrank +0.273, bge_norm +0.211, bge_norm_x_loglen +0.154, e5_logrank +0.104, bge_max +0.058, log_doc_len +0.040, e5_norm +0.036, lex13_logrank +0.034, lex13_norm +0.019, title_overlap +0.013
* `logreg__withtype__pooled-scored`: e5_logrank -1.221, rrf60 -0.815, lex13_logrank -0.777, log_n_chunks -0.561, bge_logrank -0.544, convex05_logrank +0.465, q_verbatim -0.420, bge_max +0.406, title_overlap_n +0.385, ov8_any -0.374
* `lgbm-tiny__notype-nogate__pooled-scored`: bge_logrank +0.316, bge_norm +0.265, e5_logrank +0.117, e5_norm +0.098, bge_max +0.062, log_doc_len +0.022, lex13_norm +0.022, convex05 +0.021, region_match +0.017, lex13_logrank +0.010
* `logreg__notype-nogate__pooled-scored`: e5_logrank -1.507, rrf60 -1.183, log_n_chunks -0.885, lex13_logrank -0.771, convex05_logrank +0.746, bge_logrank -0.620, convex05 +0.492, log_doc_len +0.490, title_overlap_n +0.364, bge_max +0.315
* `lgbm-tiny__notype-nobge__pooled-scored`: e5_logrank +0.247, lex13_logrank +0.213, lex13_norm +0.116, rrf60_logrank +0.115, e5_norm +0.099, log_doc_len +0.042, n_legs_top30 +0.032, title_overlap_n +0.028, title_overlap +0.022, best_pos_bm25 +0.018
* `logreg__notype-nobge__pooled-scored`: e5_logrank -0.834, lex13_logrank -0.643, log_n_chunks -0.386, ov8_any -0.339, title_overlap_n +0.306, e5_top30 +0.238, rrf60_logrank -0.233, q_verbatim -0.229, title_overlap +0.224, rrf60 -0.198
* `lgbm-tiny__small__pooled-scored`: bge_norm +0.377, bge_norm_x_loglen +0.277, e5_norm +0.107, bge_max +0.106, lex13_norm +0.048, log_doc_len +0.043, title_overlap +0.022, bm25_norm +0.006, convex05 +0.005, bge_missing +0.004
* `logreg__small__pooled-scored`: bge_norm +0.392, e5_norm +0.351, convex05 +0.333, q_verbatim -0.293, bm25_norm -0.252, bge_norm_x_loglen +0.232, lex13_norm +0.196, bge_max +0.176, bge_missing -0.170, q_len_words +0.169

Length-gate diagnostics (fit A, tree-SHAP contribution of the bge features; scored questions, human + mined val):

| model | words | n rows (q) | mean abs bge contrib | share of abs contrib | slope on bge_norm | Spearman | PD(bge_norm 0→1) | PD range |
|---|---|--:|--:|--:|--:|--:|---|--:|
| lgbm-tiny__notype__pooled | 0–25 | 825 (37) | 0.649 | 0.308 | +1.516 | +0.84 | -0.74 / -0.67 / -0.67 / -0.67 / 0.02 | +0.759 |
| lgbm-tiny__notype__pooled | 26–50 | 446 (19) | 0.567 | 0.285 | +1.585 | +0.81 | -0.66 / -0.59 / -0.59 / -0.59 / 0.03 | +0.692 |
| lgbm-tiny__notype__pooled | 51–100 | 822 (40) | 0.728 | 0.328 | +1.526 | +0.86 | -0.23 / -0.16 / -0.16 / -0.16 / 0.45 | +0.685 |
| lgbm-tiny__notype__pooled | 101–∞ | 577 (26) | 0.656 | 0.297 | +1.558 | +0.88 | -0.18 / -0.11 / -0.11 / -0.11 / 0.50 | +0.679 |
| lgbm-tiny__withtype__pooled | 0–25 | 825 (37) | 0.630 | 0.292 | +1.535 | +0.86 | -0.73 / -0.62 / -0.62 / -0.62 / 0.05 | +0.779 |
| lgbm-tiny__withtype__pooled | 26–50 | 446 (19) | 0.547 | 0.270 | +1.616 | +0.83 | -0.66 / -0.55 / -0.55 / -0.55 / 0.08 | +0.731 |
| lgbm-tiny__withtype__pooled | 51–100 | 822 (40) | 0.711 | 0.316 | +1.530 | +0.87 | -0.27 / -0.16 / -0.16 / -0.16 / 0.46 | +0.730 |
| lgbm-tiny__withtype__pooled | 101–∞ | 577 (26) | 0.640 | 0.284 | +1.556 | +0.89 | -0.22 / -0.12 / -0.12 / -0.12 / 0.52 | +0.734 |
| lgbm-tiny__notype__pooled-scored | 0–25 | 825 (37) | 0.955 | 0.487 | +1.993 | +0.90 | -0.80 / -0.56 / -0.56 / -0.56 / 0.12 | +0.919 |
| lgbm-tiny__notype__pooled-scored | 26–50 | 446 (19) | 0.838 | 0.462 | +2.199 | +0.89 | -0.85 / -0.62 / -0.62 / -0.62 / 0.06 | +0.907 |
| lgbm-tiny__notype__pooled-scored | 51–100 | 822 (40) | 1.141 | 0.522 | +1.990 | +0.90 | -0.40 / -0.15 / -0.15 / -0.15 / 0.54 | +0.937 |
| lgbm-tiny__notype__pooled-scored | 101–∞ | 577 (26) | 1.078 | 0.510 | +1.984 | +0.92 | -0.48 / -0.24 / -0.24 / -0.24 / 0.46 | +0.938 |
| lgbm-tiny__withtype__pooled-scored | 0–25 | 825 (37) | 0.934 | 0.478 | +2.001 | +0.91 | -0.81 / -0.58 / -0.58 / -0.58 / 0.14 | +0.953 |
| lgbm-tiny__withtype__pooled-scored | 26–50 | 446 (19) | 0.812 | 0.448 | +2.185 | +0.89 | -0.86 / -0.64 / -0.64 / -0.64 / 0.08 | +0.939 |
| lgbm-tiny__withtype__pooled-scored | 51–100 | 822 (40) | 1.110 | 0.513 | +1.964 | +0.91 | -0.43 / -0.20 / -0.20 / -0.20 / 0.54 | +0.977 |
| lgbm-tiny__withtype__pooled-scored | 101–∞ | 577 (26) | 1.052 | 0.501 | +1.961 | +0.92 | -0.53 / -0.29 / -0.29 / -0.29 / 0.48 | +1.002 |

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
| ltr24__logreg__notype__mined | vs bar_val (n=16, ref 0.570 → 0.415) | -0.155 [-0.398, +0.065] | 0.229 | 0.238 | 4/7/5 | -0.125 | -0.188 |
| ltr24__logreg__notype__mined | vs bar_full (n=16, ref 0.570 → 0.415) | -0.155 [-0.398, +0.065] | 0.229 | 0.238 | 4/7/5 | -0.125 | -0.188 |
| ltr24__logreg__notype__mined | vs exp14 (n=16, ref 0.519 → 0.415) | -0.104 [-0.345, +0.136] | 0.425 | 0.418 | 3/6/7 | -0.062 | -0.188 |
| ltr24__logreg__notype__mined | vs exp14_cheap (n=16, ref 0.411 → 0.415) | +0.004 [-0.144, +0.212] | 0.969 | 0.973 | 4/6/6 | +0.000 | -0.062 |
| ltr24__logreg__notype__mined | vs lex13 (n=16, ref 0.326 → 0.415) | +0.089 [-0.029, +0.259] | 0.247 | 0.266 | 8/2/6 | +0.062 | +0.000 |
| ltr24__logreg__notype__mined | vs bm25_01 (n=16, ref 0.290 → 0.415) | +0.125 [-0.013, +0.269] | 0.118 | 0.118 | 9/3/4 | +0.188 | +0.062 |
| ltr24__logreg__notype__mined | vs convex05 (n=16, ref 0.319 → 0.415) | +0.096 [-0.084, +0.291] | 0.346 | 0.349 | 7/5/4 | +0.125 | +0.062 |
| ltr24__logreg__notype__mined | vs convex05+bge@20 (n=16, ref 0.468 → 0.415) | -0.053 [-0.255, +0.153] | 0.632 | 0.614 | 5/7/4 | -0.062 | +0.000 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.415) | +0.019 [-0.087, +0.190] | 0.793 | 0.809 | 4/6/6 | +0.062 | +0.000 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap (n=16, ref 0.371 → 0.415) | +0.044 [+0.004, +0.156] | 0.204 | 0.234 | 4/3/9 | +0.062 | +0.062 |
| ltr24__logreg__notype__mined | vs exp22 gate T25 (n=16, ref 0.613 → 0.415) | -0.198 [-0.383, -0.011] | 0.064 | 0.067 | 2/10/4 | -0.125 | -0.312 |
| ltr24__lgbm-tiny__withtype__mined | vs bar_val (n=16, ref 0.570 → 0.433) | -0.138 [-0.374, +0.075] | 0.271 | 0.276 | 4/7/5 | -0.125 | -0.188 |
| ltr24__lgbm-tiny__withtype__mined | vs bar_full (n=16, ref 0.570 → 0.433) | -0.138 [-0.374, +0.075] | 0.271 | 0.276 | 4/7/5 | -0.125 | -0.188 |
| ltr24__lgbm-tiny__withtype__mined | vs exp14 (n=16, ref 0.519 → 0.433) | -0.086 [-0.325, +0.154] | 0.504 | 0.515 | 5/7/4 | -0.062 | -0.188 |
| ltr24__lgbm-tiny__withtype__mined | vs exp14_cheap (n=16, ref 0.411 → 0.433) | +0.021 [-0.141, +0.225] | 0.828 | 0.837 | 5/6/5 | +0.000 | -0.062 |
| ltr24__lgbm-tiny__withtype__mined | vs lex13 (n=16, ref 0.326 → 0.433) | +0.107 [-0.016, +0.274] | 0.174 | 0.172 | 8/2/6 | +0.062 | +0.000 |
| ltr24__lgbm-tiny__withtype__mined | vs bm25_01 (n=16, ref 0.290 → 0.433) | +0.142 [+0.004, +0.284] | 0.074 | 0.072 | 11/2/3 | +0.188 | +0.062 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05 (n=16, ref 0.319 → 0.433) | +0.114 [-0.084, +0.303] | 0.282 | 0.281 | 9/5/2 | +0.125 | +0.062 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05+bge@20 (n=16, ref 0.468 → 0.433) | -0.035 [-0.232, +0.164] | 0.742 | 0.757 | 6/7/3 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.433) | +0.036 [-0.074, +0.200] | 0.611 | 0.627 | 6/5/5 | +0.062 | +0.000 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap (n=16, ref 0.371 → 0.433) | +0.062 [+0.023, +0.170] | 0.070 | 0.008 | 8/1/7 | +0.062 | +0.062 |
| ltr24__lgbm-tiny__withtype__mined | vs exp22 gate T25 (n=16, ref 0.613 → 0.433) | -0.181 [-0.362, +0.002] | 0.081 | 0.085 | 2/10/4 | -0.125 | -0.312 |
| ltr24__logreg__withtype__mined | vs bar_val (n=16, ref 0.570 → 0.416) | -0.154 [-0.407, +0.071] | 0.250 | 0.251 | 5/7/4 | -0.125 | -0.250 |
| ltr24__logreg__withtype__mined | vs bar_full (n=16, ref 0.570 → 0.416) | -0.154 [-0.407, +0.071] | 0.250 | 0.251 | 5/7/4 | -0.125 | -0.250 |
| ltr24__logreg__withtype__mined | vs exp14 (n=16, ref 0.519 → 0.416) | -0.103 [-0.343, +0.142] | 0.432 | 0.431 | 4/8/4 | -0.062 | -0.250 |
| ltr24__logreg__withtype__mined | vs exp14_cheap (n=16, ref 0.411 → 0.416) | +0.005 [-0.146, +0.207] | 0.958 | 0.958 | 4/7/5 | +0.000 | -0.125 |
| ltr24__logreg__withtype__mined | vs lex13 (n=16, ref 0.326 → 0.416) | +0.090 [-0.055, +0.255] | 0.285 | 0.268 | 8/3/5 | +0.062 | -0.062 |
| ltr24__logreg__withtype__mined | vs bm25_01 (n=16, ref 0.290 → 0.416) | +0.126 [-0.035, +0.268] | 0.138 | 0.165 | 9/3/4 | +0.188 | +0.000 |
| ltr24__logreg__withtype__mined | vs convex05 (n=16, ref 0.319 → 0.416) | +0.097 [-0.084, +0.290] | 0.343 | 0.352 | 8/6/2 | +0.125 | +0.000 |
| ltr24__logreg__withtype__mined | vs convex05+bge@20 (n=16, ref 0.468 → 0.416) | -0.052 [-0.259, +0.151] | 0.642 | 0.639 | 6/7/3 | -0.062 | -0.062 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.416) | +0.020 [-0.107, +0.172] | 0.792 | 0.852 | 4/5/7 | +0.062 | -0.062 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap (n=16, ref 0.371 → 0.416) | +0.045 [-0.023, +0.153] | 0.329 | 0.342 | 6/4/6 | +0.062 | +0.000 |
| ltr24__logreg__withtype__mined | vs exp22 gate T25 (n=16, ref 0.613 → 0.416) | -0.197 [-0.397, -0.006] | 0.077 | 0.085 | 2/9/5 | -0.125 | -0.375 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bar_val (n=16, ref 0.570 → 0.448) | -0.122 [-0.358, +0.089] | 0.325 | 0.331 | 5/7/4 | -0.125 | -0.188 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bar_full (n=16, ref 0.570 → 0.448) | -0.122 [-0.358, +0.089] | 0.325 | 0.331 | 5/7/4 | -0.125 | -0.188 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp14 (n=16, ref 0.519 → 0.448) | -0.071 [-0.310, +0.169] | 0.582 | 0.594 | 5/7/4 | -0.062 | -0.188 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp14_cheap (n=16, ref 0.411 → 0.448) | +0.037 [-0.121, +0.236] | 0.704 | 0.718 | 5/6/5 | +0.000 | -0.062 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs lex13 (n=16, ref 0.326 → 0.448) | +0.122 [-0.005, +0.285] | 0.123 | 0.133 | 9/2/5 | +0.062 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bm25_01 (n=16, ref 0.290 → 0.448) | **+0.158** [+0.022, +0.294] | 0.045 | 0.042 | 11/1/4 | +0.188 | +0.062 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05 (n=16, ref 0.319 → 0.448) | +0.129 [-0.061, +0.316] | 0.213 | 0.214 | 9/5/2 | +0.125 | +0.062 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05+bge@20 (n=16, ref 0.468 → 0.448) | -0.020 [-0.198, +0.174] | 0.844 | 0.863 | 6/7/3 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.448) | +0.052 [-0.055, +0.210] | 0.455 | 0.438 | 6/4/6 | +0.062 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap (n=16, ref 0.371 → 0.448) | **+0.077** [+0.029, +0.176] | 0.041 | 0.008 | 8/1/7 | +0.062 | +0.062 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp22 gate T25 (n=16, ref 0.613 → 0.448) | -0.165 [-0.345, +0.013] | 0.104 | 0.108 | 2/9/5 | -0.125 | -0.312 |
| ltr24__logreg__notype-nogate__mined | vs bar_val (n=16, ref 0.570 → 0.465) | -0.105 [-0.347, +0.101] | 0.393 | 0.414 | 5/5/6 | -0.062 | -0.188 |
| ltr24__logreg__notype-nogate__mined | vs bar_full (n=16, ref 0.570 → 0.465) | -0.105 [-0.347, +0.101] | 0.393 | 0.414 | 5/5/6 | -0.062 | -0.188 |
| ltr24__logreg__notype-nogate__mined | vs exp14 (n=16, ref 0.519 → 0.465) | -0.054 [-0.313, +0.197] | 0.698 | 0.698 | 6/6/4 | +0.000 | -0.188 |
| ltr24__logreg__notype-nogate__mined | vs exp14_cheap (n=16, ref 0.411 → 0.465) | +0.054 [-0.119, +0.300] | 0.626 | 0.622 | 5/6/5 | +0.062 | -0.062 |
| ltr24__logreg__notype-nogate__mined | vs lex13 (n=16, ref 0.326 → 0.465) | +0.139 [-0.002, +0.339] | 0.133 | 0.129 | 8/1/7 | +0.125 | +0.000 |
| ltr24__logreg__notype-nogate__mined | vs bm25_01 (n=16, ref 0.290 → 0.465) | +0.175 [+0.024, +0.348] | 0.061 | 0.058 | 9/3/4 | +0.250 | +0.062 |
| ltr24__logreg__notype-nogate__mined | vs convex05 (n=16, ref 0.319 → 0.465) | +0.146 [-0.051, +0.360] | 0.198 | 0.193 | 8/5/3 | +0.188 | +0.062 |
| ltr24__logreg__notype-nogate__mined | vs convex05+bge@20 (n=16, ref 0.468 → 0.465) | -0.003 [-0.185, +0.191] | 0.979 | 0.977 | 5/6/5 | +0.000 | +0.000 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.465) | +0.069 [-0.056, +0.254] | 0.400 | 0.432 | 5/6/5 | +0.125 | +0.000 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap (n=16, ref 0.371 → 0.465) | +0.094 [+0.024, +0.240] | 0.082 | 0.055 | 6/3/7 | +0.125 | +0.062 |
| ltr24__logreg__notype-nogate__mined | vs exp22 gate T25 (n=16, ref 0.613 → 0.465) | -0.148 [-0.332, +0.021] | 0.138 | 0.150 | 2/9/5 | -0.062 | -0.312 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bar_val (n=16, ref 0.570 → 0.372) | -0.198 [-0.429, +0.011] | 0.113 | 0.118 | 3/8/5 | -0.188 | -0.250 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bar_full (n=16, ref 0.570 → 0.372) | -0.198 [-0.429, +0.011] | 0.113 | 0.118 | 3/8/5 | -0.188 | -0.250 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp14 (n=16, ref 0.519 → 0.372) | -0.146 [-0.389, +0.054] | 0.227 | 0.231 | 3/7/6 | -0.125 | -0.250 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp14_cheap (n=16, ref 0.411 → 0.372) | -0.039 [-0.206, +0.099] | 0.633 | 0.646 | 3/7/6 | -0.062 | -0.125 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs lex13 (n=16, ref 0.326 → 0.372) | +0.047 [-0.090, +0.226] | 0.579 | 0.592 | 8/4/4 | +0.000 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bm25_01 (n=16, ref 0.290 → 0.372) | +0.082 [-0.041, +0.224] | 0.261 | 0.248 | 10/2/4 | +0.125 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05 (n=16, ref 0.319 → 0.372) | +0.054 [-0.143, +0.209] | 0.568 | 0.573 | 7/6/3 | +0.062 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05+bge@20 (n=16, ref 0.468 → 0.372) | -0.095 [-0.306, +0.076] | 0.356 | 0.351 | 5/8/3 | -0.125 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.372) | -0.024 [-0.126, +0.085] | 0.672 | 0.648 | 4/6/6 | +0.000 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap (n=16, ref 0.371 → 0.372) | +0.002 [-0.000, +0.008] | 0.259 | 0.312 | 4/1/11 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp22 gate T25 (n=16, ref 0.613 → 0.372) | **-0.241** [-0.424, -0.074] | 0.019 | 0.021 | 1/10/5 | -0.188 | -0.375 |
| ltr24__logreg__notype-nobge__mined | vs bar_val (n=16, ref 0.570 → 0.255) | **-0.315** [-0.544, -0.101] | 0.018 | 0.019 | 2/9/5 | -0.312 | -0.250 |
| ltr24__logreg__notype-nobge__mined | vs bar_full (n=16, ref 0.570 → 0.255) | **-0.315** [-0.544, -0.101] | 0.018 | 0.019 | 2/9/5 | -0.312 | -0.250 |
| ltr24__logreg__notype-nobge__mined | vs exp14 (n=16, ref 0.519 → 0.255) | -0.264 [-0.498, -0.024] | 0.054 | 0.055 | 3/11/2 | -0.250 | -0.250 |
| ltr24__logreg__notype-nobge__mined | vs exp14_cheap (n=16, ref 0.411 → 0.255) | -0.156 [-0.335, -0.021] | 0.077 | 0.083 | 2/10/4 | -0.188 | -0.125 |
| ltr24__logreg__notype-nobge__mined | vs lex13 (n=16, ref 0.326 → 0.255) | -0.071 [-0.242, +0.012] | 0.259 | 0.359 | 5/4/7 | -0.125 | -0.062 |
| ltr24__logreg__notype-nobge__mined | vs bm25_01 (n=16, ref 0.290 → 0.255) | -0.035 [-0.186, +0.067] | 0.596 | 0.664 | 5/4/7 | +0.000 | +0.000 |
| ltr24__logreg__notype-nobge__mined | vs convex05 (n=16, ref 0.319 → 0.255) | -0.064 [-0.267, +0.078] | 0.477 | 0.485 | 3/9/4 | -0.062 | +0.000 |
| ltr24__logreg__notype-nobge__mined | vs convex05+bge@20 (n=16, ref 0.468 → 0.255) | -0.213 [-0.450, +0.005] | 0.093 | 0.089 | 3/10/3 | -0.250 | -0.062 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.255) | **-0.141** [-0.290, -0.043] | 0.040 | 0.030 | 2/10/4 | -0.125 | -0.062 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap (n=16, ref 0.371 → 0.255) | **-0.116** [-0.257, -0.046] | 0.037 | 0.002 | 1/10/5 | -0.125 | +0.000 |
| ltr24__logreg__notype-nobge__mined | vs exp22 gate T25 (n=16, ref 0.613 → 0.255) | **-0.358** [-0.548, -0.205] | 0.001 | 0.001 | 0/11/5 | -0.312 | -0.375 |
| ltr24__lgbm-tiny__small__mined | vs bar_val (n=16, ref 0.570 → 0.425) | -0.146 [-0.363, +0.052] | 0.210 | 0.219 | 3/7/6 | -0.188 | -0.188 |
| ltr24__lgbm-tiny__small__mined | vs bar_full (n=16, ref 0.570 → 0.425) | -0.146 [-0.363, +0.052] | 0.210 | 0.219 | 3/7/6 | -0.188 | -0.188 |
| ltr24__lgbm-tiny__small__mined | vs exp14 (n=16, ref 0.519 → 0.425) | -0.094 [-0.302, +0.088] | 0.378 | 0.377 | 5/7/4 | -0.125 | -0.188 |
| ltr24__lgbm-tiny__small__mined | vs exp14_cheap (n=16, ref 0.411 → 0.425) | +0.013 [-0.122, +0.154] | 0.855 | 0.874 | 5/6/5 | -0.062 | -0.062 |
| ltr24__lgbm-tiny__small__mined | vs lex13 (n=16, ref 0.326 → 0.425) | +0.099 [-0.056, +0.271] | 0.272 | 0.279 | 8/3/5 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs bm25_01 (n=16, ref 0.290 → 0.425) | +0.135 [-0.003, +0.274] | 0.087 | 0.089 | 10/2/4 | +0.125 | +0.062 |
| ltr24__lgbm-tiny__small__mined | vs convex05 (n=16, ref 0.319 → 0.425) | +0.106 [-0.058, +0.254] | 0.215 | 0.218 | 9/5/2 | +0.062 | +0.062 |
| ltr24__lgbm-tiny__small__mined | vs convex05+bge@20 (n=16, ref 0.468 → 0.425) | -0.043 [-0.215, +0.112] | 0.628 | 0.628 | 6/7/3 | -0.125 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.425) | +0.028 [-0.073, +0.127] | 0.597 | 0.613 | 6/4/6 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap (n=16, ref 0.371 → 0.425) | +0.054 [+0.018, +0.129] | 0.059 | 0.055 | 6/2/8 | +0.000 | +0.062 |
| ltr24__lgbm-tiny__small__mined | vs exp22 gate T25 (n=16, ref 0.613 → 0.425) | **-0.189** [-0.351, -0.038] | 0.039 | 0.040 | 2/9/5 | -0.188 | -0.312 |
| ltr24__logreg__small__mined | vs bar_val (n=16, ref 0.570 → 0.447) | -0.123 [-0.376, +0.089] | 0.334 | 0.337 | 5/6/5 | -0.062 | -0.250 |
| ltr24__logreg__small__mined | vs bar_full (n=16, ref 0.570 → 0.447) | -0.123 [-0.376, +0.089] | 0.334 | 0.337 | 5/6/5 | -0.062 | -0.250 |
| ltr24__logreg__small__mined | vs exp14 (n=16, ref 0.519 → 0.447) | -0.071 [-0.337, +0.189] | 0.614 | 0.614 | 6/7/3 | +0.000 | -0.250 |
| ltr24__logreg__small__mined | vs exp14_cheap (n=16, ref 0.411 → 0.447) | +0.036 [-0.151, +0.282] | 0.756 | 0.769 | 5/7/4 | +0.062 | -0.125 |
| ltr24__logreg__small__mined | vs lex13 (n=16, ref 0.326 → 0.447) | +0.121 [-0.018, +0.326] | 0.190 | 0.148 | 8/2/6 | +0.125 | -0.062 |
| ltr24__logreg__small__mined | vs bm25_01 (n=16, ref 0.290 → 0.447) | +0.157 [+0.007, +0.338] | 0.092 | 0.098 | 10/3/3 | +0.250 | +0.000 |
| ltr24__logreg__small__mined | vs convex05 (n=16, ref 0.319 → 0.447) | +0.128 [-0.086, +0.346] | 0.280 | 0.280 | 7/6/3 | +0.188 | +0.000 |
| ltr24__logreg__small__mined | vs convex05+bge@20 (n=16, ref 0.468 → 0.447) | -0.021 [-0.220, +0.176] | 0.844 | 0.820 | 4/7/5 | +0.000 | -0.062 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.447) | +0.051 [-0.079, +0.240] | 0.545 | 0.545 | 6/6/4 | +0.125 | -0.062 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap (n=16, ref 0.371 → 0.447) | +0.076 [+0.005, +0.228] | 0.151 | 0.160 | 7/3/6 | +0.125 | +0.000 |
| ltr24__logreg__small__mined | vs exp22 gate T25 (n=16, ref 0.613 → 0.447) | -0.166 [-0.361, +0.010] | 0.113 | 0.123 | 2/9/5 | -0.062 | -0.375 |
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
| ltr24__logreg__notype__pooled | vs bar_val (n=16, ref 0.570 → 0.423) | -0.147 [-0.366, +0.052] | 0.208 | 0.219 | 3/6/7 | -0.250 | -0.062 |
| ltr24__logreg__notype__pooled | vs bar_full (n=16, ref 0.570 → 0.423) | -0.147 [-0.366, +0.052] | 0.208 | 0.219 | 3/6/7 | -0.250 | -0.062 |
| ltr24__logreg__notype__pooled | vs exp14 (n=16, ref 0.519 → 0.423) | -0.096 [-0.261, +0.026] | 0.215 | 0.219 | 3/5/8 | -0.188 | -0.062 |
| ltr24__logreg__notype__pooled | vs exp14_cheap (n=16, ref 0.411 → 0.423) | +0.012 [-0.151, +0.157] | 0.887 | 0.883 | 6/5/5 | -0.125 | +0.062 |
| ltr24__logreg__notype__pooled | vs lex13 (n=16, ref 0.326 → 0.423) | +0.097 [-0.110, +0.318] | 0.407 | 0.410 | 9/4/3 | -0.062 | +0.125 |
| ltr24__logreg__notype__pooled | vs bm25_01 (n=16, ref 0.290 → 0.423) | +0.133 [-0.038, +0.320] | 0.183 | 0.178 | 8/4/4 | +0.062 | +0.188 |
| ltr24__logreg__notype__pooled | vs convex05 (n=16, ref 0.319 → 0.423) | +0.104 [-0.058, +0.248] | 0.216 | 0.214 | 9/4/3 | +0.000 | +0.188 |
| ltr24__logreg__notype__pooled | vs convex05+bge@20 (n=16, ref 0.468 → 0.423) | -0.045 [-0.216, +0.090] | 0.585 | 0.592 | 5/5/6 | -0.188 | +0.125 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.423) | +0.027 [-0.137, +0.181] | 0.753 | 0.746 | 6/6/4 | -0.062 | +0.125 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap (n=16, ref 0.371 → 0.423) | +0.052 [-0.085, +0.225] | 0.524 | 0.551 | 6/3/7 | -0.062 | +0.188 |
| ltr24__logreg__notype__pooled | vs exp22 gate T25 (n=16, ref 0.613 → 0.423) | -0.190 [-0.357, -0.012] | 0.054 | 0.057 | 3/9/4 | -0.250 | -0.188 |
| ltr24__logreg__notype__pooled | vs exp24 mined-only (same features) (n=16, ref 0.415 → 0.423) | +0.008 [-0.140, +0.159] | 0.920 | 0.943 | 6/4/6 | -0.125 | +0.125 |
| ltr24__lgbm-tiny__withtype__pooled | vs bar_val (n=16, ref 0.570 → 0.490) | -0.081 [-0.286, +0.151] | 0.495 | 0.519 | 3/6/7 | -0.125 | +0.062 |
| ltr24__lgbm-tiny__withtype__pooled | vs bar_full (n=16, ref 0.570 → 0.490) | -0.081 [-0.286, +0.151] | 0.495 | 0.519 | 3/6/7 | -0.125 | +0.062 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp14 (n=16, ref 0.519 → 0.490) | -0.029 [-0.152, +0.008] | 0.386 | 0.625 | 3/3/10 | -0.062 | +0.062 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp14_cheap (n=16, ref 0.411 → 0.490) | +0.078 [-0.066, +0.253] | 0.364 | 0.398 | 8/3/5 | +0.000 | +0.188 |
| ltr24__lgbm-tiny__withtype__pooled | vs lex13 (n=16, ref 0.326 → 0.490) | +0.164 [-0.087, +0.402] | 0.229 | 0.230 | 9/3/4 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled | vs bm25_01 (n=16, ref 0.290 → 0.490) | +0.199 [+0.016, +0.415] | 0.078 | 0.079 | 9/3/4 | +0.188 | +0.312 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05 (n=16, ref 0.319 → 0.490) | +0.171 [+0.027, +0.357] | 0.066 | 0.060 | 10/2/4 | +0.125 | +0.312 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05+bge@20 (n=16, ref 0.468 → 0.490) | +0.022 [-0.145, +0.222] | 0.821 | 0.836 | 4/4/8 | -0.062 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.490) | +0.093 [-0.068, +0.292] | 0.331 | 0.346 | 7/4/5 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap (n=16, ref 0.371 → 0.490) | +0.119 [-0.066, +0.336] | 0.274 | 0.280 | 8/3/5 | +0.062 | +0.312 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp22 gate T25 (n=16, ref 0.613 → 0.490) | -0.124 [-0.279, +0.102] | 0.226 | 0.228 | 2/10/4 | -0.125 | -0.062 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp24 mined-only (same features) (n=16, ref 0.433 → 0.490) | +0.057 [-0.167, +0.270] | 0.623 | 0.625 | 7/4/5 | +0.000 | +0.250 |
| ltr24__logreg__withtype__pooled | vs bar_val (n=16, ref 0.570 → 0.425) | -0.145 [-0.375, +0.060] | 0.230 | 0.240 | 4/6/6 | -0.250 | -0.062 |
| ltr24__logreg__withtype__pooled | vs bar_full (n=16, ref 0.570 → 0.425) | -0.145 [-0.375, +0.060] | 0.230 | 0.240 | 4/6/6 | -0.250 | -0.062 |
| ltr24__logreg__withtype__pooled | vs exp14 (n=16, ref 0.519 → 0.425) | -0.094 [-0.260, +0.036] | 0.238 | 0.242 | 3/6/7 | -0.188 | -0.062 |
| ltr24__logreg__withtype__pooled | vs exp14_cheap (n=16, ref 0.411 → 0.425) | +0.014 [-0.150, +0.159] | 0.866 | 0.865 | 6/5/5 | -0.125 | +0.062 |
| ltr24__logreg__withtype__pooled | vs lex13 (n=16, ref 0.326 → 0.425) | +0.099 [-0.106, +0.321] | 0.396 | 0.394 | 10/4/2 | -0.062 | +0.125 |
| ltr24__logreg__withtype__pooled | vs bm25_01 (n=16, ref 0.290 → 0.425) | +0.135 [-0.036, +0.318] | 0.170 | 0.166 | 8/3/5 | +0.062 | +0.188 |
| ltr24__logreg__withtype__pooled | vs convex05 (n=16, ref 0.319 → 0.425) | +0.106 [-0.059, +0.250] | 0.211 | 0.209 | 9/4/3 | +0.000 | +0.188 |
| ltr24__logreg__withtype__pooled | vs convex05+bge@20 (n=16, ref 0.468 → 0.425) | -0.043 [-0.222, +0.087] | 0.603 | 0.615 | 5/5/6 | -0.188 | +0.125 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.425) | +0.029 [-0.135, +0.183] | 0.734 | 0.736 | 6/6/4 | -0.062 | +0.125 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap (n=16, ref 0.371 → 0.425) | +0.054 [-0.088, +0.231] | 0.517 | 0.533 | 6/4/6 | -0.062 | +0.188 |
| ltr24__logreg__withtype__pooled | vs exp22 gate T25 (n=16, ref 0.613 → 0.425) | -0.188 [-0.369, -0.010] | 0.067 | 0.070 | 3/8/5 | -0.250 | -0.188 |
| ltr24__logreg__withtype__pooled | vs exp24 mined-only (same features) (n=16, ref 0.416 → 0.425) | +0.009 [-0.145, +0.140] | 0.906 | 0.906 | 8/3/5 | -0.125 | +0.188 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bar_val (n=16, ref 0.570 → 0.498) | -0.072 [-0.268, +0.161] | 0.529 | 0.559 | 3/6/7 | -0.125 | +0.062 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bar_full (n=16, ref 0.570 → 0.498) | -0.072 [-0.268, +0.161] | 0.529 | 0.559 | 3/6/7 | -0.125 | +0.062 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp14 (n=16, ref 0.519 → 0.498) | -0.021 [-0.131, +0.024] | 0.568 | 0.766 | 4/3/9 | -0.062 | +0.062 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp14_cheap (n=16, ref 0.411 → 0.498) | +0.087 [-0.064, +0.264] | 0.331 | 0.344 | 7/3/6 | +0.000 | +0.188 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs lex13 (n=16, ref 0.326 → 0.498) | +0.172 [-0.080, +0.407] | 0.207 | 0.206 | 9/3/4 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bm25_01 (n=16, ref 0.290 → 0.498) | +0.208 [+0.023, +0.421] | 0.067 | 0.070 | 9/3/4 | +0.188 | +0.312 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05 (n=16, ref 0.319 → 0.498) | +0.179 [+0.033, +0.361] | 0.056 | 0.049 | 10/2/4 | +0.125 | +0.312 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05+bge@20 (n=16, ref 0.468 → 0.498) | +0.030 [-0.117, +0.230] | 0.740 | 0.758 | 4/4/8 | -0.062 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.498) | +0.102 [-0.060, +0.294] | 0.289 | 0.295 | 8/4/4 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap (n=16, ref 0.371 → 0.498) | +0.127 [-0.056, +0.341] | 0.239 | 0.248 | 9/3/4 | +0.062 | +0.312 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp22 gate T25 (n=16, ref 0.613 → 0.498) | -0.115 [-0.261, +0.110] | 0.242 | 0.245 | 2/10/4 | -0.125 | -0.062 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp24 mined-only (same features) (n=16, ref 0.448 → 0.498) | +0.050 [-0.168, +0.257] | 0.658 | 0.657 | 7/4/5 | +0.000 | +0.250 |
| ltr24__logreg__notype-nogate__pooled | vs bar_val (n=16, ref 0.570 → 0.413) | -0.157 [-0.385, +0.048] | 0.194 | 0.203 | 3/6/7 | -0.250 | -0.062 |
| ltr24__logreg__notype-nogate__pooled | vs bar_full (n=16, ref 0.570 → 0.413) | -0.157 [-0.385, +0.048] | 0.194 | 0.203 | 3/6/7 | -0.250 | -0.062 |
| ltr24__logreg__notype-nogate__pooled | vs exp14 (n=16, ref 0.519 → 0.413) | -0.106 [-0.287, +0.052] | 0.255 | 0.259 | 4/7/5 | -0.188 | -0.062 |
| ltr24__logreg__notype-nogate__pooled | vs exp14_cheap (n=16, ref 0.411 → 0.413) | +0.002 [-0.152, +0.147] | 0.983 | 0.981 | 6/6/4 | -0.125 | +0.062 |
| ltr24__logreg__notype-nogate__pooled | vs lex13 (n=16, ref 0.326 → 0.413) | +0.087 [-0.089, +0.270] | 0.377 | 0.376 | 9/3/4 | -0.062 | +0.125 |
| ltr24__logreg__notype-nogate__pooled | vs bm25_01 (n=16, ref 0.290 → 0.413) | +0.123 [-0.012, +0.263] | 0.111 | 0.118 | 8/3/5 | +0.062 | +0.188 |
| ltr24__logreg__notype-nogate__pooled | vs convex05 (n=16, ref 0.319 → 0.413) | +0.094 [-0.065, +0.244] | 0.261 | 0.259 | 9/4/3 | +0.000 | +0.188 |
| ltr24__logreg__notype-nogate__pooled | vs convex05+bge@20 (n=16, ref 0.468 → 0.413) | -0.055 [-0.247, +0.113] | 0.571 | 0.575 | 6/6/4 | -0.188 | +0.125 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.413) | +0.017 [-0.119, +0.147] | 0.814 | 0.816 | 5/6/5 | -0.062 | +0.125 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap (n=16, ref 0.371 → 0.413) | +0.042 [-0.063, +0.142] | 0.441 | 0.488 | 6/3/7 | -0.062 | +0.188 |
| ltr24__logreg__notype-nogate__pooled | vs exp22 gate T25 (n=16, ref 0.613 → 0.413) | -0.200 [-0.380, -0.020] | 0.053 | 0.055 | 3/9/4 | -0.250 | -0.188 |
| ltr24__logreg__notype-nogate__pooled | vs exp24 mined-only (same features) (n=16, ref 0.465 → 0.413) | -0.052 [-0.222, +0.063] | 0.489 | 0.527 | 5/4/7 | -0.188 | +0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bar_val (n=16, ref 0.570 → 0.305) | **-0.265** [-0.461, -0.063] | 0.025 | 0.025 | 2/10/4 | -0.312 | -0.250 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bar_full (n=16, ref 0.570 → 0.305) | **-0.265** [-0.461, -0.063] | 0.025 | 0.025 | 2/10/4 | -0.312 | -0.250 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp14 (n=16, ref 0.519 → 0.305) | -0.214 [-0.431, -0.039] | 0.053 | 0.060 | 2/8/6 | -0.250 | -0.250 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp14_cheap (n=16, ref 0.411 → 0.305) | -0.106 [-0.259, -0.002] | 0.130 | 0.139 | 2/8/6 | -0.188 | -0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs lex13 (n=16, ref 0.326 → 0.305) | -0.021 [-0.193, +0.124] | 0.807 | 0.804 | 8/5/3 | -0.125 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bm25_01 (n=16, ref 0.290 → 0.305) | +0.015 [-0.089, +0.143] | 0.809 | 0.805 | 8/3/5 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05 (n=16, ref 0.319 → 0.305) | -0.014 [-0.170, +0.114] | 0.856 | 0.925 | 7/4/5 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05+bge@20 (n=16, ref 0.468 → 0.305) | -0.163 [-0.354, -0.007] | 0.088 | 0.100 | 6/7/3 | -0.250 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.305) | -0.091 [-0.203, -0.025] | 0.063 | 0.102 | 3/6/7 | -0.125 | -0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap (n=16, ref 0.371 → 0.305) | -0.066 [-0.186, -0.002] | 0.175 | 0.242 | 5/4/7 | -0.125 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp22 gate T25 (n=16, ref 0.613 → 0.305) | **-0.308** [-0.462, -0.136] | 0.003 | 0.004 | 1/13/2 | -0.312 | -0.375 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp24 mined-only (same features) (n=16, ref 0.372 → 0.305) | -0.067 [-0.186, -0.004] | 0.161 | 0.242 | 5/4/7 | -0.125 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs bar_val (n=16, ref 0.570 → 0.276) | **-0.295** [-0.512, -0.127] | 0.011 | 0.014 | 2/8/6 | -0.375 | -0.188 |
| ltr24__logreg__notype-nobge__pooled | vs bar_full (n=16, ref 0.570 → 0.276) | **-0.295** [-0.512, -0.127] | 0.011 | 0.014 | 2/8/6 | -0.375 | -0.188 |
| ltr24__logreg__notype-nobge__pooled | vs exp14 (n=16, ref 0.519 → 0.276) | **-0.243** [-0.460, -0.042] | 0.044 | 0.043 | 3/10/3 | -0.312 | -0.188 |
| ltr24__logreg__notype-nobge__pooled | vs exp14_cheap (n=16, ref 0.411 → 0.276) | -0.136 [-0.295, +0.002] | 0.103 | 0.101 | 3/8/5 | -0.250 | -0.062 |
| ltr24__logreg__notype-nobge__pooled | vs lex13 (n=16, ref 0.326 → 0.276) | -0.050 [-0.234, +0.069] | 0.524 | 0.543 | 7/3/6 | -0.188 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs bm25_01 (n=16, ref 0.290 → 0.276) | -0.015 [-0.197, +0.066] | 0.816 | 0.881 | 7/3/6 | -0.062 | +0.062 |
| ltr24__logreg__notype-nobge__pooled | vs convex05 (n=16, ref 0.319 → 0.276) | -0.043 [-0.222, +0.056] | 0.537 | 0.599 | 7/5/4 | -0.125 | +0.062 |
| ltr24__logreg__notype-nobge__pooled | vs convex05+bge@20 (n=16, ref 0.468 → 0.276) | -0.192 [-0.386, -0.017] | 0.068 | 0.070 | 5/9/2 | -0.312 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.276) | -0.121 [-0.285, -0.020] | 0.092 | 0.102 | 3/8/5 | -0.188 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap (n=16, ref 0.371 → 0.276) | -0.095 [-0.216, +0.009] | 0.137 | 0.132 | 5/7/4 | -0.188 | +0.062 |
| ltr24__logreg__notype-nobge__pooled | vs exp22 gate T25 (n=16, ref 0.613 → 0.276) | **-0.338** [-0.508, -0.202] | 0.001 | 0.001 | 0/12/4 | -0.375 | -0.312 |
| ltr24__logreg__notype-nobge__pooled | vs exp24 mined-only (same features) (n=16, ref 0.255 → 0.276) | +0.021 [-0.082, +0.090] | 0.641 | 0.613 | 8/3/5 | -0.062 | +0.062 |
| ltr24__lgbm-tiny__small__pooled | vs bar_val (n=16, ref 0.570 → 0.530) | -0.040 [-0.248, +0.199] | 0.741 | 0.760 | 5/6/5 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs bar_full (n=16, ref 0.570 → 0.530) | -0.040 [-0.248, +0.199] | 0.741 | 0.760 | 5/6/5 | -0.062 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs exp14 (n=16, ref 0.519 → 0.530) | +0.012 [-0.091, +0.107] | 0.827 | 0.844 | 5/2/9 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | vs exp14_cheap (n=16, ref 0.411 → 0.530) | +0.119 [-0.014, +0.294] | 0.152 | 0.160 | 8/2/6 | +0.062 | +0.125 |
| ltr24__lgbm-tiny__small__pooled | vs lex13 (n=16, ref 0.326 → 0.530) | +0.205 [-0.042, +0.426] | 0.119 | 0.118 | 10/2/4 | +0.125 | +0.188 |
| ltr24__lgbm-tiny__small__pooled | vs bm25_01 (n=16, ref 0.290 → 0.530) | **+0.240** [+0.050, +0.445] | 0.037 | 0.036 | 10/2/4 | +0.250 | +0.250 |
| ltr24__lgbm-tiny__small__pooled | vs convex05 (n=16, ref 0.319 → 0.530) | **+0.212** [+0.056, +0.391] | 0.029 | 0.027 | 11/2/3 | +0.188 | +0.250 |
| ltr24__lgbm-tiny__small__pooled | vs convex05+bge@20 (n=16, ref 0.468 → 0.530) | +0.063 [-0.083, +0.266] | 0.491 | 0.519 | 6/4/6 | +0.000 | +0.188 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.530) | +0.134 [-0.002, +0.321] | 0.126 | 0.119 | 7/3/6 | +0.125 | +0.188 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap (n=16, ref 0.371 → 0.530) | +0.160 [-0.006, +0.368] | 0.118 | 0.123 | 9/2/5 | +0.125 | +0.250 |
| ltr24__lgbm-tiny__small__pooled | vs exp22 gate T25 (n=16, ref 0.613 → 0.530) | -0.083 [-0.229, +0.139] | 0.390 | 0.393 | 2/8/6 | -0.062 | -0.125 |
| ltr24__lgbm-tiny__small__pooled | vs exp24 mined-only (same features) (n=16, ref 0.425 → 0.530) | +0.106 [-0.041, +0.263] | 0.200 | 0.199 | 8/2/6 | +0.125 | +0.188 |
| ltr24__logreg__small__pooled | vs bar_val (n=16, ref 0.570 → 0.506) | -0.065 [-0.259, +0.155] | 0.568 | 0.594 | 5/5/6 | -0.125 | -0.062 |
| ltr24__logreg__small__pooled | vs bar_full (n=16, ref 0.570 → 0.506) | -0.065 [-0.259, +0.155] | 0.568 | 0.594 | 5/5/6 | -0.125 | -0.062 |
| ltr24__logreg__small__pooled | vs exp14 (n=16, ref 0.519 → 0.506) | -0.013 [-0.140, +0.110] | 0.846 | 0.865 | 6/4/6 | -0.062 | -0.062 |
| ltr24__logreg__small__pooled | vs exp14_cheap (n=16, ref 0.411 → 0.506) | +0.094 [-0.067, +0.282] | 0.317 | 0.327 | 8/4/4 | +0.000 | +0.062 |
| ltr24__logreg__small__pooled | vs lex13 (n=16, ref 0.326 → 0.506) | +0.180 [-0.006, +0.407] | 0.119 | 0.118 | 10/2/4 | +0.062 | +0.125 |
| ltr24__logreg__small__pooled | vs bm25_01 (n=16, ref 0.290 → 0.506) | **+0.215** [+0.053, +0.421] | 0.043 | 0.040 | 11/2/3 | +0.188 | +0.188 |
| ltr24__logreg__small__pooled | vs convex05 (n=16, ref 0.319 → 0.506) | **+0.187** [+0.042, +0.365] | 0.042 | 0.036 | 10/3/3 | +0.125 | +0.188 |
| ltr24__logreg__small__pooled | vs convex05+bge@20 (n=16, ref 0.468 → 0.506) | +0.038 [-0.143, +0.246] | 0.714 | 0.723 | 6/5/5 | -0.062 | +0.125 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.506) | +0.109 [-0.052, +0.305] | 0.255 | 0.264 | 9/4/3 | +0.062 | +0.125 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap (n=16, ref 0.371 → 0.506) | +0.135 [-0.035, +0.349] | 0.197 | 0.187 | 9/3/4 | +0.062 | +0.188 |
| ltr24__logreg__small__pooled | vs exp22 gate T25 (n=16, ref 0.613 → 0.506) | -0.108 [-0.231, +0.106] | 0.218 | 0.231 | 1/8/7 | -0.125 | -0.188 |
| ltr24__logreg__small__pooled | vs exp24 mined-only (same features) (n=16, ref 0.447 → 0.506) | +0.059 [-0.143, +0.291] | 0.611 | 0.619 | 8/4/4 | -0.062 | +0.188 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bar_val (n=16, ref 0.570 → 0.542) | -0.029 [-0.219, +0.199] | 0.797 | 0.812 | 4/5/7 | -0.062 | +0.062 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bar_full (n=16, ref 0.570 → 0.542) | -0.029 [-0.219, +0.199] | 0.797 | 0.812 | 4/5/7 | -0.062 | +0.062 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp14 (n=16, ref 0.519 → 0.542) | +0.023 [-0.066, +0.156] | 0.689 | 0.688 | 4/3/9 | +0.000 | +0.062 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp14_cheap (n=16, ref 0.411 → 0.542) | +0.130 [-0.035, +0.343] | 0.211 | 0.221 | 8/3/5 | +0.062 | +0.188 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs lex13 (n=16, ref 0.326 → 0.542) | +0.216 [-0.053, +0.460] | 0.137 | 0.138 | 10/3/3 | +0.125 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bm25_01 (n=16, ref 0.290 → 0.542) | **+0.252** [+0.054, +0.469] | 0.039 | 0.040 | 9/2/5 | +0.250 | +0.312 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05 (n=16, ref 0.319 → 0.542) | **+0.223** [+0.059, +0.417] | 0.033 | 0.032 | 10/2/4 | +0.188 | +0.312 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05+bge@20 (n=16, ref 0.468 → 0.542) | +0.074 [-0.038, +0.273] | 0.354 | 0.422 | 4/3/9 | +0.000 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.542) | +0.145 [-0.030, +0.341] | 0.157 | 0.158 | 8/3/5 | +0.125 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap (n=16, ref 0.371 → 0.542) | +0.171 [-0.027, +0.388] | 0.140 | 0.141 | 9/3/4 | +0.125 | +0.312 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp22 gate T25 (n=16, ref 0.613 → 0.542) | -0.071 [-0.213, +0.147] | 0.444 | 0.457 | 2/8/6 | -0.062 | -0.062 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp24 mined-only (same features) (n=16, ref 0.442 → 0.542) | +0.100 [-0.133, +0.311] | 0.403 | 0.399 | 8/3/5 | +0.062 | +0.312 |
| ltr24__logreg__notype__pooled-scored | vs bar_val (n=16, ref 0.570 → 0.481) | -0.089 [-0.303, +0.154] | 0.472 | 0.519 | 3/6/7 | -0.188 | +0.000 |
| ltr24__logreg__notype__pooled-scored | vs bar_full (n=16, ref 0.570 → 0.481) | -0.089 [-0.303, +0.154] | 0.472 | 0.519 | 3/6/7 | -0.188 | +0.000 |
| ltr24__logreg__notype__pooled-scored | vs exp14 (n=16, ref 0.519 → 0.481) | -0.038 [-0.182, +0.065] | 0.559 | 0.570 | 4/4/8 | -0.125 | +0.000 |
| ltr24__logreg__notype__pooled-scored | vs exp14_cheap (n=16, ref 0.411 → 0.481) | +0.070 [-0.107, +0.262] | 0.485 | 0.481 | 7/5/4 | -0.062 | +0.125 |
| ltr24__logreg__notype__pooled-scored | vs lex13 (n=16, ref 0.326 → 0.481) | +0.155 [-0.076, +0.398] | 0.238 | 0.236 | 9/4/3 | +0.000 | +0.188 |
| ltr24__logreg__notype__pooled-scored | vs bm25_01 (n=16, ref 0.290 → 0.481) | +0.191 [-0.001, +0.409] | 0.099 | 0.108 | 8/4/4 | +0.125 | +0.250 |
| ltr24__logreg__notype__pooled-scored | vs convex05 (n=16, ref 0.319 → 0.481) | +0.162 [-0.015, +0.351] | 0.113 | 0.114 | 9/4/3 | +0.062 | +0.250 |
| ltr24__logreg__notype__pooled-scored | vs convex05+bge@20 (n=16, ref 0.468 → 0.481) | +0.013 [-0.156, +0.217] | 0.894 | 0.896 | 5/5/6 | -0.125 | +0.188 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.481) | +0.085 [-0.096, +0.281] | 0.407 | 0.419 | 8/5/3 | +0.000 | +0.188 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap (n=16, ref 0.371 → 0.481) | +0.110 [-0.051, +0.322] | 0.270 | 0.283 | 7/3/6 | +0.000 | +0.250 |
| ltr24__logreg__notype__pooled-scored | vs exp22 gate T25 (n=16, ref 0.613 → 0.481) | -0.132 [-0.297, +0.096] | 0.209 | 0.205 | 3/9/4 | -0.188 | -0.125 |
| ltr24__logreg__notype__pooled-scored | vs exp24 mined-only (same features) (n=16, ref 0.415 → 0.481) | +0.066 [-0.099, +0.271] | 0.506 | 0.511 | 8/3/5 | -0.062 | +0.188 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bar_val (n=16, ref 0.570 → 0.510) | -0.060 [-0.255, +0.164] | 0.595 | 0.608 | 5/6/5 | -0.125 | +0.062 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bar_full (n=16, ref 0.570 → 0.510) | -0.060 [-0.255, +0.164] | 0.595 | 0.608 | 5/6/5 | -0.125 | +0.062 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp14 (n=16, ref 0.519 → 0.510) | -0.008 [-0.130, +0.099] | 0.891 | 0.883 | 5/4/7 | -0.062 | +0.062 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp14_cheap (n=16, ref 0.411 → 0.510) | +0.099 [-0.054, +0.281] | 0.271 | 0.276 | 8/3/5 | +0.000 | +0.188 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs lex13 (n=16, ref 0.326 → 0.510) | +0.185 [-0.048, +0.402] | 0.143 | 0.145 | 10/2/4 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bm25_01 (n=16, ref 0.290 → 0.510) | **+0.220** [+0.042, +0.423] | 0.044 | 0.044 | 10/2/4 | +0.188 | +0.312 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05 (n=16, ref 0.319 → 0.510) | **+0.192** [+0.048, +0.364] | 0.034 | 0.029 | 11/2/3 | +0.125 | +0.312 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05+bge@20 (n=16, ref 0.468 → 0.510) | +0.043 [-0.121, +0.250] | 0.665 | 0.691 | 5/5/6 | -0.062 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.510) | +0.114 [-0.047, +0.306] | 0.231 | 0.236 | 8/3/5 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap (n=16, ref 0.371 → 0.510) | +0.140 [-0.047, +0.356] | 0.201 | 0.205 | 9/3/4 | +0.062 | +0.312 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp22 gate T25 (n=16, ref 0.613 → 0.510) | -0.103 [-0.225, +0.113] | 0.234 | 0.246 | 1/8/7 | -0.125 | -0.062 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp24 mined-only (same features) (n=16, ref 0.433 → 0.510) | +0.078 [-0.148, +0.288] | 0.501 | 0.502 | 8/3/5 | +0.000 | +0.250 |
| ltr24__logreg__withtype__pooled-scored | vs bar_val (n=16, ref 0.570 → 0.454) | -0.116 [-0.348, +0.139] | 0.379 | 0.391 | 4/7/5 | -0.188 | +0.000 |
| ltr24__logreg__withtype__pooled-scored | vs bar_full (n=16, ref 0.570 → 0.454) | -0.116 [-0.348, +0.139] | 0.379 | 0.391 | 4/7/5 | -0.188 | +0.000 |
| ltr24__logreg__withtype__pooled-scored | vs exp14 (n=16, ref 0.519 → 0.454) | -0.065 [-0.209, +0.021] | 0.277 | 0.320 | 3/5/8 | -0.125 | +0.000 |
| ltr24__logreg__withtype__pooled-scored | vs exp14_cheap (n=16, ref 0.411 → 0.454) | +0.043 [-0.119, +0.231] | 0.647 | 0.647 | 7/4/5 | -0.062 | +0.125 |
| ltr24__logreg__withtype__pooled-scored | vs lex13 (n=16, ref 0.326 → 0.454) | +0.128 [-0.127, +0.377] | 0.354 | 0.354 | 10/4/2 | +0.000 | +0.188 |
| ltr24__logreg__withtype__pooled-scored | vs bm25_01 (n=16, ref 0.290 → 0.454) | +0.164 [-0.031, +0.391] | 0.160 | 0.160 | 8/4/4 | +0.125 | +0.250 |
| ltr24__logreg__withtype__pooled-scored | vs convex05 (n=16, ref 0.319 → 0.454) | +0.135 [-0.034, +0.327] | 0.175 | 0.180 | 9/4/3 | +0.062 | +0.250 |
| ltr24__logreg__withtype__pooled-scored | vs convex05+bge@20 (n=16, ref 0.468 → 0.454) | -0.014 [-0.193, +0.188] | 0.890 | 0.891 | 4/6/6 | -0.125 | +0.188 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.454) | +0.058 [-0.116, +0.267] | 0.568 | 0.572 | 6/6/4 | +0.000 | +0.188 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap (n=16, ref 0.371 → 0.454) | +0.083 [-0.085, +0.308] | 0.425 | 0.431 | 6/5/5 | +0.000 | +0.250 |
| ltr24__logreg__withtype__pooled-scored | vs exp22 gate T25 (n=16, ref 0.613 → 0.454) | -0.159 [-0.338, +0.078] | 0.159 | 0.163 | 3/9/4 | -0.188 | -0.125 |
| ltr24__logreg__withtype__pooled-scored | vs exp24 mined-only (same features) (n=16, ref 0.416 → 0.454) | +0.038 [-0.160, +0.234] | 0.719 | 0.726 | 8/3/5 | -0.062 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bar_val (n=16, ref 0.570 → 0.576) | +0.005 [-0.180, +0.219] | 0.959 | 0.984 | 4/3/9 | +0.000 | +0.062 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bar_full (n=16, ref 0.570 → 0.576) | +0.005 [-0.180, +0.219] | 0.959 | 0.984 | 4/3/9 | +0.000 | +0.062 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp14 (n=16, ref 0.519 → 0.576) | +0.057 [-0.050, +0.194] | 0.381 | 0.406 | 5/2/9 | +0.062 | +0.062 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp14_cheap (n=16, ref 0.411 → 0.576) | +0.165 [+0.019, +0.367] | 0.091 | 0.097 | 9/2/5 | +0.125 | +0.188 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs lex13 (n=16, ref 0.326 → 0.576) | +0.250 [-0.009, +0.478] | 0.074 | 0.075 | 11/2/3 | +0.188 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bm25_01 (n=16, ref 0.290 → 0.576) | **+0.286** [+0.112, +0.492] | 0.013 | 0.011 | 10/1/5 | +0.312 | +0.312 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05 (n=16, ref 0.319 → 0.576) | **+0.257** [+0.123, +0.447] | 0.008 | 0.002 | 10/1/5 | +0.250 | +0.312 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05+bge@20 (n=16, ref 0.468 → 0.576) | +0.108 [-0.020, +0.302] | 0.209 | 0.281 | 5/4/7 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.576) | +0.179 [+0.029, +0.362] | 0.061 | 0.065 | 9/2/5 | +0.188 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=16, ref 0.371 → 0.576) | +0.205 [+0.022, +0.408] | 0.061 | 0.062 | 10/2/4 | +0.188 | +0.312 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp22 gate T25 (n=16, ref 0.613 → 0.576) | -0.037 [-0.169, +0.171] | 0.669 | 0.695 | 2/7/7 | +0.000 | -0.062 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=16, ref 0.448 → 0.576) | +0.128 [-0.097, +0.314] | 0.254 | 0.250 | 9/2/5 | +0.125 | +0.250 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bar_val (n=16, ref 0.570 → 0.425) | -0.145 [-0.363, +0.116] | 0.270 | 0.274 | 3/8/5 | -0.250 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bar_full (n=16, ref 0.570 → 0.425) | -0.145 [-0.363, +0.116] | 0.270 | 0.274 | 3/8/5 | -0.250 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp14 (n=16, ref 0.519 → 0.425) | -0.093 [-0.243, -0.000] | 0.147 | 0.180 | 3/5/8 | -0.188 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp14_cheap (n=16, ref 0.411 → 0.425) | +0.014 [-0.161, +0.209] | 0.887 | 0.882 | 8/5/3 | -0.125 | +0.125 |
| ltr24__logreg__notype-nogate__pooled-scored | vs lex13 (n=16, ref 0.326 → 0.425) | +0.100 [-0.137, +0.329] | 0.437 | 0.437 | 9/4/3 | -0.062 | +0.188 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bm25_01 (n=16, ref 0.290 → 0.425) | +0.135 [-0.050, +0.339] | 0.204 | 0.205 | 8/5/3 | +0.062 | +0.250 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05 (n=16, ref 0.319 → 0.425) | +0.107 [-0.082, +0.313] | 0.315 | 0.315 | 9/5/2 | +0.000 | +0.250 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05+bge@20 (n=16, ref 0.468 → 0.425) | -0.042 [-0.224, +0.174] | 0.688 | 0.691 | 4/6/6 | -0.188 | +0.188 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.425) | +0.029 [-0.131, +0.236] | 0.763 | 0.794 | 5/6/5 | -0.062 | +0.188 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=16, ref 0.371 → 0.425) | +0.055 [-0.093, +0.251] | 0.542 | 0.557 | 6/4/6 | -0.062 | +0.250 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp22 gate T25 (n=16, ref 0.613 → 0.425) | -0.188 [-0.353, +0.059] | 0.094 | 0.094 | 3/11/2 | -0.250 | -0.125 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=16, ref 0.465 → 0.425) | -0.040 [-0.237, +0.167] | 0.713 | 0.705 | 5/5/6 | -0.188 | +0.188 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bar_val (n=16, ref 0.570 → 0.351) | -0.220 [-0.420, -0.026] | 0.053 | 0.047 | 2/8/6 | -0.250 | -0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bar_full (n=16, ref 0.570 → 0.351) | -0.220 [-0.420, -0.026] | 0.053 | 0.047 | 2/8/6 | -0.250 | -0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp14 (n=16, ref 0.519 → 0.351) | -0.168 [-0.375, -0.013] | 0.093 | 0.070 | 2/7/7 | -0.188 | -0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp14_cheap (n=16, ref 0.411 → 0.351) | -0.060 [-0.208, +0.019] | 0.298 | 0.361 | 4/6/6 | -0.125 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs lex13 (n=16, ref 0.326 → 0.351) | +0.025 [-0.176, +0.161] | 0.777 | 0.786 | 8/4/4 | -0.062 | +0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bm25_01 (n=16, ref 0.290 → 0.351) | +0.061 [-0.045, +0.191] | 0.343 | 0.356 | 8/3/5 | +0.062 | +0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05 (n=16, ref 0.319 → 0.351) | +0.032 [-0.105, +0.152] | 0.642 | 0.639 | 7/4/5 | +0.000 | +0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05+bge@20 (n=16, ref 0.468 → 0.351) | -0.117 [-0.326, +0.047] | 0.245 | 0.252 | 5/7/4 | -0.188 | +0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.351) | -0.045 [-0.141, +0.031] | 0.329 | 0.342 | 5/6/5 | -0.062 | +0.062 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=16, ref 0.371 → 0.351) | -0.020 [-0.178, +0.105] | 0.792 | 0.797 | 5/5/6 | -0.062 | +0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp22 gate T25 (n=16, ref 0.613 → 0.351) | **-0.262** [-0.410, -0.098] | 0.006 | 0.008 | 1/12/3 | -0.250 | -0.250 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=16, ref 0.372 → 0.351) | -0.022 [-0.179, +0.103] | 0.772 | 0.779 | 6/5/5 | -0.062 | +0.125 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bar_val (n=16, ref 0.570 → 0.316) | **-0.255** [-0.449, -0.058] | 0.028 | 0.029 | 3/9/4 | -0.312 | -0.188 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bar_full (n=16, ref 0.570 → 0.316) | **-0.255** [-0.449, -0.058] | 0.028 | 0.029 | 3/9/4 | -0.312 | -0.188 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp14 (n=16, ref 0.519 → 0.316) | -0.203 [-0.409, -0.042] | 0.052 | 0.062 | 3/7/6 | -0.250 | -0.188 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp14_cheap (n=16, ref 0.411 → 0.316) | -0.095 [-0.217, -0.004] | 0.107 | 0.119 | 3/7/6 | -0.188 | -0.062 |
| ltr24__logreg__notype-nobge__pooled-scored | vs lex13 (n=16, ref 0.326 → 0.316) | -0.010 [-0.206, +0.140] | 0.914 | 0.921 | 9/4/3 | -0.125 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bm25_01 (n=16, ref 0.290 → 0.316) | +0.026 [-0.093, +0.162] | 0.711 | 0.716 | 7/4/5 | +0.000 | +0.062 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05 (n=16, ref 0.319 → 0.316) | -0.003 [-0.120, +0.124] | 0.964 | 0.983 | 7/4/5 | -0.062 | +0.062 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05+bge@20 (n=16, ref 0.468 → 0.316) | -0.152 [-0.325, -0.003] | 0.088 | 0.091 | 5/8/3 | -0.250 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.316) | -0.081 [-0.197, -0.016] | 0.095 | 0.090 | 2/7/7 | -0.125 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=16, ref 0.371 → 0.316) | -0.055 [-0.176, +0.033] | 0.338 | 0.363 | 5/4/7 | -0.125 | +0.062 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp22 gate T25 (n=16, ref 0.613 → 0.316) | **-0.297** [-0.443, -0.127] | 0.003 | 0.004 | 1/13/2 | -0.312 | -0.312 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=16, ref 0.255 → 0.316) | +0.061 [-0.067, +0.165] | 0.337 | 0.340 | 11/2/3 | +0.000 | +0.062 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bar_val (n=16, ref 0.570 → 0.510) | -0.060 [-0.248, +0.169] | 0.588 | 0.612 | 5/6/5 | -0.125 | +0.062 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bar_full (n=16, ref 0.570 → 0.510) | -0.060 [-0.248, +0.169] | 0.588 | 0.612 | 5/6/5 | -0.125 | +0.062 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp14 (n=16, ref 0.519 → 0.510) | -0.009 [-0.130, +0.098] | 0.885 | 0.906 | 5/3/8 | -0.062 | +0.062 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp14_cheap (n=16, ref 0.411 → 0.510) | +0.099 [-0.055, +0.281] | 0.273 | 0.277 | 8/2/6 | +0.000 | +0.188 |
| ltr24__lgbm-tiny__small__pooled-scored | vs lex13 (n=16, ref 0.326 → 0.510) | +0.184 [-0.050, +0.401] | 0.144 | 0.143 | 10/2/4 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bm25_01 (n=16, ref 0.290 → 0.510) | **+0.220** [+0.042, +0.421] | 0.044 | 0.049 | 10/2/4 | +0.188 | +0.312 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05 (n=16, ref 0.319 → 0.510) | **+0.191** [+0.050, +0.365] | 0.034 | 0.029 | 11/2/3 | +0.125 | +0.312 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05+bge@20 (n=16, ref 0.468 → 0.510) | +0.042 [-0.121, +0.248] | 0.668 | 0.661 | 6/5/5 | -0.062 | +0.250 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.510) | +0.114 [-0.048, +0.304] | 0.232 | 0.224 | 8/3/5 | +0.062 | +0.250 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap (n=16, ref 0.371 → 0.510) | +0.139 [-0.047, +0.355] | 0.202 | 0.206 | 9/3/4 | +0.062 | +0.312 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp22 gate T25 (n=16, ref 0.613 → 0.510) | -0.103 [-0.227, +0.111] | 0.235 | 0.254 | 1/8/7 | -0.125 | -0.062 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp24 mined-only (same features) (n=16, ref 0.425 → 0.510) | +0.085 [-0.085, +0.252] | 0.346 | 0.347 | 8/3/5 | +0.062 | +0.250 |
| ltr24__logreg__small__pooled-scored | vs bar_val (n=16, ref 0.570 → 0.523) | -0.047 [-0.234, +0.170] | 0.665 | 0.666 | 5/5/6 | -0.062 | -0.062 |
| ltr24__logreg__small__pooled-scored | vs bar_full (n=16, ref 0.570 → 0.523) | -0.047 [-0.234, +0.170] | 0.665 | 0.666 | 5/5/6 | -0.062 | -0.062 |
| ltr24__logreg__small__pooled-scored | vs exp14 (n=16, ref 0.519 → 0.523) | +0.004 [-0.123, +0.157] | 0.953 | 0.959 | 6/4/6 | +0.000 | -0.062 |
| ltr24__logreg__small__pooled-scored | vs exp14_cheap (n=16, ref 0.411 → 0.523) | +0.112 [-0.055, +0.334] | 0.287 | 0.297 | 8/4/4 | +0.062 | +0.062 |
| ltr24__logreg__small__pooled-scored | vs lex13 (n=16, ref 0.326 → 0.523) | +0.197 [-0.025, +0.438] | 0.132 | 0.133 | 10/2/4 | +0.125 | +0.125 |
| ltr24__logreg__small__pooled-scored | vs bm25_01 (n=16, ref 0.290 → 0.523) | **+0.233** [+0.049, +0.456] | 0.048 | 0.050 | 11/3/2 | +0.250 | +0.188 |
| ltr24__logreg__small__pooled-scored | vs convex05 (n=16, ref 0.319 → 0.523) | **+0.204** [+0.050, +0.398] | 0.042 | 0.036 | 10/3/3 | +0.188 | +0.188 |
| ltr24__logreg__small__pooled-scored | vs convex05+bge@20 (n=16, ref 0.468 → 0.523) | +0.055 [-0.105, +0.253] | 0.563 | 0.615 | 6/4/6 | +0.000 | +0.125 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap+bge (n=16, ref 0.396 → 0.523) | +0.127 [-0.046, +0.329] | 0.218 | 0.226 | 8/4/4 | +0.125 | +0.125 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap (n=16, ref 0.371 → 0.523) | +0.152 [-0.036, +0.377] | 0.178 | 0.182 | 9/3/4 | +0.125 | +0.188 |
| ltr24__logreg__small__pooled-scored | vs exp22 gate T25 (n=16, ref 0.613 → 0.523) | -0.090 [-0.203, +0.123] | 0.277 | 0.293 | 1/8/7 | -0.062 | -0.188 |
| ltr24__logreg__small__pooled-scored | vs exp24 mined-only (same features) (n=16, ref 0.447 → 0.523) | +0.076 [-0.133, +0.302] | 0.512 | 0.496 | 7/4/5 | +0.000 | +0.188 |

**Human full set – paired tests (Δ = exp-24 oof − reference)**

| run | reference  Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 | Δ H@10 |
|---|---|:--|--:|--:|:--|--:|--:|
| ltr24__lgbm-tiny__notype__mined | vs bar_val (n=40, ref 0.522 → 0.483) | -0.039 [-0.163, +0.088] | 0.553 | ~0.550 | 13/16/11 | +0.025 | -0.200 |
| ltr24__lgbm-tiny__notype__mined | vs bar_full (n=40, ref 0.522 → 0.483) | -0.039 [-0.163, +0.088] | 0.553 | ~0.550 | 13/16/11 | +0.025 | -0.200 |
| ltr24__lgbm-tiny__notype__mined | vs exp14 (n=40, ref 0.608 → 0.483) | -0.124 [-0.252, +0.007] | 0.075 | ~0.075 | 10/18/12 | -0.100 | -0.200 |
| ltr24__lgbm-tiny__notype__mined | vs exp14_cheap (n=40, ref 0.491 → 0.483) | -0.008 [-0.099, +0.095] | 0.879 | ~0.878 | 10/15/15 | +0.000 | -0.175 |
| ltr24__lgbm-tiny__notype__mined | vs lex13 (n=40, ref 0.391 → 0.483) | **+0.092** [+0.018, +0.181] | 0.035 | ~0.032 | 22/5/13 | +0.075 | +0.025 |
| ltr24__lgbm-tiny__notype__mined | vs bm25_01 (n=40, ref 0.339 → 0.483) | **+0.144** [+0.060, +0.239] | 0.003 | ~0.002 | 27/3/10 | +0.175 | +0.025 |
| ltr24__lgbm-tiny__notype__mined | vs convex05 (n=40, ref 0.395 → 0.483) | +0.089 [-0.017, +0.205] | 0.129 | ~0.129 | 20/12/8 | +0.125 | +0.000 |
| ltr24__lgbm-tiny__notype__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.483) | -0.012 [-0.118, +0.097] | 0.838 | ~0.836 | 15/14/11 | -0.025 | -0.050 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.483) | +0.011 [-0.059, +0.096] | 0.780 | ~0.786 | 12/12/16 | +0.025 | -0.075 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.483) | **+0.056** [+0.026, +0.120] | 0.013 | ~0.000 | 18/3/19 | +0.050 | +0.000 |
| ltr24__lgbm-tiny__notype__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.483) | **-0.145** [-0.267, -0.028] | 0.025 | ~0.027 | 7/22/11 | -0.075 | -0.275 |
| ltr24__logreg__notype__mined | vs bar_val (n=40, ref 0.522 → 0.499) | -0.023 [-0.150, +0.100] | 0.724 | ~0.727 | 13/14/13 | +0.075 | -0.125 |
| ltr24__logreg__notype__mined | vs bar_full (n=40, ref 0.522 → 0.499) | -0.023 [-0.150, +0.100] | 0.724 | ~0.727 | 13/14/13 | +0.075 | -0.125 |
| ltr24__logreg__notype__mined | vs exp14 (n=40, ref 0.608 → 0.499) | -0.108 [-0.240, +0.020] | 0.113 | ~0.116 | 7/16/17 | -0.050 | -0.125 |
| ltr24__logreg__notype__mined | vs exp14_cheap (n=40, ref 0.491 → 0.499) | +0.008 [-0.088, +0.110] | 0.874 | ~0.874 | 12/13/15 | +0.050 | -0.100 |
| ltr24__logreg__notype__mined | vs lex13 (n=40, ref 0.391 → 0.499) | **+0.108** [+0.036, +0.202] | 0.017 | ~0.015 | 20/4/16 | +0.125 | +0.100 |
| ltr24__logreg__notype__mined | vs bm25_01 (n=40, ref 0.339 → 0.499) | **+0.160** [+0.077, +0.257] | 0.001 | ~0.001 | 23/5/12 | +0.225 | +0.100 |
| ltr24__logreg__notype__mined | vs convex05 (n=40, ref 0.395 → 0.499) | +0.105 [+0.008, +0.214] | 0.058 | ~0.057 | 18/10/12 | +0.175 | +0.075 |
| ltr24__logreg__notype__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.499) | +0.004 [-0.106, +0.115] | 0.942 | ~0.941 | 14/12/14 | +0.025 | +0.025 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.499) | +0.027 [-0.036, +0.112] | 0.470 | ~0.478 | 12/11/17 | +0.075 | +0.000 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.499) | **+0.072** [+0.027, +0.146] | 0.019 | ~0.012 | 13/8/19 | +0.100 | +0.075 |
| ltr24__logreg__notype__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.499) | **-0.129** [-0.254, -0.017] | 0.043 | ~0.044 | 8/19/13 | -0.025 | -0.200 |
| ltr24__lgbm-tiny__withtype__mined | vs bar_val (n=40, ref 0.522 → 0.493) | -0.029 [-0.153, +0.093] | 0.654 | ~0.655 | 12/15/13 | +0.050 | -0.175 |
| ltr24__lgbm-tiny__withtype__mined | vs bar_full (n=40, ref 0.522 → 0.493) | -0.029 [-0.153, +0.093] | 0.654 | ~0.655 | 12/15/13 | +0.050 | -0.175 |
| ltr24__lgbm-tiny__withtype__mined | vs exp14 (n=40, ref 0.608 → 0.493) | -0.114 [-0.241, +0.015] | 0.093 | ~0.093 | 10/17/13 | -0.075 | -0.175 |
| ltr24__lgbm-tiny__withtype__mined | vs exp14_cheap (n=40, ref 0.491 → 0.493) | +0.002 [-0.087, +0.103] | 0.962 | ~0.964 | 11/14/15 | +0.025 | -0.150 |
| ltr24__lgbm-tiny__withtype__mined | vs lex13 (n=40, ref 0.391 → 0.493) | **+0.102** [+0.024, +0.201] | 0.031 | ~0.029 | 21/5/14 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__withtype__mined | vs bm25_01 (n=40, ref 0.339 → 0.493) | **+0.154** [+0.066, +0.253] | 0.003 | ~0.002 | 27/4/9 | +0.200 | +0.050 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05 (n=40, ref 0.395 → 0.493) | +0.099 [-0.002, +0.211] | 0.080 | ~0.077 | 20/11/9 | +0.150 | +0.025 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.493) | -0.002 [-0.108, +0.110] | 0.977 | ~0.976 | 15/13/12 | +0.000 | -0.025 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.493) | +0.021 [-0.043, +0.106] | 0.576 | ~0.586 | 12/12/16 | +0.050 | -0.050 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.493) | **+0.066** [+0.029, +0.139] | 0.015 | ~0.000 | 18/3/19 | +0.075 | +0.025 |
| ltr24__lgbm-tiny__withtype__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.493) | **-0.135** [-0.257, -0.021] | 0.035 | ~0.034 | 8/21/11 | -0.050 | -0.250 |
| ltr24__logreg__withtype__mined | vs bar_val (n=40, ref 0.522 → 0.476) | -0.046 [-0.175, +0.078] | 0.485 | ~0.488 | 11/15/14 | +0.025 | -0.200 |
| ltr24__logreg__withtype__mined | vs bar_full (n=40, ref 0.522 → 0.476) | -0.046 [-0.175, +0.078] | 0.485 | ~0.488 | 11/15/14 | +0.025 | -0.200 |
| ltr24__logreg__withtype__mined | vs exp14 (n=40, ref 0.608 → 0.476) | **-0.132** [-0.255, -0.008] | 0.048 | ~0.048 | 5/19/16 | -0.100 | -0.200 |
| ltr24__logreg__withtype__mined | vs exp14_cheap (n=40, ref 0.491 → 0.476) | -0.015 [-0.118, +0.090] | 0.781 | ~0.782 | 11/16/13 | +0.000 | -0.175 |
| ltr24__logreg__withtype__mined | vs lex13 (n=40, ref 0.391 → 0.476) | **+0.085** [+0.013, +0.169] | 0.043 | ~0.039 | 18/7/15 | +0.075 | +0.025 |
| ltr24__logreg__withtype__mined | vs bm25_01 (n=40, ref 0.339 → 0.476) | **+0.137** [+0.054, +0.230] | 0.005 | ~0.004 | 20/6/14 | +0.175 | +0.025 |
| ltr24__logreg__withtype__mined | vs convex05 (n=40, ref 0.395 → 0.476) | +0.082 [-0.019, +0.193] | 0.150 | ~0.149 | 17/12/11 | +0.125 | +0.000 |
| ltr24__logreg__withtype__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.476) | -0.019 [-0.131, +0.098] | 0.750 | ~0.746 | 14/15/11 | -0.025 | -0.050 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.476) | +0.004 [-0.077, +0.092] | 0.932 | ~0.932 | 11/13/16 | +0.025 | -0.075 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.476) | +0.049 [-0.010, +0.119] | 0.148 | ~0.151 | 14/11/15 | +0.050 | +0.000 |
| ltr24__logreg__withtype__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.476) | **-0.152** [-0.281, -0.036] | 0.021 | ~0.020 | 7/20/13 | -0.075 | -0.275 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bar_val (n=40, ref 0.522 → 0.528) | +0.006 [-0.121, +0.127] | 0.925 | ~0.924 | 14/14/12 | +0.100 | -0.175 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bar_full (n=40, ref 0.522 → 0.528) | +0.006 [-0.121, +0.127] | 0.925 | ~0.924 | 14/14/12 | +0.100 | -0.175 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp14 (n=40, ref 0.608 → 0.528) | -0.079 [-0.204, +0.043] | 0.222 | ~0.226 | 10/15/15 | -0.025 | -0.175 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp14_cheap (n=40, ref 0.491 → 0.528) | +0.037 [-0.045, +0.134] | 0.431 | ~0.442 | 12/13/15 | +0.075 | -0.150 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs lex13 (n=40, ref 0.391 → 0.528) | **+0.137** [+0.056, +0.241] | 0.006 | ~0.004 | 22/4/14 | +0.150 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs bm25_01 (n=40, ref 0.339 → 0.528) | **+0.189** [+0.102, +0.288] | 0.000 | ~0.000 | 27/2/11 | +0.250 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05 (n=40, ref 0.395 → 0.528) | **+0.134** [+0.037, +0.239] | 0.015 | ~0.016 | 21/9/10 | +0.200 | +0.025 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.528) | +0.033 [-0.068, +0.137] | 0.541 | ~0.543 | 16/11/13 | +0.050 | -0.025 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.528) | +0.056 [-0.004, +0.136] | 0.127 | ~0.137 | 13/9/18 | +0.100 | -0.050 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.528) | **+0.101** [+0.049, +0.183] | 0.004 | ~0.000 | 19/3/18 | +0.125 | +0.025 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.528) | -0.100 [-0.225, +0.013] | 0.117 | ~0.116 | 8/19/13 | +0.000 | -0.250 |
| ltr24__logreg__notype-nogate__mined | vs bar_val (n=40, ref 0.522 → 0.524) | +0.002 [-0.120, +0.121] | 0.971 | ~0.971 | 14/12/14 | +0.100 | -0.125 |
| ltr24__logreg__notype-nogate__mined | vs bar_full (n=40, ref 0.522 → 0.524) | +0.002 [-0.120, +0.121] | 0.971 | ~0.971 | 14/12/14 | +0.100 | -0.125 |
| ltr24__logreg__notype-nogate__mined | vs exp14 (n=40, ref 0.608 → 0.524) | -0.083 [-0.217, +0.048] | 0.229 | ~0.234 | 10/16/14 | -0.025 | -0.125 |
| ltr24__logreg__notype-nogate__mined | vs exp14_cheap (n=40, ref 0.491 → 0.524) | +0.033 [-0.067, +0.146] | 0.547 | ~0.551 | 14/11/15 | +0.075 | -0.100 |
| ltr24__logreg__notype-nogate__mined | vs lex13 (n=40, ref 0.391 → 0.524) | **+0.133** [+0.055, +0.238] | 0.007 | ~0.005 | 20/3/17 | +0.150 | +0.100 |
| ltr24__logreg__notype-nogate__mined | vs bm25_01 (n=40, ref 0.339 → 0.524) | **+0.185** [+0.099, +0.287] | 0.001 | ~0.000 | 24/4/12 | +0.250 | +0.100 |
| ltr24__logreg__notype-nogate__mined | vs convex05 (n=40, ref 0.395 → 0.524) | **+0.130** [+0.031, +0.245] | 0.024 | ~0.024 | 18/10/12 | +0.200 | +0.075 |
| ltr24__logreg__notype-nogate__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.524) | +0.029 [-0.070, +0.134] | 0.579 | ~0.590 | 13/11/16 | +0.050 | +0.025 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.524) | +0.052 [-0.014, +0.143] | 0.191 | ~0.199 | 12/10/18 | +0.100 | +0.000 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.524) | **+0.097** [+0.046, +0.175] | 0.005 | ~0.001 | 16/5/19 | +0.125 | +0.075 |
| ltr24__logreg__notype-nogate__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.524) | -0.104 [-0.228, +0.005] | 0.091 | ~0.091 | 8/18/14 | +0.000 | -0.200 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bar_val (n=40, ref 0.522 → 0.432) | -0.090 [-0.219, +0.041] | 0.188 | ~0.192 | 12/17/11 | -0.025 | -0.200 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bar_full (n=40, ref 0.522 → 0.432) | -0.090 [-0.219, +0.041] | 0.188 | ~0.192 | 12/17/11 | -0.025 | -0.200 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp14 (n=40, ref 0.608 → 0.432) | **-0.175** [-0.306, -0.050] | 0.012 | ~0.012 | 8/19/13 | -0.150 | -0.200 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp14_cheap (n=40, ref 0.491 → 0.432) | -0.059 [-0.156, +0.031] | 0.233 | ~0.239 | 7/19/14 | -0.050 | -0.175 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs lex13 (n=40, ref 0.391 → 0.432) | +0.041 [-0.035, +0.131] | 0.349 | ~0.349 | 19/8/13 | +0.025 | +0.025 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs bm25_01 (n=40, ref 0.339 → 0.432) | **+0.093** [+0.016, +0.186] | 0.038 | ~0.038 | 24/4/12 | +0.125 | +0.025 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05 (n=40, ref 0.395 → 0.432) | +0.037 [-0.065, +0.138] | 0.477 | ~0.482 | 18/12/10 | +0.075 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.432) | -0.063 [-0.183, +0.049] | 0.301 | ~0.303 | 13/16/11 | -0.075 | -0.050 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.432) | -0.040 [-0.120, +0.038] | 0.329 | ~0.325 | 8/15/17 | -0.025 | -0.075 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.432) | +0.005 [+0.001, +0.012] | 0.074 | 0.061 | 9/3/28 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.432) | **-0.196** [-0.319, -0.076] | 0.004 | ~0.003 | 6/24/10 | -0.125 | -0.275 |
| ltr24__logreg__notype-nobge__mined | vs bar_val (n=40, ref 0.522 → 0.336) | **-0.186** [-0.316, -0.058] | 0.009 | ~0.008 | 8/22/10 | -0.150 | -0.200 |
| ltr24__logreg__notype-nobge__mined | vs bar_full (n=40, ref 0.522 → 0.336) | **-0.186** [-0.316, -0.058] | 0.009 | ~0.008 | 8/22/10 | -0.150 | -0.200 |
| ltr24__logreg__notype-nobge__mined | vs exp14 (n=40, ref 0.608 → 0.336) | **-0.272** [-0.405, -0.138] | 0.000 | ~0.000 | 6/26/8 | -0.275 | -0.200 |
| ltr24__logreg__notype-nobge__mined | vs exp14_cheap (n=40, ref 0.491 → 0.336) | **-0.155** [-0.265, -0.053] | 0.007 | ~0.007 | 6/25/9 | -0.175 | -0.175 |
| ltr24__logreg__notype-nobge__mined | vs lex13 (n=40, ref 0.391 → 0.336) | -0.056 [-0.148, +0.022] | 0.213 | ~0.217 | 13/11/16 | -0.100 | +0.025 |
| ltr24__logreg__notype-nobge__mined | vs bm25_01 (n=40, ref 0.339 → 0.336) | -0.003 [-0.105, +0.094] | 0.952 | ~0.951 | 16/10/14 | +0.000 | +0.025 |
| ltr24__logreg__notype-nobge__mined | vs convex05 (n=40, ref 0.395 → 0.336) | -0.059 [-0.172, +0.046] | 0.299 | ~0.300 | 12/18/10 | -0.050 | +0.000 |
| ltr24__logreg__notype-nobge__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.336) | **-0.159** [-0.295, -0.023] | 0.028 | ~0.028 | 11/21/8 | -0.200 | -0.050 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.336) | **-0.136** [-0.236, -0.045] | 0.008 | ~0.008 | 8/22/10 | -0.150 | -0.075 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.336) | **-0.091** [-0.172, -0.039] | 0.009 | ~0.006 | 6/19/15 | -0.125 | +0.000 |
| ltr24__logreg__notype-nobge__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.336) | **-0.293** [-0.414, -0.171] | 0.000 | ~0.000 | 5/26/9 | -0.250 | -0.275 |
| ltr24__lgbm-tiny__small__mined | vs bar_val (n=40, ref 0.522 → 0.477) | -0.045 [-0.165, +0.073] | 0.473 | ~0.473 | 10/16/14 | +0.000 | -0.125 |
| ltr24__lgbm-tiny__small__mined | vs bar_full (n=40, ref 0.522 → 0.477) | -0.045 [-0.165, +0.073] | 0.473 | ~0.473 | 10/16/14 | +0.000 | -0.125 |
| ltr24__lgbm-tiny__small__mined | vs exp14 (n=40, ref 0.608 → 0.477) | **-0.130** [-0.249, -0.015] | 0.037 | ~0.036 | 9/18/13 | -0.125 | -0.125 |
| ltr24__lgbm-tiny__small__mined | vs exp14_cheap (n=40, ref 0.491 → 0.477) | -0.014 [-0.102, +0.077] | 0.770 | ~0.766 | 12/15/13 | -0.025 | -0.100 |
| ltr24__lgbm-tiny__small__mined | vs lex13 (n=40, ref 0.391 → 0.477) | **+0.086** [+0.010, +0.172] | 0.048 | ~0.046 | 19/5/16 | +0.050 | +0.100 |
| ltr24__lgbm-tiny__small__mined | vs bm25_01 (n=40, ref 0.339 → 0.477) | **+0.139** [+0.064, +0.226] | 0.002 | ~0.001 | 24/4/12 | +0.150 | +0.100 |
| ltr24__lgbm-tiny__small__mined | vs convex05 (n=40, ref 0.395 → 0.477) | +0.083 [-0.005, +0.174] | 0.084 | ~0.088 | 20/12/8 | +0.100 | +0.075 |
| ltr24__lgbm-tiny__small__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.477) | -0.018 [-0.122, +0.085] | 0.743 | ~0.742 | 15/15/10 | -0.050 | +0.025 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.477) | +0.005 [-0.061, +0.077] | 0.887 | ~0.887 | 12/13/15 | +0.000 | +0.000 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.477) | **+0.050** [+0.025, +0.096] | 0.006 | ~0.001 | 16/6/18 | +0.025 | +0.075 |
| ltr24__lgbm-tiny__small__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.477) | **-0.151** [-0.269, -0.041] | 0.015 | ~0.016 | 7/22/11 | -0.100 | -0.200 |
| ltr24__logreg__small__mined | vs bar_val (n=40, ref 0.522 → 0.469) | -0.053 [-0.174, +0.060] | 0.378 | ~0.372 | 10/15/15 | +0.025 | -0.150 |
| ltr24__logreg__small__mined | vs bar_full (n=40, ref 0.522 → 0.469) | -0.053 [-0.174, +0.060] | 0.378 | ~0.372 | 10/15/15 | +0.025 | -0.150 |
| ltr24__logreg__small__mined | vs exp14 (n=40, ref 0.608 → 0.469) | **-0.139** [-0.269, -0.011] | 0.044 | ~0.043 | 8/17/15 | -0.100 | -0.150 |
| ltr24__logreg__small__mined | vs exp14_cheap (n=40, ref 0.491 → 0.469) | -0.022 [-0.126, +0.094] | 0.698 | ~0.704 | 10/16/14 | +0.000 | -0.125 |
| ltr24__logreg__small__mined | vs lex13 (n=40, ref 0.391 → 0.469) | +0.078 [-0.002, +0.187] | 0.113 | ~0.113 | 17/5/18 | +0.075 | +0.075 |
| ltr24__logreg__small__mined | vs bm25_01 (n=40, ref 0.339 → 0.469) | **+0.130** [+0.053, +0.226] | 0.005 | ~0.004 | 22/5/13 | +0.175 | +0.075 |
| ltr24__logreg__small__mined | vs convex05 (n=40, ref 0.395 → 0.469) | +0.074 [-0.019, +0.179] | 0.154 | ~0.159 | 15/12/13 | +0.125 | +0.050 |
| ltr24__logreg__small__mined | vs convex05+bge@20 (n=40, ref 0.495 → 0.469) | -0.026 [-0.133, +0.079] | 0.638 | ~0.643 | 11/15/14 | -0.025 | +0.000 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.469) | -0.003 [-0.085, +0.095] | 0.944 | ~0.943 | 11/16/13 | +0.025 | -0.025 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap (n=40, ref 0.427 → 0.469) | +0.042 [-0.020, +0.117] | 0.239 | ~0.235 | 14/10/16 | +0.050 | +0.050 |
| ltr24__logreg__small__mined | vs exp22 gate T25 (n=40, ref 0.628 → 0.469) | **-0.159** [-0.280, -0.053] | 0.009 | ~0.007 | 4/22/14 | -0.075 | -0.225 |
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
| ltr24__lgbm-tiny__notype__pooled | vs exp24 mined-only (same features) (n=40, ref 0.483 → 0.577) | +0.093 [-0.020, +0.206] | 0.118 | ~0.119 | 19/6/15 | +0.075 | +0.250 |
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
| ltr24__logreg__notype__pooled | vs bar_val (n=40, ref 0.522 → 0.524) | +0.002 [-0.116, +0.110] | 0.975 | ~0.975 | 13/9/18 | +0.025 | -0.025 |
| ltr24__logreg__notype__pooled | vs bar_full (n=40, ref 0.522 → 0.524) | +0.002 [-0.116, +0.110] | 0.975 | ~0.975 | 13/9/18 | +0.025 | -0.025 |
| ltr24__logreg__notype__pooled | vs exp14 (n=40, ref 0.608 → 0.524) | -0.084 [-0.180, +0.007] | 0.088 | ~0.091 | 9/13/18 | -0.100 | -0.025 |
| ltr24__logreg__notype__pooled | vs exp14_cheap (n=40, ref 0.491 → 0.524) | +0.033 [-0.059, +0.119] | 0.476 | ~0.479 | 16/9/15 | +0.000 | +0.000 |
| ltr24__logreg__notype__pooled | vs lex13 (n=40, ref 0.391 → 0.524) | **+0.133** [+0.032, +0.241] | 0.019 | ~0.018 | 22/6/12 | +0.075 | +0.200 |
| ltr24__logreg__notype__pooled | vs bm25_01 (n=40, ref 0.339 → 0.524) | **+0.185** [+0.091, +0.287] | 0.001 | ~0.001 | 24/4/12 | +0.175 | +0.200 |
| ltr24__logreg__notype__pooled | vs convex05 (n=40, ref 0.395 → 0.524) | **+0.129** [+0.045, +0.223] | 0.008 | ~0.009 | 21/7/12 | +0.125 | +0.175 |
| ltr24__logreg__notype__pooled | vs convex05+bge@20 (n=40, ref 0.495 → 0.524) | +0.029 [-0.064, +0.118] | 0.545 | ~0.543 | 14/9/17 | -0.025 | +0.125 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.524) | +0.052 [-0.026, +0.130] | 0.202 | ~0.203 | 14/9/17 | +0.025 | +0.100 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap (n=40, ref 0.427 → 0.524) | **+0.097** [+0.025, +0.182] | 0.023 | ~0.019 | 19/3/18 | +0.050 | +0.175 |
| ltr24__logreg__notype__pooled | vs exp22 gate T25 (n=40, ref 0.628 → 0.524) | -0.105 [-0.220, +0.001] | 0.078 | ~0.075 | 9/18/13 | -0.075 | -0.100 |
| ltr24__logreg__notype__pooled | vs exp24 mined-only (same features) (n=40, ref 0.499 → 0.524) | +0.025 [-0.039, +0.084] | 0.448 | 0.455 | 14/6/20 | -0.050 | +0.100 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.523) | +0.002 [-0.121, +0.115] | 0.981 | ~0.979 | 14/11/15 | +0.050 | -0.075 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.523) | +0.002 [-0.121, +0.115] | 0.981 | ~0.979 | 14/11/15 | +0.050 | -0.075 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.523) | -0.084 [-0.192, +0.020] | 0.135 | ~0.136 | 10/16/14 | -0.075 | -0.075 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.523) | +0.032 [-0.052, +0.115] | 0.458 | ~0.457 | 15/11/14 | +0.025 | -0.050 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.523) | **+0.132** [+0.054, +0.224] | 0.005 | ~0.003 | 22/3/15 | +0.100 | +0.150 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.523) | **+0.185** [+0.105, +0.276] | 0.000 | ~0.000 | 26/3/11 | +0.200 | +0.150 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.523) | **+0.129** [+0.045, +0.222] | 0.008 | ~0.007 | 23/8/9 | +0.150 | +0.125 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.523) | +0.029 [-0.069, +0.123] | 0.569 | ~0.568 | 17/10/13 | +0.000 | +0.075 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.523) | +0.051 [-0.003, +0.118] | 0.106 | ~0.112 | 14/8/18 | +0.050 | +0.050 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.523) | **+0.096** [+0.052, +0.165] | 0.002 | ~0.000 | 19/3/18 | +0.075 | +0.125 |
| ltr24__logreg__notype__pooled | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.523) | -0.105 [-0.224, -0.000] | 0.076 | ~0.075 | 8/17/15 | -0.050 | -0.150 |
| ltr24__lgbm-tiny__withtype__pooled | vs bar_val (n=40, ref 0.522 → 0.588) | +0.066 [-0.047, +0.182] | 0.279 | ~0.277 | 15/9/16 | +0.125 | +0.050 |
| ltr24__lgbm-tiny__withtype__pooled | vs bar_full (n=40, ref 0.522 → 0.588) | +0.066 [-0.047, +0.182] | 0.279 | ~0.277 | 15/9/16 | +0.125 | +0.050 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp14 (n=40, ref 0.608 → 0.588) | -0.020 [-0.090, +0.033] | 0.528 | 0.554 | 8/8/24 | +0.000 | +0.050 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp14_cheap (n=40, ref 0.491 → 0.588) | **+0.097** [+0.021, +0.195] | 0.033 | ~0.030 | 18/5/17 | +0.100 | +0.075 |
| ltr24__lgbm-tiny__withtype__pooled | vs lex13 (n=40, ref 0.391 → 0.588) | **+0.196** [+0.061, +0.329] | 0.007 | ~0.007 | 22/5/13 | +0.175 | +0.275 |
| ltr24__lgbm-tiny__withtype__pooled | vs bm25_01 (n=40, ref 0.339 → 0.588) | **+0.249** [+0.144, +0.368] | 0.000 | ~0.000 | 25/3/12 | +0.275 | +0.275 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05 (n=40, ref 0.395 → 0.588) | **+0.193** [+0.103, +0.305] | 0.001 | ~0.000 | 24/5/11 | +0.225 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05+bge@20 (n=40, ref 0.495 → 0.588) | +0.093 [+0.004, +0.201] | 0.072 | ~0.073 | 14/7/19 | +0.075 | +0.200 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.588) | **+0.115** [+0.017, +0.227] | 0.040 | ~0.041 | 17/7/16 | +0.125 | +0.175 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap (n=40, ref 0.427 → 0.588) | **+0.160** [+0.046, +0.282] | 0.012 | ~0.012 | 21/5/14 | +0.150 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp22 gate T25 (n=40, ref 0.628 → 0.588) | -0.041 [-0.152, +0.071] | 0.483 | ~0.482 | 10/15/15 | +0.025 | -0.025 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp24 mined-only (same features) (n=40, ref 0.493 → 0.588) | +0.094 [-0.021, +0.210] | 0.124 | ~0.129 | 18/6/16 | +0.075 | +0.225 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.591) | +0.069 [-0.045, +0.180] | 0.247 | ~0.247 | 15/10/15 | +0.125 | +0.025 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.591) | +0.069 [-0.045, +0.180] | 0.247 | ~0.247 | 15/10/15 | +0.125 | +0.025 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.591) | -0.016 [-0.094, +0.055] | 0.675 | 0.678 | 10/9/21 | +0.000 | +0.025 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.591) | **+0.100** [+0.024, +0.191] | 0.023 | ~0.022 | 18/7/15 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.591) | **+0.200** [+0.085, +0.321] | 0.002 | ~0.002 | 23/4/13 | +0.175 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.591) | **+0.252** [+0.150, +0.366] | 0.000 | ~0.000 | 26/3/11 | +0.275 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.591) | **+0.197** [+0.108, +0.302] | 0.000 | ~0.000 | 23/5/12 | +0.225 | +0.225 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.591) | +0.096 [+0.008, +0.196] | 0.052 | 0.050 | 15/5/20 | +0.075 | +0.175 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.591) | **+0.119** [+0.037, +0.215] | 0.013 | ~0.013 | 17/4/19 | +0.125 | +0.150 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.591) | **+0.164** [+0.067, +0.275] | 0.004 | ~0.004 | 21/3/16 | +0.150 | +0.225 |
| ltr24__lgbm-tiny__withtype__pooled | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.591) | -0.037 [-0.145, +0.065] | 0.499 | ~0.498 | 11/15/14 | +0.025 | -0.050 |
| ltr24__logreg__withtype__pooled | vs bar_val (n=40, ref 0.522 → 0.530) | +0.008 [-0.114, +0.118] | 0.894 | ~0.893 | 14/9/17 | +0.025 | -0.050 |
| ltr24__logreg__withtype__pooled | vs bar_full (n=40, ref 0.522 → 0.530) | +0.008 [-0.114, +0.118] | 0.894 | ~0.893 | 14/9/17 | +0.025 | -0.050 |
| ltr24__logreg__withtype__pooled | vs exp14 (n=40, ref 0.608 → 0.530) | -0.077 [-0.172, +0.012] | 0.109 | ~0.104 | 8/13/19 | -0.100 | -0.050 |
| ltr24__logreg__withtype__pooled | vs exp14_cheap (n=40, ref 0.491 → 0.530) | +0.039 [-0.053, +0.126] | 0.404 | ~0.406 | 14/11/15 | +0.000 | -0.025 |
| ltr24__logreg__withtype__pooled | vs lex13 (n=40, ref 0.391 → 0.530) | **+0.139** [+0.038, +0.246] | 0.015 | ~0.013 | 23/5/12 | +0.075 | +0.175 |
| ltr24__logreg__withtype__pooled | vs bm25_01 (n=40, ref 0.339 → 0.530) | **+0.191** [+0.098, +0.291] | 0.001 | ~0.001 | 24/4/12 | +0.175 | +0.175 |
| ltr24__logreg__withtype__pooled | vs convex05 (n=40, ref 0.395 → 0.530) | **+0.136** [+0.049, +0.230] | 0.007 | ~0.007 | 21/7/12 | +0.125 | +0.150 |
| ltr24__logreg__withtype__pooled | vs convex05+bge@20 (n=40, ref 0.495 → 0.530) | +0.035 [-0.054, +0.125] | 0.456 | ~0.459 | 13/10/17 | -0.025 | +0.100 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.530) | +0.058 [-0.020, +0.138] | 0.165 | ~0.167 | 14/10/16 | +0.025 | +0.075 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap (n=40, ref 0.427 → 0.530) | **+0.103** [+0.027, +0.192] | 0.020 | ~0.019 | 18/5/17 | +0.050 | +0.150 |
| ltr24__logreg__withtype__pooled | vs exp22 gate T25 (n=40, ref 0.628 → 0.530) | -0.098 [-0.217, +0.009] | 0.102 | ~0.104 | 9/17/14 | -0.075 | -0.125 |
| ltr24__logreg__withtype__pooled | vs exp24 mined-only (same features) (n=40, ref 0.476 → 0.530) | +0.054 [-0.015, +0.119] | 0.126 | ~0.125 | 19/3/18 | +0.000 | +0.150 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.524) | +0.002 [-0.125, +0.118] | 0.977 | ~0.976 | 13/12/15 | +0.050 | -0.075 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.524) | +0.002 [-0.125, +0.118] | 0.977 | ~0.976 | 13/12/15 | +0.050 | -0.075 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.524) | -0.084 [-0.188, +0.020] | 0.130 | ~0.127 | 9/16/15 | -0.075 | -0.075 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.524) | +0.033 [-0.051, +0.118] | 0.458 | ~0.459 | 13/12/15 | +0.025 | -0.050 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.524) | **+0.133** [+0.052, +0.226] | 0.006 | ~0.006 | 23/3/14 | +0.100 | +0.150 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.524) | **+0.185** [+0.104, +0.276] | 0.000 | ~0.000 | 25/3/12 | +0.200 | +0.150 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.524) | **+0.129** [+0.042, +0.224] | 0.010 | ~0.010 | 20/9/11 | +0.150 | +0.125 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.524) | +0.029 [-0.069, +0.125] | 0.569 | ~0.573 | 15/12/13 | +0.000 | +0.075 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.524) | +0.052 [-0.004, +0.122] | 0.118 | ~0.120 | 12/9/19 | +0.050 | +0.050 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.524) | **+0.097** [+0.048, +0.169] | 0.003 | ~0.002 | 17/5/18 | +0.075 | +0.125 |
| ltr24__logreg__withtype__pooled | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.524) | -0.105 [-0.227, +0.002] | 0.087 | ~0.085 | 7/17/16 | -0.050 | -0.150 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bar_val (n=40, ref 0.522 → 0.566) | +0.044 [-0.059, +0.153] | 0.430 | ~0.436 | 15/9/16 | +0.075 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bar_full (n=40, ref 0.522 → 0.566) | +0.044 [-0.059, +0.153] | 0.430 | ~0.436 | 15/9/16 | +0.075 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp14 (n=40, ref 0.608 → 0.566) | -0.041 [-0.122, +0.020] | 0.258 | 0.265 | 9/10/21 | -0.050 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp14_cheap (n=40, ref 0.491 → 0.566) | +0.075 [+0.006, +0.160] | 0.061 | ~0.052 | 16/5/19 | +0.050 | +0.075 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs lex13 (n=40, ref 0.391 → 0.566) | **+0.175** [+0.046, +0.306] | 0.013 | ~0.014 | 22/5/13 | +0.125 | +0.275 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs bm25_01 (n=40, ref 0.339 → 0.566) | **+0.227** [+0.129, +0.344] | 0.000 | ~0.000 | 26/3/11 | +0.225 | +0.275 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05 (n=40, ref 0.395 → 0.566) | **+0.172** [+0.088, +0.282] | 0.001 | ~0.001 | 23/5/12 | +0.175 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05+bge@20 (n=40, ref 0.495 → 0.566) | +0.071 [-0.014, +0.181] | 0.150 | ~0.159 | 14/8/18 | +0.025 | +0.200 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.566) | +0.094 [+0.004, +0.197] | 0.067 | ~0.067 | 19/7/14 | +0.075 | +0.175 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap (n=40, ref 0.427 → 0.566) | **+0.139** [+0.027, +0.260] | 0.027 | ~0.027 | 23/6/11 | +0.100 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp22 gate T25 (n=40, ref 0.628 → 0.566) | -0.062 [-0.164, +0.041] | 0.250 | ~0.245 | 8/15/17 | -0.025 | -0.025 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp24 mined-only (same features) (n=40, ref 0.528 → 0.566) | +0.038 [-0.068, +0.145] | 0.492 | ~0.496 | 16/8/16 | -0.025 | +0.225 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.614) | +0.091 [-0.016, +0.202] | 0.117 | ~0.116 | 17/7/16 | +0.150 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.614) | +0.091 [-0.016, +0.202] | 0.117 | ~0.116 | 17/7/16 | +0.150 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.614) | +0.006 [-0.086, +0.085] | 0.892 | ~0.897 | 12/9/19 | +0.025 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.614) | **+0.122** [+0.051, +0.211] | 0.005 | ~0.003 | 18/6/16 | +0.125 | +0.075 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.614) | **+0.222** [+0.112, +0.345] | 0.001 | ~0.000 | 24/4/12 | +0.200 | +0.275 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.614) | **+0.275** [+0.178, +0.388] | 0.000 | ~0.000 | 26/0/14 | +0.300 | +0.275 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.614) | **+0.219** [+0.131, +0.324] | 0.000 | ~0.000 | 22/4/14 | +0.250 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.614) | **+0.118** [+0.022, +0.234] | 0.035 | ~0.032 | 16/8/16 | +0.100 | +0.200 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.614) | **+0.141** [+0.067, +0.240] | 0.003 | ~0.002 | 20/3/17 | +0.150 | +0.175 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.614) | **+0.186** [+0.100, +0.295] | 0.001 | ~0.000 | 23/2/15 | +0.175 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.614) | -0.015 [-0.121, +0.090] | 0.787 | ~0.787 | 11/13/16 | +0.050 | -0.025 |
| ltr24__logreg__notype-nogate__pooled | vs bar_val (n=40, ref 0.522 → 0.498) | -0.024 [-0.140, +0.078] | 0.666 | ~0.668 | 12/10/18 | -0.025 | -0.025 |
| ltr24__logreg__notype-nogate__pooled | vs bar_full (n=40, ref 0.522 → 0.498) | -0.024 [-0.140, +0.078] | 0.666 | ~0.668 | 12/10/18 | -0.025 | -0.025 |
| ltr24__logreg__notype-nogate__pooled | vs exp14 (n=40, ref 0.608 → 0.498) | **-0.110** [-0.211, -0.018] | 0.032 | ~0.030 | 10/16/14 | -0.150 | -0.025 |
| ltr24__logreg__notype-nogate__pooled | vs exp14_cheap (n=40, ref 0.491 → 0.498) | +0.006 [-0.078, +0.083] | 0.876 | ~0.874 | 15/10/15 | -0.050 | +0.000 |
| ltr24__logreg__notype-nogate__pooled | vs lex13 (n=40, ref 0.391 → 0.498) | **+0.106** [+0.015, +0.201] | 0.035 | ~0.034 | 22/5/13 | +0.025 | +0.200 |
| ltr24__logreg__notype-nogate__pooled | vs bm25_01 (n=40, ref 0.339 → 0.498) | **+0.159** [+0.089, +0.238] | 0.000 | ~0.000 | 25/3/12 | +0.125 | +0.200 |
| ltr24__logreg__notype-nogate__pooled | vs convex05 (n=40, ref 0.395 → 0.498) | **+0.103** [+0.026, +0.189] | 0.019 | ~0.015 | 22/7/11 | +0.075 | +0.175 |
| ltr24__logreg__notype-nogate__pooled | vs convex05+bge@20 (n=40, ref 0.495 → 0.498) | +0.003 [-0.089, +0.080] | 0.954 | ~0.952 | 16/10/14 | -0.075 | +0.125 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.498) | +0.025 [-0.044, +0.090] | 0.469 | ~0.466 | 14/10/16 | -0.025 | +0.100 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap (n=40, ref 0.427 → 0.498) | +0.070 [-0.004, +0.147] | 0.084 | ~0.083 | 20/5/15 | +0.000 | +0.175 |
| ltr24__logreg__notype-nogate__pooled | vs exp22 gate T25 (n=40, ref 0.628 → 0.498) | **-0.131** [-0.244, -0.032] | 0.022 | ~0.021 | 7/18/15 | -0.125 | -0.100 |
| ltr24__logreg__notype-nogate__pooled | vs exp24 mined-only (same features) (n=40, ref 0.524 → 0.498) | -0.027 [-0.110, +0.030] | 0.454 | ~0.465 | 14/8/18 | -0.125 | +0.100 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.491) | -0.031 [-0.149, +0.079] | 0.607 | ~0.609 | 13/11/16 | +0.000 | -0.075 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.491) | -0.031 [-0.149, +0.079] | 0.607 | ~0.609 | 13/11/16 | +0.000 | -0.075 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.491) | **-0.116** [-0.228, -0.012] | 0.043 | ~0.042 | 9/16/15 | -0.125 | -0.075 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.491) | +0.000 [-0.088, +0.085] | 0.997 | ~0.997 | 14/12/14 | -0.025 | -0.050 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.491) | **+0.100** [+0.021, +0.192] | 0.030 | ~0.028 | 23/4/13 | +0.050 | +0.150 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.491) | **+0.152** [+0.083, +0.238] | 0.001 | ~0.000 | 26/3/11 | +0.150 | +0.150 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.491) | **+0.097** [+0.014, +0.190] | 0.040 | ~0.037 | 21/8/11 | +0.100 | +0.125 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.491) | -0.004 [-0.096, +0.082] | 0.936 | ~0.937 | 16/10/14 | -0.050 | +0.075 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.491) | +0.019 [-0.040, +0.075] | 0.529 | ~0.529 | 14/10/16 | +0.000 | +0.050 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.491) | +0.064 [+0.002, +0.134] | 0.071 | ~0.072 | 20/5/15 | +0.025 | +0.125 |
| ltr24__logreg__notype-nogate__pooled | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.491) | **-0.137** [-0.255, -0.034] | 0.021 | ~0.019 | 7/18/15 | -0.100 | -0.150 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bar_val (n=40, ref 0.522 → 0.401) | **-0.121** [-0.235, -0.007] | 0.048 | ~0.048 | 11/18/11 | -0.100 | -0.150 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bar_full (n=40, ref 0.522 → 0.401) | **-0.121** [-0.235, -0.007] | 0.048 | ~0.048 | 11/18/11 | -0.100 | -0.150 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp14 (n=40, ref 0.608 → 0.401) | **-0.206** [-0.325, -0.109] | 0.001 | ~0.001 | 6/19/15 | -0.225 | -0.150 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp14_cheap (n=40, ref 0.491 → 0.401) | **-0.090** [-0.175, -0.020] | 0.026 | ~0.026 | 6/20/14 | -0.125 | -0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs lex13 (n=40, ref 0.391 → 0.401) | +0.010 [-0.082, +0.108] | 0.842 | ~0.843 | 18/10/12 | -0.050 | +0.075 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs bm25_01 (n=40, ref 0.339 → 0.401) | +0.062 [-0.009, +0.150] | 0.128 | ~0.127 | 22/5/13 | +0.050 | +0.075 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05 (n=40, ref 0.395 → 0.401) | +0.007 [-0.070, +0.081] | 0.862 | ~0.864 | 17/9/14 | +0.000 | +0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05+bge@20 (n=40, ref 0.495 → 0.401) | -0.094 [-0.203, +0.005] | 0.089 | ~0.092 | 14/15/11 | -0.150 | +0.000 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.401) | -0.071 [-0.150, +0.005] | 0.076 | ~0.074 | 9/15/16 | -0.100 | -0.025 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap (n=40, ref 0.427 → 0.401) | -0.026 [-0.090, +0.032] | 0.415 | ~0.421 | 13/9/18 | -0.075 | +0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp22 gate T25 (n=40, ref 0.628 → 0.401) | **-0.227** [-0.341, -0.118] | 0.000 | ~0.000 | 5/24/11 | -0.200 | -0.225 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp24 mined-only (same features) (n=40, ref 0.432 → 0.401) | -0.031 [-0.094, +0.027] | 0.330 | ~0.336 | 12/9/19 | -0.075 | +0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.420) | -0.102 [-0.231, +0.027] | 0.131 | ~0.130 | 11/18/11 | -0.050 | -0.175 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.420) | -0.102 [-0.231, +0.027] | 0.131 | ~0.130 | 11/18/11 | -0.050 | -0.175 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.420) | **-0.187** [-0.320, -0.060] | 0.008 | ~0.007 | 8/20/12 | -0.175 | -0.175 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.420) | -0.071 [-0.164, +0.014] | 0.138 | ~0.140 | 7/19/14 | -0.075 | -0.150 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.420) | +0.029 [-0.029, +0.092] | 0.355 | ~0.368 | 19/6/15 | +0.000 | +0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.420) | **+0.082** [+0.017, +0.162] | 0.032 | ~0.029 | 22/4/14 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.420) | +0.026 [-0.071, +0.118] | 0.597 | ~0.596 | 17/11/12 | +0.050 | +0.025 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.420) | -0.074 [-0.191, +0.034] | 0.203 | ~0.204 | 15/14/11 | -0.100 | -0.025 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.420) | -0.052 [-0.120, +0.002] | 0.102 | ~0.098 | 8/15/17 | -0.050 | -0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.420) | -0.007 [-0.068, +0.032] | 0.785 | 0.891 | 11/6/23 | -0.025 | +0.025 |
| ltr24__lgbm-tiny__notype-nobge__pooled | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.420) | **-0.208** [-0.328, -0.092] | 0.002 | ~0.002 | 6/23/11 | -0.150 | -0.250 |
| ltr24__logreg__notype-nobge__pooled | vs bar_val (n=40, ref 0.522 → 0.393) | **-0.129** [-0.246, -0.023] | 0.033 | ~0.032 | 9/16/15 | -0.125 | -0.125 |
| ltr24__logreg__notype-nobge__pooled | vs bar_full (n=40, ref 0.522 → 0.393) | **-0.129** [-0.246, -0.023] | 0.033 | ~0.032 | 9/16/15 | -0.125 | -0.125 |
| ltr24__logreg__notype-nobge__pooled | vs exp14 (n=40, ref 0.608 → 0.393) | **-0.214** [-0.335, -0.102] | 0.001 | ~0.001 | 8/22/10 | -0.250 | -0.125 |
| ltr24__logreg__notype-nobge__pooled | vs exp14_cheap (n=40, ref 0.491 → 0.393) | **-0.098** [-0.186, -0.032] | 0.017 | ~0.014 | 7/17/16 | -0.150 | -0.100 |
| ltr24__logreg__notype-nobge__pooled | vs lex13 (n=40, ref 0.391 → 0.393) | +0.002 [-0.087, +0.089] | 0.966 | ~0.967 | 19/7/14 | -0.075 | +0.100 |
| ltr24__logreg__notype-nobge__pooled | vs bm25_01 (n=40, ref 0.339 → 0.393) | +0.054 [-0.027, +0.124] | 0.166 | ~0.172 | 23/5/12 | +0.025 | +0.100 |
| ltr24__logreg__notype-nobge__pooled | vs convex05 (n=40, ref 0.395 → 0.393) | -0.001 [-0.083, +0.068] | 0.976 | ~0.977 | 16/11/13 | -0.025 | +0.075 |
| ltr24__logreg__notype-nobge__pooled | vs convex05+bge@20 (n=40, ref 0.495 → 0.393) | -0.102 [-0.211, -0.010] | 0.056 | ~0.057 | 13/16/11 | -0.175 | +0.025 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.393) | **-0.079** [-0.160, -0.014] | 0.044 | ~0.041 | 9/18/13 | -0.125 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap (n=40, ref 0.427 → 0.393) | -0.034 [-0.103, +0.032] | 0.348 | ~0.350 | 14/13/13 | -0.100 | +0.075 |
| ltr24__logreg__notype-nobge__pooled | vs exp22 gate T25 (n=40, ref 0.628 → 0.393) | **-0.235** [-0.351, -0.133] | 0.000 | ~0.000 | 4/24/12 | -0.225 | -0.200 |
| ltr24__logreg__notype-nobge__pooled | vs exp24 mined-only (same features) (n=40, ref 0.336 → 0.393) | +0.058 [-0.015, +0.135] | 0.144 | ~0.147 | 23/8/9 | +0.025 | +0.075 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.382) | **-0.140** [-0.262, -0.020] | 0.033 | ~0.032 | 9/19/12 | -0.125 | -0.125 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.382) | **-0.140** [-0.262, -0.020] | 0.033 | ~0.032 | 9/19/12 | -0.125 | -0.125 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.382) | **-0.225** [-0.347, -0.107] | 0.001 | ~0.001 | 6/23/11 | -0.250 | -0.125 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.382) | **-0.109** [-0.208, -0.015] | 0.035 | ~0.033 | 8/20/12 | -0.150 | -0.100 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.382) | -0.009 [-0.085, +0.059] | 0.811 | ~0.810 | 18/6/16 | -0.075 | +0.100 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.382) | +0.043 [-0.028, +0.124] | 0.269 | ~0.280 | 22/5/13 | +0.025 | +0.100 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.382) | -0.012 [-0.103, +0.074] | 0.794 | ~0.799 | 15/12/13 | -0.025 | +0.075 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.382) | -0.113 [-0.231, +0.005] | 0.071 | ~0.069 | 13/18/9 | -0.175 | +0.025 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.382) | **-0.090** [-0.175, -0.009] | 0.040 | ~0.037 | 9/20/11 | -0.125 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.382) | -0.045 [-0.110, -0.003] | 0.098 | ~0.099 | 11/13/16 | -0.100 | +0.075 |
| ltr24__logreg__notype-nobge__pooled | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.382) | **-0.246** [-0.361, -0.133] | 0.000 | ~0.000 | 5/25/10 | -0.225 | -0.200 |
| ltr24__lgbm-tiny__small__pooled | vs bar_val (n=40, ref 0.522 → 0.623) | +0.101 [-0.015, +0.220] | 0.111 | ~0.110 | 17/9/14 | +0.175 | +0.050 |
| ltr24__lgbm-tiny__small__pooled | vs bar_full (n=40, ref 0.522 → 0.623) | +0.101 [-0.015, +0.220] | 0.111 | ~0.110 | 17/9/14 | +0.175 | +0.050 |
| ltr24__lgbm-tiny__small__pooled | vs exp14 (n=40, ref 0.608 → 0.623) | +0.015 [-0.060, +0.090] | 0.696 | 0.700 | 12/7/21 | +0.050 | +0.050 |
| ltr24__lgbm-tiny__small__pooled | vs exp14_cheap (n=40, ref 0.491 → 0.623) | **+0.132** [+0.056, +0.229] | 0.005 | ~0.004 | 19/4/17 | +0.150 | +0.075 |
| ltr24__lgbm-tiny__small__pooled | vs lex13 (n=40, ref 0.391 → 0.623) | **+0.231** [+0.111, +0.354] | 0.001 | ~0.001 | 24/3/13 | +0.225 | +0.275 |
| ltr24__lgbm-tiny__small__pooled | vs bm25_01 (n=40, ref 0.339 → 0.623) | **+0.284** [+0.175, +0.403] | 0.000 | ~0.000 | 27/2/11 | +0.325 | +0.275 |
| ltr24__lgbm-tiny__small__pooled | vs convex05 (n=40, ref 0.395 → 0.623) | **+0.228** [+0.130, +0.338] | 0.000 | ~0.000 | 25/5/10 | +0.275 | +0.250 |
| ltr24__lgbm-tiny__small__pooled | vs convex05+bge@20 (n=40, ref 0.495 → 0.623) | **+0.128** [+0.041, +0.240] | 0.015 | ~0.014 | 17/6/17 | +0.125 | +0.200 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.623) | **+0.150** [+0.071, +0.256] | 0.003 | ~0.002 | 17/6/17 | +0.175 | +0.175 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap (n=40, ref 0.427 → 0.623) | **+0.195** [+0.097, +0.310] | 0.001 | ~0.001 | 21/4/15 | +0.200 | +0.250 |
| ltr24__lgbm-tiny__small__pooled | vs exp22 gate T25 (n=40, ref 0.628 → 0.623) | -0.006 [-0.115, +0.102] | 0.919 | ~0.920 | 10/15/15 | +0.075 | -0.025 |
| ltr24__lgbm-tiny__small__pooled | vs exp24 mined-only (same features) (n=40, ref 0.477 → 0.623) | **+0.145** [+0.063, +0.249] | 0.004 | ~0.003 | 21/2/17 | +0.175 | +0.175 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.618) | +0.096 [-0.017, +0.213] | 0.115 | ~0.117 | 15/9/16 | +0.175 | -0.025 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.618) | +0.096 [-0.017, +0.213] | 0.115 | ~0.117 | 15/9/16 | +0.175 | -0.025 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.618) | +0.011 [-0.070, +0.090] | 0.798 | 0.800 | 11/9/20 | +0.050 | -0.025 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.618) | **+0.127** [+0.057, +0.227] | 0.005 | ~0.003 | 16/6/18 | +0.150 | +0.000 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.618) | **+0.227** [+0.129, +0.339] | 0.000 | ~0.000 | 23/2/15 | +0.225 | +0.200 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.618) | **+0.279** [+0.188, +0.385] | 0.000 | ~0.000 | 25/1/14 | +0.325 | +0.200 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.618) | **+0.224** [+0.139, +0.321] | 0.000 | ~0.000 | 24/4/12 | +0.275 | +0.175 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.618) | **+0.123** [+0.042, +0.225] | 0.012 | ~0.010 | 17/7/16 | +0.125 | +0.125 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.618) | **+0.146** [+0.082, +0.241] | 0.001 | ~0.000 | 17/4/19 | +0.175 | +0.100 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.618) | **+0.191** [+0.113, +0.296] | 0.000 | ~0.000 | 21/2/17 | +0.200 | +0.175 |
| ltr24__lgbm-tiny__small__pooled | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.618) | -0.010 [-0.124, +0.099] | 0.861 | ~0.864 | 10/14/16 | +0.075 | -0.100 |
| ltr24__logreg__small__pooled | vs bar_val (n=40, ref 0.522 → 0.550) | +0.028 [-0.071, +0.130] | 0.603 | ~0.616 | 16/9/15 | +0.050 | -0.050 |
| ltr24__logreg__small__pooled | vs bar_full (n=40, ref 0.522 → 0.550) | +0.028 [-0.071, +0.130] | 0.603 | ~0.616 | 16/9/15 | +0.050 | -0.050 |
| ltr24__logreg__small__pooled | vs exp14 (n=40, ref 0.608 → 0.550) | -0.058 [-0.142, +0.017] | 0.162 | ~0.163 | 10/11/19 | -0.075 | -0.050 |
| ltr24__logreg__small__pooled | vs exp14_cheap (n=40, ref 0.491 → 0.550) | +0.059 [-0.022, +0.148] | 0.200 | ~0.204 | 15/10/15 | +0.025 | -0.025 |
| ltr24__logreg__small__pooled | vs lex13 (n=40, ref 0.391 → 0.550) | **+0.159** [+0.052, +0.274] | 0.009 | ~0.009 | 24/5/11 | +0.100 | +0.175 |
| ltr24__logreg__small__pooled | vs bm25_01 (n=40, ref 0.339 → 0.550) | **+0.211** [+0.123, +0.313] | 0.000 | ~0.000 | 27/4/9 | +0.200 | +0.175 |
| ltr24__logreg__small__pooled | vs convex05 (n=40, ref 0.395 → 0.550) | **+0.155** [+0.080, +0.248] | 0.001 | ~0.001 | 21/5/14 | +0.150 | +0.150 |
| ltr24__logreg__small__pooled | vs convex05+bge@20 (n=40, ref 0.495 → 0.550) | +0.055 [-0.038, +0.154] | 0.283 | ~0.286 | 15/8/17 | +0.000 | +0.100 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.550) | +0.078 [-0.008, +0.171] | 0.104 | ~0.110 | 18/7/15 | +0.050 | +0.075 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap (n=40, ref 0.427 → 0.550) | **+0.122** [+0.027, +0.225] | 0.022 | ~0.021 | 22/5/13 | +0.075 | +0.150 |
| ltr24__logreg__small__pooled | vs exp22 gate T25 (n=40, ref 0.628 → 0.550) | -0.079 [-0.175, +0.020] | 0.134 | ~0.133 | 5/18/17 | -0.050 | -0.125 |
| ltr24__logreg__small__pooled | vs exp24 mined-only (same features) (n=40, ref 0.469 → 0.550) | +0.081 [-0.008, +0.182] | 0.105 | ~0.100 | 21/5/14 | +0.025 | +0.100 |
| ltr24__logreg__small__pooled | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.541) | +0.019 [-0.084, +0.112] | 0.718 | ~0.718 | 16/9/15 | +0.050 | -0.075 |
| ltr24__logreg__small__pooled | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.541) | +0.019 [-0.084, +0.112] | 0.718 | ~0.718 | 16/9/15 | +0.050 | -0.075 |
| ltr24__logreg__small__pooled | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.541) | -0.067 [-0.155, +0.012] | 0.125 | ~0.128 | 11/12/17 | -0.075 | -0.075 |
| ltr24__logreg__small__pooled | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.541) | +0.050 [-0.023, +0.123] | 0.196 | ~0.197 | 16/9/15 | +0.025 | -0.050 |
| ltr24__logreg__small__pooled | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.541) | **+0.149** [+0.051, +0.255] | 0.008 | ~0.008 | 23/5/12 | +0.100 | +0.150 |
| ltr24__logreg__small__pooled | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.541) | **+0.202** [+0.117, +0.297] | 0.000 | ~0.000 | 25/4/11 | +0.200 | +0.150 |
| ltr24__logreg__small__pooled | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.541) | **+0.146** [+0.072, +0.229] | 0.001 | ~0.001 | 19/6/15 | +0.150 | +0.125 |
| ltr24__logreg__small__pooled | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.541) | +0.046 [-0.036, +0.123] | 0.278 | ~0.285 | 14/8/18 | +0.000 | +0.075 |
| ltr24__logreg__small__pooled | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.541) | +0.068 [+0.000, +0.140] | 0.068 | ~0.066 | 18/8/14 | +0.050 | +0.050 |
| ltr24__logreg__small__pooled | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.541) | **+0.113** [+0.038, +0.201] | 0.011 | ~0.009 | 21/6/13 | +0.075 | +0.125 |
| ltr24__logreg__small__pooled | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.541) | -0.088 [-0.187, +0.001] | 0.080 | ~0.080 | 6/18/16 | -0.050 | -0.150 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bar_val (n=40, ref 0.522 → 0.601) | +0.079 [-0.022, +0.181] | 0.149 | ~0.148 | 18/6/16 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bar_full (n=40, ref 0.522 → 0.601) | +0.079 [-0.022, +0.181] | 0.149 | ~0.148 | 18/6/16 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp14 (n=40, ref 0.608 → 0.601) | -0.007 [-0.067, +0.057] | 0.827 | 0.837 | 9/8/23 | -0.025 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp14_cheap (n=40, ref 0.491 → 0.601) | **+0.109** [+0.020, +0.216] | 0.037 | ~0.037 | 18/6/16 | +0.075 | +0.075 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs lex13 (n=40, ref 0.391 → 0.601) | **+0.209** [+0.077, +0.334] | 0.003 | ~0.003 | 24/5/11 | +0.150 | +0.275 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs bm25_01 (n=40, ref 0.339 → 0.601) | **+0.262** [+0.159, +0.369] | 0.000 | ~0.000 | 26/2/12 | +0.250 | +0.275 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05 (n=40, ref 0.395 → 0.601) | **+0.206** [+0.116, +0.309] | 0.000 | ~0.000 | 23/4/13 | +0.200 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05+bge@20 (n=40, ref 0.495 → 0.601) | **+0.105** [+0.040, +0.197] | 0.011 | 0.008 | 14/5/21 | +0.050 | +0.200 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.601) | **+0.128** [+0.031, +0.232] | 0.018 | ~0.017 | 17/6/17 | +0.100 | +0.175 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap (n=40, ref 0.427 → 0.601) | **+0.173** [+0.063, +0.285] | 0.005 | ~0.005 | 21/5/14 | +0.125 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp22 gate T25 (n=40, ref 0.628 → 0.601) | -0.028 [-0.124, +0.076] | 0.594 | ~0.595 | 9/15/16 | +0.000 | -0.025 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp24 mined-only (same features) (n=40, ref 0.483 → 0.601) | **+0.117** [+0.005, +0.224] | 0.048 | ~0.048 | 19/5/16 | +0.075 | +0.250 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.554) | +0.033 [-0.085, +0.144] | 0.584 | ~0.589 | 14/10/16 | +0.100 | -0.075 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.554) | +0.033 [-0.085, +0.144] | 0.584 | ~0.589 | 14/10/16 | +0.100 | -0.075 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.554) | -0.053 [-0.157, +0.045] | 0.312 | ~0.310 | 10/12/18 | -0.025 | -0.075 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.554) | +0.063 [+0.010, +0.132] | 0.050 | ~0.048 | 15/7/18 | +0.075 | -0.050 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.554) | **+0.163** [+0.082, +0.266] | 0.001 | ~0.001 | 23/3/14 | +0.150 | +0.150 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.554) | **+0.215** [+0.138, +0.319] | 0.000 | ~0.000 | 25/0/15 | +0.250 | +0.150 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.554) | **+0.160** [+0.092, +0.249] | 0.000 | ~0.000 | 21/5/14 | +0.200 | +0.125 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.554) | +0.059 [-0.034, +0.150] | 0.222 | ~0.228 | 17/8/15 | +0.050 | +0.075 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.554) | **+0.082** [+0.039, +0.150] | 0.005 | 0.002 | 15/3/22 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.554) | **+0.127** [+0.057, +0.218] | 0.004 | ~0.002 | 21/1/18 | +0.125 | +0.125 |
| ltr24__lgbm-tiny__notype__pooled-scored | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.554) | -0.074 [-0.191, +0.031] | 0.204 | ~0.203 | 9/16/15 | +0.000 | -0.150 |
| ltr24__logreg__notype__pooled-scored | vs bar_val (n=40, ref 0.522 → 0.560) | +0.038 [-0.078, +0.154] | 0.526 | ~0.527 | 14/8/18 | +0.050 | +0.050 |
| ltr24__logreg__notype__pooled-scored | vs bar_full (n=40, ref 0.522 → 0.560) | +0.038 [-0.078, +0.154] | 0.526 | ~0.527 | 14/8/18 | +0.050 | +0.050 |
| ltr24__logreg__notype__pooled-scored | vs exp14 (n=40, ref 0.608 → 0.560) | -0.047 [-0.132, +0.020] | 0.229 | 0.233 | 9/10/21 | -0.075 | +0.050 |
| ltr24__logreg__notype__pooled-scored | vs exp14_cheap (n=40, ref 0.491 → 0.560) | +0.069 [-0.026, +0.173] | 0.193 | ~0.194 | 15/11/14 | +0.025 | +0.075 |
| ltr24__logreg__notype__pooled-scored | vs lex13 (n=40, ref 0.391 → 0.560) | **+0.169** [+0.043, +0.298] | 0.015 | ~0.015 | 23/7/10 | +0.100 | +0.275 |
| ltr24__logreg__notype__pooled-scored | vs bm25_01 (n=40, ref 0.339 → 0.560) | **+0.222** [+0.117, +0.337] | 0.000 | ~0.000 | 23/5/12 | +0.200 | +0.275 |
| ltr24__logreg__notype__pooled-scored | vs convex05 (n=40, ref 0.395 → 0.560) | **+0.166** [+0.069, +0.277] | 0.004 | ~0.003 | 19/8/13 | +0.150 | +0.250 |
| ltr24__logreg__notype__pooled-scored | vs convex05+bge@20 (n=40, ref 0.495 → 0.560) | +0.065 [-0.033, +0.178] | 0.238 | ~0.239 | 13/10/17 | +0.000 | +0.200 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.560) | +0.088 [-0.015, +0.199] | 0.118 | ~0.117 | 17/11/12 | +0.050 | +0.175 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap (n=40, ref 0.427 → 0.560) | **+0.133** [+0.033, +0.246] | 0.022 | ~0.019 | 20/6/14 | +0.075 | +0.250 |
| ltr24__logreg__notype__pooled-scored | vs exp22 gate T25 (n=40, ref 0.628 → 0.560) | -0.068 [-0.177, +0.041] | 0.238 | ~0.232 | 10/17/13 | -0.050 | -0.025 |
| ltr24__logreg__notype__pooled-scored | vs exp24 mined-only (same features) (n=40, ref 0.499 → 0.560) | +0.061 [-0.030, +0.162] | 0.226 | ~0.232 | 18/6/16 | -0.025 | +0.175 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.523) | +0.002 [-0.121, +0.115] | 0.981 | ~0.979 | 14/11/15 | +0.050 | -0.075 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.523) | +0.002 [-0.121, +0.115] | 0.981 | ~0.979 | 14/11/15 | +0.050 | -0.075 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.523) | -0.084 [-0.192, +0.020] | 0.135 | ~0.136 | 10/16/14 | -0.075 | -0.075 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.523) | +0.032 [-0.052, +0.115] | 0.458 | ~0.457 | 15/11/14 | +0.025 | -0.050 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.523) | **+0.132** [+0.054, +0.224] | 0.005 | ~0.003 | 22/3/15 | +0.100 | +0.150 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.523) | **+0.185** [+0.105, +0.276] | 0.000 | ~0.000 | 26/3/11 | +0.200 | +0.150 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.523) | **+0.129** [+0.045, +0.222] | 0.008 | ~0.007 | 23/8/9 | +0.150 | +0.125 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.523) | +0.029 [-0.069, +0.123] | 0.569 | ~0.568 | 17/10/13 | +0.000 | +0.075 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.523) | +0.051 [-0.003, +0.118] | 0.106 | ~0.112 | 14/8/18 | +0.050 | +0.050 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.523) | **+0.096** [+0.052, +0.165] | 0.002 | ~0.000 | 19/3/18 | +0.075 | +0.125 |
| ltr24__logreg__notype__pooled-scored | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.523) | -0.105 [-0.224, -0.000] | 0.076 | ~0.075 | 8/17/15 | -0.050 | -0.150 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bar_val (n=40, ref 0.522 → 0.596) | +0.074 [-0.031, +0.182] | 0.188 | ~0.187 | 19/7/14 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bar_full (n=40, ref 0.522 → 0.596) | +0.074 [-0.031, +0.182] | 0.188 | ~0.187 | 19/7/14 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp14 (n=40, ref 0.608 → 0.596) | -0.011 [-0.087, +0.056] | 0.756 | 0.762 | 11/9/20 | -0.025 | +0.050 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp14_cheap (n=40, ref 0.491 → 0.596) | **+0.105** [+0.019, +0.202] | 0.032 | ~0.030 | 19/6/15 | +0.075 | +0.075 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs lex13 (n=40, ref 0.391 → 0.596) | **+0.205** [+0.078, +0.332] | 0.004 | ~0.004 | 23/5/12 | +0.150 | +0.275 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs bm25_01 (n=40, ref 0.339 → 0.596) | **+0.257** [+0.154, +0.370] | 0.000 | ~0.000 | 25/3/12 | +0.250 | +0.275 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05 (n=40, ref 0.395 → 0.596) | **+0.202** [+0.112, +0.312] | 0.000 | ~0.000 | 22/4/14 | +0.200 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05+bge@20 (n=40, ref 0.495 → 0.596) | +0.101 [+0.000, +0.225] | 0.087 | ~0.089 | 15/8/17 | +0.050 | +0.200 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.596) | **+0.124** [+0.026, +0.237] | 0.029 | ~0.026 | 17/6/17 | +0.100 | +0.175 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap (n=40, ref 0.427 → 0.596) | **+0.169** [+0.060, +0.286] | 0.007 | ~0.007 | 21/5/14 | +0.125 | +0.250 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp22 gate T25 (n=40, ref 0.628 → 0.596) | -0.033 [-0.115, +0.060] | 0.481 | ~0.489 | 7/14/19 | +0.000 | -0.025 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp24 mined-only (same features) (n=40, ref 0.493 → 0.596) | +0.102 [-0.009, +0.216] | 0.090 | ~0.091 | 18/5/17 | +0.050 | +0.225 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.546) | +0.025 [-0.091, +0.130] | 0.669 | ~0.667 | 15/10/15 | +0.075 | -0.075 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.546) | +0.025 [-0.091, +0.130] | 0.669 | ~0.667 | 15/10/15 | +0.075 | -0.075 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.546) | -0.061 [-0.164, +0.037] | 0.247 | ~0.251 | 10/13/17 | -0.050 | -0.075 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.546) | +0.055 [-0.009, +0.126] | 0.122 | ~0.123 | 15/8/17 | +0.050 | -0.050 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.546) | **+0.155** [+0.081, +0.248] | 0.001 | ~0.000 | 23/2/15 | +0.125 | +0.150 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.546) | **+0.208** [+0.136, +0.305] | 0.000 | ~0.000 | 26/0/14 | +0.225 | +0.150 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.546) | **+0.152** [+0.086, +0.238] | 0.000 | ~0.000 | 22/4/14 | +0.175 | +0.125 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.546) | +0.051 [-0.036, +0.138] | 0.260 | ~0.265 | 16/8/16 | +0.025 | +0.075 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.546) | **+0.074** [+0.034, +0.141] | 0.007 | 0.002 | 14/3/23 | +0.075 | +0.050 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.546) | **+0.119** [+0.052, +0.202] | 0.004 | ~0.002 | 20/2/18 | +0.100 | +0.125 |
| ltr24__lgbm-tiny__withtype__pooled-scored | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.546) | -0.082 [-0.199, +0.018] | 0.147 | ~0.151 | 8/15/17 | -0.025 | -0.150 |
| ltr24__logreg__withtype__pooled-scored | vs bar_val (n=40, ref 0.522 → 0.578) | +0.056 [-0.075, +0.188] | 0.422 | ~0.418 | 17/10/13 | +0.075 | +0.050 |
| ltr24__logreg__withtype__pooled-scored | vs bar_full (n=40, ref 0.522 → 0.578) | +0.056 [-0.075, +0.188] | 0.422 | ~0.418 | 17/10/13 | +0.075 | +0.050 |
| ltr24__logreg__withtype__pooled-scored | vs exp14 (n=40, ref 0.608 → 0.578) | -0.030 [-0.104, +0.044] | 0.444 | 0.450 | 9/10/21 | -0.050 | +0.050 |
| ltr24__logreg__withtype__pooled-scored | vs exp14_cheap (n=40, ref 0.491 → 0.578) | +0.087 [-0.010, +0.201] | 0.117 | ~0.118 | 15/9/16 | +0.050 | +0.075 |
| ltr24__logreg__withtype__pooled-scored | vs lex13 (n=40, ref 0.391 → 0.578) | **+0.186** [+0.058, +0.317] | 0.009 | ~0.008 | 24/6/10 | +0.125 | +0.275 |
| ltr24__logreg__withtype__pooled-scored | vs bm25_01 (n=40, ref 0.339 → 0.578) | **+0.239** [+0.121, +0.362] | 0.000 | ~0.001 | 24/6/10 | +0.225 | +0.275 |
| ltr24__logreg__withtype__pooled-scored | vs convex05 (n=40, ref 0.395 → 0.578) | **+0.183** [+0.075, +0.302] | 0.003 | ~0.003 | 21/8/11 | +0.175 | +0.250 |
| ltr24__logreg__withtype__pooled-scored | vs convex05+bge@20 (n=40, ref 0.495 → 0.578) | +0.083 [-0.019, +0.199] | 0.152 | ~0.154 | 13/10/17 | +0.025 | +0.200 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.578) | +0.106 [+0.009, +0.222] | 0.063 | ~0.066 | 14/11/15 | +0.075 | +0.175 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap (n=40, ref 0.427 → 0.578) | **+0.150** [+0.055, +0.266] | 0.010 | ~0.010 | 17/7/16 | +0.100 | +0.250 |
| ltr24__logreg__withtype__pooled-scored | vs exp22 gate T25 (n=40, ref 0.628 → 0.578) | -0.051 [-0.171, +0.072] | 0.426 | ~0.431 | 12/15/13 | -0.025 | -0.025 |
| ltr24__logreg__withtype__pooled-scored | vs exp24 mined-only (same features) (n=40, ref 0.476 → 0.578) | +0.102 [+0.001, +0.209] | 0.066 | ~0.067 | 19/4/17 | +0.050 | +0.250 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.526) | +0.004 [-0.122, +0.120] | 0.951 | ~0.951 | 14/11/15 | +0.050 | -0.050 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.526) | +0.004 [-0.122, +0.120] | 0.951 | ~0.951 | 14/11/15 | +0.050 | -0.050 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.526) | -0.082 [-0.184, +0.022] | 0.137 | ~0.134 | 9/15/16 | -0.075 | -0.050 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.526) | +0.035 [-0.049, +0.120] | 0.430 | ~0.430 | 13/11/16 | +0.025 | -0.025 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.526) | **+0.135** [+0.053, +0.228] | 0.005 | ~0.005 | 22/4/14 | +0.100 | +0.175 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.526) | **+0.187** [+0.106, +0.278] | 0.000 | ~0.000 | 24/4/12 | +0.200 | +0.175 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.526) | **+0.131** [+0.043, +0.226] | 0.009 | ~0.008 | 20/9/11 | +0.150 | +0.150 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.526) | +0.031 [-0.068, +0.128] | 0.548 | ~0.551 | 15/11/14 | +0.000 | +0.100 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.526) | +0.054 [-0.003, +0.123] | 0.107 | ~0.111 | 13/8/19 | +0.050 | +0.075 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.526) | **+0.099** [+0.049, +0.169] | 0.003 | ~0.001 | 18/3/19 | +0.075 | +0.150 |
| ltr24__logreg__withtype__pooled-scored | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.526) | -0.103 [-0.223, +0.004] | 0.091 | ~0.089 | 7/17/16 | -0.050 | -0.125 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bar_val (n=40, ref 0.522 → 0.620) | +0.098 [-0.000, +0.199] | 0.066 | ~0.066 | 17/4/19 | +0.125 | +0.075 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bar_full (n=40, ref 0.522 → 0.620) | +0.098 [-0.000, +0.199] | 0.066 | ~0.066 | 17/4/19 | +0.125 | +0.075 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp14 (n=40, ref 0.608 → 0.620) | +0.012 [-0.068, +0.088] | 0.763 | 0.765 | 11/7/22 | +0.000 | +0.075 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp14_cheap (n=40, ref 0.491 → 0.620) | **+0.129** [+0.046, +0.232] | 0.011 | ~0.008 | 18/5/17 | +0.100 | +0.100 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs lex13 (n=40, ref 0.391 → 0.620) | **+0.228** [+0.096, +0.361] | 0.002 | ~0.002 | 24/5/11 | +0.175 | +0.300 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs bm25_01 (n=40, ref 0.339 → 0.620) | **+0.281** [+0.182, +0.396] | 0.000 | ~0.000 | 26/1/13 | +0.275 | +0.300 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05 (n=40, ref 0.395 → 0.620) | **+0.225** [+0.136, +0.342] | 0.000 | ~0.000 | 22/3/15 | +0.225 | +0.275 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05+bge@20 (n=40, ref 0.495 → 0.620) | **+0.125** [+0.034, +0.240] | 0.023 | ~0.020 | 17/6/17 | +0.075 | +0.225 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.620) | **+0.147** [+0.051, +0.256] | 0.008 | ~0.007 | 19/6/15 | +0.125 | +0.200 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=40, ref 0.427 → 0.620) | **+0.192** [+0.078, +0.314] | 0.003 | ~0.003 | 23/6/11 | +0.150 | +0.275 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp22 gate T25 (n=40, ref 0.628 → 0.620) | -0.009 [-0.093, +0.084] | 0.851 | ~0.851 | 8/13/19 | +0.025 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=40, ref 0.528 → 0.620) | +0.092 [-0.025, +0.210] | 0.144 | ~0.144 | 18/7/15 | +0.025 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.614) | +0.091 [-0.016, +0.202] | 0.117 | ~0.116 | 17/7/16 | +0.150 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.614) | +0.091 [-0.016, +0.202] | 0.117 | ~0.116 | 17/7/16 | +0.150 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.614) | +0.006 [-0.086, +0.085] | 0.892 | ~0.897 | 12/9/19 | +0.025 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.614) | **+0.122** [+0.051, +0.211] | 0.005 | ~0.003 | 18/6/16 | +0.125 | +0.075 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.614) | **+0.222** [+0.112, +0.345] | 0.001 | ~0.000 | 24/4/12 | +0.200 | +0.275 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.614) | **+0.275** [+0.178, +0.388] | 0.000 | ~0.000 | 26/0/14 | +0.300 | +0.275 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.614) | **+0.219** [+0.131, +0.324] | 0.000 | ~0.000 | 22/4/14 | +0.250 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.614) | **+0.118** [+0.022, +0.234] | 0.035 | ~0.032 | 16/8/16 | +0.100 | +0.200 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.614) | **+0.141** [+0.067, +0.240] | 0.003 | ~0.002 | 20/3/17 | +0.150 | +0.175 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.614) | **+0.186** [+0.100, +0.295] | 0.001 | ~0.000 | 23/2/15 | +0.175 | +0.250 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.614) | -0.015 [-0.121, +0.090] | 0.787 | ~0.787 | 11/13/16 | +0.050 | -0.025 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bar_val (n=40, ref 0.522 → 0.530) | +0.008 [-0.109, +0.127] | 0.897 | ~0.898 | 14/12/14 | +0.000 | +0.050 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bar_full (n=40, ref 0.522 → 0.530) | +0.008 [-0.109, +0.127] | 0.897 | ~0.898 | 14/12/14 | +0.000 | +0.050 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp14 (n=40, ref 0.608 → 0.530) | -0.077 [-0.164, -0.010] | 0.054 | 0.053 | 8/12/20 | -0.125 | +0.050 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp14_cheap (n=40, ref 0.491 → 0.530) | +0.039 [-0.049, +0.142] | 0.439 | ~0.443 | 15/11/14 | -0.025 | +0.075 |
| ltr24__logreg__notype-nogate__pooled-scored | vs lex13 (n=40, ref 0.391 → 0.530) | **+0.139** [+0.011, +0.262] | 0.042 | ~0.043 | 22/7/11 | +0.050 | +0.275 |
| ltr24__logreg__notype-nogate__pooled-scored | vs bm25_01 (n=40, ref 0.339 → 0.530) | **+0.191** [+0.092, +0.296] | 0.001 | ~0.001 | 23/7/10 | +0.150 | +0.275 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05 (n=40, ref 0.395 → 0.530) | **+0.136** [+0.037, +0.249] | 0.019 | ~0.018 | 19/9/12 | +0.100 | +0.250 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05+bge@20 (n=40, ref 0.495 → 0.530) | +0.035 [-0.065, +0.148] | 0.531 | ~0.541 | 11/10/19 | -0.050 | +0.200 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.530) | +0.058 [-0.038, +0.164] | 0.277 | ~0.274 | 13/11/16 | +0.000 | +0.175 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=40, ref 0.427 → 0.530) | +0.103 [-0.007, +0.214] | 0.085 | ~0.086 | 19/8/13 | +0.025 | +0.250 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp22 gate T25 (n=40, ref 0.628 → 0.530) | -0.098 [-0.201, +0.011] | 0.085 | ~0.082 | 9/19/12 | -0.100 | -0.025 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=40, ref 0.524 → 0.530) | +0.006 [-0.106, +0.112] | 0.919 | ~0.921 | 14/9/17 | -0.100 | +0.175 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.508) | -0.014 [-0.132, +0.094] | 0.810 | ~0.807 | 14/10/16 | +0.000 | -0.050 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.508) | -0.014 [-0.132, +0.094] | 0.810 | ~0.807 | 14/10/16 | +0.000 | -0.050 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.508) | -0.100 [-0.202, +0.001] | 0.065 | ~0.066 | 10/16/14 | -0.125 | -0.050 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.508) | +0.017 [-0.070, +0.103] | 0.710 | ~0.711 | 15/12/13 | -0.025 | -0.025 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.508) | **+0.116** [+0.032, +0.211] | 0.016 | ~0.015 | 22/4/14 | +0.050 | +0.175 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.508) | **+0.169** [+0.095, +0.255] | 0.000 | ~0.000 | 26/3/11 | +0.150 | +0.175 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.508) | **+0.113** [+0.031, +0.206] | 0.017 | ~0.017 | 22/8/10 | +0.100 | +0.150 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.508) | +0.013 [-0.080, +0.101] | 0.787 | ~0.787 | 15/10/15 | -0.050 | +0.100 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.508) | +0.035 [-0.026, +0.097] | 0.270 | ~0.274 | 14/8/18 | +0.000 | +0.075 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.508) | **+0.080** [+0.005, +0.154] | 0.044 | ~0.044 | 21/4/15 | +0.025 | +0.150 |
| ltr24__logreg__notype-nogate__pooled-scored | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.508) | **-0.121** [-0.235, -0.019] | 0.037 | ~0.036 | 8/18/14 | -0.100 | -0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bar_val (n=40, ref 0.522 → 0.446) | -0.076 [-0.187, +0.024] | 0.170 | ~0.173 | 10/14/16 | -0.050 | -0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bar_full (n=40, ref 0.522 → 0.446) | -0.076 [-0.187, +0.024] | 0.170 | ~0.173 | 10/14/16 | -0.050 | -0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp14 (n=40, ref 0.608 → 0.446) | **-0.162** [-0.273, -0.070] | 0.004 | ~0.004 | 6/18/16 | -0.175 | -0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp14_cheap (n=40, ref 0.491 → 0.446) | -0.045 [-0.116, +0.008] | 0.158 | ~0.165 | 9/15/16 | -0.075 | -0.025 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs lex13 (n=40, ref 0.391 → 0.446) | +0.054 [-0.048, +0.144] | 0.282 | ~0.281 | 20/7/13 | +0.000 | +0.175 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs bm25_01 (n=40, ref 0.339 → 0.446) | **+0.107** [+0.044, +0.183] | 0.005 | ~0.004 | 22/5/13 | +0.100 | +0.175 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05 (n=40, ref 0.395 → 0.446) | +0.051 [-0.015, +0.123] | 0.162 | ~0.164 | 17/7/16 | +0.050 | +0.150 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05+bge@20 (n=40, ref 0.495 → 0.446) | -0.049 [-0.155, +0.038] | 0.332 | ~0.334 | 13/12/15 | -0.100 | +0.100 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.446) | -0.026 [-0.100, +0.033] | 0.441 | ~0.454 | 11/12/17 | -0.050 | +0.075 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=40, ref 0.427 → 0.446) | +0.018 [-0.074, +0.099] | 0.681 | ~0.688 | 16/9/15 | -0.025 | +0.150 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp22 gate T25 (n=40, ref 0.628 → 0.446) | **-0.182** [-0.283, -0.086] | 0.001 | ~0.001 | 4/24/12 | -0.150 | -0.125 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=40, ref 0.432 → 0.446) | +0.014 [-0.078, +0.094] | 0.756 | ~0.757 | 16/9/15 | -0.025 | +0.150 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.420) | -0.102 [-0.231, +0.027] | 0.131 | ~0.130 | 11/18/11 | -0.050 | -0.175 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.420) | -0.102 [-0.231, +0.027] | 0.131 | ~0.130 | 11/18/11 | -0.050 | -0.175 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.420) | **-0.187** [-0.320, -0.060] | 0.008 | ~0.007 | 8/20/12 | -0.175 | -0.175 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.420) | -0.071 [-0.164, +0.014] | 0.138 | ~0.140 | 7/19/14 | -0.075 | -0.150 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.420) | +0.029 [-0.029, +0.092] | 0.355 | ~0.368 | 19/6/15 | +0.000 | +0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.420) | **+0.082** [+0.017, +0.162] | 0.032 | ~0.029 | 22/4/14 | +0.100 | +0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.420) | +0.026 [-0.071, +0.118] | 0.597 | ~0.596 | 17/11/12 | +0.050 | +0.025 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.420) | -0.074 [-0.191, +0.034] | 0.203 | ~0.204 | 15/14/11 | -0.100 | -0.025 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.420) | -0.052 [-0.120, +0.002] | 0.102 | ~0.098 | 8/15/17 | -0.050 | -0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.420) | -0.007 [-0.068, +0.032] | 0.785 | 0.891 | 11/6/23 | -0.025 | +0.025 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.420) | **-0.208** [-0.328, -0.092] | 0.002 | ~0.002 | 6/23/11 | -0.150 | -0.250 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bar_val (n=40, ref 0.522 → 0.440) | -0.083 [-0.192, +0.020] | 0.142 | ~0.145 | 11/14/15 | -0.050 | -0.100 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bar_full (n=40, ref 0.522 → 0.440) | -0.083 [-0.192, +0.020] | 0.142 | ~0.145 | 11/14/15 | -0.050 | -0.100 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp14 (n=40, ref 0.608 → 0.440) | **-0.168** [-0.283, -0.074] | 0.003 | ~0.002 | 6/18/16 | -0.175 | -0.100 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp14_cheap (n=40, ref 0.491 → 0.440) | -0.052 [-0.118, +0.003] | 0.104 | ~0.108 | 8/14/18 | -0.075 | -0.075 |
| ltr24__logreg__notype-nobge__pooled-scored | vs lex13 (n=40, ref 0.391 → 0.440) | +0.048 [-0.057, +0.143] | 0.362 | ~0.368 | 22/7/11 | +0.000 | +0.125 |
| ltr24__logreg__notype-nobge__pooled-scored | vs bm25_01 (n=40, ref 0.339 → 0.440) | **+0.101** [+0.028, +0.186] | 0.018 | ~0.015 | 21/6/13 | +0.100 | +0.125 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05 (n=40, ref 0.395 → 0.440) | +0.045 [-0.020, +0.128] | 0.248 | ~0.251 | 16/7/17 | +0.050 | +0.100 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05+bge@20 (n=40, ref 0.495 → 0.440) | -0.056 [-0.155, +0.018] | 0.214 | ~0.223 | 12/11/17 | -0.100 | +0.050 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.440) | -0.033 [-0.104, +0.019] | 0.298 | ~0.313 | 7/14/19 | -0.050 | +0.025 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=40, ref 0.427 → 0.440) | +0.012 [-0.071, +0.093] | 0.781 | ~0.781 | 17/9/14 | -0.025 | +0.100 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp22 gate T25 (n=40, ref 0.628 → 0.440) | **-0.189** [-0.300, -0.087] | 0.001 | ~0.001 | 4/23/13 | -0.150 | -0.175 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=40, ref 0.336 → 0.440) | **+0.104** [+0.005, +0.197] | 0.043 | ~0.041 | 26/7/7 | +0.100 | +0.100 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.415) | -0.107 [-0.228, +0.012] | 0.094 | ~0.097 | 10/18/12 | -0.075 | -0.150 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.415) | -0.107 [-0.228, +0.012] | 0.094 | ~0.097 | 10/18/12 | -0.075 | -0.150 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.415) | **-0.192** [-0.316, -0.074] | 0.004 | ~0.004 | 6/21/13 | -0.200 | -0.150 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.415) | -0.076 [-0.173, +0.016] | 0.129 | ~0.127 | 9/19/12 | -0.100 | -0.125 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.415) | +0.024 [-0.033, +0.082] | 0.427 | ~0.441 | 18/5/17 | -0.025 | +0.075 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.415) | **+0.076** [+0.017, +0.159] | 0.036 | ~0.033 | 22/4/14 | +0.075 | +0.075 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.415) | +0.021 [-0.061, +0.106] | 0.632 | ~0.633 | 15/11/14 | +0.025 | +0.050 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.415) | -0.080 [-0.195, +0.038] | 0.192 | ~0.194 | 13/17/10 | -0.125 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.415) | -0.057 [-0.128, +0.018] | 0.135 | ~0.134 | 7/19/14 | -0.075 | -0.025 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.415) | -0.012 [-0.072, +0.033] | 0.654 | ~0.653 | 10/11/19 | -0.050 | +0.050 |
| ltr24__logreg__notype-nobge__pooled-scored | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.415) | **-0.213** [-0.328, -0.107] | 0.001 | ~0.001 | 5/23/12 | -0.175 | -0.225 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bar_val (n=40, ref 0.522 → 0.597) | +0.075 [-0.037, +0.187] | 0.204 | ~0.203 | 17/8/15 | +0.075 | +0.050 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bar_full (n=40, ref 0.522 → 0.597) | +0.075 [-0.037, +0.187] | 0.204 | ~0.203 | 17/8/15 | +0.075 | +0.050 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp14 (n=40, ref 0.608 → 0.597) | -0.010 [-0.085, +0.067] | 0.793 | 0.791 | 9/9/22 | -0.050 | +0.050 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp14_cheap (n=40, ref 0.491 → 0.597) | **+0.106** [+0.010, +0.210] | 0.046 | ~0.047 | 18/6/16 | +0.050 | +0.075 |
| ltr24__lgbm-tiny__small__pooled-scored | vs lex13 (n=40, ref 0.391 → 0.597) | **+0.206** [+0.086, +0.318] | 0.002 | ~0.001 | 24/4/12 | +0.125 | +0.275 |
| ltr24__lgbm-tiny__small__pooled-scored | vs bm25_01 (n=40, ref 0.339 → 0.597) | **+0.258** [+0.160, +0.362] | 0.000 | ~0.000 | 25/3/12 | +0.225 | +0.275 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05 (n=40, ref 0.395 → 0.597) | **+0.203** [+0.119, +0.303] | 0.000 | ~0.000 | 21/4/15 | +0.175 | +0.250 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05+bge@20 (n=40, ref 0.495 → 0.597) | **+0.102** [+0.016, +0.204] | 0.042 | ~0.041 | 14/7/19 | +0.025 | +0.200 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.597) | **+0.125** [+0.034, +0.224] | 0.016 | ~0.015 | 17/6/17 | +0.075 | +0.175 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap (n=40, ref 0.427 → 0.597) | **+0.170** [+0.065, +0.279] | 0.004 | ~0.003 | 20/6/14 | +0.100 | +0.250 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp22 gate T25 (n=40, ref 0.628 → 0.597) | -0.031 [-0.133, +0.072] | 0.563 | ~0.563 | 10/14/16 | -0.025 | -0.025 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp24 mined-only (same features) (n=40, ref 0.477 → 0.597) | **+0.120** [+0.029, +0.212] | 0.016 | ~0.015 | 20/5/15 | +0.075 | +0.175 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.551) | +0.029 [-0.090, +0.142] | 0.636 | ~0.639 | 14/11/15 | +0.075 | -0.075 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.551) | +0.029 [-0.090, +0.142] | 0.636 | ~0.639 | 14/11/15 | +0.075 | -0.075 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.551) | -0.057 [-0.155, +0.042] | 0.277 | ~0.285 | 10/14/16 | -0.050 | -0.075 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.551) | +0.060 [-0.016, +0.142] | 0.150 | ~0.151 | 15/8/17 | +0.050 | -0.050 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.551) | **+0.160** [+0.066, +0.270] | 0.004 | ~0.003 | 22/3/15 | +0.125 | +0.150 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.551) | **+0.212** [+0.134, +0.310] | 0.000 | ~0.000 | 26/0/14 | +0.225 | +0.150 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.551) | **+0.157** [+0.090, +0.234] | 0.000 | ~0.000 | 22/6/12 | +0.175 | +0.125 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.551) | +0.056 [-0.025, +0.146] | 0.217 | ~0.219 | 16/10/14 | +0.025 | +0.075 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.551) | **+0.079** [+0.010, +0.154] | 0.043 | ~0.043 | 16/7/17 | +0.075 | +0.050 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.551) | **+0.124** [+0.053, +0.210] | 0.004 | ~0.002 | 18/6/16 | +0.100 | +0.125 |
| ltr24__lgbm-tiny__small__pooled-scored | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.551) | -0.077 [-0.196, +0.030] | 0.194 | ~0.195 | 8/17/15 | -0.025 | -0.150 |
| ltr24__logreg__small__pooled-scored | vs bar_val (n=40, ref 0.522 → 0.592) | +0.070 [-0.032, +0.177] | 0.215 | ~0.216 | 17/7/16 | +0.125 | +0.025 |
| ltr24__logreg__small__pooled-scored | vs bar_full (n=40, ref 0.522 → 0.592) | +0.070 [-0.032, +0.177] | 0.215 | ~0.216 | 17/7/16 | +0.125 | +0.025 |
| ltr24__logreg__small__pooled-scored | vs exp14 (n=40, ref 0.608 → 0.592) | -0.015 [-0.092, +0.057] | 0.692 | 0.695 | 10/10/20 | +0.000 | +0.025 |
| ltr24__logreg__small__pooled-scored | vs exp14_cheap (n=40, ref 0.491 → 0.592) | **+0.101** [+0.018, +0.207] | 0.048 | ~0.047 | 17/7/16 | +0.100 | +0.050 |
| ltr24__logreg__small__pooled-scored | vs lex13 (n=40, ref 0.391 → 0.592) | **+0.201** [+0.073, +0.334] | 0.005 | ~0.006 | 24/5/11 | +0.175 | +0.250 |
| ltr24__logreg__small__pooled-scored | vs bm25_01 (n=40, ref 0.339 → 0.592) | **+0.253** [+0.148, +0.372] | 0.000 | ~0.000 | 26/5/9 | +0.275 | +0.250 |
| ltr24__logreg__small__pooled-scored | vs convex05 (n=40, ref 0.395 → 0.592) | **+0.198** [+0.109, +0.303] | 0.000 | ~0.000 | 21/5/14 | +0.225 | +0.225 |
| ltr24__logreg__small__pooled-scored | vs convex05+bge@20 (n=40, ref 0.495 → 0.592) | +0.097 [+0.000, +0.206] | 0.077 | ~0.076 | 16/6/18 | +0.075 | +0.175 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.592) | **+0.120** [+0.021, +0.224] | 0.032 | ~0.031 | 18/6/16 | +0.125 | +0.150 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap (n=40, ref 0.427 → 0.592) | **+0.165** [+0.051, +0.282] | 0.009 | ~0.009 | 22/5/13 | +0.150 | +0.225 |
| ltr24__logreg__small__pooled-scored | vs exp22 gate T25 (n=40, ref 0.628 → 0.592) | -0.036 [-0.132, +0.060] | 0.481 | ~0.485 | 8/14/18 | +0.025 | -0.050 |
| ltr24__logreg__small__pooled-scored | vs exp24 mined-only (same features) (n=40, ref 0.469 → 0.592) | **+0.123** [+0.021, +0.234] | 0.030 | ~0.028 | 20/5/15 | +0.100 | +0.175 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs bar_val (n=40, ref 0.522 → 0.537) | +0.015 [-0.092, +0.108] | 0.780 | ~0.785 | 14/9/17 | +0.075 | -0.075 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs bar_full (n=40, ref 0.522 → 0.537) | +0.015 [-0.092, +0.108] | 0.780 | ~0.785 | 14/9/17 | +0.075 | -0.075 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs exp14 (n=40, ref 0.608 → 0.537) | -0.071 [-0.173, +0.024] | 0.168 | ~0.169 | 10/13/17 | -0.050 | -0.075 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs exp14_cheap (n=40, ref 0.491 → 0.537) | +0.046 [-0.029, +0.135] | 0.287 | ~0.293 | 15/9/16 | +0.050 | -0.050 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs lex13 (n=40, ref 0.391 → 0.537) | **+0.145** [+0.046, +0.258] | 0.012 | ~0.011 | 23/5/12 | +0.125 | +0.150 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs bm25_01 (n=40, ref 0.339 → 0.537) | **+0.198** [+0.111, +0.300] | 0.000 | ~0.000 | 25/4/11 | +0.225 | +0.150 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs convex05 (n=40, ref 0.395 → 0.537) | **+0.142** [+0.066, +0.233] | 0.002 | ~0.002 | 19/7/14 | +0.175 | +0.125 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs convex05+bge@20 (n=40, ref 0.495 → 0.537) | +0.042 [-0.033, +0.109] | 0.265 | ~0.269 | 14/7/19 | +0.025 | +0.075 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs exp21-ranker cheap+bge (n=40, ref 0.472 → 0.537) | +0.064 [-0.004, +0.144] | 0.098 | ~0.096 | 18/8/14 | +0.075 | +0.050 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs exp21-ranker cheap (n=40, ref 0.427 → 0.537) | **+0.109** [+0.032, +0.200] | 0.016 | ~0.014 | 19/8/13 | +0.100 | +0.125 |
| ltr24__logreg__small__pooled-scored | [all-mined oof] vs exp22 gate T25 (n=40, ref 0.628 → 0.537) | -0.092 [-0.200, +0.002] | 0.082 | ~0.079 | 5/17/18 | -0.025 | -0.150 |

**Mined val split – paired tests (Δ = exp-24 fit A − reference)**

| run | reference  Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 | Δ H@10 |
|---|---|:--|--:|--:|:--|--:|--:|
| ltr24__lgbm-tiny__notype__mined | vs convex05 (n=159, ref 0.401 → 0.478) | **+0.077** [+0.048, +0.115] | 0.000 | ~0.000 | 58/19/82 | +0.088 | +0.063 |
| ltr24__lgbm-tiny__notype__mined | vs exp13_lex (n=159, ref 0.428 → 0.478) | **+0.050** [+0.015, +0.087] | 0.008 | ~0.007 | 52/23/84 | +0.069 | +0.044 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.585) | +0.035 [-0.002, +0.081] | 0.101 | ~0.102 | 22/8/52 | +0.024 | +0.049 |
| ltr24__lgbm-tiny__notype__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.478) | -0.009 [-0.025, +0.000] | 0.144 | ~0.153 | 24/17/118 | -0.019 | +0.006 |
| ltr24__lgbm-tiny__notype__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.585) | **+0.073** [+0.025, +0.127] | 0.007 | ~0.006 | 29/9/44 | +0.098 | +0.024 |
| ltr24__logreg__notype__mined | vs convex05 (n=159, ref 0.401 → 0.431) | +0.030 [-0.000, +0.061] | 0.056 | ~0.057 | 55/23/81 | +0.013 | +0.057 |
| ltr24__logreg__notype__mined | vs exp13_lex (n=159, ref 0.428 → 0.431) | +0.003 [-0.028, +0.033] | 0.832 | ~0.834 | 44/32/83 | -0.006 | +0.038 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.529) | -0.021 [-0.066, +0.017] | 0.322 | ~0.330 | 18/15/49 | -0.073 | +0.037 |
| ltr24__logreg__notype__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.431) | **-0.056** [-0.088, -0.030] | 0.000 | ~0.000 | 30/43/86 | -0.094 | +0.000 |
| ltr24__logreg__notype__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.529) | +0.016 [-0.027, +0.054] | 0.428 | ~0.430 | 26/11/45 | +0.000 | +0.012 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05 (n=159, ref 0.401 → 0.483) | **+0.082** [+0.051, +0.121] | 0.000 | ~0.000 | 59/18/82 | +0.101 | +0.063 |
| ltr24__lgbm-tiny__withtype__mined | vs exp13_lex (n=159, ref 0.428 → 0.483) | **+0.055** [+0.019, +0.092] | 0.004 | ~0.004 | 53/23/83 | +0.082 | +0.044 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.589) | +0.039 [+0.005, +0.085] | 0.056 | ~0.055 | 20/8/54 | +0.037 | +0.049 |
| ltr24__lgbm-tiny__withtype__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.483) | -0.004 [-0.017, +0.001] | 0.319 | ~0.401 | 22/12/125 | -0.006 | +0.006 |
| ltr24__lgbm-tiny__withtype__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.589) | **+0.077** [+0.026, +0.132] | 0.005 | ~0.005 | 30/9/43 | +0.110 | +0.024 |
| ltr24__logreg__withtype__mined | vs convex05 (n=159, ref 0.401 → 0.446) | **+0.044** [+0.012, +0.078] | 0.010 | ~0.010 | 59/20/80 | +0.031 | +0.075 |
| ltr24__logreg__withtype__mined | vs exp13_lex (n=159, ref 0.428 → 0.446) | +0.018 [-0.011, +0.045] | 0.223 | ~0.223 | 49/23/87 | +0.013 | +0.057 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.537) | -0.013 [-0.064, +0.033] | 0.605 | ~0.615 | 24/11/47 | -0.061 | +0.049 |
| ltr24__logreg__withtype__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.446) | **-0.041** [-0.074, -0.016] | 0.006 | ~0.006 | 36/34/89 | -0.075 | +0.019 |
| ltr24__logreg__withtype__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.537) | +0.025 [-0.024, +0.070] | 0.301 | ~0.309 | 28/10/44 | +0.012 | +0.024 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05 (n=159, ref 0.401 → 0.479) | **+0.078** [+0.048, +0.116] | 0.000 | ~0.000 | 57/21/81 | +0.094 | +0.050 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp13_lex (n=159, ref 0.428 → 0.479) | **+0.051** [+0.016, +0.087] | 0.007 | ~0.005 | 51/22/86 | +0.075 | +0.031 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.590) | +0.040 [+0.005, +0.085] | 0.054 | ~0.052 | 22/7/53 | +0.037 | +0.024 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.479) | -0.008 [-0.023, -0.000] | 0.143 | ~0.165 | 21/17/121 | -0.013 | -0.006 |
| ltr24__lgbm-tiny__notype-nogate__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.590) | **+0.078** [+0.026, +0.132] | 0.005 | ~0.003 | 30/10/42 | +0.110 | +0.000 |
| ltr24__logreg__notype-nogate__mined | vs convex05 (n=159, ref 0.401 → 0.434) | +0.033 [-0.001, +0.066] | 0.057 | ~0.057 | 55/25/79 | +0.025 | +0.044 |
| ltr24__logreg__notype-nogate__mined | vs exp13_lex (n=159, ref 0.428 → 0.434) | +0.006 [-0.025, +0.035] | 0.705 | ~0.707 | 44/33/82 | +0.006 | +0.025 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.531) | -0.019 [-0.067, +0.024] | 0.413 | ~0.424 | 19/15/48 | -0.061 | +0.037 |
| ltr24__logreg__notype-nogate__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.434) | **-0.053** [-0.084, -0.031] | 0.000 | ~0.000 | 26/43/90 | -0.082 | -0.013 |
| ltr24__logreg__notype-nogate__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.531) | +0.019 [-0.026, +0.061] | 0.406 | ~0.411 | 26/13/43 | +0.012 | +0.012 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05 (n=159, ref 0.401 → 0.479) | **+0.078** [+0.048, +0.116] | 0.000 | ~0.000 | 52/24/83 | +0.094 | +0.063 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp13_lex (n=159, ref 0.428 → 0.479) | **+0.051** [+0.016, +0.087] | 0.007 | ~0.006 | 50/26/83 | +0.075 | +0.044 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.589) | +0.039 [-0.003, +0.085] | 0.095 | ~0.098 | 23/9/50 | +0.037 | +0.049 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.479) | -0.008 [-0.023, -0.001] | 0.115 | ~0.116 | 17/21/121 | -0.013 | +0.006 |
| ltr24__lgbm-tiny__notype-nobge__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.589) | **+0.076** [+0.018, +0.137] | 0.013 | ~0.013 | 25/13/44 | +0.110 | +0.024 |
| ltr24__logreg__notype-nobge__mined | vs convex05 (n=159, ref 0.401 → 0.440) | **+0.039** [+0.005, +0.074] | 0.027 | ~0.024 | 53/26/80 | +0.031 | +0.044 |
| ltr24__logreg__notype-nobge__mined | vs exp13_lex (n=159, ref 0.428 → 0.440) | +0.012 [-0.017, +0.041] | 0.418 | ~0.421 | 48/29/82 | +0.013 | +0.025 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.533) | -0.017 [-0.074, +0.036] | 0.557 | ~0.563 | 19/19/44 | -0.061 | +0.012 |
| ltr24__logreg__notype-nobge__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.440) | **-0.047** [-0.080, -0.021] | 0.002 | ~0.002 | 28/42/89 | -0.075 | -0.013 |
| ltr24__logreg__notype-nobge__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.533) | +0.021 [-0.040, +0.077] | 0.479 | ~0.480 | 25/17/40 | +0.012 | -0.012 |
| ltr24__lgbm-tiny__small__mined | vs convex05 (n=159, ref 0.401 → 0.474) | **+0.073** [+0.041, +0.112] | 0.000 | ~0.000 | 59/17/83 | +0.082 | +0.038 |
| ltr24__lgbm-tiny__small__mined | vs exp13_lex (n=159, ref 0.428 → 0.474) | **+0.046** [+0.011, +0.084] | 0.015 | ~0.015 | 53/24/82 | +0.063 | +0.019 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.585) | +0.035 [+0.002, +0.081] | 0.087 | ~0.086 | 19/11/52 | +0.024 | +0.012 |
| ltr24__lgbm-tiny__small__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.474) | -0.013 [-0.031, +0.007] | 0.194 | ~0.200 | 23/30/106 | -0.025 | -0.019 |
| ltr24__lgbm-tiny__small__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.585) | **+0.072** [+0.030, +0.125] | 0.003 | ~0.003 | 26/10/46 | +0.098 | -0.012 |
| ltr24__logreg__small__mined | vs convex05 (n=159, ref 0.401 → 0.441) | **+0.039** [+0.007, +0.072] | 0.018 | ~0.017 | 56/23/80 | +0.025 | +0.069 |
| ltr24__logreg__small__mined | vs exp13_lex (n=159, ref 0.428 → 0.441) | +0.013 [-0.022, +0.044] | 0.460 | ~0.461 | 45/31/83 | +0.006 | +0.050 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.538) | -0.012 [-0.056, +0.029] | 0.576 | ~0.584 | 21/17/44 | -0.049 | +0.037 |
| ltr24__logreg__small__mined | vs exp21-ranker cheap (n=159, ref 0.487 → 0.441) | **-0.046** [-0.078, -0.021] | 0.002 | ~0.001 | 37/37/85 | -0.082 | +0.013 |
| ltr24__logreg__small__mined | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.538) | +0.026 [-0.024, +0.075] | 0.314 | ~0.321 | 28/12/42 | +0.024 | +0.012 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05 (n=159, ref 0.401 → 0.452) | **+0.051** [+0.017, +0.089] | 0.006 | ~0.005 | 51/27/81 | +0.057 | +0.057 |
| ltr24__lgbm-tiny__notype__pooled | vs exp13_lex (n=159, ref 0.428 → 0.452) | +0.024 [-0.014, +0.062] | 0.218 | ~0.217 | 45/37/77 | +0.038 | +0.038 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.548) | -0.002 [-0.033, +0.029] | 0.914 | ~0.913 | 15/13/54 | -0.024 | +0.061 |
| ltr24__lgbm-tiny__notype__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.452) | **-0.035** [-0.065, -0.007] | 0.018 | ~0.017 | 18/50/91 | -0.050 | +0.000 |
| ltr24__lgbm-tiny__notype__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.548) | +0.036 [-0.007, +0.086] | 0.133 | ~0.137 | 24/13/45 | +0.049 | +0.037 |
| ltr24__lgbm-tiny__notype__pooled | vs exp24 mined-only (same features) (n=159, ref 0.478 → 0.452) | **-0.026** [-0.051, -0.004] | 0.036 | ~0.033 | 18/47/94 | -0.031 | -0.006 |
| ltr24__logreg__notype__pooled | vs convex05 (n=159, ref 0.401 → 0.434) | +0.032 [-0.005, +0.071] | 0.098 | ~0.097 | 48/32/79 | +0.031 | +0.038 |
| ltr24__logreg__notype__pooled | vs exp13_lex (n=159, ref 0.428 → 0.434) | +0.005 [-0.033, +0.045] | 0.783 | ~0.783 | 42/37/80 | +0.013 | +0.019 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.530) | -0.020 [-0.058, +0.010] | 0.253 | ~0.256 | 19/15/48 | -0.061 | +0.049 |
| ltr24__logreg__notype__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.434) | **-0.053** [-0.090, -0.021] | 0.003 | ~0.003 | 28/49/82 | -0.075 | -0.019 |
| ltr24__logreg__notype__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.530) | +0.018 [-0.020, +0.054] | 0.342 | ~0.346 | 25/12/45 | +0.012 | +0.024 |
| ltr24__logreg__notype__pooled | vs exp24 mined-only (same features) (n=159, ref 0.431 → 0.434) | +0.002 [-0.019, +0.026] | 0.846 | ~0.847 | 24/42/93 | +0.019 | -0.019 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05 (n=159, ref 0.401 → 0.454) | **+0.052** [+0.018, +0.092] | 0.006 | ~0.006 | 53/27/79 | +0.063 | +0.050 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp13_lex (n=159, ref 0.428 → 0.454) | +0.026 [-0.014, +0.065] | 0.212 | ~0.208 | 47/38/74 | +0.044 | +0.031 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.544) | -0.006 [-0.037, +0.024] | 0.716 | ~0.722 | 17/14/51 | -0.024 | +0.049 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.454) | **-0.033** [-0.061, -0.009] | 0.015 | ~0.013 | 18/42/99 | -0.044 | -0.006 |
| ltr24__lgbm-tiny__withtype__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.544) | +0.032 [-0.015, +0.082] | 0.194 | ~0.192 | 23/12/47 | +0.049 | +0.024 |
| ltr24__lgbm-tiny__withtype__pooled | vs exp24 mined-only (same features) (n=159, ref 0.483 → 0.454) | **-0.029** [-0.056, -0.008] | 0.017 | ~0.015 | 18/42/99 | -0.038 | -0.013 |
| ltr24__logreg__withtype__pooled | vs convex05 (n=159, ref 0.401 → 0.443) | **+0.042** [+0.011, +0.076] | 0.015 | ~0.014 | 58/22/79 | +0.038 | +0.057 |
| ltr24__logreg__withtype__pooled | vs exp13_lex (n=159, ref 0.428 → 0.443) | +0.015 [-0.021, +0.051] | 0.423 | ~0.424 | 44/33/82 | +0.019 | +0.038 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.528) | -0.022 [-0.064, +0.009] | 0.236 | ~0.240 | 20/14/48 | -0.061 | +0.049 |
| ltr24__logreg__withtype__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.443) | **-0.044** [-0.078, -0.013] | 0.010 | ~0.010 | 32/42/85 | -0.069 | +0.000 |
| ltr24__logreg__withtype__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.528) | +0.016 [-0.021, +0.051] | 0.388 | ~0.393 | 26/11/45 | +0.012 | +0.024 |
| ltr24__logreg__withtype__pooled | vs exp24 mined-only (same features) (n=159, ref 0.446 → 0.443) | -0.003 [-0.025, +0.021] | 0.827 | ~0.833 | 26/42/91 | +0.006 | -0.019 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05 (n=159, ref 0.401 → 0.450) | **+0.048** [+0.013, +0.087] | 0.011 | ~0.010 | 50/28/81 | +0.050 | +0.057 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp13_lex (n=159, ref 0.428 → 0.450) | +0.021 [-0.017, +0.059] | 0.276 | ~0.275 | 45/38/76 | +0.031 | +0.038 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.549) | -0.001 [-0.032, +0.030] | 0.966 | ~0.966 | 14/14/54 | -0.024 | +0.061 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.450) | **-0.037** [-0.067, -0.011] | 0.008 | ~0.006 | 19/48/92 | -0.057 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.549) | +0.037 [-0.004, +0.086] | 0.108 | ~0.112 | 22/14/46 | +0.049 | +0.037 |
| ltr24__lgbm-tiny__notype-nogate__pooled | vs exp24 mined-only (same features) (n=159, ref 0.479 → 0.450) | **-0.030** [-0.056, -0.007] | 0.017 | ~0.016 | 19/46/94 | -0.044 | +0.006 |
| ltr24__logreg__notype-nogate__pooled | vs convex05 (n=159, ref 0.401 → 0.425) | +0.024 [-0.013, +0.061] | 0.210 | ~0.212 | 48/33/78 | +0.019 | +0.025 |
| ltr24__logreg__notype-nogate__pooled | vs exp13_lex (n=159, ref 0.428 → 0.425) | -0.003 [-0.039, +0.035] | 0.881 | ~0.882 | 38/40/81 | +0.000 | +0.006 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.527) | -0.023 [-0.062, +0.007] | 0.186 | ~0.194 | 19/16/47 | -0.061 | +0.037 |
| ltr24__logreg__notype-nogate__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.425) | **-0.062** [-0.098, -0.029] | 0.001 | ~0.000 | 25/50/84 | -0.088 | -0.031 |
| ltr24__logreg__notype-nogate__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.527) | +0.015 [-0.023, +0.049] | 0.429 | ~0.436 | 24/11/47 | +0.012 | +0.012 |
| ltr24__logreg__notype-nogate__pooled | vs exp24 mined-only (same features) (n=159, ref 0.434 → 0.425) | -0.009 [-0.029, +0.013] | 0.412 | ~0.422 | 25/45/89 | -0.006 | -0.019 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05 (n=159, ref 0.401 → 0.467) | **+0.066** [+0.035, +0.103] | 0.000 | ~0.000 | 54/27/78 | +0.082 | +0.031 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp13_lex (n=159, ref 0.428 → 0.467) | +0.039 [+0.001, +0.079] | 0.055 | ~0.054 | 47/35/77 | +0.063 | +0.013 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.569) | +0.019 [-0.018, +0.059] | 0.341 | ~0.354 | 18/11/53 | +0.012 | +0.012 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.467) | **-0.020** [-0.040, -0.004] | 0.027 | ~0.023 | 14/39/106 | -0.025 | -0.025 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.569) | **+0.057** [-0.001, +0.111] | 0.046 | ~0.045 | 26/13/43 | +0.085 | -0.012 |
| ltr24__lgbm-tiny__notype-nobge__pooled | vs exp24 mined-only (same features) (n=159, ref 0.479 → 0.467) | -0.012 [-0.029, +0.002] | 0.108 | ~0.110 | 17/34/108 | -0.013 | -0.031 |
| ltr24__logreg__notype-nobge__pooled | vs convex05 (n=159, ref 0.401 → 0.444) | **+0.043** [+0.009, +0.082] | 0.023 | ~0.023 | 50/31/78 | +0.050 | +0.013 |
| ltr24__logreg__notype-nobge__pooled | vs exp13_lex (n=159, ref 0.428 → 0.444) | +0.016 [-0.019, +0.057] | 0.399 | ~0.409 | 40/42/77 | +0.031 | -0.006 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.544) | -0.006 [-0.050, +0.031] | 0.763 | ~0.760 | 18/17/47 | -0.024 | +0.000 |
| ltr24__logreg__notype-nobge__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.444) | **-0.043** [-0.079, -0.008] | 0.018 | ~0.015 | 26/48/85 | -0.057 | -0.044 |
| ltr24__logreg__notype-nobge__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.544) | +0.031 [-0.024, +0.082] | 0.248 | ~0.250 | 28/13/41 | +0.049 | -0.024 |
| ltr24__logreg__notype-nobge__pooled | vs exp24 mined-only (same features) (n=159, ref 0.440 → 0.444) | +0.004 [-0.024, +0.035] | 0.778 | ~0.780 | 28/35/96 | +0.019 | -0.031 |
| ltr24__lgbm-tiny__small__pooled | vs convex05 (n=159, ref 0.401 → 0.451) | **+0.050** [+0.016, +0.088] | 0.007 | ~0.005 | 52/26/81 | +0.057 | +0.044 |
| ltr24__lgbm-tiny__small__pooled | vs exp13_lex (n=159, ref 0.428 → 0.451) | +0.023 [-0.017, +0.061] | 0.247 | ~0.249 | 47/35/77 | +0.038 | +0.025 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.541) | -0.009 [-0.046, +0.029] | 0.651 | ~0.661 | 20/15/47 | -0.037 | +0.037 |
| ltr24__lgbm-tiny__small__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.451) | **-0.036** [-0.068, -0.008] | 0.025 | ~0.022 | 24/41/94 | -0.050 | -0.013 |
| ltr24__lgbm-tiny__small__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.541) | +0.029 [-0.009, +0.071] | 0.148 | ~0.155 | 20/13/49 | +0.037 | +0.012 |
| ltr24__lgbm-tiny__small__pooled | vs exp24 mined-only (same features) (n=159, ref 0.474 → 0.451) | -0.023 [-0.050, -0.003] | 0.054 | ~0.054 | 25/38/96 | -0.025 | +0.006 |
| ltr24__logreg__small__pooled | vs convex05 (n=159, ref 0.401 → 0.427) | +0.026 [-0.010, +0.060] | 0.145 | ~0.145 | 53/26/80 | +0.019 | +0.031 |
| ltr24__logreg__small__pooled | vs exp13_lex (n=159, ref 0.428 → 0.427) | -0.001 [-0.041, +0.035] | 0.965 | ~0.964 | 46/36/77 | +0.000 | +0.013 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.525) | -0.025 [-0.062, +0.006] | 0.165 | ~0.169 | 16/16/50 | -0.061 | +0.037 |
| ltr24__logreg__small__pooled | vs exp21-ranker cheap (n=159, ref 0.487 → 0.427) | **-0.060** [-0.096, -0.033] | 0.000 | ~0.000 | 29/43/87 | -0.088 | -0.025 |
| ltr24__logreg__small__pooled | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.525) | +0.013 [-0.027, +0.056] | 0.529 | ~0.530 | 21/11/50 | +0.012 | +0.012 |
| ltr24__logreg__small__pooled | vs exp24 mined-only (same features) (n=159, ref 0.441 → 0.427) | -0.013 [-0.040, +0.006] | 0.229 | ~0.238 | 26/40/93 | -0.006 | -0.038 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05 (n=159, ref 0.401 → 0.441) | +0.039 [-0.001, +0.083] | 0.067 | ~0.066 | 48/33/78 | +0.050 | +0.050 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp13_lex (n=159, ref 0.428 → 0.441) | +0.013 [-0.032, +0.057] | 0.582 | ~0.589 | 44/42/73 | +0.031 | +0.031 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.550) | -0.000 [-0.036, +0.032] | 0.992 | ~0.993 | 16/17/49 | -0.024 | +0.073 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp21-ranker cheap (n=159, ref 0.487 → 0.441) | **-0.046** [-0.085, -0.009] | 0.018 | ~0.019 | 23/50/86 | -0.057 | -0.006 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.550) | +0.037 [+0.005, +0.080] | 0.052 | ~0.047 | 18/14/50 | +0.049 | +0.049 |
| ltr24__lgbm-tiny__notype__pooled-scored | vs exp24 mined-only (same features) (n=159, ref 0.478 → 0.441) | **-0.037** [-0.074, -0.004] | 0.038 | ~0.037 | 23/50/86 | -0.038 | -0.013 |
| ltr24__logreg__notype__pooled-scored | vs convex05 (n=159, ref 0.401 → 0.391) | -0.011 [-0.056, +0.033] | 0.646 | ~0.652 | 45/46/68 | -0.013 | +0.013 |
| ltr24__logreg__notype__pooled-scored | vs exp13_lex (n=159, ref 0.428 → 0.391) | -0.037 [-0.085, +0.006] | 0.119 | ~0.121 | 43/44/72 | -0.031 | -0.006 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.534) | -0.016 [-0.056, +0.014] | 0.367 | ~0.375 | 17/15/50 | -0.049 | +0.073 |
| ltr24__logreg__notype__pooled-scored | vs exp21-ranker cheap (n=159, ref 0.487 → 0.391) | **-0.096** [-0.143, -0.058] | 0.000 | ~0.000 | 25/56/78 | -0.119 | -0.044 |
| ltr24__logreg__notype__pooled-scored | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.534) | +0.021 [-0.021, +0.063] | 0.315 | ~0.320 | 20/16/46 | +0.024 | +0.049 |
| ltr24__logreg__notype__pooled-scored | vs exp24 mined-only (same features) (n=159, ref 0.431 → 0.391) | **-0.041** [-0.078, -0.009] | 0.021 | ~0.019 | 29/53/77 | -0.025 | -0.044 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05 (n=159, ref 0.401 → 0.444) | **+0.043** [+0.004, +0.085] | 0.042 | ~0.041 | 49/33/77 | +0.057 | +0.057 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp13_lex (n=159, ref 0.428 → 0.444) | +0.016 [-0.028, +0.060] | 0.479 | ~0.485 | 45/40/74 | +0.038 | +0.038 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.549) | -0.001 [-0.038, +0.031] | 0.939 | ~0.940 | 16/16/50 | -0.024 | +0.073 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp21-ranker cheap (n=159, ref 0.487 → 0.444) | **-0.043** [-0.083, -0.006] | 0.033 | ~0.033 | 25/48/86 | -0.050 | +0.000 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.549) | +0.036 [+0.004, +0.079] | 0.059 | ~0.055 | 19/13/50 | +0.049 | +0.049 |
| ltr24__lgbm-tiny__withtype__pooled-scored | vs exp24 mined-only (same features) (n=159, ref 0.483 → 0.444) | **-0.039** [-0.077, -0.004] | 0.042 | ~0.042 | 23/49/87 | -0.044 | -0.006 |
| ltr24__logreg__withtype__pooled-scored | vs convex05 (n=159, ref 0.401 → 0.407) | +0.005 [-0.038, +0.047] | 0.804 | ~0.806 | 47/40/72 | +0.000 | +0.031 |
| ltr24__logreg__withtype__pooled-scored | vs exp13_lex (n=159, ref 0.428 → 0.407) | -0.021 [-0.067, +0.021] | 0.349 | ~0.350 | 45/42/72 | -0.019 | +0.013 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.539) | -0.011 [-0.052, +0.020] | 0.537 | ~0.539 | 19/13/50 | -0.049 | +0.085 |
| ltr24__logreg__withtype__pooled-scored | vs exp21-ranker cheap (n=159, ref 0.487 → 0.407) | **-0.080** [-0.125, -0.043] | 0.000 | ~0.000 | 28/49/82 | -0.107 | -0.025 |
| ltr24__logreg__withtype__pooled-scored | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.539) | +0.026 [-0.019, +0.068] | 0.239 | ~0.245 | 22/12/48 | +0.024 | +0.061 |
| ltr24__logreg__withtype__pooled-scored | vs exp24 mined-only (same features) (n=159, ref 0.446 → 0.407) | **-0.039** [-0.078, -0.006] | 0.037 | ~0.035 | 31/48/80 | -0.031 | -0.044 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05 (n=159, ref 0.401 → 0.409) | +0.007 [-0.033, +0.049] | 0.728 | ~0.731 | 45/44/70 | +0.013 | +0.000 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp13_lex (n=159, ref 0.428 → 0.409) | -0.019 [-0.066, +0.025] | 0.409 | ~0.410 | 36/51/72 | -0.006 | -0.019 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.515) | -0.035 [-0.076, -0.003] | 0.063 | ~0.062 | 13/20/49 | -0.073 | +0.049 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=159, ref 0.487 → 0.409) | **-0.078** [-0.122, -0.038] | 0.000 | ~0.000 | 22/57/80 | -0.094 | -0.057 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.515) | +0.003 [-0.034, +0.042] | 0.872 | ~0.874 | 14/22/46 | +0.000 | +0.024 |
| ltr24__lgbm-tiny__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=159, ref 0.479 → 0.409) | **-0.071** [-0.113, -0.033] | 0.001 | ~0.001 | 21/58/80 | -0.082 | -0.050 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05 (n=159, ref 0.401 → 0.391) | -0.011 [-0.055, +0.032] | 0.634 | ~0.637 | 44/47/68 | -0.013 | +0.000 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp13_lex (n=159, ref 0.428 → 0.391) | -0.037 [-0.083, +0.006] | 0.104 | ~0.106 | 40/49/70 | -0.031 | -0.019 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.544) | -0.006 [-0.044, +0.032] | 0.746 | ~0.759 | 16/16/50 | -0.024 | +0.049 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp21-ranker cheap (n=159, ref 0.487 → 0.391) | **-0.096** [-0.141, -0.058] | 0.000 | ~0.000 | 24/58/77 | -0.119 | -0.057 |
| ltr24__logreg__notype-nogate__pooled-scored | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.544) | +0.031 [-0.009, +0.076] | 0.151 | ~0.153 | 20/17/45 | +0.049 | +0.024 |
| ltr24__logreg__notype-nogate__pooled-scored | vs exp24 mined-only (same features) (n=159, ref 0.434 → 0.391) | **-0.043** [-0.079, -0.012] | 0.013 | ~0.011 | 30/53/76 | -0.038 | -0.044 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05 (n=159, ref 0.401 → 0.436) | +0.035 [+0.001, +0.073] | 0.058 | ~0.057 | 49/33/77 | +0.044 | +0.006 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp13_lex (n=159, ref 0.428 → 0.436) | +0.008 [-0.031, +0.049] | 0.689 | ~0.695 | 42/40/77 | +0.025 | -0.013 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.528) | -0.022 [-0.055, +0.012] | 0.196 | ~0.207 | 12/18/52 | -0.037 | -0.012 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=159, ref 0.487 → 0.436) | **-0.051** [-0.085, -0.019] | 0.003 | ~0.002 | 18/53/88 | -0.063 | -0.050 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.528) | +0.015 [-0.043, +0.070] | 0.592 | ~0.596 | 23/19/40 | +0.037 | -0.037 |
| ltr24__lgbm-tiny__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=159, ref 0.479 → 0.436) | **-0.043** [-0.075, -0.013] | 0.008 | ~0.006 | 18/49/92 | -0.050 | -0.057 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05 (n=159, ref 0.401 → 0.443) | **+0.042** [+0.011, +0.077] | 0.015 | ~0.012 | 49/28/82 | +0.057 | +0.019 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp13_lex (n=159, ref 0.428 → 0.443) | +0.015 [-0.026, +0.056] | 0.476 | ~0.481 | 43/38/78 | +0.038 | +0.000 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.528) | -0.022 [-0.059, +0.016] | 0.254 | ~0.263 | 16/19/47 | -0.037 | -0.012 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp21-ranker cheap (n=159, ref 0.487 → 0.443) | **-0.044** [-0.080, -0.012] | 0.012 | ~0.011 | 21/50/88 | -0.050 | -0.038 |
| ltr24__logreg__notype-nobge__pooled-scored | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.528) | +0.015 [-0.033, +0.062] | 0.522 | ~0.527 | 22/17/43 | +0.037 | -0.037 |
| ltr24__logreg__notype-nobge__pooled-scored | vs exp24 mined-only (same features) (n=159, ref 0.440 → 0.443) | +0.003 [-0.027, +0.035] | 0.857 | ~0.855 | 31/41/87 | +0.025 | -0.025 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05 (n=159, ref 0.401 → 0.437) | +0.036 [-0.000, +0.073] | 0.056 | ~0.056 | 45/34/80 | +0.044 | +0.013 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp13_lex (n=159, ref 0.428 → 0.437) | +0.009 [-0.035, +0.051] | 0.673 | ~0.673 | 47/38/74 | +0.025 | -0.006 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.551) | +0.002 [-0.040, +0.044] | 0.945 | ~0.945 | 19/15/48 | -0.024 | +0.049 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp21-ranker cheap (n=159, ref 0.487 → 0.437) | **-0.050** [-0.088, -0.016] | 0.008 | ~0.006 | 25/43/91 | -0.063 | -0.044 |
| ltr24__lgbm-tiny__small__pooled-scored | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.551) | **+0.039** [+0.013, +0.079] | 0.015 | ~0.010 | 18/12/52 | +0.049 | +0.024 |
| ltr24__lgbm-tiny__small__pooled-scored | vs exp24 mined-only (same features) (n=159, ref 0.474 → 0.437) | **-0.037** [-0.068, -0.011] | 0.014 | ~0.012 | 28/39/92 | -0.038 | -0.025 |
| ltr24__logreg__small__pooled-scored | vs convex05 (n=159, ref 0.401 → 0.427) | +0.026 [-0.011, +0.065] | 0.175 | ~0.179 | 53/29/77 | +0.031 | +0.044 |
| ltr24__logreg__small__pooled-scored | vs exp13_lex (n=159, ref 0.428 → 0.427) | -0.001 [-0.043, +0.039] | 0.970 | ~0.970 | 45/41/73 | +0.013 | +0.025 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap+bge (n=82, ref 0.550 → 0.527) | -0.023 [-0.064, +0.018] | 0.283 | ~0.296 | 16/16/50 | -0.049 | +0.061 |
| ltr24__logreg__small__pooled-scored | vs exp21-ranker cheap (n=159, ref 0.487 → 0.427) | **-0.060** [-0.101, -0.025] | 0.003 | ~0.001 | 28/45/86 | -0.075 | -0.013 |
| ltr24__logreg__small__pooled-scored | vs convex05+bge@20 (sub) (n=82, ref 0.512 → 0.527) | +0.015 [-0.011, +0.046] | 0.307 | ~0.317 | 17/11/54 | +0.024 | +0.037 |
| ltr24__logreg__small__pooled-scored | vs exp24 mined-only (same features) (n=159, ref 0.441 → 0.427) | -0.013 [-0.045, +0.018] | 0.411 | ~0.408 | 32/45/82 | +0.006 | -0.025 |
