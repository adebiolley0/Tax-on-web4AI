"""Shared evaluation harness for the Belgian-tax RAG experiments.

Modules: :mod:`~rag_eval.corpora` (documents, questions, split protocol), :mod:`~rag_eval.chunking`,
:mod:`~rag_eval.metrics` (``evaluate_rankings``), :mod:`~rag_eval.results` (run JSONs, leaderboard,
provenance), :mod:`~rag_eval.splits` (train / val view of saved runs), :mod:`~rag_eval.cache`
(embedding cache), :mod:`~rag_eval.stats` (paired tests; needs scipy, import explicitly),
:mod:`~rag_eval.mining` + :mod:`~rag_eval.legal_refs` (regenerating the mined question sets).
See ``experiments/common/README.md``.
"""
__version__ = "0.3.0"

from rag_eval.cache import EmbeddingCache, cache_key
from rag_eval.chunking import article_chunks, fixed_chunks, whole_doc
from rag_eval.corpora import (
    Chunk,
    Doc,
    Question,
    filter_split,
    load_corpus,
    load_corpus_a,
    load_corpus_b,
    load_corpus_c,
    load_questions,
    load_questions_a,
    load_questions_b,
    load_questions_c,
    load_questions_mined,
    parse_front_matter,
    question_split,
    slice_questions,
)
from rag_eval.metrics import RunResult, dedupe_ranked, evaluate_rankings
from rag_eval.results import append_leaderboard, build_provenance, load_result, print_leaderboard, save_result

__all__ = [
    "__version__",
    "Chunk", "Doc", "Question",
    "load_corpus", "load_corpus_a", "load_corpus_b", "load_corpus_c",
    "load_questions", "load_questions_a", "load_questions_b", "load_questions_c", "load_questions_mined",
    "parse_front_matter", "question_split", "filter_split", "slice_questions",
    "whole_doc", "fixed_chunks", "article_chunks",
    "evaluate_rankings", "RunResult", "dedupe_ranked",
    "save_result", "append_leaderboard", "print_leaderboard", "build_provenance", "load_result",
    "EmbeddingCache", "cache_key",
]
