# 16 — In-domain Belgian legal retrieval models (Maastricht Law & Tech) and BSARD fine-tuning

**Question.** Do the publicly available *Belgian legal French* retrieval models (trained on Belgian statutory
articles) transfer to our tax corpora better than the general mMARCO models used so far, and does fine-tuning
our own cheap models on BSARD (the public Belgian statutory-article retrieval dataset) help?

Protocol: same corpora, chunkers, French-normalised BM25 and metrics as experiments 03 / 09 / 15
(`rag_eval` harness, document-level MRR, chunk score = max over a document's chunks). Rerankers rescore the
BM25 top-30 chunks; bi-encoders are scored dense-only and fused with BM25 (RRF and convex 0.3/0.5/0.7).
Question sets are tiny (A 29, B 40, C 64 questions; val split 12 / 16 / 35), so differences below ~0.05 MRR
are noise — read the tables as "same / clearly better / clearly worse".

## Models and data (licences)

| asset | what | licence | notes |
|---|---|---|---|
| `maastrichtlawtech/monobert-legal-french` | CamemBERT-base cross-encoder (110M) fine-tuned on LLeQA from `antoinelouis/crossencoder-camembert-base-mmarcoFR` | MIT | 443 MB, max_len 512 |
| `maastrichtlawtech/dpr-legal-french` | CamemBERT-base siamese bi-encoder (mean pooling, 768-d, max_seq 512, no prefixes) fine-tuned on LLeQA | MIT | 443 MB, sentence-transformers layout |
| `maastrichtlawtech/colbert-legal-french` | CamemBERT ColBERT (colbert-ai checkpoint, `artifact.metadata`) | MIT | **not run**: needs PyLate/RAGatouille in a separate venv (exp 12 pins ST 5.3 / torch 2.11); no time budget left |
| `maastrichtlawtech/bsard` | 22,633 Belgian statutory articles + 1,108 citizen questions (886 train / 222 test) + synthetic questions | **CC BY-NC-SA 4.0** | research use only — a BSARD-trained model cannot ship in a commercial product without a separate licence |
| `maastrichtlawtech/lleqa` | long-form legal QA (the training set of the three models above) | gated (signed data-use agreement) | not loadable here, so nothing was trained on LLeQA |

The three Maastricht models were themselves trained on LLeQA, not on BSARD, so BSARD is a genuinely
different (but same-domain) training set for our fine-tunes and the BSARD *test* split is a fair in-domain
sanity check for every model here.

## Setup

Standalone uv project (same pins as experiment 15: torch 2.14 cpu, sentence-transformers 6.1,
transformers 5.17, datasets 5.0.1). The box's root disk was full when the experiment started, so the
chunk / BM25 / embedding caches and logs live on `/dev/shm/exp16` (< 1 GB); results go to
`experiments/results/16_legal_models/` and the leaderboard through `rag_eval.save_result`.

```bash
cd experiments/16_legal_models && uv sync
uv run python run_rerank.py --model maastrichtlawtech/monobert-legal-french --corpora A,B,C   # stage 1a
uv run python run_dense.py  --model maastrichtlawtech/dpr-legal-french --corpora A,B          # stage 1b
uv run python bsard_data.py                                                                   # BSARD pairs (cached json)
uv run python finetune_ce_bsard.py --base cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 --n_q 1000 --max_len 256 --save  # stage 2
uv run python run_rerank.py --model models/mmarco-minilm-bsard --tag mmarco-minilm-bsard-len512 --max_len 512    # stage 2 at 512
uv run python finetune_bi_bsard.py --base intfloat/multilingual-e5-small                      # stage 3
```

Files: `common16.py` (env, chunk/BM25 caches, rerank and dense/fusion evaluation, result saving),
`run_rerank.py`, `run_dense.py`, `bsard_data.py` (BSARD → (question, positive article, BM25 hard negatives)),
`finetune_ce_bsard.py`, `finetune_bi_bsard.py`. Fine-tuned models are written to `models/` (git-ignored).

### BSARD training pairs

`bsard_data.build_pairs(n_questions=3000, n_neg=3)`: the 886 real train questions plus 2,114 synthetic ones
(shuffled, seed 0); article text = heading path + body, truncated to 1,500 chars (mean 730, median 570 chars,
i.e. the size of our chunks); positive = the labelled article with the best BM25 score for the question;
negatives = 3 random picks among the BM25 top-20 non-labelled articles (same French-normalised tokenizer as
experiment 03). 3,000 pairs, none skipped, built in 22 s.

## Results

Document-level MRR on all questions, with the harness' val-split MRR in parentheses where the run has one
(A: 12 val q, B: 16, C: 35). Baselines are the leaderboard rows of experiments 02 / 03 / 09 / 13 / 15 on the
same chunks. All rows of this experiment are in `experiments/results/16_legal_models/` and
`results/leaderboard.jsonl` (`experiment = 16_legal_models`).

### Stage 1a — zero-shot rerankers on BM25 top-30

| reranker (BM25 top-30 chunks) | A | B | C | s / query (2 threads, shared box) |
|---|---:|---:|---:|---:|
| BM25 alone (exp 13, French-normalised) | 0.695 (0.736) | 0.338 (0.290) | 0.601 (0.546) | – |
| mMARCO-MiniLM-L12 zero-shot (exp 15, max_len 512) | 0.604 (0.534) | 0.494 (0.500) | 0.593 (0.545) | ~2 |
| **monobert-legal-french** zero-shot (max_len 512) | **0.639 (0.603)** | 0.465 (0.427) | 0.594 (0.597) | 47 (A), 110M params |
| bge-reranker-v2-m3 (exp 03 / 09) | 0.678 (RRF cand.) | 0.517 (RRF cand.) | 0.696 | 20–24 |

monobert = mMARCO-MiniLM on B and C (0.465 vs 0.494, 0.594 vs 0.593), slightly better on A (0.639 vs 0.604,
nDCG@5 0.740 vs 0.713), everywhere below bge-reranker-v2-m3 and, on A and C, below plain BM25. It is a
CamemBERT-base, so 5× the cost of MiniLM for no gain on our questions.

### Stage 1b — dpr-legal-french as the dense leg

| dense leg | A dense | A best fusion | B dense | B best fusion |
|---|---:|---:|---:|---:|
| e5-small (exp 02/03) | 0.508 | 0.598 RRF (LanceDB, exp 04) | 0.438 | 0.457 RRF |
| e5-base (exp 02) | 0.641 | – | 0.469 (cleaned chunks) | – |
| bge-m3 (exp 02/03) | 0.678 | 0.691 convex 0.5 | too slow on CPU | – |
| **dpr-legal-french** | 0.575 (val 0.475) | **0.712 convex 0.7** (val 0.653; RRF 0.647, convex 0.3/0.5 0.671/0.685) | **0.242** (val 0.183) | 0.449 convex 0.5 (val 0.467; RRF 0.411) |

Encoding cost: 0.77 s per chunk on this shared box (A 826 s, B 6,448 s = 1.8 h for 10.9k chunks), i.e. the
cost of e5-base for e5-small/e5-base quality on A and *worse than every model tried* on B (R@10 0.45 vs 0.70 for
e5-small). Its A fusion number (0.712) is the best all-question fusion on A so far, but its val MRR (0.653) is
below BM25 alone (0.736) — the gain sits on the 17 train questions and 29 questions cannot separate 0.69 from 0.71.

### Stage 2 — cross-encoder fine-tuned on BSARD

`finetune_ce_bsard.py --n_q 1000 --n_neg 3 --max_len 256 --batch 16 --epochs 1` on top of
`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`: 886 real + 114 synthetic questions, 4,000 (query, passage, label)
rows, BCE loss, lr 2e-5, 250 steps, 65 min on the shared box (a first attempt with 3,000 questions / 500 steps
was killed at 22 s/step). Model saved in `models/mmarco-minilm-bsard/` (git-ignored).

| reranker on BM25 top-30 | BSARD test (100 q, article level) | A | B | C |
|---|---:|---:|---:|---:|
| BM25 alone | 0.231 | 0.695 (0.736) | 0.338 (0.290) | 0.601 (0.546) |
| mMARCO-MiniLM zero-shot | 0.304 | 0.604 (0.534) | 0.494 (0.500) | 0.593 (0.545) |
| mMARCO-MiniLM + BSARD, eval max_len 256 | **0.360** | 0.529 (0.434) | 0.454 (0.512) | 0.498 (0.498) |
| mMARCO-MiniLM + BSARD, eval max_len 512 | – | 0.567 (0.432) | 0.490 (0.491) | 0.575 (0.545) |

The fine-tune does what it is trained for — in-domain BSARD test MRR +18 % over the zero-shot model (0.304 →
0.360, H@1 0.22 → 0.29) after a single epoch on 886 questions — and brings **no gain on our corpora**. Scored
at the same max_len 512 as the experiment-15 baseline it is equal to the zero-shot model on B (0.490 vs 0.494)
and C (0.575 vs 0.593, val 0.545 = 0.545) and worse on A (0.567 vs 0.604; val 0.432 vs 0.534, H@1 0.41 vs
0.45). The larger drops of the max_len 256 row (A −0.08, B −0.04, C −0.10) are mostly **truncation**: our
chunks are ~350–450 XLM-R tokens, so at 256 the second half of every chunk is unseen (C: 0.498 → 0.575 just by
scoring at 512). What remains after that is explained by:

1. **Task mismatch.** BSARD questions are citizen questions ("Puis-je refuser de faire des heures
   supplémentaires ?") against short statutory articles (median 570 chars) of the civil, labour, penal and
   regional codes; our questions are practitioner tax questions against 1,200–1,500-char chunks of circulars,
   commentaries and CIR articles. The model learns BSARD's question style and code vocabulary, not tax, and
   was trained on ≤ 256-token pairs while our chunks are longer.
2. **False negatives in the hard negatives.** BSARD labels a handful of articles per question; the BM25
   top-20 "non-relevant" articles used as negatives are often neighbouring articles of the same section.
   With BCE the model is pushed to score lexically-matching, topically-relevant passages as 0 — exactly the
   passages that are relevant in our corpora, where BM25 candidates are already good (H@5 0.90 on A). This is
   what costs A its H@1.
3. **No replay of the mMARCO signal.** 250 full-model steps at lr 2e-5 on 4k rows of one narrow
   distribution move a 118M model away from general passage relevance; the loss plateaus at ~0.45 after
   50 steps, i.e. most of the epoch is spent fitting the noisy negatives rather than learning.

### Stage 3 — e5-small fine-tuned on BSARD: not run

`finetune_bi_bsard.py` is ready (MultipleNegativesRankingLoss, in-batch + one BM25 hard negative, 1 epoch,
then `run_dense.py` on A/B), but the same training signal regressed the cross-encoder on every corpus and the
bi-encoder run needs ~1.5 h of CPU (training + re-encoding 12k chunks); it was not started. The BSARD
test-split check should be run before spending that time (add `eval_bsard_test` to the script as for the CE).

### colbert-legal-french: not run

`artifact.metadata`-style colbert-ai checkpoint; needs PyLate or RAGatouille in a venv with the experiment-12
pins (sentence-transformers 5.3 / torch 2.11), which this project does not share. Given the monobert and dpr
results from the same training recipe, no gain is expected on our corpora.

## What transfers and what does not

- **Domain ≠ task.** All three Maastricht models and BSARD are "Belgian law in French", yet the questions
  (citizen vs practitioner), document type (statute articles vs circulars / commentaries / rulings) and unit
  (one article vs a 1,500-char chunk of a long document) differ, and that is what a fine-tuned retriever
  overfits to. On our tax corpora the in-domain models behave like ordinary mid-size French models.
- **Rerankers:** monobert-legal-french ≈ mMARCO-MiniLM (0.60–0.64 on A/C, 0.47 on B) at 5× the cost;
  nothing beats bge-reranker-v2-m3 (0.678 / 0.517 / 0.696).
- **Bi-encoder:** dpr-legal-french is e5-small/e5-base-class on A (0.575 dense; 0.712 with convex 0.7 fusion —
  the best A fusion so far, but not on the val split) and clearly bad on B (0.242), the corpus where dense
  retrieval matters most. e5-base (0.641 / 0.469) remains the better CPU choice.
- **BSARD as training data:** +18 % in-domain, 0 to −0.04 MRR (−0.10 val on A) out of domain after one
  epoch. Cheap transfer fine-tuning from a same-domain public dataset does not replace our own labelled
  questions; if we fine-tune, it has to be on tax question/chunk pairs (experiment 15's direction), at the
  chunk length we serve (512), with replay of the original mMARCO data and negatives filtered for false
  negatives. BSARD is also CC BY-NC-SA, so a BSARD-trained model
  could not ship in a commercial product anyway.

## Verdict

Keep the experiment-03/09 stack (French-normalised BM25 + e5-base or bge-m3 + bge-reranker-v2-m3). None of the
Belgian in-domain models earns its cost on our corpora, and BSARD fine-tuning gives nothing (equal on B/C,
worse on A) despite a clear in-domain gain. The only positive signal
is dpr-legal-french as a fusion leg on corpus A (0.712 all-question MRR), which is within noise of bge-m3 + BM25
(0.691) and did not hold on the val split or on B.

## Environment notes

- The root disk was at 100 % when the experiment started; the venv was rebuilt on disk once space came back
  (`uv sync`), caches and logs live on `/dev/shm/exp16` (< 1 GB), downloaded models in the default HF cache
  (monobert 443 MB, dpr 443 MB, BSARD 53 MB).
- The box was shared with other torch jobs (load 6–13 on 4 cores) throughout; all timings above are under
  that load, with `torch.set_num_threads(2)`. Jobs were run one at a time.
- Two identical `BSARD-test / bm25` rows exist in the leaderboard (the baseline is re-saved by each
  fine-tune run).
