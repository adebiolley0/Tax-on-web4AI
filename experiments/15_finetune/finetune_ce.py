#!/usr/bin/env python3
"""Fine-tune a small multilingual cross-encoder on the train split and evaluate it as a reranker
over cached first-stage candidates (BM25 ∪ dense top-30) on train and val of A, B, C.

  uv run python finetune_ce.py --base cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 --epochs 2
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import CrossEncoder
from sentence_transformers.cross_encoder import CrossEncoderTrainer, CrossEncoderTrainingArguments
from sentence_transformers.cross_encoder.losses import BinaryCrossEntropyLoss
from datasets import Dataset

from rag_eval import evaluate_rankings, save_result
import sys
from data import build_pairs, corpus
from rag_eval.corpora import DATA_DIR
sys.path.insert(0, str((DATA_DIR.parent / "03_hybrid_rerank").resolve()))
from run_hybrid import tokenize, to_doc_ranking  # noqa: E402
import bm25s

EXP = "15_finetune"
torch.set_num_threads(4)


def candidates_bm25(name, top=30):
    docs, qs, chunks = corpus(name)
    texts = [c.text for c in chunks]
    doc_ids = np.array([c.doc_id for c in chunks])
    r = bm25s.BM25(k1=1.5, b=0.75); r.index([tokenize(t) for t in texts], show_progress=False)
    cand = {}
    for q in qs:
        sc = r.get_scores(tokenize(q.question))
        cand[q.qid] = np.argsort(-sc)[:top]
    return qs, texts, doc_ids, cand


def evaluate(model, tag, names=("A", "B", "C"), top=30):
    for name in names:
        qs, texts, doc_ids, cand = candidates_bm25(name, top)
        rankings = {}
        t0 = time.perf_counter()
        for q in qs:
            c = cand[q.qid]
            sc = np.asarray(model.predict([(q.question, texts[j]) for j in c], batch_size=16, show_progress_bar=False), dtype=np.float32)
            full = np.full(len(texts), -1e9, dtype=np.float32); full[c] = sc
            rankings[q.qid] = to_doc_ranking(full, doc_ids)
        res = evaluate_rankings(f"bm25+{tag}@{top}", name, qs, rankings,
                                config={"reranker": tag, "candidates": "bm25", "top": top},
                                timing={"rerank_s": round(time.perf_counter() - t0, 1)})
        save_result(EXP, res); print(res.summary(), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--n_neg", type=int, default=4)
    ap.add_argument("--eval_base", action="store_true")
    ap.add_argument("--corpora", default="A,B,C")
    a = ap.parse_args()
    names = tuple(a.corpora.split(","))
    tag_base = a.base.split("/")[-1]
    if a.eval_base:
        evaluate(CrossEncoder(a.base, max_length=512, device="cpu"), tag_base, names)
    pairs = build_pairs(names, n_neg=a.n_neg, split="train")
    rows = []
    for p in pairs:
        rows.append({"query": p["question"], "passage": p["positive"], "label": 1.0})
        for n in p["negatives"]:
            rows.append({"query": p["question"], "passage": n, "label": 0.0})
    random.Random(0).shuffle(rows)
    print(f"{len(pairs)} train questions → {len(rows)} (query, passage, label) rows", flush=True)
    ds = Dataset.from_list(rows)
    model = CrossEncoder(a.base, max_length=512, device="cpu")
    out = Path(f"models/{tag_base}-ft")
    args = CrossEncoderTrainingArguments(output_dir=str(out), num_train_epochs=a.epochs, per_device_train_batch_size=8,
                                         learning_rate=a.lr, warmup_ratio=0.1, logging_steps=20, save_strategy="no",
                                         report_to=[], seed=0, dataloader_num_workers=0)
    t0 = time.perf_counter()
    trainer = CrossEncoderTrainer(model=model, args=args, train_dataset=ds, loss=BinaryCrossEntropyLoss(model))
    trainer.train()
    print(f"trained in {time.perf_counter()-t0:.0f}s", flush=True)
    model.save_pretrained(str(out))
    evaluate(model, f"{tag_base}-ft-e{a.epochs}", names)


if __name__ == "__main__":
    main()
