#!/usr/bin/env python3
"""Lexical baselines on the mined question sets vs the human sets (round-3 hygiene, part b, step 3).

Two configurations per corpus, both taken from experiment 13's machinery (no torch):

* ``bm25_tok01`` – the round-1 baseline as reproduced by exp 13: exp-01 tokenizer, single field
  (title + heading + body concatenated on B, title + body on C), BM25 k1 1.5 / b 0.75, raw text.
* ``exp13_lex`` – exp 13's final lexical configuration: tok01 + thousand-group number normalisation,
  BM25F (B: title 8 / heading 3 / body 1, k1 1.5, b 0.3/0.3/0.75 on cleaned articles; C: title 8 /
  body 1, k1 0.9, b 0.75/0.4), no cue tokens, strict (non-collapsed) evaluation.

Rankings are computed once for the human ∪ mined questions and evaluated on the human set, the mined
set and its per-source / per-label-basis slices. Every run is saved through
``rag_eval.save_result("18_eval_hygiene", …)`` (per-question ranks included).

  cd experiments/13_lexical_upgrades && uv run python ../18_eval_hygiene/mining/run_baseline.py --corpus B
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP_DIR = HERE.parents[1]
sys.path.insert(0, str(EXP_DIR / "13_lexical_upgrades"))

import numpy as np  # noqa: E402

from rag_eval import evaluate_rankings, save_result  # noqa: E402
from rag_eval.corpora import load_questions_b, load_questions_c  # noqa: E402
from lexical import Tokenizer, build_index, bm25f_matrix, concat_fields, scores_for, to_doc_ranking  # noqa: E402
from run_exp13 import load_corpus, tokenize_corpus, query_weights  # noqa: E402

EXP = "18_eval_hygiene"
CONFIGS = {
    "B": [("bm25_tok01", dict(tok=Tokenizer("01"), clean=False, fields=None, k1=1.5, b=0.75)),
          ("exp13_lex", dict(tok=Tokenizer("01", numbers=True), clean=True, fields={"title": 8.0, "heading": 3.0, "body": 1.0},
                             k1=1.5, b={"title": 0.3, "heading": 0.3, "body": 0.75}))],
    "C": [("bm25_tok01", dict(tok=Tokenizer("01"), clean=False, fields=None, k1=1.5, b=0.75)),
          ("exp13_lex", dict(tok=Tokenizer("01", numbers=True), clean=False, fields={"title": 8.0, "heading": 0.0, "body": 1.0},
                             k1=0.9, b={"title": 0.75, "heading": 0.75, "body": 0.4}))],
}


def short(m: dict) -> dict:
    return {k: m[k] for k in ("n_questions", "mrr", "hit@1", "hit@5", "recall@10", "train_mrr", "train_n", "val_mrr", "val_n") if k in m}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    human = load_questions_b() if a.corpus == "B" else load_questions_c()
    mined = load_questions_b("mined") if a.corpus == "B" else load_questions_c("mined")
    allq = human + mined
    out_path = HERE / f"baseline_results_{a.corpus}.json"
    results = json.loads(out_path.read_text()) if out_path.exists() else {}
    for name, cfg in CONFIGS[a.corpus]:
        t0 = time.perf_counter()
        C = load_corpus(a.corpus, cfg["clean"])
        C.questions = allq
        store = tokenize_corpus(C, cfg["tok"], cfg["clean"])
        index = build_index(store)
        base_fields = {"title": 1, "heading": 1, "body": 1} if a.corpus == "B" else {"title": 1, "body": 1}
        if cfg["fields"] is None:
            M = bm25f_matrix(concat_fields(index, base_fields), {"all": 1.0}, k1=cfg["k1"], b=cfg["b"])
        else:
            M = bm25f_matrix(index, cfg["fields"], k1=cfg["k1"], b=cfg["b"])
        print(f"[{a.corpus}/{name}] {len(C.docs)} docs / {store.n} units / {len(allq)} questions; index built in {time.perf_counter() - t0:.0f}s", flush=True)
        t1 = time.perf_counter()
        rankings = {}
        for q in allq:
            qv = index.query_vector(query_weights(index, cfg["tok"], q.question))
            rankings[q.qid] = to_doc_ranking(scores_for(M, qv), C.unit_doc, top=60)
        timing = {"rank_s": round(time.perf_counter() - t1, 1), "per_query_ms": round(1000 * (time.perf_counter() - t1) / len(allq), 1)}
        config = {"tokenizer": cfg["tok"].key, "clean": cfg["clean"], "fields": cfg["fields"] or base_fields, "k1": cfg["k1"], "b": cfg["b"]}
        res = {}
        slices = [("human", human), ("mined", mined)]
        for src in ("pq", "faq", "ruling"):
            slices.append((f"mined__src_{src}", [q for q in mined if q.meta.get("source") == src]))
        for basis in ("explicit", "bare", "document"):
            slices.append((f"mined__basis_{basis}", [q for q in mined if q.meta.get("label_basis") == basis]))
        for sl, qs in slices:
            if not qs:
                continue
            r = evaluate_rankings(f"{sl}__{name}", a.corpus, qs, rankings, {**config, "questions": sl}, timing)
            if not a.no_save and not sl.startswith("mined__basis"):
                save_result(EXP, r)
            res[sl] = short(r.metrics)
            print(f"   {sl:24s} {json.dumps(res[sl])}", flush=True)
        results[name] = res
        out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1))
        del C, store, index, M, rankings
        gc.collect()


if __name__ == "__main__":
    main()
