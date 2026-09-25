#!/usr/bin/env python3
"""Compute and cache the first-stage chunk-level score matrices (BM25 + e5-small dense).

Reproduces the set-ups of experiments 03 (corpus B: default subset, article_ctx_1200
chunks, bm25s k1=1.2/b=0.75, e5-small from the shared embedding cache, RRF depth 200)
and 09 (corpus C: fixed1200_title chunks, max 200k chars/doc, k1=1.5, RRF depth 300).
No embedding job is run: the cached matrices must exist, only the 40/64 queries are
encoded (HF_HUB_OFFLINE=1).

  HF_HUB_OFFLINE=1 uv run python first_stage.py --corpus B [--clean]
  HF_HUB_OFFLINE=1 uv run python first_stage.py --corpus C
"""
from __future__ import annotations

import argparse
import json
import sys
import time

import bm25s
import numpy as np

from rag_eval import article_chunks, load_questions_c
from rag_eval.cache import EmbeddingCache, _key

from common11 import CACHE  # noqa: E402  (adds sibling experiments to sys.path)
from run_sweep import MODELS, Encoder, load as load_b  # noqa: E402  (02_dense_sweep)
from run_hybrid import tokenize  # noqa: E402  (03_hybrid_rerank)
from common_c import chunk_corpus_c, cache_extra  # noqa: E402  (09_corpus_c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--clean", action="store_true", help="corpus B: experiment-08 cleaned articles")
    a = ap.parse_args()
    import torch
    torch.set_num_threads(2)
    spec = MODELS["e5-small"]
    t0 = time.perf_counter()
    if a.corpus == "B":
        docs, questions = load_b("B", a.clean)
        chunks = article_chunks(docs, 1200, 100, prefix_context=True)
        extra = f"seq{spec.max_seq}|d_prefix={spec.d_prefix!r}|article_ctx_1200"
        k1, rrf_depth, tag = 1.2, 200, "B_clean" if a.clean else "B_raw"
    else:
        questions = load_questions_c()
        docs, chunks = chunk_corpus_c("fixed1200_title")
        extra = cache_extra(spec, "fixed1200_title")
        k1, rrf_depth, tag = 1.5, 300, "C"
    print(f"{tag}: {len(docs)} docs / {len(chunks)} chunks / {len(questions)} q; loaded in {time.perf_counter()-t0:.0f}s", flush=True)
    texts = [c.text for c in chunks]
    doc_index = {d.doc_id: i for i, d in enumerate(docs)}
    chunk_doc = np.array([doc_index[c.doc_id] for c in chunks], dtype=np.int32)

    f = EmbeddingCache().dir / (_key(spec.hf_id, texts, extra) + ".npy")
    if not f.exists():
        print("no cached embeddings for", tag, f); sys.exit(1)
    emb = np.load(f)
    enc = Encoder(spec)
    qemb = enc.queries([q.question for q in questions])
    dense = (qemb @ emb.T).astype(np.float32)
    del emb

    t0 = time.perf_counter()
    r = bm25s.BM25(k1=k1, b=0.75)
    r.index([tokenize(t) for t in texts], show_progress=False)
    idx_s = time.perf_counter() - t0
    bm = np.stack([r.get_scores(tokenize(q.question)).astype(np.float32) for q in questions])
    print(f"bm25 index {idx_s:.0f}s", flush=True)

    np.save(CACHE / f"{tag}_dense_chunks.npy", dense)
    np.save(CACHE / f"{tag}_bm25_chunks.npy", bm)
    np.save(CACHE / f"{tag}_chunk_doc.npy", chunk_doc)
    (CACHE / f"{tag}_meta.json").write_text(json.dumps({
        "doc_ids": [d.doc_id for d in docs], "qids": [q.qid for q in questions], "rrf_depth": rrf_depth,
        "bm25": f"bm25s k1={k1} b=0.75 French tokenize() of exp 03", "n_chunks": len(chunks),
        "emb_key": f.name, "bm25_index_s": round(idx_s, 1)}))
    # titles / meta for the graph builders (corpus B only; corpus C is re-read from myfin_docs)
    if a.corpus == "B":
        (CACHE / f"{tag}_docs.json").write_text(json.dumps(
            [{"id": d.doc_id, "title": d.title, "meta": d.meta, "text": d.text} for d in docs], ensure_ascii=False))
    print("saved", tag)


if __name__ == "__main__":
    main()
