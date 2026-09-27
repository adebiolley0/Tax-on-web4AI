#!/usr/bin/env python3
"""Evaluate the best pipelines on the stored question sets through rag_eval and save every run as experiment "best".

  cd experiments/14_ltr_fusion && uv run python ../best/evaluate.py --corpus B --sets human,mined
  cd experiments/14_ltr_fusion && uv run python ../best/evaluate.py --corpus C --sets human
  cd experiments/14_ltr_fusion && uv run python ../best/evaluate.py --corpus A
  … --corpus all    (B human + mined, C human, A human)

Cache-only by default (no model is loaded; a missing cached score raises with the question). --allow-scoring lets the
rerankers / encoders fill the caches (torch lock, OMP_NUM_THREADS=4). Results: experiments/results/best/*.json (+ the
leaderboard), runs/eval_<corpus>_<set>.json and runs/tables.md; the per-question ranks are compared with the stored
runs of the experiments that measured the pipelines (exp 22 gate, exp 17 lex13+bge@20, exp 01).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time

import numpy as np

from rag_eval import evaluate_rankings, load_questions_a, load_questions_b, load_questions_c, load_questions_mined, save_result
from rag_eval.corpora import QUESTIONS_B_MINED, QUESTIONS_C_MINED, REPO_ROOT
from rag_eval.results import RESULTS_DIR, build_provenance

from config import EXP_NAME, GATE_WORDS, MMARCO_BETA, MMARCO_DEPTH, RUNS, B_WEIGHTS_SHORT, C_BGE_DEPTH

REFERENCE = {   # stored per-question ranks of the runs that measured the pipelines
    ("B", "human"): RESULTS_DIR / "22_reception_colbert" / "B__gate_T25__mmarco_b0.8__rec_e5.json",
    ("B", "mined"): RESULTS_DIR / "22_reception_colbert" / "B__gate_T25__mmarco_b0.8__rec_e5__mined.json",
    ("C", "human"): RESULTS_DIR / "17_lex_rerank" / "C__lex13_bge_20.json",
    ("A", "human"): RESULTS_DIR / "01_bm25" / "A__doc_stem_stop_qstop_noaccent.json",
}
BARS = {"B": {"val": 0.570, "all": 0.522}, "C": {"val": 0.665, "all": 0.703}, "A": {"val": 0.736, "all": 0.703}}
CONFIG = {
    "B": {"pipeline": "z-score convex fusion (rec BM25F, colbert-fr, e5-small), fixed weights", "weights": B_WEIGHTS_SHORT,
          "gate": f"words ≤ {GATE_WORDS}: → mMARCO @{MMARCO_DEPTH} on best 3 chunks/article, β {MMARCO_BETA}; else rec + e5 (0.5/0.5) un-reranked",
          "source": "22_reception_colbert gate_T25__mmarco_b0.8__rec_e5"},
    "C": {"pipeline": f"exp-13 BM25F (title x8, k1 0.9, b 0.4, tok01+num) → top-{C_BGE_DEPTH} chunks → bge-reranker-v2-m3 (512, score only)",
          "source": "17_lex_rerank lex13+bge@20"},
    "A": {"pipeline": "whole-document BM25, tok01 (stem + stop + question words + accent fold), k1 1.5 b 0.75", "source": "01_bm25 doc|stem+stop+qstop+noaccent"},
}


def split_metrics(res, questions) -> dict:
    ranks = {q: v["rank"] for q, v in res.per_question.items()}
    out = {}
    for sp in ("train", "val", "all"):
        qs = [q for q in questions if sp == "all" or q.split == sp]
        rr = [1.0 / ranks[q.qid] if ranks.get(q.qid) else 0.0 for q in qs]
        out[sp] = {"n": len(qs), "mrr": float(np.mean(rr)) if qs else float("nan"),
                   "hit@1": float(np.mean([1.0 if ranks.get(q.qid) == 1 else 0.0 for q in qs])) if qs else float("nan"),
                   "recall@10": float(np.mean([1.0 if ranks.get(q.qid) and ranks[q.qid] <= 10 else 0.0 for q in qs])) if qs else float("nan")}
    return out


def save_best(res, which: str, corpus: str):
    prov = build_provenance(res)
    if which == "mined":
        f = {"B": QUESTIONS_B_MINED, "C": QUESTIONS_C_MINED}[corpus]
        prov["questions_file"] = str(f.relative_to(REPO_ROOT))
        prov["questions_sha256"] = hashlib.sha256(f.read_bytes()).hexdigest()
    res.provenance = prov
    return save_result(EXP_NAME, res)


def run(corpus: str, which: str, save: bool, allow_scoring: bool, retriever=None):
    qs = {("B", "human"): load_questions_b, ("B", "mined"): lambda: load_questions_mined("B"), ("C", "human"): load_questions_c,
          ("C", "mined"): lambda: load_questions_mined("C"), ("A", "human"): load_questions_a}[(corpus, which)]()
    if retriever is None:
        from pipeline import RetrieverA, RetrieverB, RetrieverC
        retriever = {"A": lambda: RetrieverA(), "B": lambda: RetrieverB(cache_only=not allow_scoring, reception="nomined" if which == "mined" else "full"),
                     "C": lambda: RetrieverC(cache_only=not allow_scoring)}[corpus]()
    elif corpus == "B":
        retriever.set_reception("nomined" if which == "mined" else "full")
    print(f"\n== corpus {corpus}, {which} ({len(qs)} questions) ==", flush=True)
    rankings, per_q_ms, routes = {}, [], {}
    t0 = time.perf_counter()
    for q in qs:
        t1 = time.perf_counter()
        res = retriever.retrieve(q.question, 60, passages=False)
        rankings[q.qid] = res.doc_ids
        per_q_ms.append((time.perf_counter() - t1) * 1000)
        routes[res.route] = routes.get(res.route, 0) + 1
    name = f"pipeline_{corpus}" + ("__mined" if which == "mined" else "")
    timing = {"eval_s": round(time.perf_counter() - t0, 1), "ms_per_query_cached": round(float(np.mean(per_q_ms)), 1),
              "note": "cross-encoder / ColBERT scores from cache; live cost in README"}
    r = evaluate_rankings(name, corpus, qs, rankings, {**CONFIG[corpus], "question_set": which, "reception": getattr(retriever, "reception_variant", None),
                                                       "routes": routes}, timing)
    if save:
        save_best(r, which, corpus)
    m = split_metrics(r, qs)
    ref_path = REFERENCE.get((corpus, which))
    repro = None
    if ref_path and ref_path.exists():
        ref = json.loads(ref_path.read_text())["per_question"]
        same = sum(1 for q in qs if ref.get(q.qid, {}).get("rank") == r.per_question[q.qid]["rank"])
        ref_m = {sp: float(np.mean([ref[q.qid]["rr"] for q in qs if sp == "all" or q.split == sp])) for sp in ("train", "val", "all")}
        repro = {"reference": str(ref_path.relative_to(RESULTS_DIR)), "identical_ranks": same, "n": len(qs), "reference_mrr": ref_m}
    row = {"corpus": corpus, "set": which, "name": name, "n": len(qs), "metrics": m, "full": r.metrics, "timing": timing, "routes": routes, "reproduction": repro}
    print(f"  {name}: train {m['train']['mrr']:.3f} / val {m['val']['mrr']:.3f} / all {m['all']['mrr']:.3f} | H@1 all {m['all']['hit@1']:.3f} "
          f"R@10 all {m['all']['recall@10']:.3f} | {timing['ms_per_query_cached']:.0f} ms/q (cached) | routes {routes}", flush=True)
    if repro:
        print(f"  reproduction vs {repro['reference']}: {same}/{len(qs)} identical ranks; reference MRR val {ref_m['val']:.3f} / all {ref_m['all']:.3f}", flush=True)
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"eval_{corpus}_{which}.json").write_text(json.dumps({**row, "per_question": r.per_question}, ensure_ascii=False, indent=1))
    return row, retriever


def table(rows: list[dict]) -> str:
    L = ["| corpus | question set | n | MRR train | MRR **val** | MRR all | H@1 all | R@10 all | bar (val / all) | identical ranks vs source run |",
         "|---|---|---:|---:|---:|---:|---:|---:|---|---|"]
    for r in rows:
        m, b = r["metrics"], BARS[r["corpus"]]
        rp = r["reproduction"]
        L.append(f"| {r['corpus']} | {r['set']} | {r['n']} | {m['train']['mrr']:.3f} | **{m['val']['mrr']:.3f}** | {m['all']['mrr']:.3f} | {m['all']['hit@1']:.3f} | "
                 f"{m['all']['recall@10']:.3f} | {b['val']:.3f} / {b['all']:.3f} | " + (f"{rp['identical_ranks']}/{rp['n']} (`{rp['reference']}`)" if rp else "–") + " |")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="all", choices=["A", "B", "C", "all"])
    ap.add_argument("--sets", default=None, help="human,mined (default: B human,mined; C human; A human)")
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--allow-scoring", action="store_true", help="let models fill missing cache entries (torch lock!)")
    a = ap.parse_args()
    plan = {"B": ["human", "mined"], "C": ["human"], "A": ["human"]}
    corpora = ["B", "C", "A"] if a.corpus == "all" else [a.corpus]
    rows = []
    for c in corpora:
        retriever = None
        for w in (a.sets.split(",") if a.sets else plan[c]):
            row, retriever = run(c, w, not a.no_save, a.allow_scoring, retriever)
            rows.append(row)
    RUNS.mkdir(exist_ok=True)
    t = table(rows)
    (RUNS / "tables.md").write_text(t + "\n")
    print("\n" + t)


if __name__ == "__main__":
    main()
