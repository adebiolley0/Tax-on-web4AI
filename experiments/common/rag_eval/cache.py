"""On-disk cache for embeddings so each (model, chunking) pair is encoded once."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Callable, Sequence

import numpy as np

from rag_eval.corpora import DATA_DIR

CACHE_DIR = DATA_DIR / "emb_cache"


def _key(model: str, texts: Sequence[str], extra: str = "") -> str:
    h = hashlib.sha256()
    h.update(model.encode()); h.update(b"\0"); h.update(extra.encode()); h.update(b"\0")
    h.update(str(len(texts)).encode())
    for t in texts:
        h.update(hashlib.sha1(t.encode("utf-8")).digest())
    return h.hexdigest()[:24]


class EmbeddingCache:
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.dir = Path(cache_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def get_or_compute(
        self,
        model: str,
        texts: Sequence[str],
        encode: Callable[[Sequence[str]], np.ndarray],
        extra: str = "",
        label: str = "",
    ) -> tuple[np.ndarray, float]:
        """Return (embeddings, encode_seconds). encode_seconds is 0 on cache hit."""
        key = _key(model, texts, extra)
        f = self.dir / f"{key}.npy"
        if f.exists():
            return np.load(f), 0.0
        t0 = time.perf_counter()
        emb = np.asarray(encode(list(texts)), dtype=np.float32)
        dt = time.perf_counter() - t0
        np.save(f, emb)
        (self.dir / f"{key}.json").write_text(json.dumps(
            {"model": model, "extra": extra, "n": len(texts), "dim": int(emb.shape[-1]),
             "label": label, "encode_seconds": round(dt, 1)}))
        return emb, dt
