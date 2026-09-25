#!/usr/bin/env python3
"""Late interaction (ColBERT) via PyLate: full MaxSim retrieval over all chunks, ColBERT
as a reranker of BM25 / RRF candidates, and fusion with BM25 and cached dense legs.

Models
  colbert-fr       antoinelouis/colbertv1-camembert-base-mmarcoFR (111M, French, 128d) – A and B
  jina-colbert-v2  jinaai/jina-colbert-v2 (560M, multilingual, 128d)                 – A only

The token embeddings are kept in memory only (disk is tight); the exact (nq, n_chunks)
MaxSim matrix is cached under cache/ so every downstream variant is free to recompute.

Usage: uv run python run_colbert.py --corpus A --model colbert-fr [--voyager]
"""
from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

import numpy as np

from common12 import (LOCAL_CACHE, load_corpus, bm25_scores, dense_legs, fusion_suite, evaluate,
                      rrf_matrix)
from maxsim import maxsim_matrix, rerank_scores

COLBERT_MODELS = {
    # Stanford checkpoint trained with colbert-ai on a CamemBERT tokenizer: the '[unused0]' /
    # '[unused1]' markers of artifact.metadata do not exist in that vocabulary, so colbert-ai
    # mapped both to <unk> (id 4) at training time. PyLate instead *adds* the two tokens and
    # mis-sizes the embedding matrix by one (IndexError), so we reproduce the training set-up
    # explicitly with "<unk>" prefixes.
    "colbert-fr": {"hf": "antoinelouis/colbertv1-camembert-base-mmarcoFR", "params_m": 111,
                   "kw": dict(query_prefix="<unk>", document_prefix="<unk>", query_length=48, document_length=512)},
    "jina-colbert-v2": {"hf": "jinaai/jina-colbert-v2", "params_m": 560,
                        "kw": dict(query_prefix="[QueryMarker]", document_prefix="[DocumentMarker]",
                                   attend_to_expansion_tokens=True, trust_remote_code=True,
                                   query_length=48, document_length=512)},
}


def load_model(spec):
    from pylate import models
    t0 = time.perf_counter()
    m = models.ColBERT(model_name_or_path=spec["hf"], device="cpu", **spec["kw"])
    return m, time.perf_counter() - t0


def encode(m, texts, is_query: bool, bs: int):
    t0 = time.perf_counter()
    embs = m.encode(texts, batch_size=bs, is_query=is_query, show_progress_bar=False, convert_to_numpy=True)
    return [np.asarray(e, dtype=np.float32) for e in embs], time.perf_counter() - t0


def voyager_probe(m, c, q_embs, d_embs, k: int = 50) -> dict:
    """Build a PyLate Voyager (HNSW) index in a temp folder: index size + query latency."""
    from pylate import indexes, retrieve
    folder = Path("/tmp") / "exp12_voyager"
    if folder.exists():
        shutil.rmtree(folder)
    t0 = time.perf_counter()
    index = indexes.Voyager(index_folder=str(folder), index_name="idx", override=True, embedding_size=d_embs[0].shape[1])
    index.add_documents(documents_ids=[ch.chunk_id for ch in c.chunks], documents_embeddings=d_embs)
    build_s = time.perf_counter() - t0
    size = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
    retriever = retrieve.ColBERT(index=index)
    t0 = time.perf_counter()
    res = retriever.retrieve(queries_embeddings=q_embs, k=k)
    q_s = (time.perf_counter() - t0) / len(q_embs)
    # document ranking from the index (chunk → doc, max)
    cid2doc = {ch.chunk_id: ch.doc_id for ch in c.chunks}
    rankings = {}
    for q, hits in zip(c.questions, res):
        seen, out = set(), []
        for h in hits:
            d = cid2doc[h["id"]]
            if d not in seen:
                seen.add(d); out.append(d)
        rankings[q.qid] = out
    shutil.rmtree(folder, ignore_errors=True)
    return {"build_s": round(build_s, 1), "index_bytes": size, "query_s": round(q_s, 3), "rankings": rankings}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A")
    ap.add_argument("--model", default="colbert-fr")
    ap.add_argument("--dense", default="e5-small,e5-base,bge-m3")
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--voyager", action="store_true")
    a = ap.parse_args()
    c = load_corpus(a.corpus)
    spec = COLBERT_MODELS[a.model]
    print(f"corpus {c.name}: {len(c.docs)} docs / {c.n} chunks / {len(c.questions)} q; model {spec['hf']}", flush=True)

    cache = LOCAL_CACHE / f"colbert_{c.name}_{a.model}.npz"
    voy = None
    if cache.exists() and not a.voyager:
        z = np.load(cache, allow_pickle=True)
        full, timing, stats = z["scores"], z["timing"].item(), z["stats"].item()
        print("cached scores", timing, stats, flush=True)
    else:
        m, load_s = load_model(spec)
        q_embs, q_s = encode(m, [q.question for q in c.questions], True, 16)
        print(f"queries encoded {q_s:.1f}s; q tokens mean {np.mean([e.shape[0] for e in q_embs]):.1f}", flush=True)
        # rerank-cost probe: encoding 50 candidate chunks on the fly = the realistic per-query cost
        t0 = time.perf_counter(); encode(m, c.texts[:50], False, a.bs); probe_s = time.perf_counter() - t0
        d_embs, enc_s = encode(m, c.texts, False, a.bs)
        n_tok = sum(e.shape[0] for e in d_embs)
        print(f"docs encoded {enc_s:.0f}s; {n_tok} tokens, mean {n_tok / c.n:.1f}/chunk", flush=True)
        full, ms_s = maxsim_matrix(q_embs, d_embs)
        timing = {"model_load_s": round(load_s, 1), "encode_docs_s": round(enc_s, 1), "encode_queries_s": round(q_s, 2),
                  "maxsim_all_s": round(ms_s, 2), "maxsim_per_query_s": round(ms_s / len(c.questions), 3),
                  "rerank50_encode_s_per_query": round(probe_s, 2)}
        stats = {"doc_tokens": int(n_tok), "tokens_per_chunk": round(n_tok / c.n, 1), "dim": int(d_embs[0].shape[1]),
                 "index_bytes_fp32": int(n_tok * d_embs[0].shape[1] * 4)}
        np.savez(cache, scores=full, timing=timing, stats=stats)
        print("timing", timing, "stats", stats, flush=True)
        if a.voyager:
            voy = voyager_probe(m, c, q_embs, d_embs)
            print("voyager", {k: v for k, v in voy.items() if k != "rankings"}, flush=True)
        del m, d_embs

    bm, _ = bm25_scores(c)
    dense = dense_legs(c, a.dense.split(",")) if a.dense else {}
    print("dense legs:", list(dense), flush=True)
    cfg = {"model": spec["hf"], "params_m": spec["params_m"], **spec["kw"], **stats}
    base = f"colbert-{a.model}"
    # 1) full retrieval + fusion battery
    fusion_suite(base, c, full, cfg, bm, dense, timing)
    # 2) ColBERT as a reranker over first-stage candidates
    for top in (30, 50):
        evaluate(f"{base}__rerank_bm25@{top}", c, rerank_scores(full, bm, top),
                 {**cfg, "rerank_base": "bm25", "rerank_top": top}, timing)
    if "e5-small" in dense:
        rr = rrf_matrix([dense["e5-small"], bm])
        for top in (30, 50):
            evaluate(f"{base}__rerank_rrf-e5-small-bm25@{top}", c, rerank_scores(full, rr, top),
                     {**cfg, "rerank_base": "rrf(e5-small,bm25)", "rerank_top": top}, timing)
    if "bge-m3" in dense:
        evaluate(f"{base}__rerank_bge-m3@50", c, rerank_scores(full, dense["bge-m3"], 50),
                 {**cfg, "rerank_base": "bge-m3 dense", "rerank_top": 50}, timing)
    if voy is not None:
        from rag_eval import evaluate_rankings, save_result
        from common12 import EXP
        res = evaluate_rankings(f"{base}__voyager_hnsw_k50", c.name, c.questions, voy["rankings"],
                                config={**cfg, "index": "pylate Voyager HNSW", "k": 50},
                                timing={k: v for k, v in voy.items() if k != "rankings"})
        save_result(EXP, res); print(res.summary(), flush=True)


if __name__ == "__main__":
    main()
