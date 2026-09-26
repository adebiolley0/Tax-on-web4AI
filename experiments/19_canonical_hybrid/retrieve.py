#!/usr/bin/env python3
"""Stage C – first stage of the canonical-work hybrid (numpy only): z-score convex fusion of the
exp-13 lexical leg and the e5-small dense leg (fixed w = 0.5), quality filter, soft facet routing,
canonical collapsing; evaluates every pre-reranker variant and writes the reranker candidate
lists (top-20 canonical candidates, best chunk per document).

  cd experiments/17_lex_rerank && ../14_ltr_fusion/.venv/bin/python ../19_canonical_hybrid/retrieve.py

Fusion rule (fixed, not tuned): per leg, z-score its top-2,000 chunk scores (mean / std of that
population); a chunk absent from a leg's top-2,000 gets that leg's minimum z; fused = 0.5·z_lex +
0.5·z_dense, min-max normalised over the union → f ∈ [0, 1]. Facet boosts multiply f by 1.2 per
matching facet (region / year / tax domain / document type); an explicit region cue is a hard
filter (documents of another region are removed) relaxed to a boost when fewer than 10 candidates
remain. Document score = best chunk; one member per work (edition group) is kept.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

import numpy as np

from rag_eval import load_corpus_c, load_questions_c, fixed_chunks, evaluate_rankings, save_result, Question
from rag_eval.corpora import Doc

from common19 import (CACHE, EXP, RUNS, FUSION_W, FACET_BOOST, MIN_AFTER_HARD_FILTER, RERANK_DEPTH, zone_text,
                      doc_matches, sha1)

# name → (text version, quality filter, canonicalisation level, facet routing)
VARIANTS = {
    "baseline": ("raw", False, None, False),
    "+quality": ("raw", True, None, False),
    "+quality+zoning": ("zoned", True, None, False),
    "+quality+zoning+canon": ("zoned", True, "work", False),
    "full": ("zoned", True, "work", True),
    # single-component ablations (pre-reranker only)
    "+zoning_only": ("zoned", False, None, False),
    "+canon_only": ("raw", False, "work", False),
    "+facets_only": ("raw", False, None, True),
    "+canon_twin_only": ("raw", False, "twin", False),
    "full_twin": ("zoned", True, "twin", True),
}
RERANKED = ["baseline", "+quality", "+quality+zoning", "+quality+zoning+canon", "full"]


@dataclass
class Legs:
    lex_idx: np.ndarray
    lex_sc: np.ndarray
    dense_idx: np.ndarray
    dense_sc: np.ndarray
    chunk_doc: np.ndarray


def load_legs(text: str, prefix: str = "") -> Legs:
    lx = np.load(CACHE / f"{prefix}lex_{text}.npz")
    dn = np.load(CACHE / f"{prefix}dense_{text}.npz")
    ch = np.load(CACHE / "chunks.npz")
    return Legs(lx["idx"], lx["score"], dn["idx"], dn["score"], ch[f"chunk_doc_{text}"])


def zscore(x: np.ndarray) -> np.ndarray:
    s = x.std()
    return (x - x.mean()) / s if s > 0 else np.zeros_like(x)


def fused_chunks(legs: Legs, qi: int, w: float = FUSION_W) -> tuple[np.ndarray, np.ndarray, dict]:
    """Union of both legs' top chunks with the fused score f ∈ [0, 1] and per-leg z (for diagnostics)."""
    li, ls = legs.lex_idx[qi], legs.lex_sc[qi].astype(np.float64)
    di, ds = legs.dense_idx[qi], legs.dense_sc[qi].astype(np.float64)
    ok = ls > 0
    li, ls = li[ok], ls[ok]
    zl, zd = zscore(ls), zscore(ds)
    union = np.union1d(li, di)
    pos = {int(c): k for k, c in enumerate(union)}
    zl_all = np.full(len(union), zl.min() if len(zl) else 0.0)
    zd_all = np.full(len(union), zd.min())
    for c, z in zip(li, zl):
        zl_all[pos[int(c)]] = z
    for c, z in zip(di, zd):
        zd_all[pos[int(c)]] = z
    fused = (1 - w) * zl_all + w * zd_all
    lo, hi = fused.min(), fused.max()
    f = (fused - lo) / (hi - lo) if hi > lo else np.zeros_like(fused)
    return union, f, {"n_lex": int(len(li)), "n_dense": int(len(di)), "n_union": int(len(union))}


def rank_variant(legs: Legs, qi: int, facets: dict, metas: list[dict], quality: bool, canon: str | None,
                 use_facets: bool, top: int = 50, leg: str | None = None) -> tuple[list[tuple[str, int, float]], dict]:
    """Returns [(doc index, best chunk index, score)] ordered, plus diagnostics."""
    diag: dict = {}
    if leg == "lex":
        union, f = legs.lex_idx[qi][legs.lex_sc[qi] > 0], legs.lex_sc[qi][legs.lex_sc[qi] > 0].astype(np.float64)
    elif leg == "dense":
        union, f = legs.dense_idx[qi], legs.dense_sc[qi].astype(np.float64)
    else:
        union, f, diag = fused_chunks(legs, qi)
    docs_of = legs.chunk_doc[union]
    # best chunk per document
    order = np.argsort(-f, kind="stable")
    best: dict[int, tuple[int, float]] = {}
    for k in order:
        d = int(docs_of[k])
        if d not in best:
            best[d] = (int(union[k]), float(f[k]))
    n0 = len(best)
    if quality:
        best = {d: v for d, v in best.items() if not metas[d]["drop"]}
    diag["n_docs"] = n0; diag["n_after_quality"] = len(best)
    if use_facets:
        scored = {}
        n_boost = 0
        for d, (c, s) in best.items():
            m = doc_matches(metas[d], facets)
            if m:
                n_boost += 1
            scored[d] = (c, s * FACET_BOOST ** len(m), m)
        diag["n_boosted"] = n_boost
        if facets.get("region_explicit"):
            r = facets["region_explicit"]
            keep = {d: v for d, v in scored.items() if metas[d]["region"] in (r, None)}
            top_keep = sorted(keep.values(), key=lambda v: -v[1])[:MIN_AFTER_HARD_FILTER]
            if len(keep) >= MIN_AFTER_HARD_FILTER:
                diag["hard_filter_removed"] = len(scored) - len(keep)
                scored = keep
            else:
                diag["hard_filter_relaxed"] = True
        best = {d: (c, s) for d, (c, s, m) in scored.items()}
    ranked = sorted(best.items(), key=lambda kv: (-kv[1][1], kv[0]))
    if canon:
        seen, out = set(), []
        for d, v in ranked:
            g = metas[d][canon]
            if g not in seen:
                seen.add(g); out.append((d, v))
        diag["n_collapsed"] = len(ranked) - len(out)
        ranked = out
    return [(d, c, s) for d, (c, s) in ranked[:top]], diag


def edition_aware(questions: list[Question], rankings: dict[str, list[str]], doc_ids: list[str], metas: list[dict]):
    """Map ranking and expected ids to work ids so every edition of a work is an acceptable answer."""
    pos = {d: i for i, d in enumerate(doc_ids)}
    wid = lambda d: f"work:{metas[pos[d]]['work']}" if d in pos else d
    qs = [Question(q.qid, q.question, sorted({wid(e) for e in q.expected}), sorted({wid(e) for e in q.secondary}), q.meta) for q in questions]
    rk = {qid: [wid(d) for d in r] for qid, r in rankings.items()}
    return qs, rk


def slice_metrics(res, questions) -> dict:
    """MRR / H@1 / R@10 (first-hit) per mined source slice (pq / faq / ruling) and overall."""
    out = {}
    src = {q.qid: q.meta.get("source") or "all" for q in questions}
    for sl in sorted({*src.values(), "all"}):
        rows = [v for qid, v in res.per_question.items() if sl == "all" or src[qid] == sl]
        if rows:
            out[sl] = {"n": len(rows), "mrr": round(float(np.mean([v["rr"] for v in rows])), 4),
                       "hit@1": round(float(np.mean([1.0 if v["rank"] == 1 else 0.0 for v in rows])), 4),
                       "recall@10": round(float(np.mean([1.0 if v["rank"] and v["rank"] <= 10 else 0.0 for v in rows])), 4)}
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default="human", choices=["human", "mined"])
    a = ap.parse_args()
    t0 = time.perf_counter()
    meta = json.loads((CACHE / "meta.json").read_text())
    metas = json.loads((CACHE / "docs_meta.json").read_text())
    doc_ids = meta["doc_ids"]
    if a.questions == "mined":
        from rag_eval import load_questions_mined
        questions = load_questions_mined("C")
        facets = json.loads((CACHE / "mined_facets.json").read_text())
        assert [q.qid for q in questions] == json.loads((CACHE / "mined_meta.json").read_text())["qids"]
        prefix, run_prefix = "mined_", "mined__pre__"
    else:
        questions = load_questions_c()
        facets = json.loads((CACHE / "facets.json").read_text())
        assert [q.qid for q in questions] == meta["qids"]
        prefix, run_prefix = "", "pre__"
    legs = {t: load_legs(t, prefix) for t in ("raw", "zoned") if (CACHE / f"{prefix}dense_{t}.npz").exists()}
    print(f"loaded legs {sorted(legs)} ({time.perf_counter()-t0:.0f}s)", flush=True)

    results, rankings_all, cands_all, diags, slices = {}, {}, {}, {}, {}
    runs = [("lex_raw", ("raw", False, None, False), "lex"), ("dense_raw", ("raw", False, None, False), "dense")]
    runs += [(name, cfg, None) for name, cfg in VARIANTS.items()]
    for name, (text, quality, canon, use_facets), leg in runs:
        if text not in legs:
            print(f"  {name:24s} skipped (no dense_{text}.npz yet)", flush=True)
            continue
        rankings, cands, dg = {}, {}, []
        for qi, q in enumerate(questions):
            ranked, diag = rank_variant(legs[text], qi, facets[q.qid], metas, quality, canon, use_facets, leg=leg)
            rankings[q.qid] = [doc_ids[d] for d, _, _ in ranked]
            cands[q.qid] = [(doc_ids[d], c, s) for d, c, s in ranked[:RERANK_DEPTH]]
            dg.append(diag)
        cfg = {"stage": "fusion only" if leg is None else f"{leg} leg only", "text": text, "quality_filter": quality,
               "canonicalisation": canon, "facet_routing": use_facets, "fusion": f"z-score convex w_dense={FUSION_W} (fixed)",
               "facet_boost": FACET_BOOST if use_facets else None}
        cfg["questions"] = a.questions
        res = evaluate_rankings(f"{run_prefix}{name}", "C", questions, rankings, cfg, {"query_ms": 26 + 5})
        save_result(EXP, res)
        results[name] = res
        line = f"  {name:24s} train {res.metrics['train_mrr']:.3f} | val {res.metrics['val_mrr']:.3f} H@1 {res.metrics['val_hit@1']:.3f} R@10 {res.metrics['val_recall@10']:.3f} | all {res.metrics['mrr']:.3f}"
        if a.questions == "mined":
            sm = slice_metrics(res, questions)
            line += " || " + " ".join(f"{sl} {m['mrr']:.3f}" for sl, m in sm.items() if sl != "all")
            slices[name] = sm
        if canon:
            qs2, rk2 = edition_aware(questions, rankings, doc_ids, metas)
            res2 = evaluate_rankings(f"{run_prefix}{name}__editionaware", "C", qs2, rk2, {**cfg, "eval": "edition-aware (any edition of the work accepted)"})
            save_result(EXP, res2)
            results[name + "__editionaware"] = res2
            line += f" || edition-aware val {res2.metrics['val_mrr']:.3f} all {res2.metrics['mrr']:.3f}"
        print(line, flush=True)
        rankings_all[name] = rankings
        cands_all[name] = cands
        diags[name] = dg

    if a.questions == "mined":
        RUNS.mkdir(exist_ok=True)
        (RUNS / "mined_pre_summary.json").write_text(json.dumps({
            "n": len(questions), "variants": {n: {"config": VARIANTS.get(n), "metrics": r.metrics, "slices": slices.get(n)} for n, r in results.items()},
            "per_question": {n: {qid: v["rank"] for qid, v in r.per_question.items()} for n, r in results.items()}}, ensure_ascii=False, indent=1))
        print(f"done in {time.perf_counter()-t0:.0f}s", flush=True)
        return

    # ── candidate texts for the reranker (5 reranked variants) ──────────────
    docs = load_corpus_c(max_chars=200_000)
    raw_chunks = fixed_chunks(docs, 1200, 100, prefix_title=True)
    zoned_docs = [Doc(d.doc_id, d.title, zone_text(d.title, d.text)[0], dict(d.meta)) for d in docs]
    zoned_chunks = fixed_chunks(zoned_docs, 1200, 100, prefix_title=True)
    assert len(raw_chunks) == meta["n_chunks_raw"] and len(zoned_chunks) == meta["n_chunks_zoned"]
    texts = {"raw": raw_chunks, "zoned": zoned_chunks}
    out = {}
    pair_keys = set()
    for name in RERANKED:
        text = VARIANTS[name][0]
        if name not in cands_all:
            continue
        out[name] = {}
        for qi, q in enumerate(questions):
            lst = []
            for d, c, s in cands_all[name][q.qid]:
                t = texts[text][c].text
                assert texts[text][c].doc_id == d
                lst.append({"doc": d, "chunk": int(c), "text_version": text, "sha": sha1(t), "text": t, "fused": round(s, 4)})
                pair_keys.add((qi, sha1(t)))
            out[name][q.qid] = lst
    (CACHE / "candidates.json").write_text(json.dumps(out, ensure_ascii=False))
    (CACHE / "pre_rankings.json").write_text(json.dumps({n: rankings_all[n] for n in VARIANTS if n in rankings_all}, ensure_ascii=False))
    RUNS.mkdir(exist_ok=True)
    (RUNS / "pre_summary.json").write_text(json.dumps({
        "variants": {n: {"config": VARIANTS.get(n), "metrics": r.metrics} for n, r in results.items()},
        "diag_means": {n: {k: float(np.mean([d.get(k, 0) for d in dg])) for k in ("n_lex", "n_dense", "n_union", "n_docs", "n_after_quality", "n_boosted", "n_collapsed", "hard_filter_removed")}
                       for n, dg in diags.items()},
        "n_distinct_pairs": len(pair_keys)}, ensure_ascii=False, indent=1))
    print(f"candidates: {len(pair_keys)} distinct (question, chunk text) pairs over {len(RERANKED)} reranked variants; done in {time.perf_counter()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
