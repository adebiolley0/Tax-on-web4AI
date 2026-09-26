"""Part 3 – feature table per (question, candidate document) from the sparse stage-1 cache, the exp-13
lexical cache, document metadata (exp-14 `doc_meta`) and, where scored, the reranker caches.

Candidates: documents of the top-50 chunks of every leg and fusion (e5, chunk BM25, convex 0.5, RRF60),
the top-50 whole-document BM25 docs and the top-50 exp-13 lexical docs; documents in the question's
``exclude`` list are dropped. Labels: expected 1, secondary 0.5, other 0. Features follow experiment 14
(`14_ltr_fusion/features.py`); ranks beyond the kept top-K are capped (see common21.doc_ranks_capped).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

import numpy as np

from common21 import CACHE, LexStage1, Stage1, doc_ranks_capped, load_rerank_cache
from common14 import detect_region, tokenize, query_year
from features import doc_meta

CAND_TOP = 50
RERANK_TAGS = {"mmarco-minilm": "mmarco", "bge-reranker-v2-m3": "bge"}


@dataclass
class Table:
    corpus: str
    qids: list[str]
    q_index: dict[str, int]
    rows_q: np.ndarray
    rows_d: np.ndarray
    X: np.ndarray
    y: np.ndarray
    names: list[str]
    tail: list[list[int]]
    rerank_cov: dict[str, np.ndarray]      # reranker → per-question flag: all top-20 convex chunks scored

    def rows_of(self, qi: int) -> np.ndarray:
        return np.where(self.rows_q == qi)[0]

    def ranking(self, st: Stage1, qi: int, scores: np.ndarray, top: int = 60) -> list[str]:
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


def build_table(corpus: str, st: Stage1, questions, lx: LexStage1 | None, rerankers=("mmarco-minilm", "bge-reranker-v2-m3"),
                depth: int = 20) -> Table:
    meta = doc_meta(corpus)
    assert len(meta) == st.ndocs
    types = sorted({m["type"] for m in meta})
    counts = {t: sum(1 for m in meta if m["type"] == t) for t in types}
    types = [t for t in types if counts[t] >= 5]
    title_toks = [set(tokenize(m["title"])) for m in meta]
    rr = {rk: load_rerank_cache(corpus, rk) for rk in rerankers}
    rr = {k: v for k, v in rr.items() if v}
    legs = ("e5", "bm25")

    names: list[str] = []
    for lg in legs:
        names += [f"{lg}_max", f"{lg}_norm", f"{lg}_logrank", f"{lg}_top30"]
    names += ["bm25doc_score", "bm25doc_norm", "bm25doc_logrank", "rrf60", "rrf60_logrank", "convex05", "convex05_logrank",
              "n_legs_top30", "lex13_norm", "lex13_logrank", "lex13_top30"]
    for rk in rr:
        t = RERANK_TAGS[rk]
        names += [f"{t}_max", f"{t}_norm", f"{t}_logrank", f"{t}_missing"]
    names += ["log_doc_len", "log_n_chunks", "title_overlap", "title_overlap_n", "best_pos_e5", "best_pos_bm25",
              "q_has_region", "region_match", "region_mismatch", "is_yearly_edition", "year_match", "year_mismatch",
              "doc_year", "has_doc_year"]
    names += [f"type={t}" for t in types]

    rows_q, rows_d, X, y, tails = [], [], [], [], []
    cov = {rk: np.zeros(len(questions), dtype=bool) for rk in rr}
    for qi, q in enumerate(questions):
        si = st.q_index[q.qid]
        excl = set(q.meta.get("exclude") or [])
        # candidate documents
        cset: set[int] = set()
        for name in ("e5", "bm25", "convex05", "rrf60"):
            idx, _ = st.top(name, si)
            cset.update(int(st.chunk_doc[j]) for j in idx[:CAND_TOP])
        bidx, _ = st.top("bm25doc", si)
        cset.update(int(d) for d in bidx[:CAND_TOP])
        lex_doc = lx.doc_scores(lx.q_index[q.qid]) if lx is not None else {}
        lex_rank = {d: r + 1 for r, d in enumerate(sorted(lex_doc, key=lambda d: -lex_doc[d]))}
        cset.update(list(lex_rank)[:CAND_TOP] if lx is not None else [])
        cand_docs = sorted(d for d in cset if st.doc_ids[d] not in excl)
        # full-corpus doc-level leg scores / ranks (densified from the top-K)
        leg_doc, leg_norm, leg_rank = {}, {}, {}
        for lg in legs:
            lo, hi = st.minmax_of(lg, si)
            full = st.full(lg, si)
            leg_doc[lg] = st.doc_max(full)
            leg_norm[lg] = (leg_doc[lg] - lo) / (hi - lo) if hi > lo else np.zeros(st.ndocs)
            leg_rank[lg] = doc_ranks_capped(leg_doc[lg], lo)
        blo, bhi = st.minmax_of("bm25doc", si)
        bmd = np.full(st.ndocs, blo); bmd[bidx] = st.top("bm25doc", si)[1]
        bmd_norm = (bmd - blo) / (bhi - blo) if bhi > blo else np.zeros(st.ndocs)
        bmd_rank = doc_ranks_capped(bmd, blo)
        fus = {}
        for name in ("rrf60", "convex05"):
            lo, _ = st.minmax_of(name, si)
            d = st.doc_max(st.full(name, si))
            fus[name] = (d, doc_ranks_capped(d, lo))
        cvx_order = [int(d) for d in np.argsort(-fus["convex05"][0], kind="stable")[:250] if st.doc_ids[int(d)] not in excl]
        tails.append(cvx_order[:200])
        lex_max = max(lex_doc.values()) if lex_doc else 1.0
        n_lex = len(lex_rank)
        # reranker doc-level scores over the scored chunks of this question
        rr_doc: dict[str, dict[int, float]] = {}
        for rk, table in rr.items():
            cand = st.candidates(si, "convex05", depth)
            sc = {int(c): table.get((q.qid, int(c))) for c in cand}
            cov[rk][qi] = len(cand) > 0 and all(v is not None for v in sc.values())
            dm: dict[int, float] = {}
            for c, s in sc.items():
                if s is None:
                    continue
                d = int(st.chunk_doc[c])
                if s > dm.get(d, -1e9):
                    dm[d] = s
            if lx is not None:                                     # lexical candidates scored too (C)
                for u in lx.candidates(lx.q_index[q.qid], depth)[0]:
                    s = table.get((q.qid, int(u)))
                    if s is not None:
                        d = int(st.chunk_doc[u])
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
            f += [bmd[d], bmd_norm[d], math.log1p(bmd_rank[d]), fus["rrf60"][0][d], math.log1p(fus["rrf60"][1][d]),
                  fus["convex05"][0][d], math.log1p(fus["convex05"][1][d]), float(ntop + int(bmd_rank[d] <= 30))]
            lr = lex_rank.get(d, n_lex + 1)
            f += [lex_doc.get(d, 0.0) / lex_max, math.log1p(lr), float(lr <= 30)]
            for rk, dm in rr_doc.items():
                if dm:
                    vals = np.array(list(dm.values()))
                    lo, hi = float(vals.min()), float(vals.max())
                    if d in dm:
                        v = dm[d]
                        f += [v, (v - lo) / (hi - lo) if hi > lo else 0.0, math.log1p(1 + int((vals > v).sum())), 0.0]
                    else:
                        f += [lo - 1.0, -0.1, math.log1p(len(dm) + 1), 1.0]
                else:
                    f += [-10.0, -0.1, math.log1p(len(cand_docs)), 1.0]
            a_, b_ = st.doc_start[d], st.doc_start[d + 1]
            nch = max(1, b_ - a_)
            best_e5 = int(np.argmax(st.full("e5", si)[a_:b_])) if b_ > a_ else 0
            best_bm = int(np.argmax(st.full("bm25", si)[a_:b_])) if b_ > a_ else 0
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
        if (qi + 1) % 200 == 0:
            print(f"  features: {qi+1}/{len(questions)} questions", flush=True)
    X = np.asarray(X, dtype=np.float64)
    assert X.shape[1] == len(names), (X.shape, len(names))
    return Table(corpus, [q.qid for q in questions], {q.qid: i for i, q in enumerate(questions)},
                 np.asarray(rows_q), np.asarray(rows_d), X, np.asarray(y), names, tails, cov)


FEATURE_SETS = {
    "cheap": lambda n: not (n.startswith("mmarco") or n.startswith("bge")),
    "cheap+mmarco": lambda n: not n.startswith("bge"),
    "cheap+bge": lambda n: not n.startswith("mmarco"),
    "all": lambda n: True,
    "minimal+meta": lambda n: n in ("e5_norm", "bm25_norm", "bm25doc_norm", "rrf60", "lex13_norm", "title_overlap",
                                    "region_match", "region_mismatch", "year_match", "year_mismatch", "is_yearly_edition", "log_doc_len"),
    "legs-only": lambda n: n in ("e5_norm", "bm25_norm", "bm25doc_norm", "rrf60", "convex05", "lex13_norm"),
}


def select_features(tab: Table, fset: str, rows: np.ndarray | None = None):
    pred = FEATURE_SETS[fset]
    keep = [i for i, n in enumerate(tab.names) if pred(n)]
    Xr = tab.X[rows] if rows is not None else tab.X
    nz = [i for i in keep if Xr[:, i].std() > 0]
    return nz, [tab.names[i] for i in nz]


def save_table(tab: Table, path):
    np.savez(path, rows_q=tab.rows_q, rows_d=tab.rows_d, X=tab.X.astype(np.float32), y=tab.y,
             tail=np.array([t + [-1] * (200 - len(t)) for t in tab.tail], dtype=np.int64),
             **{f"cov_{RERANK_TAGS[k]}": v for k, v in tab.rerank_cov.items()})
    json.dump({"qids": tab.qids, "names": tab.names, "corpus": tab.corpus}, open(str(path).replace(".npz", ".json"), "w"))


def load_table(corpus: str, path) -> Table:
    z = np.load(path)
    m = json.load(open(str(path).replace(".npz", ".json")))
    cov = {k: z[f"cov_{t}"] for k, t in RERANK_TAGS.items() if f"cov_{t}" in z.files}
    return Table(corpus, m["qids"], {q: i for i, q in enumerate(m["qids"])}, z["rows_q"], z["rows_d"], z["X"].astype(np.float64),
                 z["y"], m["names"], [[int(d) for d in row if d >= 0] for row in z["tail"]], cov)
