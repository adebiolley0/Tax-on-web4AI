#!/usr/bin/env python3
"""Stage A – ingestion layer over corpus C (no torch): metadata, quality filter, boilerplate
zoning, canonical works, the two chunkings (raw = exp 09/14/17 chunks; zoned) and the exp-13
lexical leg (BM25F, tok01+num, title ×8, k1 0.9, b 0.4) for both text versions.

  cd experiments/17_lex_rerank && ../14_ltr_fusion/.venv/bin/python ../19_canonical_hybrid/ingest.py

Writes cache/: docs_meta.json, meta.json, chunks.npz (chunk→doc maps, zoned→raw map),
zoned_changed_texts.json, lex_raw.npz, lex_zoned.npz, facets.json.
"""
from __future__ import annotations

import gc
import json
import pickle
import time
from collections import Counter

import numpy as np

from rag_eval import load_corpus_c, load_questions_c, fixed_chunks
from rag_eval.corpora import Doc

from common19 import (CACHE, EXP13, EXP14_CACHE, REFS, TOP_LEG, doc_metadata, quality_flags, zone_text, work_groups,
                      twin_key, question_facets, sha1, per_question_ranks)
from lexical import Tokenizer, TokenStore, build_index, bm25f_matrix, scores_for, to_doc_ranking
from run_exp13 import query_weights

LEX_CFG = {"weights": {"title": 8.0, "heading": 0.0, "body": 1.0}, "k1": 0.9, "b": {"title": 0.75, "heading": 0.75, "body": 0.4}}


def lexical_leg(store: TokenStore, questions, tok: Tokenizer, unit_doc: np.ndarray, tag: str) -> dict:
    t0 = time.perf_counter()
    index = build_index(store)
    M = bm25f_matrix(index, LEX_CFG["weights"], k1=LEX_CFG["k1"], b=LEX_CFG["b"])
    t_index = time.perf_counter() - t0
    nq = len(questions)
    top_idx = np.full((nq, TOP_LEG), -1, dtype=np.int64)
    top_sc = np.zeros((nq, TOP_LEG), dtype=np.float32)
    rankings = {}
    t0 = time.perf_counter()
    for qi, q in enumerate(questions):
        sc = scores_for(M, index.query_vector(query_weights(index, tok, q.question)))
        k = min(TOP_LEG, len(sc))
        cand = np.argpartition(-sc, k - 1)[:k]
        cand = cand[np.argsort(-sc[cand], kind="stable")]
        top_idx[qi], top_sc[qi] = cand, sc[cand]
        rankings[q.qid] = to_doc_ranking(sc, unit_doc)
    q_ms = (time.perf_counter() - t0) / nq * 1000
    np.savez(CACHE / f"lex_{tag}.npz", idx=top_idx, score=top_sc)
    print(f"  lexical leg [{tag}]: {index.n} units, V={index.V}, nnz {M.nnz/1e6:.1f}M, index {t_index:.0f}s, {q_ms:.0f} ms/query", flush=True)
    del M, index
    gc.collect()
    return rankings


def build_zoned_store(store: TokenStore, cd_raw: np.ndarray, cd_zoned: np.ndarray, map_to_raw: np.ndarray,
                      zoned_chunks, tok: Tokenizer) -> TokenStore:
    """Token store of the zoned chunks: title / heading ids copied from the document's raw units, body ids
    copied for unchanged chunks (same text) and tokenised afresh for the chunks zoning changed."""
    vocab = {t: i for i, t in enumerate(store.vocab)}
    doc_first_raw = np.full(int(cd_raw.max()) + 1, -1, dtype=np.int64)
    for i in range(len(cd_raw) - 1, -1, -1):
        doc_first_raw[cd_raw[i]] = i
    fields = {}
    body_ids_raw, body_rp = store.fields["body"]
    for fname in ("title", "heading"):
        ids_raw, rp = store.fields[fname]
        ids, rowptr = [], [0]
        for u in range(len(zoned_chunks)):
            r = doc_first_raw[cd_zoned[u]]
            ids.append(ids_raw[rp[r]:rp[r + 1]]); rowptr.append(rowptr[-1] + rp[r + 1] - rp[r])
        fields[fname] = (np.concatenate(ids).astype(np.int32), np.asarray(rowptr, dtype=np.int64))
    ids, rowptr = [], [0]
    for u, c in enumerate(zoned_chunks):
        r = map_to_raw[u]
        if r >= 0:
            arr = body_ids_raw[body_rp[r]:body_rp[r + 1]]
        else:
            pre = f"{c.title}\n\n"
            body = c.text[len(pre):] if c.text.startswith(pre) else c.text
            arr = np.array([vocab.setdefault(t, len(vocab)) for t in tok(body)], dtype=np.int32)
        ids.append(arr); rowptr.append(rowptr[-1] + len(arr))
    fields["body"] = (np.concatenate(ids).astype(np.int32), np.asarray(rowptr, dtype=np.int64))
    inv = [None] * len(vocab)
    for t, i in vocab.items():
        inv[i] = t
    return TokenStore(inv, fields, len(zoned_chunks))


def main():
    CACHE.mkdir(exist_ok=True)
    t0 = time.perf_counter()
    docs = load_corpus_c(max_chars=200_000)
    questions = load_questions_c()
    print(f"corpus C: {len(docs)} docs, {len(questions)} questions ({time.perf_counter()-t0:.0f}s)", flush=True)

    # ── metadata, zoning, quality, works ────────────────────────────────────
    metas = [doc_metadata(d) for d in docs]
    zoned, removed_lines = [], 0
    for d in docs:
        z, r = zone_text(d.title, d.text)
        zoned.append(z); removed_lines += r
    flags = [quality_flags(d, m, z) for d, m, z in zip(docs, metas, zoned)]
    t1 = time.perf_counter()
    work, wstats = work_groups(docs, metas, zoned)
    print(f"  works: {wstats} ({time.perf_counter()-t1:.0f}s)", flush=True)
    twins: dict[str, int] = {}
    twin = [twins.setdefault(twin_key(d.doc_id, d.title, m["folder"]), len(twins)) for d, m in zip(docs, metas)]
    for i, (m, f) in enumerate(zip(metas, flags)):
        m.update(f); m["work"] = work[i]; m["twin"] = twin[i]; m["zoned_chars"] = len(zoned[i])
    expected = {e for q in questions for e in q.expected}
    dropped_expected = [d.doc_id for d, f in zip(docs, flags) if f["drop"] and d.doc_id in expected]
    n_drop = Counter(f["reason"] for f in flags if f["drop"])
    wsize = Counter(work)
    tsize = Counter(twin)
    multi = {w: c for w, c in wsize.items() if c > 1}
    print(f"  quality: drop {sum(n_drop.values())} docs {dict(n_drop)}; expected docs dropped: {dropped_expected}", flush=True)
    print(f"  zoning: {removed_lines} lines removed, chars {sum(len(d.text) for d in docs)/1e6:.1f}M → {sum(len(z) for z in zoned)/1e6:.1f}M", flush=True)
    print(f"  canonicalisation: {len(wsize)} works for {len(docs)} docs ({len(multi)} works with >1 edition, "
          f"{sum(c-1 for c in multi.values())} editions collapsed); twin level: {len(tsize)} groups", flush=True)
    print(f"  region: {Counter(m['region'] for m in metas)}; lang: {Counter(m['lang'] for m in metas)}", flush=True)
    print(f"  domain: {Counter(m['domain'] for m in metas)}", flush=True)
    # expected docs whose work has several members
    ex_multi = [(e, wsize[work[i]]) for i, d in enumerate(docs) if d.doc_id in expected and wsize[work[i]] > 1 for e in [d.doc_id]]
    print(f"  expected docs in multi-edition works: {len(ex_multi)}", flush=True)

    # ── chunkings ───────────────────────────────────────────────────────────
    raw_chunks = fixed_chunks(docs, 1200, 100, prefix_title=True)
    zoned_docs = [Doc(d.doc_id, d.title, z, dict(d.meta)) for d, z in zip(docs, zoned)]
    zoned_chunks = fixed_chunks(zoned_docs, 1200, 100, prefix_title=True)
    doc_index = {d.doc_id: i for i, d in enumerate(docs)}
    cd_raw = np.array([doc_index[c.doc_id] for c in raw_chunks], dtype=np.int64)
    cd_zoned = np.array([doc_index[c.doc_id] for c in zoned_chunks], dtype=np.int64)
    z14 = np.load(EXP14_CACHE / "C_stage1.npz", allow_pickle=False)
    assert np.array_equal(z14["chunk_doc"].astype(np.int64), cd_raw), "raw chunks must equal the exp-14 chunks"
    raw_by_text = {}
    for i, c in enumerate(raw_chunks):
        raw_by_text.setdefault(sha1(c.text), i)
    map_to_raw = np.array([raw_by_text.get(sha1(c.text), -1) for c in zoned_chunks], dtype=np.int64)
    changed = np.flatnonzero(map_to_raw < 0)
    print(f"  chunks: raw {len(raw_chunks)}, zoned {len(zoned_chunks)}, changed (need re-embedding) {len(changed)} "
          f"({len(changed)/len(zoned_chunks)*100:.1f} %)", flush=True)
    np.savez(CACHE / "chunks.npz", chunk_doc_raw=cd_raw, chunk_doc_zoned=cd_zoned, map_to_raw=map_to_raw)
    (CACHE / "zoned_changed_texts.json").write_text(json.dumps({str(int(i)): zoned_chunks[int(i)].text for i in changed}, ensure_ascii=False))
    facets = {q.qid: question_facets(q.question) for q in questions}
    (CACHE / "facets.json").write_text(json.dumps(facets, ensure_ascii=False, indent=1))
    print(f"  facets: region {sum(1 for f in facets.values() if f['region'])} (explicit {sum(1 for f in facets.values() if f['region_explicit'])}), "
          f"year {sum(1 for f in facets.values() if f['years'])}, domain {sum(1 for f in facets.values() if f['domains'])}, "
          f"doctype {sum(1 for f in facets.values() if f['folders'])} questions", flush=True)

    # ── lexical leg, raw (exp-13 cached tokenisation) ───────────────────────
    tok = Tokenizer("01", numbers=True)
    store: TokenStore = pickle.load((EXP13 / ".cache" / "C_tok01+num.pkl").open("rb"))
    assert store.n == len(raw_chunks)
    unit_doc_raw = np.array([c.doc_id for c in raw_chunks])
    rk = lexical_leg(store, questions, tok, unit_doc_raw, "raw")
    ref = per_question_ranks(REFS["lex13"][0])
    from rag_eval import evaluate_rankings
    res = evaluate_rankings("lex_raw_check", "C", questions, rk)
    same = sum(1 for qid in ref if ref[qid] == res.per_question[qid]["rank"])
    print(f"  exp-13 lexical reproduction: {same}/{len(ref)} per-question ranks identical (val MRR {res.metrics['val_mrr']:.3f})", flush=True)

    # ── lexical leg, zoned: reuse token ids of unchanged units, tokenise the changed ones ──
    t1 = time.perf_counter()
    store_z = build_zoned_store(store, cd_raw, cd_zoned, map_to_raw, zoned_chunks, tok)
    print(f"  zoned tokenisation: {len(changed)} units re-tokenised, V {len(store.vocab)} → {len(store_z.vocab)} ({time.perf_counter()-t1:.0f}s)", flush=True)
    del store
    gc.collect()
    unit_doc_zoned = np.array([c.doc_id for c in zoned_chunks])
    rk_z = lexical_leg(store_z, questions, tok, unit_doc_zoned, "zoned")
    res_z = evaluate_rankings("lex_zoned_check", "C", questions, rk_z)
    print(f"  lexical only, zoned text: val MRR {res_z.metrics['val_mrr']:.3f} (raw {res.metrics['val_mrr']:.3f})", flush=True)

    (CACHE / "docs_meta.json").write_text(json.dumps(metas, ensure_ascii=False))
    (CACHE / "meta.json").write_text(json.dumps({
        "doc_ids": [d.doc_id for d in docs], "qids": [q.qid for q in questions],
        "n_chunks_raw": len(raw_chunks), "n_chunks_zoned": len(zoned_chunks), "n_changed_chunks": int(len(changed)),
        "zoning": {"lines_removed": removed_lines, "chars_before": sum(len(d.text) for d in docs), "chars_after": sum(len(z) for z in zoned)},
        "quality": {"dropped": dict(n_drop), "dropped_expected": dropped_expected},
        "works": {"n_docs": len(docs), "n_works": len(wsize), "n_multi": len(multi), "n_collapsed": sum(c - 1 for c in multi.values()),
                  "tiers": wstats, "n_twin_groups": len(tsize), "expected_in_multi": ex_multi},
        "lexical": {"config": LEX_CFG, "raw_val_mrr": res.metrics["val_mrr"], "zoned_val_mrr": res_z.metrics["val_mrr"],
                    "reproduced_exp13": f"{same}/{len(ref)}"},
        "seconds": round(time.perf_counter() - t0)}, ensure_ascii=False, indent=1))
    print(f"done in {time.perf_counter()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
