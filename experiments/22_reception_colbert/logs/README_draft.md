# 22 – Reception BM25F + colbert-fr + e5-small on corpus B (fixed z-score fusion, rerankers, learned ranker)

Question: exp 20's reception field is the first lexical stage on B that closes the paraphrase gap
(+0.115 MRR on 304 mined questions, p < 0.001) but its fused pipeline only ties the round-1 bar; exp 12's
French ColBERT is the best single first stage on B (val R@30 0.938) and answers the questions the reception
field cannot (rate and regional-tariff articles nobody cites by number). Does a three-leg first stage —
reception BM25F, colbert-fr, cached e5-small — under **fixed** z-score weights, behind mMARCO @30 / bge @20
and under an exp-14-style logistic ranker trained on *mined* labels, beat val 0.570 / full 0.522 with
p < 0.05 on the mined set and directionally on the human set?

Bars: B val 0.570 / full 0.522 (exp 03 e5 RRF + mMARCO @30); round-2 best val 0.610 (exp 14, mMARCO β chosen on
train), oof 0.548 (exp 14 mMARCO) / 0.608 (exp 14 logreg oof); exp 17 lexical → bge @20 val 0.440; best first stage
val 0.539 / R@30 0.938 (exp 12 colbert-fr + BM25 RRF); exp 20 reception + e5 val 0.465 (first stage), 0.573 reranked.

```bash
cd experiments/22_reception_colbert
LOCK="flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1"
$LOCK env EXP12_THREADS=4 ../12_sparse_colbert/.venv/bin/python colbert_scores.py   # PyLate: encode B once (persisted), MaxSim 344 q
PY=../14_ltr_fusion/.venv/bin/python
$PY legs.py && $PY run_stage1.py                        # reception BM25F / e5 / exp-03 BM25 legs, fusions, tests, candidates
$LOCK $PY rerank_score.py --what mmarco && $LOCK $PY rerank_score.py --what bge
$PY run_rerank.py && $PY ltr.py                         # (run_chain.sh = the whole sequence after colbert_scores.py)
```

Results: `experiments/results/22_reception_colbert/*.json` (every run with per-question ranks, all in
`leaderboard.jsonl`; mined runs carry the `__mined` suffix and the mined question file in their provenance stamp),
tables in `runs/*_tables.md`, per-question ranks in `runs/*.json`, logs in `logs/`.

## 1. Setup

* **Question sets.** The 40 human corpus-B questions (24 train / 16 val, untouched, never used to fit or select
  anything) and the 304 mined questions of `18_eval_hygiene` (`rag_eval.load_questions_mined("B")`: PQ 159 /
  ruling 142 / FAQ 3; md5 split 145 train / 159 val; the question's source PQ is dropped from the ranking by the
  harness). Every configuration choice of this experiment is made on the **mined train split only**.
* **Legs** (document = statute article, 5,853; the exp-14 / exp-12 chunk universe `article_ctx_1200`, 10,869
  chunks, is asserted identical in every script):
  * `rec` – exp 20's reception BM25F, its train-selected lexical point (`sent+title`, weight 0.5, b 0.5, on the
    exp-13 index + code-family cue field); doc = max unit. Human questions use the full reception
    (`20_reception_intent/cache/B_reception.json`), the mined questions the **leak-free** field exp 20 built
    without any sentence from a mined question's source document (`B_reception_nomined.json`, 607 documents
    skipped, 65,353 sentences on 3,437 articles). `legs.py` reproduces exp 20's stored ranks 40/40 and 304/304.
  * `colbert` – `antoinelouis/colbertv1-camembert-base-mmarcoFR` through PyLate exactly as exp 12 (`<unk>`
    markers, query length 48, document length 512), brute-force MaxSim over all chunks, doc = max chunk. Exp 12
    never persisted the token embeddings (disk was at 99 % then), so `colbert_scores.py` encodes the 10,869
    chunks once more (fp16 token matrix kept in `cache/B_colbert_tokens.npy`, 0.6 GB, so the next experiment
    does not pay again) and scores the 344 questions; the 40 human rows are checked against exp 12's cached
    matrix.
  * `e5` – cached e5-small (`passage:` chunk vectors of exp 02, human query vectors from exp 14's stage-1
    cache, mined query vectors from exp 20), doc = max chunk.
  * For the reference pipelines: exp 03's chunk BM25 (tok03, k1 1.2, b 0.75) → the exp-03 e5 RRF first stage
    (the bar's) and exp 12's colbert-fr + BM25 RRF are recomputed on both sets (RRF60 over the top-200 chunks,
    doc = first chunk); on the human set they agree with the stored ranks up to RRF tie order (±1 rank on 5/40,
    identical MRR to 3 decimals for e5 alone 40/40, BM25 alone 39/40 — the 40th is the old top-50 cut-off).
* **Fusion.** Per query, each leg's document scores are z-scored over the 5,853 articles and combined with
  **fixed** weights: `z3_equal` (⅓, ⅓, ⅓) and `z_rec_colbert` (0.5, 0.5, 0) are the two pre-registered
  candidates (the one with the higher mined-train MRR is "selected"); `z_rec_e5`, `z_colbert_e5` and the
  min-max twin `mm3_equal` are reported for the fusion-rule and leg-ablation reading only. Nothing is tuned.
* **Rerankers.** mMARCO-MiniLM-L12 (512 tokens) on every chunk of the top-30 (and top-20) articles, doc = max
  chunk, reranker score only (plus exp 14's fixed β 0.8 interpolation, not re-tuned); exp 20's and exp 14's
  score caches are reused where the (question, chunk) pair exists. The bar's own recipe (top-30 *chunks* of the
  e5 RRF stage → mMARCO) is reproduced on the human set (checked against the stored bar) and run on the 304
  mined questions, so that the mined-set comparison is paired against the real bar pipeline and not against a
  first stage. bge-reranker-v2-m3 (512 tokens) @20 on one chunk per article (the article's best chunk by
  z(colbert) + z(e5)) on the human set for both candidates and, on a 100-question stratified subsample of the
  mined set (drawn inside exp 21's 150-question subsample, seed 22: PQ 52 / ruling 47 / FAQ 1), on the selected
  pipeline.
* **Learned ranker** (`ltr.py`, exp 21's feature cache did not exist yet): candidates = top-50 of each leg ∪
  top-50 of the selected fusion (≈ 130 articles / question, candidate recall 0.95 human / 0.92 mined);
  features = per leg z-score, log rank, top-30 flag; has-reception flag; fused z-score and log rank; number of
  legs with the article in the top 30 (`legs`, 13 features) + exp-14 metadata (log length, chunk count, title
  overlap, region cue / match / mismatch, code-family one-hot; `cheap`, 36 features). Logistic regression
  (standardised, L2; C chosen by 5-fold grouped CV on the mined train half), fitted on the mined train half and
  evaluated on the mined val half, the swapped fold (→ 2-fold oof over the 304) and the 40 human questions
  (true held-out); six random half-fits give the stability of the val MRR and of the coefficient signs.
* **Statistics.** `rag_eval.stats.paired_stats` on reciprocal ranks (paired t, exact / Monte-Carlo sign-flip,
  BCa bootstrap CI, win / loss / tie) plus hit@10 and hit@30 deltas; human tests on val (16), train (24) and all
  (40), mined tests on all (304), PQ (159), ruling (142), train (145) and val (159).

RESULTS_PLACEHOLDER
