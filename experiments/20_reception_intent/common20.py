"""Experiment 20 – shared pieces (paths, reference runs, metrics helpers, paired tests).

Run everything with the exp-14 venv (torch + sentence-transformers + bm25s + scipy + rag_eval):
    cd experiments/20_reception_intent && ../14_ltr_fusion/.venv/bin/python <script>.py
Torch scripts (embed_*.py, rerank_*.py) go under `flock experiments/.torch.lock` with OMP_NUM_THREADS=4.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np

from rag_eval.corpora import DATA_DIR, REPO_ROOT

EXP = "20_reception_intent"
EXP_DIR = Path(__file__).resolve().parent
CACHE = EXP_DIR / "cache"
RUNS = EXP_DIR / "runs"
CACHE.mkdir(exist_ok=True)
RUNS.mkdir(exist_ok=True)
EXPS = DATA_DIR.parent
RESULTS = EXPS / "results"
MYFIN = REPO_ROOT / "myfin_docs"

for _p in ("11_graph_retrieval", "13_lexical_upgrades", "08_corpus_b_cleanup", "17_lex_rerank", "14_ltr_fusion",
           "01_bm25", "02_dense_sweep", "03_hybrid_rerank", "09_corpus_c"):
    sys.path.insert(0, str((EXPS / _p).resolve()))

# reference runs (stored per-question ranks) ------------------------------------------------------
REFS = {
    "B": {
        "bar": (RESULTS / "03_hybrid_rerank" / "B__e5-small__article_ctx_1200__rrf_mmarco-minilm_30.json",
                "exp 03: e5-small + BM25 RRF + mMARCO @30 (round-1 bar, val 0.570)"),
        "r2_best": (RESULTS / "14_ltr_fusion" / "B__tune__e5_bm25chunk__rerank_mmarco-minilm_only__fit-train.json",
                    "exp 14: e5-small + mMARCO @20, β chosen on train (round-2 best, val 0.610)"),
        "first_stage_best": (RESULTS / "12_sparse_colbert" / "B__colbert-colbert-fr_bm25__rrf.json",
                             "exp 12: colbert-fr + BM25 RRF (best first stage, val 0.539)"),
        "e5_rrf": (RESULTS / "03_hybrid_rerank" / "B__e5-small__article_ctx_1200__rrf.json",
                   "exp 03: e5-small + BM25 RRF (first stage of the bar, val 0.420)"),
        "lex13": (RESULTS / "13_lexical_upgrades" / "B__combo__fields_tok01_num_cues.json",
                  "exp 13: BM25F lexical (val 0.341)"),
    },
    "C": {
        "bar": (RESULTS / "09_corpus_c" / "C__bm25__fixed1200_title__bm25_bge-reranker-v2-m3_30.json",
                "exp 09: BM25 + bge-reranker @30 (round-1 bar, val 0.665)"),
        "r2_best": (RESULTS / "17_lex_rerank" / "C__lex13_bge_20.json",
                    "exp 17: exp-13 lexical + bge-reranker @20 (round-2 best, val 0.688)"),
        "r2_best30": (RESULTS / "17_lex_rerank" / "C__lex13_bge_30.json",
                      "exp 17: exp-13 lexical + bge-reranker @30 (val 0.675)"),
        "lex13": (RESULTS / "13_lexical_upgrades" / "C__combo__fields_tok01_num_cues.json",
                  "exp 13: BM25F lexical (val 0.616)"),
        "fusion09": (RESULTS / "09_corpus_c" / "C__e5-small__fixed1200_title__convex0.5.json",
                     "exp 09: e5-small + BM25 (tok03) convex 0.5, no reranker"),
    },
}


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def minmax(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    lo, hi = float(x.min()), float(x.max())
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


def per_question_ranks(path: Path) -> dict[str, int | None]:
    r = json.loads(Path(path).read_text())
    return {qid: v["rank"] for qid, v in r["per_question"].items()}


def ranks_of_result(res) -> dict[str, int | None]:
    return {qid: v["rank"] for qid, v in res.per_question.items()}


def split_metrics(ranks: dict[str, int | None], questions) -> dict:
    """train / val / all: MRR, hit@1, R@10, R@30 (rank of the first expected doc ≤ k)."""
    out = {}
    for sp in ("train", "val", "all"):
        qs = [q for q in questions if sp == "all" or q.split == sp]
        rr = [1.0 / ranks[q.qid] if ranks.get(q.qid) else 0.0 for q in qs]
        out[sp] = {"n": len(qs), "mrr": float(np.mean(rr)),
                   "hit@1": float(np.mean([1.0 if ranks.get(q.qid) == 1 else 0.0 for q in qs])),
                   "recall@10": float(np.mean([1.0 if ranks.get(q.qid) and ranks[q.qid] <= 10 else 0.0 for q in qs])),
                   "recall@30": float(np.mean([1.0 if ranks.get(q.qid) and ranks[q.qid] <= 30 else 0.0 for q in qs]))}
    return out


def paired_tests(rr_new: np.ndarray, rr_ref: np.ndarray, seed: int = 0, n_boot: int = 20000) -> dict:
    """Paired t, sign test, Wilcoxon and bootstrap CI on per-question reciprocal-rank differences
    (same as experiments/17_lex_rerank/evaluate.py)."""
    from scipy import stats
    d = np.asarray(rr_new, dtype=np.float64) - np.asarray(rr_ref, dtype=np.float64)
    n = len(d)
    wins, losses = int((d > 1e-12).sum()), int((d < -1e-12).sum())
    out = {"n": n, "mean_diff": float(d.mean()), "wins": wins, "losses": losses, "ties": n - wins - losses}
    if n > 1 and d.std() > 0:
        t = stats.ttest_rel(rr_new, rr_ref)
        out["t"] = float(t.statistic); out["p_t"] = float(t.pvalue)
        try:
            out["p_wilcoxon"] = float(stats.wilcoxon(rr_new, rr_ref, zero_method="wilcox").pvalue)
        except ValueError:
            out["p_wilcoxon"] = None
    else:
        out["t"] = None; out["p_t"] = None; out["p_wilcoxon"] = None
    out["p_sign"] = float(stats.binomtest(wins, wins + losses, 0.5).pvalue) if wins + losses else None
    rng = np.random.default_rng(seed)
    boots = np.array([d[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    out["ci95"] = [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]
    return out


def rr_vector(ranks: dict[str, int | None], qids: list[str]) -> np.ndarray:
    return np.array([1.0 / ranks[q] if ranks.get(q) else 0.0 for q in qids], dtype=np.float64)


def ranking_from_scores(scores: np.ndarray, doc_ids: list[str], top: int = 50) -> list[str]:
    k = min(top, len(scores) - 1)
    cand = np.argpartition(-scores, k)[:k + 1] if k < len(scores) - 1 else np.arange(len(scores))
    cand = cand[np.argsort(-scores[cand], kind="stable")]
    return [doc_ids[j] for j in cand[:top] if scores[j] > -np.inf]


def fmt_row(label: str, m: dict, extra: str = "") -> str:
    return (f"| {label} | {m['train']['mrr']:.3f} | **{m['val']['mrr']:.3f}** | {m['all']['mrr']:.3f} | "
            f"{m['train']['hit@1']:.3f} | {m['val']['hit@1']:.3f} | {m['all']['hit@1']:.3f} | "
            f"{m['val']['recall@10']:.3f} | {m['all']['recall@10']:.3f} | {m['val']['recall@30']:.3f} | {m['all']['recall@30']:.3f} |{(' ' + extra + ' |') if extra else ''}")


TABLE_HEAD = ["| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | R@30 val | R@30 all |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]


def fmt_test(label: str, t: dict) -> str:
    if t.get("p_t") is None:
        return f"| {label} | {t['mean_diff']:+.3f} | {t['wins']} / {t['losses']} / {t['ties']} | – | – | – | – |"
    pw = f"{t['p_wilcoxon']:.3f}" if t.get("p_wilcoxon") is not None else "–"
    ps = f"{t['p_sign']:.3f}" if t.get("p_sign") is not None else "–"
    return (f"| {label} | {t['mean_diff']:+.3f} | {t['wins']} / {t['losses']} / {t['ties']} | {t['p_t']:.3f} | {ps} | {pw} | "
            f"[{t['ci95'][0]:+.3f}, {t['ci95'][1]:+.3f}] |")


TEST_HEAD = ["| comparison (val) | mean Δrr | wins / losses / ties | paired t p | sign p | Wilcoxon p | bootstrap 95 % CI |",
             "|---|---:|---|---:|---:|---:|---|"]


# sentence splitting ------------------------------------------------------------------------------
_ABBR = {w.lower() for w in (
    "art arts n nr nrs no al par p pp cf etc M MM Mme Mlle ch vol éd ed c Ci RH E T AR L LP AGFisc AAF AFER R D S V Q W B K "
    "St Ste min max env resp réf ref op cit ibid suiv ss s préc i e ex dd d v vs Cass Civ Comm Trib").split()}
_SENT_END = re.compile(r"[.;!?]+[\"»)\]]?\s+(?=[«\"(]?[A-ZÀ-ÜÉÈ0-9])")
_WORD_BEFORE = re.compile(r"([A-Za-zÀ-ÿ]+|\d+)$")
_NEWLINE_BREAK = re.compile(r"\n\s*\n")


def _is_boundary(text: str, m: re.Match) -> bool:
    """A '.' after an abbreviation, a lone digit ('1. Quelles …', 'art. 5, § 1. Les …') or a single capital
    letter is not a sentence end; ';' '!' '?' always are."""
    if m.group(0)[0] != ".":
        return True
    w = _WORD_BEFORE.search(text, max(0, m.start() - 12), m.start())
    if not w:
        return True
    tok = w.group(1)
    if tok.lower() in _ABBR or (tok.isdigit() and len(tok) <= 2) or (len(tok) == 1 and tok.isupper()):
        return False
    return True


def sentence_spans(text: str) -> list[tuple[int, int]]:
    """(start, end) spans of sentences; paragraph breaks always split, '.;!?' followed by a capital
    or digit split unless preceded by a common abbreviation or a lone digit/letter."""
    spans = []
    pos = 0
    for para in _NEWLINE_BREAK.finditer(text):
        spans.extend(_split_para(text, pos, para.start()))
        pos = para.end()
    spans.extend(_split_para(text, pos, len(text)))
    return spans


def _split_para(text: str, a: int, b: int) -> list[tuple[int, int]]:
    out = []
    start = a
    for m in _SENT_END.finditer(text, a, b):
        if not _is_boundary(text, m):
            continue
        end = m.start() + len(m.group(0).rstrip())
        if end > start:
            out.append((start, end))
        start = m.end()
    if b > start:
        out.append((start, b))
    return out
