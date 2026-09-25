#!/usr/bin/env python3
"""Principled fusion / reranker tuning with a train/val protocol.

Grid: first stage = convex(w) over min-max chunk scores (w in 0..1) or RRF(k) (k in 10..200,
depth 300) of a dense leg and a lexical leg; second stage = cross-encoder on the top-N fused
chunks (N in 10/20/30/50) with score interpolation
    final = beta * minmax(rerank) + (1 - beta) * minmax(fused)     (beta in 0..1; beta=1 = "replace")
The best config is selected on the train split (mean RR, ties: nDCG@5 then lower depth) and
reported on val; the swapped fold selects on val and reports on train; "oof" combines both.

  uv run python tune_fusion.py --corpus A --dense e5 --lex chunk
  uv run python tune_fusion.py --corpus A --dense bgem3 --lex doc
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

import numpy as np

from rag_eval import load_questions_a, load_questions_b, load_questions_c
from common14 import CACHE, Stage1, convex_scores, minmax, rrf_scores
from features import load_rerank
from protocol import fold_report, per_question_metrics, select_best, split_masks

LOADERS = {"A": load_questions_a, "B": load_questions_b, "C": load_questions_c}
W_GRID = [round(w, 1) for w in np.arange(0, 1.01, 0.1)]
K_GRID = [10, 20, 40, 60, 100, 200]
DEPTHS = [10, 20, 30, 50]
BETAS = [round(b, 1) for b in np.arange(0, 1.01, 0.1)]


def base_configs():
    return [("convex", w) for w in W_GRID] + [("rrf", k) for k in K_GRID]


def fused_scores(st: Stage1, qi: int, dense: str, lex: str, kind: str, p: float) -> np.ndarray:
    d = st.legs[dense][qi].astype(np.float64)
    if lex == "chunk":
        b = st.legs["bm25"][qi].astype(np.float64)
    else:                                            # whole-document BM25 broadcast to its chunks
        b = st.bm25_doc[qi].astype(np.float64)[st.chunk_doc]
    return convex_scores(d, b, p) if kind == "convex" else rrf_scores([d, b], float(p))


def rank_docs_from_order(st: Stage1, order: np.ndarray, top: int = 50) -> list[str]:
    seen: set[int] = set(); out: list[str] = []
    for j in order:
        dd = int(st.chunk_doc[j])
        if dd not in seen:
            seen.add(dd); out.append(st.doc_ids[dd])
            if len(out) >= top:
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--dense", default="e5")
    ap.add_argument("--lex", default="chunk", choices=["chunk", "doc"])
    ap.add_argument("--rerankers", default="mmarco-minilm,bge-reranker-v2-m3")
    ap.add_argument("--no_save", action="store_true")
    a = ap.parse_args()
    st = Stage1(a.corpus)
    questions = LOADERS[a.corpus]()
    assert [q.qid for q in questions] == st.qids
    nq = len(questions)
    masks = split_masks(questions)
    rr_tables = {rk: load_rerank(a.corpus, rk) for rk in a.rerankers.split(",") if rk != "none"}
    rr_tables = {k: v for k, v in rr_tables.items() if v is not None}
    print(f"corpus {a.corpus}: dense={a.dense} lex={a.lex}; rerankers cached: {list(rr_tables)}", flush=True)
    t0 = time.perf_counter()

    # ── enumerate configs: (kind, p, reranker|None, depth, beta) ───────────────
    configs: list[tuple] = []
    rankings: list[list[list[str]]] = []          # per config: per question ranking
    coverage: dict[tuple, list[float]] = {}
    for kind, p in base_configs():
        per_q_base: list[list[str]] = []
        per_q_top: list[tuple[np.ndarray, np.ndarray]] = []
        for qi in range(nq):
            s = fused_scores(st, qi, a.dense, a.lex, kind, p)
            k = min(len(s), 2000)
            part = np.argpartition(-s, k - 1)[:k] if k < len(s) else np.arange(len(s))
            order = part[np.argsort(-s[part], kind="stable")]
            per_q_base.append(rank_docs_from_order(st, order))
            per_q_top.append((order, s))
        configs.append((kind, p, None, 0, 0.0)); rankings.append(per_q_base)
        for rk, table in rr_tables.items():
            for N in DEPTHS:
                cov = []
                variants: dict[float, list[list[str]]] = {b: [] for b in BETAS}
                for qi in range(nq):
                    order, s = per_q_top[qi]
                    top = order[:N]
                    qsc = table.get(qi, {})
                    rr = np.array([qsc.get(int(j), np.nan) for j in top])
                    present = ~np.isnan(rr)
                    cov.append(float(present.mean()))
                    if present.any():
                        rr[~present] = np.nanmin(rr)          # unscored chunk: assume worst
                    else:
                        rr[:] = 0.0
                    rr_n = minmax(rr); fu_n = minmax(s[top])
                    for b in BETAS:
                        final = b * rr_n + (1 - b) * fu_n
                        new_top = top[np.argsort(-final, kind="stable")]
                        variants[b].append(rank_docs_from_order(st, np.concatenate([new_top, order[N:]])))
                coverage[(kind, p, rk, N)] = cov
                for b in BETAS:
                    configs.append((kind, p, rk, N, b)); rankings.append(variants[b])
    print(f"  {len(configs)} configs in {time.perf_counter()-t0:.0f}s", flush=True)
    for (kind, p, rk, N), cov in coverage.items():
        if (kind, p) in (("convex", 0.5), ("rrf", 60)):
            print(f"  coverage {kind}{p} {rk}@{N}: {np.mean(cov):.2f} of top-{N} chunks have reranker scores")

    # ── per-question metrics for every config ──────────────────────────────
    M = np.zeros((len(configs), nq, 4))
    for ci, rks in enumerate(rankings):
        for qi, q in enumerate(questions):
            M[ci, qi] = per_question_metrics(q, rks[qi])
    RR, H1, R10, ND = M[..., 0], M[..., 1], M[..., 2], M[..., 3]
    cost = np.array([c[3] for c in configs], dtype=float)
    is_stage1 = np.array([c[2] is None for c in configs])
    is_replace = np.array([c[2] is not None and c[4] == 1.0 for c in configs])

    def describe(ci):
        kind, p, rk, N, b = configs[ci]
        d = {"fusion": f"{kind}{p}", "dense": a.dense, "lex": a.lex}
        if rk:
            d.update({"reranker": rk, "depth": N, "beta": b})
        return d

    def fmt(ci):
        kind, p, rk, N, b = configs[ci]
        return f"{kind}{p}" + (f"+{rk.split('-')[0]}@{N} β={b}" if rk else "")

    def report_family(label: str, allowed: np.ndarray, name: str):
        idx = np.where(allowed)[0]
        sel_tr = idx[select_best(RR[idx], masks["train"], ND[idx], cost[idx])]
        sel_va = idx[select_best(RR[idx], masks["val"], ND[idx], cost[idx])]
        oracle_val = idx[select_best(RR[idx], masks["val"], ND[idx], cost[idx])]
        print(f"\n[{label}] selected on train: {fmt(sel_tr)}  train={RR[sel_tr][masks['train']].mean():.3f} "
              f"val={RR[sel_tr][masks['val']].mean():.3f} | selected on val: {fmt(sel_va)} "
              f"val={RR[sel_va][masks['val']].mean():.3f} train={RR[sel_va][masks['train']].mean():.3f}", flush=True)
        # top-5 on train with their val numbers (how flat is the optimum?)
        top5 = idx[np.argsort(-(RR[idx][:, masks["train"]].mean(1) + 1e-4 * ND[idx][:, masks["train"]].mean(1)))[:5]]
        for ci in top5:
            print(f"    train {RR[ci][masks['train']].mean():.3f} val {RR[ci][masks['val']].mean():.3f} all {RR[ci].mean():.3f}  {fmt(ci)}")
        fold_report(name, a.corpus, questions,
                    fit=lambda mask: idx[select_best(RR[idx], mask, ND[idx], cost[idx])],
                    rank=lambda ci, qi: rankings[ci][qi], describe=describe,
                    extra_config={"grid": label, "n_configs": int(len(idx))}, save=not a.no_save)
        return sel_tr, sel_va, oracle_val

    tag = f"{a.dense}+bm25{a.lex}"
    s1 = report_family("first stage only", is_stage1, f"tune__{tag}__stage1")
    families = {"replace (β=1)": is_replace, "interpolated": ~is_stage1}
    for rk in rr_tables:
        families[f"{rk} only"] = np.array([c[2] == rk for c in configs])
    results = {}
    for label, allowed in families.items():
        if not allowed.any():
            continue
        short = label.replace(" ", "_").replace("(", "").replace(")", "").replace("=", "")
        results[label] = report_family(label, allowed, f"tune__{tag}__rerank_{short}")

    # ── β curve at the train-selected base/depth (both rerankers) ──────────
    if not rr_tables:
        return
    sel = results["interpolated"][0]
    kind, p, rk_sel, N_sel, _ = configs[sel]
    print(f"\nβ curves at {kind}{p}, depth {N_sel} (val MRR / train MRR / all MRR):")
    curves = {}
    for rk in rr_tables:
        row = []
        for b in BETAS:
            ci = configs.index((kind, p, rk, N_sel, b))
            row.append((b, RR[ci][masks["val"]].mean(), RR[ci][masks["train"]].mean(), RR[ci].mean()))
        curves[rk] = row
        print(f"  {rk:22s} " + " ".join(f"β{b}:{v:.3f}/{t:.3f}/{al:.3f}" for b, v, t, al in row))
    print(f"\ndepth curve at {kind}{p}, β=1 and β=0.5 (val/train/all MRR):")
    for rk in rr_tables:
        for b in (1.0, 0.5):
            row = []
            for N in DEPTHS:
                ci = configs.index((kind, p, rk, N, b))
                row.append(f"N{N}:{RR[ci][masks['val']].mean():.3f}/{RR[ci][masks['train']].mean():.3f}/{RR[ci].mean():.3f}")
            print(f"  {rk:22s} β={b}: " + " ".join(row))
    # dump the full grid for the README
    dump = [{"config": dict(zip(("fusion", "p", "reranker", "depth", "beta"), c)),
             "train_mrr": float(RR[i][masks["train"]].mean()), "val_mrr": float(RR[i][masks["val"]].mean()),
             "all_mrr": float(RR[i].mean()), "all_h1": float(H1[i].mean()), "all_r10": float(R10[i].mean()),
             "all_ndcg5": float(ND[i].mean())} for i, c in enumerate(configs)]
    (CACHE / f"{a.corpus}_grid_{tag}.json").write_text(json.dumps(dump))


if __name__ == "__main__":
    main()
