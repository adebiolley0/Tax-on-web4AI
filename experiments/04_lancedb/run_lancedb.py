#!/usr/bin/env python3
"""Experiment 04 – LanceDB embedded hybrid store.

Builds a LanceDB table per corpus (chunk text + metadata + precomputed
multilingual-e5-small vectors), a native full-text index, and evaluates with the
shared harness:

* ``vector``      – exact (flat) cosine kNN over the chunk vectors
* ``fts_en``      – native FTS, default (English) tokenizer
* ``fts_fr``      – native FTS, ``language="French"`` (Snowball stem + FR stop-words + ASCII folding)
* ``hybrid_rrf``  – ``query_type="hybrid"`` + ``RRFReranker`` (vector top-k ∪ FTS top-k)
* ``hybrid_ce``   – hybrid + ``CrossEncoderReranker`` (multilingual cross-encoder)
* ``vector_ivf``  – approximate search through an IVF_PQ index (to see what the index costs)

Chunk hits are mapped to ``doc_id`` (first occurrence wins) and scored at document level.

Usage:
  uv run python run_lancedb.py --corpus A
  uv run python run_lancedb.py --corpus B --runs vector,fts_fr,hybrid_rrf
  uv run python run_lancedb.py --corpus A --runs hybrid_ce --rerankers bge-reranker-v2-m3,mmarco-minilm
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import torch

torch.set_num_threads(2)  # the 4-core box is shared with the other experiments

import lancedb  # noqa: E402
from lancedb.index import FTS, IvfPq  # noqa: E402
from lancedb.rerankers import CrossEncoderReranker, Reranker, RRFReranker  # noqa: E402

from rag_eval import (EmbeddingCache, evaluate_rankings, save_result, print_leaderboard,  # noqa: E402
                      load_corpus_a, load_questions_a, load_corpus_b, load_questions_b,
                      fixed_chunks, article_chunks)
from rag_eval.corpora import DATA_DIR  # noqa: E402

EXP = "04_lancedb"
HERE = Path(__file__).resolve().parent
DB_DIR = HERE / "lancedb_data"
MODEL = "intfloat/multilingual-e5-small"
Q_PREFIX, D_PREFIX = "query: ", "passage: "
MAX_SEQ = 512
TOP_CHUNKS = 50

RERANKERS = {
    "bge-reranker-v2-m3": ("BAAI/bge-reranker-v2-m3", 1024),
    "mmarco-minilm": ("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1", 512),
}


class TopKCrossEncoderReranker(Reranker):
    """Custom LanceDB reranker: RRF-fuse the two legs, keep the top ``rerank_top`` fused
    candidates, score them with a sentence-transformers CrossEncoder.

    LanceDB's built-in ``CrossEncoderReranker`` scores the *union* of the vector and FTS legs
    (up to 2 x limit rows) with the CrossEncoder defaults (no max_length / batch_size control),
    which is too slow on CPU with a 568M-parameter reranker. This one bounds the work to exactly
    ``rerank_top`` pairs per query. ~25 lines: this is the whole plug-in surface of LanceDB.
    """

    def __init__(self, model_name: str, rerank_top: int = 30, max_length: int = 1024,
                 column: str = "text", batch_size: int = 8):
        super().__init__("relevance")
        from sentence_transformers import CrossEncoder
        self.model_name, self.rerank_top, self.column, self.batch_size = model_name, rerank_top, column, batch_size
        self.rrf = RRFReranker()
        self.model = CrossEncoder(model_name, max_length=max_length, device="cpu")

    def __str__(self):
        return f"TopKCrossEncoderReranker({self.model_name}, top={self.rerank_top})"

    def rerank_hybrid(self, query: str, vector_results: pa.Table, fts_results: pa.Table) -> pa.Table:
        fused = self.rrf.rerank_hybrid(query, vector_results, fts_results).slice(0, self.rerank_top)
        pairs = [(query, t) for t in fused[self.column].to_pylist()]
        scores = self.model.predict(pairs, batch_size=self.batch_size, show_progress_bar=False)
        fused = fused.drop_columns(["_relevance_score"]).append_column(
            "_relevance_score", pa.array(np.asarray(scores, dtype=np.float32)))
        return fused.sort_by([("_relevance_score", "descending")])

# Same chunker keys / cache keys as experiment 02 so the shared EmbeddingCache is reused.
CHUNKERS = {
    "A": ("fixed1500_title", lambda docs: fixed_chunks(docs, 1500, 200, prefix_title=True)),
    "B": ("article_ctx", lambda docs: article_chunks(docs, 2000, 150, prefix_context=True)),
}


def default_codes_b() -> list[str]:
    rep = json.loads((DATA_DIR / "corpus_b" / "parse_report.json").read_text())
    return [k for k, v in rep.items() if v.get("default_subset")]


def load(corpus: str):
    if corpus == "A":
        return load_corpus_a(), load_questions_a()
    return load_corpus_b(codes=default_codes_b()), load_questions_b()


class E5:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        t0 = time.perf_counter()
        self.m = SentenceTransformer(MODEL, device="cpu")
        self.m.max_seq_length = MAX_SEQ
        self.load_s = time.perf_counter() - t0

    def _enc(self, texts, prefix):
        e = self.m.encode([prefix + t for t in texts], batch_size=16, normalize_embeddings=True,
                          show_progress_bar=False)
        return np.asarray(e, dtype=np.float32)

    def docs(self, texts):
        return self._enc(texts, D_PREFIX)

    def queries(self, texts):
        return self._enc(texts, Q_PREFIX)


def build_table(db, corpus: str, chunks, emb: np.ndarray, rebuild: bool):
    """Create (or reuse) the LanceDB table for a corpus. Returns (table, timing)."""
    name = f"chunks_{corpus}"
    timing: dict = {}
    if not rebuild and name in db.table_names():  # list_tables() returns a ListTablesResponse object in 0.39, not a list
        tbl = db.open_table(name)
        if tbl.count_rows() == len(chunks):
            print(f"reusing table {name} ({tbl.count_rows()} rows)")
            return tbl, {"table_reused": True}
    dim = int(emb.shape[1])
    meta_key = "doctype" if corpus == "A" else "code"
    meta_src = "document_type" if corpus == "A" else "code"
    schema = pa.schema([
        pa.field("chunk_id", pa.string()),
        pa.field("doc_id", pa.string()),
        pa.field("title", pa.string()),
        pa.field(meta_key, pa.string()),
        pa.field("text", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), dim)),
    ])
    data = pa.table({
        "chunk_id": [c.chunk_id for c in chunks],
        "doc_id": [c.doc_id for c in chunks],
        "title": [c.title for c in chunks],
        meta_key: [str(c.meta.get(meta_src) or "") for c in chunks],
        "text": [c.text for c in chunks],
        "vector": pa.FixedSizeListArray.from_arrays(pa.array(emb.ravel(), type=pa.float32()), dim),
    }, schema=schema)
    t0 = time.perf_counter()
    tbl = db.create_table(name, data=data, mode="overwrite")
    timing["insert_s"] = round(time.perf_counter() - t0, 2)
    print(f"table {name}: {tbl.count_rows()} rows inserted in {timing['insert_s']}s", flush=True)
    return tbl, timing


def fts_index(tbl, language: str) -> float:
    t0 = time.perf_counter()
    cfg = FTS(language=language, stem=True, remove_stop_words=True, ascii_folding=True, lower_case=True,
              base_tokenizer="simple", with_position=False)
    tbl.create_index("text", config=cfg, replace=True)  # create_fts_index(...) is deprecated since 0.25
    dt = time.perf_counter() - t0
    print(f"FTS index ({language}) built in {dt:.2f}s: {[i.name for i in tbl.list_indices()]}", flush=True)
    return round(dt, 2)


def vector_index(tbl) -> float:
    t0 = time.perf_counter()
    n = tbl.count_rows()
    parts = max(1, int(np.sqrt(n)) // 2)  # ~ sqrt(n)/2 partitions; small tables
    tbl.create_index("vector", config=IvfPq(distance_type="cosine", num_partitions=parts, num_sub_vectors=48),
                     replace=True)
    dt = time.perf_counter() - t0
    print(f"IVF_PQ index (partitions={parts}, sub_vectors=48) built in {dt:.2f}s", flush=True)
    return round(dt, 2)


def to_doc_ranking(rows: list[dict]) -> list[str]:
    seen, out = set(), []
    for r in rows:
        d = r["doc_id"]
        if d not in seen:
            seen.add(d); out.append(d)
    return out


def lat_stats(lat: list[float]) -> dict:
    ms = sorted(x * 1000 for x in lat)
    return {"mean_ms": round(statistics.mean(ms), 1), "p50_ms": round(ms[len(ms) // 2], 1),
            "p95_ms": round(ms[min(len(ms) - 1, int(0.95 * len(ms)))], 1), "max_ms": round(ms[-1], 1)}


def run_queries(questions, fn, warmup=True) -> tuple[dict, list[float]]:
    if warmup:
        fn(0)  # first call pays for lazy opens / model loads
    rankings, lat = {}, []
    for i, q in enumerate(questions):
        t0 = time.perf_counter()
        rows = fn(i)
        lat.append(time.perf_counter() - t0)
        rankings[q.qid] = to_doc_ranking(rows)
    return rankings, lat


def filter_demo(tbl, corpus, questions, qemb):
    """Sanity check of metadata filtering (SQL-ish where clause) on vector / hybrid queries."""
    meta_key = "doctype" if corpus == "A" else "code"
    # take the metadata value of the first expected doc of the first question so the filter is non-empty
    val = tbl.search().where(f"doc_id = '{questions[0].expected[0]}'").limit(1).select([meta_key]).to_list()[0][meta_key]
    q, v = questions[0].question, qemb[0].tolist()
    t0 = time.perf_counter()
    rows = (tbl.search(v, vector_column_name="vector").distance_type("cosine")
            .where(f"{meta_key} = '{val}'", prefilter=True).limit(5).select(["doc_id", meta_key]).to_list())
    dt_v = time.perf_counter() - t0
    t0 = time.perf_counter()
    rows_h = (tbl.search(query_type="hybrid", vector_column_name="vector", fts_columns="text")
              .vector(v).text(q).distance_type("cosine").where(f"{meta_key} = '{val}'", prefilter=True)
              .limit(5).select(["doc_id", meta_key]).rerank(RRFReranker()).to_list())
    dt_h = time.perf_counter() - t0
    ok = all(r[meta_key] == val for r in rows + rows_h)
    print(f"filter demo where {meta_key}='{val}': vector {len(rows)} rows {dt_v*1000:.0f}ms, "
          f"hybrid {len(rows_h)} rows {dt_h*1000:.0f}ms, all-match={ok}: {[r['doc_id'] for r in rows_h]}")
    return {"where": f"{meta_key} = '{val}'", "vector_ms": round(dt_v * 1000, 1), "hybrid_ms": round(dt_h * 1000, 1),
            "all_match": ok}


def print_table(corpus: str) -> None:
    """Markdown table of the latest 04_lancedb runs (plus reference rows from 01/02/03/06)."""
    from rag_eval.results import LEADERBOARD
    rows = [json.loads(l) for l in LEADERBOARD.read_text().splitlines() if l.strip()]
    latest: dict = {}
    for r in rows:
        if r["corpus"] == corpus:
            latest[(r["experiment"], r["run"])] = r
    print("| run | MRR | nDCG@5 | nDCG@10 | hit@1 | hit@5 | hit@10 | recall@10 | query ms (mean / p95) | index / build |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for (exp, run), r in sorted(latest.items(), key=lambda kv: -kv[1]["mrr"]):
        if exp != EXP:
            continue
        t = r.get("timing", {}); q = t.get("query", {})
        build = ", ".join(f"{k.replace('_s', '')} {v}s" for k, v in t.items()
                          if k in ("encode_docs_s", "insert_s", "fts_index_s", "vector_index_s", "reranker_load_s") and v)
        print(f"| `{run}` | {r['mrr']:.3f} | {r['ndcg@5']:.3f} | {r['ndcg@10']:.3f} | {r['hit@1']:.3f} | {r['hit@5']:.3f} | "
              f"{r['hit@10']:.3f} | {r['recall@10']:.3f} | {q.get('mean_ms', '')} / {q.get('p95_ms', '')} | {build} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A")
    ap.add_argument("--runs", default="vector,fts_en,fts_fr,hybrid_rrf,hybrid_ce,vector_ivf")
    ap.add_argument("--rerankers", default="mmarco-minilm", help="comma list of RERANKERS keys (mmarco-minilm is ~6x faster than bge-reranker-v2-m3 on CPU)")
    ap.add_argument("--ce_limit", type=int, default=30, help="cross-encoder candidates (rrf top-k; with --ce_builtin: per-leg limit)")
    ap.add_argument("--ce_builtin", action="store_true", help="use lancedb.rerankers.CrossEncoderReranker instead of the custom top-k reranker")
    ap.add_argument("--rebuild", action="store_true", help="recreate the LanceDB table even if it exists")
    ap.add_argument("--leaderboard", action="store_true")
    ap.add_argument("--table", action="store_true", help="print the markdown results table for this corpus (README)")
    a = ap.parse_args()
    if a.leaderboard:
        print_leaderboard(a.corpus); return
    if a.table:
        print_table(a.corpus); return
    runs = [r for r in a.runs.split(",") if r and r != "none"]

    docs, questions = load(a.corpus)
    ck, chunker = CHUNKERS[a.corpus]
    chunks = chunker(docs)
    texts = [c.text for c in chunks]
    print(f"corpus {a.corpus}: {len(docs)} docs / {len(chunks)} chunks / {len(questions)} questions; lancedb {lancedb.__version__}",
          flush=True)

    enc = E5()
    cache = EmbeddingCache()
    key_extra = f"seq{MAX_SEQ}|d_prefix={D_PREFIX!r}|{ck}"
    emb, enc_s = cache.get_or_compute(MODEL, texts, enc.docs, extra=key_extra, label=f"{a.corpus}/{ck}")
    print(f"chunk embeddings: {emb.shape} encode={enc_s:.0f}s{' (cached)' if enc_s == 0 else ''}", flush=True)
    t0 = time.perf_counter()
    qemb = enc.queries([q.question for q in questions])
    q_enc_s = time.perf_counter() - t0

    DB_DIR.mkdir(exist_ok=True)
    db = lancedb.connect(str(DB_DIR))
    tbl, build_t = build_table(db, a.corpus, chunks, emb, a.rebuild)
    base_cfg = {"model": MODEL, "chunker": ck, "n_chunks": len(chunks), "dim": int(emb.shape[1]),
                "lancedb": lancedb.__version__, "top_chunks": TOP_CHUNKS}
    base_t = {"encode_docs_s": round(enc_s, 1), "encode_queries_s": round(q_enc_s, 2), **build_t}
    sel = ["chunk_id", "doc_id"]

    def save(run, rankings, lat, cfg, tim):
        res = evaluate_rankings(f"lancedb__e5-small__{run}", a.corpus, questions, rankings,
                                config={**base_cfg, **cfg}, timing={**base_t, **tim, "query": lat_stats(lat)})
        save_result(EXP, res)
        print(res.summary(), f"| {lat_stats(lat)['mean_ms']:.0f} ms/q (p95 {lat_stats(lat)['p95_ms']:.0f})", flush=True)

    fts_lang = None
    for run in runs:
        if run == "vector":
            def fn(i):
                return (tbl.search(qemb[i].tolist(), vector_column_name="vector").distance_type("cosine")
                        .bypass_vector_index().limit(TOP_CHUNKS).select(sel).to_list())
            rk, lat = run_queries(questions, fn)
            save(run, rk, lat, {"search": "flat cosine"}, {})
        elif run in ("fts_en", "fts_fr"):
            fts_lang = "English" if run == "fts_en" else "French"
            fts_s = fts_index(tbl, fts_lang)
            def fn(i):
                return (tbl.search(questions[i].question, query_type="fts", fts_columns="text")
                        .limit(TOP_CHUNKS).select(sel).to_list())
            rk, lat = run_queries(questions, fn)
            save(run, rk, lat, {"search": "native fts", "language": fts_lang, "stem": True,
                                "remove_stop_words": True, "ascii_folding": True}, {"fts_index_s": fts_s})
        elif run == "hybrid_rrf":
            if fts_lang != "French":
                fts_lang = "French"; fts_index(tbl, fts_lang)
            rr = RRFReranker()
            def fn(i):
                return (tbl.search(query_type="hybrid", vector_column_name="vector", fts_columns="text")
                        .vector(qemb[i].tolist()).text(questions[i].question).distance_type("cosine")
                        .bypass_vector_index().limit(TOP_CHUNKS).select(sel).rerank(rr).to_list())
            rk, lat = run_queries(questions, fn)
            save(run, rk, lat, {"search": "hybrid", "fts_language": fts_lang, "reranker": "RRFReranker(K=60)"}, {})
        elif run == "hybrid_ce":
            if fts_lang != "French":
                fts_lang = "French"; fts_index(tbl, fts_lang)
            for rk_key in a.rerankers.split(","):
                hf, max_len = RERANKERS[rk_key]
                t0 = time.perf_counter()
                if a.ce_builtin:   # LanceDB's own plug-in: reranks the union of both legs (<= 2*limit rows)
                    ce = CrossEncoderReranker(model_name=hf, column="text", device="cpu")
                    _ = ce.model
                    limit, cand, rname = a.ce_limit, f"<= {2 * a.ce_limit} (union of legs)", f"hybrid+{rk_key}@union{a.ce_limit}"
                else:              # custom plug-in: RRF top-`ce_limit` only
                    ce = TopKCrossEncoderReranker(hf, rerank_top=a.ce_limit, max_length=max_len)
                    limit, cand, rname = TOP_CHUNKS, f"{a.ce_limit} (rrf top-k)", f"hybrid_rrf+{rk_key}@{a.ce_limit}"
                load_s = time.perf_counter() - t0
                def fn(i):
                    return (tbl.search(query_type="hybrid", vector_column_name="vector", fts_columns="text")
                            .vector(qemb[i].tolist()).text(questions[i].question).distance_type("cosine")
                            .bypass_vector_index().limit(limit).select(sel + ["text"]).rerank(ce).to_list())
                rk, lat = run_queries(questions, fn)
                save(rname, rk, lat,
                     {"search": "hybrid", "fts_language": fts_lang, "reranker": str(ce), "hybrid_limit": limit,
                      "candidates": cand, "max_length": None if a.ce_builtin else max_len},
                     {"reranker_load_s": round(load_s, 1)})
                del ce
        elif run == "vector_ivf":
            idx_s = vector_index(tbl)
            def fn(i):
                return (tbl.search(qemb[i].tolist(), vector_column_name="vector").distance_type("cosine")
                        .nprobes(10).limit(TOP_CHUNKS).select(sel).to_list())
            rk, lat = run_queries(questions, fn)
            save(run, rk, lat, {"search": "IVF_PQ nprobes=10 sub_vectors=48"}, {"vector_index_s": idx_s})
        else:
            print(f"unknown run {run}"); sys.exit(1)

    demo = filter_demo(tbl, a.corpus, questions, qemb)
    (HERE / f"filter_demo_{a.corpus}.json").write_text(json.dumps(demo, indent=1))
    size = sum(p.stat().st_size for p in (DB_DIR / f"chunks_{a.corpus}.lance").rglob("*") if p.is_file())
    print(f"on-disk size of chunks_{a.corpus}.lance: {size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
