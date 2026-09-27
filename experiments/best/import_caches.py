#!/usr/bin/env python3
"""One-off: bring the caches and indexes computed by the experiment folders into best/ (before those folders go).

Everything is re-keyed by question text (config.qkey) and stamped with the chunk-universe fingerprint:
  22_reception_colbert/cache/B_colbert_tokens.npy + lengths  → index/B_colbert/  (hard link, 0.6 GB)
  22_reception_colbert/cache/B_colbert_scores.npz             → cache/B_colbert_scores.npz   (344 questions)
  21_mined_eval/cache/{B,C}_qemb_e5.npy                       → cache/q_e5.npz               (344 + 761 questions)
  22_reception_colbert/cache/B_mmarco22.npz                   → cache/B_mmarco.npz           (34k pairs)
  17_lex_rerank/cache/C_rerank_bge-reranker-v2-m3.npz         → cache/C_bge.npz              (3.2k pairs)
  20_reception_intent/cache/B_reception{,_nomined}.json       → index/                       (hard link)
Sources that no longer exist are skipped (the pipelines then rebuild / rescore on demand).
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import numpy as np

from rag_eval import load_questions_b, load_questions_c, load_questions_mined

from config import BGE_ID, CACHE, COLBERT_ID, COLBERT_QUERY_LENGTH, EXPERIMENTS, INDEX, MMARCO_ID, RERANK_MAX_LENGTH, qkey

E22 = EXPERIMENTS / "22_reception_colbert" / "cache"
E21 = EXPERIMENTS / "21_mined_eval" / "cache"
E20 = EXPERIMENTS / "20_reception_intent" / "cache"
E17 = EXPERIMENTS / "17_lex_rerank" / "cache"


def link(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)
    print(f"  {src.relative_to(EXPERIMENTS)} → {dst.relative_to(EXPERIMENTS)}")


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    INDEX.mkdir(parents=True, exist_ok=True)
    qb = load_questions_b() + load_questions_mined("B")
    qc = load_questions_c() + load_questions_mined("C")
    text_b = {q.qid: q.question for q in qb}
    text_c = {q.qid: q.question for q in qc}

    # reception -------------------------------------------------------------------------------------------------
    for f in ("B_reception.json", "B_reception_nomined.json"):
        if (E20 / f).exists():
            link(E20 / f, INDEX / f)

    # corpus B universe-bound caches --------------------------------------------------------------------------
    from corpus import universe_b
    uni = universe_b()
    fp = uni.fingerprint()
    if (E22 / "B_colbert_tokens.npy").exists():
        folder = INDEX / "B_colbert"
        link(E22 / "B_colbert_tokens.npy", folder / "tokens.npy")
        link(E22 / "B_colbert_lengths.npy", folder / "lengths.npy")
        lens = np.load(folder / "lengths.npy")
        assert len(lens) == uni.n_chunks
        (folder / "meta.json").write_text(json.dumps({"model": COLBERT_ID, "n_chunks": uni.n_chunks, "fingerprint": fp, "n_tokens": int(lens.sum()),
                                                       "query_length": COLBERT_QUERY_LENGTH, "document_length": 512, "source": "22_reception_colbert/colbert_scores.py"}))
    if (E22 / "B_colbert_scores.npz").exists() and not (CACHE / "B_colbert_scores.npz").exists():
        z = np.load(E22 / "B_colbert_scores.npz", allow_pickle=False)
        keys = [qkey(text_b[str(q)]) for q in z["qids"]]
        order = np.argsort(keys)
        np.savez(CACHE / "B_colbert_scores.npz", keys=np.array([keys[i] for i in order], dtype="U40"), scores=z["scores"][order].astype(np.float32),
                 fingerprint=np.array(fp), model=np.array(COLBERT_ID), query_length=np.array(COLBERT_QUERY_LENGTH))
        print(f"  colbert scores: {len(keys)} questions → cache/B_colbert_scores.npz")
    if (E22 / "B_mmarco22.npz").exists() and not (CACHE / "B_mmarco.npz").exists():
        z = np.load(E22 / "B_mmarco22.npz", allow_pickle=False)
        rows = sorted({(qkey(text_b[str(q)]), int(c)): float(s) for q, c, s in zip(z["qid"], z["chunk_idx"], z["score"])}.items())
        np.savez(CACHE / "B_mmarco.npz", qkey=np.array([k[0] for k, _ in rows], dtype="U40"), chunk_idx=np.array([k[1] for k, _ in rows], dtype=np.int64),
                 score=np.array([s for _, s in rows], dtype=np.float32))
        (CACHE / "B_mmarco.json").write_text(json.dumps({"model": MMARCO_ID, "max_length": RERANK_MAX_LENGTH, "corpus": "B", "n_chunks": uni.n_chunks,
                                                          "fingerprint": fp, "n_pairs": len(rows), "source": "22_reception_colbert/cache/B_mmarco22.npz"}, indent=1))
        print(f"  mMARCO pairs: {len(rows)} → cache/B_mmarco.npz")

    # e5 query vectors --------------------------------------------------------------------------------------------
    vecs = {}
    if (CACHE / "q_e5.npz").exists():
        z = np.load(CACHE / "q_e5.npz", allow_pickle=False)
        vecs = {str(k): v for k, v in zip(z["keys"], z["vecs"])}
    n0 = len(vecs)
    for corpus, texts in (("B", text_b), ("C", text_c)):
        f = E21 / f"{corpus}_qemb_e5.npy"
        if f.exists():
            qids = json.loads((E21 / f"{corpus}_qemb_e5.json").read_text())["qids"]
            for q, v in zip(qids, np.load(f)):
                vecs.setdefault(qkey(texts[q]), v.astype(np.float32))
    if len(vecs) > n0:
        keys = sorted(vecs)
        np.savez(CACHE / "q_e5.npz", keys=np.array(keys, dtype="U40"), vecs=np.stack([vecs[k] for k in keys]))
        print(f"  e5 query vectors: {len(vecs)} → cache/q_e5.npz")

    # corpus C bge pairs -----------------------------------------------------------------------------------------
    if (E17 / "C_rerank_bge-reranker-v2-m3.npz").exists() and not (CACHE / "C_bge.npz").exists():
        from corpus import universe_c
        unic = universe_c()
        z = np.load(E17 / "C_rerank_bge-reranker-v2-m3.npz", allow_pickle=False)
        assert int(z["max_length"]) == RERANK_MAX_LENGTH
        qids = json.loads((E17 / "C_lex.json").read_text())["qids"]
        rows = sorted({(qkey(text_c[qids[int(q)]]), int(c)): float(s) for q, c, s in zip(z["q_idx"], z["chunk_idx"], z["score"])}.items())
        assert max(k[1] for k, _ in rows) < unic.n_chunks
        np.savez(CACHE / "C_bge.npz", qkey=np.array([k[0] for k, _ in rows], dtype="U40"), chunk_idx=np.array([k[1] for k, _ in rows], dtype=np.int64),
                 score=np.array([s for _, s in rows], dtype=np.float32))
        (CACHE / "C_bge.json").write_text(json.dumps({"model": BGE_ID, "max_length": RERANK_MAX_LENGTH, "corpus": "C", "n_chunks": unic.n_chunks,
                                                       "fingerprint": unic.fingerprint(), "n_pairs": len(rows), "source": "17_lex_rerank/cache/C_rerank_bge-reranker-v2-m3.npz"}, indent=1))
        print(f"  bge pairs: {len(rows)} → cache/C_bge.npz")
    print("done")


if __name__ == "__main__":
    main()
