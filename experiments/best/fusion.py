"""Score fusion: per-query z-score convex combination with fixed weights (exp 22; exp 21 refuted RRF and exp 14
train-tuned weights), min-max interpolation for the reranker stage, and chunk → document aggregation."""
from __future__ import annotations

import numpy as np


def zscore(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    sd = x.std()
    return (x - x.mean()) / sd if sd > 0 else np.zeros_like(x)


def minmax(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


def fuse_z(legs: dict[str, np.ndarray], weights: dict[str, float]) -> np.ndarray:
    """Σ_leg w · z(scores_leg) over one query's document-score vectors; legs with weight 0 are not needed."""
    out = None
    for name, w in weights.items():
        if w <= 0:
            continue
        part = w * zscore(legs[name])
        out = part if out is None else out + part
    return out


def doc_max(chunk_scores: np.ndarray, chunk_doc: np.ndarray, n_docs: int, fill: float) -> np.ndarray:
    """Document score = max over its chunks (`fill` for documents without a chunk)."""
    out = np.full(n_docs, fill, dtype=np.float64)
    np.maximum.at(out, chunk_doc, np.asarray(chunk_scores, dtype=np.float64))
    return out


def top_k(scores: np.ndarray, k: int) -> np.ndarray:
    """Indices of the k largest scores, descending, stable on ties."""
    k = min(k, len(scores))
    cand = np.argpartition(-scores, k - 1)[:k]
    return cand[np.argsort(-scores[cand], kind="stable")]


def interpolate(reranker: np.ndarray, stage1: np.ndarray, beta: float) -> np.ndarray:
    """β · minmax(reranker) + (1 − β) · minmax(stage 1); β = 1 → reranker score only."""
    r = np.asarray(reranker, dtype=np.float64)
    return r if beta >= 1 else beta * minmax(r) + (1 - beta) * minmax(stage1)
