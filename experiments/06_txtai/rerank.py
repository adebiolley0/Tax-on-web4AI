#!/usr/bin/env python3
"""Experiment 06 – cross-encoder rerank of the persisted txtai hybrid index.

Uses txtai's own `Reranker(Embeddings, Similarity(crossencode=True))` pipeline on the
top-N hybrid hits (dense weight 0.5).  txtai's CrossEncoder wraps a transformers
`text-classification` pipeline with batch_size=1 and no truncation, and its
constructor kwargs are routed to `model_kwargs` (see `HFPipeline.parseargs`), so
batching / truncation have to be set on the pipeline object after construction.

Usage: TXTAI_THREADS=4 uv run python rerank.py --corpus A --top 30
"""
from __future__ import annotations

import argparse
import os
import time

import torch

torch.set_num_threads(int(os.environ.get("TXTAI_THREADS", "2")))

from txtai import Embeddings  # noqa: E402
from txtai.pipeline import Reranker, Similarity  # noqa: E402

from rag_eval import evaluate_rankings, save_result  # noqa: E402
from run_txtai import EXP, INDEX_DIR, RERANKER, TOP, load, rankings_from, run_search  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--max-length", type=int, default=1024)
    ap.add_argument("--batch-size", type=int, default=8)
    a = ap.parse_args()

    docs, questions, chunks = load(a.corpus)
    chunk2doc = {c.chunk_id: c.doc_id for c in chunks}
    emb = Embeddings()
    emb.load(str(INDEX_DIR / f"{a.corpus}_hybrid_e5small"))
    print(f"loaded index: {emb.count()} rows", flush=True)

    base, dt = run_search(emb, questions, 0.5, chunk2doc, TOP)

    t0 = time.perf_counter()
    sim = Similarity(RERANKER, crossencode=True, gpu=False)
    # Workaround: txtai gives no public knob for these.
    sim.pipeline._batch_size = a.batch_size
    sim.pipeline._preprocess_params = {"truncation": True, "max_length": a.max_length}
    load_s = time.perf_counter() - t0

    reranker = Reranker(emb, sim)
    qtexts = [q.question for q in questions]
    t0 = time.perf_counter()
    reranked = reranker(qtexts, limit=a.top, factor=1, weights=0.5)
    rr_s = time.perf_counter() - t0

    rk = {}
    for q, rows in zip(questions, reranked):
        head = rankings_from({q.qid: rows}, chunk2doc)[q.qid]
        rk[q.qid] = head + [d for d in base[q.qid] if d not in head]
    name = f"txtai__e5-small__hybrid_w0.5+bge-reranker-v2-m3@{a.top}"
    res = evaluate_rankings(name, a.corpus, questions, rk,
                            config={"model": "intfloat/multilingual-e5-small", "dense_weight": 0.5, "reranker": RERANKER,
                                    "rerank_top": a.top, "max_length": a.max_length, "batch_size": a.batch_size,
                                    "n_chunks": len(chunks), "top": TOP,
                                    "desc": "txtai Reranker(Embeddings, Similarity(crossencode=True)) on top-N hybrid hits"},
                            timing={"hybrid_search_s": round(dt, 2), "reranker_load_s": round(load_s, 1),
                                    "rerank_s": round(rr_s, 1), "per_query_s": round(rr_s / len(questions), 2),
                                    "threads": torch.get_num_threads()})
    save_result(EXP, res)
    print(res.summary(), f"| rerank {rr_s:.0f}s ({rr_s/len(questions):.1f}s/q)", flush=True)


if __name__ == "__main__":
    main()
