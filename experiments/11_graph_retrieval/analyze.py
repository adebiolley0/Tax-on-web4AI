#!/usr/bin/env python3
"""Per-question view of what the graph changed: rank of the first expected document under the
baseline vs the selected graph runs, per split. Prints a markdown table for the README.

  uv run python analyze.py --corpus B --runs rrf,rrf+expand[k30,sum,h1,a0.3],rrf+ppr[k10,b0.5,a0.3]
"""
from __future__ import annotations

import argparse
import json

from rag_eval.results import RESULTS_DIR
from common11 import EXP


def load_run(corpus: str, name: str) -> dict:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
    return json.loads((RESULTS_DIR / EXP / f"{corpus}__{safe}.json").read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--runs", required=True)
    a = ap.parse_args()
    runs = a.runs.split(";")
    data = {r: load_run(a.corpus, r) for r in runs}
    qids = list(data[runs[0]]["per_question"])
    print("| q | split | " + " | ".join(runs) + " |")
    print("|---|---|" + "---|" * len(runs))
    for q in qids:
        cells = []
        base = data[runs[0]]["per_question"][q]["rank"]
        for r in runs:
            rk = data[r]["per_question"][q]["rank"]
            mark = "" if r == runs[0] or rk == base else (" ↑" if (rk or 999) < (base or 999) else " ↓")
            cells.append(f"{rk if rk else '>50'}{mark}")
        print(f"| {q} | {data[runs[0]]['per_question'][q]['split']} | " + " | ".join(cells) + " |")
    for r in runs:
        m = data[r]["metrics"]
        print(f"\n{r}: all MRR {m['mrr']:.3f} | train {m['train_mrr']:.3f} | val {m['val_mrr']:.3f} | H@1 {m['hit@1']:.3f} | R@10 {m['recall@10']:.3f}")


if __name__ == "__main__":
    main()
