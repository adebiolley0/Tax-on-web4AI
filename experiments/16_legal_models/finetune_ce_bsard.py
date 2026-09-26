#!/usr/bin/env python3
"""Fine-tune a cross-encoder on BSARD (question, article) pairs with BM25 hard negatives and evaluate it as a
reranker of BM25 top-30 chunks on our corpora A/B/C (both our splits are held out: the training data is external).

  python finetune_ce_bsard.py --base cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 --n_q 3000 --n_neg 3 --max_len 384
  python finetune_ce_bsard.py --base maastrichtlawtech/monobert-legal-french --n_q 3000 --max_len 384
"""
from __future__ import annotations

import argparse
import random
import time

import numpy as np

import common16 as C
from bsard_data import build_pairs, bsard_test_candidates


def eval_bsard_test(model, tag: str, top: int = 30, n_questions: int = 100):
    """In-domain check: rerank BM25 top-30 BSARD articles for the first ``n_questions`` test questions."""
    rows, texts, ids, cand, expected = bsard_test_candidates(top, n_questions)
    from rag_eval.corpora import Question
    from rag_eval.metrics import evaluate_rankings
    qs = [Question(str(r["id"]), r["question"], expected[str(r["id"])]) for r in rows]
    rank_bm, rank_ce = {}, {}
    for q in qs:
        c = cand[q.qid]
        rank_bm[q.qid] = [str(ids[j]) for j in c]
        sc = np.asarray(model.predict([(q.question, texts[j]) for j in c], batch_size=16, show_progress_bar=False)).reshape(-1)
        rank_ce[q.qid] = [str(ids[j]) for j in c[np.argsort(-sc)]]
    for nm, rk in (("bm25", rank_bm), (f"bm25+{tag}@{top}", rank_ce)):
        res = evaluate_rankings(nm, "BSARD-test", qs, rk, config={"n_questions": n_questions, "top": top})
        C.save(res)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--n_q", type=int, default=3000)
    ap.add_argument("--n_neg", type=int, default=3)
    ap.add_argument("--max_len", type=int, default=384)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--max_steps", type=int, default=-1)
    ap.add_argument("--corpora", default="A,B,C")
    ap.add_argument("--no_synthetic", action="store_true")
    ap.add_argument("--bsard_test", type=int, default=100, help="n BSARD test questions for the in-domain check (0 = skip)")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--skip_zeroshot", action="store_true", help="skip the zero-shot BSARD-test check (already saved)")
    a = ap.parse_args()
    tag = a.tag or f"{a.base.split('/')[-1]}-bsard"

    pairs, meta = build_pairs(a.n_q, a.n_neg, use_synthetic=not a.no_synthetic)
    rows = []
    for p in pairs:
        rows.append({"query": p["question"], "passage": p["positive"], "label": 1.0})
        for ng in p["negatives"]:
            rows.append({"query": p["question"], "passage": ng, "label": 0.0})
    random.Random(0).shuffle(rows)
    C.log(f"[{tag}] {len(pairs)} BSARD questions → {len(rows)} (query, passage, label) rows; meta={meta}")

    from datasets import Dataset
    from sentence_transformers import CrossEncoder
    from sentence_transformers.cross_encoder import CrossEncoderTrainer, CrossEncoderTrainingArguments
    from sentence_transformers.cross_encoder.losses import BinaryCrossEntropyLoss
    model = CrossEncoder(a.base, max_length=a.max_len, device="cpu")
    if a.bsard_test and not a.skip_zeroshot:
        eval_bsard_test(model, f"{a.base.split('/')[-1]}-zeroshot", n_questions=a.bsard_test)
    args = CrossEncoderTrainingArguments(output_dir=str(C.SHM / "ckpt" / tag), num_train_epochs=a.epochs, max_steps=a.max_steps,
                                         per_device_train_batch_size=a.batch, learning_rate=a.lr, warmup_steps=0.1,
                                         logging_steps=25, save_strategy="no", report_to=[], seed=0, dataloader_num_workers=0)
    t0 = time.perf_counter()
    trainer = CrossEncoderTrainer(model=model, args=args, train_dataset=Dataset.from_list(rows), loss=BinaryCrossEntropyLoss(model))
    trainer.train()
    train_s = time.perf_counter() - t0
    C.log(f"[{tag}] trained in {train_s:.0f}s ({len(rows)} rows, batch {a.batch}, max_len {a.max_len}, lr {a.lr}, epochs {a.epochs})")
    if a.save:
        model.save_pretrained(str(C.MODELS_DIR / tag))
    if a.bsard_test:
        eval_bsard_test(model, tag, n_questions=a.bsard_test)
    C.evaluate_rerank(model, tag, tuple(a.corpora.split(",")), 30, 16,
                      extra_config={"base": a.base, "train": "bsard", **meta, "max_len": a.max_len, "batch": a.batch,
                                    "lr": a.lr, "epochs": a.epochs, "train_s": round(train_s)})


if __name__ == "__main__":
    main()
