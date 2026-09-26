#!/usr/bin/env python3
"""Encode every question (human + mined) of a corpus with e5-small → cache/<corpus>_qemb_e5.npy (+ qids).
The only torch job of Part 1 (run under the torch lock):
  flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 uv run python ../21_mined_eval/embed_queries.py --corpus B
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
from common21 import CACHE, all_questions  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    import torch
    torch.set_num_threads(a.threads)
    from models import MODELS
    from run_sweep import Encoder
    qs = all_questions(a.corpus)
    out = CACHE / f"{a.corpus}_qemb_e5.npy"
    if out.exists():
        meta = json.loads((CACHE / f"{a.corpus}_qemb_e5.json").read_text())
        if meta["qids"] == [q.qid for q in qs]:
            print("already done", out); return
    t0 = time.perf_counter()
    enc = Encoder(MODELS["e5-small"])
    emb = enc.queries([q.question for q in qs])
    np.save(out, emb.astype(np.float32))
    (CACHE / f"{a.corpus}_qemb_e5.json").write_text(json.dumps({"qids": [q.qid for q in qs], "model": MODELS["e5-small"].hf_id,
                                                                "seconds": round(time.perf_counter() - t0, 1)}))
    print(f"encoded {len(qs)} questions of {a.corpus} in {time.perf_counter() - t0:.0f}s → {out}", flush=True)


if __name__ == "__main__":
    main()
