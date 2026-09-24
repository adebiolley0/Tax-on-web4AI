#!/usr/bin/env python3
"""Experiment 03 – hybrid retrieval (dense + BM25) and cross-encoder reranking.

Builds on experiment 02: dense chunk embeddings are read from the shared
EmbeddingCache (computed once), BM25 is computed with bm25s on the same chunks.
Fusion: RRF (k=60) or convex score combination (min-max normalised).
Reranking: sentence-transformers CrossEncoder on the top-N fused chunks; the
document score is the max reranked chunk score.

Usage:
  uv run python run_hybrid.py --corpus A --model e5-base --chunker fixed1500_title \
      --fusions rrf,convex0.5 --rerankers none,bge-reranker-v2-m3 --rerank_top 30
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata

import numpy as np
import bm25s
import Stemmer

from rag_eval import (EmbeddingCache, evaluate_rankings, save_result, print_leaderboard,
                      load_corpus_a, load_questions_a, load_corpus_b, load_questions_b)
from rag_eval.cache import _key
from rag_eval.corpora import DATA_DIR

sys.path.insert(0, str((DATA_DIR.parent / "02_dense_sweep").resolve()))
from models import MODELS  # noqa: E402
from run_sweep import CHUNKERS, Encoder, default_codes_b  # noqa: E402

EXP = "03_hybrid_rerank"

RERANKERS = {
    "bge-reranker-v2-m3": {"hf": "BAAI/bge-reranker-v2-m3", "max_len": 1024},
    "bge-reranker-base": {"hf": "BAAI/bge-reranker-base", "max_len": 512},
    "jina-reranker-v2": {"hf": "jinaai/jina-reranker-v2-base-multilingual", "max_len": 1024, "trust": True},
    "mxbai-rerank-base-v2": {"hf": "mixedbread-ai/mxbai-rerank-base-v2", "max_len": 1024, "trust": True},
    "mmarco-minilm": {"hf": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1", "max_len": 512},
}

_stemmer = Stemmer.Stemmer("french")
_STOP = set("""le la les l un une des du de d et ou à a au aux en dans par pour sur avec sans sous ce cet cette ces
se sa son ses leur leurs mon ma mes ton ta tes notre nos votre vos qui que quoi dont où ne pas plus est sont
été être ont a avoir il elle ils elles on nous vous je tu y ne n s c qu d l lorsque lorsqu si comme mais donc
or ni car tout tous toute toutes même autre autres entre vers chez ainsi aussi alors""".split())


def tokenize(text: str, strip_accents: bool = True) -> list[str]:
    t = text.lower()
    if strip_accents:
        t = unicodedata.normalize("NFKD", t)
        t = "".join(ch for ch in t if not unicodedata.combining(ch))
    toks = re.findall(r"[a-z0-9]+(?:/[0-9]+)*", t)
    toks = [w for w in toks if w not in _STOP and len(w) > 1]
    return _stemmer.stemWords(toks)


def load(corpus):
    if corpus == "A":
        return load_corpus_a(), load_questions_a()
    return load_corpus_b(codes=default_codes_b()), load_questions_b()


def rrf(rank_lists: list[np.ndarray], k: int = 60, n: int = 0) -> np.ndarray:
    """rank_lists: list of arrays of chunk indices ordered best→worst."""
    score = np.zeros(n)
    for ranks in rank_lists:
        score[ranks] += 1.0 / (k + np.arange(1, len(ranks) + 1))
    return score


def minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


def to_doc_ranking(chunk_scores: np.ndarray, doc_ids: np.ndarray, top: int = 50, agg: str = "max"):
    order = np.argsort(-chunk_scores)
    if agg == "max":
        seen, out = set(), []
        for j in order:
            d = str(doc_ids[j])
            if d not in seen:
                seen.add(d); out.append(d)
                if len(out) >= top:
                    break
        return out
    # sum of top-3 chunk scores per doc
    acc: dict[str, list] = {}
    for j in order[: top * 10]:
        acc.setdefault(str(doc_ids[j]), []).append(float(chunk_scores[j]))
    return [d for d, _ in sorted(acc.items(), key=lambda kv: -sum(sorted(kv[1], reverse=True)[:3]))][:top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A")
    ap.add_argument("--model", default="e5-base")
    ap.add_argument("--chunker", default="fixed1500_title")
    ap.add_argument("--fusions", default="dense,bm25,rrf,convex0.3,convex0.5,convex0.7")
    ap.add_argument("--rerankers", default="none")
    ap.add_argument("--rerank_top", type=int, default=30)
    ap.add_argument("--rerank_base", default="rrf", help="fusion whose candidates are reranked")
    ap.add_argument("--agg", default="max")
    ap.add_argument("--leaderboard", action="store_true")
    a = ap.parse_args()
    if a.leaderboard:
        print_leaderboard(a.corpus); return

    docs, questions = load(a.corpus)
    spec = MODELS[a.model]
    chunks = CHUNKERS[a.chunker](docs)
    texts = [c.text for c in chunks]
    doc_ids = np.array([c.doc_id for c in chunks])
    n = len(chunks)
    key_extra = f"seq{spec.max_seq}|d_prefix={spec.d_prefix!r}|{a.chunker}"
    cache = EmbeddingCache()
    f = cache.dir / (_key(spec.hf_id, texts, key_extra) + ".npy")
    if not f.exists():
        print(f"no cached embeddings for {a.model}/{a.chunker} on corpus {a.corpus}: run experiment 02 first"); sys.exit(1)
    emb = np.load(f)
    enc = Encoder(spec)
    qemb = enc.queries([q.question for q in questions])
    dense = qemb @ emb.T                                   # (nq, n)

    t0 = time.perf_counter()
    retriever = bm25s.BM25(k1=1.2, b=0.75)
    retriever.index([tokenize(t) for t in texts], show_progress=False)
    qtok = [tokenize(q.question) for q in questions]
    bm = np.zeros((len(questions), n), dtype=np.float32)
    for qi, qt in enumerate(qtok):
        bm[qi] = retriever.get_scores(qt)
    bm25_s = time.perf_counter() - t0
    print(f"corpus {a.corpus}: {len(docs)} docs / {n} chunks; bm25 index {bm25_s:.1f}s", flush=True)

    fused: dict[str, np.ndarray] = {}
    for fu in a.fusions.split(","):
        if fu == "dense":
            fused[fu] = dense
        elif fu == "bm25":
            fused[fu] = bm
        elif fu == "rrf":
            fused[fu] = np.stack([rrf([np.argsort(-dense[i])[:200], np.argsort(-bm[i])[:200]], 60, n) for i in range(len(questions))])
        elif fu.startswith("convex"):
            w = float(fu[len("convex"):])
            fused[fu] = np.stack([w * minmax(dense[i]) + (1 - w) * minmax(bm[i]) for i in range(len(questions))])
        rankings = {q.qid: to_doc_ranking(fused[fu][i], doc_ids, agg=a.agg) for i, q in enumerate(questions)}
        res = evaluate_rankings(f"{a.model}__{a.chunker}__{fu}{'' if a.agg == 'max' else '__' + a.agg}", a.corpus, questions, rankings,
                                config={"model": spec.hf_id, "chunker": a.chunker, "fusion": fu, "agg": a.agg, "n_chunks": n})
        save_result(EXP, res); print(res.summary(), flush=True)

    for rk in [r for r in a.rerankers.split(",") if r != "none"]:
        from sentence_transformers import CrossEncoder
        rs = RERANKERS[rk]
        t0 = time.perf_counter()
        ce = CrossEncoder(rs["hf"], max_length=rs["max_len"], device="cpu", trust_remote_code=rs.get("trust", False))
        load_s = time.perf_counter() - t0
        base = fused[a.rerank_base]
        rankings = {}
        t0 = time.perf_counter()
        for i, q in enumerate(questions):
            cand = np.argsort(-base[i])[: a.rerank_top]
            pairs = [(q.question, texts[j]) for j in cand]
            sc = np.asarray(ce.predict(pairs, batch_size=8, show_progress_bar=False), dtype=np.float32)
            full = np.full(n, -1e9, dtype=np.float32); full[cand] = sc
            rankings[q.qid] = to_doc_ranking(full, doc_ids, agg="max")
        rr_s = time.perf_counter() - t0
        res = evaluate_rankings(f"{a.model}__{a.chunker}__{a.rerank_base}+{rk}@{a.rerank_top}", a.corpus, questions, rankings,
                                config={"model": spec.hf_id, "chunker": a.chunker, "fusion": a.rerank_base,
                                        "reranker": rs["hf"], "rerank_top": a.rerank_top, "n_chunks": n},
                                timing={"rerank_s": round(rr_s, 1), "per_query_s": round(rr_s / len(questions), 2),
                                        "reranker_load_s": round(load_s, 1)})
        save_result(EXP, res); print(res.summary(), f"| rerank {rr_s:.0f}s ({rr_s/len(questions):.1f}s/q)", flush=True)
        del ce


if __name__ == "__main__":
    main()
