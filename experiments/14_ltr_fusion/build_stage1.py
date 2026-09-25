#!/usr/bin/env python3
"""Compute and cache the first-stage score matrices of one corpus:

* one chunk-level matrix per cached dense leg (e5-small everywhere; bge-m3 on A; potion on C),
  read from the shared EmbeddingCache — only the queries are encoded here (HF_HUB_OFFLINE=1)
* chunk-level BM25 (French-normalised bm25s, k1=1.5, b=0.75) and document-level BM25
* chunk → document map, chunk position within its document, document lengths

  uv run python build_stage1.py --corpus A
"""
from __future__ import annotations

import argparse
import json
import os
import time

import bm25s
import numpy as np

from common14 import (CACHE, DENSE_LEGS, MODELS, Encoder, EmbeddingCache, _key, tokenize,
                      load_corpus_and_chunks)

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def bm25_matrix(texts, questions, k1=1.5, b=0.75) -> np.ndarray:
    r = bm25s.BM25(k1=k1, b=b)
    r.index([tokenize(t) for t in texts], show_progress=False)
    return np.stack([r.get_scores(tokenize(q.question)).astype(np.float32) for q in questions])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    a = ap.parse_args()
    import torch
    torch.set_num_threads(2)
    t0 = time.perf_counter()
    docs, questions, chunks, doc_texts = load_corpus_and_chunks(a.corpus)
    texts = [c.text for c in chunks]
    doc_index = {d.doc_id: i for i, d in enumerate(docs)}
    chunk_doc = np.array([doc_index[c.doc_id] for c in chunks], dtype=np.int32)
    chunk_pos = np.array([int(c.chunk_id.rsplit("#", 1)[1]) for c in chunks], dtype=np.int32)
    counts = np.bincount(chunk_doc, minlength=len(docs))
    doc_start = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
    assert np.all(np.diff(chunk_doc) >= 0), "chunks must be grouped by document"
    print(f"corpus {a.corpus}: {len(docs)} docs / {len(chunks)} chunks / {len(questions)} q "
          f"(load {time.perf_counter()-t0:.0f}s)", flush=True)

    out: dict[str, np.ndarray] = {"chunk_doc": chunk_doc, "chunk_pos": chunk_pos, "doc_start": doc_start}
    cache = EmbeddingCache()
    for leg, (mk, extra) in DENSE_LEGS[a.corpus].items():
        spec = MODELS[mk]
        f = cache.dir / (_key(spec.hf_id, texts, extra) + ".npy")
        if not f.exists():
            raise SystemExit(f"no cached embeddings for {mk} ({extra}) on corpus {a.corpus}: {f}")
        emb = np.load(f)
        t1 = time.perf_counter()
        enc = Encoder(spec)
        qemb = enc.queries([q.question for q in questions])
        out[f"leg_{leg}"] = (qemb @ emb.T).astype(np.float32)
        print(f"  dense leg {leg} ({mk}): {emb.shape} in {time.perf_counter()-t1:.0f}s", flush=True)
        del emb, enc
    t1 = time.perf_counter()
    out["leg_bm25"] = bm25_matrix(texts, questions)
    print(f"  bm25 chunks: {time.perf_counter()-t1:.0f}s", flush=True)
    t1 = time.perf_counter()
    out["bm25_doc"] = bm25_matrix(doc_texts, questions)
    print(f"  bm25 docs: {time.perf_counter()-t1:.0f}s", flush=True)
    np.savez(CACHE / f"{a.corpus}_stage1.npz", **out)
    (CACHE / f"{a.corpus}_stage1.json").write_text(json.dumps({
        "doc_ids": [d.doc_id for d in docs], "qids": [q.qid for q in questions],
        "doc_len": [len(d.text) for d in docs], "n_chunks": len(chunks)}))
    print("saved", CACHE / f"{a.corpus}_stage1.npz", f"total {time.perf_counter()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
