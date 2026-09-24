#!/usr/bin/env python3
"""Experiment 02 – dense retrieval sweep: embedding model × chunking strategy.

Retrieval is plain cosine similarity in numpy (no vector DB) so that only the
model / chunking choice is measured. Document score = max over its chunks.

Usage:
  uv run python run_sweep.py --corpus A --models minilm-l12,e5-small --chunkers fixed1500,fixed1500_title
  uv run python run_sweep.py --corpus B --models e5-base --chunkers article_ctx
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from rag_eval import (EmbeddingCache, evaluate_rankings, save_result, print_leaderboard,
                      load_corpus_a, load_questions_a, load_corpus_b, load_questions_b,
                      whole_doc, fixed_chunks, article_chunks)
from rag_eval.corpora import DATA_DIR
from models import MODELS, ModelSpec

EXP = "02_dense_sweep"


def default_codes_b() -> list[str]:
    rep = json.loads((DATA_DIR / "corpus_b" / "parse_report.json").read_text())
    return [k for k, v in rep.items() if v.get("default_subset")]


def load(corpus: str, clean: bool = False):
    if corpus == "A":
        return load_corpus_a(), load_questions_a()
    docs = load_corpus_b(codes=default_codes_b())
    if clean:  # experiment 08: strip amendment-history preambles
        sys.path.insert(0, str((DATA_DIR.parent / "08_corpus_b_cleanup").resolve()))
        from cleanup import clean_article
        docs = [type(d)(d.doc_id, d.title, clean_article(d.text), dict(d.meta)) for d in docs]
    return docs, load_questions_b()


CHUNKERS = {
    # corpus A
    "whole": lambda docs: whole_doc(docs),
    "fixed1500": lambda docs: fixed_chunks(docs, 1500, 200),
    "fixed1500_title": lambda docs: fixed_chunks(docs, 1500, 200, prefix_title=True),
    "fixed800_title": lambda docs: fixed_chunks(docs, 800, 100, prefix_title=True),
    "fixed3000_title": lambda docs: fixed_chunks(docs, 3000, 300, prefix_title=True),
    # corpus B (articles)
    "article_ctx": lambda docs: article_chunks(docs, 2000, 150, prefix_context=True),
    "article_noctx": lambda docs: article_chunks(docs, 2000, 150, prefix_context=False),
    "article_ctx_1000": lambda docs: article_chunks(docs, 1000, 100, prefix_context=True),
    # token-safe for 512-token encoders: 1200 chars + heading context ≈ 330-450 e5 tokens (exp 05 finding)
    "article_ctx_1200": lambda docs: article_chunks(docs, 1200, 100, prefix_context=True),
}


class Encoder:
    def __init__(self, spec: ModelSpec):
        self.spec = spec
        t0 = time.perf_counter()
        if spec.kind == "model2vec":
            from model2vec import StaticModel
            self.m = StaticModel.from_pretrained(spec.hf_id)
        else:
            from sentence_transformers import SentenceTransformer
            self.m = SentenceTransformer(spec.hf_id, device="cpu", trust_remote_code=spec.trust_remote_code,
                                         **spec.st_kwargs)
            try:
                self.m.max_seq_length = spec.max_seq
            except AttributeError:  # static embedding models have no sequence limit
                pass
        self.load_s = time.perf_counter() - t0

    def _enc(self, texts, prefix, kw):
        texts = [prefix + t for t in texts]
        if self.spec.kind == "model2vec":
            e = self.m.encode(texts)
        else:
            e = self.m.encode(texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False, **kw)
        e = np.asarray(e, dtype=np.float32)
        n = np.linalg.norm(e, axis=1, keepdims=True); n[n == 0] = 1
        return e / n

    def docs(self, texts):
        return self._enc(texts, self.spec.d_prefix, self.spec.encode_kwargs)

    def queries(self, texts):
        return self._enc(texts, self.spec.q_prefix, self.spec.q_encode_kwargs)


def run(corpus: str, model_keys: list[str], chunker_keys: list[str], top_docs: int = 50, clean: bool = False) -> None:
    docs, questions = load(corpus, clean)
    tag = "_clean" if clean else ""
    cache = EmbeddingCache()
    print(f"corpus {corpus}: {len(docs)} docs, {len(questions)} questions")
    for mk in model_keys:
        spec = MODELS[mk]
        enc = None
        for ck in chunker_keys:
            chunks = CHUNKERS[ck](docs)
            texts = [c.text for c in chunks]
            key_extra = f"seq{spec.max_seq}|d_prefix={spec.d_prefix!r}|{ck}"
            from rag_eval.cache import _key
            cached = (cache.dir / (_key(spec.hf_id, texts, key_extra) + ".npy")).exists()
            if enc is None:
                enc = Encoder(spec)
            emb, enc_s = cache.get_or_compute(spec.hf_id, texts, enc.docs, extra=key_extra, label=f"{corpus}/{ck}")
            qtexts = [q.question for q in questions]
            t1 = time.perf_counter()
            qemb = enc.queries(qtexts)
            q_s = time.perf_counter() - t1
            t2 = time.perf_counter()
            sims = qemb @ emb.T                       # (nq, nchunks)
            doc_ids = np.array([c.doc_id for c in chunks])
            rankings = {}
            for qi, q in enumerate(questions):
                order = np.argsort(-sims[qi])
                seen, ranked = set(), []
                for j in order:
                    d = doc_ids[j]
                    if d not in seen:
                        seen.add(d); ranked.append(str(d))
                        if len(ranked) >= top_docs:
                            break
                rankings[q.qid] = ranked
            search_s = time.perf_counter() - t2
            name = f"{mk}__{ck}{tag}"
            res = evaluate_rankings(name, corpus, questions, rankings,
                                    config={"model": spec.hf_id, "chunker": ck, "max_seq": spec.max_seq, "clean": clean,
                                            "n_chunks": len(chunks), "dim": int(emb.shape[1]),
                                            "q_prefix": spec.q_prefix, "d_prefix": spec.d_prefix},
                                    timing={"encode_docs_s": round(enc_s, 1), "encode_queries_s": round(q_s, 2),
                                            "search_s": round(search_s, 3), "model_load_s": round(enc.load_s, 1),
                                            "cached": cached})
            save_result(EXP, res)
            print(res.summary(), f"| chunks={len(chunks)} enc={enc_s:.0f}s{' (cached)' if cached else ''}", flush=True)
        enc = None  # free memory before next model


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A")
    ap.add_argument("--models", default="minilm-l12,e5-small")
    ap.add_argument("--chunkers", default="fixed1500,fixed1500_title")
    ap.add_argument("--leaderboard", action="store_true")
    ap.add_argument("--clean", action="store_true", help="corpus B: apply experiment-08 article cleanup")
    a = ap.parse_args()
    if a.leaderboard:
        print_leaderboard(a.corpus); sys.exit()
    run(a.corpus, a.models.split(","), a.chunkers.split(","), clean=a.clean)
