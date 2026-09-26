#!/usr/bin/env python3
"""Score (question, unit) pairs with bge-reranker-v2-m3 (max_length 512) for the top-20 units of the selected
reception first stage (cache/C_candidates.json, human questions), reusing every identical pair already scored at
512 tokens by experiments 17, 20 and 21, and experiment 14's 1024-token scores when the pair fits in 512 tokens.

  cd experiments/14_ltr_fusion && flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 .venv/bin/python ../23_reception_c/rerank23.py
→ cache/C_bge23.npz (q_idx / chunk_idx / score / src: 0 scored here, 17 / 20 / 21 / 14 = copied) + cache/C_bge23_timing.json
"""
from __future__ import annotations

import json
import os
import time

import numpy as np

from common23 import CACHE, EXPS  # noqa: E402
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
    cand = json.loads((CACHE / "C_candidates.json").read_text())
    C = load_corpus("C", False)
    qids = [q.qid for q in C.questions]
    qtext = {q.qid: q.question for q in C.questions}
    need: set[tuple[int, int]] = set()
    for key in ("top_units", "lex13_top_units"):
        for qi, qid in enumerate(qids):
            for u, _ in cand[key][qid]:
                need.add((qi, int(u)))
    texts = {u: f"{C.raw_fields['title'][u]}\n\n{C.raw_fields['body'][u]}" for _, u in need}   # == exp 14 / 17 / 20 / 21 chunk text
    out_f = CACHE / "C_bge23.npz"
    done: dict[tuple[int, int], tuple[float, int]] = {}
    if out_f.exists():
        z = np.load(out_f, allow_pickle=False)
        done = {(int(q), int(c)): (float(s), int(src)) for q, c, s, src in zip(z["q_idx"], z["chunk_idx"], z["score"], z["src"])}
    # 512-token caches keyed by human question index (exp 17, exp 20) and by qid string (exp 21)
    direct: list[tuple[int, dict]] = []
    z17 = np.load(EXPS / "17_lex_rerank" / "cache" / "C_rerank_bge-reranker-v2-m3.npz", allow_pickle=False)
    assert json.loads((EXPS / "17_lex_rerank" / "cache" / "C_lex.json").read_text())["qids"] == qids
    direct.append((17, {(int(q), int(c)): float(s) for q, c, s in zip(z17["q_idx"], z17["chunk_idx"], z17["score"])}))
    z20 = np.load(EXPS / "20_reception_intent" / "cache" / "C_bge.npz", allow_pickle=False)
    direct.append((20, {(int(q), int(c)): float(s) for q, c, s in zip(z20["q_idx"], z20["chunk_idx"], z20["score"])}))
    z21 = np.load(EXPS / "21_mined_eval" / "cache" / "C_rerank_bge-reranker-v2-m3.npz", allow_pickle=False)
    qpos = {qid: i for i, qid in enumerate(qids)}
    direct.append((21, {(qpos[str(q)], int(c)): float(s) for q, c, s in zip(z21["qid"], z21["chunk_idx"], z21["score"]) if str(q) in qpos}))
    z14 = np.load(EXPS / "14_ltr_fusion" / "cache" / "C_rerank_bge-reranker-v2-m3.npz", allow_pickle=False)
    c14 = {(int(q), int(c)): float(s) for q, c, s in zip(z14["q_idx"], z14["chunk_idx"], z14["score"])}
    tokenizer = AutoTokenizer.from_pretrained(HF)
    n_src = {17: 0, 20: 0, 21: 0, 14: 0}
    for k in sorted(need):
        if k in done:
            continue
        for tag, table in direct:
            if k in table:
                done[k] = (table[k], tag); n_src[tag] += 1; break
        else:
            if k in c14 and len(tokenizer(qtext[qids[k[0]]], texts[k[1]], truncation=False)["input_ids"]) <= MAX_LEN:
                done[k] = (c14[k], 14); n_src[14] += 1
    todo = sorted(k for k in need if k not in done)
    print(f"{len(need)} pairs needed: reused {n_src}, {len(todo)} to score (~{len(todo)/60:.0f} min at 1 s/pair)", flush=True)
    timing = {"n_pairs_needed": len(need), "n_reused": n_src, "n_scored": len(todo), "max_length": MAX_LEN, "threads": 4}

    def flush():
        keys = sorted(done)
        np.savez(out_f, q_idx=np.array([k[0] for k in keys], dtype=np.int32), chunk_idx=np.array([k[1] for k in keys], dtype=np.int64),
                 score=np.array([done[k][0] for k in keys], dtype=np.float32), src=np.array([done[k][1] for k in keys], dtype=np.int8))
    if todo:
        t0 = time.perf_counter()
        ce = CrossEncoder(HF, max_length=MAX_LEN, device="cpu")
        timing["load_s"] = round(time.perf_counter() - t0, 1)
        t0 = time.perf_counter()
        by_q: dict[int, list[int]] = {}
        for qi, u in todo:
            by_q.setdefault(qi, []).append(u)
        n = 0
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
    flush()
    (CACHE / "C_bge23_timing.json").write_text(json.dumps(timing, indent=1))
    print("saved", out_f, timing, flush=True)


if __name__ == "__main__":
    main()
