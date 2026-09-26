#!/usr/bin/env python3
"""Paired tests of the pre-reranker ablations on the 697 mined corpus-C questions (exp 18b), overall
and per source slice (faq / pq / ruling), each component against the fusion baseline and the full
stack against the baseline. Writes runs/mined_tests.json and runs/mined_tables.md.

  cd experiments/17_lex_rerank && ../14_ltr_fusion/.venv/bin/python ../19_canonical_hybrid/mined_stats.py
"""
from __future__ import annotations

import json

import numpy as np

from rag_eval import load_questions_mined
from rag_eval.results import RESULTS_DIR, safe_name

from common19 import EXP, RUNS, paired_tests

PAIRS = [("+quality", "baseline"), ("+zoning_only", "baseline"), ("+canon_only", "baseline"), ("+facets_only", "baseline"),
         ("+canon_twin_only", "baseline"), ("full", "baseline"), ("full", "+quality+zoning+canon"), ("baseline", "lex_raw")]


def load(name: str) -> dict:
    return json.loads((RESULTS_DIR / EXP / f"C__{safe_name('mined__pre__' + name)}.json").read_text())["per_question"]


def main():
    qs = load_questions_mined("C")
    src = {q.qid: q.meta["source"] for q in qs}
    runs = {n: load(n) for n in {a for p in PAIRS for a in p}}
    out, lines = {}, ["| comparison (B − A) | slice | n | MRR A | MRR B | Δ | wins / losses / ties | paired t p | sign-flip p | sign test p | 95 % CI |",
                      "|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|"]
    for b, a in PAIRS:
        for sl in ("all", "faq", "pq", "ruling"):
            qids = [q.qid for q in qs if sl == "all" or src[q.qid] == sl]
            ra = np.array([runs[a][q]["rr"] for q in qids]); rb = np.array([runs[b][q]["rr"] for q in qids])
            t = paired_tests(rb, ra)
            out[f"{b} vs {a} [{sl}]"] = t
            p = lambda v: "–" if v is None else f"{v:.3f}"
            lines.append(f"| {b} vs {a} | {sl} | {len(qids)} | {ra.mean():.3f} | {rb.mean():.3f} | {t['mean_diff']:+.3f} | {t['wins']} / {t['losses']} / {t['ties']} | "
                         f"{p(t.get('p_t'))} | {p(t.get('p_perm'))} | {p(t.get('p_sign'))} | [{t['ci95'][0]:+.3f}, {t['ci95'][1]:+.3f}] |")
    RUNS.mkdir(exist_ok=True)
    (RUNS / "mined_tests.json").write_text(json.dumps(out, indent=1))
    (RUNS / "mined_tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
