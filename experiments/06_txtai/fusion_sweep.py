#!/usr/bin/env python3
"""Experiment 06 – alternative txtai hybrid fusion strategies on the persisted index.

txtai picks the fusion method from the sparse `normalize` setting (see
txtai/embeddings/search/hybrid.py):
  normalize: True     -> convex combination  w*dense + (1-w)*sparse   (run_txtai.py)
  normalize: False    -> weighted RRF        w/rank_dense + (1-w)/rank_sparse   (no k constant)
  normalize: "bb25"   -> log-odds fusion of calibrated dense logits + BB25 probabilities

Normalisation happens at query time, so the same on-disk index can be reloaded with a
config override and no re-embedding.

Usage: uv run python fusion_sweep.py --corpus A
"""
from __future__ import annotations

import argparse
import os
import time

import torch

torch.set_num_threads(int(os.environ.get("TXTAI_THREADS", "2")))

from txtai import Embeddings  # noqa: E402
from txtai.scoring.normalize import Normalize  # noqa: E402

from rag_eval import evaluate_rankings, save_result  # noqa: E402
from run_txtai import EXP, INDEX_DIR, MODEL, SCORING_FR, TOP, load, run_search  # noqa: E402

MODES = {"rrf": False, "bb25": "bb25"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A")
    ap.add_argument("--weights", default="0.3,0.5,0.7")
    a = ap.parse_args()

    docs, questions, chunks = load(a.corpus)
    chunk2doc = {c.chunk_id: c.doc_id for c in chunks}
    for mode, norm in MODES.items():
        emb = Embeddings()
        emb.load(str(INDEX_DIR / f"{a.corpus}_hybrid_e5small"), config={"scoring": {**SCORING_FR, "normalize": norm}})
        # The scoring object restores `normalize` from its own pickled state, so the config
        # override alone is not enough: patch the loaded scoring instance.
        emb.scoring.normalize = norm
        emb.scoring.normalizer = Normalize(norm) if norm else None
        print(f"[{mode}] scoring.normalize={emb.scoring.normalize!r} isbayes={emb.scoring.isbayes()}", flush=True)
        for w in [float(x) for x in a.weights.split(",")]:
            rk, dt = run_search(emb, questions, w, chunk2doc, TOP)
            name = f"txtai__e5-small__hybrid_{mode}_w{w}"
            res = evaluate_rankings(name, a.corpus, questions, rk,
                                    config={"model": MODEL, "n_chunks": len(chunks), "top": TOP, "dense_weight": w,
                                            "fusion": mode, "txtai_scoring": {**SCORING_FR, "normalize": norm}},
                                    timing={"search_s": round(dt, 2), "per_query_ms": round(1000 * dt / len(questions), 1)})
            save_result(EXP, res); print(res.summary(), f"| {1000*dt/len(questions):.0f} ms/q", flush=True)
        del emb


if __name__ == "__main__":
    main()
