"""Ranking metrics computed at *document* level.

A retrieval system returns, per question id, a ranked list of ``doc_id`` values (chunk hits may be
passed as-is: :func:`dedupe_ranked` keeps the first occurrence of each document, which fixes its rank).

Per question, after the ids in ``Question.exclude`` are removed from the ranking:

* ``rank``   – 1-based rank of the first *expected* (primary) document, ``None`` on a miss;
* ``rr``     – its reciprocal rank (0 on a miss); **MRR** and **hit@k** (``rank <= k``) follow from it;
* **recall@k** – fraction of the expected documents in the top-k;
* **nDCG@k** – graded: expected = 1.0, secondary = ``secondary_weight`` (0.5 unless overridden).

Set-level metrics are means over the questions; ``train_*`` / ``val_*`` (MRR, hit@1, hit@5, recall@10,
n) are the same means over each half of the split protocol.  All floats are rounded to 4 decimals.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Iterable, Sequence

from rag_eval.corpora import Question

HIT_KS = (1, 3, 5, 10)
RECALL_KS = (5, 10)
NDCG_KS = (5, 10)


def dedupe_ranked(doc_ids: Iterable[str]) -> list[str]:
    """Collapse a chunk-level ranking to document level (first occurrence wins)."""
    seen: set[str] = set()
    out: list[str] = []
    for d in doc_ids:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


@dataclass
class RunResult:
    """One evaluated run.  ``per_question[qid] = {"rank", "rr", "top5", "expected", "split"}`` is
    what :mod:`rag_eval.stats` reads back; ``provenance`` is filled by :func:`rag_eval.results.save_result`."""
    name: str
    corpus: str
    config: dict
    metrics: dict
    per_question: dict
    timing: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        m = self.metrics
        s = (f"{self.name:60s} MRR={m['mrr']:.3f} nDCG@5={m['ndcg@5']:.3f} "
             f"H@1={m['hit@1']:.3f} H@5={m['hit@5']:.3f} R@10={m['recall@10']:.3f}")
        if "val_mrr" in m:
            s += f" | train MRR={m.get('train_mrr', 0):.3f} val MRR={m['val_mrr']:.3f} (n={m.get('val_n')})"
        return s


def ndcg_at_k(ranked: Sequence[str], rel: dict[str, float], k: int) -> float:
    """nDCG@k with graded relevance ``rel`` (log2 discount, ideal = sorted grades)."""
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
    """Score ``rankings`` (qid → ranked doc ids; a missing qid counts as an empty ranking) on
    ``questions``; see the module docstring for the metric definitions."""
    if not questions:
        raise ValueError("evaluate_rankings needs at least one question")
    per_q: dict = {}
    split_acc: dict[str, list[tuple[float, float, float, float]]] = {"train": [], "val": []}
    mrr = 0.0
    hits = {k: 0 for k in HIT_KS}
    rec = {k: 0.0 for k in RECALL_KS}
    ndcg = {k: 0.0 for k in NDCG_KS}
    n = len(questions)
    for q in questions:
        ranked = dedupe_ranked(rankings.get(q.qid, []))
        excl = set(q.exclude)
        if excl:
            ranked = [d for d in ranked if d not in excl]
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
            ndcg[k] += ndcg_at_k(ranked, rel, k)
        per_q[q.qid] = {"rank": first, "rr": round(rr, 4), "top5": ranked[:5],
                        "expected": q.expected, "split": q.split}
        split_acc[q.split].append((rr, 1.0 if first and first <= 1 else 0.0, 1.0 if first and first <= 5 else 0.0,
                                   len(exp & set(ranked[:10])) / max(1, len(exp))))
    metrics: dict = {"mrr": mrr / n}
    metrics.update({f"ndcg@{k}": ndcg[k] / n for k in NDCG_KS})
    metrics.update({f"hit@{k}": hits[k] / n for k in HIT_KS})
    metrics.update({f"recall@{k}": rec[k] / n for k in RECALL_KS})
    metrics["n_questions"] = n
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
