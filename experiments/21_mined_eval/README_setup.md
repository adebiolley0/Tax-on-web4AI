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
