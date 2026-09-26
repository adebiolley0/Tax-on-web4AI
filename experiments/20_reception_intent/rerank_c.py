#!/usr/bin/env python3
"""Score (question, unit) pairs with bge-reranker-v2-m3 (max_length 512) for the top-20 documents of every
candidate run in cache/C_candidates.json (unit = the document's best fused chunk). Reuses experiment 17's
cache (same texts, 512 tokens) and experiment 14's cache for pairs that fit in 512 tokens (scored at 1024
there, identical when nothing is truncated).

  flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 ../14_ltr_fusion/.venv/bin/python rerank_c.py
→ cache/C_bge.npz + cache/C_bge_timing.json
"""
from __future__ import annotations

import json
import os
import time

import numpy as np

from common20 import CACHE, EXPS  # noqa: E402
from run_exp13 import load_corpus  # noqa: E402

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
HF = "BAAI/bge-reranker-v2-m3"
MAX_LEN = 512


def main():
    import torch
    torch.set_num_threads(4)
    from sentence_transformers import CrossEncoder
    from transformers import AutoTokenizer
    cands = json.loads((CACHE / "C_candidates.json").read_text())
    C = load_corpus("C", False)
    qids = [q.qid for q in C.questions]
    qtext = {q.qid: q.question for q in C.questions}
    need: set[tuple[int, int]] = set()
    for run, per_q in cands.items():
        for qi, qid in enumerate(qids):
            for _, u, _ in per_q[qid]:
                need.add((qi, int(u)))
    texts = {u: f"{C.raw_fields['title'][u]}\n\n{C.raw_fields['body'][u]}" for _, u in need}   # == exp 17 / exp 14 chunk text
    done: dict[tuple[int, int], tuple[float, int]] = {}
    out_f = CACHE / "C_bge.npz"
    if out_f.exists():
        z = np.load(out_f, allow_pickle=False)
        done = {(int(q), int(c)): (float(s), int(src)) for q, c, s, src in zip(z["q_idx"], z["chunk_idx"], z["score"], z["src"])}
    z17 = np.load(EXPS / "17_lex_rerank" / "cache" / "C_rerank_bge-reranker-v2-m3.npz", allow_pickle=False)
    c17 = {(int(q), int(c)): float(s) for q, c, s in zip(z17["q_idx"], z17["chunk_idx"], z17["score"])}
    z14 = np.load(EXPS / "14_ltr_fusion" / "cache" / "C_rerank_bge-reranker-v2-m3.npz", allow_pickle=False)
    c14 = {(int(q), int(c)): float(s) for q, c, s in zip(z14["q_idx"], z14["chunk_idx"], z14["score"])}
    tokenizer = AutoTokenizer.from_pretrained(HF)
    n17 = n14 = 0
    for k in sorted(need):
        if k in done:
            continue
        if k in c17:
            done[k] = (c17[k], 17); n17 += 1
        elif k in c14:
            n_tok = len(tokenizer(qtext[qids[k[0]]], texts[k[1]], truncation=False)["input_ids"])
            if n_tok <= MAX_LEN:
                done[k] = (c14[k], 14); n14 += 1
    todo = sorted(k for k in need if k not in done)
    print(f"{len(need)} pairs needed: {n17} from exp 17, {n14} from exp 14, {len(todo)} to score (~{len(todo)/60:.0f} min)", flush=True)
    timing = {"n_pairs_needed": len(need), "n_reused_17": n17, "n_reused_14": n14, "n_scored": len(todo), "max_length": MAX_LEN, "threads": 4}
    if todo:
        t0 = time.perf_counter()
        ce = CrossEncoder(HF, max_length=MAX_LEN, device="cpu")
        timing["load_s"] = round(time.perf_counter() - t0, 1)
        t0 = time.perf_counter()
        by_q: dict[int, list[int]] = {}
        for qi, u in todo:
            by_q.setdefault(qi, []).append(u)
        n = 0

        def flush():
            keys = sorted(done)
            np.savez(out_f, q_idx=np.array([k[0] for k in keys], dtype=np.int32), chunk_idx=np.array([k[1] for k in keys], dtype=np.int64),
                     score=np.array([done[k][0] for k in keys], dtype=np.float32), src=np.array([done[k][1] for k in keys], dtype=np.int8))
        for i, (qi, us) in enumerate(sorted(by_q.items())):
            us = sorted(us, key=lambda u: len(texts[u]))
            sc = np.asarray(ce.predict([(qtext[qids[qi]], texts[u]) for u in us], batch_size=8, show_progress_bar=False), dtype=np.float32)
            for u, s in zip(us, sc):
                done[(qi, u)] = (float(s), 0)
            n += len(us)
            el = time.perf_counter() - t0
            print(f"  [{i+1}/{len(by_q)}] q{qi} {qids[qi]}: {len(us)} pairs, {el/n:.2f} s/pair, {el/60:.1f} min", flush=True)
            if (i + 1) % 5 == 0:
                flush()
        el = time.perf_counter() - t0
        timing.update({"seconds": round(el, 1), "s_per_pair": round(el / len(todo), 3)})
    else:
        timing["s_per_pair"] = 0.94       # exp-17 measurement (same model, same box, 4 threads)
    keys = sorted(done)
    np.savez(out_f, q_idx=np.array([k[0] for k in keys], dtype=np.int32), chunk_idx=np.array([k[1] for k in keys], dtype=np.int64),
             score=np.array([done[k][0] for k in keys], dtype=np.float32), src=np.array([done[k][1] for k in keys], dtype=np.int8))
    (CACHE / "C_bge_timing.json").write_text(json.dumps(timing, indent=1))
    print("saved", out_f, timing, flush=True)


if __name__ == "__main__":
    main()
