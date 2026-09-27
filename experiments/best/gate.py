"""Length gate of the corpus-B pipeline (exp 22 §2.5): questions of at most GATE_WORDS words take the mMARCO route
(three-leg fusion → mMARCO @30, β 0.8); longer, document-like questions (pasted PQ blocks, ruling objects) take the
un-reranked reception + e5 fusion, because both cross-encoders are destructive on long queries (exp 21 / 22, p < 0.001)
and ColBERT's 48-token query window truncates them."""
from __future__ import annotations

from config import GATE_WORDS

SHORT, LONG = "short", "long"


def n_words(question: str) -> int:
    return len(question.split())


def route(question: str, threshold: int = GATE_WORDS) -> str:
    return SHORT if n_words(question) <= threshold else LONG
