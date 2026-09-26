#!/usr/bin/env python3
"""Stage-1 top-K cache for human + mined questions (numpy / bm25s only; needs cache/<corpus>_qemb_e5.npy).

Legs are exactly those of experiment 14 (same chunker, same cached e5-small chunk embeddings, same exp-01
BM25 tokenizer, k1 1.5 / b 0.75 at chunk and document level); fusions (convex 0.5, RRF60) are computed on
the full chunk vectors and only the top-K kept.
  uv run python ../21_mined_eval/build_stage1.py --corpus B
"""
from __future__ import annotations

import argparse
import json
import time

import bm25s
import numpy as np

from common21 import CACHE, TOPK_CHUNK, TOPK_DOC, all_questions, minmax, rrf_scores, topk
from common14 import DENSE_LEGS, MODELS, _key, tokenize, load_corpus_and_chunks
from rag_eval.cache import EmbeddingCache


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    a = ap.parse_args()
    t0 = time.perf_counter()
    docs, _, chunks, doc_texts = load_corpus_and_chunks(a.corpus)
    questions = all_questions(a.corpus)
    qids = [q.qid for q in questions]
    texts = [c.text for c in chunks]
    doc_index = {d.doc_id: i for i, d in enumerate(docs)}
    chunk_doc = np.array([doc_index[c.doc_id] for c in chunks], dtype=np.int32)
    counts = np.bincount(chunk_doc, minlength=len(docs))
    doc_start = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
    assert np.all(np.diff(chunk_doc) >= 0)
    nq, nch = len(questions), len(chunks)
    print(f"corpus {a.corpus}: {len(docs)} docs / {nch} chunks / {nq} questions (load {time.perf_counter()-t0:.0f}s)", flush=True)

    qmeta = json.loads((CACHE / f"{a.corpus}_qemb_e5.json").read_text())
    assert qmeta["qids"] == qids, "query embeddings do not match the question list: rerun embed_queries.py"
    qemb = np.load(CACHE / f"{a.corpus}_qemb_e5.npy")
    mk, extra = DENSE_LEGS[a.corpus]["e5"]
    f = EmbeddingCache().dir / (_key(MODELS[mk].hf_id, texts, extra) + ".npy")
    assert f.exists(), f"no cached e5 chunk embeddings for {a.corpus}: {f}"
    emb = np.load(f)
    assert emb.shape[0] == nch

    t1 = time.perf_counter()
    r_chunk = bm25s.BM25(k1=1.5, b=0.75); r_chunk.index([tokenize(t) for t in texts], show_progress=False)
    print(f"  bm25 chunk index {time.perf_counter()-t1:.0f}s", flush=True); t1 = time.perf_counter()
    r_doc = bm25s.BM25(k1=1.5, b=0.75); r_doc.index([tokenize(t) for t in doc_texts], show_progress=False)
    print(f"  bm25 doc index {time.perf_counter()-t1:.0f}s", flush=True); t1 = time.perf_counter()

    K, KD = min(TOPK_CHUNK, nch), min(TOPK_DOC, len(docs))
    out = {"chunk_doc": chunk_doc, "doc_start": doc_start}
    for name, k in (("e5", K), ("bm25", K), ("convex05", K), ("rrf60", K), ("bm25doc", KD)):
        out[f"{name}_idx"] = np.full((nq, k), -1, dtype=np.int32)
        out[f"{name}_val"] = np.zeros((nq, k), dtype=np.float32)
        out[f"{name}_min"] = np.zeros(nq, dtype=np.float32)
        out[f"{name}_max"] = np.zeros(nq, dtype=np.float32)

    def put(name, qi, v):
        idx, val = topk(v, out[f"{name}_idx"].shape[1])
        out[f"{name}_idx"][qi], out[f"{name}_val"][qi] = idx, val
        out[f"{name}_min"][qi], out[f"{name}_max"][qi] = float(v.min()), float(v.max())

    B = 32
    for s in range(0, nq, B):
        dense = (qemb[s:s + B] @ emb.T).astype(np.float64)
        for j in range(dense.shape[0]):
            qi = s + j
            toks = tokenize(questions[qi].question)
            bm = r_chunk.get_scores(toks).astype(np.float64)
            bd = r_doc.get_scores(toks).astype(np.float64)
            e5 = dense[j]
            put("e5", qi, e5); put("bm25", qi, bm); put("bm25doc", qi, bd)
            put("convex05", qi, 0.5 * minmax(e5) + 0.5 * minmax(bm))
            put("rrf60", qi, rrf_scores([e5, bm], 60.0))
        if (s // B) % 5 == 0:
            print(f"  {min(s+B, nq)}/{nq} questions, {time.perf_counter()-t1:.0f}s", flush=True)
    np.savez(CACHE / f"{a.corpus}_stage1.npz", **out)
    (CACHE / f"{a.corpus}_stage1.json").write_text(json.dumps({
        "qids": qids, "doc_ids": [d.doc_id for d in docs], "doc_len": [len(d.text) for d in docs], "n_chunks": nch,
        "chunk_ids": [c.chunk_id for c in chunks], "topk_chunk": K, "topk_doc": KD,
        "legs": {"e5": f"{MODELS[mk].hf_id} | {extra}", "bm25": "bm25s k1=1.5 b=0.75, exp-01 tokenizer, chunk level",
                 "bm25doc": "bm25s k1=1.5 b=0.75, exp-01 tokenizer, document level (exp-14 doc_texts)"}}))
    print(f"saved cache/{a.corpus}_stage1.npz in {time.perf_counter()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
