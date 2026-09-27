"""Dense leg: multilingual-e5-small over the chunk universe (exp 02 / 09 / 22).

* chunk vectors come from the shared ``experiments/data/emb_cache`` (same key as exp 02 / 09, so nothing is
  re-encoded; ``build`` encodes them if the key is missing: ~10 min for B, hours for C on 4 CPU cores);
* query vectors are cached per question text in ``cache/q_e5.npz`` (keyed by :func:`config.qkey`), so evaluation of
  the stored question sets needs no torch process; unseen questions are encoded on the fly (~50 ms).
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np

from rag_eval.cache import EmbeddingCache, _key

from config import CACHE, E5_D_PREFIX, E5_ID, E5_MAX_SEQ, E5_Q_PREFIX, EMB_EXTRA, qkey
from corpus import Universe
from fusion import doc_max


class E5Encoder:
    """sentence-transformers e5-small, CPU, normalised vectors (exp-02 `Encoder`)."""

    def __init__(self, threads: int = 4):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(threads)
        t0 = time.perf_counter()
        self.m = SentenceTransformer(E5_ID, device="cpu")
        self.m.max_seq_length = E5_MAX_SEQ
        self.load_s = time.perf_counter() - t0

    def _enc(self, texts, prefix: str) -> np.ndarray:
        e = self.m.encode([prefix + t for t in texts], batch_size=16, normalize_embeddings=True, show_progress_bar=False)
        e = np.asarray(e, dtype=np.float32)
        n = np.linalg.norm(e, axis=1, keepdims=True); n[n == 0] = 1
        return e / n

    def queries(self, texts) -> np.ndarray:
        return self._enc(texts, E5_Q_PREFIX)

    def passages(self, texts) -> np.ndarray:
        return self._enc(texts, E5_D_PREFIX)


class QueryVectorCache:
    """question text → e5 query vector (cache/q_e5.npz)."""

    def __init__(self, path: Path = CACHE / "q_e5.npz"):
        self.path = Path(path)
        self.vecs: dict[str, np.ndarray] = {}
        if self.path.exists():
            z = np.load(self.path, allow_pickle=False)
            self.vecs = {str(k): v for k, v in zip(z["keys"], z["vecs"])}
        self._dirty = False

    def get(self, question: str) -> np.ndarray | None:
        return self.vecs.get(qkey(question))

    def put(self, question: str, vec: np.ndarray) -> None:
        self.vecs[qkey(question)] = np.asarray(vec, dtype=np.float32)
        self._dirty = True

    def save(self) -> None:
        if not self._dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        keys = sorted(self.vecs)
        np.savez(self.path, keys=np.array(keys, dtype="U40"), vecs=np.stack([self.vecs[k] for k in keys]))
        self._dirty = False


def chunk_embeddings_path(uni: Universe) -> Path:
    return EmbeddingCache().dir / (_key(E5_ID, uni.texts, EMB_EXTRA[uni.corpus]) + ".npy")


def chunk_embeddings(uni: Universe, build: bool = False, encoder: "E5Encoder | None" = None) -> np.ndarray:
    """(n_chunks, 384) float32 from the shared cache; with ``build`` the missing matrix is encoded (torch lock!)."""
    f = chunk_embeddings_path(uni)
    if f.exists():
        return np.load(f)
    if not build:
        raise FileNotFoundError(f"{f} (e5 chunk embeddings for corpus {uni.corpus}) missing – run build_indexes.py --corpus {uni.corpus} --encode")
    enc = encoder or E5Encoder()
    cache = EmbeddingCache()
    emb, dt = cache.get_or_compute(E5_ID, uni.texts, enc.passages, extra=EMB_EXTRA[uni.corpus], label=f"{uni.corpus}/{EMB_EXTRA[uni.corpus]}")
    print(f"  e5 chunk embeddings for {uni.corpus}: {emb.shape} in {dt:.0f}s", flush=True)
    return emb


class DenseLeg:
    def __init__(self, uni: Universe, cache_only: bool = False, threads: int = 4):
        self.uni = uni
        self.emb = chunk_embeddings(uni)
        self.qcache = QueryVectorCache()
        self.cache_only = cache_only
        self.threads = threads
        self._enc: E5Encoder | None = None

    def query_vector(self, question: str) -> np.ndarray:
        v = self.qcache.get(question)
        if v is None:
            if self.cache_only:
                raise KeyError(f"e5 query vector not cached for: {question[:60]}…")
            if self._enc is None:
                self._enc = E5Encoder(self.threads)
            v = self._enc.queries([question])[0]
            self.qcache.put(question, v)
            self.qcache.save()
        return v

    def chunk_scores(self, question: str) -> np.ndarray:
        return (self.emb @ self.query_vector(question)).astype(np.float32)

    def doc_scores(self, chunk_scores: np.ndarray) -> np.ndarray:
        return doc_max(chunk_scores, self.uni.chunk_doc, self.uni.n_docs, fill=-1.0)
