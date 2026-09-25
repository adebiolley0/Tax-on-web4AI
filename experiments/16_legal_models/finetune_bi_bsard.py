#!/usr/bin/env python3
"""Fine-tune a bi-encoder (multilingual-e5-small) with MultipleNegativesRankingLoss on BSARD (question, article)
pairs (+ one BM25 hard negative per pair when --hard_neg), then re-encode corpora A/B and evaluate dense / RRF /
convex fusion with BM25 (run_dense.py).

  python finetune_bi_bsard.py --base intfloat/multilingual-e5-small --n_q 3000 --batch 32 --max_seq 256
"""
from __future__ import annotations

import argparse
import random
import subprocess
import sys
import time

import common16 as C
from bsard_data import build_pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="intfloat/multilingual-e5-small")
    ap.add_argument("--tag", default="e5-small-bsard")
    ap.add_argument("--q_prefix", default="query: ")
    ap.add_argument("--d_prefix", default="passage: ")
    ap.add_argument("--n_q", type=int, default=3000)
    ap.add_argument("--max_seq", type=int, default=256)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--max_steps", type=int, default=-1)
    ap.add_argument("--hard_neg", action="store_true")
    ap.add_argument("--corpora", default="A,B")
    ap.add_argument("--no_synthetic", action="store_true")
    a = ap.parse_args()

    pairs, meta = build_pairs(a.n_q, 3, use_synthetic=not a.no_synthetic)
    rows = []
    for p in pairs:
        r = {"anchor": a.q_prefix + p["question"], "positive": a.d_prefix + p["positive"]}
        if a.hard_neg:
            r["negative"] = a.d_prefix + p["negatives"][0]
        rows.append(r)
    random.Random(0).shuffle(rows)
    C.log(f"[{a.tag}] {len(rows)} MNRL rows (hard_neg={a.hard_neg}); meta={meta}")

    from datasets import Dataset
    from sentence_transformers import SentenceTransformer, SentenceTransformerTrainer, SentenceTransformerTrainingArguments
    from sentence_transformers.losses import MultipleNegativesRankingLoss
    model = SentenceTransformer(a.base, device="cpu")
    model.max_seq_length = a.max_seq
    args = SentenceTransformerTrainingArguments(output_dir=str(C.SHM / "ckpt" / a.tag), num_train_epochs=a.epochs, max_steps=a.max_steps,
                                                per_device_train_batch_size=a.batch, learning_rate=a.lr, warmup_ratio=0.1,
                                                logging_steps=10, save_strategy="no", report_to=[], seed=0, dataloader_num_workers=0,
                                                batch_sampler="no_duplicates")
    t0 = time.perf_counter()
    trainer = SentenceTransformerTrainer(model=model, args=args, train_dataset=Dataset.from_list(rows), loss=MultipleNegativesRankingLoss(model))
    trainer.train()
    train_s = time.perf_counter() - t0
    C.log(f"[{a.tag}] trained in {train_s:.0f}s ({len(rows)} rows, batch {a.batch}, max_seq {a.max_seq}, lr {a.lr}, epochs {a.epochs})")
    out = C.MODELS_DIR / a.tag
    model.max_seq_length = 512
    model.save_pretrained(str(out))
    del model, trainer
    cmd = [sys.executable, "run_dense.py", "--model", str(out), "--hf_id", a.tag, "--tag", a.tag, "--corpora", a.corpora,
           "--q_prefix", a.q_prefix, "--d_prefix", a.d_prefix, "--max_seq", "512"]
    C.log("running: " + " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
