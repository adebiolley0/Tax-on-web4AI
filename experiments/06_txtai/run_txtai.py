#!/usr/bin/env python3
"""Experiment 06 – txtai all-in-one Embeddings database.

One ``txtai.Embeddings`` object holds the dense index (Faiss), the sparse BM25
terms index, and a SQLite content store with metadata.  We evaluate:

* dense only          (weights=1.0 on the hybrid index)
* BM25 only           (weights=0.0 on the hybrid index, French-aware tokenizer)
* BM25 only           (separate keyword index, txtai *default* tokenizer)
* hybrid convex fusion with dense weight 0.3 / 0.5 / 0.7
* hybrid 0.5 + cross-encoder rerank of the top 30 (txtai Reranker + Similarity)

Usage:
  uv run python run_txtai.py --corpus A
  uv run python run_txtai.py --corpus B --no-rerank
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

torch.set_num_threads(2)

from txtai import Embeddings  # noqa: E402
from txtai.pipeline import Reranker, Similarity  # noqa: E402

from rag_eval import (article_chunks, evaluate_rankings, fixed_chunks, load_corpus_a,  # noqa: E402
                      load_corpus_b, load_questions_a, load_questions_b, save_result)
from rag_eval.corpora import DATA_DIR  # noqa: E402

EXP = "06_txtai"
HERE = Path(__file__).resolve().parent
INDEX_DIR = HERE / "txtai_index"
MODEL = "intfloat/multilingual-e5-small"
RERANKER = "BAAI/bge-reranker-v2-m3"
TOP = 50

# French stop words (same list as experiments 01/03) – txtai only ships English ones.
FR_STOP = sorted(set("""le la les l un une des du de d et ou à a au aux en dans par pour sur avec sans sous ce cet cette ces
se sa son ses leur leurs mon ma mes ton ta tes notre nos votre vos qui que quoi dont où ne pas plus est sont
été être ont a avoir il elle ils elles on nous vous je tu y ne n s c qu d l lorsque lorsqu si comme mais donc
or ni car tout tous toute toutes même autre autres entre vers chez ainsi aussi alors""".split()))

# txtai's default UAX#29 tokenizer keeps "l'impôt" as one token; this regexp splits on
# anything that is not a letter/digit run so elisions are separated.  No stemmer and no
# accent folding exist in txtai's Tokenizer.
FR_TOKENIZER = {"regexp": r"\p{L}+|\d+", "stopwords": FR_STOP}

SCORING_FR = {"method": "bm25", "terms": True, "normalize": True, "tokenizer": FR_TOKENIZER}
SCORING_DEFAULT = {"method": "bm25", "terms": True, "normalize": True}

HYBRID_CONFIG = {
    "path": MODEL,
    "method": "sentence-transformers",
    "instructions": {"query": "query: ", "data": "passage: "},
    "encodebatch": 32,
    "content": True,        # SQLite store -> results carry text + metadata, SQL filters work
    "hybrid": True,         # dense + sparse
    "scoring": SCORING_FR,
}


def default_codes_b() -> list[str]:
    rep = json.loads((DATA_DIR / "corpus_b" / "parse_report.json").read_text())
    return [k for k, v in rep.items() if isinstance(v, dict) and v.get("default_subset")]


def load(corpus: str):
    if corpus == "A":
        docs, qs = load_corpus_a(), load_questions_a()
        chunks = fixed_chunks(docs, 1500, 200, prefix_title=True)
    else:
        docs, qs = load_corpus_b(codes=default_codes_b()), load_questions_b()
        chunks = article_chunks(docs, 2000, 150, prefix_context=True)
    return docs, qs, chunks


def to_documents(chunks, corpus: str):
    """txtai documents: (id, dict, tags). Extra dict keys land in the SQLite `data`
    JSON column and are queryable as SQL columns."""
    for c in chunks:
        row = {"text": c.text, "doc_id": c.doc_id, "title": c.title}
        if corpus == "A":
            row["document_type"] = c.meta.get("document_type")
            row["document_date"] = c.meta.get("document_date")
        else:
            code = c.meta.get("code") or ""
            row["code"] = code
            row["article"] = c.meta.get("article")
            row["region"] = next((r for r in ("wal", "bxl", "vla") if code.endswith("_" + r)), "federal")
        yield (c.chunk_id, row, None)


def build_or_load(name: str, config: dict, chunks, corpus: str, rebuild: bool) -> tuple[Embeddings, float]:
    path = INDEX_DIR / name
    emb = Embeddings(config)
    if path.exists() and not rebuild:
        t0 = time.perf_counter()
        emb.load(str(path))
        print(f"[{name}] loaded from {path} in {time.perf_counter() - t0:.1f}s ({emb.count()} rows)", flush=True)
        return emb, 0.0
    t0 = time.perf_counter()
    emb.index(to_documents(chunks, corpus))
    build_s = time.perf_counter() - t0
    emb.save(str(path))
    print(f"[{name}] indexed {emb.count()} chunks in {build_s:.1f}s -> {path}", flush=True)
    return emb, build_s


def rankings_from(results, chunk2doc) -> dict:
    out = {}
    for qid, rows in results.items():
        seen, docs = set(), []
        for r in rows:
            d = chunk2doc[r["id"]]
            if d not in seen:
                seen.add(d); docs.append(d)
        out[qid] = docs
    return out


def run_search(emb: Embeddings, questions, weights: float | None, chunk2doc, limit: int = TOP):
    qtexts = [q.question for q in questions]
    t0 = time.perf_counter()
    res = emb.batchsearch(qtexts, limit, weights=weights) if weights is not None else emb.batchsearch(qtexts, limit)
    dt = time.perf_counter() - t0
    return rankings_from({q.qid: r for q, r in zip(questions, res)}, chunk2doc), dt


def sql_demo(emb: Embeddings, corpus: str) -> str:
    """Metadata filter + semantic search in one SQL statement."""
    if corpus == "B":
        q, sql = ("Quel est le taux normal de la TVA ?",
                  "select id, code, region, score from txtai where code = 'ctva' and similar(:q, 100, 0.5) limit 5")
        q2, sql2 = ("droits de succession en ligne directe",
                    "select id, code, region, score from txtai where region = 'wal' and similar(:q, 100, 0.5) limit 5")
    else:
        q, sql = ("rentes alimentaires déductibles",
                  "select id, document_type, score from txtai where document_type = 'Circulaires' and similar(:q, 100, 0.5) limit 5")
        q2, sql2 = ("voiture de société avantage de toute nature",
                    "select id, document_type, document_date, score from txtai where document_date >= '2020' and similar(:q, 100, 0.5) limit 5")
    lines = []
    for question, stmt in ((q, sql), (q2, sql2)):
        t0 = time.perf_counter()
        rows = emb.search(stmt, parameters={"q": question})
        dt = (time.perf_counter() - t0) * 1000
        lines.append(f"-- {stmt}\n--   :q = {question!r}   ({dt:.0f} ms)")
        for r in rows:
            lines.append("   " + json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}, ensure_ascii=False))
    out = "\n".join(lines)
    print(out, flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--no-rerank", action="store_true")
    ap.add_argument("--rerank-top", type=int, default=30)
    a = ap.parse_args()
    corpus = a.corpus

    docs, questions, chunks = load(corpus)
    chunk2doc = {c.chunk_id: c.doc_id for c in chunks}
    print(f"corpus {corpus}: {len(docs)} docs / {len(chunks)} chunks / {len(questions)} questions", flush=True)
    INDEX_DIR.mkdir(exist_ok=True)

    base_cfg = {"model": MODEL, "chunker": "fixed1500_title" if corpus == "A" else "article2000_ctx",
                "n_chunks": len(chunks), "top": TOP, "txtai_scoring": SCORING_FR, "fusion": "convex (normalize=True)"}

    # ---- hybrid index (dense + sparse FR tokenizer) ---------------------------------
    t0 = time.perf_counter()
    hyb, build_s = build_or_load(f"{corpus}_hybrid_e5small", HYBRID_CONFIG, chunks, corpus, a.rebuild)
    total_build = time.perf_counter() - t0
    timing_base = {"index_build_s": round(build_s, 1), "build_or_load_wall_s": round(total_build, 1)}

    runs = [("txtai__e5-small__dense", 1.0, "dense only (weights=1.0)"),
            ("txtai__e5-small__bm25", 0.0, "bm25 only, FR regexp tokenizer + FR stopwords (weights=0.0)"),
            ("txtai__e5-small__hybrid_w0.3", 0.3, "hybrid convex, dense weight 0.3"),
            ("txtai__e5-small__hybrid_w0.5", 0.5, "hybrid convex, dense weight 0.5"),
            ("txtai__e5-small__hybrid_w0.7", 0.7, "hybrid convex, dense weight 0.7")]
    hybrid_rankings = {}
    for name, w, desc in runs:
        rk, dt = run_search(hyb, questions, w, chunk2doc)
        hybrid_rankings[w] = rk
        res = evaluate_rankings(name, corpus, questions, rk,
                                config={**base_cfg, "dense_weight": w, "desc": desc},
                                timing={**timing_base, "search_s": round(dt, 2), "per_query_ms": round(1000 * dt / len(questions), 1)})
        save_result(EXP, res); print(res.summary(), f"| {1000*dt/len(questions):.0f} ms/q", flush=True)

    # ---- bm25-only index with txtai's DEFAULT tokenizer (no FR handling) -----------
    kw_cfg = {"keyword": True, "content": True, "scoring": SCORING_DEFAULT}
    kw, kw_build = build_or_load(f"{corpus}_bm25_default_tok", kw_cfg, chunks, corpus, a.rebuild)
    rk, dt = run_search(kw, questions, None, chunk2doc)
    res = evaluate_rankings("txtai__bm25_default_tokenizer", corpus, questions, rk,
                            config={**base_cfg, "model": None, "txtai_scoring": SCORING_DEFAULT,
                                    "desc": "keyword-only index, txtai default UAX#29 tokenizer, no stopwords"},
                            timing={"index_build_s": round(kw_build, 1), "search_s": round(dt, 2),
                                    "per_query_ms": round(1000 * dt / len(questions), 1)})
    save_result(EXP, res); print(res.summary(), f"| {1000*dt/len(questions):.0f} ms/q", flush=True)

    # ---- SQL metadata filter demo -------------------------------------------------
    demo = sql_demo(hyb, corpus)
    (HERE / f"sql_demo_{corpus}.txt").write_text(demo + "\n", encoding="utf-8")

    # ---- cross-encoder rerank via txtai Reranker + Similarity(crossencode) -------
    if not a.no_rerank:
        t0 = time.perf_counter()
        sim = Similarity(RERANKER, crossencode=True, gpu=False)
        load_s = time.perf_counter() - t0
        reranker = Reranker(hyb, sim)
        qtexts = [q.question for q in questions]
        t0 = time.perf_counter()
        reranked = reranker(qtexts, limit=a.rerank_top, factor=1, weights=0.5)
        rr_s = time.perf_counter() - t0
        rk = {}
        for q, rows in zip(questions, reranked):
            top = rankings_from({q.qid: rows}, chunk2doc)[q.qid]
            tail = [d for d in hybrid_rankings[0.5][q.qid] if d not in top]
            rk[q.qid] = top + tail
        res = evaluate_rankings(f"txtai__e5-small__hybrid_w0.5+bge-reranker-v2-m3@{a.rerank_top}", corpus, questions, rk,
                                config={**base_cfg, "dense_weight": 0.5, "reranker": RERANKER, "rerank_top": a.rerank_top,
                                        "desc": "txtai Reranker(Embeddings, Similarity(crossencode=True)) on top-30 hybrid hits"},
                                timing={**timing_base, "reranker_load_s": round(load_s, 1), "rerank_s": round(rr_s, 1),
                                        "per_query_s": round(rr_s / len(questions), 2)})
        save_result(EXP, res); print(res.summary(), f"| rerank {rr_s:.0f}s ({rr_s/len(questions):.1f}s/q)", flush=True)


if __name__ == "__main__":
    main()
