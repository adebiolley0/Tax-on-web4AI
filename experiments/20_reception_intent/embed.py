#!/usr/bin/env python3
"""e5-small embedding jobs of experiment 20 (one torch process, run under the lock):

  --what bank : the corpus-C intent bank (Q→Q, 'query: ' prefix on both sides) + the 64 corpus-C questions
                → cache/C_bank_e5.npy, cache/C_q_e5.npy
  --what b    : the 40 corpus-B questions ('query: ') + the reception text of every corpus-B article that has
                one, in ≤ 4 pieces of ≤ 1,200 chars ('passage: ') → cache/B_reception_e5.npz

  flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 ../14_ltr_fusion/.venv/bin/python embed.py --what bank
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from common20 import CACHE  # noqa: E402  (sys.path)
from rag_eval import load_questions_b, load_questions_c

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
PIECE_CHARS = 1200
MAX_PIECES = 4


def pieces_of(v: dict) -> list[str]:
    """Group the (type-round-robin ordered) sentences into ≤ MAX_PIECES pieces of ≤ PIECE_CHARS chars;
    the citing titles go into the first piece."""
    out, buf = [], ""
    items = list(v["titles"]) + [s["t"] for s in v["sentences"]]
    for s in items:
        if buf and len(buf) + len(s) + 1 > PIECE_CHARS:
            out.append(buf); buf = ""
            if len(out) >= MAX_PIECES:
                break
        buf = f"{buf} {s}".strip() if buf else s[:PIECE_CHARS]
    if buf and len(out) < MAX_PIECES:
        out.append(buf)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", required=True, choices=["bank", "b"])
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    import torch
    torch.set_num_threads(a.threads)
    from models import MODELS  # noqa: E402  (02_dense_sweep)
    from run_sweep import Encoder  # noqa: E402
    enc = Encoder(MODELS["e5-small"])
    print(f"e5-small loaded in {enc.load_s:.1f}s", flush=True)
    if a.what == "bank":
        bank = json.loads((CACHE / "C_bank.json").read_text())["units"]
        texts = [u["q"] for u in bank]
        t0 = time.perf_counter()
        emb = enc.queries(texts)
        dt = time.perf_counter() - t0
        np.save(CACHE / "C_bank_e5.npy", emb.astype(np.float32))
        qs = load_questions_c()
        qe = enc.queries([q.question for q in qs])
        np.save(CACHE / "C_q_e5.npy", qe.astype(np.float32))
        (CACHE / "C_bank_e5.json").write_text(json.dumps({"n": len(texts), "encode_s": round(dt, 1), "qids": [q.qid for q in qs],
                                                          "prefix": "query: (both sides)", "model": "intfloat/multilingual-e5-small"}))
        print(f"bank: {len(texts)} texts in {dt:.0f}s ({dt/len(texts)*1000:.0f} ms/text); {len(qs)} questions", flush=True)
    else:
        rec = json.loads((CACHE / "B_reception.json").read_text())["articles"]
        art_ids, piece_art, texts = [], [], []
        for k, (art, v) in enumerate(sorted(rec.items())):
            art_ids.append(art)
            for p in pieces_of(v):
                piece_art.append(k); texts.append(p)
        t0 = time.perf_counter()
        emb = enc.docs(texts)
        dt = time.perf_counter() - t0
        qs = load_questions_b()
        qe = enc.queries([q.question for q in qs])
        np.savez(CACHE / "B_reception_e5.npz", art_ids=np.array(art_ids), piece_art=np.array(piece_art, dtype=np.int32),
                 vec=emb.astype(np.float32), q=qe.astype(np.float32), qids=np.array([q.qid for q in qs]))
        (CACHE / "B_reception_e5.json").write_text(json.dumps({"articles": len(art_ids), "pieces": len(texts), "encode_s": round(dt, 1),
                                                               "piece_chars": PIECE_CHARS, "max_pieces": MAX_PIECES}))
        print(f"reception: {len(art_ids)} articles → {len(texts)} pieces in {dt:.0f}s ({dt/len(texts)*1000:.0f} ms/piece)", flush=True)


if __name__ == "__main__":
    main()
