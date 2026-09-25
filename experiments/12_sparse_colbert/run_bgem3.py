#!/usr/bin/env python3
"""BGE-M3's three heads from ONE forward pass: dense (CLS), sparse (lexical weights) and
multi-vector (ColBERT). Implements the FlagEmbedding BGEM3 formulas directly on top of
transformers (no FlagEmbedding dependency):

  sparse : w_t = relu(sparse_linear(h_t)); per token id keep max(w); drop special tokens;
           score = sum over shared token ids of q_w * d_w
  colbert: v_t = normalize(colbert_linear(h_t)) for t >= 1 (CLS skipped), masked;
           score = mean over query tokens of max over doc tokens of q·d
  dense  : normalize(h_CLS) – recomputed only as a sanity check against the exp-02 cache.

568M params → corpus A only. Usage: uv run python run_bgem3.py --corpus A
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import scipy.sparse as sp
import torch

from common12 import (LOCAL_CACHE, load_corpus, bm25_scores, dense_legs, fusion_suite, evaluate,
                      rrf_matrix, tuned_convex, minmax)
from maxsim import maxsim_matrix, rerank_scores

HF = "BAAI/bge-m3"


def encode_all(texts: list[str], max_len: int, bs: int, model, tok, sparse_lin, colbert_lin, special: set[int]):
    rows, cols, vals, col_vecs, dense = [], [], [], [], []
    with torch.inference_mode():
        for i in range(0, len(texts), bs):
            b = tok(texts[i:i + bs], padding=True, truncation=True, max_length=max_len, return_tensors="pt")
            h = model(**b).last_hidden_state                                   # (B, L, 1024)
            am = b["attention_mask"]
            dense.append(torch.nn.functional.normalize(h[:, 0], dim=-1).numpy())
            w = torch.relu(sparse_lin(h)).squeeze(-1) * am                        # (B, L)
            ids = b["input_ids"]
            for j in range(h.shape[0]):
                d: dict[int, float] = {}
                for t, wt in zip(ids[j].tolist(), w[j].tolist()):
                    if wt > 0 and t not in special and wt > d.get(t, 0.0):
                        d[t] = wt
                rows.extend([i + j] * len(d)); cols.extend(d.keys()); vals.extend(d.values())
            cv = torch.nn.functional.normalize(colbert_lin(h[:, 1:]), dim=-1) * am[:, 1:, None]
            for j in range(h.shape[0]):
                L = int(am[j, 1:].sum())
                col_vecs.append(cv[j, :L].to(torch.float16).numpy())
    S = sp.csr_matrix((np.asarray(vals, dtype=np.float32), (rows, cols)), shape=(len(texts), tok.vocab_size))
    return S, col_vecs, np.concatenate(dense)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A")
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--dense", default="e5-small,bge-m3")
    a = ap.parse_args()
    if a.corpus != "A":
        raise SystemExit("bge-m3 (568M) is restricted to corpus A on this CPU box")
    c = load_corpus(a.corpus)
    print(f"corpus {c.name}: {len(c.docs)} docs / {c.n} chunks / {len(c.questions)} q; {HF} sparse+colbert heads", flush=True)

    cache = LOCAL_CACHE / f"bgem3_{c.name}.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        sparse_sc, colbert_sc, timing, stats = z["sparse"], z["colbert"], z["timing"].item(), z["stats"].item()
        print("cached scores", timing, stats, flush=True)
    else:
        from huggingface_hub import hf_hub_download
        from transformers import AutoModel, AutoTokenizer
        t0 = time.perf_counter()
        tok = AutoTokenizer.from_pretrained(HF)
        model = AutoModel.from_pretrained(HF).eval()
        sparse_lin = torch.nn.Linear(model.config.hidden_size, 1)
        sparse_lin.load_state_dict(torch.load(hf_hub_download(HF, "sparse_linear.pt"), map_location="cpu"))
        colbert_lin = torch.nn.Linear(model.config.hidden_size, model.config.hidden_size)
        colbert_lin.load_state_dict(torch.load(hf_hub_download(HF, "colbert_linear.pt"), map_location="cpu"))
        special = {tok.cls_token_id, tok.eos_token_id, tok.pad_token_id, tok.unk_token_id}
        load_s = time.perf_counter() - t0
        qs = [q.question for q in c.questions]
        t0 = time.perf_counter()
        Qs, q_col, _ = encode_all(qs, 64, 16, model, tok, sparse_lin, colbert_lin, special)
        q_s = time.perf_counter() - t0
        t0 = time.perf_counter(); encode_all(c.texts[:50], 512, a.bs, model, tok, sparse_lin, colbert_lin, special)
        probe_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        Ds, d_col, d_dense = encode_all(c.texts, 512, a.bs, model, tok, sparse_lin, colbert_lin, special)
        enc_s = time.perf_counter() - t0
        print(f"docs encoded {enc_s:.0f}s", flush=True)
        # sanity: our dense CLS vs the experiment-02 cache (same model, same chunks, seq 512)
        from common12 import dense_cache_path
        ref = np.load(dense_cache_path(c, "bge-m3"))
        cos = float(np.mean(np.sum(ref * d_dense, axis=1)))
        t0 = time.perf_counter(); sparse_sc = (Qs @ Ds.T).toarray().astype(np.float32); sp_s = time.perf_counter() - t0
        colbert_sc, ms_s = maxsim_matrix(q_col, d_col, normalize_by_qlen=True)
        n_tok = sum(e.shape[0] for e in d_col)
        timing = {"model_load_s": round(load_s, 1), "encode_docs_s": round(enc_s, 1), "encode_queries_s": round(q_s, 2),
                  "sparse_search_s": round(sp_s, 3), "maxsim_all_s": round(ms_s, 2),
                  "maxsim_per_query_s": round(ms_s / len(c.questions), 3), "rerank50_encode_s_per_query": round(probe_s, 2)}
        stats = {"dense_cos_vs_exp02_cache": round(cos, 4), "doc_nnz_mean": round(Ds.nnz / Ds.shape[0], 1),
                 "query_nnz_mean": round(Qs.nnz / Qs.shape[0], 1),
                 "sparse_index_bytes": int(Ds.data.nbytes + Ds.indices.nbytes + Ds.indptr.nbytes),
                 "doc_tokens": int(n_tok), "tokens_per_chunk": round(n_tok / c.n, 1), "colbert_dim": 1024,
                 "colbert_index_bytes_fp16": int(n_tok * 1024 * 2)}
        np.savez(cache, sparse=sparse_sc, colbert=colbert_sc, timing=timing, stats=stats)
        print("timing", timing, "stats", stats, flush=True)
        del model, d_col

    bm, _ = bm25_scores(c)
    dense = dense_legs(c, a.dense.split(","))
    print("dense legs:", list(dense), flush=True)
    cfg = {"model": HF, "params_m": 568, **stats}
    # learned sparse head
    fusion_suite("sparse-bge-m3", c, sparse_sc, {**cfg, "head": "sparse"}, bm, dense, timing)
    # colbert head: full retrieval, fusion, and as reranker
    base = "colbert-bge-m3"
    fusion_suite(base, c, colbert_sc, {**cfg, "head": "colbert"}, bm, dense, timing)
    for top in (30, 50):
        evaluate(f"{base}__rerank_bm25@{top}", c, rerank_scores(colbert_sc, bm, top), {**cfg, "rerank_base": "bm25", "rerank_top": top}, timing)
    if "e5-small" in dense:
        rr = rrf_matrix([dense["e5-small"], bm])
        for top in (30, 50):
            evaluate(f"{base}__rerank_rrf-e5-small-bm25@{top}", c, rerank_scores(colbert_sc, rr, top),
                     {**cfg, "rerank_base": "rrf(e5-small,bm25)", "rerank_top": top}, timing)
    if "bge-m3" in dense:
        dm = dense["bge-m3"]
        evaluate(f"{base}__rerank_bge-m3@50", c, rerank_scores(colbert_sc, dm, 50), {**cfg, "rerank_base": "bge-m3 dense", "rerank_top": 50}, timing)
        # M3 "all" combinations (dense + sparse + colbert of the same model)
        evaluate("bge-m3-all__rrf3", c, rrf_matrix([dm, sparse_sc, colbert_sc]), {**cfg, "fusion": "rrf", "legs": ["dense", "sparse", "colbert"]})
        m3 = np.stack([(minmax(dm[i]) + 0.3 * minmax(sparse_sc[i]) + minmax(colbert_sc[i])) / 2.3 for i in range(len(c.questions))])
        evaluate("bge-m3-all__paper-weights_1-0.3-1", c, m3, {**cfg, "fusion": "convex minmax", "weights": [1, 0.3, 1]})
        tuned_convex("bge-m3-dense+sparse", c, dm, sparse_sc, {**cfg, "legs": ["dense", "sparse"]})
        tuned_convex("bge-m3-dense+colbert", c, dm, colbert_sc, {**cfg, "legs": ["dense", "colbert"]})
        evaluate("bge-m3-all+bm25__rrf4", c, rrf_matrix([dm, sparse_sc, colbert_sc, bm]), {**cfg, "fusion": "rrf", "legs": ["dense", "sparse", "colbert", "bm25"]})


if __name__ == "__main__":
    main()
