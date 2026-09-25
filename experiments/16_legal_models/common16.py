"""Shared helpers for experiment 16 (in-domain Belgian legal models).

Environment notes (this box): the root disk was full when this experiment started, so the BM25 /
chunk / embedding caches and the logs live on the RAM-backed ``/dev/shm/exp16`` (small, < 1 GB);
results are written to ``experiments/results/16_legal_models`` through ``rag_eval.results.save_result``
(with a JSON copy on /dev/shm in case the disk write fails).
"""
from __future__ import annotations

import json
import os
import pickle
import sys
import time
from pathlib import Path

SHM = Path(os.environ.get("EXP16_SHM", "/dev/shm/exp16"))
(SHM / "results").mkdir(parents=True, exist_ok=True)
(SHM / "logs").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")   # HF cache: the default ~/.cache/huggingface (disk)

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("EXP16_THREADS", "2")))

from rag_eval import evaluate_rankings, save_result  # noqa: E402
from rag_eval.corpora import DATA_DIR  # noqa: E402
from rag_eval.metrics import RunResult  # noqa: E402

EXPS = DATA_DIR.parent
for _p in ("15_finetune", "03_hybrid_rerank", "02_dense_sweep"):
    sys.path.insert(0, str(EXPS / _p))
from data import corpus  # noqa: E402  (experiment 15: docs, questions, chunks per corpus)
from run_hybrid import tokenize, rrf, minmax, to_doc_ranking  # noqa: E402,F401
import bm25s  # noqa: E402

EXP = "16_legal_models"
RESULTS_LOG = SHM / "logs" / "results.txt"
MODELS_DIR = Path(__file__).resolve().parent / "models"   # fine-tuned models are written here only
MODELS_DIR.mkdir(exist_ok=True)


def log(msg: str) -> None:
    print(msg, flush=True)
    with RESULTS_LOG.open("a") as fh:
        fh.write(msg + "\n")


def save(result: RunResult) -> None:
    """save_result (disk) + backup copy on /dev/shm; never crash on a full disk."""
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in result.name)
    (SHM / "results" / f"{result.corpus}__{safe}.json").write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=1))
    try:
        save_result(EXP, result)
    except OSError as e:  # disk full
        log(f"!! save_result failed ({e}); backup kept in {SHM / 'results'}")
    log(result.summary())


# ── first-stage candidates (BM25 over the same chunks as experiments 03/15) ────────────────
def load_chunks(name: str):
    """docs, questions, chunk texts, chunk→doc ids (cached on /dev/shm)."""
    f = SHM / f"chunks_{name}.pkl"
    if f.exists():
        return pickle.load(f.open("rb"))
    docs, qs, chunks = corpus(name)
    texts = [c.text for c in chunks]
    doc_ids = np.array([c.doc_id for c in chunks])
    out = (qs, texts, doc_ids)
    pickle.dump(out, f.open("wb"))
    return out


def bm25_scores(name: str):
    """questions, texts, doc_ids, BM25 score matrix (nq × n_chunks), cached on /dev/shm."""
    f = SHM / f"bm25_{name}.pkl"
    if f.exists():
        return pickle.load(f.open("rb"))
    qs, texts, doc_ids = load_chunks(name)
    t0 = time.perf_counter()
    r = bm25s.BM25(k1=1.5, b=0.75)
    r.index([tokenize(t) for t in texts], show_progress=False)
    bm = np.zeros((len(qs), len(texts)), dtype=np.float32)
    for i, q in enumerate(qs):
        bm[i] = r.get_scores(tokenize(q.question))
    print(f"[{name}] bm25 over {len(texts)} chunks in {time.perf_counter() - t0:.0f}s", flush=True)
    out = (qs, texts, doc_ids, bm)
    pickle.dump(out, f.open("wb"))
    return out


def candidates_bm25(name: str, top: int = 30):
    qs, texts, doc_ids, bm = bm25_scores(name)
    cand = {q.qid: np.argsort(-bm[i])[:top] for i, q in enumerate(qs)}
    return qs, texts, doc_ids, cand


def evaluate_rerank(model, tag: str, names=("A", "B", "C"), top: int = 30, batch: int = 16,
                    extra_config: dict | None = None) -> dict:
    """Rerank BM25 top-``top`` chunks with a CrossEncoder-like ``model.predict(pairs)``; doc score = max chunk."""
    out = {}
    for name in names:
        qs, texts, doc_ids, cand = candidates_bm25(name, top)
        rankings = {}
        t0 = time.perf_counter()
        for q in qs:
            c = cand[q.qid]
            sc = np.asarray(model.predict([(q.question, texts[j]) for j in c], batch_size=batch,
                                          show_progress_bar=False), dtype=np.float32).reshape(-1)
            full = np.full(len(texts), -1e9, dtype=np.float32)
            full[c] = sc
            rankings[q.qid] = to_doc_ranking(full, doc_ids)
        dt = time.perf_counter() - t0
        res = evaluate_rankings(f"bm25+{tag}@{top}", name, qs, rankings,
                                config={"reranker": tag, "candidates": "bm25", "top": top, **(extra_config or {})},
                                timing={"rerank_s": round(dt, 1), "per_query_s": round(dt / len(qs), 2)})
        save(res)
        out[name] = res
    return out


def evaluate_dense(name: str, qemb: np.ndarray, emb: np.ndarray, tag: str, fusions=("dense", "rrf", "convex0.3", "convex0.5", "convex0.7"),
                   extra_config: dict | None = None) -> dict:
    """Dense-only / RRF / convex fusion with BM25 over the same chunks (experiment 03 protocol)."""
    qs, texts, doc_ids, bm = bm25_scores(name)
    dense = qemb @ emb.T
    n = len(texts)
    out = {}
    for fu in fusions:
        if fu == "dense":
            s = dense
        elif fu == "bm25":
            s = bm
        elif fu == "rrf":
            s = np.stack([rrf([np.argsort(-dense[i])[:200], np.argsort(-bm[i])[:200]], 60, n) for i in range(len(qs))])
        elif fu.startswith("convex"):
            w = float(fu[len("convex"):])
            s = np.stack([w * minmax(dense[i]) + (1 - w) * minmax(bm[i]) for i in range(len(qs))])
        else:
            raise ValueError(fu)
        rankings = {q.qid: to_doc_ranking(s[i], doc_ids) for i, q in enumerate(qs)}
        res = evaluate_rankings(f"{tag}__{fu}", name, qs, rankings,
                                config={"model": tag, "fusion": fu, "n_chunks": n, **(extra_config or {})})
        save(res)
        out[fu] = res
    return out
