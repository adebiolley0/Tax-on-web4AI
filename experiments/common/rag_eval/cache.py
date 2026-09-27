"""On-disk embedding cache: each (model, texts, extra) triple is encoded once.

Files live in ``experiments/data/emb_cache/<key>.npy`` (float32 matrix) + ``<key>.json`` (model,
extra, n, dim, label, encode seconds).  The key hashes the model name, the ``extra`` tag (chunking /
prefix settings) and the SHA-1 of every text, so two runs that embed byte-identical texts share one
file; :func:`cache_key` lets a script locate a matrix written by another experiment.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Callable, Sequence

import numpy as np

from rag_eval.corpora import DATA_DIR

CACHE_DIR = DATA_DIR / "emb_cache"


def cache_key(model: str, texts: Sequence[str], extra: str = "") -> str:
    """24-hex key of (model, extra, len(texts), sha1 of each text)."""
    h = hashlib.sha256()
    h.update(model.encode()); h.update(b"\0"); h.update(extra.encode()); h.update(b"\0")
    h.update(str(len(texts)).encode())
    for t in texts:
        h.update(hashlib.sha1(t.encode("utf-8")).digest())
    return h.hexdigest()[:24]


_key = cache_key      # pre-0.3 name, still imported by some experiments


class EmbeddingCache:
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.dir = Path(cache_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def path(self, model: str, texts: Sequence[str], extra: str = "") -> Path:
        """Where the matrix for these inputs is (or would be) stored."""
        return self.dir / f"{cache_key(model, texts, extra)}.npy"

    def get_or_compute(
        self,
        model: str,
        texts: Sequence[str],
        encode: Callable[[Sequence[str]], np.ndarray],
        extra: str = "",
        label: str = "",
    ) -> tuple[np.ndarray, float]:
        """Return ``(embeddings, encode_seconds)``; ``encode_seconds`` is 0 on a cache hit."""
        f = self.path(model, texts, extra)
        if f.exists():
            return np.load(f), 0.0
        t0 = time.perf_counter()
        emb = np.asarray(encode(list(texts)), dtype=np.float32)
        dt = time.perf_counter() - t0
        np.save(f, emb)
        f.with_suffix(".json").write_text(json.dumps(
            {"model": model, "extra": extra, "n": len(texts), "dim": int(emb.shape[-1]),
             "label": label, "encode_seconds": round(dt, 1)}))
        return emb, dt
