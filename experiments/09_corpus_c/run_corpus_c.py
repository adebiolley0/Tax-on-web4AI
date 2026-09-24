#!/usr/bin/env python3
"""Corpus C evaluation: BM25 (doc / chunk), dense (cached embeddings), fusion, reranking.

  uv run python run_corpus_c.py --runs bm25_doc,bm25_chunk
  uv run python run_corpus_c.py --model e5-small --runs dense,rrf,convex0.5 --rerankers bge-reranker-v2-m3
"""
from __future__ import annotations

import argparse
import json
import sys
import time

import bm25s
import numpy as np

from rag_eval import evaluate_rankings, save_result, load_questions_c, whole_doc
from rag_eval.cache import EmbeddingCache, _key
from common_c import MODELS, Encoder, chunk_corpus_c, cache_extra
from run_hybrid import tokenize, rrf, minmax, to_doc_ranking, RERANKERS  # noqa: E402  (03_hybrid_rerank)

EXP = "09_corpus_c"


def bm25_scores(texts, questions, k1=1.5, b=0.75):
    t0 = time.perf_counter()
    r = bm25s.BM25(k1=k1, b=b)
    r.index([tokenize(t) for t in texts], show_progress=False)
    idx_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    sc = np.stack([r.get_scores(tokenize(q.question)).astype(np.float32) for q in questions])
    return sc, idx_s, (time.perf_counter() - t0) / len(questions)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunker", default="fixed1200_title")
    ap.add_argument("--model", default=None)
    ap.add_argument("--runs", default="bm25_doc,bm25_chunk")
    ap.add_argument("--rerankers", default="none")
    ap.add_argument("--rerank_base", default="rrf")
    ap.add_argument("--rerank_top", type=int, default=30)
    a = ap.parse_args()
    questions = load_questions_c()
    docs, chunks = chunk_corpus_c(a.chunker)
    texts = [c.text for c in chunks]
    doc_ids = np.array([c.doc_id for c in chunks])
    n = len(chunks)
    print(f"corpus C: {len(docs)} docs / {n} chunks / {len(questions)} questions", flush=True)
    runs = a.runs.split(",")
    fused: dict[str, np.ndarray] = {}
    bm = None

    if "bm25_doc" in runs:
        dtexts = [d.text[:200_000] for d in docs]
        sc, idx_s, q_s = bm25_scores(dtexts, questions)
        d_ids = np.array([d.doc_id for d in docs])
        rankings = {q.qid: [str(d_ids[j]) for j in np.argsort(-sc[i])[:50]] for i, q in enumerate(questions)}
        res = evaluate_rankings("bm25_doc", "C", questions, rankings, config={"unit": "doc"},
                                timing={"index_s": round(idx_s, 1), "query_s": round(q_s, 4)})
        save_result(EXP, res); print(res.summary(), f"| idx {idx_s:.0f}s", flush=True)
    if any(r in runs for r in ("bm25_chunk", "rrf")) or a.rerankers != "none" or any(r.startswith("convex") for r in runs):
        bm, idx_s, q_s = bm25_scores(texts, questions)
        if "bm25_chunk" in runs:
            rankings = {q.qid: to_doc_ranking(bm[i], doc_ids) for i, q in enumerate(questions)}
            res = evaluate_rankings(f"bm25_chunk__{a.chunker}", "C", questions, rankings,
                                    config={"unit": "chunk", "chunker": a.chunker, "n_chunks": n},
                                    timing={"index_s": round(idx_s, 1), "query_s": round(q_s, 4)})
            save_result(EXP, res); print(res.summary(), f"| idx {idx_s:.0f}s", flush=True)
        fused["bm25"] = bm

    dense = None
    if a.model:
        spec = MODELS[a.model]
        f = EmbeddingCache().dir / (_key(spec.hf_id, texts, cache_extra(spec, a.chunker)) + ".npy")
        if not f.exists():
            print("no cached embeddings; run encode_corpus.py first:", f); sys.exit(1)
        emb = np.load(f)
        enc = Encoder(spec)
        qemb = enc.queries([q.question for q in questions])
        t0 = time.perf_counter()
        dense = qemb @ emb.T
        q_s = (time.perf_counter() - t0) / len(questions)
        fused["dense"] = dense
        for fu in runs:
            if fu == "dense":
                sc = dense
            elif fu == "rrf":
                sc = np.stack([rrf([np.argsort(-dense[i])[:300], np.argsort(-bm[i])[:300]], 60, n) for i in range(len(questions))])
            elif fu.startswith("convex"):
                w = float(fu[len("convex"):])
                sc = np.stack([w * minmax(dense[i]) + (1 - w) * minmax(bm[i]) for i in range(len(questions))])
            else:
                continue
            fused[fu] = sc
            rankings = {q.qid: to_doc_ranking(sc[i], doc_ids) for i, q in enumerate(questions)}
            res = evaluate_rankings(f"{a.model}__{a.chunker}__{fu}", "C", questions, rankings,
                                    config={"model": spec.hf_id, "chunker": a.chunker, "fusion": fu, "n_chunks": n},
                                    timing={"dense_query_s": round(q_s, 4)})
            save_result(EXP, res); print(res.summary(), flush=True)

    for rk in [r for r in a.rerankers.split(",") if r != "none"]:
        from sentence_transformers import CrossEncoder
        rs = RERANKERS[rk]
        ce = CrossEncoder(rs["hf"], max_length=rs["max_len"], device="cpu", trust_remote_code=rs.get("trust", False))
        base = fused[a.rerank_base]
        rankings = {}
        t0 = time.perf_counter()
        for i, q in enumerate(questions):
            cand = np.argsort(-base[i])[: a.rerank_top]
            sc = np.asarray(ce.predict([(q.question, texts[j]) for j in cand], batch_size=8, show_progress_bar=False), dtype=np.float32)
            full = np.full(n, -1e9, dtype=np.float32); full[cand] = sc
            rankings[q.qid] = to_doc_ranking(full, doc_ids)
        rr_s = time.perf_counter() - t0
        res = evaluate_rankings(f"{a.model or 'bm25'}__{a.chunker}__{a.rerank_base}+{rk}@{a.rerank_top}", "C", questions, rankings,
                                config={"model": a.model, "chunker": a.chunker, "fusion": a.rerank_base, "reranker": rs["hf"],
                                        "rerank_top": a.rerank_top, "n_chunks": n},
                                timing={"rerank_s": round(rr_s, 1), "per_query_s": round(rr_s / len(questions), 2)})
        save_result(EXP, res); print(res.summary(), f"| rerank {rr_s:.0f}s", flush=True)


if __name__ == "__main__":
    main()
