#!/usr/bin/env python3
"""Markdown tables for the README from experiments/results/14_ltr_fusion/*.json (+ the grid dumps)."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from common14 import CACHE, EXP, EXP_DIR  # noqa: F401

RESULTS_DIR = EXP_DIR.parent / "results" / EXP

BARS = {"A": (0.736, 0.703), "B": (0.570, 0.522), "C": (0.665, 0.703)}   # (val bar, full-set bar) from the leaderboard


def load(corpus: str) -> dict[str, dict[str, dict]]:
    by_method: dict[str, dict[str, dict]] = defaultdict(dict)
    for f in sorted(RESULTS_DIR.glob(f"{corpus}__*.json")):
        r = json.loads(f.read_text())
        name = r["name"]
        base, fold = name.rsplit("__", 1)
        by_method[base][fold] = r
    return by_method


def short_sel(sel: dict) -> str:
    if not sel:
        return ""
    if "train_fold" in sel:
        return f"{short_sel(sel['train_fold'])} / {short_sel(sel['val_fold'])}"
    s = sel.get("fusion", sel.get("method", ""))
    if sel.get("reranker"):
        s += f"+{sel['reranker'].split('-')[0]}@{sel['depth']} β{sel['beta']}"
    if sel.get("fset"):
        s += f" [{sel['fset']}]"
    if sel.get("dense") and sel.get("dense") != "e5":
        s += f" ({sel['dense']})"
    if sel.get("lex") == "doc":
        s += " (lex=doc)"
    return s


def table(corpus: str, prefix: str | None = None) -> str:
    rows = []
    for base, folds in load(corpus).items():
        if prefix and not base.startswith(prefix):
            continue
        if not all(k in folds for k in ("fit-train", "fit-val", "oof")):
            continue
        tr, va, oof = folds["fit-train"]["metrics"], folds["fit-val"]["metrics"], folds["oof"]["metrics"]
        rows.append((base, short_sel(folds["fit-train"]["config"].get("selected", {})),
                     short_sel(folds["fit-val"]["config"].get("selected", {})),
                     tr["train_mrr"], tr["val_mrr"], va["val_mrr"], va["train_mrr"],
                     oof["mrr"], oof["hit@1"], oof["recall@10"], oof.get("ndcg@5", float("nan"))))
    rows.sort(key=lambda r: -r[7])
    vb, fb = BARS[corpus]
    out = [f"| method | selected (train fold) | selected (val fold) | train resub | **val** | val resub | **train (swapped)** | **oof MRR** | oof H@1 | oof R@10 | oof nDCG@5 |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]:.3f} | {r[4]:.3f} | {r[5]:.3f} | {r[6]:.3f} | {r[7]:.3f} | {r[8]:.3f} | {r[9]:.3f} | {r[10]:.3f} |")
    out.append(f"| _bar_ | | | | {vb:.3f} | | | {fb:.3f} | | | |")
    return "\n".join(out)


if __name__ == "__main__":
    for c in (sys.argv[1:] or ["A", "B", "C"]):
        print(f"\n### corpus {c}\n")
        print(table(c))
