#!/usr/bin/env python3
"""Document-level first-stage legs on corpus B for the 40 human and 304 mined questions (no torch, no lock):

* rec      – exp 20's reception BM25F (exp-13 index + cue field + `sent+title` reception field, w 0.5, b 0.5);
             human questions: full reception (cache/B_reception.json of exp 20); mined questions: the leak-free
             field (B_reception_nomined.json: no sentence from any mined question's source document)
* e5       – cached e5-small (article_ctx_1200 chunks, doc = max chunk): human rows from exp 14's stage-1
             cache, mined rows from exp 20's mined query embeddings · the shared chunk embedding cache
* bm25_03  – exp 03 / exp 12 chunk BM25 (exp-03 tokenizer, bm25s k1 1.2 b 0.75), needed to reproduce the
             exp-03 e5 RRF first stage (the bar's) and exp 12's colbert-fr + BM25 RRF on the mined set
* colbert  – read from cache/B_colbert_scores.npz (colbert_scores.py) if present, doc = max chunk

  ../14_ltr_fusion/.venv/bin/python legs.py      → cache/B_legs.npz + cache/B_legs.json
"""
from __future__ import annotations

import json
import re
import time

import numpy as np

from common22 import CACHE, EXP14, EXP20, doc_max, load_universe, questions_human, questions_mined, REC_VARIANT, REC_W, REC_B
from lexical import Tokenizer, build_index, bm25f_matrix, scores_for, REGION_TOKEN  # noqa: E402  (13_lexical_upgrades)
from run_exp13 import load_corpus, tokenize_corpus, query_weights  # noqa: E402
from common17 import LEX_CONFIG, b_code_cues  # noqa: E402
from cleanup import region_of_code  # noqa: E402
from rag_eval.cache import EmbeddingCache, _key  # noqa: E402
from models import MODELS  # noqa: E402  (02_dense_sweep)
from run_hybrid import tokenize as tok03  # noqa: E402  (03_hybrid_rerank)
import bm25s  # noqa: E402


def reception_scores(questions, rec_file, tok, cfg, C, store_base, unit_doc_idx, n_docs) -> tuple[np.ndarray, float]:
    """exp 20 run_b.py `lexical()` with the reception field of `rec_file` (train-selected point)."""
    rec = json.loads(rec_file.read_text())["articles"]
    with_titles = REC_VARIANT == "sent+title"
    per_art = {art: tok("\n".join(s["t"] for s in v["sentences"]) + ("\n" + "\n".join(v["titles"]) if with_titles else ""))
               for art, v in rec.items()}
    fname = f"rec_{REC_VARIANT}"
    store = store_base
    if fname in store.fields:
        store.fields.pop(fname)          # replaced per question set (full vs leak-free)
    store.add_field(fname, [per_art.get(C.unit_doc[u], []) for u in range(store.n)])
    weights = {**cfg["weights"], fname: REC_W}
    fields = [f for f in weights if weights[f] > 0]
    index = build_index(store, fields)
    M = bm25f_matrix(index, {f: weights[f] for f in fields}, k1=cfg["k1"], b={**cfg["b"], fname: REC_B})
    t0 = time.perf_counter()
    out = np.zeros((len(questions), n_docs))
    for i, q in enumerate(questions):
        w = query_weights(index, tok, q.question)
        for dt in b_code_cues(q.question):
            w[dt] = w.get(dt, 0) + cfg["doctype_w"]
        out[i] = doc_max(scores_for(M, index.query_vector(w)), unit_doc_idx, n_docs, fill=0.0)
    return out, (time.perf_counter() - t0) / len(questions) * 1000


def main():
    t_all = time.perf_counter()
    human, mined = questions_human(), questions_mined()
    docs, chunks, chunk_doc, doc_start, doc_ids = load_universe()
    n_docs, n_chunks = len(doc_ids), len(chunks)
    doc_index = {d: i for i, d in enumerate(doc_ids)}
    print(f"corpus B: {n_docs} articles / {n_chunks} chunks; {len(human)} human + {len(mined)} mined questions", flush=True)

    # ── reception BM25F (exp-13 machinery, exp-20 field) ─────────────────────
    cfg = LEX_CONFIG["B"]
    tok = Tokenizer(**cfg["tokenizer"])
    C = load_corpus("B", cfg["clean_b"])
    assert [d.doc_id for d in C.docs] == doc_ids
    unit_doc_idx = np.array([doc_index[d] for d in C.unit_doc], dtype=np.int64)
    store = tokenize_corpus(C, tok, cfg["clean_b"])
    cue_tokens = []
    for u in range(store.n):
        code = C.unit_meta[u].get("code", "")
        toks = [REGION_TOKEN[r] for r in region_of_code(code).split(",") if r in REGION_TOKEN]
        toks.append("dt" + re.sub(r"_(wal|bxl|vla)$", "", code))
        cue_tokens.append(toks)
    store.add_field("cue", cue_tokens)
    t0 = time.perf_counter()
    rec_h, ms_h = reception_scores(human, EXP20 / "cache" / "B_reception.json", tok, cfg, C, store, unit_doc_idx, n_docs)
    rec_m, ms_m = reception_scores(mined, EXP20 / "cache" / "B_reception_nomined.json", tok, cfg, C, store, unit_doc_idx, n_docs)
    print(f"  reception BM25F: human {ms_h:.1f} ms/q, mined (leak-free) {ms_m:.1f} ms/q; build {time.perf_counter() - t0:.0f}s", flush=True)
    del store, C

    # ── e5-small (cached) ────────────────────────────────────────────────────
    z14 = np.load(EXP14 / "cache" / "B_stage1.npz", allow_pickle=False)
    m14 = json.loads((EXP14 / "cache" / "B_stage1.json").read_text())
    assert m14["qids"] == [q.qid for q in human] and np.array_equal(z14["chunk_doc"], chunk_doc)
    e5_chunk_h = z14["leg_e5"].astype(np.float32)                      # (40, n_chunks)
    qm = json.loads((EXP20 / "cache" / "B_mined_q_e5.json").read_text())
    assert qm["qids"] == [q.qid for q in mined]
    q_e5 = np.load(EXP20 / "cache" / "B_mined_q_e5.npy")
    spec = MODELS["e5-small"]
    emb = np.load(EmbeddingCache().dir / (_key(spec.hf_id, [c.text for c in chunks], "seq512|d_prefix='passage: '|article_ctx_1200") + ".npy"))
    e5_chunk_m = (q_e5 @ emb.T).astype(np.float32)                      # (304, n_chunks)
    del emb
    e5_chunk = np.concatenate([e5_chunk_h, e5_chunk_m])
    e5_doc = np.stack([doc_max(e5_chunk[i], chunk_doc, n_docs, fill=-1.0) for i in range(len(e5_chunk))])
    print("  e5 legs done", flush=True)

    # ── exp-03 chunk BM25 (k1 1.2, b 0.75, exp-03 tokenizer) ─────────────────
    t0 = time.perf_counter()
    r = bm25s.BM25(k1=1.2, b=0.75)
    r.index([tok03(c.text) for c in chunks], show_progress=False)
    bm_chunk = np.stack([r.get_scores(tok03(q.question)).astype(np.float32) for q in human + mined])
    print(f"  exp-03 BM25 chunks: {time.perf_counter() - t0:.0f}s", flush=True)

    out = {"rec_human": rec_h.astype(np.float32), "rec_mined": rec_m.astype(np.float32), "e5_doc": e5_doc.astype(np.float32),
           "e5_chunk": e5_chunk, "bm25_03_chunk": bm_chunk, "chunk_doc": chunk_doc, "doc_start": doc_start}
    meta = {"qids_human": [q.qid for q in human], "qids_mined": [q.qid for q in mined], "doc_ids": doc_ids, "n_chunks": n_chunks,
            "reception": {"variant": REC_VARIANT, "weight": REC_W, "b": REC_B, "human": "B_reception.json (full)",
                          "mined": "B_reception_nomined.json (leak-free)", "query_ms_human": round(ms_h, 2), "query_ms_mined": round(ms_m, 2)},
            "colbert": None}
    cf = CACHE / "B_colbert_scores.npz"
    if cf.exists():
        z = np.load(cf, allow_pickle=False)
        assert list(z["qids"]) == meta["qids_human"] + meta["qids_mined"]
        out["colbert_chunk"] = z["scores"].astype(np.float32)
        out["colbert_doc"] = np.stack([doc_max(z["scores"][i], chunk_doc, n_docs, fill=-1e4) for i in range(len(z["scores"]))]).astype(np.float32)
        meta["colbert"] = json.loads(str(z["timing"]))
        print("  colbert legs attached", flush=True)
    else:
        print("  no cache/B_colbert_scores.npz yet (colbert_scores.py under the torch lock) – legs saved without colbert", flush=True)
    np.savez(CACHE / "B_legs.npz", **out)
    (CACHE / "B_legs.json").write_text(json.dumps(meta))
    print(f"saved cache/B_legs.npz in {time.perf_counter() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
