"""Feature table per (question, candidate document) for learning-to-rank.

Candidates = documents of the wide candidate chunk set (top-50 chunks of every first-stage
leg). Reranker scores come from the cached npz files written by score_rerankers.py; a document
outside the bge candidate set (top-30 per leg) gets the question's minimum bge score − 1 and a
missing flag. Labels: expected 1.0, secondary 0.5, other 0.0.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass

import numpy as np

from common14 import (CACHE, TOP_CAND, TOP_CAND_WIDE, Stage1, convex_scores, detect_region, doc_region_c,
                      load_corpus_and_chunks, query_year, ranks_of, region_of_code, rrf_scores, tokenize, minmax)

_REV = re.compile(r"_revenus_(20\d\d)")


def doc_meta(corpus: str) -> list[dict]:
    """Per-document metadata (title, type, region, year, path), cached as json."""
    f = CACHE / f"{corpus}_docmeta.json"
    if f.exists():
        return json.loads(f.read_text())
    docs, _, _, _ = load_corpus_and_chunks(corpus)
    out = []
    for d in docs:
        m = d.meta
        if corpus == "A":
            typ, region = (m.get("document_type") or "?"), None
            date = m.get("document_date")
        elif corpus == "B":
            typ = re.sub(r"_(wal|bxl|vla)$", "", m.get("code") or "?")
            region = region_of_code(m.get("code") or "")
            date = None
        else:
            typ = m.get("folder") or "?"
            region = doc_region_c(d.doc_id, d.title, m.get("path") or [])
            date = m.get("document_date")
        year = None
        if date and re.match(r"^\d{4}", str(date)):
            year = int(str(date)[:4])
        mm = _REV.search(d.doc_id)
        out.append({"title": d.title, "type": typ, "region": region, "year": year,
                    "rev_year": int(mm.group(1)) if mm else None})
    f.write_text(json.dumps(out, ensure_ascii=False))
    return out


def load_rerank(corpus: str, reranker: str) -> dict[int, dict[int, float]] | None:
    f = CACHE / f"{corpus}_rerank_{reranker}.npz"
    if not f.exists():
        return None
    z = np.load(f)
    out: dict[int, dict[int, float]] = {}
    for q, c, s in zip(z["q_idx"].tolist(), z["chunk_idx"].tolist(), z["score"].tolist()):
        out.setdefault(q, {})[c] = s
    return out


@dataclass
class Table:
    corpus: str
    qids: list[str]
    q_index: dict[str, int]
    rows_q: np.ndarray            # (n,) question index per row
    rows_d: np.ndarray            # (n,) document index per row
    X: np.ndarray                 # (n, nfeat)
    y: np.ndarray                 # (n,) 1 / 0.5 / 0
    names: list[str]
    tail: list[list[int]]         # per question: document order (convex0.5) used after the candidates

    def rows_of(self, qi: int) -> np.ndarray:
        return np.where(self.rows_q == qi)[0]

    def ranking(self, st: Stage1, qi: int, scores: np.ndarray, top: int = 50) -> list[str]:
        """Candidates ordered by ``scores`` (one per row of question qi), then the tail."""
        rows = self.rows_of(qi)
        order = rows[np.argsort(-scores, kind="stable")]
        out = [int(self.rows_d[r]) for r in order]
        seen = set(out)
        for d in self.tail[qi]:
            if len(out) >= top:
                break
            if d not in seen:
                out.append(d); seen.add(d)
        return [st.doc_ids[d] for d in out[:top]]


def build_table(corpus: str, st: Stage1, questions, rerankers=("mmarco-minilm", "bge-reranker-v2-m3"),
                wide: int = TOP_CAND_WIDE) -> Table:
    meta = doc_meta(corpus)
    rr = {rk: load_rerank(corpus, rk) for rk in rerankers}
    rr = {k: v for k, v in rr.items() if v is not None}
    legs = list(st.legs)                                  # e5, [bgem3|potion], bm25
    types = sorted({m["type"] for m in meta})
    type_counts = {t: sum(1 for m in meta if m["type"] == t) for t in types}
    types = [t for t in types if type_counts[t] >= 5] if corpus != "A" else types
    title_toks = [set(tokenize(m["title"])) for m in meta]
    n_chunks = np.diff(st.doc_start)

    names: list[str] = []
    for lg in legs:
        names += [f"{lg}_max", f"{lg}_norm", f"{lg}_logrank", f"{lg}_top30"]
    names += ["bm25doc_score", "bm25doc_norm", "bm25doc_logrank", "rrf60", "rrf60_logrank", "convex05", "convex05_logrank",
              "n_legs_top30"]
    for rk in rr:
        short = "mmarco" if rk.startswith("mmarco") else "bge"
        names += [f"{short}_max", f"{short}_norm", f"{short}_logrank", f"{short}_missing"]
    names += ["log_doc_len", "log_n_chunks", "title_overlap", "title_overlap_n", "best_pos_e5", "best_pos_bm25",
              "q_has_region", "region_match", "region_mismatch", "is_yearly_edition", "year_match", "year_mismatch",
              "doc_year", "has_doc_year"]
    names += [f"type={t}" for t in types]

    rows_q, rows_d, X, y = [], [], [], []
    tails: list[list[int]] = []
    for qi, q in enumerate(questions):
        cand = st.candidates(qi, wide)
        cand_docs = sorted({int(st.chunk_doc[j]) for j in cand})
        cd = np.array(cand_docs)
        # per-leg doc-level scores / ranks over the FULL corpus
        leg_doc = {lg: st.doc_max(st.legs[lg][qi].astype(np.float64)) for lg in legs}
        leg_norm = {lg: st.doc_max(minmax(st.legs[lg][qi].astype(np.float64))) for lg in legs}
        leg_rank = {lg: ranks_of(leg_doc[lg]) for lg in legs}
        bmd = st.bm25_doc[qi].astype(np.float64)
        bmd_rank = ranks_of(bmd)
        bmd_norm = minmax(bmd)
        rrf_c = rrf_scores([st.legs["e5"][qi], st.legs["bm25"][qi]], 60.0)
        rrf_d = st.doc_max(rrf_c); rrf_rank = ranks_of(rrf_d)
        cvx_c = convex_scores(st.legs["e5"][qi], st.legs["bm25"][qi], 0.5)
        cvx_d = st.doc_max(cvx_c); cvx_rank = ranks_of(cvx_d)
        tails.append(np.argsort(-cvx_d, kind="stable")[:200].tolist())
        # reranker doc-level max over scored chunks
        rr_doc: dict[str, dict[int, float]] = {}
        for rk, table in rr.items():
            qsc = table.get(qi, {})
            dm: dict[int, float] = {}
            for j, s in qsc.items():
                d = int(st.chunk_doc[j])
                if s > dm.get(d, -1e9):
                    dm[d] = s
            rr_doc[rk] = dm
        q_region = detect_region(q.question)
        q_year = query_year(q.question)
        qtoks = set(tokenize(q.question))
        exp, sec = set(q.expected), set(q.secondary)
        for d in cand_docs:
            f: list[float] = []
            ntop = 0
            for lg in legs:
                r = leg_rank[lg][d]
                f += [leg_doc[lg][d], leg_norm[lg][d], math.log1p(r), float(r <= 30)]
                ntop += int(r <= 30)
            f += [bmd[d], bmd_norm[d], math.log1p(bmd_rank[d]), rrf_d[d], math.log1p(rrf_rank[d]), cvx_d[d],
                  math.log1p(cvx_rank[d]), float(ntop + int(bmd_rank[d] <= 30))]
            for rk, dm in rr_doc.items():
                vals = np.array([dm.get(x, np.nan) for x in cand_docs])
                present = ~np.isnan(vals)
                if present.any():
                    lo, hi = np.nanmin(vals), np.nanmax(vals)
                    fill = lo - 1.0
                    v = dm.get(d, fill)
                    norm = (v - lo) / (hi - lo) if hi > lo else 0.0
                    norm = max(norm, -0.1) if d in dm else -0.1
                    rank = 1 + int(np.sum(vals[present] > v)) if d in dm else int(present.sum()) + 1
                    f += [v, norm, math.log1p(rank), float(d not in dm)]
                else:
                    f += [-10.0, -0.1, math.log1p(len(cand_docs)), 1.0]
            a, b = st.doc_start[d], st.doc_start[d + 1]
            nch = max(1, b - a)
            best_e5 = int(np.argmax(st.legs["e5"][qi][a:b])) if b > a else 0
            best_bm = int(np.argmax(st.legs["bm25"][qi][a:b])) if b > a else 0
            m = meta[d]
            ov = len(qtoks & title_toks[d])
            reg = m["region"]
            f += [math.log1p(st.doc_len[d]), math.log1p(nch), ov / max(1, len(qtoks)), float(ov),
                  best_e5 / max(1, nch - 1), best_bm / max(1, nch - 1),
                  float(q_region is not None),
                  float(q_region is not None and reg is not None and q_region in reg.split(",")),
                  float(q_region is not None and reg is not None and reg != "fed" and q_region not in reg.split(",")),
                  float(m["rev_year"] is not None),
                  float(q_year is not None and m["rev_year"] == q_year),
                  float(q_year is not None and m["rev_year"] is not None and m["rev_year"] != q_year),
                  ((m["year"] or 2000) - 2000) / 30.0, float(m["year"] is not None)]
            f += [float(m["type"] == t) for t in types]
            did = st.doc_ids[d]
            rows_q.append(qi); rows_d.append(d); X.append(f)
            y.append(1.0 if did in exp else (0.5 if did in sec else 0.0))
    X = np.asarray(X, dtype=np.float64)
    assert X.shape[1] == len(names), (X.shape, len(names))
    return Table(corpus, [q.qid for q in questions], {q.qid: i for i, q in enumerate(questions)},
                 np.asarray(rows_q), np.asarray(rows_d), X, np.asarray(y), names, tails)


FEATURE_SETS = {
    # everything available
    "all": None,
    # no cross-encoder: what a pure first-stage LTR can do
    "cheap": lambda n: not (n.startswith("mmarco") or n.startswith("bge")),
    # 6 hand-picked features: normalised legs + reranker(s)
    "minimal": lambda n: n in ("e5_norm", "bm25_norm", "bm25doc_norm", "rrf60", "mmarco_norm", "bge_norm"),
    # minimal + metadata
    "minimal+meta": lambda n: n in ("e5_norm", "bm25_norm", "bm25doc_norm", "rrf60", "mmarco_norm", "bge_norm",
                                    "title_overlap", "region_match", "region_mismatch", "year_match", "year_mismatch",
                                    "is_yearly_edition", "log_doc_len"),
}


def select_features(tab: Table, fset: str) -> tuple[np.ndarray, list[str]]:
    pred = FEATURE_SETS[fset]
    keep = [i for i, n in enumerate(tab.names) if pred is None or pred(n)]
    X = tab.X[:, keep]
    names = [tab.names[i] for i in keep]
    # drop constant columns (e.g. region features on A)
    nz = [i for i in range(X.shape[1]) if X[:, i].std() > 0]
    return X[:, nz], [names[i] for i in nz]
