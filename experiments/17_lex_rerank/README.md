# 17 – Experiment-13 lexical first stage + bge-reranker-v2-m3

Does the improved lexical retriever of experiment 13 (BM25F title boost, exp-01 tokenizer, thousand-group
number normalisation, per-corpus k1/b, cleaned articles on B) make a better *first stage* for the
bge-reranker-v2-m3 cross-encoder than the old first stages did? Bars to beat, **val** split
(`Question.split`, 50/50 by question-id hash): corpus **C 0.665** (exp 09: BM25 tok03 chunks + bge @30) and
corpus **B 0.570** (exp 03: e5-small + BM25 RRF + mMARCO-MiniLM @30). Full-set bests: C 0.703, B 0.522.

```bash
cd experiments/17_lex_rerank
# the exp-14 venv already holds torch / sentence-transformers / bm25s / PyStemmer / rag-eval; `uv sync` also works
PY=../14_ltr_fusion/.venv/bin/python
$PY build_lexical.py --corpus B && $PY build_lexical.py --corpus C          # stage 1: exp-13 ranking, top-200 units/question (B 3 s, C 1 min)
./run_queue17.sh                                                            # stage 2: reranker, one torch process, 4 threads (waits for other torch jobs)
$PY evaluate.py --corpus C && $PY evaluate.py --corpus B && $PY evaluate.py --corpus B --tag _len1024   # stage 3
```

Results: `experiments/results/17_lex_rerank/<corpus>__<run>.json` (29 runs, all in `leaderboard.jsonl`),
tables + per-question val ranks + tests in `runs/<corpus>_tables*.md` / `runs/<corpus>_eval*.json`, logs in `logs/`.

## Setup

* **First stage** (`build_lexical.py`, `common17.LEX_CONFIG`) – exp 13's final configuration per corpus,
  chosen on train there and not re-tuned here: tokenizer `tok01+num` (bm25s French stoplist + question words,
  NFKD folding, Snowball, `50.000 → 50000`); C: `fixed_chunks(1200, 100)` units, BM25F title ×8 / body ×1,
  k1 0.9, b 0.4 (title b 0.75); B: cleaned articles (exp 08 `clean_article`), `article_chunks(2000, 150)`
  units, BM25F title ×8 / heading path ×3 / body ×1, k1 1.5, b 0.75 (title/heading b 0.3), code-family cue
  tokens (`dtcir92`, `dtctva`, …) with query weight 1. Built from exp 13's cached tokenisation
  (`../13_lexical_upgrades/.cache`); the document ranking reproduces the per-question ranks saved by
  exp 13 **exactly** (B 40/40, C 64/64; val MRR 0.616 on C, 0.341 on B).
* **Candidates** – the top-*depth* units (chunks) of that ranking, depth ∈ {20, 30, 50}, as in exp 03/09;
  document = best reranked chunk; the lexical ranking is appended below the reranked block (so ranks > depth
  are the lexical ones instead of the arbitrary order that a `-1e9` fill gives in exp 03/09).
* **Reranker** – `BAAI/bge-reranker-v2-m3` (sentence-transformers `CrossEncoder`, CPU, 4 threads,
  batch 8, **max_length 512**). Texts: C = the title-prefixed chunk text (identical to exp 09/14), B = title
  + heading path + cleaned 2,000-char unit. Exp 14's cache (`14_ltr_fusion/cache/C_rerank_bge-reranker-v2-m3.npz`,
  scored at max_length 1024) is reused on C for every (question, chunk) pair that fits in 512 tokens (1,198 of
  3,200 pairs; 8 cached pairs longer than 512 tokens were re-scored so that every score in a run comes from the
  same truncation). On B the exp-14 chunks are different texts (`article_ctx_1200`, raw articles) so nothing
  was reusable; B was scored twice, at 512 and at 1024 tokens (50 % of its pairs exceed 512 tokens; C: 0.8 %).
* **Interpolation** – `β · minmax(reranker) + (1 − β) · minmax(BM25F)` over the candidate set, β ∈ {0.5, 0.7,
  1.0 (= reranker only)}, β chosen per depth on **train** MRR, reported on val.
* **Significance** (`evaluate.py`) – per-question reciprocal-rank differences on val vs the bar pipeline's
  stored per-question ranks (`results/09_corpus_c/C__bm25__fixed1200_title__bm25_bge-reranker-v2-m3_30.json`,
  `results/03_hybrid_rerank/B__e5-small__article_ctx_1200__rrf_mmarco-minilm_30.json`): paired t-test, two-sided
  sign test (ties excluded), Wilcoxon signed-rank, bootstrap 95 % CI of the mean difference (20k resamples).
* R@10 below = the first expected document is in the top 10 (`rag_eval.splits` convention); MRR / H@1 as usual.

## Results

### Corpus C (21,259 docs → 201,404 chunks; 64 questions: 29 train / 35 val)

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | cost / query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| exp 09: BM25 tok03 on chunks (old first stage) | 0.626 | 0.536 | 0.577 | 0.517 | 0.400 | 0.453 | 0.857 | 0.844 | ms |
| exp 13 lexical (this first stage), no reranker | 0.764 | 0.616 | 0.683 | 0.724 | 0.486 | 0.594 | 0.886 | 0.875 | 27 ms |
| **bar** – exp 09: BM25 tok03 + bge-reranker-v2-m3 @30 | 0.734 | **0.665** | 0.696 | 0.655 | 0.543 | 0.594 | 0.886 | 0.875 | 21 s (exp 09) |
| exp 13 lexical + bge @20 | 0.757 | **0.688** | 0.719 | 0.690 | 0.571 | 0.625 | 0.914 | 0.891 | 19 s |
| exp 13 lexical + bge @20, β = 0.7 (β chosen on train; **train-selected depth+β**) | 0.803 | 0.675 | 0.733 | 0.759 | 0.571 | 0.656 | 0.914 | 0.891 | 19 s |
| exp 13 lexical + bge @20, β = 0.5 | 0.786 | 0.645 | 0.709 | 0.724 | 0.514 | 0.609 | 0.914 | 0.891 | 19 s |
| **exp 13 lexical + bge @30** (the pipeline under test) | 0.734 | **0.675** | 0.702 | 0.655 | 0.543 | 0.594 | 0.943 | 0.906 | 28 s |
| exp 13 lexical + bge @30, β = 0.7 (β chosen on train) | 0.786 | 0.678 | 0.727 | 0.724 | 0.571 | 0.641 | 0.943 | 0.906 | 28 s |
| exp 13 lexical + bge @30, β = 0.5 | 0.786 | 0.648 | 0.710 | 0.724 | 0.514 | 0.609 | 0.943 | 0.906 | 28 s |
| exp 13 lexical + bge @50 | 0.734 | 0.662 | 0.695 | 0.655 | 0.543 | 0.594 | 0.914 | 0.891 | 47 s |
| exp 13 lexical + bge @50, β = 0.7 (β chosen on train) | 0.786 | 0.677 | 0.726 | 0.724 | 0.571 | 0.641 | 0.914 | 0.891 | 47 s |
| exp 13 lexical + bge @50, β = 0.5 | 0.786 | 0.661 | 0.718 | 0.724 | 0.543 | 0.625 | 0.943 | 0.906 | 47 s |

Paired tests on val (n = 35) vs the bar, reciprocal-rank differences:

| run | mean Δrr | wins / losses / ties | paired t p | sign test p | Wilcoxon p | bootstrap 95 % CI |
|---|---:|---|---:|---:|---:|---|
| lex13 + bge @20 | +0.023 | 4 / 1 / 30 | 0.19 | 0.38 | 0.22 | [−0.004, +0.061] |
| lex13 + bge @20, β 0.7 | +0.010 | 6 / 7 / 22 | 0.76 | 1.00 | 0.89 | [−0.055, +0.074] |
| **lex13 + bge @30** | **+0.010** | **2 / 0 / 33** | **0.30** | **0.50** | 0.18 | [+0.000, +0.030] |
| lex13 + bge @30, β 0.7 | +0.014 | 5 / 5 / 25 | 0.69 | 1.00 | 0.65 | [−0.052, +0.076] |
| lex13 + bge @50 | −0.003 | 1 / 5 / 29 | 0.77 | 0.22 | 0.35 | [−0.019, +0.016] |
| lex13 lexical only | −0.049 | 6 / 10 / 19 | 0.28 | 0.45 | 0.27 | [−0.139, +0.034] |

Val changes at depth 30 vs the bar: C40 *abus fiscal* (not in top 50 → 3; the old BM25 never retrieved the
document, the new one puts it at 8 and the reranker lifts it) and C27 *frontalier Luxembourg* (11 → 9); all
other 33 val questions get the same rank — the two pipelines share the reranker and their top-30 candidate
sets overlap almost entirely. At depth 20 the tail candidates that mislead the reranker are gone (C25 6 → 16
is the one loss); at depth 50 they hurt (C39 2 → 3, C47 6 → 8, C48 4 → 7). The lexical wins that the reranker
undoes: C51 (lexical 1 → reranked 2), C64 (1 → 2), C25 (16 → 6 is a reranker win, but lexical 5 in exp 09).

### Corpus B (5,853 articles → 8,035 units; 40 questions: 24 train / 16 val)

| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | cost / query |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| exp 03: e5-small + BM25 RRF (old first stage) | 0.481 | 0.420 | 0.457 | 0.292 | 0.312 | 0.300 | 0.750 | 0.750 | ms + dense |
| exp 13 lexical (this first stage), no reranker | 0.458 | 0.341 | 0.411 | 0.333 | 0.250 | 0.300 | 0.625 | 0.625 | 1 ms |
| **bar** – exp 03: e5-small + BM25 RRF + mMARCO-MiniLM @30 | 0.490 | **0.570** | 0.522 | 0.292 | 0.438 | 0.350 | 0.812 | 0.825 | 2 s |
| exp 03: e5-small + BM25 RRF + bge-reranker-v2-m3 @30 (same reranker, old first stage) | 0.562 | 0.450 | 0.518 | 0.417 | 0.312 | 0.375 | 0.750 | 0.825 | ≈20 s |
| exp 13 lexical + bge @20 | 0.567 | **0.443** | 0.517 | 0.500 | 0.312 | 0.425 | 0.625 | 0.675 | 20 s |
| exp 13 lexical + bge @20, β = 0.7 (β chosen on train) | 0.569 | 0.367 | 0.488 | 0.500 | 0.188 | 0.375 | 0.625 | 0.675 | 20 s |
| exp 13 lexical + bge @20, β = 0.5 | 0.558 | 0.411 | 0.499 | 0.500 | 0.312 | 0.425 | 0.625 | 0.675 | 20 s |
| **exp 13 lexical + bge @30** (the pipeline under test) | 0.564 | **0.440** | 0.514 | 0.458 | 0.312 | 0.400 | 0.625 | 0.700 | 31 s |
| exp 13 lexical + bge @30, β = 0.7 (β chosen on train; **train-selected depth+β**) | 0.570 | 0.367 | 0.489 | 0.500 | 0.188 | 0.375 | 0.625 | 0.725 | 31 s |
| exp 13 lexical + bge @30, β = 0.5 | 0.566 | 0.411 | 0.504 | 0.500 | 0.312 | 0.425 | 0.625 | 0.700 | 31 s |
| exp 13 lexical + bge @50 | 0.559 | 0.424 | 0.505 | 0.458 | 0.312 | 0.400 | 0.625 | 0.700 | 51 s |
| exp 13 lexical + bge @50, β = 0.7 (β chosen on train) | 0.569 | 0.391 | 0.498 | 0.500 | 0.250 | 0.400 | 0.625 | 0.725 | 51 s |
| exp 13 lexical + bge @50, β = 0.5 | 0.566 | 0.414 | 0.505 | 0.500 | 0.312 | 0.425 | 0.625 | 0.700 | 51 s |
| same at max_length 1024: @20 / @30 / @50 (`*_len1024` runs) | 0.562 / 0.544 / 0.528 | 0.443 / 0.443 / 0.440 | 0.514 / 0.503 / 0.493 | | | | | | 25 / 37 / 62 s |

Paired tests on val (n = 16) vs the bar:

| run | mean Δrr | wins / losses / ties | paired t p | sign test p | Wilcoxon p | bootstrap 95 % CI |
|---|---:|---|---:|---:|---:|---|
| lex13 + bge @20 | −0.128 | 4 / 5 / 7 | 0.29 | 1.00 | 0.31 | [−0.354, +0.083] |
| **lex13 + bge @30** | **−0.131** | **4 / 5 / 7** | **0.28** | **1.00** | 0.31 | [−0.355, +0.078] |
| lex13 + bge @30, β 0.7 | −0.204 | 4 / 6 / 6 | 0.08 | 0.75 | 0.10 | [−0.418, −0.006] |
| lex13 + bge @50 | −0.146 | 3 / 5 / 8 | 0.23 | 0.73 | 0.23 | [−0.371, +0.063] |
| lex13 lexical only | −0.230 | 4 / 6 / 6 | 0.09 | 0.75 | 0.11 | [−0.479, +0.005] |
| lex13 + bge @30 vs exp-03 RRF + **bge** @30 | −0.011 | 4 / 5 / 7 | 0.89 | 1.00 | 0.77 | |

The three val questions the bar answers at ranks 3 / 1 / 1 and this pipeline misses entirely (not in the top
50 of the lexical stage): B16 *100 euros à une ONG reconnue* (statute: *libéralités … institutions agréées*),
B23 *SRL 80.000 euros de bénéfice* (rate article), B26 *cours particuliers, dois-je facturer la TVA* — the
layman ↔ statute vocabulary gap that only the dense leg bridges. The reranker fixes what the lexical stage
retrieves (B14 8 → 1, B15 8 → 2, B6 6 → 5, B1 5 → 3) but cannot recall what it does not.

## Conclusions

1. **Corpus C: the new pipeline matches the bar, it does not beat it in any demonstrable way.** Exp-13 lexical +
   bge @30 gives val MRR **0.675 vs 0.665** (+0.010, hit@1 0.543 = 0.543, R@10 0.943 vs 0.886): 2 val questions
   improve, 0 worsen, 33 are identical; paired t p = 0.30, sign test p = 0.50. Depth 20 is the best val number
   (0.688, 4 wins / 1 loss, p = 0.19) and the train-selected configuration (depth 20, β 0.7) gives 0.675 val /
   **0.733 on the full set** (above the full-set best 0.703, but that is a train-heavy number: 0.803 train).
   With 35 val questions and two shared components (the same reranker, ~90 % overlapping candidates) no
   configuration reaches significance; the honest reading is *"+0.01–0.02 val MRR, consistent in sign, not
   proven"*. The +0.08 val that the lexical upgrade gave on its own (0.536 → 0.616, 13 wins / 3 losses, sign
   test p = 0.02 vs the old BM25) mostly disappears once the cross-encoder reorders the candidates: the
   reranker already recovered most of what a better first stage recovers, and it also undoes some lexical
   wins (C51, C64).
2. **Corpus B: the new pipeline is below the bar and the bar is not the right comparison for a lexical
   stage.** Val MRR **0.440 vs 0.570** (−0.13; 4 / 5 / 7; p = 0.28, sign p = 1.0; not significant with 16 val
   questions, but the bootstrap CI is [−0.36, +0.08] and every configuration is negative). Full set: 0.514–0.517
   vs 0.522, a tie. Two things are going on: (a) the mMARCO bar on B has an unusual val/train profile
   (val 0.570, train 0.490) whereas the same first stage with bge gives val 0.450 / train 0.562 — the "bar"
   partly is split noise; against the exp-03 **bge** run the lexical first stage is exactly level (−0.011,
   p = 0.89), so replacing the hybrid first stage by the exp-13 lexical stage costs nothing when the reranker is
   fixed; (b) three val questions are unreachable for any lexical stage (B16, B23, B26: not in the top 50) —
   B's failure mode is recall through the vocabulary gap, which needs the dense leg or an LLM query rewrite,
   not a better reranker. So on B: keep the dense leg (RRF) in front of the reranker.
3. **Interpolating the reranker score with BM25F (β) does not transfer.** β = 0.7 is chosen on train at every
   depth on both corpora (+0.05 train MRR on C, +0.005 on B) and gives on val +0.003 (C @30) and **−0.07 (B
   @30: 0.440 → 0.367)**; β = 0.5 is worse than the plain reranker everywhere on val. The BM25F score encodes
   the title match that the questions were written from, which is exactly what over-fits train. Use the
   reranker score alone.
4. **Depth: 20–30 is right, 50 hurts.** On C val: 0.688 / 0.675 / 0.662 for 20 / 30 / 50; on B 0.443 / 0.440 /
   0.424. Deeper candidate lists add documents that bge ranks above the right one (C39, C47, C48), and cost
   grows linearly.
5. **max_length 512 is enough** even where it truncates: on B 50 % of the (question, unit) pairs exceed 512
   tokens, yet 512 vs 1024 gives the same val MRR (0.443 / 0.440 vs 0.443 / 0.443 at depth 20 / 30) for
   +20 % time per pair (1.02 → 1.23 s). On C 0.8 % of the pairs exceed 512 tokens.
6. **Cost per query** (4 threads, idle 4-core box, bge-reranker-v2-m3 at 512 tokens): lexical stage 27 ms (C,
   201k chunks) / 1 ms (B) + **0.94 s per pair** on C (0.7 s in exp 09 with the older torch) and 1.02 s on B →
   **19 s @20, 28 s @30, 47 s @50** on C; 20 / 31 / 51 s on B. The exp-14 cache saved 37 % of the C pairs.
   The reranker is the whole cost; the first stage is free. A GPU brings this to well under a second.

**Verdict.** The stronger lexical first stage is worth having (it is free, and it raises the no-reranker
baseline on C by +0.08 val), but *lexical + bge-reranker* does not beat the validation bars: on C it is
+0.010 val MRR (0.675 vs 0.665, p ≈ 0.3, 2 wins / 0 losses), on B it is −0.13 (0.440 vs 0.570, p ≈ 0.3) because
the lexical stage cannot retrieve three of the sixteen val questions at all. For the MCP stack this means:
exp-13 lexical leg + dense leg (for recall on paraphrased questions) → bge-reranker on the top 20–30, reranker
score only, no BM25 interpolation.

## Files

* `common17.py` – exp-13 configurations, stage-1 cache format, bar / reference result paths, helpers.
* `build_lexical.py` – stage 1 (rebuilds the exp-13 ranking from `../13_lexical_upgrades/.cache`, verifies it
  against the saved exp-13 per-question ranks and against exp 14's chunk indices, caches texts + scores).
* `rerank.py` – stage 2 (bge-reranker-v2-m3; reuses exp-14 pairs that fit in `--max_length`; resumable;
  `--tag` for a second cache such as `_len1024`).
* `evaluate.py` – stage 3 (depth × β grid, train selection, paired tests, markdown tables).
* `run_queue17.sh` – the sequential torch queue used for the runs (waits for other torch jobs first).
* `cache/` (git-ignored): `<corpus>_lex.{npz,json}`, `<corpus>_lex_texts.json`, `<corpus>_rerank_bge-reranker-v2-m3[_len1024].npz`
  (exp-14 format: `q_idx / chunk_idx / score`, plus `src` = 1 for pairs copied from exp 14).
