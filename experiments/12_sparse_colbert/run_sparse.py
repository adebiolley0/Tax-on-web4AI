#!/usr/bin/env python3
"""Learned sparse retrieval (SPLADE-style) on corpus A / B.

Models
  opensearch : opensearch-project/opensearch-neural-sparse-encoding-multilingual-v1
               (doc-side MLM + SPLADE pooling; query side = tokenizer + IDF table, no inference)
  splade-fr  : antoinelouis/splade-max-camembert-base-mmarcoFR (both sides encoded; only if on disk)

Score = dot product of the sparse vectors (scipy CSR). The (nq, n_chunks) score matrix is
cached under cache/ so fusions can be re-run without re-encoding.

Usage: uv run python run_sparse.py --corpus A --model opensearch
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import scipy.sparse as sp
import torch

from common12 import (LOCAL_CACHE, load_corpus, bm25_scores, dense_legs, fusion_suite, evaluate)

SPARSE_MODELS = {
    "opensearch": {"hf": "opensearch-project/opensearch-neural-sparse-encoding-multilingual-v1", "kind": "st", "params_m": 160},
    "splade-fr": {"hf": "antoinelouis/splade-max-camembert-base-mmarcoFR", "kind": "mlm-max", "params_m": 111},
}


def _to_csr(t: torch.Tensor) -> sp.csr_matrix:
    t = t.coalesce()
    idx = t.indices().numpy()
    return sp.csr_matrix((t.values().numpy().astype(np.float32), (idx[0], idx[1])), shape=tuple(t.shape))


def encode_st_sparse(hf: str, texts: list[str], queries: list[str], max_len: int = 512, bs: int = 4):
    # bs=4: the MLM logits (bs, 512, 105k vocab) fp32 are 0.9 GB per batch; bs=16 was OOM-killed
    # (5.3 GB RSS) in the session's memory cgroup.
    from sentence_transformers import SparseEncoder
    t0 = time.perf_counter()
    m = SparseEncoder(hf, device="cpu")
    m.max_seq_length = max_len
    load_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    parts = []  # encode in slices so the (n, vocab) intermediate never materialises for corpus B
    for i in range(0, len(texts), 256):
        parts.append(_to_csr(m.encode_document(texts[i:i + 256], batch_size=bs, show_progress_bar=False,
                                               convert_to_sparse_tensor=True)))
        print(f"  encoded {min(i + 256, len(texts))}/{len(texts)} ({time.perf_counter() - t0:.0f}s)", flush=True)
    D = sp.vstack(parts).tocsr()
    enc_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    Q = _to_csr(m.encode_query(queries, batch_size=bs, show_progress_bar=False, convert_to_sparse_tensor=True))
    q_s = time.perf_counter() - t0
    return D, Q, {"model_load_s": round(load_s, 1), "encode_docs_s": round(enc_s, 1), "encode_queries_s": round(q_s, 2)}


def encode_mlm_max(hf: str, texts: list[str], queries: list[str], max_len_doc: int = 512, max_len_q: int = 64, bs: int = 16):
    """SPLADE-max: amax_over_tokens(log1p(relu(MLM logits))) with the attention mask."""
    from transformers import AutoModelForMaskedLM, AutoTokenizer
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(hf)
    model = AutoModelForMaskedLM.from_pretrained(hf).eval()
    # transformers 5.3 does NOT tie the MLM decoder of this 2024 CamemBERT checkpoint (the file has no
    # lm_head.decoder.* keys; the load report lists them as MISSING and leaves a *random* decoder and a
    # zero bias → 78 % of the vocabulary "active", garbage top tokens). Re-tie explicitly.
    emb = model.get_input_embeddings().weight
    dec = model.lm_head.decoder
    if not torch.equal(dec.weight, emb):
        dec.weight = emb
    if getattr(model.lm_head, "bias", None) is not None and not torch.equal(dec.bias, model.lm_head.bias):
        dec.bias = model.lm_head.bias
    load_s = time.perf_counter() - t0

    def enc(batch_texts, max_len):
        rows, cols, vals = [], [], []
        with torch.inference_mode():
            for i in range(0, len(batch_texts), bs):
                b = tok(batch_texts[i:i + bs], padding=True, truncation=True, max_length=max_len, return_tensors="pt")
                logits = model(**b).logits
                act = torch.amax(torch.log1p(torch.relu(logits)) * b["attention_mask"].unsqueeze(-1), dim=1)
                nz = act.nonzero(as_tuple=False)
                rows.append((nz[:, 0] + i).numpy()); cols.append(nz[:, 1].numpy()); vals.append(act[nz[:, 0], nz[:, 1]].numpy())
        return sp.csr_matrix((np.concatenate(vals).astype(np.float32), (np.concatenate(rows), np.concatenate(cols))),
                             shape=(len(batch_texts), model.config.vocab_size))

    t0 = time.perf_counter(); D = enc(texts, max_len_doc); enc_s = time.perf_counter() - t0
    t0 = time.perf_counter(); Q = enc(queries, max_len_q); q_s = time.perf_counter() - t0
    # the model card L2-normalises both sides (cosine of the sparse vectors)
    def _l2(M: sp.csr_matrix) -> sp.csr_matrix:
        norms = np.sqrt(np.asarray(M.multiply(M).sum(axis=1)).ravel()); norms[norms == 0] = 1.0
        return sp.diags(1.0 / norms) @ M
    D, Q = _l2(D).tocsr(), _l2(Q).tocsr()
    return D, Q, {"model_load_s": round(load_s, 1), "encode_docs_s": round(enc_s, 1), "encode_queries_s": round(q_s, 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A")
    ap.add_argument("--model", default="opensearch")
    ap.add_argument("--dense", default="e5-small,e5-base,bge-m3")
    a = ap.parse_args()
    c = load_corpus(a.corpus)
    spec = SPARSE_MODELS[a.model]
    print(f"corpus {c.name}: {len(c.docs)} docs / {c.n} chunks / {len(c.questions)} q; model {spec['hf']}", flush=True)

    cache = LOCAL_CACHE / f"sparse_{c.name}_{a.model}.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        scores, timing, stats = z["scores"], z["timing"].item(), z["stats"].item()
        print("cached scores", flush=True)
    else:
        qs = [q.question for q in c.questions]
        if spec["kind"] == "st":
            D, Q, timing = encode_st_sparse(spec["hf"], c.texts, qs)
        else:
            D, Q, timing = encode_mlm_max(spec["hf"], c.texts, qs)
        t0 = time.perf_counter()
        scores = (Q @ D.T).toarray().astype(np.float32)
        timing["search_s"] = round(time.perf_counter() - t0, 3)
        stats = {"doc_nnz_mean": round(D.nnz / D.shape[0], 1), "query_nnz_mean": round(Q.nnz / Q.shape[0], 1),
                 "index_bytes": int(D.data.nbytes + D.indices.nbytes + D.indptr.nbytes), "vocab": int(D.shape[1])}
        np.savez(cache, scores=scores, timing=timing, stats=stats)
    print("timing", timing, "stats", stats, flush=True)

    bm, _ = bm25_scores(c)
    dense = dense_legs(c, a.dense.split(",")) if a.dense else {}
    print("dense legs:", list(dense), flush=True)
    evaluate(f"bm25__{c.chunker}", c, bm, {"model": "bm25s k1=1.2 b=0.75 (exp03 tokenizer)"})
    for k, m in dense.items():
        evaluate(f"{k}__{c.chunker}__dense", c, m, {"model": k, "cached": True})
    cfg = {"model": spec["hf"], "params_m": spec["params_m"], **stats}
    fusion_suite(f"sparse-{a.model}", c, scores, cfg, bm, dense, timing)


if __name__ == "__main__":
    main()
