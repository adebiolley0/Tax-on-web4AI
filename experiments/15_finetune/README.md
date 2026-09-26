# 15 — Fine-tuning the mMARCO-MiniLM cross-encoder on our own train split

Standalone `uv` project. Question: can the cheap reranker (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`,
2 s/query on CPU) be fine-tuned on the **train half** of our three question sets and gain on the
**validation half**, without any LLM-generated data?

## Setup

* `data.py` — training pairs from the train split only (md5 parity of the question id, as in
  `rag_eval.corpora.Question.split`): for each train question of A, B and C, the positive chunk(s) of the
  expected document(s) plus `n_neg=4` hard negatives taken from the French-normalised BM25 top-30 that are
  not expected documents. 70 train questions → 88 optimisation steps at batch 8 (≈ 700 rows).
* `finetune_ce.py` — `CrossEncoderTrainer` + `BinaryCrossEntropyLoss` (sentence-transformers 5), lr 2e-5,
  warm-up 10 %, 2 epochs, max length 512, CPU. Evaluation reranks the BM25 top-30 chunks on all three
  corpora and saves through `rag_eval.save_result("15_finetune", …)`.
* `eval_ft.py` — evaluation-only entry point for the saved model (the first training run was killed at
  step 40/88 while the box was oversubscribed; the second run trained to completion but its evaluation was
  cut off, so the saved weights were scored separately). Training took ≈ 75 min on 4 cores when run alone.
* Weights in `models/` are git-ignored (450 MB).

## Results (BM25 top-30 → reranker; MRR at document level)

| corpus | zero-shot mMARCO: all / train / val | fine-tuned 2 epochs: all / train / val | val bar |
|---|---|---|---|
| A (29 q, val 12) | 0.604 / 0.654 / **0.534** | 0.613 / 0.703 / **0.486** | 0.736 (BM25 whole doc) |
| B (40 q, val 16) | 0.494 / 0.490 / **0.500** | 0.562 / 0.611 / **0.488** | 0.570 (e5 RRF + mMARCO) |
| C (64 q, val 35) | 0.593 / 0.652 / **0.545** | 0.669 / 0.769 / **0.585** | 0.665 (BM25 + bge) |

## Reading

* The model learns the train half (train MRR +0.05 to +0.12 on every corpus) and gives it back on the
  validation half of A and B (−0.05 and −0.01): with 17–24 train questions per corpus, two epochs of
  binary cross-entropy on BM25-mined negatives overfit question wording rather than learn the domain.
* On C, the largest set (29 train / 35 val questions), the validation half improves by +0.04 (0.545 →
  0.585, H@1 0.48 → 0.56 on the full set). That is within one standard error of a 35-question MRR
  (≈ 0.07), so it is a hint, not a result; it is consistent with idea 74's diagnosis that the missing
  ingredient is volume of pairs, not the recipe.
* BM25-mined negatives contain false negatives (yearly / regional twins of the expected document, see exp
  11 and ideas 26, 74); the fine-tuned model is pushed to score those at 0 and loses part of its
  zero-shot lexical sense — visible on A, where BM25 alone is already the best system.
* Compare exp 16: the same base model fine-tuned on BSARD (886 real legal questions, out of domain) also
  regresses on our sets; in-domain volume is the bottleneck both ways.

## Verdict

Not a round-2 win: no validation bar is beaten and two of three validation halves get worse. Keep the
zero-shot cross-encoders. Revisit only with (a) several hundred mined or synthetic question → article pairs
(ideas 12, 69, 73), (b) de-duplicated hard negatives with a positive-anchored margin (idea 74) and
(c) the zero-shot model's scores as a distillation target (idea 76).
