#!/usr/bin/env python3
"""Fill the shared EmbeddingCache for corpus C (run once per model; hours for
transformer models on CPU). Encodes in shards so progress survives a crash.

  uv run python encode_corpus.py --model e5-small --chunker fixed1200_title
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from rag_eval import EmbeddingCache
from rag_eval.cache import _key
from common_c import MODELS, Encoder, chunk_corpus_c, cache_extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="e5-small")
    ap.add_argument("--chunker", default="fixed1200_title")
    ap.add_argument("--shard", type=int, default=20000)
    a = ap.parse_args()
    spec = MODELS[a.model]
    docs, chunks = chunk_corpus_c(a.chunker)
    texts = [c.text for c in chunks]
    cache = EmbeddingCache()
    extra = cache_extra(spec, a.chunker)
    final = cache.dir / (_key(spec.hf_id, texts, extra) + ".npy")
    if final.exists():
        print("already cached:", final); return
    print(f"corpus C: {len(docs)} docs, {len(chunks)} chunks; model {spec.hf_id}", flush=True)
    enc = Encoder(spec)
    parts = []
    t0 = time.perf_counter()
    for i in range(0, len(texts), a.shard):
        shard_texts = texts[i:i + a.shard]
        emb, dt = cache.get_or_compute(spec.hf_id, shard_texts, enc.docs, extra=extra + f"|shard{i}",
                                       label=f"C shard {i}")
        parts.append(emb)
        print(f"  shard {i}-{i+len(shard_texts)} done ({dt:.0f}s, total {time.perf_counter()-t0:.0f}s)", flush=True)
    full = np.concatenate(parts).astype(np.float32)
    np.save(final, full)
    (cache.dir / (final.stem + ".json")).write_text(
        f'{{"model": "{spec.hf_id}", "extra": "{extra}", "n": {len(texts)}, "dim": {full.shape[1]}, '
        f'"label": "C/{a.chunker}", "encode_seconds": {time.perf_counter()-t0:.0f}}}')
    print("saved", final, full.shape, flush=True)


if __name__ == "__main__":
    main()
