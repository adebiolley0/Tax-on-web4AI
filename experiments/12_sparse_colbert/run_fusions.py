#!/usr/bin/env python3
"""Post-hoc fusions over the cached score matrices (no encoding): every learned-sparse and
late-interaction leg × the experiment-01 whole-document BM25 leg (the 0.736-val bar on A),
cross-family pairs (sparse + ColBERT), ColBERT reranking of whole-doc BM25 candidates, and
3-way combinations with the best cached dense leg. Weights are tuned on train only.

Usage: uv run python run_fusions.py --corpus A
"""
from __future__ import annotations

import argparse

import numpy as np

from common12 import (LOCAL_CACHE, load_corpus, bm25_scores, bm25_doc_scores, dense_legs, evaluate,
                      rrf_matrix, tuned_convex)
from maxsim import rerank_scores


def cached_legs(corpus: str) -> dict[str, np.ndarray]:
    legs = {}
    for f in sorted(LOCAL_CACHE.glob(f"sparse_{corpus}_*.npz")):
        legs["sparse-" + f.stem.split("_", 2)[2]] = np.load(f, allow_pickle=True)["scores"]
    for f in sorted(LOCAL_CACHE.glob(f"colbert_{corpus}_*.npz")):
        legs["colbert-" + f.stem.split("_", 2)[2]] = np.load(f, allow_pickle=True)["scores"]
    f = LOCAL_CACHE / f"bgem3_{corpus}.npz"
    if f.exists():
        z = np.load(f, allow_pickle=True)
        legs["sparse-bge-m3"], legs["colbert-bge-m3"] = z["sparse"], z["colbert"]
    return legs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A")
    a = ap.parse_args()
    c = load_corpus(a.corpus)
    legs = cached_legs(c.name)
    print(f"corpus {c.name}: cached legs {list(legs)}", flush=True)
    bm, _ = bm25_scores(c)
    bmd = bm25_doc_scores(c)
    dense = dense_legs(c, ("e5-small", "e5-base", "bge-m3") if c.name == "A" else ("e5-small",))
    dk = "e5-base" if "e5-base" in dense else "e5-small"
    evaluate("bm25doc__exp01-best-broadcast", c, bmd, {"model": "exp01 doc|stem+stop+qstop+noaccent k1=1.5"})
    evaluate(f"bm25doc+{dk}__rrf", c, rrf_matrix([bmd, dense[dk]]), {"fusion": "rrf", "legs": ["bm25doc", dk]})
    tuned_convex(f"bm25doc+{dk}", c, bmd, dense[dk], {"legs": ["bm25doc", dk]})
    for name, m in legs.items():
        cfg = {"leg": name}
        evaluate(f"{name}+bm25doc__rrf", c, rrf_matrix([m, bmd]), {**cfg, "fusion": "rrf", "legs": [name, "bm25doc"]})
        tuned_convex(f"{name}+bm25doc", c, m, bmd, {**cfg, "legs": [name, "bm25doc"]})
        evaluate(f"{name}+bm25doc+{dk}__rrf", c, rrf_matrix([m, bmd, dense[dk]]),
                 {**cfg, "fusion": "rrf", "legs": [name, "bm25doc", dk]})
        if name.startswith("colbert"):
            for top in (30, 50):
                evaluate(f"{name}__rerank_bm25doc@{top}", c, rerank_scores(m, bmd, top),
                         {**cfg, "rerank_base": "bm25doc", "rerank_top": top})
            # rerank the convex(bm25doc, dense) candidates – the strongest cheap first stage
            from common12 import convex_matrix
            evaluate(f"{name}__rerank_convex-bm25doc-{dk}@50", c, rerank_scores(m, convex_matrix(bmd, dense[dk], 0.5), 50),
                     {**cfg, "rerank_base": f"convex0.5(bm25doc,{dk})", "rerank_top": 50})
    # cross-family pairs: sparse × colbert
    for s in [k for k in legs if k.startswith("sparse")]:
        for l in [k for k in legs if k.startswith("colbert")]:
            tuned_convex(f"{s}+{l}", c, legs[s], legs[l], {"legs": [s, l]})
            evaluate(f"{s}+{l}+bm25doc__rrf", c, rrf_matrix([legs[s], legs[l], bmd]), {"fusion": "rrf", "legs": [s, l, "bm25doc"]})


if __name__ == "__main__":
    main()
