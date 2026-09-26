#!/usr/bin/env python3
"""Cross-encoder scores for the candidate sets of cache/B_candidates.json (run_stage1.py), cached by
(question id, exp-14 chunk index) and resumable:

* mMARCO-MiniLM-L12 (512 tokens): the best 3 chunks (z(colbert) + z(e5)) of each of the top-30 articles of the final / selected (and, on the human set, the alternative)
  z-score pipelines (human + mined), and the top-30 *chunks* of the reproduced exp-03 e5 RRF stage (the bar's own
  recipe) on both sets; exp 20's cache/B_mmarco.npz and exp 14's cache are reused where the pair exists.
* bge-reranker-v2-m3 (512 tokens): the best dense chunk of each of the top-20 articles of the selected (and the
  alternative) pipeline on the human set, and of the selected pipeline on a 100-question stratified subsample of
  the mined set (drawn inside exp 21's 150-question subsample, seed 22).

  flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 ../14_ltr_fusion/.venv/bin/python rerank_score.py --what mmarco
  flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 ../14_ltr_fusion/.venv/bin/python rerank_score.py --what bge
→ cache/B_mmarco22.npz, cache/B_bge22.npz (+ *_timing.json), cache/subsample100.json
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter

import numpy as np

from common22 import CACHE, EXP14, EXP20, load_universe, questions_all

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
HF = {"mmarco": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1", "bge": "BAAI/bge-reranker-v2-m3"}
MAX_LEN = 512
DEPTH_MMARCO, DEPTH_BGE = 30, 20
SUB_N = 100


def load_cache(f):
    if not f.exists():
        return {}
    z = np.load(f, allow_pickle=False)
    return {(str(q), int(c)): (float(s), int(src)) for q, c, s, src in zip(z["qid"], z["chunk_idx"], z["score"], z["src"])}


def save_cache(f, table):
    keys = sorted(table)
    np.savez(f, qid=np.array([k[0] for k in keys], dtype="U40"), chunk_idx=np.array([k[1] for k in keys], dtype=np.int64),
             score=np.array([table[k][0] for k in keys], dtype=np.float32), src=np.array([table[k][1] for k in keys], dtype=np.int8))


def subsample100(mined) -> list[str]:
    f = CACHE / "subsample100.json"
    if f.exists():
        return json.loads(f.read_text())["qids"]
    base = json.loads((EXP14.parent / "21_mined_eval" / "cache" / "subsample_B.json").read_text())["qids"]
    by_q = {q.qid: q for q in mined}
    src = Counter(by_q[q].meta["source"] for q in base)
    alloc = {s: int(round(SUB_N * n / len(base))) for s, n in src.items()}
    while sum(alloc.values()) > SUB_N:
        alloc[max(alloc, key=alloc.get)] -= 1
    while sum(alloc.values()) < SUB_N:
        alloc[max(alloc, key=alloc.get)] += 1
    rng = np.random.default_rng(22)
    chosen = []
    for s in sorted(alloc):
        pool = sorted(q for q in base if by_q[q].meta["source"] == s)
        chosen += list(rng.choice(pool, size=min(alloc[s], len(pool)), replace=False))
    chosen = sorted(chosen)
    info = {"n": len(chosen), "seed": 22, "drawn_from": "21_mined_eval/cache/subsample_B.json (150)", "allocation": alloc,
            "by_split": dict(Counter(by_q[q].split for q in chosen)), "qids": chosen}
    f.write_text(json.dumps(info, indent=1))
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", default="mmarco", choices=["mmarco", "bge"])
    ap.add_argument("--no-alt", action="store_true", help="skip the alternative pipeline's pairs")
    ap.add_argument("--alt-depth-mined", type=int, default=20, help="mMARCO depth of the alternative pipeline on the mined set (budget)")
    ap.add_argument("--mined-alt", action="store_true", help="also score the alternative pipeline on the mined set (off: budget)")
    a = ap.parse_args()
    import torch
    torch.set_num_threads(4)
    from sentence_transformers import CrossEncoder
    docs, chunks, chunk_doc, doc_start, doc_ids = load_universe()
    doc_index = {d: i for i, d in enumerate(doc_ids)}
    texts = [c.text for c in chunks]
    qs = questions_all()
    qtext = {q.qid: q.question for q in qs}
    mined = [q for q in qs if q.meta.get("source")]
    cands = json.loads((CACHE / "B_candidates.json").read_text())
    st = json.loads((CACHE.parent / "runs" / "stage1.json").read_text())
    selected, alt = st["selected"], st["alt"]
    final = st.get("final", selected)
    pipes = list(dict.fromkeys([final, selected] + ([] if a.no_alt else [alt])))
    main_pipes = list(dict.fromkeys([final, selected]))       # full depth on both sets; bge on the human set

    need: dict[tuple[str, int], None] = {}
    if a.what == "mmarco":
        for w in ("human", "mined"):
            for pipe in pipes:
                if w == "mined" and pipe not in main_pipes and not a.mined_alt:
                    continue
                depth = DEPTH_MMARCO if (w == "human" or pipe in main_pipes) else a.alt_depth_mined
                for qid, e in cands[f"{w}:{pipe}"].items():
                    for d, _ in e["docs"][:depth]:
                        for c in e["top_chunks"][d]:                 # the article's best CHUNK_CAP chunks (budget)
                            need[(qid, c)] = None
            for qid, e in cands[f"{w}:e5_bm25__rrf03"].items():
                for c in e["chunks"][:DEPTH_MMARCO]:
                    need[(qid, c)] = None
        out_f = CACHE / "B_mmarco22.npz"
        done = load_cache(out_f)
        # reuse exp 20 (src 2) and exp 14 (src 1): same model, same texts, same max_length, q_idx = human order
        hq = [q.qid for q in qs if not q.meta.get("source")]
        n_re = {1: 0, 2: 0}
        for src, f in ((2, EXP20 / "cache" / "B_mmarco.npz"), (1, EXP14 / "cache" / "B_rerank_mmarco-minilm.npz")):
            if f.exists():
                z = np.load(f, allow_pickle=False)
                for qi, c, s in zip(z["q_idx"], z["chunk_idx"], z["score"]):
                    k = (hq[int(qi)], int(c))
                    if k in need and k not in done:
                        done[k] = (float(s), src); n_re[src] += 1
        print(f"mMARCO: {len(need)} pairs needed; reused exp 20 {n_re[2]}, exp 14 {n_re[1]}; already here {sum(1 for k in need if k in done) - sum(n_re.values())}", flush=True)
    else:
        sub = set(subsample100(mined))
        for pipe in main_pipes:
            for qid, e in cands[f"human:{pipe}"].items():
                for d, _ in e["docs"][:DEPTH_BGE]:
                    need[(qid, e["best_chunk"][d])] = None
        for qid, e in cands[f"mined:{final}"].items():
            if qid in sub:
                for d, _ in e["docs"][:DEPTH_BGE]:
                    need[(qid, e["best_chunk"][d])] = None
        out_f = CACHE / "B_bge22.npz"
        done = load_cache(out_f)
        print(f"bge: {len(need)} pairs needed (human {sum(1 for k in need if not k[0].startswith('MB-'))}, mined subsample {len(sub)} q); already here {sum(1 for k in need if k in done)}", flush=True)

    todo = sorted(k for k in need if k not in done)
    timing = {"n_pairs_needed": len(need), "n_scored": len(todo), "max_length": MAX_LEN, "threads": 4, "model": HF[a.what]}
    if todo:
        t0 = time.perf_counter()
        ce = CrossEncoder(HF[a.what], max_length=MAX_LEN, device="cpu")
        timing["load_s"] = round(time.perf_counter() - t0, 1)
        by_q: dict[str, list[int]] = {}
        for qid, c in todo:
            by_q.setdefault(qid, []).append(c)
        t0 = time.perf_counter()
        n = 0
        for j, (qid, cs) in enumerate(sorted(by_q.items())):
            cs = sorted(cs, key=lambda c: len(texts[c]))
            sc = np.asarray(ce.predict([(qtext[qid], texts[c]) for c in cs], batch_size=16 if a.what == "mmarco" else 8, show_progress_bar=False), dtype=np.float32)
            for c, s in zip(cs, sc):
                done[(qid, c)] = (float(s), 0)
            n += len(cs)
            if (j + 1) % 20 == 0 or j == len(by_q) - 1:
                save_cache(out_f, done)
                print(f"  {j + 1}/{len(by_q)} questions, {n} pairs, {(time.perf_counter() - t0) / n:.3f} s/pair", flush=True)
        el = time.perf_counter() - t0
        timing.update({"seconds": round(el, 1), "s_per_pair": round(el / len(todo), 4)})
    save_cache(out_f, done)
    (CACHE / f"B_{a.what}22_timing.json").write_text(json.dumps(timing, indent=1))
    print("saved", out_f, timing, flush=True)


if __name__ == "__main__":
    main()
