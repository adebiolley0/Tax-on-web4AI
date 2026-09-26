#!/usr/bin/env python3
"""Stratified subsample of the mined questions for the reranker runs (Part 2): proportional by source,
with the corpus-C PQ (diagnostic) slice capped; deterministic (seed 21).  Writes cache/subsample_<corpus>.json."""
from __future__ import annotations

import argparse
import json
from collections import Counter

import numpy as np

from common21 import CACHE, SUB_PQ_CAP, SUB_SIZE, SOURCES, all_questions


def allocate(counts: dict[str, int], n: int, cap: dict[str, int | None]) -> dict[str, int]:
    alloc = {s: 0 for s in counts}
    remaining, pool = n, dict(counts)
    for s, c in cap.items():
        if s in pool and c is not None and c < round(n * pool[s] / sum(pool.values())):
            alloc[s] = min(c, pool[s]); remaining -= alloc[s]; pool.pop(s)
    tot = sum(pool.values())
    raw = {s: remaining * pool[s] / tot for s in pool}
    for s in pool:
        alloc[s] = int(raw[s])
    for s in sorted(pool, key=lambda s: -(raw[s] - int(raw[s])))[: remaining - sum(alloc[s] for s in pool)]:
        alloc[s] += 1
    return alloc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    a = ap.parse_args()
    mined = [q for q in all_questions(a.corpus) if q.meta.get("source")]
    counts = Counter(q.meta["source"] for q in mined)
    alloc = allocate(dict(counts), SUB_SIZE[a.corpus], {"pq": SUB_PQ_CAP[a.corpus]})
    rng = np.random.default_rng(21)
    chosen = []
    for s in SOURCES:
        qs = sorted([q.qid for q in mined if q.meta["source"] == s])
        if not qs or alloc.get(s, 0) == 0:
            continue
        chosen += list(rng.choice(qs, size=min(alloc[s], len(qs)), replace=False))
    chosen = sorted(chosen)
    by_q = {q.qid: q for q in mined}
    info = {"corpus": a.corpus, "n": len(chosen), "seed": 21, "allocation": alloc, "population": dict(counts),
            "by_split": dict(Counter(by_q[q].split for q in chosen)),
            "by_source_split": {f"{by_q[q].meta['source']}/{by_q[q].split}": 0 for q in chosen}, "qids": chosen}
    for q in chosen:
        info["by_source_split"][f"{by_q[q].meta['source']}/{by_q[q].split}"] += 1
    (CACHE / f"subsample_{a.corpus}.json").write_text(json.dumps(info, indent=1))
    print(json.dumps({k: v for k, v in info.items() if k != "qids"}))


if __name__ == "__main__":
    main()
