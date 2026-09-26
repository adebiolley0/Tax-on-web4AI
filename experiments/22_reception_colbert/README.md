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

## 2. Results

### 2.1 First stage (`runs/stage1_tables.md`; every run saved)

Human questions (40: 24 train / 16 val; R@30 = first expected article within the top 30):

| run | MRR train | MRR **val** | MRR all | H@1 val | H@1 all | R@10 val | R@10 all | R@30 val | R@30 all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ref – exp 01 BM25 | 0.371 | 0.290 | 0.339 | 0.125 | 0.200 | 0.562 | 0.600 | 0.625 | 0.675 |
| ref – exp 03 e5-small + BM25 RRF (the bar's first stage) | 0.481 | 0.420 | 0.457 | 0.312 | 0.300 | 0.750 | 0.750 | 0.812 | 0.850 |
| ref – exp 12 colbert-fr alone | 0.502 | 0.432 | 0.474 | 0.250 | 0.325 | 0.875 | 0.825 | 1.000 | 0.950 |
| ref – exp 12 colbert-fr + BM25 RRF (best first stage so far) | 0.470 | **0.539** | 0.498 | 0.438 | 0.375 | 0.812 | 0.800 | 0.938 | 0.875 |
| ref – exp 20 reception + e5 min-max 0.5 | 0.717 | 0.448 | 0.609 | 0.250 | 0.500 | 0.812 | 0.825 | 0.812 | 0.850 |
| `rec` (reception BM25F alone; = exp 20, 40/40) | 0.646 | 0.427 | 0.558 | 0.312 | 0.475 | 0.750 | 0.775 | 0.812 | 0.825 |
| `e5` alone (cached) | 0.512 | 0.327 | 0.438 | 0.188 | 0.300 | 0.562 | 0.700 | 0.812 | 0.900 |
| `z_rec_e5` (z-score twin of exp 20's fusion) | 0.696 | 0.478 | 0.609 | 0.312 | 0.500 | 0.812 | 0.825 | 0.812 | 0.825 |
| `z_colbert_e5` | 0.623 | 0.428 | 0.545 | 0.250 | 0.375 | 0.750 | 0.825 | 0.938 | 0.925 |
| `z_rec_colbert` (0.5 / 0.5 / 0) – alternative | 0.676 | 0.523 | 0.615 | 0.375 | 0.525 | 0.812 | 0.800 | 0.875 | 0.925 |
| **`z3_equal` (⅓ / ⅓ / ⅓) – selected on mined train** | 0.700 | **0.545** | **0.638** | 0.375 | 0.525 | 0.812 | 0.825 | **0.938** | **0.950** |
| `mm3_equal` (same legs, min-max instead of z-score) | 0.712 | 0.536 | 0.642 | 0.375 | 0.525 | 0.812 | 0.825 | 0.875 | 0.925 |

Mined questions (304, leak-free reception; MRR / H@1 / R@10 / R@30):

| run | all (304) | pq (159) | ruling (142) | train (145) | val (159) |
|---|---|---|---|---|---|
| ref – exp 01 BM25 | 0.360 / 0.280 / 0.523 / 0.645 | 0.213 / 0.145 / 0.358 / 0.491 | 0.533 / 0.437 / 0.718 / 0.831 | 0.342 | 0.377 |
| ref – exp 13 lexical | 0.408 / 0.322 / 0.579 / 0.684 | 0.216 / 0.138 / 0.396 / 0.497 | 0.633 / 0.535 / 0.796 / 0.908 | 0.387 | 0.428 |
| exp 03 first stage reproduced (e5 + BM25 RRF) | 0.359 / 0.270 / 0.546 / 0.678 | 0.217 / 0.151 / 0.371 / 0.535 | 0.525 / 0.408 / 0.754 / 0.852 | 0.333 | 0.383 |
| exp 12 first stage reproduced (colbert-fr + BM25 RRF) | 0.268 / 0.178 / 0.497 / 0.678 | 0.206 / 0.132 / 0.390 / 0.553 | 0.343 / 0.232 / 0.627 / 0.831 | 0.274 | 0.263 |
| `colbert` alone (query length 48) | 0.203 / 0.128 / 0.391 / 0.533 | 0.165 / 0.101 / 0.314 / 0.459 | 0.251 / 0.162 / 0.486 / 0.627 | 0.188 | 0.217 |
| `e5` alone | 0.306 / 0.230 / 0.447 / 0.599 | 0.186 / 0.126 / 0.302 / 0.484 | 0.448 / 0.352 / 0.620 / 0.739 | 0.305 | 0.307 |
| `rec` alone (= exp 20, 304/304) | 0.531 / 0.444 / 0.714 / 0.832 | 0.348 / 0.270 / 0.528 / 0.711 | 0.738 / 0.641 / 0.923 / 0.972 | 0.528 | 0.533 |
| ref – exp 20 reception + e5 min-max 0.5 | 0.534 / 0.434 / 0.757 / 0.865 | 0.331 / 0.214 / 0.610 / 0.774 | 0.769 / 0.690 / 0.930 / 0.979 | 0.523 | 0.544 |
| `z_rec_e5` | **0.536** / 0.438 / 0.763 / **0.868** | 0.335 / 0.220 / 0.616 / 0.780 | 0.769 / 0.690 / 0.937 / 0.979 | 0.523 | 0.547 |
| `z_colbert_e5` | 0.305 / 0.217 / 0.447 / 0.612 | 0.212 / 0.151 / 0.327 / 0.547 | 0.415 / 0.296 / 0.592 / 0.697 | 0.295 | 0.314 |
| `z_rec_colbert` – alternative | 0.490 / 0.391 / 0.697 / 0.839 | 0.340 / 0.233 / 0.579 / 0.748 | 0.667 / 0.577 / 0.838 / 0.951 | 0.474 | 0.506 |
| **`z3_equal` – selected on mined train** | 0.494 / 0.401 / 0.707 / 0.836 | 0.318 / 0.208 / 0.579 / 0.761 | 0.701 / 0.627 / 0.859 / 0.930 | 0.482 | 0.505 |
| `mm3_equal` | 0.489 / 0.395 / 0.694 / 0.836 | 0.319 / 0.208 / 0.560 / 0.761 | 0.690 / 0.613 / 0.859 / 0.930 | 0.480 | 0.497 |

Post-hoc ColBERT query-length variants (decided after the mined-set collapse above; the choice between them is made
on the mined **train** split only, but the variants themselves were not pre-registered — the pre-registered
pipeline is `z3_equal` with exp 12's 48-token queries). `_q256`: PyLate query length 256 (every question padded
with [MASK] expansion tokens to 256); `_q256t`: the same encoding, keeping only max(48, real tokens) query vectors
(≈ 105 on average; 287 / 344 questions exceed 48 tokens). The document side is unchanged (persisted token matrix);
MaxSim costs 4.2 s / query at 256 tokens and 2.3 s trimmed against 0.73 s at 48.

| run | human MRR train / **val** / all | human R@30 val / all | mined all MRR / H@1 / R@10 / R@30 | pq | ruling | mined train | mined val |
|---|---|---|---|---|---|---|---|
| `colbert` (48) | 0.502 / **0.432** / 0.474 | 1.000 / 0.950 | 0.203 / 0.128 / 0.391 / 0.533 | 0.165 | 0.251 | 0.188 | 0.217 |
| `colbert_q256` | 0.261 / **0.129** / 0.208 | 0.500 / 0.550 | 0.256 / 0.174 / 0.424 / 0.546 | 0.160 | 0.369 | 0.240 | 0.271 |
| `colbert_q256t` | 0.451 / **0.297** / 0.389 | 0.938 / 0.950 | 0.256 / 0.168 / 0.438 / 0.546 | 0.188 | 0.338 | 0.246 | 0.266 |
| exp 12 colbert + BM25 RRF (48) | 0.474 / **0.539** / 0.500 | 0.938 / 0.875 | 0.268 / 0.178 / 0.497 / 0.678 | 0.206 | 0.343 | 0.274 | 0.263 |
| same, `_q256` / `_q256t` | 0.389 / **0.332** / 0.366 · 0.479 / **0.416** / 0.454 | 0.812 / 0.775 · 0.812 / 0.875 | 0.333 / 0.230 / 0.553 / 0.688 · 0.322 / 0.227 / 0.510 / 0.655 | 0.236 · 0.215 | 0.449 · 0.449 | 0.315 · 0.312 | 0.350 · 0.332 |
| `z3_equal` (48) – pre-registered | 0.700 / **0.545** / 0.638 | 0.938 / 0.950 | 0.494 / 0.401 / 0.707 / 0.836 | 0.318 | 0.701 | 0.482 | 0.505 |
| `z3_equal_q256` – query length selected on mined train | 0.716 / **0.486** / 0.624 | 0.812 / 0.850 | 0.516 / 0.428 / 0.691 / 0.852 | 0.330 | 0.735 | **0.526** | 0.508 |
| `z3_equal_q256t` | 0.726 / **0.486** / 0.630 | 0.812 / 0.900 | 0.511 / 0.414 / 0.711 / 0.849 | 0.329 | 0.724 | 0.505 | 0.516 |

Paired tests (Δ = new − base, reciprocal rank; p_t paired t / p_perm sign-flip; W / L / T):

| comparison | n | MRR base → new | Δ [95 % CI] | p_t / p_perm | W / L / T | Δ H@30 |
|---|---:|---|---|---|---|---|
| **human val** `z3_equal` vs exp 20 reception + e5 | 16 | 0.448 → 0.545 | **+0.097** [+0.035, +0.215] | 0.048 / 0.016 | 7 / 0 / 9 | +0.125 |
| human train / all, same | 24 / 40 | 0.717 → 0.700 / 0.609 → 0.638 | −0.017 / +0.029 [−0.038, +0.087] | 0.69 / 0.38 | 5/4/15 / 12/4/24 | +0.083 / +0.100 (p 0.04) |
| human val `z3_equal` vs exp 12 colbert + BM25 RRF | 16 | 0.539 → 0.545 | +0.006 [−0.188, +0.156] | 0.95 / 0.95 | 5 / 6 / 5 | 0 |
| human train / all, same | 24 / 40 | 0.470 → 0.700 / 0.498 → 0.638 | **+0.230** [+0.126, +0.366] / **+0.140** [+0.038, +0.241] | 0.001 / 0.012 | 13/1/10 / 18/7/15 | +0.125 / +0.075 |
| human val / all `z3_equal` vs exp 01 BM25 | 16 / 40 | 0.290 → 0.545 / 0.339 → 0.638 | **+0.255** [+0.101, +0.420] / **+0.299** [+0.190, +0.410] | 0.008 / < 0.001 | 10/2/4 / 27/4/9 | +0.312 / +0.275 |
| human val / all `z3_equal` vs exp 03 e5 RRF | 16 / 40 | 0.420 → 0.545 / 0.457 → 0.638 | +0.125 [−0.008, +0.246] / **+0.181** [+0.086, +0.274] | 0.080 / 0.001 | 8/2/6 / 22/5/13 | +0.125 / +0.100 |
| human val / all `z3_equal` vs `z_rec_colbert` | 16 / 40 | 0.523 → 0.545 / 0.615 → 0.638 | +0.021 / +0.023 | 0.78 / 0.46 | 5/2/9 / 11/3/26 | +0.062 / +0.025 |
| **mined all** `z3_equal` vs exp 20 reception + e5 | 304 | 0.534 → 0.494 | **−0.040** [−0.062, −0.019] | < 0.001 | 46 / 94 / 164 | −0.030 (p 0.03) |
| mined pq / ruling, same | 159 / 142 | 0.331 → 0.318 / 0.769 → 0.701 | −0.013 [−0.040, +0.013] / **−0.069** [−0.108, −0.038] | 0.34 / < 0.001 | 40/50/69 / 6/43/93 | −0.013 / −0.049 |
| mined all `z_rec_colbert` vs exp 20 reception + e5 | 304 | 0.534 → 0.490 | **−0.043** [−0.069, −0.018] | 0.001 | 52 / 106 / 146 | −0.026 |
| mined all `z3_equal` vs exp 12 colbert + BM25 RRF | 304 | 0.268 → 0.494 | **+0.226** [+0.189, +0.266] | < 0.001 | 194 / 26 / 84 | +0.158 |
| mined all `z3_equal` vs exp 01 BM25 / exp 13 lexical / exp 03 e5 RRF | 304 | 0.360 / 0.408 / 0.359 → 0.494 | **+0.134** / **+0.086** / **+0.135** | < 0.001 each | 163/42/99 · 141/51/112 · 161/42/101 | +0.19 / +0.15 / +0.16 |
| mined all `z3_equal` vs `z_rec_colbert` | 304 | 0.490 → 0.494 | +0.004 [−0.016, +0.025] | 0.73 | 78 / 67 / 159 | −0.003 |
| mined all `z_rec_e5` vs exp 20 min-max (fusion rule, same legs) | 304 | 0.534 → 0.536 | +0.002 [−0.000, +0.009] | 0.29 | 30 / 24 / 250 | +0.003 |
| mined all `z3_equal` vs `mm3_equal` (fusion rule) | 304 | 0.489 → 0.494 | +0.005 [−0.004, +0.015] | 0.31 | 49 / 39 / 216 | 0 |

Reading. On the **human** questions the triple is the best first stage measured on B: val 0.545 / all 0.638 /
R@30 val 0.938, all 0.950 — it keeps exp 12's recall (colbert answers B23, B33, B37, the rate and tariff articles
nobody cites by number) and exp 20's precision (train 0.700, the reception field's B9 / B12 / B17 / B30 at rank
1–2), and beats exp 20's fused stage on the val half with 7 wins and no loss (+0.097, p_perm 0.016 — nominal,
16 questions, one of two pre-registered candidates) while tying colbert + BM25 on val and beating it on all
(+0.140, p 0.012). On the **mined** questions the same triple is **0.040 below exp 20's reception + e5**
(p < 0.001; the loss is on the ruling slice, −0.069, PQ −0.013 n.s.), because colbert-fr is the *weakest* leg
there (0.203 alone, below e5 0.306 and far below the reception field 0.531) — see the query-length analysis
below. Both pre-registered candidates are indistinguishable from each other on either set (±0.02, p > 0.4);
z-score and min-max fusion are the same thing here (±0.005, ≥ 216 ties of 304).

**Why colbert-fr collapses on the mined set.** The mined questions are long (median 78 words, p75 102; the human
questions: median 20, max 28) and exp 12's PyLate set-up truncates queries at **48 tokens**, so the MaxSim
score of a PQ block or a ruling *objet* sees its first ≈ 35 words only; the lexical and e5 legs see the whole
text. ColBERT's MRR on mined questions is flat across length buckets (0.17–0.21 for < 25, 25–40, 40–80, 80+
words) while e5's grows with length (0.09 → 0.21 → 0.30 → 0.34). No question is in Dutch. Giving ColBERT the whole question does **not** repair the leg: with 256-token queries colbert-fr alone goes
from 0.203 to 0.256 on the mined set (ruling 0.251 → 0.369, PQ unchanged) but collapses on the short human
questions (val 0.432 → 0.129: 230 [MASK] expansion tokens per 20-word question dominate the MaxSim sum, five
times the expansion the model was trained with); trimming the expansion back to the 48-token budget does not
restore it either (val 0.297 — the real-token vectors are contextualised over the masks that were present at
encoding time, so a per-question query length would need per-question encoding). Under the protocol the query
length is chosen on the mined train split, which picks `_q256` (0.526 vs 0.482 vs 0.505) — a choice that is worth
+0.003 on the mined val half and −0.059 on the human val half, i.e. it does not transfer across the two question
populations; `z3_equal_q256` is therefore carried through the reranker as the protocol's "final" pipeline but the
honest first-stage recommendation is the pre-registered `z3_equal` at 48 tokens for citizen-length questions.
The deeper point stands: the reception field is the leg that carries the mined questions (0.531 alone), colbert-fr
is a citizen-question leg (short, paraphrased) and its exp-12 numbers were measured on 40 questions of that kind.

### 2.2 mMARCO-MiniLM behind the first stages (`runs/rerank_tables.md`)

Unit: the best 3 chunks (by z(colbert) + z(e5)) of each of the top-k articles, doc = max chunk, reranker score
only; the median candidate article has 3 chunks (mean 7.5, max 249 — reranking *every* chunk of the top-30
would have been 225 pairs / query on the mined set, 85k pairs). 28,325 pairs in all, 3,409 reused from exp 20 /
exp 14, 24,916 scored here in 48.5 min at 0.117 s/pair; per query ≈ 74 pairs / 8.6 s @30 (the bar's recipe: 30
pairs / 3.5 s). The bar's own recipe (top-30 *chunks* of the e5 RRF stage → mMARCO) reproduced on the human set
gives val 0.572 / all 0.523 against the stored 0.570 / 0.522 (37 / 40 ranks identical, three ties re-ordered).

Human questions:

| run | MRR train | MRR **val** | MRR all | H@1 val | H@1 all | R@10 val | R@10 all |
|---|---:|---:|---:|---:|---:|---:|---:|
| ref – round-1 bar (exp 03 e5 RRF + mMARCO @30) | 0.490 | **0.570** | 0.522 | 0.438 | 0.350 | 0.812 | 0.825 |
| ref – round-2 best (exp 14 e5 + mMARCO @20, β 0.8 chosen on train) | 0.630 | **0.610** | 0.622 | 0.500 | 0.500 | 0.750 | 0.800 |
| ref – exp 20 reception + e5 → mMARCO @30 | 0.578 | 0.573 | 0.576 | 0.438 | 0.425 | 0.750 | 0.800 |
| ref – exp 14 logreg minimal+meta (oof) | 0.667 | 0.519 | 0.608 | 0.375 | 0.475 | 0.812 | 0.825 |
| bar recipe reproduced (e5 RRF → mMARCO @30 chunks) | 0.491 | 0.572 | 0.523 | 0.438 | 0.350 | 0.812 | 0.825 |
| **`z3_equal` → mMARCO @30** | 0.515 | **0.651** | 0.569 | 0.500 | 0.375 | 0.875 | 0.900 |
| `z3_equal` → mMARCO @30, β 0.8 (exp 14's fixed value, not re-tuned) | 0.614 | 0.613 | **0.614** | 0.438 | 0.425 | 0.938 | 0.925 |
| `z3_equal` → mMARCO @20 | 0.509 | 0.579 | 0.537 | 0.438 | 0.350 | 0.812 | 0.850 |
| `z_rec_colbert` → mMARCO @30 / β 0.8 | 0.536 / 0.609 | 0.596 / 0.603 | 0.560 / 0.606 | 0.438 / 0.438 | 0.375 / 0.425 | 0.875 / 0.875 | 0.875 / 0.875 |

Mined questions (304):

| run | all | pq | ruling | train | val |
|---|---|---|---|---|---|
| exp 03 first stage (no reranker) | 0.359 / 0.270 / 0.546 / 0.678 | 0.217 | 0.525 | 0.333 | 0.383 |
| bar recipe (e5 RRF → mMARCO @30 chunks) | 0.223 / 0.132 / 0.477 / 0.678 | 0.184 | 0.271 | 0.201 | 0.242 |
| `z3_equal` first stage (no reranker) | 0.494 / 0.401 / 0.707 / 0.836 | 0.318 | 0.701 | 0.482 | 0.505 |
| `z3_equal` → mMARCO @30 | 0.213 / 0.102 / 0.464 / 0.836 | 0.193 | 0.240 | 0.196 | 0.229 |
| `z3_equal` → mMARCO @30, β 0.8 | 0.276 / 0.148 / 0.536 / 0.836 | 0.236 | 0.327 | 0.246 | 0.303 |
| `z3_equal` → mMARCO @20 | 0.240 / 0.118 / 0.507 / 0.836 | 0.212 | 0.277 | 0.220 | 0.259 |

Paired tests:

| comparison | n | MRR base → new | Δ [95 % CI] | p_t / p_perm | W / L / T | Δ H@10 |
|---|---:|---|---|---|---|---|
| **human val** `z3_equal` → mMARCO @30 vs the bar | 16 | 0.570 → 0.651 | +0.081 [+0.026, +0.219] | 0.083 / 0.062 | 5 / 0 / 11 | +0.062 |
| human all, same | 40 | 0.522 → 0.569 | +0.047 [+0.001, +0.114] | 0.111 / 0.119 | 10 / 2 / 28 | +0.075 (p 0.08) |
| human val / all `z3_equal` → mMARCO @30 vs round-2 best (exp 14) | 16 / 40 | 0.610 → 0.651 / 0.622 → 0.569 | +0.041 [−0.069, +0.157] / −0.053 [−0.149, +0.032] | 0.51 / 0.26 | 4/3/9 / 10/12/18 | +0.125 / +0.100 |
| human val / all `z3_equal` → mMARCO @30 vs exp 20 reception + e5 → mMARCO | 16 / 40 | 0.573 → 0.651 / 0.576 → 0.569 | +0.079 [+0.001, +0.343] / −0.006 | 0.23 / 0.88 | 3/0/13 / 6/6/28 | +0.125 / +0.100 (p 0.04) |
| human val / all `z3_equal` → mMARCO @30, β 0.8 vs the bar | 16 / 40 | 0.570 → 0.613 / 0.522 → 0.614 | +0.043 [−0.146, +0.133] / **+0.092** [+0.019, +0.154] | 0.52 / 0.012 | 7/1/8 / 19/2/19 | +0.125 / +0.100 (p 0.04) |
| human val / all, β 0.8 vs round-2 best | 16 / 40 | 0.610 → 0.613 / 0.622 → 0.614 | +0.003 / −0.009 [−0.100, +0.066] | 0.97 / 0.84 | 4/3/9 / 11/7/22 | +0.188 / +0.125 (p 0.02) |
| human val / all reranker gain (`z3_equal` → mMARCO @30 vs its first stage) | 16 / 40 | 0.545 → 0.651 / 0.638 → 0.569 | +0.106 [−0.077, +0.329] / −0.069 [−0.195, +0.069] | 0.34 / 0.32 | 6/5/5 / 12/16/12 | +0.062 / +0.075 |
| **mined all** `z3_equal` → mMARCO @30 vs the bar recipe | 304 | 0.223 → 0.213 | −0.010 [−0.035, +0.013] | 0.42 | 110 / 128 / 66 | −0.013 |
| mined all `z3_equal` → mMARCO @30, β 0.8 vs the bar recipe | 304 | 0.223 → 0.276 | **+0.054** [+0.029, +0.079] | < 0.001 | 162 / 64 / 78 | +0.059 (p 0.01) |
| mined val, same | 159 | 0.242 → 0.303 | **+0.061** [+0.023, +0.097] | 0.002 | 93 / 25 / 41 | +0.094 |
| mined all reranker gain (`z3_equal` → mMARCO @30 vs its first stage) | 304 | 0.494 → 0.213 | **−0.281** [−0.329, −0.235] | < 0.001 | 33 / 188 / 83 | −0.243 |
| mined all bar recipe vs its first stage (exp 03 e5 RRF) | 304 | 0.359 → 0.223 | **−0.136** | < 0.001 | – | – |

The protocol's "final" pipeline (`z3_equal_q256`, query length chosen on mined train) behind mMARCO, for
completeness: human val 0.528 / all 0.517 reranker-only (vs the bar −0.043 / −0.005, vs `z3_equal` → mMARCO
−0.123 val / −0.052 all, 1 / 3 / 12 and 2 / 7 / 31), 0.576 / 0.581 with β 0.8; mined all 0.222 reranker-only
(= bar recipe, −0.001), 0.291 with β 0.8 (+0.068 over the bar recipe, p < 0.001), 0.247 @20; vs `z3_equal` →
mMARCO on the mined set +0.009 (p 0.18). The query-length choice buys nothing behind the reranker on either set.

Reading. On the human set the triple in front of mMARCO gives the highest B numbers of the project — **val 0.651
reranker-only, all 0.614 with exp 14's fixed β 0.8** — and the comparisons go the right way on both halves:
vs the bar +0.081 val (5 / 0 / 11, p_perm 0.06) and +0.047 all reranker-only, +0.092 all with β 0.8 (19 / 2 / 19,
p 0.012 — the one comparison against a bar that reaches p < 0.05 on the human set, on the full 40 rather than
the 16); vs the round-2 best it is +0.04 on val and −0.05 / −0.01 on all (that run's train half is tuned).
The candidate recall is the visible part of the gain: R@10 0.900 / 0.925 on all 40 against 0.825.

On the mined set mMARCO-MiniLM is **destructive**: the bar's own recipe falls from 0.359 to 0.223 and ours from
0.494 to 0.213 (−0.281, 33 wins / 188 losses, p < 0.001), and the damage grows with question length (z3 first
stage → reranked: < 40 words 0.445 → 0.377, 40–80 words 0.457 → 0.209, 80 + words 0.536 → 0.181; the bar's
recipe on the < 40-word questions still gains, 0.242 → 0.274). A 78-word question plus a 1,200-character chunk
fills the 512-token window and is nothing like the MS-MARCO queries the MiniLM cross-encoder was distilled on;
the expected article is inside the reranker's top-30 for 254 / 304 questions and only 56 % of them stay in the
top 10 after reranking. The β 0.8 interpolation, which carries the first-stage score, is the only reranked
variant above the bar's recipe on the mined set (+0.054, p < 0.001) and it is still 0.22 below the un-reranked
first stage. **The mined set therefore says: with mMARCO-MiniLM there is no reranked B pipeline; the question
the coordinator asked (a pipeline that beats the bar at p < 0.05 on the mined set) is answered by the first stage
itself** — `z3_equal` first stage vs the bar's recipe: 0.494 vs 0.223 (and exp 20's `rec + e5` 0.534) —
and by what bge and the learned ranker do next.

### 2.3 bge-reranker-v2-m3 @20 (`runs/rerank_tables.md`)

One pair per article (its best dense chunk), 512 tokens, reranker score only: 800 pairs on the human set
(`z3_equal`), 2,000 on the 100-question mined subsample; 2,800 pairs scored in 49 min at 1.05 s/pair (≈ 21 s /
query @20).

| run | MRR train | MRR **val** | MRR all | H@1 val | H@1 all | R@10 val | R@10 all |
|---|---:|---:|---:|---:|---:|---:|---:|
| ref – round-1 bar (exp 03 e5 RRF + mMARCO @30) | 0.490 | **0.570** | 0.522 | 0.438 | 0.350 | 0.812 | 0.825 |
| ref – exp 03 e5 RRF + bge @30 | 0.562 | 0.450 | 0.518 | 0.312 | 0.375 | 0.750 | 0.825 |
| ref – exp 17 lexical → bge @20 | 0.567 | 0.443 | 0.517 | 0.312 | 0.425 | 0.625 | 0.675 |
| `z3_equal` → mMARCO @30 (above) | 0.515 | 0.651 | 0.569 | 0.500 | 0.375 | 0.875 | 0.900 |
| **`z3_equal` → bge @20** | 0.575 | **0.569** | 0.572 | 0.438 | 0.425 | 0.812 | 0.875 |

Human paired tests: vs the bar −0.002 val (5 / 4 / 7) / +0.050 all [−0.054, +0.159] (16 / 8 / 16, p 0.36); vs the
round-2 best −0.042 val / −0.050 all; vs exp 17's lexical → bge @20 +0.126 val [−0.060, +0.371] / +0.055 all
(hit@10 +0.200, p 0.01); vs exp 03's e5 RRF → bge @30 +0.119 val [+0.004, +0.356] (5 / 1 / 10, p 0.16) / +0.055
all (p 0.11); vs its own mMARCO @30 −0.082 val (2 / 6 / 8) / +0.003 all — on B the large reranker is not better
than the small one (exp 17's finding again: B's failure mode is recall and vocabulary, not the reranker), and
with this first stage both rerankers *lose* MRR on the train half against the un-reranked stage (0.700 → 0.515
/ 0.575), the reception field's rank-1 statute lookups being demoted by both cross-encoders.

**Mined 100-question subsample** (PQ 52 / ruling 47 / FAQ 1; every row on the same 100 questions, MRR / H@1 / R@10 / R@30):

| run | all (100) | pq (52) | ruling (47) | val (60) |
|---|---|---|---|---|
| exp 03 first stage (e5 RRF, no reranker) | 0.426 / 0.330 / 0.640 / 0.790 | 0.296 | 0.580 | 0.452 |
| bar recipe (e5 RRF → mMARCO @30 chunks) | 0.283 / 0.180 / 0.580 / 0.790 | 0.260 | 0.314 | 0.312 |
| `z3_equal` first stage (no reranker) | **0.587** / 0.500 / 0.800 / 0.850 | 0.454 | 0.747 | 0.606 |
| `z3_equal` → mMARCO @30 / @20 / @30 β 0.8 | 0.267 / 0.294 / 0.349 | 0.264 / 0.290 / 0.335 | 0.277 / 0.304 / 0.373 | 0.298 / 0.332 / 0.396 |
| **`z3_equal` → bge @20** | 0.503 / 0.390 / 0.800 / 0.850 | 0.369 | 0.661 | 0.520 |

Paired tests on the subsample: bge @20 vs mMARCO @30 on the same first stage **+0.235** [+0.149, +0.324]
(p < 0.001, 60 / 13 / 27; ruling +0.384, PQ +0.105 p 0.016), vs the bar's recipe **+0.220** [+0.135, +0.307]
(p < 0.001, 62 / 17 / 21), vs exp 03's first stage +0.076 (p 0.009) — and vs its own un-reranked first stage
**−0.084** [−0.155, −0.026] (p 0.011, 16 / 28 / 56; PQ −0.085, ruling −0.085). So on the mined population the
large reranker is far better than the small one (it reads a 78-word question), a `z3_equal` → bge @20 pipeline
beats the round-1 bar's recipe at p < 0.001, and it is still worse than not reranking at all: the reception field
already places the cited article at rank 1 for half of these questions (H@1 0.500) and bge demotes it for a
document that reads more like the question. Hit@10 and hit@30 are identical before and after (the reranker
only reorders the top 20); the whole loss is inside the top 10.


### 2.4 Logistic ranker trained on mined labels (`runs/ltr_tables.md`)

Candidates ≈ 127 / 134 articles per question (recall 0.950 human / 0.921 mined). C by grouped 5-fold CV on the mined
train half (`legs` 13 features: C 3.0, CV 0.521–0.525 flat; `cheap` 36 features: C 0.01, CV 0.551); six random
half-fits of the train half move the mined-val MRR by sd 0.003–0.006, coefficient signs agree 0.92 (`cheap`) /
0.69 (`legs`). What the ranker learns on the mined labels is one thing: **reception rank first** (`rec_logrank`
−0.58 / −1.47, `rec_z` +0.48 / +0.72), then the fused rank, then *colbert negative* (`colbert_z` −0.31 / −0.41 —
the leg is noise on 78-word questions), title overlap +0.26, shorter articles (+), region match −0.17 (mined
questions are mostly federal), i.e. it re-learns exp 20's reception + e5 fusion.

| run | human MRR train / **val** / all | human R@10 val / all | mined oof (304) MRR / H@1 / R@10 / R@30 | pq | ruling | mined val (fit on mined train) |
|---|---|---|---|---|---|---|
| ref – exp 14 logreg minimal+meta (oof, fitted on the human halves) | 0.667 / **0.519** / 0.608 | 0.812 / 0.825 | – | – | – | – |
| `z3_equal` first stage | 0.700 / **0.545** / 0.638 | 0.812 / 0.825 | 0.494 / 0.401 / 0.707 / 0.836 | 0.318 | 0.701 | 0.505 |
| exp 20 reception + e5 (reference, no fit) | 0.717 / 0.448 / 0.609 | 0.812 / 0.825 | 0.534 / 0.434 / 0.757 / 0.865 | 0.331 | 0.769 | 0.544 |
| `ltr__legs` fit on mined train → human / mined | 0.631 / **0.400** / 0.539 | 0.688 / 0.775 | 0.532 / 0.441 / 0.720 / 0.842 | 0.352 | 0.737 | 0.545 (resub 0.525) |
| `ltr__legs` fit on all mined → human | 0.622 / **0.440** / 0.549 | 0.750 / 0.800 | – | – | – | – |
| `ltr__cheap` fit on mined train → human / mined | 0.607 / **0.406** / 0.527 | 0.688 / 0.725 | **0.546** / 0.451 / 0.757 / 0.849 | 0.342 | **0.783** | **0.558** (resub 0.557) |
| `ltr__cheap` fit on all mined → human | 0.625 / **0.414** / 0.540 | 0.688 / 0.725 | – | – | – | – |

Paired tests: on the mined set the `cheap` ranker beats its own first stage (oof +0.052 [+0.026, +0.078],
p < 0.001, 98 / 57 / 149; mined val +0.053, p 0.005; ruling +0.082, PQ +0.024 n.s.) — but not exp 20's
reception + e5, the thing it re-learns (+0.012 [−0.009, +0.033], p 0.27, 72 / 68 / 164; PQ +0.011, ruling
+0.014) — and it beats the reception field alone by +0.015 (p 0.08; ruling +0.045, p 0.001). On the **human**
questions every fit is *below* the un-learned first stage (val 0.400–0.440 vs 0.545, all 0.527–0.549 vs 0.638,
−0.099 / −0.111 on all 40, p 0.03–0.05, 4–6 wins / 18–19 losses) and level with the round-1 bar (+0.005 /
+0.017 on all, p > 0.8), because the weights it learned (down-weight colbert, trust the reception rank) are
the wrong weights for short paraphrased questions, where colbert is the leg that finds B23 / B33 / B37.
The transfer failure is the finding: **a ranker fitted on the mined population does not transfer to the
citizen-phrased population**, exactly as the query-length choice did not. Exp 14's human-fitted logreg (oof
0.608 / val 0.519) remains the better ranker for the human set, and the honest ranker for a deployment that
serves both populations would need per-population features (question length is the obvious one) or a mixed
training set.


### 2.5 Length gate (coordinator's follow-up; cache-only, `gate.py`, `runs/gate_tables.md`)

The population-aware policy as **one** pipeline: a question of L words goes to `z3_equal` → mMARCO @30 β 0.8 when
L ≤ T and to the un-reranked reception + e5 fusion (`z_rec_e5`) otherwise; variant: `z3_equal` → bge @20 on the
long side (where bge pairs are cached: human 40, mined 100-question subsample). T ∈ {25, 35, 50} words, chosen on
the pooled MRR of the mined **train** split (145; 40 inside the subsample for the bge variant) + the human
**train** half (24): rec_e5 variant T = 25 (pooled 0.539 / 0.525 / 0.505), bge variant T = 35 (0.527 / 0.539 /
0.503). Questions per side (≤ T → mMARCO route / > T → long route): T = 25: human 35 / 5, mined 7 / 297
(subsample 2 / 98); T = 35: human 40 / 0, mined 26 / 278 (8 / 92); T = 50: human 40 / 0, mined 64 / 240 (20 / 80);
words per question: human median 20 (9–28), mined median 78 (11–133). The gate therefore routes almost every
human question to the reranker and almost every mined question to the un-reranked fusion — the two populations
barely overlap in length, and the five human questions above 25 words are the only ones the two routes contend for.
No new reranker pairs were scored (`cache/B_mmarco22.npz`, `B_bge22.npz`); 15 runs saved (`gate_T*__mmarco_b0.8__*`).

| run | human MRR train / **val** / all | human R@10 all | mined sub100 all / pq / ruling / val (MRR) | mined 304 all / pq / ruling / val |
|---|---|---|---|---|
| ref – round-1 bar / bar recipe | 0.490 / **0.570** / 0.522 | 0.825 | 0.283 / 0.260 / 0.314 / 0.312 | 0.223 / 0.184 / 0.271 / 0.242 |
| `z3_equal` → mMARCO @30 β 0.8 (un-gated) | 0.614 / **0.613** / 0.614 | 0.925 | 0.349 / 0.335 / 0.373 / 0.396 | 0.276 / 0.236 / 0.327 / 0.303 |
| `z_rec_e5` un-reranked (un-gated) | 0.696 / **0.478** / 0.609 | 0.825 | 0.643 / 0.467 / 0.851 / 0.675 | 0.536 / 0.335 / 0.769 / 0.547 |
| `z3_equal` → bge @20 (un-gated) | 0.575 / **0.569** / 0.572 | 0.875 | 0.503 / 0.369 / 0.661 / 0.520 | – |
| **gate T = 25: mMARCO β 0.8 ↔ `z_rec_e5`** (selected) | 0.639 / **0.613** / **0.628** | 0.900 | **0.643** / 0.467 / 0.851 / 0.675 | **0.534** / 0.334 / 0.769 / 0.545 |
| gate T = 35 / 50, same routes | 0.614 / 0.613 / 0.614 (both) | 0.925 | 0.639 / 0.605 (all) | 0.528 / 0.501 (all) |
| gate T = 35: mMARCO β 0.8 ↔ bge @20 (selected) | 0.614 / **0.613** / 0.614 | 0.925 | 0.529 / 0.378 / 0.707 / 0.552 | – |
| gate T = 25 / 50, bge variant | 0.609 / 0.613 / 0.611 · 0.614 / 0.613 / 0.614 | 0.925 | 0.509 · 0.505 (all) | – |

Paired tests (Δ = gated − base): the selected gate (T = 25, `z_rec_e5` on the long side) vs the **bar** is
+0.043 on human val [−0.146, +0.133] (7 / 1 / 8, p 0.52), **+0.149** on human train (12 / 2 / 10, p 0.006),
**+0.106 on all 40** [+0.029, +0.182] (19 / 3 / 18, **p 0.011**); on the mined subsample **+0.360** [+0.279,
+0.440] (70 / 8 / 22, p < 0.001; PQ +0.207, ruling +0.537, val +0.363) and on all 304 mined questions **+0.311**
[+0.266, +0.357] (221 / 26 / 57, p < 0.001; PQ +0.150, ruling +0.498). Vs the un-gated pipelines it is, by
construction, the better of the two on each population: vs `z3_equal` → mMARCO β 0.8 +0.015 on human all (2 / 1 /
37: the five long human questions, B21 / B11 up, B3 down; val identical) and +0.293 on the subsample / +0.258 on
the 304 (p < 0.001); vs `z_rec_e5` un-reranked +0.136 on human val [−0.045, +0.329] (6 / 2 / 8, p 0.19), −0.057
on human train, +0.020 on all 40 (p 0.75), and −0.002 on the 304 (1 / 2 / 301: the seven mined questions of ≤ 25
words). The bge variant (T = 35) is identical to the un-gated mMARCO pipeline on the human set (no human question
exceeds 35 words) and on the subsample it is +0.246 over the bar recipe (p < 0.001) but **−0.114 below the rec_e5
gate** [−0.177, −0.058] (11 / 41 / 48, p < 0.001) — the un-reranked fusion remains the right long-side route.

Reading: the gate is the first single B pipeline that is above the bar on every reported slice — human val +0.04
(directional), human all +0.11 (p 0.01), mined +0.31 / +0.36 (p < 0.001) — but it earns that by *routing*,
not by combining: with T = 25 the human set is 35 / 5 and the mined set 7 / 297, so the gate is a switch between
two pipelines that were each already the best on their own population, and its only genuine test is the ten
questions near the boundary (five human > 25 words, seven mined ≤ 25), where it is +0.015 / −0.002. The word
count is a proxy for "citizen question vs pasted document"; a deployment would rather gate on that intent
directly (or on the reranker's own confidence), and the selected T is a train-split choice that any threshold
between 25 and 35 reproduces on the human set (T = 35 / 50 give the un-gated mMARCO numbers there).

## 3. Conclusion

**Is there now a B pipeline that beats val 0.570 / full 0.522 with p < 0.05 on the mined set and directionally on
the human set?** Split the answer by population, because the two populations disagree about every component.

* **Human questions (the bars' population).** Yes, directionally, and for the first time on both halves:
  `z3_equal` (reception BM25F ⅓ + colbert-fr ⅓ + e5-small ⅓, z-scores, no tuning) → mMARCO @30 gives **val 0.651
  / all 0.569** reranker-only (vs the bar +0.081 val, 5 / 0 / 11, p_perm 0.06; +0.047 all, 10 / 2 / 28) and **val
  0.613 / all 0.614** with exp 14's fixed β 0.8 (+0.092 all, 19 / 2 / 19, **p 0.012** — the only bar comparison
  that clears p < 0.05 on the human set, on the full 40); it is level with the round-2 best (+0.04 val / −0.01
  all with β 0.8, that run's train half being tuned). The first stage alone is val 0.545 / all 0.638 / R@30 0.938
  / 0.950, the best B first stage measured (+0.097 val over exp 20's fusion, 7 / 0 / 9, p_perm 0.016; +0.140 all
  over exp 12's colbert + BM25, p 0.012). bge @20 behind it only ties the bar (val 0.569 / all 0.572).
* **Mined questions (304, leak-free).** Yes at p < 0.05 — but not with a cross-encoder. mMARCO-MiniLM is
  destructive on 78-word questions (the bar's own recipe: 0.359 → 0.223; ours: 0.494 → 0.213, p < 0.001) and
  bge @20 on the 100-question subsample, although +0.22 over the bar's recipe (p < 0.001), is −0.084 below the
  un-reranked first stage (p 0.011). The pipelines that beat the bar's recipe (0.223) at p < 0.001 are the
  **un-reranked first stages**: exp 20's reception + e5 0.534, this experiment's `z_rec_e5` 0.536 and
  `z3_equal` 0.494, and the mined-trained logistic ranker 0.546 (oof; +0.052 over `z3_equal`, p < 0.001, but only
  +0.012 over reception + e5, p 0.27). On this population **colbert-fr is the weakest leg** (0.203 alone;
  `z3_equal` is −0.040 below reception + e5, p < 0.001, the loss on the ruling slice) and neither a 256-token query
  window (+0.003 on the mined val half, −0.059 on human val) nor trimming its expansion repairs it.
* **What transfers and what does not.** The reception field transfers (it carries both sets); colbert-fr is a
  short-question leg; every choice made on the mined train split — the colbert query length, the logistic
  ranker's weights (reception rank first, colbert negative) — is right for the mined val half and wrong for the
  40 human questions (ranker val 0.400–0.440 vs 0.545 un-learned; −0.10 on all 40, p 0.03–0.05). The two
  pre-registered weightings are indistinguishable (±0.02, p > 0.4), z-score and min-max fusion are the same
  (≥ 216 / 304 ties), exp 20's convex-0.5 finding holds. The honest recommendation for the MCP server is
  population-aware: three-leg z-score fusion + mMARCO (β 0.8) for citizen-length questions, reception + e5 with
  **no cross-encoder** (or a length gate in front of one) for long, document-like queries — and a reranker that
  has seen long legal queries (distillation on the mined pairs, ideas 13 / 76) before any reranker is trusted on
  them. As one pipeline (§2.5, length gate at 25 words, cache-only follow-up): human val 0.613 / all 0.628, mined
  304 0.534 — above the bar on every slice (all 40: +0.106, p 0.011; mined: +0.311, p < 0.001; val +0.043 directional),
  by routing rather than combining.

**Cost per query** (4 threads, shared box): reception BM25F 2.3–2.8 ms; e5-small dot product ≈ 1 ms plus the
query encoding; colbert-fr brute-force MaxSim over 10,869 chunks **0.73 s** at 48 query tokens (2.3 s trimmed /
4.2 s at 256; PLAID would bring it to ms; the fp16 token index is 0.6 GB); mMARCO @30 ≈ 74 pairs ≈ 8.6 s (the
bar's recipe: 30 pairs, 3.5 s); bge @20 ≈ 21 s. One-off: corpus encoding with colbert-fr 38 min (210 ms /
chunk); 24,916 + 5,611 mMARCO pairs 59 min; 2,800 bge pairs 49 min; all under the torch lock.

## 4. Files

`common22.py` (question sets, reference runs, z-score fusion, metrics per split / slice, paired tests, saving
with the mined question-file stamp, chunk universe), `colbert_scores.py` (PyLate, exp-12 venv; `--query-length`,
`--trim`; persists the token matrix), `legs.py` (reception / e5 / exp-03 BM25 legs, attaches the colbert variants),
`run_stage1.py` (fusions, selection on mined train, reference reproductions, tests, reranker candidates with the
best-3-chunk cap), `rerank_score.py` (mMARCO / bge score caches, reuse of exp 20 / 14, 100-question subsample),
`run_rerank.py` (reranked pipelines, bar recipe, tests, per-question ranks), `ltr.py` (logistic ranker;
`EXP22_LTR_PIPE` pins the first stage), `gate.py` (length gate, cache-only; `runs/gate.json`, `runs/gate_tables.md`), `run_chain1b.sh` / `run_chain2.sh` (the sequences actually run; `run_chain.sh`
is the first attempt without the chunk cap, abandoned at 85k pairs), `cache/` (colbert scores for 48 / 256 /
256-trimmed queries, the fp16 token matrix, legs, candidates, reranker caches, subsample), `runs/` (`stage1`,
`rerank`, `ltr` JSON + tables), `logs/`. Every run (65 result files, 140 leaderboard rows incl. re-saves) is in `experiments/results/22_reception_colbert/` (per-question
ranks; mined runs end in `__mined`) and in `leaderboard.jsonl`.


