# Experiment 14 — learning-to-rank over cheap features, principled fusion / reranker tuning

Question: the fusion weights, RRF constants and reranker depths of experiments 03/09 were picked on the
full question sets. Do they survive a train/validation protocol? Can a small learned ranker over cheap
features (first-stage scores, reranker scores, metadata) beat the hand-tuned recipe, and does it transfer
between halves of the (tiny) question sets?

Standalone `uv` project (CPU torch). Everything expensive (cross-encoder scores) is computed once and cached
under `cache/` (git-ignored); all tuning and learning runs on numpy tables in seconds.

```bash
cd experiments/14_ltr_fusion && uv sync
uv run python build_stage1.py --corpus A          # first-stage score matrices (A, B, C)
./run_rerank_queue.sh                             # mMARCO-MiniLM + bge-reranker-v2-m3 on the candidate sets (sequential)
uv run python tune_fusion.py --corpus A --dense e5 --lex chunk
uv run python train_ltr.py --corpus A
```

## 1. Setup

### Corpora, legs, candidate sets

| corpus | docs / chunks | questions (train / val) | dense legs (cached embeddings) | lexical legs |
|---|---|---|---|---|
| A | 91 / 1,072 (`fixed1500_title`) | 29 (17 / 12) | e5-small, bge-m3 | BM25 chunk-max, BM25 whole document |
| B | 5,853 / 10,869 (`article_ctx_1200`) | 40 (24 / 16) | e5-small | BM25 chunk-max, BM25 article + heading path |
| C | 21,259 / 201,404 (`fixed1200_title`) | 64 (29 / 35) | e5-small, potion-128M | BM25 chunk-max, BM25 whole document |

BM25 uses the best normalisation of experiment 01 (Snowball stem + French stoplist + question-word stoplist
+ accent folding, k1=1.5, b=0.75) for both units; this reproduces the exp-01 numbers exactly (A whole-doc
0.695) and is +0.02 over the exp-03 tokenizer on C chunks (0.601 vs 0.577). Dense legs reproduce exp 02/09
exactly (A e5 0.543, bge-m3 0.678; C e5 0.433, potion 0.315).

Candidate chunks per question = union of the top-K chunks of every leg (plus, on A/B, the best-BM25 chunk of
the top-K whole-document BM25 docs): K=50 for the cheap mMARCO reranker (A 127 / B 107 / C 123 chunks per
question). bge-reranker-v2-m3 (0.7 s/pair on an idle box, several seconds per pair while five torch jobs
shared the four cores) is run as a **cascade**: its candidates are the top-30 chunks by mMARCO score (top-20 on C)
plus the top-10 chunks of every leg (on C: e5 and BM25 only), i.e. ~40 chunks per question. In the grids below,
a top-N chunk without a bge score is given the worst bge score of that question ("coverage" is reported).
Candidate recall of the expected document at K=50: A 1.00, B 0.925, C 0.969 — this is the ceiling of every method below.

Cross-encoder scores are computed once per (corpus, reranker, candidate set) by `score_rerankers.py`
(2 torch threads, resumable npz) and reused by every grid point and every LTR model.

### Features per (question, candidate document) — `features.py`

| group | features |
|---|---|
| per chunk leg (e5, bge-m3 on A, potion on C, bm25) | raw doc-max score, min-max-normalised doc-max, log(doc rank), in-top-30 flag |
| whole-document BM25 | score, min-max, log rank |
| fixed fusions | RRF k=60 (e5+bm25) doc-max + log rank, convex 0.5 doc-max + log rank, number of legs where the doc is in the top 30 |
| rerankers | mMARCO-MiniLM and bge-reranker-v2-m3: doc-max score, min-max within the question's candidates, log rank among candidates, missing flag (doc outside the bge candidate set) |
| document | log chars, log number of chunks, position of the best e5 / best BM25 chunk within the document (0 = first chunk) |
| query–title | share of query stems present in the title, count |
| region (B/C) | query has a region (city / region word, exp 08 `detect_region`), doc region matches, doc region contradicts (federal docs never contradict) |
| yearly editions (C) | `is_yearly_edition` (id `…_revenus_20xx`), query year = edition year, query year ≠ edition year, document year (from `document_date`), has date |
| type | one-hot of document type (A: Fisconet type; B: code family without region suffix; C: folder, ≥ 5 docs) |

Label: expected 1.0, secondary 0.5, other 0.0 (LambdaMART uses integer grades 2 / 1 / 0 with `label_gain=[0,1,2]`).
Feature sets: `all`, `cheap` (no cross-encoder), `minimal` (e5_norm, bm25_norm, bm25doc_norm, rrf60,
mmarco_norm, bge_norm), `minimal+meta` (minimal + title overlap, region, year, length). Constant columns are dropped per corpus.

### Grids — `tune_fusion.py`

* first stage: convex `w·minmax(dense) + (1−w)·minmax(bm25)` for w ∈ {0, 0.1, …, 1} (w=0 pure BM25, w=1 pure
  dense) and RRF(k) for k ∈ {10, 20, 40, 60, 100, 200} (depth 300), at chunk level, document = max chunk;
  lexical leg = chunk BM25 (`--lex chunk`) or whole-document BM25 broadcast to the chunks (`--lex doc`);
* second stage: reranker ∈ {mMARCO-MiniLM, bge-reranker-v2-m3} on the top-N fused chunks, N ∈ {10, 20, 30, 50},
  with score interpolation `β·minmax(rerank) + (1−β)·minmax(fused)` over the top-N, β ∈ {0, 0.1, …, 1}
  (β=1 is the usual "replace by the reranker score"); chunks below N keep their fused order.
  17 first-stage × (1 + 2 × 4 × 11) = 1,513 configurations per (corpus, dense leg, lexical leg).

### Protocol — `protocol.py`

Every question has a deterministic split (`Question.split`, md5 of the id). For every method:

* **fit-train**: select / fit on train, evaluate on all — the harness prints train (resubstitution) and val (honest);
* **fit-val**: the swapped fold — fit on val, train is now the honest number;
* **oof**: out-of-fold rankings (val from fit-train, train from fit-val) = 2-fold cross-validation over the
  whole set, the number comparable with the full-set bars of earlier experiments.

Grid selection maximises train MRR, ties broken by train nDCG@5 then by lower rerank depth. All runs are saved
through `rag_eval.save_result("14_ltr_fusion", …)` (`experiments/results/14_ltr_fusion/`, leaderboard).

Bars to beat (from the leaderboard, val MRR): A 0.736 (whole-doc BM25), B 0.570 (RRF + mMARCO@30),
C 0.665 (BM25 + bge@30); full set: A 0.703, B 0.522, C 0.703.

## 2. Results

Every table: **val** = selected/fitted on the train half, scored on the val half (honest); **train (swapped)** =
fitted on val, scored on train (honest); **oof** = the two honest halves put together (2-fold CV over the whole
set, comparable with the full-set bars). Resubstitution numbers are shown to size the optimism.

### 2.1 Does hand-tuning transfer? (fusion grid, `tune_fusion.py`)

_(pending: tables from `make_tables.py`, β / depth curves)_

### 2.2 Learning to rank (`train_ltr.py`)

_(pending)_

### 2.3 What the models learn

_(pending)_

## 3. Conclusions and recommended recipe

_(pending)_
