#!/usr/bin/env python3
"""Markdown tables for the README from the saved results of experiment 13.

  uv run python report.py            # all corpora present in runs/*_summary.json
  uv run python report.py C
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rag_eval.results import RESULTS_DIR

RUNS = Path(__file__).parent / "runs"
RES = RESULTS_DIR / "13_lexical_upgrades"


def load_run(corpus: str, name: str) -> dict:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
    return json.loads((RES / f"{corpus}__{safe}.json").read_text())


def row(label: str, m: dict) -> str:
    return (f"| {label} | {m.get('train_mrr', 0):.3f} | {m.get('val_mrr', 0):.3f} | {m['mrr']:.3f} | "
            f"{m.get('train_hit@1', 0):.3f} | {m.get('val_hit@1', 0):.3f} | {m['hit@1']:.3f} | "
            f"{m.get('val_recall@10', 0):.3f} | {m['recall@10']:.3f} |")


HDR = ("| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all |\n"
       "|---|---:|---:|---:|---:|---:|---:|---:|---:|")


def grid_table(grid: list, top: int = 8) -> str:
    rows = sorted(grid, key=lambda r: -r[1])[:top]
    out = ["| run | MRR train | MRR val | MRR all |", "|---|---:|---:|---:|"]
    out += [f"| `{n}` | {t:.3f} | {v:.3f} | {a:.3f} |" for n, t, v, a in rows]
    return "\n".join(out)


def report(corpus: str) -> str:
    S = json.loads((RUNS / f"{corpus}_summary.json").read_text())
    out = [f"### Corpus {corpus}\n", HDR, row(f"baseline `{S['baseline']['name']}`", S["baseline"]["metrics"])]
    st = S["stages"]
    if "fields" in st:
        f = st["fields"]
        out.append(row(f"BM25F best weights on train `{f['grid_best']}`", f["grid_best_metrics"]))
        out.append(row(f"cheap concat best on train `{f['concat_best']}`", f["concat_best_metrics"]))
        out.append(row(f"+ k1/b on train `{f['k1b_best']}`", f["k1b_best_metrics"]))
    if "rm3" in st:
        r = st["rm3"]
        out.append(row(f"RM3 best on train `{r['best']}` (val range over 27 configs {r['val_range'][0]:.3f}–{r['val_range'][1]:.3f}, {r['n_better_val']}/27 above baseline on val)", r["best_metrics"]))
    if "norm" in st:
        n = st["norm"]
        out.append(row(f"tokenizer variant best on train `{n['tokenizer_best']}`", n["tokenizer_best_metrics"]))
        out.append(row(f"cue tokens best on train `{n['cue_best']}`", n["cue_best_metrics"]))
        try:
            out.append(row("region filter (exp 08 style)", load_run(corpus, "norm__region_filter")["metrics"]))
        except FileNotFoundError:
            pass
    if "pmi" in st:
        p = st["pmi"]
        out.append(row(f"PMI expansion best on train `{p['best']}`", p["best_metrics"]))
    if "collapse" in st:
        for name, m in st["collapse"]["runs"]:
            out.append(row(f"`{name}`", m))
    if "best" in st:
        b = st["best"]
        for name, m in b["combos"]:
            out.append(row(f"combo `{name}`", m))
        if b["final"] != b["best_combo"]:
            out.append(row(f"**final** `{b['final']}`", b["final_metrics"]))
    # grids
    for key, title in [("fields", "BM25F / k1-b grid (top 8 by train MRR)"), ("rm3", "RM3 grid (top 8 by train MRR)"),
                       ("norm", "normalisation grid (top 8 by train MRR)"), ("pmi", "PMI grid")]:
        if key in st and "grid" in st[key]:
            out.append(f"\n<details><summary>{title}</summary>\n\n{grid_table(st[key]['grid'])}\n\n</details>")
    if "pmi" in st:
        ex = "; ".join(f"*{t}* → {', '.join(f'{w} ({p})' for w, p in ws)}" for t, ws in st["pmi"]["examples"][:6])
        out.append(f"\nPMI neighbours (examples): {ex}")
    # per-question val wins / losses
    if "per_question" in S:
        rows = [r for r in S["per_question"] if r["split"] == "val"]
        ch = [r for r in rows if (r["base_rank"] or 999) != (r["final_rank"] or 999)]
        out.append(f"\n**Per-question changes on val** (final vs baseline; {len(rows)} val questions, {len(ch)} changed):\n")
        out.append("| qid | question | baseline rank | final rank |\n|---|---|---:|---:|")
        for r in sorted(ch, key=lambda r: ((r["final_rank"] or 999) - (r["base_rank"] or 999))):
            out.append(f"| {r['qid']} | {r['question']} | {r['base_rank'] or '–'} | {r['final_rank'] or '–'} |")
    return "\n".join(out)


if __name__ == "__main__":
    wanted = sys.argv[1:] or [p.stem[0] for p in sorted(RUNS.glob("*_summary.json"))]
    for c in wanted:
        print(report(c)); print()
