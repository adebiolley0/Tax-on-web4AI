#!/usr/bin/env python3
"""Stage B – dense leg (multilingual-e5-small, one torch process under the lock):

* raw text: the exp-09 chunk embeddings from the shared EmbeddingCache (201,404 chunks, nothing
  re-encoded) + the 64 query embeddings → chunk scores; checked against exp 14's ``leg_e5``;
* zoned text: embeddings of unchanged chunks are copied through ``map_to_raw``; only the chunks
  zoning changed are encoded here (sharded, resumable);
* per question the top-``TOP_LEG`` chunks of each version are cached (``cache/dense_{raw,zoned}.npz``).

  cd experiments/17_lex_rerank && OMP_NUM_THREADS=4 flock ../.torch.lock \
      ../14_ltr_fusion/.venv/bin/python ../19_canonical_hybrid/embed.py
"""
from __future__ import annotations

import json
import os
import sys
import time

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np

from rag_eval import load_corpus_c, load_questions_c, fixed_chunks
from rag_eval.cache import EmbeddingCache, _key
from rag_eval.corpora import DATA_DIR

from common19 import CACHE, EXP14_CACHE, E5_HF, E5_EXTRA, TOP_LEG

for _p in ("02_dense_sweep", "03_hybrid_rerank"):
    sys.path.insert(0, str((DATA_DIR.parent / _p).resolve()))
from models import MODELS  # noqa: E402
from run_sweep import Encoder  # noqa: E402

SHARD = 2000


def topk(scores: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    nq = scores.shape[0]
    idx = np.empty((nq, k), dtype=np.int64)
    sc = np.empty((nq, k), dtype=np.float32)
    for i in range(nq):
        c = np.argpartition(-scores[i], k - 1)[:k]
        c = c[np.argsort(-scores[i][c], kind="stable")]
        idx[i], sc[i] = c, scores[i][c]
    return idx, sc


def main():
    import torch
    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "4")))
    t0 = time.perf_counter()
    docs, questions = load_corpus_c(max_chars=200_000), load_questions_c()
    raw = fixed_chunks(docs, 1200, 100, prefix_title=True)
    texts = [c.text for c in raw]
    f = EmbeddingCache().dir / (_key(E5_HF, texts, E5_EXTRA) + ".npy")
    emb = np.load(f)
    assert emb.shape[0] == len(texts), emb.shape
    print(f"raw embeddings {emb.shape} from {f.name} ({time.perf_counter()-t0:.0f}s)", flush=True)
    del raw, texts, docs
    ch = np.load(CACHE / "chunks.npz")
    m2r = ch["map_to_raw"]
    changed = json.loads((CACHE / "zoned_changed_texts.json").read_text())
    idxs = sorted(int(k) for k in changed)
    ctexts = [changed[str(i)] for i in idxs]

    enc = Encoder(MODELS["e5-small"])
    qemb = enc.queries([q.question for q in questions])
    dense_raw = (qemb @ emb.T).astype(np.float32)
    z14 = np.load(EXP14_CACHE / "C_stage1.npz", allow_pickle=False)
    diff = float(np.abs(dense_raw - z14["leg_e5"]).max())
    print(f"dense raw vs exp-14 leg_e5: max abs diff {diff:.2e}", flush=True)
    idx, sc = topk(dense_raw, TOP_LEG)
    np.savez(CACHE / "dense_raw.npz", idx=idx, score=sc)
    np.save(CACHE / "e5_queries.npy", qemb)

    # changed chunks (sharded, resumable)
    t1 = time.perf_counter()
    out = np.zeros((len(idxs), emb.shape[1]), dtype=np.float32)
    n_enc = 0
    for s in range(0, len(idxs), SHARD):
        fs = CACHE / f"e5_changed_{s}.npy"
        if fs.exists():
            out[s:s + SHARD] = np.load(fs)
            continue
        e = enc.docs(ctexts[s:s + SHARD])
        np.save(fs, e)
        out[s:s + SHARD] = e
        n_enc += len(e)
        el = time.perf_counter() - t1
        print(f"  encoded {s + len(e)}/{len(idxs)} changed chunks ({el/max(n_enc,1):.3f} s/chunk, {el/60:.1f} min)", flush=True)
    t_enc = time.perf_counter() - t1
    emb_z = np.empty((len(m2r), emb.shape[1]), dtype=np.float32)
    ok = m2r >= 0
    emb_z[ok] = emb[m2r[ok]]
    emb_z[np.asarray(idxs)] = out
    dense_zoned = (qemb @ emb_z.T).astype(np.float32)
    idx, sc = topk(dense_zoned, TOP_LEG)
    np.savez(CACHE / "dense_zoned.npz", idx=idx, score=sc)
    (CACHE / "embed_timing.json").write_text(json.dumps({
        "n_changed": len(idxs), "n_encoded_this_run": n_enc, "encode_s": round(t_enc, 1),
        "s_per_chunk": round(t_enc / max(n_enc, 1), 4), "raw_vs_exp14_maxdiff": diff, "total_s": round(time.perf_counter() - t0, 1)}, indent=1))
    print(f"done: {len(idxs)} changed chunks, {t_enc/60:.1f} min encoding, total {(time.perf_counter()-t0)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
