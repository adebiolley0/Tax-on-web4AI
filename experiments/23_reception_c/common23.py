"""Experiment 23 – reception field for corpus C: shared paths, reference runs, metrics and table helpers.

Run everything with an existing venv (no new venv):
    cd experiments/13_lexical_upgrades && .venv/bin/python ../23_reception_c/<script>.py      # BM25 / numpy jobs
    cd experiments/14_ltr_fusion && flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 \
        .venv/bin/python ../23_reception_c/rerank23.py                                       # the one torch job
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from rag_eval.corpora import DATA_DIR, REPO_ROOT, QUESTIONS_C_MINED

EXP = "23_reception_c"
EXP_DIR = Path(__file__).resolve().parent
CACHE = EXP_DIR / "cache"
RUNS = EXP_DIR / "runs"
EXPS = DATA_DIR.parent
RESULTS = EXPS / "results"
MYFIN = REPO_ROOT / "myfin_docs"
for _p in ("11_graph_retrieval", "13_lexical_upgrades", "08_corpus_b_cleanup", "17_lex_rerank", "14_ltr_fusion", "20_reception_intent"):
    sys.path.insert(0, str((EXPS / _p).resolve()))

# reference runs (stored per-question ranks)
REFS = {
    "lex13_human": (RESULTS / "13_lexical_upgrades" / "C__combo__fields_tok01_num_cues.json", "exp 13: BM25F lexical (human, val 0.616)"),
    "lex13_mined": (RESULTS / "21_mined_eval" / "C__mined__exp13_lex.json", "exp 21: exp-13 lexical on the 697 mined questions (0.729)"),
    "bar": (RESULTS / "09_corpus_c" / "C__bm25__fixed1200_title__bm25_bge-reranker-v2-m3_30.json", "exp 09: BM25 + bge @30 (round-1 bar, val 0.665)"),
    "r2_best": (RESULTS / "17_lex_rerank" / "C__lex13_bge_20.json", "exp 17: exp-13 lexical → bge @20 (round-2 best, val 0.688)"),
}
SLICES = ("pq", "ruling", "faq")
STATUTE_FOLDERS = {"code_et_legislation", "legislation_et_reglementation_regionale_et_locale", "arretes_royaux", "arretes_ministeriels"}


def per_question_ranks(path: Path) -> dict[str, int | None]:
    r = json.loads(Path(path).read_text())
    return {qid: v["rank"] for qid, v in r["per_question"].items()}


def ranks_of(res) -> dict[str, int | None]:
    return {qid: v["rank"] for qid, v in res.per_question.items()}


def _m(ranks: dict, qs) -> dict:
    rr = [1.0 / ranks[q.qid] if ranks.get(q.qid) else 0.0 for q in qs]
    hit = lambda k: float(np.mean([1.0 if ranks.get(q.qid) and ranks[q.qid] <= k else 0.0 for q in qs]))
    return {"n": len(qs), "mrr": float(np.mean(rr)) if qs else 0.0, "hit@1": hit(1), "recall@10": hit(10), "recall@20": hit(20), "recall@30": hit(30)}


def split_metrics(ranks: dict, questions) -> dict:
    """train / val / all (human) – MRR, H@1, first-hit R@10/20/30."""
    return {sp: _m(ranks, [q for q in questions if sp == "all" or q.split == sp]) for sp in ("train", "val", "all")}


def slice_metrics(ranks: dict, questions) -> dict:
    """all / pq / ruling / faq / train / val (mined)."""
    out = {}
    for sl in ("all",) + SLICES + ("train", "val"):
        qs = [q for q in questions if sl == "all" or q.meta.get("source") == sl or (sl in ("train", "val") and q.split == sl)]
        if qs:
            out[sl] = _m(ranks, qs)
    return out


def rr_vec(ranks: dict, qids) -> np.ndarray:
    return np.array([1.0 / ranks[q] if ranks.get(q) else 0.0 for q in qids], dtype=np.float64)


def paired(ranks_base: dict, ranks_new: dict, qids) -> dict:
    """rag_eval.stats.paired_stats on reciprocal ranks (Δ = new − base) and on hit@10."""
    from rag_eval.stats import paired_stats
    qids = list(qids)
    if len(qids) < 3:
        return {"n": len(qids)}
    p = paired_stats(rr_vec(ranks_base, qids), rr_vec(ranks_new, qids), "rr")
    h = paired_stats((np.array([ranks_base.get(q) or 10**9 for q in qids]) <= 10).astype(float),
                     (np.array([ranks_new.get(q) or 10**9 for q in qids]) <= 10).astype(float), "hit@10")
    return {"n": p.n, "mrr_base": p.mean_a, "mrr_new": p.mean_b, "delta": p.delta, "ci": [p.ci_lo, p.ci_hi], "ci_method": p.ci_method,
            "p_t": p.p_t, "p_perm": p.p_perm, "perm_exact": p.perm_exact, "wins": p.wins, "losses": p.losses, "ties": p.ties,
            "effect": p.effect_size, "delta_hit10": h.delta, "p_t_hit10": h.p_t}


def fmt_p(label: str, t: dict) -> str:
    if "delta" not in t:
        return f"| {label} | n={t['n']} | – | – | – | – | – |"
    return (f"| {label} | {t['n']} | {t['mrr_base']:.3f} → {t['mrr_new']:.3f} | {t['delta']:+.3f} [{t['ci'][0]:+.3f}, {t['ci'][1]:+.3f}] | "
            f"{t['p_t']:.3f} / {t['p_perm']:.3f} | {t['wins']} / {t['losses']} / {t['ties']} | {t['delta_hit10']:+.3f} ({t['p_t_hit10']:.3f}) |")


P_HEAD = ["| comparison [slice] | n | MRR base → new | Δ MRR [95 % CI] | p_t / p_perm | W / L / T | Δ hit@10 (p_t) |",
          "|---|---:|---|---|---|---|---|"]


def fmt_human(label: str, m: dict) -> str:
    return (f"| {label} | {m['train']['mrr']:.3f} | **{m['val']['mrr']:.3f}** | {m['all']['mrr']:.3f} | {m['val']['hit@1']:.3f} | {m['all']['hit@1']:.3f} | "
            f"{m['val']['recall@10']:.3f} | {m['all']['recall@10']:.3f} | {m['val']['recall@20']:.3f} | {m['all']['recall@20']:.3f} | "
            f"{m['val']['recall@30']:.3f} | {m['all']['recall@30']:.3f} |")


HUMAN_HEAD = ["| run | MRR train | MRR **val** | MRR all | H@1 val | H@1 all | R@10 val | R@10 all | R@20 val | R@20 all | R@30 val | R@30 all |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]


def fmt_mined(label: str, m: dict) -> str:
    cells = []
    for sl in ("all",) + SLICES + ("train", "val"):
        d = m.get(sl)
        cells.append(f"{d['mrr']:.3f} / {d['hit@1']:.3f} / {d['recall@10']:.3f} / {d['recall@30']:.3f}" if d else "–")
    return f"| {label} | " + " | ".join(cells) + " |"


MINED_HEAD = ["| run (MRR / H@1 / R@10 / R@30) | all (697) | pq (163) | ruling (377) | faq (157) | train (352) | val (345) |",
              "|---|---|---|---|---|---|---|"]


def mined_provenance(res) -> None:
    """Stamp the mined question file in the provenance (the harness stamps the human file by default)."""
    import hashlib
    from rag_eval.results import build_provenance
    res.provenance = build_provenance(res)
    res.provenance["questions_file"] = str(QUESTIONS_C_MINED.relative_to(REPO_ROOT))
    res.provenance["questions_sha256"] = hashlib.sha256(QUESTIONS_C_MINED.read_bytes()).hexdigest()
