#!/usr/bin/env python3
"""Print the experiment 06 results as markdown tables (one per corpus) from
experiments/results/06_txtai/*.json.  Usage: uv run python results_table.py"""
from __future__ import annotations

import json
from pathlib import Path

from rag_eval.results import RESULTS_DIR

ORDER = ["txtai__bm25_default_tokenizer", "txtai__e5-small__bm25", "txtai__e5-small__dense",
         "txtai__e5-small__hybrid_w0.3", "txtai__e5-small__hybrid_w0.5", "txtai__e5-small__hybrid_w0.7",
         "txtai__e5-small__hybrid_rrf_w0.3", "txtai__e5-small__hybrid_rrf_w0.5", "txtai__e5-small__hybrid_rrf_w0.7",
         "txtai__e5-small__hybrid_bb25_w0.3", "txtai__e5-small__hybrid_bb25_w0.5", "txtai__e5-small__hybrid_bb25_w0.7",
         "txtai__e5-small__hybrid_w0.5+bge-reranker-v2-m3@30"]


def main():
    rows = [json.loads(p.read_text()) for p in sorted((RESULTS_DIR / "06_txtai").glob("*.json"))]
    for corpus in ("A", "B"):
        rs = {r["name"]: r for r in rows if r["corpus"] == corpus}
        if not rs:
            continue
        print(f"\n### Corpus {corpus}\n")
        print("| run | MRR | nDCG@5 | nDCG@10 | H@1 | H@3 | H@5 | H@10 | R@5 | R@10 | latency |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for name in ORDER + sorted(set(rs) - set(ORDER)):
            r = rs.get(name)
            if not r:
                continue
            m, t = r["metrics"], r["timing"]
            lat = f"{t['per_query_ms']:.0f} ms/q" if "per_query_ms" in t else f"{t.get('per_query_s', 0):.1f} s/q"
            print(f"| `{name}` | {m['mrr']:.3f} | {m['ndcg@5']:.3f} | {m['ndcg@10']:.3f} | {m['hit@1']:.3f} | {m['hit@3']:.3f} | "
                  f"{m['hit@5']:.3f} | {m['hit@10']:.3f} | {m['recall@5']:.3f} | {m['recall@10']:.3f} | {lat} |")


if __name__ == "__main__":
    main()
