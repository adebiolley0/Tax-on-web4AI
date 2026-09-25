"""Recompute train/val split metrics for existing result files (per-question ranks are stored)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rag_eval.corpora import question_split
from rag_eval.results import RESULTS_DIR


def split_metrics(result_json: Path) -> dict:
    r = json.loads(result_json.read_text())
    out = {}
    for sp in ("train", "val"):
        rows = [v for k, v in r["per_question"].items() if question_split(k) == sp]
        if not rows:
            continue
        n = len(rows)
        out[sp] = {"n": n, "mrr": round(sum(v["rr"] for v in rows) / n, 4),
                   "hit@1": round(sum(1 for v in rows if v["rank"] == 1) / n, 4),
                   "hit@5": round(sum(1 for v in rows if v["rank"] and v["rank"] <= 5) / n, 4),
                   "recall@10": round(sum(1 for v in rows if v["rank"] and v["rank"] <= 10) / n, 4)}
    return out


def leaderboard(corpus: str, top: int = 25) -> None:
    rows = []
    for f in RESULTS_DIR.glob(f"*/{corpus}__*.json"):
        r = json.loads(f.read_text())
        m = split_metrics(f)
        if "val" not in m:
            continue
        rows.append((m["val"]["mrr"], m["train"]["mrr"], r["metrics"]["mrr"], f.parent.name, r["name"], m["val"]["n"]))
    rows.sort(reverse=True)
    print(f"{'val MRR':>8s} {'train':>6s} {'all':>6s}  {'experiment':22s} run")
    for v, t, a, exp, name, n in rows[:top]:
        print(f"{v:8.3f} {t:6.3f} {a:6.3f}  {exp[:22]:22s} {name} (val n={n})")


if __name__ == "__main__":
    leaderboard(sys.argv[1] if len(sys.argv) > 1 else "A", int(sys.argv[2]) if len(sys.argv) > 2 else 25)
