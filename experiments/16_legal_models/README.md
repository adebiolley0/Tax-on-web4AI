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
uv run python finetune_ce_bsard.py --base cross-encoder/mmarco-mMiniLMv2-L12-H384-v1          # stage 2
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

