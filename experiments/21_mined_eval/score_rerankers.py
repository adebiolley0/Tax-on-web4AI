#!/usr/bin/env python3
"""Part 2 – score (question, chunk) pairs with a cross-encoder ONCE; cache keyed by question id + chunk id
(cache/<corpus>_rerank_<reranker>.npz: qid / chunk_idx / chunk_id / score). Candidates: the top-``depth``
chunks of the fixed convex-0.5 fusion (stage-1 cache) or of the exp-13 lexical ranking (C only, unit index
== chunk index). Scores already available for identical texts are copied: exp-14 mMARCO cache (max_length
512, human questions), exp-17 bge cache (512, C human questions), exp-14 bge cache (1024) only for pairs that
fit in 512 tokens. Resumable; ``--max-minutes`` stops cleanly.

  flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 uv run python ../21_mined_eval/score_rerankers.py \
      --corpus C --reranker bge-reranker-v2-m3 --set sub --cands convex05
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
from common21 import (CACHE, EXP14, EXP17, RERANK_DEPTH, RERANKERS, LexStage1, Stage1, all_questions, human_questions,  # noqa: E402
                      load_rerank_cache, load_subsample, save_rerank_cache)


def question_set(corpus: str, which: str):
    qs = all_questions(corpus)
    if which == "all":
        return qs
    if which == "human":
        return [q for q in qs if q.meta.get("source") is None]
    if which == "mined":
        return [q for q in qs if q.meta.get("source")]
    sub = set(load_subsample(corpus))
    return [q for q in qs if q.qid in sub]


def candidate_chunks(corpus: str, cands: str, questions, depth: int) -> dict[str, np.ndarray]:
    if cands == "convex05":
        st = Stage1(corpus)
        return {q.qid: st.candidates(st.q_index[q.qid], "convex05", depth) for q in questions}
    lx = LexStage1(corpus, "exp13_lex")
    assert lx.same_units_as_stage1, "lexical units are not the stage-1 chunks (C only)"
    return {q.qid: lx.candidates(lx.q_index[q.qid], depth)[0] for q in questions}


def copy_existing(corpus: str, reranker: str, questions, cands: dict, table: dict, texts, max_len: int) -> dict:
    """Copy scores of identical (question text, chunk text) pairs from the exp-14 / exp-17 caches."""
    human = human_questions(corpus)
    hidx = {q.qid: i for i, q in enumerate(human)}
    stats = {"exp14": 0, "exp17": 0, "exp14_too_long": 0}
    srcs = []
    f14 = EXP14 / "cache" / f"{corpus}_rerank_{reranker}.npz"
    if f14.exists():
        z = np.load(f14, allow_pickle=False)
        srcs.append(("exp14", {(int(q), int(c)): float(s) for q, c, s in zip(z["q_idx"], z["chunk_idx"], z["score"])},
                     reranker == "mmarco-minilm"))          # exp-14 bge was scored at max_length 1024
    f17 = EXP17 / "cache" / f"{corpus}_rerank_{reranker}.npz"
    if corpus == "C" and reranker == "bge-reranker-v2-m3" and f17.exists():
        z = np.load(f17, allow_pickle=False)
        srcs.append(("exp17", {(int(q), int(c)): float(s) for q, c, s in zip(z["q_idx"], z["chunk_idx"], z["score"])}, True))
    if not srcs:
        return stats
    tok = None
    for q in questions:
        if q.qid not in hidx:
            continue
        hi = hidx[q.qid]
        for c in cands[q.qid]:
            key = (q.qid, int(c))
            if key in table:
                continue
            for name, src, direct in srcs:
                v = src.get((hi, int(c)))
                if v is None:
                    continue
                if not direct:
                    if tok is None:
                        from transformers import AutoTokenizer
                        tok = AutoTokenizer.from_pretrained(RERANKERS[reranker]["hf"])
                    if len(tok(q.question, texts[int(c)], truncation=False)["input_ids"]) > max_len:
                        stats["exp14_too_long"] += 1
                        continue
                table[key] = v; stats[name] += 1
                break
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--reranker", required=True, choices=list(RERANKERS))
    ap.add_argument("--set", default="sub", choices=["sub", "human", "mined", "all"])
    ap.add_argument("--cands", default="convex05", choices=["convex05", "lex13"])
    ap.add_argument("--depth", type=int, default=RERANK_DEPTH)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--max-minutes", type=float, default=None)
    a = ap.parse_args()
    import torch
    torch.set_num_threads(a.threads)
    from sentence_transformers import CrossEncoder
    from common14 import load_corpus_and_chunks

    rs = RERANKERS[a.reranker]
    questions = question_set(a.corpus, a.set)
    cands = candidate_chunks(a.corpus, a.cands, questions, a.depth)
    meta1 = json.loads((CACHE / f"{a.corpus}_stage1.json").read_text())
    _, _, chunks, _ = load_corpus_and_chunks(a.corpus)
    chunk_ids = [c.chunk_id for c in chunks]
    assert chunk_ids == meta1["chunk_ids"], "chunk order differs from the stage-1 cache"
    texts = [c.text for c in chunks]
    table = load_rerank_cache(a.corpus, a.reranker)
    n0 = len(table)
    copied = copy_existing(a.corpus, a.reranker, questions, cands, table, texts, rs["max_len"])
    todo = [(q, int(c)) for q in questions for c in cands[q.qid] if (q.qid, int(c)) not in table]
    n_pairs = sum(len(cands[q.qid]) for q in questions)
    metaf = CACHE / f"{a.corpus}_rerank_{a.reranker}.json"
    meta = json.loads(metaf.read_text()) if metaf.exists() else {"reranker": rs["hf"], "max_length": rs["max_len"], "runs": []}
    print(f"corpus {a.corpus} / {a.reranker} / set {a.set} / cands {a.cands}@{a.depth}: {len(questions)} q, {n_pairs} pairs; "
          f"{n0} cached, copied {copied}, {len(todo)} to score", flush=True)
    if not todo:
        save_rerank_cache(a.corpus, a.reranker, table, chunk_ids, meta); return
    ce = CrossEncoder(rs["hf"], max_length=rs["max_len"], device="cpu")
    t0 = time.perf_counter()
    by_q: dict[str, list[int]] = {}
    qtext = {}
    for q, c in todo:
        by_q.setdefault(q.qid, []).append(c); qtext[q.qid] = q.question
    n_scored, stopped = 0, False
    for i, (qid, cs) in enumerate(by_q.items()):
        order = sorted(cs, key=lambda c: len(texts[c]))
        sc = ce.predict([(qtext[qid], texts[c]) for c in order], batch_size=a.batch, show_progress_bar=False)
        for c, s in zip(order, np.asarray(sc, dtype=np.float32)):
            table[(qid, c)] = float(s)
        n_scored += len(cs)
        el = time.perf_counter() - t0
        print(f"  [{i+1}/{len(by_q)}] {qid}: {len(cs)} pairs, {el/n_scored:.2f} s/pair, {el/60:.1f} min", flush=True)
        if (i + 1) % 5 == 0:
            save_rerank_cache(a.corpus, a.reranker, table, chunk_ids, meta)
        if a.max_minutes and el / 60 > a.max_minutes:
            stopped = True; print("  time budget reached, stopping", flush=True); break
    el = time.perf_counter() - t0
    meta["runs"].append({"set": a.set, "cands": a.cands, "depth": a.depth, "pairs": n_scored, "seconds": round(el, 1),
                         "s_per_pair": round(el / max(1, n_scored), 3), "threads": a.threads, "copied": copied,
                         "stopped_early": stopped})
    save_rerank_cache(a.corpus, a.reranker, table, chunk_ids, meta)
    print(f"saved {len(table)} pairs ({n_scored} scored in {el/60:.1f} min, {el/max(1,n_scored):.2f} s/pair)", flush=True)


if __name__ == "__main__":
    main()
