"""Shared plumbing for experiment 12: corpora/chunks, BM25 leg, cached dense legs,
fusion helpers, train/val-protocol evaluation and result saving.

Everything here mirrors experiments 02/03 (same chunkers, same BM25 tokenizer, same
embedding cache keys) so that the numbers are directly comparable.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("EXP12_THREADS", "2")))

from rag_eval import (evaluate_rankings, save_result, load_corpus_a, load_questions_a,  # noqa: E402
                      load_corpus_b, load_questions_b, fixed_chunks, article_chunks)
from rag_eval.cache import _key, CACHE_DIR  # noqa: E402
from rag_eval.corpora import DATA_DIR, Question  # noqa: E402
from rag_eval.metrics import RunResult  # noqa: E402

HERE = Path(__file__).resolve().parent
LOCAL_CACHE = HERE / "cache"
LOCAL_CACHE.mkdir(exist_ok=True)
EXP = "12_sparse_colbert"

sys.path.insert(0, str((DATA_DIR.parent / "02_dense_sweep").resolve()))
from models import MODELS  # noqa: E402

# ── corpora ──────────────────────────────────────────────────────────────────

def default_codes_b() -> list[str]:
    rep = json.loads((DATA_DIR / "corpus_b" / "parse_report.json").read_text())
    return [k for k, v in rep.items() if v.get("default_subset")]


@dataclass
class Corpus:
    name: str
    chunker: str
    docs: list
    questions: list[Question]
    chunks: list
    texts: list[str]
    doc_ids: np.ndarray

    @property
    def n(self) -> int:
        return len(self.chunks)


def load_corpus(name: str) -> Corpus:
    if name == "A":
        docs, qs = load_corpus_a(), load_questions_a()
        chunker = "fixed1500_title"
        chunks = fixed_chunks(docs, 1500, 200, prefix_title=True)
    elif name == "B":
        docs, qs = load_corpus_b(codes=default_codes_b()), load_questions_b()
        chunker = "article_ctx_1200"
        chunks = article_chunks(docs, 1200, 100, prefix_context=True)
    else:
        raise ValueError("corpus C is out of scope for experiment 12 (CPU budget)")
    texts = [c.text for c in chunks]
    return Corpus(name, chunker, docs, qs, chunks, texts, np.array([c.doc_id for c in chunks]))


# ── BM25 leg (identical to experiment 03) ────────────────────────────────────
import bm25s  # noqa: E402
import Stemmer  # noqa: E402

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


def bm25_scores(c: Corpus) -> tuple[np.ndarray, float]:
    """(nq, n_chunks) BM25 score matrix on the chunks (k1=1.2, b=0.75 as in exp 03)."""
    t0 = time.perf_counter()
    r = bm25s.BM25(k1=1.2, b=0.75)
    r.index([tokenize(t) for t in c.texts], show_progress=False)
    out = np.zeros((len(c.questions), c.n), dtype=np.float32)
    for i, q in enumerate(c.questions):
        out[i] = r.get_scores(tokenize(q.question))
    return out, time.perf_counter() - t0


# ── cached dense legs (experiment 02 embeddings) ─────────────────────────────

def dense_cache_path(c: Corpus, model_key: str) -> Path:
    spec = MODELS[model_key]
    extra = f"seq{spec.max_seq}|d_prefix={spec.d_prefix!r}|{c.chunker}"
    return CACHE_DIR / (_key(spec.hf_id, c.texts, extra) + ".npy")


def dense_scores(c: Corpus, model_key: str) -> np.ndarray | None:
    """(nq, n_chunks) cosine matrix from cached chunk embeddings; queries are encoded
    here (cached locally so the encoder is loaded once per corpus/model)."""
    f = dense_cache_path(c, model_key)
    if not f.exists():
        return None
    qf = LOCAL_CACHE / f"q_{c.name}_{model_key}.npy"
    if qf.exists():
        qemb = np.load(qf)
    else:
        from run_sweep import Encoder  # experiment 02 loader (same prefixes / seq len)
        enc = Encoder(MODELS[model_key])
        qemb = enc.queries([q.question for q in c.questions])
        np.save(qf, qemb)
        del enc
    return (qemb @ np.load(f).T).astype(np.float32)


# ── fusion (identical to experiment 03) ──────────────────────────────────────

def rrf(rank_lists: list[np.ndarray], k: int = 60, n: int = 0) -> np.ndarray:
    score = np.zeros(n)
    for ranks in rank_lists:
        score[ranks] += 1.0 / (k + np.arange(1, len(ranks) + 1))
    return score


def rrf_matrix(mats: list[np.ndarray], depth: int = 200, k: int = 60) -> np.ndarray:
    nq, n = mats[0].shape
    return np.stack([rrf([np.argsort(-m[i])[:depth] for m in mats], k, n) for i in range(nq)])


def minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


def convex_matrix(a: np.ndarray, b: np.ndarray, w: float) -> np.ndarray:
    """w * minmax(a) + (1-w) * minmax(b), row-wise."""
    return np.stack([w * minmax(a[i]) + (1 - w) * minmax(b[i]) for i in range(a.shape[0])])


def to_doc_ranking(chunk_scores: np.ndarray, doc_ids: np.ndarray, top: int = 50) -> list[str]:
    order = np.argsort(-chunk_scores)
    seen, out = set(), []
    for j in order:
        d = str(doc_ids[j])
        if d not in seen:
            seen.add(d); out.append(d)
            if len(out) >= top:
                break
    return out


def rankings_from(scores: np.ndarray, c: Corpus) -> dict[str, list[str]]:
    return {q.qid: to_doc_ranking(scores[i], c.doc_ids) for i, q in enumerate(c.questions)}


# ── evaluation under the train/val protocol ──────────────────────────────────

def evaluate(name: str, c: Corpus, scores: np.ndarray, config: dict, timing: dict | None = None,
             save: bool = True, quiet: bool = False) -> RunResult:
    res = evaluate_rankings(name, c.name, c.questions, rankings_from(scores, c),
                            config={"chunker": c.chunker, "n_chunks": c.n, **config}, timing=timing or {})
    if save:
        save_result(EXP, res)
    if not quiet:
        print(res.summary(), flush=True)
    return res


def train_mrr(c: Corpus, scores: np.ndarray) -> float:
    """MRR on the train split only (used to tune fusion weights)."""
    qs = [q for q in c.questions if q.split == "train"]
    idx = [i for i, q in enumerate(c.questions) if q.split == "train"]
    r = {q.qid: to_doc_ranking(scores[i], c.doc_ids) for i, q in zip(idx, qs)}
    return evaluate_rankings("tmp", c.name, qs, r).metrics["mrr"]


def tuned_convex(name: str, c: Corpus, a: np.ndarray, b: np.ndarray, config: dict,
                 grid=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9), timing: dict | None = None) -> RunResult:
    """Pick the convex weight on the *train* questions only, then evaluate the whole set
    (summary prints train and val separately). Ties → the weight closest to 0.5."""
    best = max(grid, key=lambda w: (round(train_mrr(c, convex_matrix(a, b, w)), 6), -abs(w - 0.5)))
    res = evaluate(f"{name}__convex{best}", c, convex_matrix(a, b, best),
                   {**config, "fusion": "convex", "weight": best, "weight_tuned_on": "train",
                    "grid_train_mrr": {str(w): round(train_mrr(c, convex_matrix(a, b, w)), 4) for w in grid}},
                   timing)
    return res


def fusion_suite(base: str, c: Corpus, leg: np.ndarray, config: dict, bm: np.ndarray,
                 dense: dict[str, np.ndarray], timing: dict | None = None) -> list[RunResult]:
    """Standard fusion battery for a new scoring leg: alone; +BM25 (RRF, tuned convex);
    +each cached dense leg (RRF, tuned convex); +BM25+dense (3-way RRF)."""
    out = [evaluate(base, c, leg, config, timing)]
    out.append(evaluate(f"{base}+bm25__rrf", c, rrf_matrix([leg, bm]), {**config, "fusion": "rrf", "legs": ["self", "bm25"]}))
    out.append(tuned_convex(f"{base}+bm25", c, leg, bm, {**config, "legs": ["self", "bm25"]}))
    for dk, dm in dense.items():
        out.append(evaluate(f"{base}+{dk}__rrf", c, rrf_matrix([leg, dm]), {**config, "fusion": "rrf", "legs": ["self", dk]}))
        out.append(tuned_convex(f"{base}+{dk}", c, leg, dm, {**config, "legs": ["self", dk]}))
        out.append(evaluate(f"{base}+{dk}+bm25__rrf", c, rrf_matrix([leg, dm, bm]),
                            {**config, "fusion": "rrf", "legs": ["self", dk, "bm25"]}))
    return out


def dense_legs(c: Corpus, keys=("e5-small", "e5-base", "bge-m3")) -> dict[str, np.ndarray]:
    out = {}
    for k in keys:
        m = dense_scores(c, k)
        if m is not None:
            out[k] = m
    return out


def memo_npz(path: Path, fn, **save_kwargs):
    """Tiny on-disk memo for expensive encodes (np.savez)."""
    if path.exists():
        return dict(np.load(path, allow_pickle=True))
    out = fn()
    np.savez(path, **out)
    return out
