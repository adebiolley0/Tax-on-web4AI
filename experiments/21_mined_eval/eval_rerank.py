#!/usr/bin/env python3
"""Part 2 – rerankers on the stratified subsample: fixed convex-0.5 top-20 → mMARCO-MiniLM / bge-reranker-v2-m3
(reranker score only, fused tail below), and on C exp-13 lexical top-20 → bge / mMARCO. Only questions whose 20
candidates are all scored count (coverage reported). Paired tests vs the un-reranked first stage and between
rerankers, per source slice and pooled, plus max-T over the family. Human sets are evaluated too when scored.
  uv run python ../21_mined_eval/eval_rerank.py --corpus C
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from rag_eval import evaluate_rankings
from rag_eval.stats import compare_many
from common21 import (EXP, PAIRED_HEADER, RERANK_DEPTH, RUNS, LexStage1, Stage1, all_questions, as_run, fmt_paired, hit_at,
                      load_rerank_cache, load_subsample, paired, recall_at, save21, short_metrics, SOURCES)

TAG = {"mmarco-minilm": "mmarco", "bge-reranker-v2-m3": "bge"}


def rerank_ranking(cand: np.ndarray, scores: np.ndarray, chunk_doc, doc_ids, tail: list[str], top: int = 60) -> list[str]:
    order = np.argsort(-scores, kind="stable")
    seen, out = set(), []
    for j in order:
        d = doc_ids[int(chunk_doc[cand[j]])]
        if d not in seen:
            seen.add(d); out.append(d)
    for d in tail:
        if d not in seen:
            seen.add(d); out.append(d)
    return out[:top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--depth", type=int, default=RERANK_DEPTH)
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    st = Stage1(a.corpus)
    questions = all_questions(a.corpus)
    byq = {q.qid: q for q in questions}
    sub = [byq[q] for q in load_subsample(a.corpus)]
    human = [q for q in questions if q.meta.get("source") is None]
    caches = {rk: load_rerank_cache(a.corpus, rk) for rk in TAG}
    lx = LexStage1(a.corpus, "exp13_lex") if a.corpus == "C" else None

    # ── systems: name → (question → ranking) over sub ∪ human, plus coverage ──────────────
    systems: dict[str, dict[str, list[str]]] = {}
    desc: dict[str, str] = {}
    pool = sub + human
    systems["convex05"] = {q.qid: st.doc_ranking("convex05", st.q_index[q.qid], 60) for q in pool}
    desc["convex05"] = "fixed convex 0.5 first stage (no reranker)"
    if lx is not None:
        systems["lex13"] = {q.qid: lx.doc_ranking(lx.q_index[q.qid], 60) for q in pool}
        desc["lex13"] = "exp-13 lexical first stage (no reranker)"
    for rk, tag in TAG.items():
        cache = caches[rk]
        if not cache:
            continue
        for first in (["convex05"] + (["lex13"] if lx is not None else [])):
            name = f"{first}+{tag}@{a.depth}"
            rankings = {}
            for q in pool:
                qi = st.q_index[q.qid]
                if first == "convex05":
                    cand = st.candidates(qi, "convex05", a.depth)
                    tail = systems["convex05"][q.qid]
                else:
                    cand = lx.candidates(lx.q_index[q.qid], a.depth)[0]
                    tail = systems["lex13"][q.qid]
                sc = [cache.get((q.qid, int(c))) for c in cand]
                if len(cand) == 0 or any(s is None for s in sc):
                    continue
                rankings[q.qid] = rerank_ranking(cand, np.array(sc, dtype=np.float64), st.chunk_doc, st.doc_ids, tail)
            if rankings:
                systems[name] = rankings
                desc[name] = f"{desc[first].split(' (')[0]} top-{a.depth} → {rk} (reranker score only), fused tail below"

    # questions with every reranked system available (paired comparisons need the same questions)
    rer = [n for n in systems if "+" in n]
    if not rer:
        print("no reranker scores cached yet"); return
    common_sub = [q for q in sub if all(q.qid in systems[n] for n in rer)]
    common_human = [q for q in human if all(q.qid in systems[n] for n in rer)]
    print(f"corpus {a.corpus}: subsample {len(sub)} → {len(common_sub)} with all {len(rer)} reranked systems scored; "
          f"human {len(human)} → {len(common_human)}", flush=True)
    coverage = {n: {"sub": sum(q.qid in systems[n] for q in sub), "human": sum(q.qid in systems[n] for q in human)} for n in systems}

    # ── evaluate per slice, save ─────────────────────────────────────────────
    def slice_sets(qs, prefix):
        out = {prefix: qs}
        for s in SOURCES:
            x = [q for q in qs if q.meta.get("source") == s]
            if len(x) >= 5:
                out[f"{prefix}__src_{s}"] = x
        return out
    metrics, saved = {}, {}
    for n, rankings in systems.items():
        metrics[n], saved[n] = {}, {}
        for sl, qs in list(slice_sets(common_sub, "sub").items()) + ([("human", common_human)] if common_human else []):
            qs = [q for q in qs if q.qid in rankings]
            if not qs:
                continue
            res = evaluate_rankings(f"{sl}__{n}", a.corpus, qs, rankings, {"system": desc[n], "depth": a.depth, "questions": sl, "part": 2})
            res.metrics["recall@30"] = round(recall_at(qs, rankings, 30), 4)
            res.metrics["hit@30"] = round(hit_at(qs, rankings, 30), 4)
            if not a.no_save:
                save21(res, a.corpus, "human" if sl == "human" else "mined")
            metrics[n][sl] = short_metrics(res); saved[n][sl] = as_run(res)
        print(f"  {n:22s} " + "  ".join(f"{sl}={m['mrr']:.3f}" for sl, m in metrics[n].items()), flush=True)

    # ── paired tests ─────────────────────────────────────────────────────────
    pairs = []
    for n in rer:
        base = n.split("+")[0]
        pairs.append((base, n))
    if "convex05+mmarco@20" in systems and "convex05+bge@20" in systems:
        pairs.append(("convex05+mmarco@20", "convex05+bge@20"))
    if "lex13+bge@20" in systems and "convex05+bge@20" in systems:
        pairs.append(("convex05+bge@20", "lex13+bge@20"))
        pairs.append(("convex05", "lex13+bge@20"))
    if "lex13+mmarco@20" in systems and "lex13+bge@20" in systems:
        pairs.append(("lex13+mmarco@20", "lex13+bge@20"))
    tests, maxt = {}, {}
    for sl, qs in list(slice_sets(common_sub, "sub").items()) + ([("human", common_human)] if common_human else []):
        qids = [q.qid for q in qs]
        tests[sl] = {}
        for base, n in pairs:
            ra, rb = saved[base][sl], saved[n][sl]
            tests[sl][f"{n} vs {base}"] = paired(ra, rb, qids)
        if sl == "sub":
            tests["sub_val"] = {f"{n} vs {base}": paired(saved[base]["sub"], saved[n]["sub"], qids, split="val") for base, n in pairs}
        base = saved["convex05"][sl]
        cnames = [n for n in systems if n != "convex05" and sl in saved[n]]
        maxt[sl] = dict(zip(cnames, compare_many(base, [saved[n][sl] for n in cnames], n_resamples=10000))) if cnames else {}
    out = {"corpus": a.corpus, "depth": a.depth, "n_sub": len(sub), "n_sub_scored": len(common_sub), "n_human_scored": len(common_human),
           "coverage": coverage, "descriptions": desc, "metrics": metrics, "tests": tests, "maxT_vs_convex05": maxt}
    (RUNS / f"part2_{a.corpus}.json").write_text(json.dumps(out, indent=1))

    L = [f"### Part 2 – corpus {a.corpus}: rerankers on the stratified subsample ({len(common_sub)} of {len(sub)} questions fully scored)", ""]
    for sl in metrics[next(iter(metrics))]:
        n_sl = metrics["convex05"][sl]["n_questions"]
        L += [f"**{sl}** (n = {n_sl})", "", "| system | MRR | H@1 | R@10 | R@30 | H@30 | MRR val (n) |", "|---|--:|--:|--:|--:|--:|--:|"]
        for n, m in metrics.items():
            if sl in m:
                mm = m[sl]
                L.append(f"| {n} | {mm['mrr']:.3f} | {mm['hit@1']:.3f} | {mm['recall@10']:.3f} | {mm['recall@30']:.3f} | {mm['hit@30']:.3f} | "
                         f"{mm.get('val_mrr', float('nan')):.3f} ({mm.get('val_n', 0)}) |")
        L += ["", "| comparison " + PAIRED_HEADER[1:] + " max-T p |", "|---|:--|--:|--:|:--|--:|--:|--:|"]
        for k, t in tests.get(sl, {}).items():
            n = k.split(" vs ")[0]
            L.append(f"| {k} | {fmt_paired(t)} | {maxt[sl][n]['p_adj']:.3f} |" if n in maxt.get(sl, {}) else f"| {k} | {fmt_paired(t)} | |")
        L.append("")
    if "sub_val" in tests:
        L += ["**subsample, val split only**", "", "| comparison " + PAIRED_HEADER[1:], "|---|:--|--:|--:|:--|--:|--:|"]
        for k, t in tests["sub_val"].items():
            L.append(f"| {k} (n={t['n']}) | {fmt_paired(t)} |")
        L.append("")
    (RUNS / f"part2_{a.corpus}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
