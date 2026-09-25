#!/usr/bin/env python3
"""Print the README results tables from experiments/results/12_sparse_colbert/*.json
(latest file per run name; train / val / all MRR, hit@1, recall@10, timings)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rag_eval.results import RESULTS_DIR

D = RESULTS_DIR / "12_sparse_colbert"


def rows(corpus: str):
    out = []
    for f in sorted(D.glob(f"{corpus}__*.json")):
        r = json.loads(f.read_text())
        m, t = r["metrics"], r.get("timing", {})
        out.append({"run": r["name"], "val": m.get("val_mrr", 0), "train": m.get("train_mrr", 0), "all": m["mrr"],
                    "ndcg5": m["ndcg@5"], "h1": m["hit@1"], "r10": m["recall@10"],
                    "enc": t.get("encode_docs_s"), "q": t.get("maxsim_per_query_s") or t.get("search_s"),
                    "rr": t.get("rerank50_encode_s_per_query"), "cfg": r["config"]})
    return out


def table(corpus: str, prefix: str | None = None, sort: bool = True):
    rs = [r for r in rows(corpus) if prefix is None or r["run"].startswith(prefix)]
    if sort:
        rs.sort(key=lambda r: -r["val"])
    print(f"| run | val MRR | train MRR | all MRR | nDCG@5 | H@1 | R@10 |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for r in rs:
        print(f"| `{r['run']}` | **{r['val']:.3f}** | {r['train']:.3f} | {r['all']:.3f} | {r['ndcg5']:.3f} | {r['h1']:.3f} | {r['r10']:.3f} |")


if __name__ == "__main__":
    corpus = sys.argv[1] if len(sys.argv) > 1 else "A"
    prefix = sys.argv[2] if len(sys.argv) > 2 else None
    table(corpus, prefix)
