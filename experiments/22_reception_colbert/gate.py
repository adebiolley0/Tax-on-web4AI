#!/usr/bin/env python3
"""Length gate (coordinator's follow-up, cache-only): one pipeline that applies `z3_equal` → mMARCO @30 β 0.8 when the
question has ≤ T words and the un-reranked reception + e5 fusion (`z_rec_e5`) otherwise; variant: `z3_equal` → bge @20
for the long side (where bge pairs are cached: human 40, mined 100-question subsample). T ∈ {25, 35, 50} chosen on the
mined TRAIN split + the human TRAIN half (pooled MRR). Uses cache/B_mmarco22.npz and cache/B_bge22.npz only.

  ../14_ltr_fusion/.venv/bin/python gate.py   → runs/gate.json, runs/gate_tables.md, saved runs gate_T*__…
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from common22 import (CACHE, FUSIONS, HUMAN_HEAD, PAIRED_HEAD, REFS_HUMAN, RESULTS, RUNS, evaluate_save, fmt_human, fmt_paired,
                      fuse_z, load_legs, minmax, paired, questions_human, questions_mined, rankings_from, ranks_of, ranks_of_file,
                      slice_metrics, split_metrics)
from rerank_score import load_cache

T_GRID = (25, 35, 50)
BETA = 0.8


def n_words(q) -> int:
    return len(q.question.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    L = load_legs()
    z, doc_ids = L["z"], L["doc_ids"]
    doc_index = {d: i for i, d in enumerate(doc_ids)}
    sets = {"human": questions_human(), "mined": questions_mined()}
    nh = len(sets["human"])
    rows = {"human": slice(0, nh), "mined": slice(nh, None)}
    cands = json.loads((CACHE / "B_candidates.json").read_text())
    mm = {k: v[0] for k, v in load_cache(CACHE / "B_mmarco22.npz").items()}
    bg = {k: v[0] for k, v in load_cache(CACHE / "B_bge22.npz").items()}
    sub = set(json.loads((CACHE / "subsample100.json").read_text())["qids"])

    # component rankings per question -------------------------------------------------------------
    comp = {w: {} for w in sets}          # w → component → qid → ranking
    for w, qs in sets.items():
        lg = {"rec": z["rec_human"] if w == "human" else z["rec_mined"], "colbert": z["colbert_doc"][rows[w]], "e5": z["e5_doc"][rows[w]]}
        comp[w]["z_rec_e5"] = rankings_from(fuse_z(lg, FUSIONS["z_rec_e5"]), qs, doc_ids, 60)
        tail = rankings_from(fuse_z(lg, FUSIONS["z3_equal"]), qs, doc_ids, 60)
        for name, table, depth, pick, beta in (("z3_mmarco30_b0.8", mm, 30, "top", BETA), ("z3_bge20", bg, 20, "best", 1.0)):
            rk = {}
            for q in qs:
                e = cands[f"{w}:z3_equal"][q.qid]
                docs = e["docs"][:depth]
                sc = []
                for d, _ in docs:
                    cs = [e["best_chunk"][d]] if pick == "best" else list(e["top_chunks"][d])
                    vals = [table.get((q.qid, c)) for c in cs]
                    if any(v is None for v in vals):
                        sc = None
                        break
                    sc.append(max(vals))
                if sc is None:
                    continue
                sc = np.array(sc)
                s1 = np.array([s for _, s in docs])
                fused = sc if beta >= 1 else beta * minmax(sc) + (1 - beta) * minmax(s1)
                order = np.argsort(-fused, kind="stable")
                ranked = [docs[j][0] for j in order]
                seen = set(ranked)
                ranked += [d for d in tail[q.qid] if d not in seen]
                rk[q.qid] = ranked[:60]
            comp[w][name] = rk
    subq = [q for q in sets["mined"] if q.qid in sub]
    assert all(q.qid in comp["mined"]["z3_bge20"] for q in subq) and all(q.qid in comp["human"]["z3_bge20"] for q in sets["human"])

    def gated(w, T, long_name):
        return {q.qid: (comp[w]["z3_mmarco30_b0.8"][q.qid] if n_words(q) <= T else comp[w][long_name][q.qid])
                for q in sets[w] if q.qid in comp[w][long_name]}

    def rr(rk, qs):
        r = ranks_of_tmp(rk, qs)
        return np.mean([1.0 / r[q.qid] if r.get(q.qid) else 0.0 for q in qs])

    from rag_eval import evaluate_rankings

    def ranks_of_tmp(rk, qs):
        return ranks_of(evaluate_rankings("tmp", "B", qs, rk))

    # selection of T on mined train + human train (pooled MRR) -------------------------------------
    h_train = [q for q in sets["human"] if q.split == "train"]
    m_train = [q for q in sets["mined"] if q.split == "train"]
    m_train_sub = [q for q in m_train if q.qid in sub]
    sel = {}
    for variant, long_name, mtr in (("rec_e5", "z_rec_e5", m_train), ("bge20", "z3_bge20", m_train_sub)):
        sel[variant] = {}
        for T in T_GRID:
            rk_h, rk_m = gated("human", T, long_name), gated("mined", T, long_name)
            rh = ranks_of_tmp(rk_h, h_train); rm = ranks_of_tmp(rk_m, mtr)
            pooled = np.mean([1.0 / rh[q.qid] if rh.get(q.qid) else 0.0 for q in h_train] + [1.0 / rm[q.qid] if rm.get(q.qid) else 0.0 for q in mtr])
            sel[variant][T] = {"pooled_mrr": float(pooled), "human_train_mrr": float(np.mean([1.0 / rh[q.qid] if rh.get(q.qid) else 0.0 for q in h_train])),
                               "mined_train_mrr": float(np.mean([1.0 / rm[q.qid] if rm.get(q.qid) else 0.0 for q in mtr])), "n": len(h_train) + len(mtr)}
        best = max(T_GRID, key=lambda T: (round(sel[variant][T]["pooled_mrr"], 4), -T))
        sel[variant]["T"] = best
        print(f"[{variant}] T selection (human train 24 + mined train {len(mtr)}): " + ", ".join(f"T={T}: {sel[variant][T]['pooled_mrr']:.3f}" for T in T_GRID) + f" → T = {best}", flush=True)

    # evaluate: gated (selected T and the grid), un-gated components, refs ----------------------
    results = {"human": {}, "mined": {}, "sub100": {}}
    sides = {}

    def run(w, name, rk, config, qs=None, key=None):
        qs = qs or sets[w]
        rk = {q.qid: rk[q.qid] for q in qs if q.qid in rk}
        qs = [q for q in qs if q.qid in rk]
        res = evaluate_save(name, qs, rk, config, w, save=not a.no_save)
        ranks = ranks_of(res)
        m = split_metrics(ranks, qs) if w == "human" else slice_metrics(ranks, qs)
        results[key or w][name] = {"ranks": ranks, "metrics": m, "n": len(qs)}
        return ranks

    for variant, long_name in (("rec_e5", "z_rec_e5"), ("bge20", "z3_bge20")):
        for T in T_GRID:
            name = f"gate_T{T}__mmarco_b0.8__{variant}"
            cfg = {"gate": f"words ≤ {T}: z3_equal → mMARCO @30 β 0.8; else " + ("z_rec_e5 un-reranked" if variant == "rec_e5" else "z3_equal → bge @20"),
                   "T": T, "selected_T": sel[variant]["T"], "T_selected_on": "mined train + human train (pooled MRR)"}
            run("human", name, gated("human", T, long_name), cfg)
            rk_m = gated("mined", T, long_name)
            if variant == "rec_e5":
                run("mined", name, rk_m, cfg)
            run("mined", name + "__sub100", rk_m, {**cfg, "questions": "mined subsample 100"}, subq, key="sub100")
            sides[f"{variant}_T{T}"] = {"human_short": sum(1 for q in sets["human"] if n_words(q) <= T), "human_long": sum(1 for q in sets["human"] if n_words(q) > T),
                                        "mined_short": sum(1 for q in sets["mined"] if n_words(q) <= T), "mined_long": sum(1 for q in sets["mined"] if n_words(q) > T),
                                        "sub100_short": sum(1 for q in subq if n_words(q) <= T), "sub100_long": sum(1 for q in subq if n_words(q) > T)}
    ungated = {}
    for w in sets:
        for c in ("z3_mmarco30_b0.8", "z_rec_e5", "z3_bge20"):
            rk = comp[w][c]
            ungated[(w, c)] = ranks_of_tmp(rk, [q for q in sets[w] if q.qid in rk])
    bar_h = ranks_of_file(REFS_HUMAN["bar"][0])
    bar_m = ranks_of_file(RESULTS / "22_reception_colbert" / "B__e5_bm25__rrf03-_mmarco_30chunks__mined.json")

    tests = {"human": {}, "sub100": {}, "mined": {}}
    hq = {"train": [q.qid for q in h_train], "val": [q.qid for q in sets["human"] if q.split == "val"], "all": [q.qid for q in sets["human"]]}
    sq = {"all": [q.qid for q in subq], "pq": [q.qid for q in subq if q.meta["source"] == "pq"], "ruling": [q.qid for q in subq if q.meta["source"] == "ruling"],
          "train": [q.qid for q in subq if q.split == "train"], "val": [q.qid for q in subq if q.split == "val"]}
    mq = {"all": [q.qid for q in sets["mined"]], "train": [q.qid for q in m_train], "val": [q.qid for q in sets["mined"] if q.split == "val"],
          "pq": [q.qid for q in sets["mined"] if q.meta["source"] == "pq"], "ruling": [q.qid for q in sets["mined"] if q.meta["source"] == "ruling"]}
    for variant in ("rec_e5", "bge20"):
        T = sel[variant]["T"]
        name = f"gate_T{T}__mmarco_b0.8__{variant}"
        bases_h = {"bar (exp 03)": bar_h, "z3_equal → mMARCO @30 β 0.8 (un-gated)": ungated[("human", "z3_mmarco30_b0.8")],
                   "z_rec_e5 un-reranked": ungated[("human", "z_rec_e5")], "z3_equal → bge @20": ungated[("human", "z3_bge20")]}
        for bl, br in bases_h.items():
            for g, qids in hq.items():
                tests["human"][f"{name} vs {bl} [{g}]"] = paired(br, results["human"][name]["ranks"], qids)
        bases_s = {"bar recipe (e5 RRF → mMARCO @30 chunks)": bar_m, "z3_equal → mMARCO @30 β 0.8 (un-gated)": ungated[("mined", "z3_mmarco30_b0.8")],
                   "z_rec_e5 un-reranked": ungated[("mined", "z_rec_e5")], "z3_equal → bge @20": ungated[("mined", "z3_bge20")]}
        for bl, br in bases_s.items():
            for g, qids in sq.items():
                tests["sub100"][f"{name} vs {bl} [{g}]"] = paired(br, results["sub100"][name + "__sub100"]["ranks"], qids)
        if variant == "rec_e5":
            for bl in ("bar recipe (e5 RRF → mMARCO @30 chunks)", "z3_equal → mMARCO @30 β 0.8 (un-gated)", "z_rec_e5 un-reranked"):
                for g, qids in mq.items():
                    tests["mined"][f"{name} vs {bl} [{g}]"] = paired(bases_s[bl], results["mined"][name]["ranks"], qids)
    tests["human"]["gate rec_e5 vs gate bge20 [all]"] = paired(results["human"][f"gate_T{sel['bge20']['T']}__mmarco_b0.8__bge20"]["ranks"],
                                                              results["human"][f"gate_T{sel['rec_e5']['T']}__mmarco_b0.8__rec_e5"]["ranks"], hq["all"])
    tests["sub100"]["gate rec_e5 vs gate bge20 [all]"] = paired(results["sub100"][f"gate_T{sel['bge20']['T']}__mmarco_b0.8__bge20__sub100"]["ranks"],
                                                               results["sub100"][f"gate_T{sel['rec_e5']['T']}__mmarco_b0.8__rec_e5__sub100"]["ranks"], sq["all"])

    words = {w: sorted(n_words(q) for q in sets[w]) for w in sets}
    summary = {"T_grid": list(T_GRID), "selection": sel, "sides": sides, "words": {w: {"median": float(np.median(v)), "min": v[0], "max": v[-1]} for w, v in words.items()},
               "runs": {k: {n: {"metrics": v["metrics"], "n": v["n"]} for n, v in d.items()} for k, d in results.items()},
               "ungated": {f"{w}:{c}": (split_metrics(r, sets[w]) if w == "human" else slice_metrics(r, [q for q in sets[w] if q.qid in r])) for (w, c), r in ungated.items()},
               "tests": tests}
    (RUNS / "gate.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))

    um = summary["ungated"]
    T = ["### Length gate – human questions (40)", "", *HUMAN_HEAD,
         fmt_human("ref – round-1 bar", split_metrics(bar_h, sets["human"])),
         fmt_human("z3_equal → mMARCO @30 β 0.8 (un-gated)", um["human:z3_mmarco30_b0.8"]),
         fmt_human("z_rec_e5 un-reranked (un-gated)", um["human:z_rec_e5"]),
         fmt_human("z3_equal → bge @20 (un-gated)", um["human:z3_bge20"])]
    for n, v in results["human"].items():
        star = " **(T selected)**" if n.startswith(f"gate_T{sel['rec_e5']['T']}__") and n.endswith("rec_e5") or n.startswith(f"gate_T{sel['bge20']['T']}__") and n.endswith("bge20") else ""
        T.append(fmt_human(n + star, v["metrics"]))
    mrow = lambda label, m: f"| {label} | " + " | ".join(f"{m[s]['mrr']:.3f} / {m[s]['hit@1']:.3f} / {m[s]['recall@10']:.3f}" if s in m and m[s]["n"] else "–" for s in ("all", "pq", "ruling", "train", "val")) + " |"
    T += ["", "### Length gate – mined 100-question subsample (MRR / H@1 / R@10)", "", "| run | all (100) | pq (52) | ruling (47) | train (40) | val (60) |", "|---|---|---|---|---|---|",
          mrow("bar recipe (e5 RRF → mMARCO @30 chunks)", slice_metrics(bar_m, subq)),
          mrow("z3_equal → mMARCO @30 β 0.8 (un-gated)", slice_metrics(ungated[("mined", "z3_mmarco30_b0.8")], subq)),
          mrow("z_rec_e5 un-reranked (un-gated)", slice_metrics(ungated[("mined", "z_rec_e5")], subq)),
          mrow("z3_equal → bge @20 (un-gated)", um["mined:z3_bge20"])]
    for n, v in results["sub100"].items():
        T.append(mrow(n, v["metrics"]))
    T += ["", "### Length gate (rec_e5 variant) – all 304 mined questions (MRR / H@1 / R@10)", "", "| run | all (304) | pq (159) | ruling (142) | train (145) | val (159) |", "|---|---|---|---|---|---|",
          mrow("bar recipe", slice_metrics(bar_m, sets["mined"])), mrow("z3_equal → mMARCO @30 β 0.8 (un-gated)", um["mined:z3_mmarco30_b0.8"]), mrow("z_rec_e5 un-reranked", um["mined:z_rec_e5"])]
    for n, v in results["mined"].items():
        T.append(mrow(n, v["metrics"]))
    T += ["", "T selection (pooled MRR over human train 24 + mined train): " + "; ".join(f"{var}: " + ", ".join(f"T={t} {sel[var][t]['pooled_mrr']:.3f} (h {sel[var][t]['human_train_mrr']:.3f} / m {sel[var][t]['mined_train_mrr']:.3f})" for t in T_GRID) + f" → T = {sel[var]['T']}" for var in sel),
          "", "Questions per side of T (short = ≤ T words → mMARCO route): " + "; ".join(f"T={t}: human {sides[f'rec_e5_T{t}']['human_short']} / {sides[f'rec_e5_T{t}']['human_long']}, mined {sides[f'rec_e5_T{t}']['mined_short']} / {sides[f'rec_e5_T{t}']['mined_long']}, subsample {sides[f'rec_e5_T{t}']['sub100_short']} / {sides[f'rec_e5_T{t}']['sub100_long']}" for t in T_GRID)
          + f". Words per question: human median {summary['words']['human']['median']:.0f} (range {summary['words']['human']['min']}–{summary['words']['human']['max']}), mined median {summary['words']['mined']['median']:.0f} ({summary['words']['mined']['min']}–{summary['words']['mined']['max']})."]
    for w in ("human", "sub100", "mined"):
        T += ["", f"Paired tests, {w} (Δ = gated − base):", "", *PAIRED_HEAD]
        for k, t in tests[w].items():
            T.append(fmt_paired(k, t))
    (RUNS / "gate_tables.md").write_text("\n".join(T) + "\n")
    print("\n".join(T), flush=True)


if __name__ == "__main__":
    main()
