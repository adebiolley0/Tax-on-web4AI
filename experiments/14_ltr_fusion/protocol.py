"""Train/val protocol helpers shared by tune_fusion.py and train_ltr.py.

Every question carries ``.split`` ("train"/"val", md5 of its id). A *method* is anything that,
given a set of fitting questions, produces a full ranking for every question. We report:

* ``fit-train``: fitted/selected on train, evaluated on all (the harness prints train and val;
  val is the honest number, train the resubstitution number);
* ``fit-val``  : the swapped fold (fitted on val, train is the honest number);
* ``oof``      : out-of-fold rankings (val from fit-train, train from fit-val) = 2-fold CV over the
  whole question set, comparable with the full-set bars.
"""
from __future__ import annotations

import math
from typing import Callable

import numpy as np

from rag_eval import evaluate_rankings, save_result
from rag_eval.corpora import Question
from common14 import EXP


def per_question_metrics(q: Question, ranked: list[str]) -> tuple[float, float, float, float]:
    """(rr, hit@1, recall@10, ndcg@5) exactly as rag_eval.metrics computes them."""
    exp = set(q.expected)
    first = next((i + 1 for i, d in enumerate(ranked) if d in exp), None)
    rr = 1.0 / first if first else 0.0
    rec10 = len(exp & set(ranked[:10])) / max(1, len(exp))
    rel = {d: 1.0 for d in exp}
    rel.update({d: 0.5 for d in q.secondary if d not in rel})
    dcg = sum(rel.get(d, 0.0) / math.log2(i + 2) for i, d in enumerate(ranked[:5]))
    ideal = sorted(rel.values(), reverse=True)[:5]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return rr, 1.0 if first == 1 else 0.0, rec10, (dcg / idcg if idcg else 0.0)


def split_masks(questions: list[Question]) -> dict[str, np.ndarray]:
    sp = np.array([q.split for q in questions])
    return {"train": sp == "train", "val": sp == "val", "all": np.ones(len(sp), dtype=bool)}


def select_best(scores: np.ndarray, mask: np.ndarray, tiebreak: np.ndarray | None = None,
                cost: np.ndarray | None = None) -> int:
    """Index of the config with the best mean score on ``mask`` (rows = configs, cols = questions);
    ties broken by ``tiebreak`` mean (e.g. nDCG@5) then by lower ``cost`` (e.g. rerank depth)."""
    m = scores[:, mask].mean(1)
    key = m.copy()
    if tiebreak is not None:
        key = key + 1e-4 * tiebreak[:, mask].mean(1)
    if cost is not None:
        key = key - 1e-6 * cost
    return int(np.argmax(key))


def fold_report(name: str, corpus: str, questions: list[Question], fit: Callable[[np.ndarray], object],
                rank: Callable[[object, int], list[str]], describe: Callable[[object], dict], extra_config: dict | None = None,
                save: bool = True, verbose: bool = True) -> dict:
    """Run the 3 reports (fit-train / fit-val / oof) for one method and save them."""
    masks = split_masks(questions)
    params = {sp: fit(masks[sp]) for sp in ("train", "val")}
    rankings = {sp: {q.qid: rank(params[sp], i) for i, q in enumerate(questions)} for sp in ("train", "val")}
    oof = {q.qid: rankings["train" if q.split == "val" else "val"][q.qid] for q in questions}
    out = {}
    for tag, rk, p in (("fit-train", rankings["train"], params["train"]), ("fit-val", rankings["val"], params["val"]),
                       ("oof", oof, None)):
        cfg = dict(extra_config or {})
        cfg["fold"] = tag
        if p is not None:
            cfg["selected"] = describe(p)
        else:
            cfg["selected"] = {"train_fold": describe(params["train"]), "val_fold": describe(params["val"])}
        res = evaluate_rankings(f"{name}__{tag}", corpus, questions, rk, config=cfg)
        if save:
            save_result(EXP, res)
        out[tag] = res
        if verbose:
            print(res.summary(), flush=True)
    m_tr, m_va, m_oof = out["fit-train"].metrics, out["fit-val"].metrics, out["oof"].metrics
    if verbose:
        print(f"    => honest: val(fit-train)={m_tr['val_mrr']:.3f}  train(fit-val)={m_va['train_mrr']:.3f}  "
              f"oof-all={m_oof['mrr']:.3f} (H@1 {m_oof['hit@1']:.3f}, R@10 {m_oof['recall@10']:.3f}) | "
              f"resub: train(fit-train)={m_tr['train_mrr']:.3f} val(fit-val)={m_va['val_mrr']:.3f}", flush=True)
    return out
