#!/usr/bin/env python3
"""Score (question, candidate chunk) pairs with a cross-encoder ONCE and cache them.

Candidates: union of the top-K chunks of every first-stage leg (K=50 for the cheap
mMARCO-MiniLM reranker, K=30 for bge-reranker-v2-m3; on A/B also the best-BM25 chunk of the
top-K whole-document BM25 docs). Output: cache/<corpus>_rerank_<reranker>.npz with parallel
arrays q_idx / chunk_idx / score. Resumable (partial file rewritten every few questions).

  uv run python score_rerankers.py --corpus C --reranker mmarco-minilm
  uv run python score_rerankers.py --corpus C --reranker bge-reranker-v2-m3
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np

from common14 import CACHE, RERANKERS, TOP_CAND, TOP_CAND_WIDE, Stage1, load_corpus_and_chunks

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--reranker", required=True, choices=list(RERANKERS))
    ap.add_argument("--top", type=int, default=None, help="per-leg candidate depth (default 50 mmarco / 30 others)")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--legs", default=None, help="comma-separated legs forming the candidate set (default: all)")
    a = ap.parse_args()
    import torch
    torch.set_num_threads(a.threads)
    from sentence_transformers import CrossEncoder

    top = a.top or (TOP_CAND_WIDE if a.reranker == "mmarco-minilm" else TOP_CAND)
    st = Stage1(a.corpus)
    docs, questions, chunks, _ = load_corpus_and_chunks(a.corpus)
    assert len(chunks) == st.nchunks and [q.qid for q in questions] == st.qids
    texts = [c.text for c in chunks]
    legs = tuple(a.legs.split(",")) if a.legs else None
    cands = st.candidate_sets(top, legs=legs)
    n_pairs = sum(len(c) for c in cands)
    out_f = CACHE / f"{a.corpus}_rerank_{a.reranker}.npz"
    done: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    if out_f.exists():
        z = np.load(out_f)
        for qi in np.unique(z["q_idx"]):
            m = z["q_idx"] == qi
            done[int(qi)] = (z["chunk_idx"][m], z["score"][m])
        print(f"resuming: {len(done)} questions already scored", flush=True)
    rs = RERANKERS[a.reranker]
    ce = CrossEncoder(rs["hf"], max_length=rs["max_len"], device="cpu", trust_remote_code=rs.get("trust", False))
    print(f"corpus {a.corpus}: {a.reranker} on {n_pairs} pairs ({n_pairs/len(questions):.1f}/q, top={top} per leg)", flush=True)

    def flush():
        qs = sorted(done)
        np.savez(out_f, q_idx=np.concatenate([np.full(len(done[q][0]), q, dtype=np.int32) for q in qs]),
                 chunk_idx=np.concatenate([done[q][0] for q in qs]).astype(np.int64),
                 score=np.concatenate([done[q][1] for q in qs]).astype(np.float32),
                 top=np.array(top), threads=np.array(a.threads), legs=np.array(",".join(legs or tuple(st.legs))))

    t0 = time.perf_counter()
    n_done_pairs = 0
    for qi, q in enumerate(questions):
        if qi in done:
            continue
        cand = cands[qi]
        # sort by length so batches have similar padding
        order = np.argsort([len(texts[j]) for j in cand])
        pairs = [(q.question, texts[cand[j]]) for j in order]
        sc = np.asarray(ce.predict(pairs, batch_size=8, show_progress_bar=False), dtype=np.float32)
        scores = np.empty(len(cand), dtype=np.float32)
        scores[order] = sc
        done[qi] = (cand, scores)
        n_done_pairs += len(cand)
        el = time.perf_counter() - t0
        print(f"  q{qi+1}/{len(questions)} {q.qid}: {len(cand)} pairs, {el/n_done_pairs:.2f} s/pair, "
              f"elapsed {el/60:.1f} min", flush=True)
        if (qi + 1) % 4 == 0:
            flush()
    flush()
    print(f"saved {out_f}: {sum(len(v[0]) for v in done.values())} pairs in {(time.perf_counter()-t0)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
