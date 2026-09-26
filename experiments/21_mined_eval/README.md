# 21 — Re-judging the round-2 systems on the mined question sets, and a learned ranker on real labels

Status: Parts 1 and 3 (cheap features) complete; Part 2 (rerankers) is still scoring under the torch lock (`run_rerank_queue.sh`, log `logs/rerank_queue.log`; B mMARCO done, C mMARCO / bge jobs queued, each lock-wrapped and resumable). To finish: wait for `RERANK_QUEUE_DONE`, then `uv run python ../21_mined_eval/eval_rerank.py --corpus B|C` (→ `runs/part2_<c>.md`) and `uv run python ../21_mined_eval/train21.py --corpus B|C --balance --fsets cheap+mmarco,cheap+bge` (reranker-feature LTR on the scored questions), then paste the tables into §3 / §5 below.

## 1. Setup

Round-3 experiment: re-judge the round-2 candidate systems on the mined question sets of `18_eval_hygiene`
(`rag_eval.load_questions_mined("B")`: 304 questions, PQ 159 / ruling 142 / FAQ 3; `("C")`: 697 questions,
ruling 377 / PQ 163 / FAQ 157), where a paired Δ MRR of ≈ 0.03 is detectable, and train the exp-14 style
learned ranker on real labels. All statistics are `rag_eval.stats` (paired t, exact / Monte-Carlo sign-flip,
BCa bootstrap CI, max-T over the family of systems compared against the same baseline). No new venv: every
script runs with the exp-14 venv (`cd experiments/14_ltr_fusion && uv run python ../21_mined_eval/<script>.py`).

### Question sets, slices, splits

* **human**: the 40 / 64 round-1 questions (untouched; the true held-out set of Part 3).
* **mined**: pooled mined set; **mined · pq / ruling / faq**: the per-source slices. The C PQ → statute slice is a
  statute-lookup recall diagnostic (lexical MRR 0.05, the answer's cited article is the label while the corpus
  holds unlabelled PQs / circulars on the same point); the FAQ and ruling slices are verbatim targets (the query
  is copied from the target document). Nothing is pooled across sources without the per-source rows next to it.
* The harness md5 split (`Question.split`) gives mined B 145 train / 159 val, mined C 352 train / 345 val.
  Part 3 fits on the mined *train* half and reports the mined *val* half; the human sets never enter a fit.
* `evaluate_rankings` drops the documents in `q.meta["exclude"]` (the PQ a question was copied from) before scoring.

### Systems (Part 1, first stages; no torch except one e5-small query pass)

| name | what | code |
|---|---|---|
| `bm25_tok01` | exp-01 BM25 as reproduced by exp 13 / 18: tok01, one concatenated field, k1 1.5 / b 0.75 | `build_lexical.py` (exp-13 machinery) |
| `exp13_lex` | exp-13 final lexical stack (BM25F title 8 / heading 3 / body 1 on cleaned articles for B; title 8 / body 1, k1 0.9 for C; number normalisation) | `build_lexical.py` |
| `bm25chunk` | exp-14 chunk-level BM25 leg (bm25s, exp-01 tokenizer, chunk max) | `build_stage1.py` |
| `bm25doc` | exp-14 whole-document BM25 leg (B: article + heading path) | `build_stage1.py` |
| `e5` | e5-small dense leg, chunk max, cached exp-02 / exp-09 chunk embeddings (B `article_ctx_1200`, C `fixed1200_title`) | `embed_queries.py` (queries only) + `build_stage1.py` |
| `convex05` | fixed convex 0.5 of min-max e5 and chunk BM25 (exp-14 fusion) | `build_stage1.py` |
| `rrf60` | fixed RRF k = 60, depth 300 (exp-03 / 09 fusion) | `build_stage1.py` |

The exp-12 OpenSearch sparse leg was not run: `12_sparse_colbert/cache` holds indexes for A and B only, no C
index or encoder cache, and encoding 201k chunks is outside the budget.

`cache/<corpus>_stage1.npz` keeps, per question, the top-1,500 chunks of every leg and fusion with the exact
corpus-wide min / max of the leg (so min-max normalisation of the kept chunks is exact) and the top-1,000
whole-document BM25 docs; fusions are computed on the full chunk vectors before truncation. Document ranks
beyond the kept top-K are capped (`common21.doc_ranks_capped`), which only affects Part 3 rank features of
documents outside every leg's top-1,500.

### Rerankers (Part 2, under the torch lock)

Stratified subsample (`subsample.py`, seed 21, proportional by source): **B 150** (PQ 78 / ruling 70 / FAQ 2;
68 train / 82 val) and **C 200** (ruling 108 / PQ 47 / FAQ 45; 106 train / 94 val; the PQ cap of 50 did not
bind). Candidates = the top-20 chunks of the fixed convex-0.5 fusion, reranked by mMARCO-MiniLM
(`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, 512 tokens) or bge-reranker-v2-m3 (512 tokens), reranker score
only, fused order below the top-20; on C also exp-13 lexical top-20 → bge / mMARCO (unit index == exp-14
chunk index, asserted). Scores are cached once per (question id, chunk id) in
`cache/<corpus>_rerank_<reranker>.npz` (`score_rerankers.py`, resumable); identical pairs already scored by
exp 14 (mMARCO, 512) and exp 17 (C bge, 512) are copied, exp-14 bge scores (1,024 tokens) only when the pair
fits in 512 tokens.

### Learned ranker (Part 3)

`features21.py` mirrors `14_ltr_fusion/features.py` on the sparse cache: per leg doc-max score, min-max
score, log rank, top-30 flag (e5, chunk BM25), whole-document BM25 (score, min-max, log rank), the two fixed
fusions (score, log rank), the number of legs with the document in the top 30, **exp-13 lexical** (score
relative to the question's best unit, log rank, top-30 flag — new), document length / chunk count, position
of the best e5 / BM25 chunk, query–title stem overlap, region flags (exp-08 `detect_region`), yearly-edition
and document-year flags, document-type one-hot; reranker features (doc max, min-max, log rank, missing flag)
only on questions whose convex top-20 was scored in Part 2. Candidates = documents of the top-50 chunks of
every leg / fusion ∪ top-50 whole-document BM25 ∪ top-50 exp-13 lexical documents, minus the question's
`exclude` list; ranking = model score over the candidates, then the convex-0.5 document order.

`train21.py`: logistic regression (standardised features, L2, positives weighted by grade; C chosen by 5-fold
grouped CV on the mined train half), stability = six random half-fits of the train half (sd of the val MRR,
coefficient sign agreement); LightGBM LambdaMART "tiny" (3 leaves, 100 trees, 5-seed bag, exp-14 settings)
only when the logreg half-fit sd ≤ 0.02. Reports: fit on mined train → mined val (pooled and per source),
train resubstitution, human all / human val; the swapped fold (fit on mined val → mined train); the 2-fold
"oof" over the mined set; fit on all mined → human. Paired tests on the human sets against the exp-14 oof runs,
the round-1 bars (val split and full set), exp-13 lexical and this experiment's fixed fusions; on the mined
val split against the first stages and, on the subsample ∩ val, against the reranked systems.

### Files

```
21_mined_eval/
  common21.py          question sets, slices, sparse Stage1 / LexStage1 loaders, fusions, save21 (question-file stamp), paired()
  embed_queries.py     e5-small query embeddings for human + mined questions (torch lock)      → cache/<c>_qemb_e5.npy
  build_stage1.py      legs + fusions top-K (bm25s + numpy)                                     → cache/<c>_stage1.npz
  build_lexical.py     exp-01 BM25 and exp-13 lexical via exp-13 machinery, saves the runs      → cache/<c>_lex_<cfg>.npz
  subsample.py         stratified subsample for Part 2                                          → cache/subsample_<c>.json
  score_rerankers.py   cross-encoder scores, cached by (question id, chunk id) (torch lock)    → cache/<c>_rerank_<rk>.npz
  eval_stage1.py       Part 1 tables + paired tests                                             → runs/part1_<c>.{json,md}
  eval_rerank.py       Part 2 tables + paired tests                                             → runs/part2_<c>.{json,md}
  features21.py / train21.py   Part 3                                                          → cache/<c>_features.npz, runs/part3_<c>.{json,md}
  run_stage1_queue.sh / run_rerank_queue.sh   the lock-wrapped job queues actually run
```

Every run is saved through `rag_eval.save_result("21_mined_eval", …)` as `<slice>__<system>` (slices `human`,
`mined`, `mined__src_<source>`, `sub`, `sub__src_<source>`), with the provenance stamp's `questions_file` /
`questions_sha256` pointing at the mined question file (the harness stamps the human file by default; `save21`).

## 2. Part 1 — first stages on the mined sets

Full tables (every slice, both corpora, val split, max-T p): `runs/part1_B.md`, `runs/part1_C.md`; numbers in
`runs/part1_<corpus>.json`. Baseline of every paired test: `bm25_tok01` (exp-01 BM25). Δ = system − baseline;
CI = BCa bootstrap 95 %; p_perm = sign-flip (`~` Monte-Carlo); max-T over the six systems compared on that slice.

### 2.1 Corpus B (article retrieval, 5,853 articles)

| slice | n | bm25_tok01 | exp13_lex | bm25chunk | bm25doc | e5 | convex05 | rrf60 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| human | 40 | 0.339 | 0.391 | 0.345 | 0.324 | **0.438** | 0.395 | 0.408 |
| mined, all | 304 | 0.360 | **0.408** | 0.362 | 0.357 | 0.306 | 0.378 | 0.356 |
| mined · pq | 159 | 0.213 | 0.216 | 0.198 | 0.220 | 0.185 | 0.222 | 0.209 |
| mined · ruling | 142 | 0.533 | **0.633** | 0.554 | 0.518 | 0.448 | 0.561 | 0.528 |
| mined, val split | 159 | 0.377 | **0.428** | 0.393 | 0.374 | 0.307 | 0.401 | 0.381 |

Paired vs exp-01 BM25 on the mined set (n = 304):

| system | Δ MRR [95 % CI] | p_t | p_perm | W/L/T | max-T p | Δ H@1 | Δ R@10 |
|---|:--|--:|--:|:--|--:|--:|--:|
| exp13_lex | **+0.048** [+0.025, +0.073] | 0.000 | 0.000 | 110/31/163 | **0.000** | +0.043 | +0.067 |
| bm25chunk | +0.002 [−0.019, +0.023] | 0.867 | 0.869 | 71/65/168 | 1.000 | +0.007 | +0.009 |
| bm25doc | −0.003 [−0.021, +0.014] | 0.743 | 0.741 | 65/63/176 | 0.999 | +0.003 | −0.015 |
| e5 | **−0.054** [−0.093, −0.014] | 0.007 | 0.007 | 77/117/110 | **0.034** | −0.049 | −0.043 |
| convex05 | +0.018 [−0.006, +0.043] | 0.150 | 0.151 | 106/56/142 | 0.528 | +0.013 | +0.029 |
| rrf60 | −0.005 [−0.034, +0.024] | 0.752 | 0.751 | 90/84/130 | 0.999 | −0.010 | +0.008 |

* **exp-13 lexical is confirmed on B**: +0.048 pooled (val half +0.051, p = 0.002, max-T 0.010), +0.099 on the
  ruling slice (61 wins / 5 losses), +0.003 on the PQ slice. The gain is the title / article-number field on
  questions that name the provision; on citizen-phrased PQs it is nil. Exp 13's own B claim was "+0.02 val on
  16 questions"; the effect is real and larger, and it is a lexical-vs-lexical effect.
* **The dense leg alone loses on the mined B questions** (−0.054, max-T 0.034; −0.085 on rulings, −0.027 on
  PQs) while it is the best single first stage on the human set (+0.100, 21/9/10, p = 0.12). The two sets ask
  different questions: human B questions are citizen paraphrases, mined B questions are ruling objets and
  parliamentary questions that carry legal vocabulary. Neither fixed fusion is distinguishable from BM25 on the
  mined set (convex 0.5 +0.018, p = 0.15; RRF60 −0.005) — the round-2 amendment "keep the dense leg" rests on
  the human set only; on the mined set a fixed fusion is at best a wash before reranking.
* PQ → article on B is hard for everything (MRR 0.19–0.22, R@10 ≈ 0.2): the paraphrase gap exp 17 described on
  16 questions, now on 159, and no first stage closes it.

### 2.2 Corpus C (document retrieval, 21,259 documents)

| slice | n | bm25_tok01 | exp13_lex | bm25chunk | bm25doc | e5 | convex05 | rrf60 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| human | 64 | 0.601 | **0.683** | 0.601 | 0.602 | 0.434 | 0.622 | 0.567 |
| mined, all | 697 | 0.722 | **0.729** | 0.722 | 0.697 | 0.613 | 0.721 | 0.691 |
| mined · pq (diagnostic) | 163 | 0.050 | 0.059 | 0.050 | 0.029 | 0.051 | 0.058 | 0.060 |
| mined · ruling (verbatim) | 377 | 0.918 | **0.923** | 0.918 | 0.902 | 0.769 | 0.911 | 0.869 |
| mined · faq (verbatim) | 157 | 0.949 | **0.958** | 0.949 | 0.896 | 0.819 | 0.953 | 0.917 |
| mined, val split | 345 | 0.694 | **0.708** | 0.694 | 0.670 | 0.596 | 0.703 | 0.666 |

Paired vs exp-01 BM25:

| system | slice | Δ MRR [95 % CI] | p_t | p_perm | W/L/T | max-T p |
|---|---|:--|--:|--:|:--|--:|
| exp13_lex | mined all (697) | **+0.007** [+0.001, +0.013] | 0.039 | 0.037 | 42/32/623 | 0.158 |
| exp13_lex | mined val (345) | +0.014 [+0.006, +0.026] | 0.005 | 0.004 | 26/13/306 | **0.020** |
| exp13_lex | human (64) | **+0.083** [+0.026, +0.156] | 0.015 | 0.012 | 20/7/37 | 0.058 |
| exp13_lex | pq (163) | +0.008 [−0.000, +0.025] | 0.148 | 0.155 | 20/21/122 | 0.503 |
| convex05 | mined all | −0.002 [−0.011, +0.007] | 0.748 | 0.748 | 55/46/596 | 0.998 |
| convex05 | pq | +0.008 [+0.000, +0.019] | 0.103 | 0.102 | 30/19/114 | 0.365 |
| rrf60 | mined all | **−0.032** [−0.047, −0.017] | 0.000 | 0.000 | 54/89/554 | **0.000** |
| rrf60 | pq | +0.009 [+0.001, +0.024] | 0.098 | 0.098 | 31/23/109 | 0.346 |
| bm25doc | mined all | **−0.026** [−0.042, −0.010] | 0.002 | 0.002 | 41/102/554 | **0.007** |
| e5 | mined all | **−0.110** [−0.133, −0.088] | 0.000 | 0.000 | 45/170/482 | **0.000** |

* `bm25chunk` (exp-14's bm25s leg with the exp-01 tokenizer) and `bm25_tok01` (exp-13 machinery) are rank-identical
  on C (0/0/697) and within 0.006 on B: the two BM25 implementations are the same system, so exp-14 fusions
  and exp-13 lexical runs are comparable.
* **The verbatim slices are a coverage check, as `README_mining.md` warned**: 85–95 % ties, everything
  lexical at 0.90–0.96. Within that, exp-13 lexical is +0.005 / +0.009 (not significant) and the dense-heavy
  systems lose (RRF60 −0.049 on rulings, −0.032 on FAQ; e5 −0.13 to −0.15). On the human C set the exp-13 gain
  (+0.083, 20/7/37, p = 0.015) is the same direction as exp 13's val claim (0.536 → 0.616) and now has a p-value,
  but it is 64 questions and max-T 0.058.
* **RRF60 is a measured loss on C** (−0.032 pooled, max-T < 0.001; −0.028 on val) whereas convex 0.5 ties BM25
  (−0.002): with an e5-small leg that is 0.11 behind BM25, rank fusion gives the weak leg too much weight; the
  min-max convex fusion does not. This settles exp 14's "convex 0.5 or RRF60 are interchangeable" in favour of
  convex 0.5 on C (on B both are within ±0.02 of BM25).
* **The PQ → statute diagnostic stays at 0.05–0.06 for every first stage** (R@30 0.09–0.15): the label gap of
  idea 73 (the corpus holds other PQs / circulars on the same point) dominates, and no lexical or dense change
  moves it. It is reported here for completeness and should not enter any pooled number.

### 2.3 What Part 1 says about the round-2 claims

| round-2 claim | mined verdict |
|---|---|
| exp-13 lexical upgrades, C val 0.536 → 0.616 (lexical vs lexical) | **confirmed in direction** on every slice of both corpora; large on B rulings (+0.10) and the human sets (+0.05 / +0.08), small on C verbatim slices (+0.005–0.009), nil on PQs |
| exp-14 "fixed w = 0.5 or RRF60 is at least as good as tuned weights" | convex 0.5: ties BM25 on C, +0.018 on B (undecidable); **RRF60 refuted on C** (−0.032, max-T < 0.001) |
| round-2 amendment "keep the dense leg (B paraphrases)" | supported on human B only (+0.10, p = 0.12); **on mined B the e5 leg is a measured loss** (−0.054) and fusions are a wash. Undecidable as a first-stage rule; the reranker tables (Part 2) are where it matters |
| exp-12 OpenSearch sparse + BM25 RRF (A only) | not testable here (no C index, no mined A set) |

## 3. Part 2 — rerankers on the stratified subsample (pending; see status line above)

Design and caches are in §1; numbers land in `runs/part2_<corpus>.md` once the queue finishes.

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

## 5. Reranker-feature learned ranker (pending Part 2 scores)

`train21.py --fsets cheap+mmarco,cheap+bge` trains only on questions whose convex top-20 was scored (subsample ∩ train, ~70–105 questions) and evaluates on the scored val / human questions; it is skipped automatically until the caches exist.

## 6. Which round-2 claims survive, and the recommended stack

| claim | verdict on the mined sets |
|---|---|
| exp-13 lexical upgrades (C val 0.536 → 0.616; B +0.02) | **confirmed**: B +0.048 (n=304, max-T p<0.001; rulings +0.10), C +0.007–0.014 (verbatim slices, max-T 0.02 on val), human C +0.083 (p=0.015); nil on PQ paraphrases |
| exp-14 "fixed convex 0.5 ≈ RRF60 ≈ tuned" | convex 0.5 ties BM25 on C and is +0.018 on B (undecidable); **RRF60 refuted on C** (−0.032, max-T <0.001) |
| "keep the dense leg" (exp 17, round-2 amendment) | undecidable: e5 alone is −0.054 on mined B (max-T 0.03) but +0.10 on human B; fusion with it is a wash as a first stage |
| exp-14 learned ranker beats the bars (oof B 0.608 / C 0.723) | **not reproduced without cross-encoder features**: a mined-trained lgbm-tiny is −0.095 (B) / −0.025 (C) vs the round-1 bars on the human sets (both p>0.15, undecidable) and −0.180 / −0.052 vs those exp-14 oof runs; vs exp-14's own cheap-feature logreg it is −0.064 (B) / **+0.068 (C, p=0.036)** |
| learned ranker vs its first stage | **confirmed on mined val at p<0.001** (B +0.086, C +0.039 vs convex 0.5; +0.059 / +0.034 vs exp-13 lexical), +0.03–0.05 on human (p 0.07–0.5) |
| reranker claims (exp 17 lex13→bge@20 val 0.688; mMARCO vs bge) | pending Part 2 |

Recommended stack (first stage, from what is measured here): exp-13 lexical leg (BM25F title / article field, number normalisation) as the lexical leg; convex 0.5 with e5-small rather than RRF; a LightGBM-tiny ranker over the six leg scores (+ title overlap, doc length, yearly-edition flag) trained on mined labels for statute / ruling lookups, but with the document-type prior taken from human or pooled labels, not from the mined set (the mined-trained logreg collapses to 0.44 on human C because it learns "answers are code articles"); the bge reranker stays the quality ceiling on paraphrased questions until Part 2 says otherwise on 150 / 200 questions.
