#!/usr/bin/env python3
"""Rebuild the exp-01 BM25 (`bm25_tok01`) and the exp-13 final lexical configuration (`exp13_lex`) for
human + mined questions with experiment 13's machinery (as 18_eval_hygiene/mining/run_baseline.py), keep the
top-200 units per question (+ reranker texts for the top-60 units of exp13_lex on C) and save the runs.
No torch, no lock.  uv run python ../21_mined_eval/build_lexical.py --corpus C
"""
from __future__ import annotations

import argparse
import gc
import json
import time

import numpy as np

from common21 import CACHE, all_questions, eval_and_save, short_metrics
from lexical import Tokenizer, build_index, bm25f_matrix, concat_fields, scores_for, to_doc_ranking
from run_exp13 import load_corpus, tokenize_corpus, query_weights

CONFIGS = {
    "B": [("bm25_tok01", dict(tok=Tokenizer("01"), clean=False, fields=None, k1=1.5, b=0.75)),
          ("exp13_lex", dict(tok=Tokenizer("01", numbers=True), clean=True, fields={"title": 8.0, "heading": 3.0, "body": 1.0},
                             k1=1.5, b={"title": 0.3, "heading": 0.3, "body": 0.75}))],
    "C": [("bm25_tok01", dict(tok=Tokenizer("01"), clean=False, fields=None, k1=1.5, b=0.75)),
          ("exp13_lex", dict(tok=Tokenizer("01", numbers=True), clean=False, fields={"title": 8.0, "heading": 0.0, "body": 1.0},
                             k1=0.9, b={"title": 0.75, "heading": 0.75, "body": 0.4}))],
}
TOP_UNITS = 200
TEXT_UNITS = 60


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--configs", default="bm25_tok01,exp13_lex")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    allq = all_questions(a.corpus)
    summary = {}
    for name, cfg in CONFIGS[a.corpus]:
        if name not in a.configs.split(","):
            continue
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
        print(f"[{a.corpus}/{name}] {len(C.docs)} docs / {store.n} units / {len(allq)} q; index {time.perf_counter()-t0:.0f}s", flush=True)
        doc_index = {d.doc_id: i for i, d in enumerate(C.docs)}
        unit_doc = np.array([doc_index[d] for d in C.unit_doc], dtype=np.int64)
        nq = len(allq)
        top_units = np.full((nq, TOP_UNITS), -1, dtype=np.int64)
        top_scores = np.zeros((nq, TOP_UNITS), dtype=np.float32)
        rankings = {}
        t1 = time.perf_counter()
        for qi, q in enumerate(allq):
            sc = scores_for(M, index.query_vector(query_weights(index, cfg["tok"], q.question)))
            k = min(TOP_UNITS, len(sc))
            cand = np.argpartition(-sc, k - 1)[:k]
            cand = cand[np.argsort(-sc[cand], kind="stable")]
            top_units[qi], top_scores[qi] = cand, sc[cand]
            rankings[q.qid] = to_doc_ranking(sc, C.unit_doc, top=60)
        query_ms = 1000 * (time.perf_counter() - t1) / nq
        config = {"stage": "lexical (exp-13 machinery)", "tokenizer": cfg["tok"].key, "clean": cfg["clean"],
                  "fields": cfg["fields"] or base_fields, "k1": cfg["k1"], "b": cfg["b"]}
        res = eval_and_save(name, a.corpus, allq, rankings, config, {"query_ms": round(query_ms, 1)}, save=not a.no_save)
        summary[name] = {sl: short_metrics(r) for sl, r in res.items()}
        for sl, r in res.items():
            print(f"   {sl:22s} {json.dumps(short_metrics(r))}", flush=True)
        same = False
        if a.corpus == "C":
            z = np.load(CACHE / "C_stage1.npz", allow_pickle=False) if (CACHE / "C_stage1.npz").exists() else None
            if z is not None:
                same = bool(np.array_equal(z["chunk_doc"].astype(np.int64), unit_doc))
                print(f"   unit→doc map identical to stage-1 chunk→doc map: {same}", flush=True)
            else:
                z14 = np.load(CACHE.parent.parent / "14_ltr_fusion" / "cache" / "C_stage1.npz", allow_pickle=False)
                same = bool(np.array_equal(z14["chunk_doc"].astype(np.int64), unit_doc))
                print(f"   unit→doc map identical to exp-14 chunk→doc map: {same}", flush=True)
        texts = {}
        if a.corpus == "C" and name == "exp13_lex":
            for qi in range(nq):
                for u in top_units[qi][:TEXT_UNITS]:
                    u = int(u)
                    if u >= 0 and u not in texts:
                        texts[u] = f"{C.raw_fields['title'][u]}\n\n{C.raw_fields['body'][u]}"     # == Chunk.text (prefix_title)
            (CACHE / f"{a.corpus}_lex_{name}_texts.json").write_text(json.dumps({str(k): v for k, v in texts.items()}, ensure_ascii=False))
        np.savez(CACHE / f"{a.corpus}_lex_{name}.npz", unit_doc=unit_doc, top_units=top_units, top_scores=top_scores)
        (CACHE / f"{a.corpus}_lex_{name}.json").write_text(json.dumps(
            {"qids": [q.qid for q in allq], "doc_ids": [d.doc_id for d in C.docs], "config": config,
             "same_units_as_exp14": same, "query_ms": round(query_ms, 1), "n_texts": len(texts)}, ensure_ascii=False))
        print(f"   saved cache/{a.corpus}_lex_{name}.npz ({time.perf_counter()-t0:.0f}s)", flush=True)
        del C, store, index, M, rankings
        gc.collect()
    (CACHE / f"{a.corpus}_lexical_summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
