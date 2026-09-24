"""Persist experiment results: one JSON per run + a shared leaderboard JSONL."""
from __future__ import annotations

import json
import time
from pathlib import Path

from rag_eval.corpora import REPO_ROOT
from rag_eval.metrics import RunResult

RESULTS_DIR = REPO_ROOT / "experiments" / "results"
LEADERBOARD = RESULTS_DIR / "leaderboard.jsonl"


def save_result(experiment: str, result: RunResult) -> Path:
    d = RESULTS_DIR / experiment
    d.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in result.name)
    p = d / f"{result.corpus}__{safe}.json"
    p.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=1))
    append_leaderboard(experiment, result)
    return p


def append_leaderboard(experiment: str, result: RunResult) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "experiment": experiment, "run": result.name,
           "corpus": result.corpus, **result.metrics, "timing": result.timing, "config": result.config}
    with LEADERBOARD.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def print_leaderboard(corpus: str | None = None, top: int = 40) -> None:
    rows = [json.loads(l) for l in LEADERBOARD.read_text().splitlines() if l.strip()]
    if corpus:
        rows = [r for r in rows if r["corpus"] == corpus]
    # keep latest row per (experiment, run, corpus)
    latest: dict = {}
    for r in rows:
        latest[(r["experiment"], r["run"], r["corpus"])] = r
    rows = sorted(latest.values(), key=lambda r: -r["mrr"])[:top]
    print(f"{'corpus':6s} {'experiment':22s} {'run':52s} {'MRR':>6s} {'nDCG5':>6s} {'H@1':>6s} {'H@5':>6s} {'R@10':>6s}")
    for r in rows:
        print(f"{r['corpus']:6s} {r['experiment'][:22]:22s} {r['run'][:52]:52s} {r['mrr']:6.3f} {r['ndcg@5']:6.3f} "
              f"{r['hit@1']:6.3f} {r['hit@5']:6.3f} {r['recall@10']:6.3f}")


if __name__ == "__main__":
    import sys
    print_leaderboard(sys.argv[1] if len(sys.argv) > 1 else None)
