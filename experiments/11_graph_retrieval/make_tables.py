#!/usr/bin/env python3
"""Render the README results tables from summary_<tag>.json + results_grid_<tag>.csv."""
from __future__ import annotations

import csv
import json
import sys

from common11 import HERE

METHODS = ["first_stage", "expand", "expand_sel", "ppr", "prior", "collapse", "expand_sel+collapse", "stack", "stack+collapse"]


def oracle(tag: str) -> dict:
    rows = list(csv.DictReader((HERE / f"results_grid_{tag}.csv").open()))
    best: dict = {}
    for r in rows:
        base, rest = r["name"].split("+", 1)
        meth = rest.split("[")[0]
        k = (base, meth)
        if k not in best or float(r["val_mrr"]) > float(best[k]["val_mrr"]):
            best[k] = r
    return best


def table(tag: str, bases: list[str], methods: list[str] | None = None) -> str:
    s = json.loads((HERE / f"summary_{tag}.json").read_text())
    orc = oracle(tag)
    methods = methods or METHODS
    out = ["| run | train MRR | **val MRR** | all MRR | hit@1 (all / val) | recall@10 (all / val) | val-oracle MRR |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for base in bases:
        for r in s["runs"]:
            c = r["config"]
            name = r["name"].split(":", 1)[-1]
            if c.get("base") != base or c.get("method") not in methods or "__" in name:
                continue
            meth = c["method"]
            o = orc.get((base, meth))
            ov = f"{float(o['val_mrr']):.3f}" if o else "–"
            bold = "**" if meth == "first_stage" else ""
            out.append(f"| {bold}{name}{bold} | {r['train_mrr']:.3f} | **{r['val_mrr']:.3f}** | {r['mrr']:.3f} | "
                       f"{r['hit@1']:.3f} / {r['val_hit@1']:.3f} | {r['recall@10']:.3f} / {r['val_recall@10']:.3f} | {ov} |")
    return "\n".join(out)


def ablation(tag: str, base: str) -> str:
    s = json.loads((HERE / f"summary_{tag}.json").read_text())
    rows = [r for r in s["runs"] if r["config"].get("base") == base and r["config"].get("ablation")]
    base_row = next(r for r in s["runs"] if r["name"].split(":", 1)[-1] == base)
    full = next(r for r in s["runs"] if r["config"].get("base") == base and r["config"].get("method") == "expand" and "__" not in r["name"])
    out = [f"| edge type | only this type: train / val | without it: train / val |", "|---|---:|---:|",
           f"| *(baseline {base})* | {base_row['train_mrr']:.3f} / {base_row['val_mrr']:.3f} | |",
           f"| *(all types: {full['name'].split('+',1)[1]})* | {full['train_mrr']:.3f} / {full['val_mrr']:.3f} | |"]
    types = []
    for r in rows:
        t = r["name"].split("__only_")[-1] if "__only_" in r["name"] else r["name"].split("__without_")[-1]
        if t not in types:
            types.append(t)
    for t in types:
        only = next((r for r in rows if r["name"].endswith(f"__only_{t}")), None)
        without = next((r for r in rows if r["name"].endswith(f"__without_{t}")), None)
        o = f"{only['train_mrr']:.3f} / {only['val_mrr']:.3f}" if only else "–"
        w = f"{without['train_mrr']:.3f} / {without['val_mrr']:.3f}" if without else "–"
        out.append(f"| {t} | {o} | {w} |")
    return "\n".join(out)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("all", "B"):
        print("### B_raw\n"); print(table("B_raw", ["bm25", "dense", "rrf"]))
        print("\n### B_clean\n"); print(table("B_clean", ["bm25", "dense", "rrf"]))
        print("\n### ablation B rrf\n"); print(ablation("B_raw", "rrf"))
        print("\n### ablation B dense\n"); print(ablation("B_raw", "dense"))
    if what in ("all", "C"):
        print("\n### C\n"); print(table("C", ["bm25", "dense", "rrf", "convex0.5"]))
        print("\n### ablation C convex0.5\n"); print(ablation("C", "convex0.5"))
        print("\n### ablation C bm25\n"); print(ablation("C", "bm25"))
