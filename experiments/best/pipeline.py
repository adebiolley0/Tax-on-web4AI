#!/usr/bin/env python3
"""The best measured retrieval pipelines as callables (experiments/EXPERIMENTS.md §4, round-3 amendments).

* :func:`retrieve_b` – statute articles (corpus B, 5,853 articles): z-score convex fusion with fixed equal weights of
  reception-BM25F, French ColBERT and e5-small, then the length gate: ≤ 25 words → mMARCO-MiniLM over the best 3
  chunks of the top-30 articles interpolated at β 0.8 with the fused score; longer questions → the un-reranked
  reception + e5 fusion. Human all 0.628 (bar 0.522), mined 0.534 (exp 22).
* :func:`retrieve_c` – Fisconet+ documents (corpus C, 21,259): exp-13 BM25F over fixed1200_title chunks → top-20
  chunks → bge-reranker-v2-m3 (score only) → documents by best chunk, lexical tail. Human val 0.688 / all 0.733 (exp 17).
* :func:`retrieve_a` – the 91-document validation corpus: whole-document BM25 (exp 01, val 0.736).

Every function returns a :class:`Result` with ranked document ids, scores and the passages that produced them.
Models are loaded lazily and only when a cache miss needs them (``cache_only=True`` forbids that: evaluation mode).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from config import (A_TOP, B_TOP, B_WEIGHTS_LONG, B_WEIGHTS_SHORT, C_BGE_DEPTH, C_LEX_TOP_UNITS, C_TOP, CHUNK_CAP, INDEX,
                    MMARCO_BETA, MMARCO_DEPTH)
from corpus import Universe, lexical_units_b, universe_b, universe_c
from fusion import fuse_z, interpolate, top_k, zscore
from gate import SHORT, route
from lexical import LexicalIndex


@dataclass
class Passage:
    chunk_idx: int
    chunk_id: str
    text: str
    score: float | None = None          # reranker score when the passage was scored by the cross-encoder


@dataclass
class Hit:
    doc_id: str
    rank: int
    score: float                        # final score (reranker-interpolated for reranked documents, stage-1 fusion otherwise)
    reranked: bool
    title: str = ""
    stage1_score: float | None = None
    passages: list[Passage] = field(default_factory=list)


@dataclass
class Result:
    corpus: str
    question: str
    route: str
    hits: list[Hit]
    timing: dict = field(default_factory=dict)

    @property
    def doc_ids(self) -> list[str]:
        return [h.doc_id for h in self.hits]


def _lex_path(corpus: str):
    p = INDEX / f"{corpus}_lexical.pkl"
    if not p.exists():
        raise FileNotFoundError(f"{p} missing – run build_indexes.py --corpus {corpus}")
    return p


# ── corpus B ─────────────────────────────────────────────────────────────────────────────────────────────────
class RetrieverB:
    def __init__(self, cache_only: bool = False, reception: str = "full", threads: int = 4):
        from colbert import ColbertLeg
        from dense import DenseLeg
        from reception import load_reception
        from rerank import Reranker
        t0 = time.perf_counter()
        self.uni: Universe = universe_b()
        units = lexical_units_b()
        self.reception_variant = reception
        self.lex = LexicalIndex.load(_lex_path("B"), load_reception(exclude_mined=(reception == "nomined")), unit_texts=units.unit_texts)
        self.dense = DenseLeg(self.uni, cache_only, threads)
        self.colbert = ColbertLeg(self.uni, cache_only, threads)
        self.mmarco = Reranker("mmarco", self.uni, cache_only, threads)
        self.title = {d.doc_id: d.title for d in self.uni.docs}
        self.load_s = time.perf_counter() - t0

    def set_reception(self, reception: str) -> None:
        """'full' (production) or 'nomined' (leak-free, for the mined evaluation sets)."""
        from reception import load_reception
        if reception != self.reception_variant:
            self.lex.set_reception(load_reception(exclude_mined=(reception == "nomined")))
            self.reception_variant = reception

    def retrieve(self, question: str, k: int = 10, passages: bool = True) -> Result:
        t = {}
        t0 = time.perf_counter()
        uni, cd, ds = self.uni, self.uni.chunk_doc, self.uni.doc_start
        rec = self.lex.doc_scores(question)
        t["rec_ms"] = round((time.perf_counter() - t0) * 1000, 1); t1 = time.perf_counter()
        e5c = self.dense.chunk_scores(question)
        e5d = self.dense.doc_scores(e5c)
        t["e5_ms"] = round((time.perf_counter() - t1) * 1000, 1); t1 = time.perf_counter()
        r = route(question)
        if r == SHORT:
            cbc = self.colbert.chunk_scores(question)
            fused = fuse_z({"rec": rec, "colbert": self.colbert.doc_scores(cbc), "e5": e5d}, B_WEIGHTS_SHORT)
            t["colbert_ms"] = round((time.perf_counter() - t1) * 1000, 1); t1 = time.perf_counter()
            chunk_evidence = zscore(cbc) + zscore(e5c)          # best chunks of an article by dense evidence
        else:
            fused = fuse_z({"rec": rec, "e5": e5d}, B_WEIGHTS_LONG)
            chunk_evidence = e5c.astype(np.float64)
        order = top_k(fused, B_TOP)
        best_chunks = {}                                        # doc index → [chunk idx] by chunk_evidence
        for d in order:
            a, b = int(ds[d]), int(ds[d + 1])
            loc = np.argsort(-chunk_evidence[a:b], kind="stable")[:CHUNK_CAP]
            best_chunks[int(d)] = [a + int(j) for j in loc]
        hits: list[Hit] = []
        if r == SHORT:
            cands = [int(d) for d in order[:MMARCO_DEPTH]]
            s1 = fused[cands]
            flat = [c for d in cands for c in best_chunks[d]]
            sc = self.mmarco.score(question, flat)
            per_doc, pos = {}, 0
            for d in cands:
                n = len(best_chunks[d])
                per_doc[d] = sc[pos:pos + n]; pos += n
            rr = np.array([per_doc[d].max() for d in cands])
            final = interpolate(rr, s1, MMARCO_BETA)
            for j in np.argsort(-final, kind="stable"):
                d = cands[j]
                hits.append(Hit(uni.doc_ids[d], 0, float(final[j]), True, self.title[uni.doc_ids[d]], float(fused[d]),
                                [Passage(c, uni.chunks[c].chunk_id, uni.chunks[c].text, float(s)) for c, s in
                                 sorted(zip(best_chunks[d], per_doc[d]), key=lambda cs: -cs[1])] if passages else []))
            t["mmarco_ms"] = round((time.perf_counter() - t1) * 1000, 1)
            tail = [int(d) for d in order[MMARCO_DEPTH:]]
            route_name = "short: rec+colbert+e5 → mMARCO@30 β0.8"
        else:
            tail = [int(d) for d in order]
            route_name = "long: rec+e5 un-reranked"
        for d in tail:
            c = best_chunks[d][0]
            hits.append(Hit(uni.doc_ids[d], 0, float(fused[d]) - (1e3 if r == SHORT else 0.0), False, self.title[uni.doc_ids[d]], float(fused[d]),
                            [Passage(c, uni.chunks[c].chunk_id, uni.chunks[c].text)] if passages else []))
        for i, h in enumerate(hits):
            h.rank = i + 1
        t["total_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return Result("B", question, route_name, hits[:k], t)

    def rank(self, question: str, top: int = B_TOP) -> list[str]:
        return self.retrieve(question, top, passages=False).doc_ids


# ── corpus C ─────────────────────────────────────────────────────────────────────────────────────────────────
class RetrieverC:
    def __init__(self, cache_only: bool = False, threads: int = 4):
        from rerank import Reranker
        t0 = time.perf_counter()
        self.uni: Universe = universe_c()
        self.lex = LexicalIndex.load(_lex_path("C"), unit_texts=self.uni.texts)
        assert self.lex.store.n == self.uni.n_chunks, "lexical units must be the universe chunks (unit index == chunk index)"
        self.bge = Reranker("bge", self.uni, cache_only, threads)
        self.title = {d.doc_id: d.title for d in self.uni.docs}
        self.load_s = time.perf_counter() - t0

    def retrieve(self, question: str, k: int = 10, passages: bool = True) -> Result:
        t = {}
        t0 = time.perf_counter()
        uni = self.uni
        us = self.lex.unit_scores(question)
        units, lex = self.lex.top_units(us, C_LEX_TOP_UNITS)
        tail = self.lex.doc_ranking(us, C_TOP)
        t["lexical_ms"] = round((time.perf_counter() - t0) * 1000, 1); t1 = time.perf_counter()
        cand = [int(u) for u in units[:C_BGE_DEPTH]]
        rr = self.bge.score(question, cand) if cand else np.zeros(0)
        t["bge_ms"] = round((time.perf_counter() - t1) * 1000, 1)
        hits: list[Hit] = []
        seen: set[str] = set()
        by_doc: dict[str, list[tuple[int, float]]] = {}
        for c, s in zip(cand, rr):
            by_doc.setdefault(uni.doc_ids[int(uni.chunk_doc[c])], []).append((c, float(s)))
        for j in np.argsort(-rr, kind="stable"):
            d = uni.doc_ids[int(uni.chunk_doc[cand[j]])]
            if d in seen:
                continue
            seen.add(d)
            ps = sorted(by_doc[d], key=lambda cs: -cs[1])
            hits.append(Hit(d, 0, float(rr[j]), True, self.title[d], float(us[cand[j]]),
                            [Passage(c, uni.chunks[c].chunk_id, uni.chunks[c].text, s) for c, s in ps] if passages else []))
        first_unit = {}
        for u in units:
            first_unit.setdefault(uni.doc_ids[int(uni.chunk_doc[u])], int(u))
        floor = float(rr.min()) if len(rr) else 0.0
        for d in tail:
            if d in seen:
                continue
            seen.add(d)
            u = first_unit.get(d)
            hits.append(Hit(d, 0, floor - 1e3 + (float(us[u]) if u is not None else 0.0) * 1e-3, False, self.title[d], float(us[u]) if u is not None else None,
                            [Passage(u, uni.chunks[u].chunk_id, uni.chunks[u].text)] if (passages and u is not None) else []))
        for i, h in enumerate(hits):
            h.rank = i + 1
        t["total_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return Result("C", question, "lexical → bge@20", hits[:k], t)

    def rank(self, question: str, top: int = C_TOP) -> list[str]:
        return self.retrieve(question, top, passages=False).doc_ids


# ── corpus A ─────────────────────────────────────────────────────────────────────────────────────────────────
class RetrieverA:
    def __init__(self, passage_chars: int = 2000):
        from corpus import lexical_units_a
        units = lexical_units_a()
        self.lex = LexicalIndex.load(_lex_path("A"), unit_texts=units.unit_texts)
        self.passage_chars = passage_chars
        self.title = {}
        from corpus import load_a
        self.title = {d.doc_id: d.title for d in load_a()}

    def retrieve(self, question: str, k: int = 10, passages: bool = True) -> Result:
        t0 = time.perf_counter()
        us = self.lex.unit_scores(question)
        ranked = self.lex.doc_ranking(us, A_TOP)
        di = {d: i for i, d in enumerate(self.lex.doc_ids)}
        hits = [Hit(d, i + 1, float(us[di[d]]), False, self.title.get(d, ""), float(us[di[d]]),
                    [Passage(di[d], f"{d}#0", self.lex.unit_texts[di[d]][:self.passage_chars])] if passages else []) for i, d in enumerate(ranked)]
        return Result("A", question, "whole-document BM25", hits[:k], {"total_ms": round((time.perf_counter() - t0) * 1000, 1)})

    def rank(self, question: str, top: int = A_TOP) -> list[str]:
        return self.retrieve(question, top, passages=False).doc_ids


# ── module-level convenience (one lazily built retriever per corpus) ────────────────────────────────────────
_R: dict[str, object] = {}


def retrieve_b(question: str, k: int = 10, **kw) -> Result:
    if "B" not in _R:
        _R["B"] = RetrieverB(**kw)
    return _R["B"].retrieve(question, k)


def retrieve_c(question: str, k: int = 10, **kw) -> Result:
    if "C" not in _R:
        _R["C"] = RetrieverC(**kw)
    return _R["C"].retrieve(question, k)


def retrieve_a(question: str, k: int = 10, **kw) -> Result:
    if "A" not in _R:
        _R["A"] = RetrieverA(**kw)
    return _R["A"].retrieve(question, k)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="ask one question to one corpus")
    ap.add_argument("corpus", choices=["A", "B", "C"])
    ap.add_argument("question")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--cache-only", action="store_true")
    a = ap.parse_args()
    kw = {"cache_only": a.cache_only} if a.corpus != "A" else {}
    res = {"A": retrieve_a, "B": retrieve_b, "C": retrieve_c}[a.corpus](a.question, a.k, **kw)
    print(f"[{res.corpus}] {res.route} | {res.timing}")
    for h in res.hits:
        print(f"{h.rank:3d} {h.score:8.3f} {'R' if h.reranked else ' '} {h.doc_id}  {h.title[:70]}")
        for p in h.passages[:1]:
            print("      " + p.text[:200].replace("\n", " ") + ("…" if len(p.text) > 200 else ""))
