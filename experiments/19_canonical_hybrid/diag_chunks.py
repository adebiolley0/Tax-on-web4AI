#!/usr/bin/env python3
"""Diagnostic (cache only, no new reranker pairs): does the candidate *chunk* choice explain the
gap to exp 17? exp 17 reranks the top-20 lexical chunks (several per document); this experiment
reranks one chunk per document – the best *fused* chunk. For every candidate document of a
variant, take the max reranker score over all its chunks that have a cached score (this run's
pairs + exp 17's lexical top-50 pairs, both raw text, 512 tokens) and re-evaluate.

  cd experiments/17_lex_rerank && ../14_ltr_fusion/.venv/bin/python ../19_canonical_hybrid/diag_chunks.py
"""
from __future__ import annotations

import json

import numpy as np

from rag_eval import load_questions_c, load_corpus_c, fixed_chunks, evaluate_rankings, save_result

from common19 import CACHE, EXP, EXP17_CACHE, RUNS, REFS, sha1, per_question_ranks, split_metrics_from_ranks, paired_tests
from retrieve import RERANKED, VARIANTS


def main():
    questions = load_questions_c()
    qidx = {q.qid: i for i, q in enumerate(questions)}
    cands = json.loads((CACHE / "candidates.json").read_text())
    pre = json.loads((CACHE / "pre_rankings.json").read_text())
    scores = json.loads((CACHE / "rerank_scores.json").read_text())
    docs = load_corpus_c(max_chars=200_000)
    raw = fixed_chunks(docs, 1200, 100, prefix_title=True)
    z17 = np.load(EXP17_CACHE / "C_rerank_bge-reranker-v2-m3.npz", allow_pickle=False)
    # per (question, doc): all cached chunk scores (exp 17 lexical top-50 chunks + this run's chunks)
    by_qd: dict[tuple[int, str], list[float]] = {}
    for q, c, s in zip(z17["q_idx"], z17["chunk_idx"], z17["score"]):
        by_qd.setdefault((int(q), raw[int(c)].doc_id), []).append(float(s))
    n_extra = 0
    out = {}
    for name in RERANKED:
        text = VARIANTS[name][0]
        rankings, n_multi = {}, 0
        for q in questions:
            qi = qidx[q.qid]
            lst = cands[name][q.qid]
            sc = []
            for c in lst:
                own = scores[f"{qi}|{c['sha']}"]
                others = by_qd.get((qi, c["doc"]), []) if text == "raw" else []
                if others:
                    n_multi += 1
                sc.append(max([own] + others))
            order = np.argsort(-np.asarray(sc), kind="stable")
            ranked = [lst[j]["doc"] for j in order]
            seen = set(ranked)
            for d in pre[name][q.qid]:
                if d not in seen:
                    seen.add(d); ranked.append(d)
            rankings[q.qid] = ranked[:50]
        res = evaluate_rankings(f"diag_maxchunk__{name}", "C", questions, rankings,
                                {"diagnostic": "max reranker score over cached chunks per candidate doc (own + exp-17 lexical top-50 chunks)",
                                 "variant": name, "text": text})
        save_result(EXP, res)
        out[name] = {"metrics": split_metrics_from_ranks({k: v["rank"] for k, v in res.per_question.items()}, questions),
                     "docs_with_extra_chunks": n_multi}
        print(f"  {name:24s} val {res.metrics['val_mrr']:.3f} H@1 {res.metrics['val_hit@1']:.3f} | all {res.metrics['mrr']:.3f} H@1 {res.metrics['hit@1']:.3f} "
              f"({n_multi} candidate docs had extra cached chunks)", flush=True)
        if name == "baseline":
            ref = per_question_ranks(REFS["round2_best"][0])
            val_q = [q.qid for q in questions if q.split == "val"]
            rr = lambda r: np.array([1.0 / r[x] if r.get(x) else 0.0 for x in val_q])
            out[name]["test_vs_round2_best_val"] = paired_tests(rr({k: v["rank"] for k, v in res.per_question.items()}), rr(ref))
    (RUNS / "diag_chunks.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
