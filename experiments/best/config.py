"""Fixed configuration of the best measured retrieval pipelines (experiments/EXPERIMENTS.md §4, round-2/3 amendments).

Nothing in this file is tuned at run time: every value was selected on train splits in the experiments named next
to it and is frozen here. Paths can be moved with BEST_CACHE / BEST_INDEX (both git-ignored).
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

BEST_DIR = Path(__file__).resolve().parent
EXPERIMENTS = BEST_DIR.parent
CACHE = Path(os.environ.get("BEST_CACHE", BEST_DIR / "cache"))     # score caches keyed by question text (git-ignored)
INDEX = Path(os.environ.get("BEST_INDEX", BEST_DIR / "index"))     # built indexes: lexical pickles, reception, ColBERT tokens
RUNS = BEST_DIR / "runs"
EXP_NAME = "best"                                                   # experiments/results/best/, leaderboard rows
TORCH_LOCK = EXPERIMENTS / ".torch.lock"                            # flock this for any torch job (round-3 rule)

# ── models (all in the HF cache; HF_HUB_OFFLINE=1 is fine) ───────────────────────────────────────────────────
E5_ID = "intfloat/multilingual-e5-small"                            # dense leg (exp 02 / 03 / 09: best quality per CPU second)
COLBERT_ID = "antoinelouis/colbertv1-camembert-base-mmarcoFR"       # French ColBERT via PyLate (exp 12 / 22)
MMARCO_ID = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"            # cheap cross-encoder, corpus B short questions (exp 03 / 14 / 22)
BGE_ID = "BAAI/bge-reranker-v2-m3"                                  # strong cross-encoder, corpus C (exp 09 / 17)
RERANK_MAX_LENGTH = 512                                             # exp 17: 512 == 1024 in quality, −20 % time
E5_MAX_SEQ = 512
E5_Q_PREFIX, E5_D_PREFIX = "query: ", "passage: "

# ── chunking (the "chunk universe" of the dense / ColBERT / reranker stages) ─────────────────────────────────
# B: article_ctx_1200 = article_chunks(docs, 1200, 100, prefix_context=True) on the RAW articles (exp 02 / 14 / 22)
# C: fixed1200_title = fixed_chunks(docs, 1200, 100, prefix_title=True), docs truncated at 200k chars (exp 09 / 14 / 17)
CHUNKING = {"B": ("article_ctx_1200", 1200, 100), "C": ("fixed1200_title", 1200, 100)}
C_MAX_CHARS = 200_000
# shared embedding cache keys (experiments/data/emb_cache; same strings as exp 02 / 09 so the vectors are reused)
EMB_EXTRA = {"B": "seq512|d_prefix='passage: '|article_ctx_1200", "C": "seq512|d_prefix='passage: '|C/fixed1200_title"}

# ── lexical stage (exp 13 final configuration per corpus, selected on train; exp 17 `LEX_CONFIG`) ────────────
LEX_CONFIG = {
    # A: exp-01 best = whole-document BM25, tok01 (Snowball + bm25s French stoplist + question words + accent fold), k1 1.5 b 0.75
    "A": {"tokenizer": {"base": "01", "numbers": False, "artrefs": False}, "clean_b": False,
          "weights": {"body": 1.0}, "k1": 1.5, "b": {"body": 0.75}, "doctype_w": 0.0},
    # B: cleaned articles (exp 08), 2000-char units, BM25F title ×8 / heading ×3 / body / code-family cue field, k1 1.5
    "B": {"tokenizer": {"base": "01", "numbers": True, "artrefs": False}, "clean_b": True,
          "weights": {"title": 8.0, "heading": 3.0, "body": 1.0, "cue": 1.0}, "k1": 1.5,
          "b": {"title": 0.3, "heading": 0.3, "body": 0.75}, "doctype_w": 1.0},
    # C: fixed1200_title chunks, BM25F title ×8, k1 0.9 / b 0.4 (exp 13: val 0.536 → 0.616 at zero query cost)
    "C": {"tokenizer": {"base": "01", "numbers": True, "artrefs": False}, "clean_b": False,
          "weights": {"title": 8.0, "heading": 0.0, "body": 1.0}, "k1": 0.9,
          "b": {"title": 0.75, "heading": 0.75, "body": 0.4}, "doctype_w": 0.0},
}
# reception field on B (exp 20, train-selected point; exp 22 uses the same): citing sentences + citing titles, BM25F weight 0.5, b 0.5
RECEPTION = {"variant": "sent+title", "weight": 0.5, "b": 0.5, "field": "rec_sent+title"}

# ── corpus B first stage + gate (exp 22 §2.5, gate.py) ──────────────────────────────────────────────────────
B_LEGS = ("rec", "colbert", "e5")
B_WEIGHTS_SHORT = {"rec": 1 / 3, "colbert": 1 / 3, "e5": 1 / 3}      # `z3_equal`, pre-registered, selected on mined train
B_WEIGHTS_LONG = {"rec": 0.5, "colbert": 0.0, "e5": 0.5}             # `z_rec_e5`, un-reranked route for long questions
COLBERT_QUERY_LENGTH = 48                                            # exp 12 set-up; 256 collapses on citizen questions (exp 22)
GATE_WORDS = 25                                                      # ≤ 25 words → mMARCO route (T chosen on train splits, exp 22)
MMARCO_DEPTH = 30                                                    # top-30 articles
CHUNK_CAP = 3                                                        # best 3 chunks per article by z(colbert) + z(e5)
MMARCO_BETA = 0.8                                                    # 0.8 minmax(reranker) + 0.2 minmax(stage 1) (exp 14 value, not re-tuned)
B_TOP = 60                                                           # ranking depth returned

# ── corpus C (exp 17: lexical → bge @20, reranker score only) ───────────────────────────────────────────────
C_LEX_TOP_UNITS = 200
C_BGE_DEPTH = 20
C_TOP = 50
A_TOP = 50

# ── latency (hard requirement: a retrieval above the budget is a failure; budget.py, evaluate.py --live) ────
LATENCY_BUDGET_S = 5.0                                               # per query, models loaded, 4 CPU threads
LIVE_BATCH = {"mmarco": 8, "bge": 2}                                 # cross-encoder mini-batch under a deadline (≈ 1 s each here)


def qkey(question: str) -> str:
    """Cache key of a question: sha1 of its stripped text (caches are keyed by text, not by question id)."""
    return hashlib.sha1(question.strip().encode("utf-8")).hexdigest()


def fingerprint(texts) -> str:
    """Fingerprint of a chunk universe (order-sensitive), stored in every cache and checked on load."""
    h = hashlib.sha256()
    h.update(str(len(texts)).encode())
    for t in texts:
        h.update(hashlib.sha1(t.encode("utf-8")).digest())
    return h.hexdigest()[:24]
