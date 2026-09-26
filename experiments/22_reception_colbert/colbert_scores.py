#!/usr/bin/env python3
"""colbert-fr (antoinelouis/colbertv1-camembert-base-mmarcoFR via PyLate, exp-12 set-up) MaxSim scores of the
40 human + 304 mined corpus-B questions over the 10,869 exp-14 / exp-12 chunks (article_ctx_1200).

Exp 12 kept the token embeddings in memory only, so the corpus is encoded once more here and the fp16 token
matrix is persisted (cache/B_colbert_tokens.npy, ≈ 0.6 GB) so that nobody has to pay the hour again.
The 40 human rows are checked against exp 12's cached score matrix.

  cd experiments/22_reception_colbert
  flock ../.torch.lock env OMP_NUM_THREADS=4 EXP12_THREADS=4 HF_HUB_OFFLINE=1 \
      ../12_sparse_colbert/.venv/bin/python colbert_scores.py
→ cache/B_colbert_scores.npz (qids, scores (344, 10869) float32, timing)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "12_sparse_colbert"))
CACHE = HERE / "cache"

from common12 import load_corpus  # noqa: E402  (sets torch threads from EXP12_THREADS)
from maxsim import maxsim_matrix  # noqa: E402
from run_colbert import COLBERT_MODELS, encode, load_model  # noqa: E402
from rag_eval import load_questions_b, load_questions_mined  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--qblock", type=int, default=32)
    ap.add_argument("--no-persist", action="store_true", help="do not write the fp16 token matrix")
    ap.add_argument("--query-length", type=int, default=48, help="PyLate query length (exp 12: 48; mined questions have a median of 78 words)")
    a = ap.parse_args()
    import torch
    suffix = "" if a.query_length == 48 else f"_q{a.query_length}"
    out_f = CACHE / f"B_colbert_scores{suffix}.npz"
    c = load_corpus("B")
    questions = load_questions_b() + load_questions_mined("B")
    qids = [q.qid for q in questions]
    assert len(set(qids)) == len(qids)
    m14 = json.loads((HERE.parent / "14_ltr_fusion" / "cache" / "B_stage1.json").read_text())
    assert c.n == m14["n_chunks"] and [d.doc_id for d in c.docs] == m14["doc_ids"], "chunk universe differs from exp 14"
    print(f"corpus B: {len(c.docs)} docs / {c.n} chunks; {len(questions)} questions ({len(qids) - 304} human + 304 mined); "
          f"torch threads {torch.get_num_threads()}", flush=True)
    spec = {**COLBERT_MODELS["colbert-fr"], "kw": {**COLBERT_MODELS["colbert-fr"]["kw"], "query_length": a.query_length}}
    m, load_s = load_model(spec)
    print(f"model loaded in {load_s:.1f}s", flush=True)
    timing = {"model_load_s": round(load_s, 1)}

    tok_f, len_f = CACHE / "B_colbert_tokens.npy", CACHE / "B_colbert_lengths.npy"
    if tok_f.exists() and len_f.exists():
        toks, lens = np.load(tok_f, mmap_mode="r"), np.load(len_f)
        assert len(lens) == c.n
        off = np.concatenate([[0], np.cumsum(lens)])
        d_embs = [np.asarray(toks[off[i]:off[i + 1]]) for i in range(c.n)]
        timing["encode_docs_s"] = 0.0
        print(f"doc tokens loaded from cache: {int(lens.sum())} tokens", flush=True)
    else:
        d_embs, enc_s = encode(m, c.texts, False, a.bs)
        timing["encode_docs_s"] = round(enc_s, 1)
        n_tok = sum(e.shape[0] for e in d_embs)
        print(f"docs encoded in {enc_s:.0f}s ({enc_s / c.n * 1000:.0f} ms/chunk); {n_tok} tokens, {n_tok / c.n:.1f}/chunk", flush=True)
        if not a.no_persist:
            np.save(tok_f, np.concatenate(d_embs, axis=0).astype(np.float16))
            np.save(len_f, np.array([e.shape[0] for e in d_embs], dtype=np.int32))
            print(f"persisted {tok_f} ({tok_f.stat().st_size / 1e6:.0f} MB)", flush=True)
    q_embs, q_s = encode(m, [q.question for q in questions], True, 16)
    timing["encode_queries_s"] = round(q_s, 1)
    print(f"queries encoded in {q_s:.1f}s; q tokens mean {np.mean([e.shape[0] for e in q_embs]):.1f}", flush=True)
    del m

    t0 = time.perf_counter()
    scores = np.zeros((len(questions), c.n), dtype=np.float32)
    for s in range(0, len(questions), a.qblock):
        blk, _ = maxsim_matrix(q_embs[s:s + a.qblock], d_embs, doc_batch=128)
        scores[s:s + a.qblock] = blk
        print(f"  maxsim {min(s + a.qblock, len(questions))}/{len(questions)} ({time.perf_counter() - t0:.0f}s)", flush=True)
    ms = time.perf_counter() - t0
    timing.update({"maxsim_all_s": round(ms, 1), "maxsim_per_query_s": round(ms / len(questions), 3), "n_chunks": c.n,
                   "threads": torch.get_num_threads(), "query_length": a.query_length,
                   "q_tokens_mean": float(np.mean([e.shape[0] for e in q_embs]))})

    # sanity: the 40 human rows against exp 12's cached matrix
    ref = np.load(HERE.parent / "12_sparse_colbert" / "cache" / "colbert_B_colbert-fr.npz", allow_pickle=True)["scores"]
    nh = len(qids) - 304
    if ref.shape == (nh, c.n) and a.query_length == 48:
        top_agree = np.mean([np.argmax(ref[i]) == np.argmax(scores[i]) for i in range(nh)])
        corr = np.mean([np.corrcoef(ref[i], scores[i])[0, 1] for i in range(nh)])
        timing["check_vs_exp12"] = {"top1_chunk_agreement": float(top_agree), "mean_row_corr": float(corr),
                                    "max_abs_diff": float(np.abs(ref - scores[:nh]).max())}
        print("check vs exp 12:", timing["check_vs_exp12"], flush=True)
    np.savez(out_f, qids=np.array(qids), scores=scores, timing=json.dumps(timing))
    print("saved", out_f, timing, flush=True)


if __name__ == "__main__":
    main()
