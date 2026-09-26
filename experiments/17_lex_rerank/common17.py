"""Experiment 17 – shared pieces.

* the experiment-13 recommended lexical configuration per corpus (chosen on *train* in exp 13,
  see ../13_lexical_upgrades/runs/<corpus>_summary.json) and the code to rebuild that ranking
  from exp 13's cached tokenisation (``../13_lexical_upgrades/.cache``);
* stage-1 cache format (``cache/<corpus>_lex.npz`` + ``cache/<corpus>_lex_texts.json``):
  per question the top-``TOP_UNITS`` units (chunk indices + BM25F scores) and the texts the
  cross-encoder sees; unit index == chunk index of experiment 14 on corpus C;
* the bar pipelines whose per-question ranks are stored in ``experiments/results``.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from rag_eval.corpora import DATA_DIR

EXP = "17_lex_rerank"
EXP_DIR = Path(__file__).resolve().parent
CACHE = EXP_DIR / "cache"
RUNS = EXP_DIR / "runs"
RESULTS = DATA_DIR.parent / "results"
EXP13 = DATA_DIR.parent / "13_lexical_upgrades"
EXP14_CACHE = DATA_DIR.parent / "14_ltr_fusion" / "cache"
for _p in (EXP13, DATA_DIR.parent / "08_corpus_b_cleanup"):
    sys.path.insert(0, str(_p.resolve()))

TOP_UNITS = 200            # units kept per question in the stage-1 cache (≥ the deepest reranker depth)
DEPTHS = (20, 30, 50)
BETAS = (0.5, 0.7, 1.0)
RERANKER = "bge-reranker-v2-m3"
RERANKER_HF = "BAAI/bge-reranker-v2-m3"

# experiment-13 final configuration per corpus (`combo__fields+tok01+num+cues`, selected on train)
LEX_CONFIG = {
    "C": {"tokenizer": {"base": "01", "numbers": True, "artrefs": False}, "clean_b": False,
          "weights": {"title": 8.0, "heading": 0.0, "body": 1.0}, "k1": 0.9,
          "b": {"title": 0.75, "heading": 0.75, "body": 0.4}, "region_w": 0.0, "doctype_w": 0.0},
    "B": {"tokenizer": {"base": "01", "numbers": True, "artrefs": False}, "clean_b": True,
          "weights": {"title": 8.0, "heading": 3.0, "body": 1.0, "cue": 1.0}, "k1": 1.5,
          "b": {"title": 0.3, "heading": 0.3, "body": 0.75}, "region_w": 0.0, "doctype_w": 1.0},
}
# the bars (val MRR) and the runs whose per-question ranks reproduce them
BARS = {
    "C": {"bar": RESULTS / "09_corpus_c" / "C__bm25__fixed1200_title__bm25_bge-reranker-v2-m3_30.json",
          "bar_label": "exp 09: BM25 (tok03, chunks) + bge-reranker-v2-m3 @30",
          "first_stage": RESULTS / "09_corpus_c" / "C__bm25_chunk__fixed1200_title.json",
          "first_stage_label": "exp 09: BM25 tok03 on 1200-char chunks (old first stage)",
          "lex13": RESULTS / "13_lexical_upgrades" / "C__combo__fields_tok01_num_cues.json"},
    "B": {"bar": RESULTS / "03_hybrid_rerank" / "B__e5-small__article_ctx_1200__rrf_mmarco-minilm_30.json",
          "bar_label": "exp 03: e5-small + BM25 RRF + mMARCO-MiniLM @30",
          "first_stage": RESULTS / "03_hybrid_rerank" / "B__e5-small__article_ctx_1200__rrf.json",
          "first_stage_label": "exp 03: e5-small + BM25 RRF (old first stage)",
          "bge_bar": RESULTS / "03_hybrid_rerank" / "B__e5-small__article_ctx_1200__rrf_bge-reranker-v2-m3_30.json",
          "lex13": RESULTS / "13_lexical_upgrades" / "B__combo__fields_tok01_num_cues.json"},
}


@dataclass
class LexStage1:
    corpus: str
    qids: list[str]
    doc_ids: list[str]                 # doc index → doc id
    unit_doc: np.ndarray               # unit → doc index
    top_units: np.ndarray              # (nq, TOP_UNITS) unit indices (-1 padded), descending score
    top_scores: np.ndarray             # (nq, TOP_UNITS) BM25F scores
    texts: dict[int, str]              # unit index → reranker text (only for cached units)
    timing: dict

    @classmethod
    def load(cls, corpus: str) -> "LexStage1":
        z = np.load(CACHE / f"{corpus}_lex.npz", allow_pickle=False)
        meta = json.loads((CACHE / f"{corpus}_lex.json").read_text())
        texts = {int(k): v for k, v in json.loads((CACHE / f"{corpus}_lex_texts.json").read_text()).items()}
        return cls(corpus, meta["qids"], meta["doc_ids"], z["unit_doc"], z["top_units"], z["top_scores"], texts, meta["timing"])

    def doc_ranking(self, qi: int, top: int = 50) -> list[str]:
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

    def candidates(self, qi: int, depth: int) -> tuple[np.ndarray, np.ndarray]:
        """Top-``depth`` units with a positive score (chunk level, like exp 03 / 09)."""
        u, s = self.top_units[qi][:depth], self.top_scores[qi][:depth]
        m = (u >= 0) & (s > 0)
        return u[m], s[m]


def rerank_cache_path(corpus: str, tag: str = "") -> Path:
    return CACHE / f"{corpus}_rerank_{RERANKER}{tag}.npz"


def load_rerank_cache(path: Path) -> dict[tuple[int, int], float]:
    if not path.exists():
        return {}
    z = np.load(path, allow_pickle=False)
    return {(int(q), int(c)): float(s) for q, c, s in zip(z["q_idx"], z["chunk_idx"], z["score"])}


def per_question_ranks(result_json: Path) -> dict[str, int | None]:
    r = json.loads(result_json.read_text())
    return {qid: v["rank"] for qid, v in r["per_question"].items()}


def split_metrics_from_ranks(ranks: dict[str, int | None], questions) -> dict:
    """train / val / all MRR, hit@1, recall@10 (first-hit recall, as rag_eval.splits) from stored ranks."""
    out = {}
    for sp in ("train", "val", "all"):
        qs = [q for q in questions if sp == "all" or q.split == sp]
        rr = [1.0 / ranks[q.qid] if ranks.get(q.qid) else 0.0 for q in qs]
        out[sp] = {"n": len(qs), "mrr": float(np.mean(rr)),
                   "hit@1": float(np.mean([1.0 if ranks.get(q.qid) == 1 else 0.0 for q in qs])),
                   "recall@10": float(np.mean([1.0 if ranks.get(q.qid) and ranks[q.qid] <= 10 else 0.0 for q in qs]))}
    return out


def minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(x.min()), float(x.max())
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x, dtype=np.float64)


_B_CODE_CUES = [(r"\btva\b|taxe sur la valeur", "dtctva"), (r"\btva\b|facture", "dtartva"), (r"succession|deces|decede|herit", "dtcsucc"),
                (r"enregistrement|donation|achete|achat|vente d'un|droits de vente", "dtcenr"), (r"circulation|immatricul|voiture|mise en circulation", "dtcta"),
                (r"impot des societes|societe|impot des personnes|declaration|revenus", "dtcir92"), (r"flandre|flamand|gand|louvain|anvers", "dtvcf"),
                (r"precompte immobilier|bruxelles", "dtcbpf")]


def b_code_cues(question: str) -> list[str]:
    from lexical import fold
    q = fold(question.lower())
    return [tok for pat, tok in _B_CODE_CUES if re.search(pat, q)]
