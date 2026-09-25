#!/usr/bin/env python3
"""Corpus B only: does graph expansion improve the *candidate window* of a cross-encoder?

Reranks the top-30 candidates of several first stages with cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
(the fast reranker that gave the corpus-B bar, val MRR 0.570 in experiment 03):
  * rrf_chunks   – exact experiment-03 protocol (top-30 fused *chunks*), sanity check
  * rrf          – top-30 *documents* of RRF, best first-stage chunk of each
  * rrf+expand   – top-30 documents after graph expansion (config selected on train in run_graph.py)
  * rrf+seq      – top-30 documents after sequential-neighbour expansion only
  * rrf+prior    – top-30 documents after the structure prior

  HF_HUB_OFFLINE=1 uv run python rerank_b.py --tag B_raw
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

from rag_eval import article_chunks, load_questions_b, evaluate_rankings, save_result
from rag_eval.corpora import Doc
from common11 import FirstStage, CACHE, EXP, minmax, ranking_from_scores, rrf_chunks
from propagate import PropGraph, top_k_seeds
from prior import boost_matrix, doc_attrs_b
from run_graph import rownorm

RERANKER = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="B_raw")
    ap.add_argument("--top", type=int, default=30)
    a = ap.parse_args()
    import torch
    torch.set_num_threads(2)
    fs = FirstStage(a.tag)
    questions = load_questions_b()
    docs = json.loads((CACHE / f"{a.tag}_docs.json").read_text())
    chunks = article_chunks([Doc(d["id"], d["title"], d["text"], d["meta"]) for d in docs], 1200, 100, prefix_context=True)
    assert len(chunks) == fs.n_chunks
    texts = [c.text for c in chunks]
    g = json.loads((CACHE / f"{a.tag}_graph.json").read_text())
    G = PropGraph(fs.doc_ids, g["edges"], g["groups"])
    summ = json.loads((CACHE.parent / f"summary_{a.tag}.json").read_text())
    sel = next(r["config"] for r in summ["runs"] if r["name"].startswith("rrf+expand_sel["))
    reg, dom = doc_attrs_b(fs.doc_ids)

    # chunk-level RRF (experiment-03 protocol) and doc-level first stages
    nq = len(questions)
    rrf_c = np.zeros((nq, fs.n_chunks), dtype=np.float32)
    for i in range(nq):
        d, b = fs.chunk["dense"][i], fs.chunk["bm25"][i]
        rrf_c[i] = rrf_chunks([np.argsort(-d)[:200], np.argsort(-b)[:200]], 60, fs.n_chunks)
    Sn = np.stack([minmax(r) for r in fs.doc_max(rrf_c)]).astype(np.float32)
    seeds = top_k_seeds(Sn, sel["k"])
    stages = {
        "rrf": Sn,
        "rrf+expand_sel": Sn + sel["alpha"] * rownorm(G.expand(seeds, {t: 1.0 for t in sel["types"]}, sel["norm"], sel["hops"])),
        "rrf+seq": Sn + 0.3 * rownorm(G.expand(top_k_seeds(Sn, 30), {"seq": 1.0}, "sum", 1)),
        "rrf+prior": Sn * boost_matrix(questions, reg, dom, 0.3, 0.5),
    }
    # best first-stage chunk per doc (for the pair texts)
    best_chunk = np.zeros((nq, fs.n_docs), dtype=np.int64)
    for i in range(nq):
        order = np.argsort(-rrf_c[i], kind="stable")
        seen = np.zeros(fs.n_docs, dtype=bool)
        for j in order:
            d = fs.chunk_doc[j]
            if not seen[d]:
                seen[d] = True; best_chunk[i, d] = j
    from sentence_transformers import CrossEncoder
    ce = CrossEncoder(RERANKER, max_length=512, device="cpu")

    def rerank(name: str, cand_chunks: list[np.ndarray], config: dict):
        t0 = time.perf_counter()
        rankings = {}
        for i, q in enumerate(questions):
            cand = cand_chunks[i]
            sc = np.asarray(ce.predict([(q.question, texts[j]) for j in cand], batch_size=8, show_progress_bar=False), dtype=np.float32)
            full = np.full(fs.n_chunks, -1e9, dtype=np.float32); full[cand] = sc
            rankings[q.qid] = ranking_from_scores(fs.doc_max(full[None, :])[0], fs.doc_ids)
        dt = time.perf_counter() - t0
        res = evaluate_rankings(name, "B", questions, rankings, config={"tag": a.tag, "reranker": RERANKER, "rerank_top": a.top, **config},
                                timing={"rerank_s": round(dt, 1), "per_query_s": round(dt / nq, 2)})
        save_result(EXP, res); print(res.summary(), f"| {dt:.0f}s", flush=True)
        # candidate recall: is an expected doc among the candidates?
        hits = sum(1 for i, q in enumerate(questions) if set(q.expected) & {fs.doc_ids[fs.chunk_doc[j]] for j in cand_chunks[i]})
        vh = sum(1 for i, q in enumerate(questions) if q.split == "val" and set(q.expected) & {fs.doc_ids[fs.chunk_doc[j]] for j in cand_chunks[i]})
        print(f"   candidate recall@{a.top}: all {hits/nq:.3f}  val {vh/sum(1 for q in questions if q.split=='val'):.3f}", flush=True)

    rerank("rrf_chunks+mmarco-minilm@30", [np.argsort(-rrf_c[i])[: a.top] for i in range(nq)], {"candidates": "top-30 fused chunks (exp 03)"})
    for name, S in stages.items():
        cands = []
        for i in range(nq):
            top_docs = np.argsort(-S[i], kind="stable")[: a.top]
            cands.append(best_chunk[i, top_docs])
        rerank(f"{name}+mmarco-minilm@30", cands, {"candidates": f"top-30 docs of {name}, best chunk each"})


if __name__ == "__main__":
    main()
