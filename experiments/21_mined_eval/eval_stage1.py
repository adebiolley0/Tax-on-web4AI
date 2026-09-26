#!/usr/bin/env python3
"""Part 1 – first stages on the mined sets (+ the human sets for reference): exp-01 BM25 (`bm25_tok01`, exp-13
machinery), exp-13 lexical, exp-14 chunk BM25 leg, whole-document BM25, e5-small dense, fixed convex 0.5 and
RRF60 fusions. Every system is saved per slice; paired tests vs exp-01 BM25 (rag_eval.stats, with max-T over
the family) per slice and pooled. Writes runs/part1_<corpus>.json + .md.
  uv run python ../21_mined_eval/eval_stage1.py --corpus C
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from rag_eval.stats import compare_many
from common21 import (PAIRED_HEADER, RUNS, Stage1, all_questions, as_run, eval_and_save, fmt_paired, load_saved, paired,
                      short_metrics, slices)

SYSTEMS = [("bm25chunk", "exp-14 chunk BM25 leg (exp-01 tokenizer, bm25s)"),
           ("bm25doc", "whole-document BM25 (exp-14 doc leg)"),
           ("e5", "e5-small dense (chunk max)"),
           ("convex05", "fixed convex 0.5 (e5 + chunk BM25, min-max)"),
           ("rrf60", "fixed RRF k=60 (e5 + chunk BM25)")]
LEXICAL = [("bm25_tok01", "exp-01 BM25 (exp-13 machinery, tok01, single field)"),
           ("exp13_lex", "exp-13 lexical (BM25F title boost, tok01+num, per-corpus k1/b)")]
BASE = "bm25_tok01"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    st = Stage1(a.corpus)
    questions = all_questions(a.corpus)
    assert [q.qid for q in questions] == st.qids
    metrics, runs = {}, {}
    for name, desc in SYSTEMS:
        rankings = {}
        for qi, q in enumerate(questions):
            rankings[q.qid] = st.bm25doc_ranking(qi, 60) if name == "bm25doc" else st.doc_ranking({"bm25chunk": "bm25"}.get(name, name), qi, 60)
        res = eval_and_save(name, a.corpus, questions, rankings, {"system": desc, "stage": "first stage"}, save=not a.no_save)
        metrics[name] = {sl: short_metrics(r) for sl, r in res.items()}
        runs[name] = {sl: as_run(r) for sl, r in res.items()}
        print(f"{name:12s} " + "  ".join(f"{sl}={m['mrr']:.3f}" for sl, m in metrics[name].items()), flush=True)
    for name, _ in LEXICAL:
        metrics[name], runs[name] = {}, {}
        for sl in slices(questions):
            r = load_saved(f"{sl}__{name}", a.corpus)
            runs[name][sl] = r
            metrics[name][sl] = {k: r["metrics"][k] for k in short_metrics_keys(r["metrics"])}

    # paired tests vs exp-01 BM25 per slice (all questions of the slice) and on the mined val split
    names = [n for n, _ in LEXICAL + SYSTEMS if n != BASE]
    tests, maxt = {}, {}
    for sl in slices(questions):
        base = runs[BASE][sl]
        cands = [runs[n][sl] for n in names]
        tests[sl] = {n: paired(base, c) for n, c in zip(names, cands)}
        maxt[sl] = dict(zip(names, compare_many(base, cands, n_resamples=10000)))
        if sl == "mined":
            tests["mined_val"] = {n: paired(base, c, split="val") for n, c in zip(names, cands)}
            tests["mined_train"] = {n: paired(base, c, split="train") for n, c in zip(names, cands)}
            maxt["mined_val"] = dict(zip(names, compare_many(base, cands, split="val", n_resamples=10000)))
    out = {"corpus": a.corpus, "metrics": metrics, "tests_vs_" + BASE: tests, "maxT": maxt}
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"part1_{a.corpus}.json").write_text(json.dumps(out, indent=1))

    # markdown
    L = [f"### Part 1 – corpus {a.corpus}: first stages on the mined set ({len(slices(questions)['mined'])} q) and the human set", ""]
    order = [n for n, _ in LEXICAL] + [n for n, _ in SYSTEMS]
    for sl, qs in slices(questions).items():
        L += [f"**{sl}** (n = {len(qs)})", "", "| system | MRR | H@1 | R@10 | R@30 | H@30 | " + PAIRED_HEADER[2:],
              "|---|--:|--:|--:|--:|--:|---|--:|--:|:--|--:|--:|"]
        for n in order:
            m = metrics[n][sl]
            row = f"| {n} | {m['mrr']:.3f} | {m['hit@1']:.3f} | {m['recall@10']:.3f} | {m['recall@30']:.3f} | {m['hit@30']:.3f} | "
            row += (fmt_paired(tests[sl][n]) + f" (max-T p {maxt[sl][n]['p_adj']:.3f})" if n != BASE else "– (baseline) | | | | | ")
            L.append(row + " |")
        L.append("")
    L += ["**mined, val split only** (the protocol's honest half; tests vs exp-01 BM25)", "",
          "| system | MRR val | Δ MRR [95 % CI] | p_t | p_perm | W/L/T | max-T p |", "|---|--:|:--|--:|--:|:--|--:|"]
    for n in order:
        m = metrics[n]["mined"]
        if n == BASE:
            L.append(f"| {n} | {m['val_mrr']:.3f} | – | | | | |"); continue
        t = tests["mined_val"][n]
        L.append(f"| {n} | {m['val_mrr']:.3f} | {t['delta']:+.3f} [{t['ci'][0]:+.3f}, {t['ci'][1]:+.3f}] | {t['p_t']:.3f} | {t['p_perm']:.3f} | "
                 f"{t['wlt'][0]}/{t['wlt'][1]}/{t['wlt'][2]} | {maxt['mined_val'][n]['p_adj']:.3f} |")
    (RUNS / f"part1_{a.corpus}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


def short_metrics_keys(m):
    return [k for k in ("n_questions", "mrr", "hit@1", "hit@5", "recall@10", "hit@10", "recall@30", "hit@30", "train_mrr", "train_n", "val_mrr", "val_n") if k in m]


if __name__ == "__main__":
    main()
