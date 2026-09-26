#!/usr/bin/env python3
"""Score (question, chunk) pairs with mMARCO-MiniLM for the top-30 articles of every candidate run of
cache/B_candidates.json (all exp-14 chunks of each article: article_ctx_1200 over the raw articles, the texts
exp 03 / 14 reranked), reusing experiment 14's cache (same model, same texts, max_length 512).

  flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 ../14_ltr_fusion/.venv/bin/python rerank_b.py
→ cache/B_mmarco.npz (q_idx, chunk_idx, score, src[1 = exp 14]) + cache/B_mmarco_timing.json
"""
from __future__ import annotations

import json
import os
import time

import numpy as np

from common20 import CACHE, EXPS  # noqa: E402

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
HF = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


def main():
    import torch
    torch.set_num_threads(4)
    from sentence_transformers import CrossEncoder
    from common14 import load_corpus_and_chunks  # noqa: E402
    docs, questions, chunks, _ = load_corpus_and_chunks("B")
    z14 = np.load(EXPS / "14_ltr_fusion" / "cache" / "B_stage1.npz", allow_pickle=False)
    doc_start = z14["doc_start"]
    assert len(chunks) == len(z14["chunk_doc"])
    doc_index = {d.doc_id: i for i, d in enumerate(docs)}
    texts = [c.text for c in chunks]
    cands = json.loads((CACHE / "B_candidates.json").read_text())
    qids = [q.qid for q in questions]
    need: set[tuple[int, int]] = set()
    for run, per_q in cands.items():
        for qi, qid in enumerate(qids):
            for d, _ in per_q[qid]:
                di = doc_index[d]
                for c in range(int(doc_start[di]), int(doc_start[di + 1])):
                    need.add((qi, c))
    done: dict[tuple[int, int], tuple[float, int]] = {}
    out_f = CACHE / "B_mmarco.npz"
    if out_f.exists():
        z = np.load(out_f, allow_pickle=False)
        done = {(int(q), int(c)): (float(s), int(src)) for q, c, s, src in zip(z["q_idx"], z["chunk_idx"], z["score"], z["src"])}
    z = np.load(EXPS / "14_ltr_fusion" / "cache" / "B_rerank_mmarco-minilm.npz", allow_pickle=False)
    c14 = {(int(q), int(c)): float(s) for q, c, s in zip(z["q_idx"], z["chunk_idx"], z["score"])}
    n_reused = 0
    for k in need:
        if k not in done and k in c14:
            done[k] = (c14[k], 1); n_reused += 1
    todo = sorted(k for k in need if k not in done)
    print(f"{len(need)} pairs needed ({len(need)/len(qids):.0f}/q): {n_reused} reused from exp 14, {len(todo)} to score", flush=True)
    timing = {"n_pairs_needed": len(need), "n_reused_exp14": n_reused, "n_scored": len(todo)}
    if todo:
        t0 = time.perf_counter()
        ce = CrossEncoder(HF, max_length=512, device="cpu")
        timing["load_s"] = round(time.perf_counter() - t0, 1)
        t0 = time.perf_counter()
        by_q: dict[int, list[int]] = {}
        for qi, c in todo:
            by_q.setdefault(qi, []).append(c)
        n = 0
        for qi, cs in sorted(by_q.items()):
            cs = sorted(cs, key=lambda c: len(texts[c]))
            sc = np.asarray(ce.predict([(questions[qi].question, texts[c]) for c in cs], batch_size=16, show_progress_bar=False), dtype=np.float32)
            for c, s in zip(cs, sc):
                done[(qi, c)] = (float(s), 0)
            n += len(cs)
            print(f"  q{qi} {qids[qi]}: {len(cs)} pairs, {(time.perf_counter()-t0)/n:.3f} s/pair", flush=True)
        el = time.perf_counter() - t0
        timing.update({"seconds": round(el, 1), "s_per_pair": round(el / len(todo), 4), "threads": 4, "max_length": 512})
    keys = sorted(done)
    np.savez(out_f, q_idx=np.array([k[0] for k in keys], dtype=np.int32), chunk_idx=np.array([k[1] for k in keys], dtype=np.int64),
             score=np.array([done[k][0] for k in keys], dtype=np.float32), src=np.array([done[k][1] for k in keys], dtype=np.int8))
    (CACHE / "B_mmarco_timing.json").write_text(json.dumps(timing, indent=1))
    print("saved", out_f, timing, flush=True)


if __name__ == "__main__":
    main()
