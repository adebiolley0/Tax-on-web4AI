#!/usr/bin/env python3
"""Stage 1 – rebuild experiment 13's recommended lexical ranking (per corpus) and cache the
top-200 units per question with their BM25F scores and reranker texts.

  ../14_ltr_fusion/.venv/bin/python build_lexical.py --corpus B
  ../14_ltr_fusion/.venv/bin/python build_lexical.py --corpus C

Checks: the document ranking must reproduce the per-question ranks saved by exp 13
(results/13_lexical_upgrades/<corpus>__combo__fields_tok01_num_cues.json); on C the unit
indices must coincide with the chunk indices of experiment 14 (same docs, same chunker) so
that the cached bge-reranker scores can be reused.
"""
from __future__ import annotations

import argparse
import json
import re
import time

import numpy as np

from rag_eval import evaluate_rankings, save_result

from common17 import (CACHE, EXP, EXP14_CACHE, LEX_CONFIG, TOP_UNITS, BARS, b_code_cues, per_question_ranks)
from lexical import Tokenizer, build_index, bm25f_matrix, scores_for, to_doc_ranking, REGION_TOKEN, split_line
from run_exp13 import load_corpus, tokenize_corpus, query_weights
from cleanup import region_of_code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    cfg = LEX_CONFIG[a.corpus]
    tok = Tokenizer(**cfg["tokenizer"])
    t0 = time.perf_counter()
    C = load_corpus(a.corpus, cfg["clean_b"])
    t_load = time.perf_counter() - t0
    print(f"corpus {C.name}: {len(C.docs)} docs / {len(C.unit_doc)} units / {len(C.questions)} questions ({t_load:.0f}s)", flush=True)
    t0 = time.perf_counter()
    store = tokenize_corpus(C, tok, cfg["clean_b"])
    if cfg["doctype_w"] or cfg["region_w"]:          # B: code-family / region cue field (exp 13 stage 4b)
        cue_tokens = []
        for u in range(store.n):
            meta = C.unit_meta[u]
            code = meta.get("code", "")
            toks = [REGION_TOKEN[r] for r in region_of_code(code).split(",") if r in REGION_TOKEN]
            toks.append("dt" + re.sub(r"_(wal|bxl|vla)$", "", code))
            cue_tokens.append(toks)
        store.add_field("cue", cue_tokens)
    index = build_index(store)
    M = bm25f_matrix(index, cfg["weights"], k1=cfg["k1"], b=cfg["b"])
    t_index = time.perf_counter() - t0
    print(f"  index: {index.n} units, V={index.V}, {M.nnz/1e6:.1f}M nonzeros ({t_index:.0f}s)", flush=True)

    doc_index = {d.doc_id: i for i, d in enumerate(C.docs)}
    unit_doc = np.array([doc_index[d] for d in C.unit_doc], dtype=np.int64)
    nq = len(C.questions)
    top_units = np.full((nq, TOP_UNITS), -1, dtype=np.int64)
    top_scores = np.zeros((nq, TOP_UNITS), dtype=np.float32)
    rankings = {}
    t0 = time.perf_counter()
    for qi, q in enumerate(C.questions):
        w = query_weights(index, tok, q.question)
        if cfg["doctype_w"]:
            for dt in b_code_cues(q.question):
                w[dt] = w.get(dt, 0) + cfg["doctype_w"]
        sc = scores_for(M, index.query_vector(w))
        k = min(TOP_UNITS, len(sc))
        cand = np.argpartition(-sc, k - 1)[:k]
        cand = cand[np.argsort(-sc[cand], kind="stable")]
        top_units[qi], top_scores[qi] = cand, sc[cand]
        rankings[q.qid] = to_doc_ranking(sc, C.unit_doc)
    t_query = (time.perf_counter() - t0) / nq
    print(f"  {nq} queries, {t_query*1000:.0f} ms/query", flush=True)

    # exp-13 reproduction check
    name = f"lex13__{a.corpus}"
    res = evaluate_rankings(name, a.corpus, C.questions, rankings,
                            {"stage": "lexical (exp 13 final config)", **{k: v for k, v in cfg.items()}},
                            {"index_s": round(t_index, 1), "query_ms": round(t_query * 1000, 2)})
    print(f"  {name}: {split_line(res)}", flush=True)
    ref = per_question_ranks(BARS[a.corpus]["lex13"])
    diff = [(qid, ref[qid], res.per_question[qid]["rank"]) for qid in ref if ref[qid] != res.per_question[qid]["rank"]]
    print(f"  reproduction of exp 13 per-question ranks: {len(ref) - len(diff)}/{len(ref)} identical" + (f"; differences {diff[:10]}" if diff else ""), flush=True)
    if not a.no_save:
        save_result(EXP, res)

    # unit index == exp-14 chunk index on C (same docs, same chunker)?
    if a.corpus == "C":
        z = np.load(EXP14_CACHE / "C_stage1.npz", allow_pickle=False)
        meta14 = json.loads((EXP14_CACHE / "C_stage1.json").read_text())
        same_docs = meta14["doc_ids"] == [d.doc_id for d in C.docs]
        same_units = len(z["chunk_doc"]) == len(unit_doc) and bool(np.array_equal(z["chunk_doc"], unit_doc))
        print(f"  exp-14 alignment: same doc order {same_docs}, same unit→doc map {same_units}", flush=True)
        assert same_docs and same_units, "unit indices do not match exp 14 chunk indices"

    # reranker texts for the cached units
    texts = {}
    for qi in range(nq):
        for u in top_units[qi]:
            u = int(u)
            if u < 0 or u in texts:
                continue
            if a.corpus == "C":
                texts[u] = f"{C.raw_fields['title'][u]}\n\n{C.raw_fields['body'][u]}"        # == Chunk.text of fixed_chunks(prefix_title=True)
            else:
                hp = C.unit_meta[u].get("heading_path") or []
                texts[u] = f"{C.raw_fields['title'][u]}\n" + (" > ".join(hp) + "\n" if hp else "") + "\n" + C.raw_fields["body"][u]
    CACHE.mkdir(exist_ok=True)
    np.savez(CACHE / f"{a.corpus}_lex.npz", unit_doc=unit_doc, top_units=top_units, top_scores=top_scores)
    (CACHE / f"{a.corpus}_lex.json").write_text(json.dumps(
        {"qids": [q.qid for q in C.questions], "doc_ids": [d.doc_id for d in C.docs], "config": cfg,
         "timing": {"load_s": round(t_load, 1), "index_s": round(t_index, 1), "query_ms": round(t_query * 1000, 2)},
         "metrics": res.metrics}, ensure_ascii=False, indent=1))
    (CACHE / f"{a.corpus}_lex_texts.json").write_text(json.dumps({str(k): v for k, v in texts.items()}, ensure_ascii=False))
    print(f"  saved cache/{a.corpus}_lex.npz ({len(texts)} unit texts)", flush=True)


if __name__ == "__main__":
    main()
