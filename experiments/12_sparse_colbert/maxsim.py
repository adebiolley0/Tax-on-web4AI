"""Exact in-memory late-interaction scoring (ColBERT MaxSim) with torch, plus helpers to
turn a full score matrix into "rerank the top-k candidates of another retriever" runs."""
from __future__ import annotations

import time

import numpy as np
import torch


def pad_stack(embs: list[np.ndarray], dtype=torch.float32) -> tuple[torch.Tensor, torch.Tensor]:
    """List of (L_i, d) arrays -> (N, Lmax, d) tensor + (N, Lmax) bool mask."""
    n, d = len(embs), embs[0].shape[1]
    lmax = max(e.shape[0] for e in embs)
    out = torch.zeros((n, lmax, d), dtype=dtype)
    mask = torch.zeros((n, lmax), dtype=torch.bool)
    for i, e in enumerate(embs):
        out[i, : e.shape[0]] = torch.as_tensor(e, dtype=dtype)
        mask[i, : e.shape[0]] = True
    return out, mask


def maxsim_matrix(q_embs: list[np.ndarray], d_embs: list[np.ndarray], doc_batch: int = 512,
                  normalize_by_qlen: bool = False) -> tuple[np.ndarray, float]:
    """(nq, n_docs) MaxSim scores: sum over query tokens of max over doc tokens of q·d.
    Padded doc tokens are masked to -inf before the max. Query tokens that are all-zero
    (padding) contribute 0."""
    t0 = time.perf_counter()
    Q, qmask = pad_stack(q_embs)
    D, dmask = pad_stack(d_embs)
    nq, n = Q.shape[0], D.shape[0]
    out = torch.zeros((nq, n), dtype=torch.float32)
    with torch.inference_mode():
        for s in range(0, n, doc_batch):
            Db, mb = D[s:s + doc_batch], dmask[s:s + doc_batch]           # (b, Ld, d)
            sim = torch.einsum("qid,bjd->qbij", Q, Db)                     # (nq, b, Lq, Ld)
            sim = sim.masked_fill(~mb[None, :, None, :], -1e4)
            best = sim.amax(dim=-1)                                        # (nq, b, Lq)
            best = best * qmask[:, None, :]
            out[:, s:s + doc_batch] = best.sum(-1)
    if normalize_by_qlen:
        out = out / qmask.sum(-1, keepdim=True).clamp(min=1)
    return out.numpy(), time.perf_counter() - t0


def rerank_scores(full: np.ndarray, base: np.ndarray, top: int) -> np.ndarray:
    """Keep the late-interaction score only on the top-`top` chunks of `base` (per query),
    everything else -inf → equivalent to reranking those candidates with ColBERT."""
    out = np.full_like(full, -1e9, dtype=np.float32)
    for i in range(full.shape[0]):
        cand = np.argsort(-base[i])[:top]
        out[i, cand] = full[i, cand]
    return out
