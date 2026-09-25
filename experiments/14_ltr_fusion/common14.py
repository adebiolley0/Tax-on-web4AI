"""Shared pieces for experiment 14 (LTR / fusion tuning).

* corpus loading + chunking identical to the experiments whose embeddings are cached
  (A: fixed1500_title, B: article_ctx_1200, C: fixed1200_title)
* first-stage score matrices (dense legs from the shared EmbeddingCache, BM25 at chunk and
  document level) cached once per corpus in ``cache/<corpus>_stage1.npz``
* deterministic candidate sets per question (union of the top-K chunks of each leg)
* fusion helpers (convex / RRF at chunk level, document ranking = max chunk)
"""
from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np

from rag_eval import (load_corpus_a, load_questions_a, load_corpus_b, load_questions_b,
                      load_corpus_c, load_questions_c, fixed_chunks, article_chunks)
from rag_eval.cache import EmbeddingCache, _key
from rag_eval.corpora import DATA_DIR

EXP = "14_ltr_fusion"
EXP_DIR = Path(__file__).resolve().parent
CACHE = EXP_DIR / "cache"
CACHE.mkdir(exist_ok=True)
for _p in ("01_bm25", "02_dense_sweep", "03_hybrid_rerank", "08_corpus_b_cleanup"):
    sys.path.insert(0, str((DATA_DIR.parent / _p).resolve()))
from models import MODELS  # noqa: E402
from run_sweep import Encoder, default_codes_b  # noqa: E402
from run_hybrid import RERANKERS  # noqa: E402
from cleanup import detect_region, region_of_code  # noqa: E402
from run_bm25 import TokCfg, make_tokenizer  # noqa: E402  (01_bm25)

# exp 01's best French normalisation: Snowball stem + bm25s French stoplist + question-word
# stoplist + accent folding (whole-doc BM25 0.695 on A vs 0.652 with the exp-03 tokenizer)
tokenize = make_tokenizer(TokCfg(stem=True, stopwords=True, accents=False, qstop=True))

# Which cached dense legs exist per corpus: leg name -> (model key, cache-key extra)
DENSE_LEGS = {
    "A": {"e5": ("e5-small", "seq512|d_prefix='passage: '|fixed1500_title"),
          "bgem3": ("bge-m3", "seq512|d_prefix=''|fixed1500_title")},
    "B": {"e5": ("e5-small", "seq512|d_prefix='passage: '|article_ctx_1200")},
    "C": {"e5": ("e5-small", "seq512|d_prefix='passage: '|C/fixed1200_title"),
          "potion": ("potion-ml-128m", "seq512|d_prefix=''|C/fixed1200_title")},
}
TOP_CAND = 30          # per-leg depth for the (expensive) bge candidate set
TOP_CAND_WIDE = 50     # per-leg depth for the (cheap) mmarco candidate set


def load_corpus_and_chunks(corpus: str):
    if corpus == "A":
        docs, questions = load_corpus_a(), load_questions_a()
        chunks = fixed_chunks(docs, 1500, 200, prefix_title=True)
        doc_texts = [d.text for d in docs]                       # exp 01 best: whole doc
    elif corpus == "B":
        docs, questions = load_corpus_b(codes=default_codes_b()), load_questions_b()
        chunks = article_chunks(docs, 1200, 100, prefix_context=True)
        doc_texts = []                                            # exp 01 best: article + heading path
        for d in docs:
            hp = d.meta.get("heading_path") or []
            doc_texts.append(f"{d.title}\n" + (" > ".join(hp) + "\n" if hp else "") + d.text)
    elif corpus == "C":
        docs, questions = load_corpus_c(max_chars=200_000), load_questions_c()
        chunks = fixed_chunks(docs, 1200, 100, prefix_title=True)
        doc_texts = [d.text[:200_000] for d in docs]
    else:
        raise ValueError(corpus)
    return docs, questions, chunks, doc_texts


class Stage1:
    """First-stage scores for one corpus (loaded from cache/<corpus>_stage1.npz)."""

    def __init__(self, corpus: str):
        self.corpus = corpus
        f = CACHE / f"{corpus}_stage1.npz"
        if not f.exists():
            raise FileNotFoundError(f"{f} missing: run build_stage1.py --corpus {corpus}")
        z = np.load(f, allow_pickle=False)
        self.legs: dict[str, np.ndarray] = {k[4:]: z[k] for k in z.files if k.startswith("leg_")}   # chunk-level (nq, nchunks)
        self.bm25_doc: np.ndarray = z["bm25_doc"]                                                   # (nq, ndocs)
        self.chunk_doc: np.ndarray = z["chunk_doc"]                                                 # (nchunks,) doc index
        self.chunk_pos: np.ndarray = z["chunk_pos"]                                                 # (nchunks,) position within doc
        self.doc_start: np.ndarray = z["doc_start"]                                                 # (ndocs+1,) chunk range per doc
        meta = json.loads((CACHE / f"{corpus}_stage1.json").read_text())
        self.doc_ids: list[str] = meta["doc_ids"]
        self.qids: list[str] = meta["qids"]
        self.doc_len: np.ndarray = np.asarray(meta["doc_len"])
        self.nq, self.nchunks = self.legs["e5"].shape
        self.ndocs = len(self.doc_ids)

    # ── candidate sets ──────────────────────────────────────────────────────
    def candidates(self, qi: int, top: int = TOP_CAND, legs: tuple[str, ...] | None = None,
                   with_doc_leg: bool | None = None) -> np.ndarray:
        """Union of the top-``top`` chunks of every leg (+ the best-BM25 chunk of the top-``top``
        whole-document BM25 docs on A/B, where the document-level BM25 is the strongest lexical
        leg). Sorted chunk indices."""
        legs = legs or tuple(self.legs)
        if with_doc_leg is None:
            with_doc_leg = self.corpus in ("A", "B")
        s: set[int] = set()
        for lg in legs:
            s.update(np.argpartition(-self.legs[lg][qi], top)[:top].tolist())
        if with_doc_leg:
            bm = self.legs["bm25"][qi]
            for d in np.argpartition(-self.bm25_doc[qi], top)[:top]:
                a, b = self.doc_start[d], self.doc_start[d + 1]
                s.add(int(a + np.argmax(bm[a:b])))
        return np.array(sorted(s), dtype=np.int64)

    def candidate_sets(self, top: int, **kw) -> list[np.ndarray]:
        return [self.candidates(qi, top, **kw) for qi in range(self.nq)]

    # ── document-level aggregation ───────────────────────────────────────────
    def doc_max(self, chunk_scores: np.ndarray) -> np.ndarray:
        out = np.full(self.ndocs, -np.inf, dtype=np.float64)
        np.maximum.at(out, self.chunk_doc, chunk_scores)
        return out


def ranks_of(scores: np.ndarray) -> np.ndarray:
    """1-based rank of every element (descending)."""
    order = np.argsort(-scores, kind="stable")
    r = np.empty(len(scores), dtype=np.int64)
    r[order] = np.arange(1, len(scores) + 1)
    return r


def minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(x.min()), float(x.max())
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x, dtype=np.float64)


def rrf_scores(legs: list[np.ndarray], k: float = 60.0, depth: int = 300) -> np.ndarray:
    """Chunk-level RRF over the top-``depth`` chunks of each leg (as in exp 03/09)."""
    n = len(legs[0])
    out = np.zeros(n, dtype=np.float64)
    for s in legs:
        top = np.argpartition(-s, depth)[:depth]
        top = top[np.argsort(-s[top], kind="stable")]
        out[top] += 1.0 / (k + np.arange(1, depth + 1))
    return out


def convex_scores(dense: np.ndarray, bm25: np.ndarray, w: float) -> np.ndarray:
    return w * minmax(dense) + (1.0 - w) * minmax(bm25)


def doc_ranking(st: Stage1, chunk_scores: np.ndarray, top: int = 50) -> list[str]:
    """Documents ordered by their best chunk (dedupe on first occurrence)."""
    k = min(len(chunk_scores), top * 40)
    cand = np.argpartition(-chunk_scores, k - 1)[:k] if k < len(chunk_scores) else np.arange(len(chunk_scores))
    cand = cand[np.argsort(-chunk_scores[cand], kind="stable")]
    seen: set[int] = set()
    out: list[str] = []
    for j in cand:
        d = int(st.chunk_doc[j])
        if d not in seen:
            seen.add(d)
            out.append(st.doc_ids[d])
            if len(out) >= top:
                break
    return out


# ── cheap text features ──────────────────────────────────────────────────────
_YEAR_RE = re.compile(r"\b(20[0-3]\d)\b")
_REV_RE = re.compile(r"revenus[_ ](20\d\d)")


def query_year(q: str) -> int | None:
    m = _YEAR_RE.search(q)
    return int(m.group(1)) if m else None


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def doc_region_c(doc_id: str, title: str, path: list[str]) -> str | None:
    """Region of a corpus-C document from its id / title / taxonomy path."""
    m = re.search(r"_(wa|br|vl)_", doc_id)
    if m:
        return {"wa": "wal", "br": "bxl", "vl": "vla"}[m.group(1)]
    t = fold(title + " " + " ".join(path or []))
    if re.search(r"wallon|wallonie", t):
        return "wal"
    if re.search(r"bruxell|brussel", t):
        return "bxl"
    if re.search(r"flamand|vlaams|vlaanderen|flandre", t):
        return "vla"
    return None
