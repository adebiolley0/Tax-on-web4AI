#!/usr/bin/env python3
"""Stage 2 – score (question, unit) pairs with bge-reranker-v2-m3 for the top-``--depth`` lexical
candidates of every question; reuse experiment 14's cached scores where the pair exists AND the
pair fits in ``--max_length`` tokens (the exp-14 cache was scored at max_length 1024, so a cached
score is identical to a fresh one only when nothing is truncated); compute the rest.

  OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 ../14_ltr_fusion/.venv/bin/python rerank.py --corpus C --depth 50 --threads 4

Output: cache/<corpus>_rerank_bge-reranker-v2-m3.npz (q_idx / chunk_idx / score, exp-14 format,
plus `src` = 1 for pairs copied from exp 14, 0 for pairs scored here). Resumable.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from common17 import CACHE, EXP14_CACHE, RERANKER, RERANKER_HF, LexStage1, rerank_cache_path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--depth", type=int, default=50)
    ap.add_argument("--max_length", type=int, default=512)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--no-reuse", action="store_true", help="ignore the exp-14 cache")
    ap.add_argument("--tag", default="", help="suffix for the cache file (e.g. _len1024)")
    a = ap.parse_args()
    import torch
    torch.set_num_threads(a.threads)
    from sentence_transformers import CrossEncoder
    from transformers import AutoTokenizer

    st = LexStage1.load(a.corpus)
    nq = len(st.qids)
    questions = {}
    from rag_eval import load_questions_b, load_questions_c
    for q in (load_questions_c() if a.corpus == "C" else load_questions_b()):
        questions[q.qid] = q.question
    assert list(questions) == st.qids
    cands = [st.candidates(qi, a.depth)[0] for qi in range(nq)]
    n_pairs = sum(len(c) for c in cands)

    out_f = rerank_cache_path(a.corpus, a.tag)
    done: dict[tuple[int, int], tuple[float, int]] = {}
    if out_f.exists():
        z = np.load(out_f, allow_pickle=False)
        for q, c, s, src in zip(z["q_idx"], z["chunk_idx"], z["score"], z["src"]):
            done[(int(q), int(c))] = (float(s), int(src))
        print(f"resuming: {len(done)} pairs already in {out_f.name}", flush=True)

    # exp-14 cache reuse (C only: same chunk texts; B was chunked differently there)
    tokenizer = AutoTokenizer.from_pretrained(RERANKER_HF)
    n_reused = n_too_long = 0
    if a.corpus == "C" and not a.no_reuse:
        z = np.load(EXP14_CACHE / f"C_rerank_{RERANKER}.npz", allow_pickle=False)
        c14 = {(int(q), int(c)): float(s) for q, c, s in zip(z["q_idx"], z["chunk_idx"], z["score"])}
        for qi in range(nq):
            for u in cands[qi]:
                key = (qi, int(u))
                if key in done or key not in c14:
                    continue
                n_tok = len(tokenizer(questions[st.qids[qi]], st.texts[int(u)], truncation=False)["input_ids"])
                if n_tok <= a.max_length:
                    done[key] = (c14[key], 1); n_reused += 1
                else:
                    n_too_long += 1
        print(f"exp-14 cache: {n_reused} pairs reused, {n_too_long} cached pairs re-scored because > {a.max_length} tokens", flush=True)

    todo = [(qi, int(u)) for qi in range(nq) for u in cands[qi] if (qi, int(u)) not in done]
    print(f"corpus {a.corpus}: {n_pairs} pairs at depth {a.depth} ({n_pairs/nq:.1f}/q); {len(done)} known, {len(todo)} to score "
          f"({RERANKER}, max_length {a.max_length}, {a.threads} threads)", flush=True)

    def flush(timing):
        keys = sorted(done)
        np.savez(out_f, q_idx=np.array([k[0] for k in keys], dtype=np.int32), chunk_idx=np.array([k[1] for k in keys], dtype=np.int64),
                 score=np.array([done[k][0] for k in keys], dtype=np.float32), src=np.array([done[k][1] for k in keys], dtype=np.int8),
                 max_length=np.array(a.max_length), threads=np.array(a.threads), depth=np.array(a.depth))
        (CACHE / f"{a.corpus}_rerank_timing{a.tag}.json").write_text(json.dumps(timing, indent=1))

    timing = json.loads((CACHE / f"{a.corpus}_rerank_timing{a.tag}.json").read_text()) if (CACHE / f"{a.corpus}_rerank_timing{a.tag}.json").exists() else {}
    if todo:
        t0 = time.perf_counter()
        ce = CrossEncoder(RERANKER_HF, max_length=a.max_length, device="cpu")
        load_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        n_scored = 0
        # score question by question (so a partial run is usable), length-sorted batches inside
        by_q: dict[int, list[int]] = {}
        for qi, u in todo:
            by_q.setdefault(qi, []).append(u)
        for i, (qi, units) in enumerate(sorted(by_q.items())):
            order = sorted(units, key=lambda u: len(st.texts[u]))
            pairs = [(questions[st.qids[qi]], st.texts[u]) for u in order]
            sc = np.asarray(ce.predict(pairs, batch_size=a.batch, show_progress_bar=False), dtype=np.float32)
            for u, s in zip(order, sc):
                done[(qi, u)] = (float(s), 0)
            n_scored += len(units)
            el = time.perf_counter() - t0
            print(f"  [{i+1}/{len(by_q)}] q{qi} {st.qids[qi]}: {len(units)} pairs, {el/n_scored:.2f} s/pair, elapsed {el/60:.1f} min", flush=True)
            if (i + 1) % 4 == 0:
                flush({**timing, "last_run": {"pairs": n_scored, "s_per_pair": round(el / n_scored, 3), "load_s": round(load_s, 1)}})
        el = time.perf_counter() - t0
        timing.setdefault("runs", []).append({"pairs": n_scored, "seconds": round(el, 1), "s_per_pair": round(el / max(n_scored, 1), 3),
                                              "threads": a.threads, "max_length": a.max_length, "load_s": round(load_s, 1)})
        timing["n_reused_exp14"] = n_reused
        timing.pop("last_run", None)
    flush(timing)
    print(f"saved {out_f}: {len(done)} pairs ({sum(1 for v in done.values() if v[1] == 1)} from exp 14)", flush=True)


if __name__ == "__main__":
    main()
