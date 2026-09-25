"""Shared helpers for experiment 11: paths, first-stage score matrices, doc-level aggregation.

First-stage scores are computed once by ``first_stage.py`` and cached as chunk-level
matrices (n_questions x n_chunks) in ``cache/``; every graph experiment then works on
doc-level vectors derived from them, exactly as experiments 03 / 09 did (doc score =
max over its chunks; RRF / convex fusion at chunk level, then max).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from rag_eval.corpora import DATA_DIR

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
CACHE.mkdir(exist_ok=True)
EXP = "11_graph_retrieval"

for _sub in ("02_dense_sweep", "03_hybrid_rerank", "08_corpus_b_cleanup", "09_corpus_c"):
    sys.path.insert(0, str((DATA_DIR.parent / _sub).resolve()))


def minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


def rrf_chunks(rank_lists: list[np.ndarray], k: int, n: int) -> np.ndarray:
    score = np.zeros(n, dtype=np.float32)
    for ranks in rank_lists:
        score[ranks] += 1.0 / (k + np.arange(1, len(ranks) + 1))
    return score


class FirstStage:
    """Cached chunk-level score matrices + chunk→doc mapping for one corpus tag."""

    def __init__(self, tag: str):
        self.tag = tag
        meta = json.loads((CACHE / f"{tag}_meta.json").read_text())
        self.doc_ids: list[str] = meta["doc_ids"]
        self.qids: list[str] = meta["qids"]
        self.chunk_doc = np.load(CACHE / f"{tag}_chunk_doc.npy")          # (n_chunks,) int32 doc index
        self.n_docs = len(self.doc_ids)
        self.n_chunks = len(self.chunk_doc)
        # chunks are contiguous per doc → reduceat boundaries
        starts = np.flatnonzero(np.r_[True, self.chunk_doc[1:] != self.chunk_doc[:-1]])
        assert len(starts) == self.n_docs, "chunks must be contiguous per doc"
        self._starts = starts
        self.chunk: dict[str, np.ndarray] = {}
        for name in ("bm25", "dense"):
            f = CACHE / f"{tag}_{name}_chunks.npy"
            if f.exists():
                self.chunk[name] = np.load(f)
        self.rrf_depth = meta.get("rrf_depth", 200)
        self.bm25_note = meta.get("bm25", "")

    def doc_max(self, chunk_scores: np.ndarray) -> np.ndarray:
        """(nq, n_chunks) → (nq, n_docs): max over the chunks of each doc."""
        return np.maximum.reduceat(chunk_scores, self._starts, axis=1)

    def doc_scores(self, name: str) -> np.ndarray:
        """Doc-level first-stage matrix for 'bm25' | 'dense' | 'rrf' | 'convexW'."""
        if name in ("bm25", "dense"):
            return self.doc_max(self.chunk[name])
        nq = len(self.qids)
        if name == "rrf":
            out = np.zeros((nq, self.n_chunks), dtype=np.float32)
            for i in range(nq):
                d, b = self.chunk["dense"][i], self.chunk["bm25"][i]
                out[i] = rrf_chunks([np.argsort(-d)[: self.rrf_depth], np.argsort(-b)[: self.rrf_depth]], 60, self.n_chunks)
            return self.doc_max(out)
        if name.startswith("convex"):
            w = float(name[len("convex"):])
            out = np.stack([w * minmax(self.chunk["dense"][i]) + (1 - w) * minmax(self.chunk["bm25"][i]) for i in range(nq)])
            return self.doc_max(out)
        raise ValueError(name)


def ranking_from_scores(scores: np.ndarray, doc_ids: list[str], top: int = 50) -> list[str]:
    order = np.argpartition(-scores, min(top, len(scores) - 1))[:top]
    order = order[np.argsort(-scores[order], kind="stable")]
    return [doc_ids[j] for j in order]
