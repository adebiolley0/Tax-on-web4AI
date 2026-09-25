"""Score propagation over the citation / structure graph (numpy + scipy.sparse).

Two operators over a first-stage document score vector ``s`` (min-max normalised, seeds =
top-k of the first stage, everything else 0):

* neighbour expansion  s'(d) = s(d) + α · Σ_h decay^(h-1) · (P^h s)(d), h = 1..hops,
  P = Σ_types w_t · norm(A_t); ``norm`` ∈ {sum, mean (D⁻¹A), sym (D⁻½AD⁻½)};
  group hyperedges (same heading / found_via / path / edition) contribute the *average*
  score of the other members of the group.
* personalized PageRank restarted from the top-k: p = (1-β) r + β · P_col p, 30 iterations,
  s' = s + α · p / max(p).

Edges are symmetrised (a citation links both documents) and binary by default.
"""
from __future__ import annotations

import collections

import numpy as np
import scipy.sparse as sp


class PropGraph:
    def __init__(self, doc_ids: list[str], edges: list, groups: dict[str, list[list[str]]], binary: bool = True,
                 max_group: int | None = None):
        self.n = len(doc_ids)
        idx = {d: i for i, d in enumerate(doc_ids)}
        rows: dict[str, list] = collections.defaultdict(lambda: ([], [], []))
        dropped = 0
        for s, t, ty, w in edges:
            if s in idx and t in idx:
                r, c, v = rows[ty]
                r.append(idx[s]); c.append(idx[t]); v.append(1.0 if binary else float(w))
            else:
                dropped += 1
        self.dropped_edges = dropped
        self.adj: dict[str, sp.csr_matrix] = {}
        for ty, (r, c, v) in rows.items():
            A = sp.coo_matrix((v, (r, c)), shape=(self.n, self.n)).tocsr()
            A = A + A.T
            if binary:
                A.data[:] = 1.0
            A.setdiag(0); A.eliminate_zeros()
            self.adj[ty] = A
        # groups → incidence matrices (docs × groups), weight 1/(size-1): contribution = mean of the other members
        self.grp: dict[str, sp.csr_matrix] = {}
        for name, gs in groups.items():
            r, c, v = [], [], []
            gi = 0
            for g in gs:
                members = [idx[d] for d in g if d in idx]
                if len(members) < 2 or (max_group and len(members) > max_group):
                    continue
                for m in members:
                    r.append(m); c.append(gi); v.append(1.0 / (len(members) - 1))
                gi += 1
            self.grp[name] = sp.coo_matrix((v, (r, c)), shape=(self.n, max(gi, 1))).tocsr()
        self._norm_cache: dict[tuple[str, str], sp.csr_matrix] = {}

    @property
    def types(self) -> list[str]:
        return list(self.adj) + list(self.grp)

    def degree(self, ty: str) -> np.ndarray:
        if ty in self.adj:
            return np.asarray(self.adj[ty].sum(axis=1)).ravel()
        B = self.grp[ty]
        return np.asarray((B > 0).sum(axis=1)).ravel().astype(float)

    def _normed(self, ty: str, norm: str) -> sp.csr_matrix:
        key = (ty, norm)
        if key not in self._norm_cache:
            A = self.adj[ty]
            d = np.asarray(A.sum(axis=1)).ravel()
            if norm == "sum":
                M = A
            elif norm == "mean":
                inv = np.where(d > 0, 1.0 / np.maximum(d, 1e-9), 0.0)
                M = sp.diags(inv) @ A
            elif norm == "sym":
                inv = np.where(d > 0, 1.0 / np.sqrt(np.maximum(d, 1e-9)), 0.0)
                M = sp.diags(inv) @ A @ sp.diags(inv)
            else:
                raise ValueError(norm)
            self._norm_cache[key] = M.tocsr()
        return self._norm_cache[key]

    def apply(self, X: np.ndarray, weights: dict[str, float], norm: str = "mean") -> np.ndarray:
        """One propagation step on X of shape (n, nq)."""
        Y = np.zeros_like(X)
        for ty, w in weights.items():
            if w == 0:
                continue
            if ty in self.adj:
                Y += w * (self._normed(ty, norm) @ X)
            elif ty in self.grp:
                B = self.grp[ty]
                tot = B.T @ X                                    # (n_groups, nq): weighted sums of member scores
                own = np.asarray(B.sum(axis=1)).ravel()[:, None] * X   # a doc's own contribution to its group
                Y += w * ((B @ tot) - own)                      # mean of the *other* members
        return Y

    def expand(self, S: np.ndarray, weights: dict[str, float], norm: str, hops: int, decay: float = 0.5) -> np.ndarray:
        """S: (nq, n) seed scores → propagated scores (nq, n)."""
        X = S.T.copy()
        out = np.zeros_like(X)
        for h in range(hops):
            X = self.apply(X, weights, norm)
            out += (decay ** h) * X
        return out.T

    def ppr(self, S: np.ndarray, weights: dict[str, float], beta: float = 0.85, iters: int = 30) -> np.ndarray:
        """Personalized PageRank from restart distribution S (nq, n); column-stochastic spreading."""
        ones = np.ones((self.n, 1))
        d = self.apply(ones, weights, "sum").ravel()
        d_safe = np.where(d > 0, d, 1.0)
        R = S.T / np.maximum(S.sum(axis=1), 1e-9)[None, :]
        P = R.copy()
        for _ in range(iters):
            P = (1 - beta) * R + beta * self.apply(P / d_safe[:, None], weights, "sum")
        mx = P.max(axis=0, keepdims=True)
        return (P / np.maximum(mx, 1e-12)).T


def top_k_seeds(S_norm: np.ndarray, k: int) -> np.ndarray:
    """Keep only the top-k scores per row (others → 0)."""
    if k >= S_norm.shape[1]:
        return S_norm
    thr = -np.partition(-S_norm, k - 1, axis=1)[:, k - 1: k]
    return np.where(S_norm >= thr, S_norm, 0.0)
