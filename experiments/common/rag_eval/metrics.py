"""Ranking metrics computed at *document* level.

A retrieval system returns, per question, a ranked list of ``doc_id`` values
(already deduplicated: the first occurrence of a document determines its rank).
Use :func:`dedupe_ranked` to collapse chunk-level results.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Iterable, Sequence

from rag_eval.corpora import Question


def dedupe_ranked(doc_ids: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for d in doc_ids:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


@dataclass
class RunResult:
    name: str
    corpus: str
    config: dict
    metrics: dict
    per_question: dict
    timing: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        m = self.metrics
        s = (f"{self.name:60s} MRR={m['mrr']:.3f} nDCG@5={m['ndcg@5']:.3f} "
             f"H@1={m['hit@1']:.3f} H@5={m['hit@5']:.3f} R@10={m['recall@10']:.3f}")
        if "val_mrr" in m:
            s += f" | train MRR={m.get('train_mrr', 0):.3f} val MRR={m['val_mrr']:.3f} (n={m.get('val_n')})"
        return s


def _ndcg(ranked: Sequence[str], rel: dict[str, float], k: int) -> float:
    dcg = sum(rel.get(d, 0.0) / math.log2(i + 2) for i, d in enumerate(ranked[:k]))
    ideal = sorted(rel.values(), reverse=True)[:k]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def evaluate_rankings(
    name: str,
    corpus: str,
    questions: list[Question],
    rankings: dict[str, list[str]],
    config: dict | None = None,
    timing: dict | None = None,
    secondary_weight: float = 0.5,
) -> RunResult:
    """Compute MRR, nDCG@5/10, hit@1/3/5/10, recall@5/10.

    * **MRR / hit@k** – rank of the first *expected* (primary) document.
    * **recall@k** – fraction of expected documents found in top-k, averaged.
    * **nDCG@k** – graded: expected=1.0, secondary=``secondary_weight``.
    """
    per_q: dict = {}
    split_acc: dict = {"train": [], "val": []}
    mrr = 0.0
    hits = {1: 0, 3: 0, 5: 0, 10: 0}
    rec = {5: 0.0, 10: 0.0}
    ndcg = {5: 0.0, 10: 0.0}
    n = len(questions)
    for q in questions:
        ranked = dedupe_ranked(rankings.get(q.qid, []))
        exp = set(q.expected)
        first = next((i + 1 for i, d in enumerate(ranked) if d in exp), None)
        rr = 1.0 / first if first else 0.0
        mrr += rr
        for k in hits:
            if first and first <= k:
                hits[k] += 1
        for k in rec:
            rec[k] += len(exp & set(ranked[:k])) / max(1, len(exp))
        rel = {d: 1.0 for d in exp}
        rel.update({d: secondary_weight for d in q.secondary if d not in rel})
        for k in ndcg:
            ndcg[k] += _ndcg(ranked, rel, k)
        per_q[q.qid] = {"rank": first, "rr": round(rr, 4), "top5": ranked[:5],
                        "expected": q.expected, "split": q.split}
        split_acc[q.split].append((rr, 1.0 if first and first <= 1 else 0.0, 1.0 if first and first <= 5 else 0.0,
                                   len(exp & set(ranked[:10])) / max(1, len(exp))))
    metrics = {
        "mrr": mrr / n,
        "ndcg@5": ndcg[5] / n,
        "ndcg@10": ndcg[10] / n,
        "hit@1": hits[1] / n,
        "hit@3": hits[3] / n,
        "hit@5": hits[5] / n,
        "hit@10": hits[10] / n,
        "recall@5": rec[5] / n,
        "recall@10": rec[10] / n,
        "n_questions": n,
    }
    for sp, rows in split_acc.items():
        if rows:
            m = len(rows)
            metrics[f"{sp}_mrr"] = sum(r[0] for r in rows) / m
            metrics[f"{sp}_hit@1"] = sum(r[1] for r in rows) / m
            metrics[f"{sp}_hit@5"] = sum(r[2] for r in rows) / m
            metrics[f"{sp}_recall@10"] = sum(r[3] for r in rows) / m
            metrics[f"{sp}_n"] = m
    metrics = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in metrics.items()}
    return RunResult(name, corpus, config or {}, metrics, per_q, timing or {})
