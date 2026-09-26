#!/usr/bin/env python3
"""Stage 1 of experiment 22: the three legs (reception BM25F, colbert-fr, cached e5-small) alone and under FIXED
z-score convex weights, on the 40 human and the 304 mined corpus-B questions; reproduction of the reference
first stages (exp 03 e5 RRF, exp 12 colbert + BM25 RRF) on both sets; selection between the two pre-registered
candidates on the mined TRAIN split only; paired tests (rag_eval.stats); candidate files for the rerankers.

  ../14_ltr_fusion/.venv/bin/python run_stage1.py        (needs cache/B_legs.npz with the colbert legs)
→ runs/stage1.json, runs/stage1_tables.md, cache/B_candidates.json
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from common22 import (CACHE, CANDIDATES, FUSIONS, HUMAN_HEAD, LEGS, MINED_HEAD, PAIRED_HEAD, REFS_HUMAN, REFS_MINED, RUNS, SLICES,
                      doc_max, evaluate_save, fmt_human, fmt_mined, fmt_paired, fuse_z, load_legs, minmax, paired, questions_human,
                      questions_mined, rankings_from, ranks_of, ranks_of_file, slice_metrics, split_metrics, zscore)

DEPTH = 30


def rrf_chunk(mats: list[np.ndarray], depth: int = 200, k: int = 60) -> np.ndarray:
    """exp 03 / exp 12 RRF at chunk level (top-200 chunks of each leg, k = 60)."""
    nq, n = mats[0].shape
    out = np.zeros((nq, n))
    for m in mats:
        for i in range(nq):
            top = np.argsort(-m[i], kind="stable")[:depth]
            out[i, top] += 1.0 / (k + np.arange(1, depth + 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    L = load_legs()
    z, doc_ids = L["z"], L["doc_ids"]
    assert "colbert_doc" in z, "run colbert_scores.py (torch lock) then legs.py first"
    n_docs = len(doc_ids)
    chunk_doc, doc_start = z["chunk_doc"], z["doc_start"]
    sets = {"human": questions_human(), "mined": questions_mined()}
    nh = len(sets["human"])
    rows = {"human": slice(0, nh), "mined": slice(nh, nh + len(sets["mined"]))}
    legs = {"human": {"rec": z["rec_human"], "colbert": z["colbert_doc"][rows["human"]], "e5": z["e5_doc"][rows["human"]]},
            "mined": {"rec": z["rec_mined"], "colbert": z["colbert_doc"][rows["mined"]], "e5": z["e5_doc"][rows["mined"]]}}
    chunk_legs = {w: {"colbert": z["colbert_chunk"][rows[w]], "e5": z["e5_chunk"][rows[w]], "bm25_03": z["bm25_03_chunk"][rows[w]]} for w in sets}

    results = {w: {} for w in sets}          # which → run → {"ranks", "metrics", "config", "scores"}
    top_chunks = {w: {} for w in sets}        # bar replication: top-30 chunk ids of the exp-03 RRF

    def run(w: str, name: str, scores: np.ndarray, config: dict, positive_only: bool = False):
        qs = sets[w]
        rk = rankings_from(scores, qs, doc_ids, 60, positive_only)
        res = evaluate_save(name, qs, rk, config, w, save=not a.no_save)
        ranks = ranks_of(res)
        m = split_metrics(ranks, qs) if w == "human" else slice_metrics(ranks, qs)
        results[w][name] = {"ranks": ranks, "metrics": m, "config": config, "scores": scores, "rankings": rk}
        if w == "human":
            print(f"  [{w}] {name:28s} train {m['train']['mrr']:.3f}  val {m['val']['mrr']:.3f}  all {m['all']['mrr']:.3f} | R@30 val {m['val']['recall@30']:.3f} all {m['all']['recall@30']:.3f}", flush=True)
        else:
            print(f"  [{w}] {name:28s} all {m['all']['mrr']:.3f}  pq {m['pq']['mrr']:.3f}  ruling {m['ruling']['mrr']:.3f} | train {m['train']['mrr']:.3f} val {m['val']['mrr']:.3f} | R@30 {m['all']['recall@30']:.3f}", flush=True)

    rec_cfg = {"reception": L["reception"]}
    for w, qs in sets.items():
        print(f"\n== {w} ({len(qs)} questions) ==", flush=True)
        lg = legs[w]
        run(w, "rec", lg["rec"], {"stage": "reception BM25F alone (exp-20 train-selected point)", **rec_cfg}, True)
        run(w, "colbert", lg["colbert"], {"stage": "colbert-fr MaxSim alone (doc = max chunk)", "model": "antoinelouis/colbertv1-camembert-base-mmarcoFR"})
        run(w, "e5", lg["e5"], {"stage": "e5-small alone (doc = max chunk, cached)"})
        # reference first stages reproduced here (chunk-level RRF, doc = max)
        cl = chunk_legs[w]
        rr = rrf_chunk([cl["e5"], cl["bm25_03"]])
        top_chunks[w] = {q.qid: [int(j) for j in np.argsort(-rr[i], kind="stable")[:DEPTH]] for i, q in enumerate(qs)}
        run(w, "e5_bm25__rrf03", np.stack([doc_max(rr[i], chunk_doc, n_docs, 0.0) for i in range(len(qs))]),
            {"stage": "exp 03 first stage reproduced: RRF60(e5-small, BM25 tok03) over top-200 chunks"})
        rr = rrf_chunk([cl["colbert"], cl["bm25_03"]])
        run(w, "colbert_bm25__rrf12", np.stack([doc_max(rr[i], chunk_doc, n_docs, 0.0) for i in range(len(qs))]),
            {"stage": "exp 12 first stage reproduced: RRF60(colbert-fr, BM25 tok03) over top-200 chunks"})
        run(w, "rec_e5__mm05", np.stack([0.5 * minmax(lg["rec"][i]) + 0.5 * minmax(lg["e5"][i]) for i in range(len(qs))]),
            {"stage": "exp 20 fused stage reproduced: 0.5 minmax(reception) + 0.5 minmax(e5)", **rec_cfg})
        # fixed z-score fusions
        for name, wts in FUSIONS.items():
            run(w, name, fuse_z(lg, wts), {"stage": "z-score convex fusion, fixed weights", "weights": dict(zip(LEGS, wts)), **rec_cfg})
        run(w, "mm3_equal", np.stack([sum(minmax(lg[l][i]) for l in LEGS) / 3 for i in range(len(qs))]),
            {"stage": "min-max convex fusion, equal weights (fusion-rule check)", "weights": dict(zip(LEGS, (1 / 3,) * 3)), **rec_cfg})

    # ── selection on the mined TRAIN split only ─────────────────────────────
    mt = {c: results["mined"][c]["metrics"]["train"] for c in CANDIDATES}
    selected = max(CANDIDATES, key=lambda c: (round(mt[c]["mrr"], 4), mt[c]["recall@30"]))
    alt = [c for c in CANDIDATES if c != selected][0]
    print(f"\nselected on mined train: {selected} (train MRR {mt[selected]['mrr']:.3f} vs {alt} {mt[alt]['mrr']:.3f})", flush=True)

    # ── references and paired tests ─────────────────────────────────────────
    refs = {"human": {k: {"label": v[1], "ranks": ranks_of_file(v[0])} for k, v in REFS_HUMAN.items() if v[0].exists()},
            "mined": {k: {"label": v[1], "ranks": ranks_of_file(v[0])} for k, v in REFS_MINED.items() if v[0].exists()}}
    for w in sets:
        for v in refs[w].values():
            v["metrics"] = split_metrics(v["ranks"], sets[w]) if w == "human" else slice_metrics(v["ranks"], sets[w])
    repro = {}
    for w in sets:
        qs = sets[w]
        for mine, ref in (("rec", "rec"), ("rec_e5__mm05", "rec_e5"), ("e5_bm25__rrf03", "e5_rrf"), ("colbert_bm25__rrf12", "colbert_bm25"), ("colbert", "colbert")):
            if ref in refs[w]:
                repro[f"{w}:{mine} vs {ref}"] = sum(1 for q in qs if results[w][mine]["ranks"][q.qid] == refs[w][ref]["ranks"].get(q.qid))
    print("reproduction of stored ranks:", repro, flush=True)

    tests = {"human": {}, "mined": {}}
    for w in sets:
        qs = sets[w]
        groups = {"val": [q.qid for q in qs if q.split == "val"], "train": [q.qid for q in qs if q.split == "train"], "all": [q.qid for q in qs]}
        if w == "mined":
            groups.update({sl: [q.qid for q in qs if q.meta.get("source") == sl] for sl in SLICES if sl != "faq"})
        base_runs = {"rec_e5 (exp 20)": refs[w]["rec_e5"]["ranks"],
                     "colbert+bm25 RRF (exp 12)": refs[w]["colbert_bm25"]["ranks"] if "colbert_bm25" in refs[w] else results[w]["colbert_bm25__rrf12"]["ranks"],
                     "bm25 (exp 01)": refs[w]["bm25_01"]["ranks"], "lex13 (exp 13)": refs[w]["lex13"]["ranks"],
                     "e5 RRF (exp 03)": refs[w]["e5_rrf"]["ranks"] if "e5_rrf" in refs[w] else results[w]["e5_bm25__rrf03"]["ranks"],
                     "colbert alone": results[w]["colbert"]["ranks"]}
        for cand in (selected, alt):
            for bl, br in base_runs.items():
                for g, qids in groups.items():
                    tests[w][f"{cand} vs {bl} [{g}]"] = paired(br, results[w][cand]["ranks"], qids)
        for g, qids in groups.items():
            tests[w][f"{selected} vs {alt} [{g}]"] = paired(results[w][alt]["ranks"], results[w][selected]["ranks"], qids)
            tests[w][f"z_rec_e5 vs rec_e5 (exp 20) [{g}] (z-score vs min-max, same legs)"] = paired(refs[w]["rec_e5"]["ranks"], results[w]["z_rec_e5"]["ranks"], qids)
            tests[w][f"z3_equal vs mm3_equal [{g}] (fusion rule)"] = paired(results[w]["mm3_equal"]["ranks"], results[w]["z3_equal"]["ranks"], qids)

    # ── candidates for the rerankers ────────────────────────────────────────
    cands = {}
    for w, qs in sets.items():
        cl = chunk_legs[w]
        for pipe in (selected, alt):
            per_q = {}
            sc = results[w][pipe]["scores"]
            for i, q in enumerate(qs):
                zc = zscore(cl["colbert"][i]) + zscore(cl["e5"][i])            # chunk-level dense evidence → best chunk per article
                top = results[w][pipe]["rankings"][q.qid][:DEPTH]
                entry = [[d, float(sc[i][DOC_INDEX[d]])] for d in top]
                best = {}
                for d, _ in entry:
                    di = DOC_INDEX[d]
                    a_, b_ = int(doc_start[di]), int(doc_start[di + 1])
                    best[d] = int(a_ + np.argmax(zc[a_:b_]))
                per_q[q.qid] = {"docs": entry, "best_chunk": best}
            cands[f"{w}:{pipe}"] = per_q
        cands[f"{w}:e5_bm25__rrf03"] = {q.qid: {"chunks": top_chunks[w][q.qid]} for q in qs}
    (CACHE / "B_candidates.json").write_text(json.dumps(cands))

    # ── summary + tables ────────────────────────────────────────────────────
    summary = {"selected": selected, "alt": alt, "candidates": list(CANDIDATES), "mined_train_selection": mt, "reproduction": repro,
               "runs": {w: {k: {"metrics": v["metrics"], "config": v["config"]} for k, v in results[w].items()} for w in sets},
               "refs": {w: {k: {"label": v["label"], "metrics": v["metrics"]} for k, v in refs[w].items()} for w in sets},
               "tests": tests,
               "per_question": {w: {q.qid: {"question": q.question, "split": q.split, "source": q.meta.get("source"),
                                            **{r: results[w][r]["ranks"][q.qid] for r in results[w]},
                                            **{f"ref:{k}": refs[w][k]["ranks"].get(q.qid) for k in refs[w]}} for q in sets[w]} for w in sets}}
    (RUNS / "stage1.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))

    L_ = ["### Corpus B – first stage, human questions (40: 24 train / 16 val)", "", *HUMAN_HEAD]
    for k in ("bm25_01", "lex13", "e5_rrf", "colbert", "colbert_bm25", "rec", "rec_e5", "rec_e5_w1"):
        if k in refs["human"]:
            L_.append(fmt_human(f"ref – {refs['human'][k]['label']}", refs["human"][k]["metrics"]))
    for k, v in results["human"].items():
        star = " **(selected on mined train)**" if k == selected else (" *(alternative)*" if k == alt else "")
        L_.append(fmt_human(k + star, v["metrics"]))
    L_ += ["", "### Corpus B – first stage, mined questions (304: pq 159 / ruling 142 / faq 3; leak-free reception)", "", *MINED_HEAD]
    for k in ("bm25_01", "lex13", "lex13_e5", "rec", "rec_e5", "rec_e5_w1"):
        if k in refs["mined"]:
            L_.append(fmt_mined(f"ref – {refs['mined'][k]['label']}", refs["mined"][k]["metrics"]))
    for k, v in results["mined"].items():
        star = " **(selected on mined train)**" if k == selected else (" *(alternative)*" if k == alt else "")
        L_.append(fmt_mined(k + star, v["metrics"]))
    L_ += ["", f"Selection on the mined train split (145 q): " + ", ".join(f"{c} {mt[c]['mrr']:.3f} (R@30 {mt[c]['recall@30']:.3f})" for c in CANDIDATES) + f" → **{selected}**", ""]
    for w in sets:
        L_ += ["", f"Paired tests, {w} questions (rag_eval.stats.paired_stats; Δ = new − base, reciprocal rank; p_t paired t, p_perm sign-flip, '~' Monte-Carlo):", "", *PAIRED_HEAD]
        for k, t in tests[w].items():
            L_.append(fmt_paired(k, t))
    L_ += ["", "Reproduction of stored reference ranks from these legs: " + ", ".join(f"{k}: {v}" for k, v in repro.items())]
    (RUNS / "stage1_tables.md").write_text("\n".join(L_) + "\n")
    print("\n".join(L_[:60]), flush=True)


DOC_INDEX: dict = {}

if __name__ == "__main__":
    _L = load_legs()
    DOC_INDEX = {d: i for i, d in enumerate(_L["doc_ids"])}
    main()
