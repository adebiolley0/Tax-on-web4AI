"""Split-protocol view of saved runs: train / val metrics recomputed from the stored per-question ranks.

The split is a property of the question id (:func:`rag_eval.corpora.question_split`), so any run
JSON — including ones saved before the protocol existed — can be re-read per half.  Configurations are
chosen on ``train``; the number that counts is ``val``.

CLI::

    python -m rag_eval.splits C [top]        # val-sorted leaderboard over every saved run on corpus C
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rag_eval.corpora import question_split
from rag_eval.results import RESULTS_DIR

SPLITS = ("train", "val")


def split_metrics(per_question: dict) -> dict:
    """``{"train": {...}, "val": {...}}`` with ``n``, ``mrr``, ``hit@1``, ``hit@5``, ``hit@10`` from a
    run's ``per_question`` dict (``rank`` = first expected doc, ``None`` on a miss).  ``hit@10`` is the
    first-hit rate at 10 (equal to recall@10 for single-target questions).  Empty halves are omitted."""
    out = {}
    for sp in SPLITS:
        rows = [v for k, v in per_question.items() if question_split(k) == sp]
        if not rows:
            continue
        n = len(rows)
        out[sp] = {"n": n, "mrr": round(sum(v["rr"] for v in rows) / n, 4),
                   "hit@1": round(sum(1 for v in rows if v["rank"] == 1) / n, 4),
                   "hit@5": round(sum(1 for v in rows if v["rank"] and v["rank"] <= 5) / n, 4),
                   "hit@10": round(sum(1 for v in rows if v["rank"] and v["rank"] <= 10) / n, 4)}
    return out


def split_metrics_file(result_json: Path) -> dict:
    return split_metrics(json.loads(Path(result_json).read_text())["per_question"])


def print_split_leaderboard(corpus: str, top: int = 25, results_dir: Path = RESULTS_DIR) -> None:
    rows = []
    for f in sorted(results_dir.glob(f"*/{corpus}__*.json")):
        r = json.loads(f.read_text())
        m = split_metrics(r["per_question"])
        if "val" not in m or "train" not in m:
            continue
        rows.append((m["val"]["mrr"], m["train"]["mrr"], r["metrics"]["mrr"], f.parent.name, r["name"], m["val"]["n"]))
    rows.sort(reverse=True)
    print(f"{'val MRR':>8s} {'train':>6s} {'all':>6s}  {'experiment':22s} run")
    for v, t, a, exp, name, n in rows[:top]:
        print(f"{v:8.3f} {t:6.3f} {a:6.3f}  {exp[:22]:22s} {name} (val n={n})")


if __name__ == "__main__":
    print_split_leaderboard(sys.argv[1] if len(sys.argv) > 1 else "A", int(sys.argv[2]) if len(sys.argv) > 2 else 25)
