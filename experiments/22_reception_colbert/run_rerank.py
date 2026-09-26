#!/usr/bin/env python3
"""Reranked pipelines of experiment 22 from the cached cross-encoder scores (rerank_score.py):

* `<pipe>->mmarco@30` / `@20`: mMARCO-MiniLM over the best CHUNK_CAP (3) chunks of each of the top-k articles of the z-score
  pipeline (doc = max chunk), reranker score only; `_b0.8` = exp 14's fixed interpolation (not re-tuned);
* `e5_bm25__rrf03->mmarco@30chunks`: the round-1 bar's own recipe (top-30 chunks of the e5 RRF stage) reproduced,
  on the human set (checked against the stored bar) and on the 304 mined questions;
* `<pipe>->bge@20`: bge-reranker-v2-m3 on the best dense chunk of the top-20 articles (human; mined 100-subsample).
Paired tests (rag_eval.stats) against the bars and the round-2 best runs.

  ../14_ltr_fusion/.venv/bin/python run_rerank.py   → runs/rerank.json, runs/rerank_tables.md
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from common22 import (CACHE, FUSIONS, HUMAN_HEAD, MINED_HEAD, PAIRED_HEAD, REFS_HUMAN, RUNS, SLICES, colbert_variants, doc_max,
                      evaluate_save, fmt_human, fmt_mined, fmt_paired, fuse_z, load_legs, minmax, paired, pipe_parts, questions_human,
                      questions_mined, rankings_from, ranks_of, ranks_of_file, slice_metrics, split_metrics)
from rerank_score import load_cache
from run_stage1 import rrf_chunk

BETA = 0.8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    L = load_legs()
    z, doc_ids = L["z"], L["doc_ids"]
    doc_index = {d: i for i, d in enumerate(doc_ids)}
    n_docs = len(doc_ids)
    chunk_doc, doc_start = z["chunk_doc"], z["doc_start"]
    sets = {"human": questions_human(), "mined": questions_mined()}
    nh = len(sets["human"])
    rows = {"human": slice(0, nh), "mined": slice(nh, None)}
    st = json.loads((RUNS / "stage1.json").read_text())
    selected, alt = st["selected"], st["alt"]
    final = st.get("final", selected)
    variants = colbert_variants(z)
    pipes = list(dict.fromkeys([final, selected, alt]))
    weights_of = lambda pipe: FUSIONS[pipe_parts(pipe, variants)[0]]
    cands = json.loads((CACHE / "B_candidates.json").read_text())
    mm = {k: v[0] for k, v in load_cache(CACHE / "B_mmarco22.npz").items()}
    bg = {k: v[0] for k, v in load_cache(CACHE / "B_bge22.npz").items()}
    tm_mm = json.loads((CACHE / "B_mmarco22_timing.json").read_text()) if (CACHE / "B_mmarco22_timing.json").exists() else {}
    tm_bg = json.loads((CACHE / "B_bge22_timing.json").read_text()) if (CACHE / "B_bge22_timing.json").exists() else {}
    sub = json.loads((CACHE / "subsample100.json").read_text())["qids"] if (CACHE / "subsample100.json").exists() else []
    print(f"mMARCO pairs cached {len(mm)} ({tm_mm.get('s_per_pair', float('nan'))} s/pair), bge pairs {len(bg)} ({tm_bg.get('s_per_pair', float('nan'))} s/pair), subsample {len(sub)}", flush=True)

    # stage-1 tails (top-60 rankings) recomputed from the legs
    tails = {}
    stage1_ranks = {}
    for w, qs in sets.items():
        lg = {"rec": z["rec_human"] if w == "human" else z["rec_mined"], "colbert": z["colbert_doc"][rows[w]], "e5": z["e5_doc"][rows[w]]}
        for pipe in pipes:
            base, v = pipe_parts(pipe, variants)
            tails[(w, pipe)] = rankings_from(fuse_z({**lg, "colbert": z[f"colbert{v}_doc"][rows[w]]}, FUSIONS[base]), qs, doc_ids, 60)
        rr = rrf_chunk([z["e5_chunk"][rows[w]], z["bm25_03_chunk"][rows[w]]])
        tails[(w, "e5_bm25__rrf03")] = rankings_from(np.stack([doc_max(rr[i], chunk_doc, n_docs, 0.0) for i in range(len(qs))]), qs, doc_ids, 60)
        for k, rk in list(tails.items()):
            if k[0] == w:
                stage1_ranks[k] = {qid: (rk[qid].index(next((d for d in rk[qid] if d in q.expected), None)) + 1
                                         if any(d in q.expected for d in rk[qid]) else None) for q in sets[w] for qid in [q.qid]}

    results = {w: {} for w in sets}
    pairs_per_q = {}

    def evaluate(w, name, rankings, config, timing, qs=None):
        qs = qs or sets[w]
        res = evaluate_save(name, qs, rankings, config, w, timing, save=not a.no_save)
        ranks = ranks_of(res)
        m = split_metrics(ranks, qs) if w == "human" else slice_metrics(ranks, qs)
        results[w][name] = {"ranks": ranks, "metrics": m, "config": config, "timing": timing}
        if w == "human":
            print(f"  [{w}] {name:40s} train {m['train']['mrr']:.3f}  val {m['val']['mrr']:.3f}  all {m['all']['mrr']:.3f}  H@1 val {m['val']['hit@1']:.3f}", flush=True)
        else:
            print(f"  [{w}] {name:40s} all {m['all']['mrr']:.3f}  pq {m['pq']['mrr']:.3f}  ruling {m['ruling']['mrr']:.3f} | val {m['val']['mrr']:.3f}", flush=True)

    def rerank_articles(w, pipe, depth, table, beta=1.0, pick="all"):
        """Articles of the pipeline's top-`depth` reordered by the reranker (doc = max over its chunks, or its best
        dense chunk when pick == 'best'); the stage-1 order below. Returns (rankings, mean pairs per query) or None."""
        rk, npairs = {}, []
        for q in sets[w]:
            e = cands[f"{w}:{pipe}"][q.qid]
            docs = e["docs"][:depth]
            sc = []
            for d, _ in docs:
                di = doc_index[d]
                cs = [e["best_chunk"][d]] if pick == "best" else list(e["top_chunks"][d])
                vals = [table.get((q.qid, c)) for c in cs]
                if any(v is None for v in vals):
                    return None
                sc.append(max(vals)); npairs.append(len(cs))
            sc = np.array(sc)
            s1 = np.array([s for _, s in docs])
            fused = sc if beta >= 1 else beta * minmax(sc) + (1 - beta) * minmax(s1)
            order = np.argsort(-fused, kind="stable")
            ranked = [docs[j][0] for j in order]
            seen = set(ranked)
            ranked += [d for d in tails[(w, pipe)][q.qid] if d not in seen]
            rk[q.qid] = ranked[:60]
        return rk, float(np.sum(npairs) / len(sets[w]))

    def rerank_bar(w):
        rk = {}
        for q in sets[w]:
            cs = cands[f"{w}:e5_bm25__rrf03"][q.qid]["chunks"][:30]
            if any((q.qid, c) not in mm for c in cs):
                return None
            best: dict[str, float] = {}
            for c in cs:
                d = doc_ids[int(chunk_doc[c])]
                best[d] = max(best.get(d, -1e9), mm[(q.qid, c)])
            ranked = [d for d, _ in sorted(best.items(), key=lambda kv: -kv[1])]
            seen = set(ranked)
            ranked += [d for d in tails[(w, "e5_bm25__rrf03")][q.qid] if d not in seen]
            rk[q.qid] = ranked[:60]
        return rk

    mm_cfg = {"reranker": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1", "max_length": 512}
    bg_cfg = {"reranker": "BAAI/bge-reranker-v2-m3", "max_length": 512}
    for w in sets:
        print(f"\n== {w} ==", flush=True)
        rk = rerank_bar(w)
        if rk is not None:
            evaluate(w, "e5_bm25__rrf03->mmarco@30chunks", rk, {"first_stage": "exp 03 e5 RRF (reproduced)", "unit": "top-30 chunks", **mm_cfg, "fusion": "reranker only"},
                     {"pairs_per_query": 30, "per_query_s": round(30 * tm_mm.get("s_per_pair", 0), 2)})
        for pipe in pipes:
            for depth in (30, 20):
                out = rerank_articles(w, pipe, depth, mm)
                if out is None:
                    print(f"  [{w}] {pipe}->mmarco@{depth}: pairs missing", flush=True)
                    continue
                rk, npq = out
                pairs_per_q[(w, pipe, depth)] = npq
                cfg = {"first_stage": pipe, "weights": weights_of(pipe), "unit": f"best 3 chunks (z colbert + z e5) of each of the top-{depth} articles", **mm_cfg}
                evaluate(w, f"{pipe}->mmarco@{depth}", rk, {**cfg, "fusion": "reranker only"}, {"pairs_per_query": round(npq, 1), "per_query_s": round(npq * tm_mm.get("s_per_pair", 0), 2)})
                if depth == 30:
                    rk, _ = rerank_articles(w, pipe, depth, mm, beta=BETA)
                    evaluate(w, f"{pipe}->mmarco@{depth}_b{BETA}", rk, {**cfg, "fusion": f"{BETA} minmax(reranker) + {1 - BETA:.1f} minmax(stage 1) (exp-14 value, not re-tuned)"},
                             {"pairs_per_query": round(npq, 1), "per_query_s": round(npq * tm_mm.get("s_per_pair", 0), 2)})
            if w == "human":
                out = rerank_articles(w, pipe, 20, bg, pick="best")
                if out is not None:
                    evaluate(w, f"{pipe}->bge@20", out[0], {"first_stage": pipe, "weights": weights_of(pipe), "unit": "best dense chunk of the top-20 articles", **bg_cfg, "fusion": "reranker only"},
                             {"pairs_per_query": 20, "per_query_s": round(20 * tm_bg.get("s_per_pair", 0), 2)})

    # mined 100-question subsample: bge @20 on the selected pipeline, with the same-questions comparisons
    if sub:
        subq = [q for q in sets["mined"] if q.qid in set(sub)]
        out = rerank_articles("mined", final, 20, bg, pick="best")
        if out is not None:
            rk = {q.qid: out[0][q.qid] for q in subq}
            res = evaluate_save(f"{final}->bge@20__sub100", subq, rk, {"first_stage": final, "unit": "best dense chunk of the top-20 articles", **bg_cfg, "fusion": "reranker only", "questions": "mined subsample 100"},
                                {"pairs_per_query": 20, "per_query_s": round(20 * tm_bg.get("s_per_pair", 0), 2)}, "mined", save=not a.no_save)
            results["mined"][f"{final}->bge@20__sub100"] = {"ranks": ranks_of(res), "metrics": slice_metrics(ranks_of(res), subq), "config": res.config, "timing": res.timing}
            print(f"  [sub100] {final}->bge@20  all {results['mined'][f'{final}->bge@20__sub100']['metrics']['all']['mrr']:.3f}", flush=True)

    # ── references, tests ───────────────────────────────────────────────────
    refs = {k: {"label": v[1], "ranks": ranks_of_file(v[0])} for k, v in REFS_HUMAN.items() if v[0].exists()}
    for v in refs.values():
        v["metrics"] = split_metrics(v["ranks"], sets["human"])
    tests = {"human": {}, "mined": {}, "sub100": {}}
    hq = {"val": [q.qid for q in sets["human"] if q.split == "val"], "train": [q.qid for q in sets["human"] if q.split == "train"], "all": [q.qid for q in sets["human"]]}
    repro = {}
    if "e5_bm25__rrf03->mmarco@30chunks" in results["human"]:
        repro["bar recipe reproduced vs stored bar (human, identical ranks)"] = sum(1 for q in sets["human"] if results["human"]["e5_bm25__rrf03->mmarco@30chunks"]["ranks"][q.qid] == refs["bar"]["ranks"].get(q.qid))
    for name, v in results["human"].items():
        for rk_ in ("bar", "r2_best", "rec_e5_mmarco", "exp17_bge", "exp14_oof") + (("e5_bge",) if "bge" in name else ()):
            for g, qids in hq.items():
                tests["human"][f"{name} vs {refs[rk_]['label']} [{g}]"] = paired(refs[rk_]["ranks"], v["ranks"], qids)
    for g, qids in hq.items():
        for pipe in pipes:
            if f"{pipe}->mmarco@30" in results["human"]:
                tests["human"][f"{pipe}->mmarco@30 vs {pipe} first stage [{g}] (reranker gain)"] = paired(stage1_ranks[("human", pipe)], results["human"][f"{pipe}->mmarco@30"]["ranks"], qids)
            if f"{pipe}->bge@20" in results["human"] and f"{pipe}->mmarco@30" in results["human"]:
                tests["human"][f"{pipe}->bge@20 vs {pipe}->mmarco@30 [{g}]"] = paired(results["human"][f"{pipe}->mmarco@30"]["ranks"], results["human"][f"{pipe}->bge@20"]["ranks"], qids)
        if f"{selected}->mmarco@30" in results["human"] and f"{alt}->mmarco@30" in results["human"]:
            tests["human"][f"{selected}->mmarco@30 vs {alt}->mmarco@30 [{g}]"] = paired(results["human"][f"{alt}->mmarco@30"]["ranks"], results["human"][f"{selected}->mmarco@30"]["ranks"], hq[g])
        if final != selected and f"{final}->mmarco@30" in results["human"] and f"{selected}->mmarco@30" in results["human"]:
            tests["human"][f"{final}->mmarco@30 vs {selected}->mmarco@30 [{g}] (colbert query length)"] = paired(results["human"][f"{selected}->mmarco@30"]["ranks"], results["human"][f"{final}->mmarco@30"]["ranks"], hq[g])
    mq = {"all": [q.qid for q in sets["mined"]], "train": [q.qid for q in sets["mined"] if q.split == "train"], "val": [q.qid for q in sets["mined"] if q.split == "val"]}
    mq.update({sl: [q.qid for q in sets["mined"] if q.meta.get("source") == sl] for sl in SLICES if sl != "faq"})
    bar_m = results["mined"].get("e5_bm25__rrf03->mmarco@30chunks")
    for name, v in results["mined"].items():
        if name.endswith("__sub100"):
            continue
        for g, qids in mq.items():
            if bar_m is not None and name != "e5_bm25__rrf03->mmarco@30chunks":
                tests["mined"][f"{name} vs bar recipe (e5 RRF → mMARCO @30 chunks) [{g}]"] = paired(bar_m["ranks"], v["ranks"], qids)
            pipe = name.split("->")[0]
            if ("mined", pipe) in stage1_ranks and "mmarco@30" in name and "_b" not in name:
                tests["mined"][f"{name} vs {pipe} first stage [{g}] (reranker gain)"] = paired(stage1_ranks[("mined", pipe)], v["ranks"], qids)
    for g, qids in mq.items():
        if f"{selected}->mmarco@20" in results["mined"] and f"{alt}->mmarco@20" in results["mined"]:
            tests["mined"][f"{selected}->mmarco@20 vs {alt}->mmarco@20 [{g}]"] = paired(results["mined"][f"{alt}->mmarco@20"]["ranks"], results["mined"][f"{selected}->mmarco@20"]["ranks"], qids)
        if final != selected and f"{final}->mmarco@30" in results["mined"] and f"{selected}->mmarco@30" in results["mined"]:
            tests["mined"][f"{final}->mmarco@30 vs {selected}->mmarco@30 [{g}] (colbert query length)"] = paired(results["mined"][f"{selected}->mmarco@30"]["ranks"], results["mined"][f"{final}->mmarco@30"]["ranks"], qids)
        if f"{final}->mmarco@20" in results["mined"] and f"{final}->mmarco@30" in results["mined"]:
            tests["mined"][f"{final}->mmarco@20 vs @30 [{g}]"] = paired(results["mined"][f"{final}->mmarco@30"]["ranks"], results["mined"][f"{final}->mmarco@20"]["ranks"], qids)
        if f"{final}->mmarco@30_b{BETA}" in results["mined"]:
            tests["mined"][f"{final}->mmarco@30_b{BETA} vs reranker only [{g}]"] = paired(results["mined"][f"{final}->mmarco@30"]["ranks"], results["mined"][f"{final}->mmarco@30_b{BETA}"]["ranks"], qids)
        if bar_m is not None:
            tests["mined"][f"bar recipe vs its first stage (e5 RRF) [{g}] (reranker gain)"] = paired(stage1_ranks[("mined", "e5_bm25__rrf03")], bar_m["ranks"], qids)
    sub_metrics = {}
    if sub and f"{final}->bge@20__sub100" in results["mined"]:
        subq = [q for q in sets["mined"] if q.qid in set(sub)]
        bge_r = results["mined"][f"{final}->bge@20__sub100"]["ranks"]
        comp = {f"{final}->bge@20": bge_r}
        for name in (f"{final}->mmarco@30", f"{final}->mmarco@20", "e5_bm25__rrf03->mmarco@30chunks"):
            if name in results["mined"]:
                comp[name] = results["mined"][name]["ranks"]
        comp[f"{final} first stage"] = stage1_ranks[("mined", final)]
        comp["e5 RRF first stage"] = stage1_ranks[("mined", "e5_bm25__rrf03")]
        sub_metrics = {k: slice_metrics(v, subq) for k, v in comp.items()}
        subsets = {"all": sub, "pq": [q.qid for q in subq if q.meta["source"] == "pq"], "ruling": [q.qid for q in subq if q.meta["source"] == "ruling"],
                   "val": [q.qid for q in subq if q.split == "val"]}
        for base in [k for k in comp if k != f"{final}->bge@20"]:
            for g, qids in subsets.items():
                tests["sub100"][f"{final}->bge@20 vs {base} [{g}]"] = paired(comp[base], bge_r, qids)

    summary = {"selected": selected, "alt": alt, "final": final, "timing": {"mmarco": tm_mm, "bge": tm_bg}, "pairs_per_query": {f"{k[0]}:{k[1]}@{k[2]}": v for k, v in pairs_per_q.items()},
               "reproduction": repro, "runs": {w: {k: {"metrics": v["metrics"], "config": v["config"], "timing": v["timing"]} for k, v in results[w].items()} for w in sets},
               "sub100": sub_metrics, "refs": {k: {"label": v["label"], "metrics": v["metrics"]} for k, v in refs.items()}, "tests": tests,
               "per_question_human": {q.qid: {"question": q.question, "split": q.split, **{r: results["human"][r]["ranks"][q.qid] for r in results["human"]},
                                              **{f"ref:{k}": refs[k]["ranks"].get(q.qid) for k in ("bar", "r2_best", "rec_e5_mmarco", "exp17_bge", "exp14_oof")}} for q in sets["human"]}}
    (RUNS / "rerank.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))

    T = ["### Corpus B – reranked pipelines, human questions (40: 24 train / 16 val)", "", *HUMAN_HEAD]
    for k in ("bar", "r2_best", "rec_e5_mmarco", "exp17_bge", "e5_bge", "exp14_oof"):
        T.append(fmt_human(f"ref – {refs[k]['label']}", refs[k]["metrics"]))
    for k, v in results["human"].items():
        T.append(fmt_human(k, v["metrics"]))
    T += ["", "### Corpus B – reranked pipelines, mined questions (304; leak-free reception)", "", *MINED_HEAD]
    for k, v in results["mined"].items():
        if not k.endswith("__sub100"):
            T.append(fmt_mined(k, v["metrics"]))
    if sub_metrics:
        T += ["", f"### Mined 100-question stratified subsample (bge-reranker-v2-m3 @20 on `{final}`; every row on the same 100 questions)", "",
              "| run | all (100) MRR / H@1 / R@10 / R@30 | pq | ruling | faq | train | val |", "|---|---|---|---|---|---|---|"]
        for k, v in sub_metrics.items():
            T.append(fmt_mined(k, v))
    for w in ("human", "mined", "sub100"):
        if tests[w]:
            T += ["", f"Paired tests, {w} (Δ = new − base, reciprocal rank):", "", *PAIRED_HEAD]
            for k, t in tests[w].items():
                T.append(fmt_paired(k, t))
    T += ["", "Per-question ranks, human val questions:", "", "| qid | question | bar | r2 best | exp20 rec+e5→mMARCO | " + " | ".join(results["human"]) + " |",
          "|---|---|---:|---:|---:|" + "---:|" * len(results["human"])]
    g_ = lambda x: "–" if x is None else str(x)
    for q in sets["human"]:
        if q.split == "val":
            T.append(f"| {q.qid} | {q.question[:70]} | {g_(refs['bar']['ranks'].get(q.qid))} | {g_(refs['r2_best']['ranks'].get(q.qid))} | {g_(refs['rec_e5_mmarco']['ranks'].get(q.qid))} | "
                     + " | ".join(g_(results["human"][r]["ranks"][q.qid]) for r in results["human"]) + " |")
    if repro:
        T += ["", "Reproduction: " + "; ".join(f"{k}: {v}/40" for k, v in repro.items())]
    (RUNS / "rerank_tables.md").write_text("\n".join(T) + "\n")
    print("\n".join(T[: 12 + len(results["human"]) + len(results["mined"]) + 6]), flush=True)


if __name__ == "__main__":
    main()
