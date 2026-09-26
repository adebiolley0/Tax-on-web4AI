"""Experiment 22 – shared pieces: question sets (human 40 + mined 304 on corpus B), the exp-14 chunk universe,
leg loaders, z-score fusion, metrics per split / slice, paired statistics (rag_eval.stats), saving with the
right question-file stamp, reference runs.

Two venvs, no new one:
  ../14_ltr_fusion/.venv/bin/python  legs.py / run_stage1.py / rerank_score.py / run_rerank.py / ltr.py
  ../12_sparse_colbert/.venv/bin/python  colbert_scores.py   (PyLate; torch lock)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

from rag_eval import evaluate_rankings, load_questions_b, load_questions_mined, save_result
from rag_eval.corpora import DATA_DIR, QUESTIONS_B, QUESTIONS_B_MINED, REPO_ROOT
from rag_eval.results import build_provenance
from rag_eval.stats import paired_stats

EXP = "22_reception_colbert"
EXP_DIR = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("EXP22_CACHE", EXP_DIR / "cache"))      # overridable for smoke tests on a scratch copy
RUNS = Path(os.environ.get("EXP22_RUNS", EXP_DIR / "runs"))
CACHE.mkdir(parents=True, exist_ok=True)
RUNS.mkdir(parents=True, exist_ok=True)
EXPS = DATA_DIR.parent
RESULTS = EXPS / "results"
EXP20 = EXPS / "20_reception_intent"
EXP14 = EXPS / "14_ltr_fusion"
EXP12 = EXPS / "12_sparse_colbert"
for _p in ("20_reception_intent", "11_graph_retrieval", "13_lexical_upgrades", "08_corpus_b_cleanup", "17_lex_rerank",
           "14_ltr_fusion", "01_bm25", "02_dense_sweep", "03_hybrid_rerank"):
    sys.path.insert(0, str((EXPS / _p).resolve()))

SLICES = ("pq", "ruling", "faq")
# reception configuration: exp 20's train-selected lexical point (`sent+title`, w 0.5, b 0.5), the one exp 20
# put in front of mMARCO; the train-selected *fused* point (w 1.0) is kept as a reference run only.
REC_VARIANT, REC_W, REC_B = "sent+title", 0.5, 0.5
LEGS = ("rec", "colbert", "e5")
FUSIONS = {                      # name → weights over LEGS (z-score convex, fixed)
    "z3_equal": (1 / 3, 1 / 3, 1 / 3),
    "z_rec_colbert": (0.5, 0.5, 0.0),
    "z_rec_e5": (0.5, 0.0, 0.5),
    "z_colbert_e5": (0.0, 0.5, 0.5),
}
CANDIDATES = ("z3_equal", "z_rec_colbert")      # the two pre-registered candidates; selection on mined TRAIN only

# reference runs (stored per-question ranks) -------------------------------------------------------
REFS_HUMAN = {
    "bm25_01": (RESULTS / "18_eval_hygiene" / "B__human__bm25_tok01.json", "exp 01 BM25 (tok01, exp-18 rerun)"),
    "lex13": (RESULTS / "13_lexical_upgrades" / "B__combo__fields_tok01_num_cues.json", "exp 13 BM25F lexical"),
    "e5_rrf": (RESULTS / "03_hybrid_rerank" / "B__e5-small__article_ctx_1200__rrf.json", "exp 03 e5-small + BM25 RRF (bar's first stage)"),
    "colbert_bm25": (RESULTS / "12_sparse_colbert" / "B__colbert-colbert-fr_bm25__rrf.json", "exp 12 colbert-fr + BM25 RRF (best first stage)"),
    "colbert": (RESULTS / "12_sparse_colbert" / "B__colbert-colbert-fr.json", "exp 12 colbert-fr alone"),
    "rec_e5": (RESULTS / "20_reception_intent" / "B__lexrec__sent_title_w0.5_b0.5_e5.json", "exp 20 reception (w 0.5) + e5 convex 0.5"),
    "rec_e5_w1": (RESULTS / "20_reception_intent" / "B__lexrec__sent_title_w1.0_b0.5_e5.json", "exp 20 reception (w 1.0, train-selected fused) + e5"),
    "rec": (RESULTS / "20_reception_intent" / "B__lexrec__sent_title_w0.5_b0.5.json", "exp 20 reception lexical only (w 0.5)"),
    "bar": (RESULTS / "03_hybrid_rerank" / "B__e5-small__article_ctx_1200__rrf_mmarco-minilm_30.json", "exp 03 e5 RRF + mMARCO @30 (round-1 bar)"),
    "r2_best": (RESULTS / "14_ltr_fusion" / "B__tune__e5_bm25chunk__rerank_mmarco-minilm_only__fit-train.json", "exp 14 e5 + mMARCO @20, β 0.8 (round-2 best)"),
    "exp14_oof": (RESULTS / "14_ltr_fusion" / "B__ltr__logreg__minimal_meta__oof.json", "exp 14 logreg minimal+meta (oof)"),
    "exp17_bge": (RESULTS / "17_lex_rerank" / "B__lex13_bge_20.json", "exp 17 lexical → bge @20"),
    "rec_e5_mmarco": (RESULTS / "20_reception_intent" / "B__lexrec__sent_title_w0.5_b0.5_e5-_mmarco_30.json", "exp 20 reception + e5 → mMARCO @30"),
    "e5_bge": (RESULTS / "03_hybrid_rerank" / "B__e5-small__article_ctx_1200__rrf_bge-reranker-v2-m3_30.json", "exp 03 e5 RRF + bge @30"),
}
REFS_MINED = {
    "bm25_01": (RESULTS / "18_eval_hygiene" / "B__mined__bm25_tok01.json", "exp 01 BM25 (tok01, exp-18 rerun)"),
    "lex13": (RESULTS / "18_eval_hygiene" / "B__mined__exp13_lex.json", "exp 13 BM25F lexical (exp-18 rerun)"),
    "rec_e5": (RESULTS / "20_reception_intent" / "B__lexrec__sent_title_w0.5_b0.5_e5__mined.json", "exp 20 reception (w 0.5, leak-free) + e5 convex 0.5"),
    "rec_e5_w1": (RESULTS / "20_reception_intent" / "B__lexrec__sent_title_w1.0_b0.5_e5__mined.json", "exp 20 reception (w 1.0, leak-free) + e5"),
    "rec": (RESULTS / "20_reception_intent" / "B__lexrec__sent_title_w0.5_b0.5__mined.json", "exp 20 reception lexical only (leak-free)"),
    "lex13_e5": (RESULTS / "20_reception_intent" / "B__lex13_e5__mined.json", "exp 20 lex13 + e5 convex 0.5"),
}


# ── questions ────────────────────────────────────────────────────────────────
def questions_human():
    return load_questions_b()


def questions_mined():
    return load_questions_mined("B")


def questions_all():
    qs = questions_human() + questions_mined()
    assert len({q.qid for q in qs}) == len(qs)
    return qs


def slice_of(q) -> str:
    return q.meta.get("source") or "human"


# ── saving (question-file stamp for the mined set) ──────────────────────────
def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save22(res, which: str):
    prov = build_provenance(res)
    f = QUESTIONS_B if which == "human" else QUESTIONS_B_MINED
    prov["questions_file"] = str(f.relative_to(REPO_ROOT))
    prov["questions_sha256"] = _sha(f)
    res.provenance = prov
    return save_result(EXP, res)


def evaluate_save(name: str, questions, rankings: dict, config: dict, which: str, timing: dict | None = None, save: bool = True):
    """which = 'human' | 'mined'; the mined run name gets the `__mined` suffix (exp-20 convention)."""
    full = name if which == "human" else f"{name}__mined"
    res = evaluate_rankings(full, "B", questions, rankings, {**config, "question_set": which}, timing or {})
    if save:
        save22(res, which)
    return res


def ranks_of(res) -> dict[str, int | None]:
    return {qid: v["rank"] for qid, v in res.per_question.items()}


def ranks_of_file(path: Path) -> dict[str, int | None]:
    r = json.loads(Path(path).read_text())
    return {qid: v["rank"] for qid, v in r["per_question"].items()}


# ── metrics ──────────────────────────────────────────────────────────────────
def _m(ranks: dict, qs) -> dict:
    rr = [1.0 / ranks[q.qid] if ranks.get(q.qid) else 0.0 for q in qs]
    return {"n": len(qs), "mrr": float(np.mean(rr)) if qs else float("nan"),
            "hit@1": float(np.mean([1.0 if ranks.get(q.qid) == 1 else 0.0 for q in qs])) if qs else float("nan"),
            "recall@10": float(np.mean([1.0 if ranks.get(q.qid) and ranks[q.qid] <= 10 else 0.0 for q in qs])) if qs else float("nan"),
            "recall@30": float(np.mean([1.0 if ranks.get(q.qid) and ranks[q.qid] <= 30 else 0.0 for q in qs])) if qs else float("nan")}


def split_metrics(ranks: dict, questions) -> dict:
    return {sp: _m(ranks, [q for q in questions if sp == "all" or q.split == sp]) for sp in ("train", "val", "all")}


def slice_metrics(ranks: dict, questions) -> dict:
    out = {"all": _m(ranks, questions)}
    for sl in SLICES:
        qs = [q for q in questions if q.meta.get("source") == sl]
        if qs:
            out[sl] = _m(ranks, qs)
    for sp in ("train", "val"):
        out[sp] = _m(ranks, [q for q in questions if q.split == sp])
    return out


def rr_vec(ranks: dict, qids) -> np.ndarray:
    return np.array([1.0 / ranks[q] if ranks.get(q) else 0.0 for q in qids], dtype=np.float64)


def paired(ranks_base: dict, ranks_new: dict, qids) -> dict:
    """rag_eval.stats.paired_stats on reciprocal ranks (Δ = new − base) + hit@10 delta."""
    qids = [q for q in qids if q in ranks_base and q in ranks_new]
    if len(qids) < 3:
        return {"n": len(qids)}
    p = paired_stats(rr_vec(ranks_base, qids), rr_vec(ranks_new, qids), "rr")
    h = paired_stats((np.array([ranks_base.get(q) or 10**9 for q in qids]) <= 10).astype(float),
                     (np.array([ranks_new.get(q) or 10**9 for q in qids]) <= 10).astype(float), "hit@10")
    h30 = paired_stats((np.array([ranks_base.get(q) or 10**9 for q in qids]) <= 30).astype(float),
                       (np.array([ranks_new.get(q) or 10**9 for q in qids]) <= 30).astype(float), "hit@30")
    return {"n": p.n, "mrr_base": p.mean_a, "mrr_new": p.mean_b, "delta": p.delta, "ci": [p.ci_lo, p.ci_hi], "p_t": p.p_t,
            "p_perm": p.p_perm, "perm_exact": p.perm_exact, "wins": p.wins, "losses": p.losses, "ties": p.ties,
            "effect": p.effect_size, "d_hit10": h.delta, "p_hit10": h.p_t, "d_hit30": h30.delta, "p_hit30": h30.p_t}


def fmt_paired(label: str, t: dict) -> str:
    if "delta" not in t:
        return f"| {label} | n={t['n']} | – | – | – | – | – |"
    star = "**" if t["p_t"] < 0.05 else ""
    ex = "" if t.get("perm_exact", True) else "~"
    return (f"| {label} | {t['n']} | {t['mrr_base']:.3f} → {t['mrr_new']:.3f} | {star}{t['delta']:+.3f}{star} [{t['ci'][0]:+.3f}, {t['ci'][1]:+.3f}] | "
            f"{t['p_t']:.3f} / {ex}{t['p_perm']:.3f} | {t['wins']} / {t['losses']} / {t['ties']} | {t['d_hit10']:+.3f} ({t['p_hit10']:.2f}) | {t['d_hit30']:+.3f} ({t['p_hit30']:.2f}) |")


PAIRED_HEAD = ["| comparison | n | MRR base → new | Δ MRR [95 % CI] | p_t / p_perm | W / L / T | Δ H@10 (p) | Δ H@30 (p) |",
               "|---|---:|---|---|---|---|---|---|"]


def fmt_human(label: str, m: dict) -> str:
    return (f"| {label} | {m['train']['mrr']:.3f} | **{m['val']['mrr']:.3f}** | {m['all']['mrr']:.3f} | "
            f"{m['val']['hit@1']:.3f} | {m['all']['hit@1']:.3f} | {m['val']['recall@10']:.3f} | {m['all']['recall@10']:.3f} | "
            f"{m['train']['recall@30']:.3f} | {m['val']['recall@30']:.3f} | {m['all']['recall@30']:.3f} |")


HUMAN_HEAD = ["| run | MRR train | MRR **val** | MRR all | H@1 val | H@1 all | R@10 val | R@10 all | R@30 train | R@30 val | R@30 all |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]


def fmt_mined(label: str, m: dict) -> str:
    cells = []
    for sl in ("all",) + SLICES + ("train", "val"):
        d = m.get(sl)
        cells.append(f"{d['mrr']:.3f} / {d['hit@1']:.3f} / {d['recall@10']:.3f} / {d['recall@30']:.3f}" if d and d["n"] else "–")
    return f"| {label} | " + " | ".join(cells) + " |"


MINED_HEAD = ["| run | all (304) MRR / H@1 / R@10 / R@30 | pq (159) | ruling (142) | faq (3) | train (145) | val (159) |",
              "|---|---|---|---|---|---|---|"]


# ── scores → rankings ────────────────────────────────────────────────────────
def zscore(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    sd = x.std()
    return (x - x.mean()) / sd if sd > 0 else np.zeros_like(x)


def minmax(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


def fuse_z(legs: dict[str, np.ndarray], weights: tuple[float, ...]) -> np.ndarray:
    """Row-wise z-score convex fusion of doc-level score matrices (nq, ndocs)."""
    nq = next(iter(legs.values())).shape[0]
    out = np.zeros_like(next(iter(legs.values())), dtype=np.float64)
    for w, name in zip(weights, LEGS):
        if w > 0:
            out += w * np.stack([zscore(legs[name][i]) for i in range(nq)])
    return out


def rankings_from(scores: np.ndarray, questions, doc_ids: list[str], top: int = 60, positive_only: bool = False) -> dict:
    out = {}
    for i, q in enumerate(questions):
        s = scores[i]
        k = min(top, len(s))
        cand = np.argpartition(-s, k - 1)[:k]
        cand = cand[np.argsort(-s[cand], kind="stable")]
        out[q.qid] = [doc_ids[j] for j in cand if (s[j] > 0 or not positive_only)]
    return out


def doc_max(chunk_scores: np.ndarray, chunk_doc: np.ndarray, n_docs: int, fill: float = -1.0) -> np.ndarray:
    out = np.full(n_docs, fill, dtype=np.float64)
    np.maximum.at(out, chunk_doc, chunk_scores.astype(np.float64))
    return out


# ── the exp-14 chunk universe (== exp 12 / exp 03 chunks, asserted by the builders) ──────────────
def load_universe():
    """docs, chunks (article_ctx_1200), chunk_doc, doc_start, doc_ids (exp-14 order == exp-13 order)."""
    from common14 import load_corpus_and_chunks  # noqa: E402
    docs, _, chunks, _ = load_corpus_and_chunks("B")
    z14 = np.load(EXP14 / "cache" / "B_stage1.npz", allow_pickle=False)
    m14 = json.loads((EXP14 / "cache" / "B_stage1.json").read_text())
    doc_ids = [d.doc_id for d in docs]
    assert m14["doc_ids"] == doc_ids and len(chunks) == m14["n_chunks"]
    return docs, chunks, z14["chunk_doc"].astype(np.int64), z14["doc_start"].astype(np.int64), doc_ids


def load_legs() -> dict:
    """cache/B_legs.npz → dict with doc-level legs per question set and the chunk-level dense legs."""
    z = np.load(CACHE / "B_legs.npz", allow_pickle=False)
    meta = json.loads((CACHE / "B_legs.json").read_text())
    return {"z": {k: z[k] for k in z.files}, **meta}
