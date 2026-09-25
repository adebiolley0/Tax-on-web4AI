#!/usr/bin/env python3
"""Dense leg with a sentence-transformers bi-encoder on corpora A/B: dense-only, RRF and convex fusion with BM25.

Chunk embeddings are cached on /dev/shm (same key scheme as rag_eval.cache / experiment 02, so they can be
copied into experiments/data/emb_cache later).

  python run_dense.py --model maastrichtlawtech/dpr-legal-french --tag dpr-legal-french --corpora A,B
  python run_dense.py --model /dev/shm/exp16/models/e5-small-bsard --tag e5-small-bsard --q_prefix "query: " --d_prefix "passage: "
"""
from __future__ import annotations

import argparse
import time

import numpy as np

import common16 as C
from rag_eval.cache import EmbeddingCache

CHUNKER = {"A": "fixed1500_title", "B": "article_ctx_1200", "C": "C/fixed1200_title"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--hf_id", default=None, help="id used in the cache key (defaults to --model)")
    ap.add_argument("--corpora", default="A,B")
    ap.add_argument("--max_seq", type=int, default=512)
    ap.add_argument("--q_prefix", default="")
    ap.add_argument("--d_prefix", default="")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--fusions", default="dense,rrf,convex0.3,convex0.5,convex0.7")
    a = ap.parse_args()
    tag = a.tag or a.model.split("/")[-1]
    hf_id = a.hf_id or a.model
    from sentence_transformers import SentenceTransformer
    t0 = time.perf_counter()
    m = SentenceTransformer(a.model, device="cpu")
    m.max_seq_length = a.max_seq
    C.log(f"loaded {a.model} in {time.perf_counter() - t0:.0f}s; dim={m.get_sentence_embedding_dimension()} "
          f"max_seq={m.max_seq_length} threads={C.torch.get_num_threads()}")

    def enc(texts, prefix):
        e = m.encode([prefix + t for t in texts], batch_size=a.batch, normalize_embeddings=True, show_progress_bar=False)
        e = np.asarray(e, dtype=np.float32)
        n = np.linalg.norm(e, axis=1, keepdims=True); n[n == 0] = 1
        return e / n

    cache = EmbeddingCache(C.SHM / "emb_cache")
    for name in a.corpora.split(","):
        qs, texts, doc_ids, bm = C.bm25_scores(name)
        key_extra = f"seq{a.max_seq}|d_prefix={a.d_prefix!r}|{CHUNKER[name]}"
        t0 = time.perf_counter()
        emb, enc_s = cache.get_or_compute(hf_id, texts, lambda t: enc(t, a.d_prefix), extra=key_extra, label=f"{name}/{CHUNKER[name]}")
        C.log(f"[{name}] {len(texts)} chunks encoded in {enc_s:.0f}s (cached={enc_s == 0})")
        qemb = enc([q.question for q in qs], a.q_prefix)
        C.evaluate_dense(name, qemb, emb, f"{tag}__{CHUNKER[name]}", tuple(a.fusions.split(",")),
                         extra_config={"hf": hf_id, "max_seq": a.max_seq, "q_prefix": a.q_prefix, "d_prefix": a.d_prefix,
                                       "encode_docs_s": round(enc_s, 1)})


if __name__ == "__main__":
    main()
