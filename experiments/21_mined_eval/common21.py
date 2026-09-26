"""Experiment 21 – shared pieces: question sets (human + mined), sparse stage-1 cache, fusions,
slices, saving with a correct question-file stamp, paired statistics helpers.

Run everything with the experiment-14 venv:
  cd experiments/14_ltr_fusion && uv run python ../21_mined_eval/<script>.py ...
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

from rag_eval import evaluate_rankings, save_result
from rag_eval.corpora import (DATA_DIR, QUESTIONS_B, QUESTIONS_B_MINED, QUESTIONS_C, QUESTIONS_C_MINED, REPO_ROOT,
                              load_questions_b, load_questions_c, load_questions_mined)
from rag_eval.results import build_provenance
from rag_eval.metrics import dedupe_ranked

EXP = "21_mined_eval"
EXP_DIR = Path(__file__).resolve().parent
CACHE = EXP_DIR / "cache"
RUNS = EXP_DIR / "runs"
RESULTS = DATA_DIR.parent / "results"
EXP14 = DATA_DIR.parent / "14_ltr_fusion"
EXP17 = DATA_DIR.parent / "17_lex_rerank"
EXP13 = DATA_DIR.parent / "13_lexical_upgrades"
for _p in (EXP14, EXP13, DATA_DIR.parent / "08_corpus_b_cleanup"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

TOPK_CHUNK = 1500          # chunks kept per leg / fusion per question in the stage-1 cache
TOPK_DOC = 1000            # docs kept for the whole-document BM25 leg
SOURCES = ("pq", "ruling", "faq")
SUB_SIZE = {"B": 150, "C": 200}
SUB_PQ_CAP = {"B": None, "C": 50}
RERANK_DEPTH = 20
RERANKERS = {"mmarco-minilm": {"hf": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1", "max_len": 512},
             "bge-reranker-v2-m3": {"hf": "BAAI/bge-reranker-v2-m3", "max_len": 512}}
QFILES = {"B": (QUESTIONS_B, QUESTIONS_B_MINED), "C": (QUESTIONS_C, QUESTIONS_C_MINED)}

# reference runs (stored per-question ranks) on the HUMAN sets
REFS = {
    "B": {"bar_val": ("03_hybrid_rerank", "e5-small__article_ctx_1200__rrf+mmarco-minilm@30",
                      "round-1 bar: e5 RRF + mMARCO@30 (exp 03), val 0.570 / all 0.522"),
          "bar_full": ("03_hybrid_rerank", "e5-small__article_ctx_1200__rrf+mmarco-minilm@30",
                       "round-1 full-set best (same run)"),
          "exp14": ("14_ltr_fusion", "ltr__logreg__minimal+meta__oof", "exp-14 logreg 7 features, oof 0.608"),
          "exp14_cheap": ("14_ltr_fusion", "ltr__logreg__cheap__oof", "exp-14 logreg cheap features, oof"),
          "lex13": ("18_eval_hygiene", "human__exp13_lex", "exp-13 lexical (exp-18 rerun)"),
          "bm25_01": ("18_eval_hygiene", "human__bm25_tok01", "exp-01 BM25 (exp-18 rerun)")},
    "C": {"bar_val": ("09_corpus_c", "bm25__fixed1200_title__bm25+bge-reranker-v2-m3@30",
                      "round-1 bar: BM25 chunks + bge@30 (exp 09), val 0.665 / all 0.696"),
          "bar_full": ("09_corpus_c", "e5-small__fixed1200_title__convex0.5+bge-reranker-v2-m3@30",
                       "round-1 full-set best: e5 convex0.5 + bge@30 (exp 09), all 0.703"),
          "exp14": ("14_ltr_fusion", "ltr__lgbm-tiny__all__oof", "exp-14 LambdaMART tiny, all features, oof 0.723"),
          "exp14_cheap": ("14_ltr_fusion", "ltr__logreg__cheap__oof", "exp-14 logreg cheap features, oof"),
          "exp17": ("17_lex_rerank", "lex13+bge@20", "exp-17 lexical → bge@20, val 0.688 / all 0.719"),
          "lex13": ("18_eval_hygiene", "human__exp13_lex", "exp-13 lexical (exp-18 rerun)"),
          "bm25_01": ("18_eval_hygiene", "human__bm25_tok01", "exp-01 BM25 (exp-18 rerun)")},
}


# ── questions ────────────────────────────────────────────────────────────────
def human_questions(corpus: str):
    return load_questions_b() if corpus == "B" else load_questions_c()


def all_questions(corpus: str):
    """Human questions first, then the mined set. Ids are unique across the two."""
    qs = human_questions(corpus) + load_questions_mined(corpus)
    ids = [q.qid for q in qs]
    assert len(ids) == len(set(ids)), "duplicate question ids"
    return qs


def is_human(q) -> bool:
    return q.meta.get("source") is None


def slices(questions) -> dict[str, list]:
    """Named slices: human, mined (pooled), mined per source."""
    out = {"human": [q for q in questions if is_human(q)], "mined": [q for q in questions if not is_human(q)]}
    for s in SOURCES:
        qs = [q for q in questions if q.meta.get("source") == s]
        if qs:
            out[f"mined__src_{s}"] = qs
    return out


def load_subsample(corpus: str) -> list[str]:
    return json.loads((CACHE / f"subsample_{corpus}.json").read_text())["qids"]


# ── saving with the right question-file stamp ───────────────────────────────
def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save21(res, corpus: str, which: str = "mined"):
    """save_result with the provenance stamp pointing at the question file actually scored
    (the harness stamps the human file by default)."""
    prov = build_provenance(res)
    human_f, mined_f = QFILES[corpus]
    if which == "human":
        files = [human_f]
    elif which == "mined":
        files = [mined_f]
    else:
        files = [human_f, mined_f]
    prov["questions_file"] = "+".join(str(f.relative_to(REPO_ROOT)) for f in files)
    prov["questions_sha256"] = "+".join(_sha(f) for f in files)
    res.provenance = prov
    return save_result(EXP, res)


def eval_and_save(name: str, corpus: str, questions, rankings, config: dict, timing: dict | None = None,
                  save: bool = True):
    """Evaluate one system on every slice; save one run per slice (`<slice>__<name>`)."""
    out = {}
    for sl, qs in slices(questions).items():
        if not qs:
            continue
        res = evaluate_rankings(f"{sl}__{name}", corpus, qs, rankings, {**config, "questions": sl}, timing or {})
        res.metrics["recall@30"] = round(recall_at(qs, rankings, 30), 4)
        res.metrics["hit@30"] = round(hit_at(qs, rankings, 30), 4)
        if save:
            save21(res, corpus, "human" if sl == "human" else "mined")
        out[sl] = res
    return out


def recall_at(questions, rankings, k: int) -> float:
    tot = 0.0
    for q in questions:
        ranked = dedupe_ranked(rankings.get(q.qid, []))
        excl = set(q.meta.get("exclude") or [])
        ranked = [d for d in ranked if d not in excl][:k]
        exp = set(q.expected)
        tot += len(exp & set(ranked)) / max(1, len(exp))
    return tot / max(1, len(questions))


def hit_at(questions, rankings, k: int) -> float:
    n = 0
    for q in questions:
        ranked = dedupe_ranked(rankings.get(q.qid, []))
        excl = set(q.meta.get("exclude") or [])
        ranked = [d for d in ranked if d not in excl][:k]
        n += int(any(d in set(q.expected) for d in ranked))
    return n / max(1, len(questions))


def short_metrics(res) -> dict:
    m = res.metrics
    return {k: m[k] for k in ("n_questions", "mrr", "hit@1", "hit@5", "recall@10", "hit@10", "recall@30", "hit@30",
                              "train_mrr", "train_n", "val_mrr", "val_n") if k in m}


# ── stage-1 cache ────────────────────────────────────────────────────────────
class Stage1:
    """Sparse first-stage cache: per question the top-K chunks (index + score) of every leg and of the
    two fixed fusions, the corpus-wide min / max of every leg (so min-max normalisation is exact for the
    kept chunks), and the top-K documents of whole-document BM25."""

    LEGS = ("e5", "bm25")
    FUSIONS = ("convex05", "rrf60")

    def __init__(self, corpus: str):
        self.corpus = corpus
        f = CACHE / f"{corpus}_stage1.npz"
        if not f.exists():
            raise FileNotFoundError(f"{f}: run build_stage1.py --corpus {corpus}")
        z = np.load(f, allow_pickle=False)
        self.z = {k: z[k] for k in z.files}
        meta = json.loads((CACHE / f"{corpus}_stage1.json").read_text())
        self.qids: list[str] = meta["qids"]
        self.q_index = {q: i for i, q in enumerate(self.qids)}
        self.doc_ids: list[str] = meta["doc_ids"]
        self.doc_index = {d: i for i, d in enumerate(self.doc_ids)}
        self.doc_len = np.asarray(meta["doc_len"])
        self.chunk_doc = self.z["chunk_doc"]
        self.doc_start = self.z["doc_start"]
        self.nchunks = int(meta["n_chunks"])
        self.ndocs = len(self.doc_ids)
        self.nq = len(self.qids)

    def top(self, name: str, qi: int) -> tuple[np.ndarray, np.ndarray]:
        """(indices, scores) of the kept units of leg / fusion ``name`` for question qi, best first."""
        idx, val = self.z[f"{name}_idx"][qi], self.z[f"{name}_val"][qi]
        m = idx >= 0
        return idx[m], val[m]

    def minmax_of(self, name: str, qi: int) -> tuple[float, float]:
        return float(self.z[f"{name}_min"][qi]), float(self.z[f"{name}_max"][qi])

    def full(self, name: str, qi: int) -> np.ndarray:
        """Densified chunk vector: kept chunks exact, others at the corpus-wide minimum."""
        lo, _ = self.minmax_of(name, qi)
        v = np.full(self.nchunks, lo, dtype=np.float64)
        idx, val = self.top(name, qi)
        v[idx] = val
        return v

    def full_norm(self, name: str, qi: int) -> np.ndarray:
        lo, hi = self.minmax_of(name, qi)
        v = self.full(name, qi)
        return (v - lo) / (hi - lo) if hi > lo else np.zeros_like(v)

    def doc_max(self, chunk_scores: np.ndarray) -> np.ndarray:
        out = np.full(self.ndocs, -np.inf, dtype=np.float64)
        np.maximum.at(out, self.chunk_doc, chunk_scores)
        return out

    def doc_ranking(self, name: str, qi: int, top: int = 50) -> list[str]:
        idx, _ = self.top(name, qi)
        seen, out = set(), []
        for j in idx:
            d = int(self.chunk_doc[j])
            if d not in seen:
                seen.add(d); out.append(self.doc_ids[d])
                if len(out) >= top:
                    break
        return out

    def bm25doc_ranking(self, qi: int, top: int = 50) -> list[str]:
        idx, _ = self.top("bm25doc", qi)
        return [self.doc_ids[int(d)] for d in idx[:top]]

    def candidates(self, qi: int, name: str, depth: int) -> np.ndarray:
        """Top-``depth`` chunks of a leg / fusion (for reranking)."""
        idx, _ = self.top(name, qi)
        return idx[:depth].astype(np.int64)


def doc_ranks_capped(doc_scores: np.ndarray, floor: float) -> np.ndarray:
    """1-based rank of every document by score; documents at the floor (no kept chunk) share the rank
    just below the last scored document."""
    above = doc_scores > floor + 1e-12
    n_above = int(above.sum())
    r = np.full(len(doc_scores), n_above + 1, dtype=np.int64)
    idx = np.where(above)[0]
    order = idx[np.argsort(-doc_scores[idx], kind="stable")]
    r[order] = np.arange(1, n_above + 1)
    return r


# ── lexical (exp 13) cache ───────────────────────────────────────────────────
class LexStage1:
    """Top-200 units per question of a lexical configuration (exp-13 machinery), unit index == exp-14
    chunk index on C (asserted at build time); on B the units are exp-13's 2000-char article chunks."""

    def __init__(self, corpus: str, cfg: str = "exp13_lex"):
        z = np.load(CACHE / f"{corpus}_lex_{cfg}.npz", allow_pickle=False)
        meta = json.loads((CACHE / f"{corpus}_lex_{cfg}.json").read_text())
        self.corpus, self.cfg = corpus, cfg
        self.qids = meta["qids"]; self.q_index = {q: i for i, q in enumerate(self.qids)}
        self.doc_ids = meta["doc_ids"]
        self.unit_doc = z["unit_doc"]; self.top_units = z["top_units"]; self.top_scores = z["top_scores"]
        self.same_units_as_stage1 = bool(meta.get("same_units_as_exp14", False))
        tf = CACHE / f"{corpus}_lex_{cfg}_texts.json"
        self.texts = {int(k): v for k, v in json.loads(tf.read_text()).items()} if tf.exists() else {}

    def candidates(self, qi: int, depth: int) -> tuple[np.ndarray, np.ndarray]:
        u, s = self.top_units[qi][:depth], self.top_scores[qi][:depth]
        m = (u >= 0) & (s > 0)
        return u[m].astype(np.int64), s[m]

    def doc_ranking(self, qi: int, top: int = 60) -> list[str]:
        seen, out = set(), []
        for u, s in zip(self.top_units[qi], self.top_scores[qi]):
            if u < 0 or s <= 0:
                break
            d = int(self.unit_doc[u])
            if d not in seen:
                seen.add(d); out.append(self.doc_ids[d])
                if len(out) >= top:
                    break
        return out

    def doc_scores(self, qi: int) -> dict[int, float]:
        """doc index → best unit score among the kept units."""
        out: dict[int, float] = {}
        for u, s in zip(self.top_units[qi], self.top_scores[qi]):
            if u < 0 or s <= 0:
                break
            d = int(self.unit_doc[u])
            if s > out.get(d, -1.0):
                out[d] = float(s)
        return out


# ── reranker score cache (keyed by question id + chunk id) ──────────────────
def rerank_cache_path(corpus: str, reranker: str) -> Path:
    return CACHE / f"{corpus}_rerank_{reranker}.npz"


def load_rerank_cache(corpus: str, reranker: str) -> dict[tuple[str, int], float]:
    f = rerank_cache_path(corpus, reranker)
    if not f.exists():
        return {}
    z = np.load(f, allow_pickle=False)
    return {(str(q), int(c)): float(s) for q, c, s in zip(z["qid"], z["chunk_idx"], z["score"])}


def save_rerank_cache(corpus: str, reranker: str, table: dict[tuple[str, int], float], chunk_ids: list[str],
                      meta: dict) -> None:
    keys = sorted(table)
    np.savez(rerank_cache_path(corpus, reranker),
             qid=np.array([k[0] for k in keys], dtype="U40"), chunk_idx=np.array([k[1] for k in keys], dtype=np.int64),
             chunk_id=np.array([chunk_ids[k[1]] for k in keys], dtype="U200"),
             score=np.array([table[k] for k in keys], dtype=np.float32))
    (CACHE / f"{corpus}_rerank_{reranker}.json").write_text(json.dumps(meta, indent=1))


# ── fusions (exact, chunk level) ─────────────────────────────────────────────
def minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(x.min()), float(x.max())
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x, dtype=np.float64)


def rrf_scores(legs: list[np.ndarray], k: float = 60.0, depth: int = 300) -> np.ndarray:
    n = len(legs[0])
    out = np.zeros(n, dtype=np.float64)
    for s in legs:
        top = np.argpartition(-s, depth)[:depth]
        top = top[np.argsort(-s[top], kind="stable")]
        out[top] += 1.0 / (k + np.arange(1, depth + 1))
    return out


def topk(v: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    k = min(k, len(v))
    idx = np.argpartition(-v, k - 1)[:k] if k < len(v) else np.arange(len(v))
    idx = idx[np.argsort(-v[idx], kind="stable")]
    return idx.astype(np.int32), v[idx].astype(np.float32)


# ── stored runs / paired statistics ─────────────────────────────────────────
def load_ref(corpus: str, key: str) -> dict:
    from rag_eval.stats import load_run
    exp, run, _ = REFS[corpus][key]
    r = load_run(exp, run, corpus)
    r["_experiment"] = exp
    return r


def load_saved(name: str, corpus: str) -> dict:
    from rag_eval.stats import load_run
    r = load_run(EXP, name, corpus)
    r["_experiment"] = EXP
    return r


def restrict(run: dict, qids) -> dict:
    qids = set(qids)
    return {**run, "per_question": {q: v for q, v in run["per_question"].items() if q in qids}}


def paired(run_a: dict, run_b: dict, qids=None, split=None) -> dict:
    """Paired stats (B − A) on rr / hit@1 / hit@10 restricted to ``qids``; compact dict."""
    from rag_eval.stats import compare_loaded
    a, b = run_a, run_b
    if qids is not None:
        a, b = restrict(a, qids), restrict(b, qids)
    c = compare_loaded(a, b, split=split, ks=(1, 10))
    rr = c.rr
    return {"n": c.n, "mrr_a": round(rr.mean_a, 4), "mrr_b": round(rr.mean_b, 4), "delta": round(rr.delta, 4),
            "ci": [round(rr.ci_lo, 4), round(rr.ci_hi, 4)], "p_t": round(rr.p_t, 4), "p_perm": round(rr.p_perm, 4),
            "perm_exact": rr.perm_exact, "wlt": [rr.wins, rr.losses, rr.ties], "sd_d": round(rr.sd_delta, 4),
            "d_h1": round(c.hits[1].delta, 4), "p_h1": round(c.hits[1].p_perm, 4),
            "d_h10": round(c.hits[10].delta, 4), "p_h10": round(c.hits[10].p_perm, 4)}


def fmt_paired(p: dict) -> str:
    star = "**" if p["p_t"] < 0.05 else ""
    ex = "" if p.get("perm_exact", True) else "~"
    return (f"{star}{p['delta']:+.3f}{star} [{p['ci'][0]:+.3f}, {p['ci'][1]:+.3f}] | {p['p_t']:.3f} | {ex}{p['p_perm']:.3f} | "
            f"{p['wlt'][0]}/{p['wlt'][1]}/{p['wlt'][2]} | {p['d_h1']:+.3f} | {p['d_h10']:+.3f}")


PAIRED_HEADER = "| Δ MRR [95 % CI] | p_t | p_perm | W/L/T | Δ H@1 | Δ H@10 |"
