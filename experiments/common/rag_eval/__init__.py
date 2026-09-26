"""Shared harness for RAG experiments: corpora, questions, metrics, result logging, paired statistics."""
__version__ = "0.2.0"
from rag_eval.corpora import (
    Chunk,
    Doc,
    Question,
    load_corpus_a,
    load_corpus_b,
    load_questions_a,
    load_questions_b,
    load_corpus,
    load_corpus_c,
    load_questions_c,
    question_split,
    filter_split,
)
from rag_eval.metrics import evaluate_rankings, RunResult
from rag_eval.cache import EmbeddingCache
from rag_eval.results import save_result, append_leaderboard, print_leaderboard, build_provenance
# paired statistics live in rag_eval.stats (needs scipy): `from rag_eval.stats import compare_runs`
from rag_eval.chunking import whole_doc, fixed_chunks, article_chunks

__all__ = [
    "Chunk", "Doc", "Question",
    "load_corpus_a", "load_corpus_b", "load_questions_a", "load_questions_b", "load_corpus",
    "load_corpus_c", "load_questions_c", "question_split", "filter_split",
    "evaluate_rankings", "RunResult", "EmbeddingCache", "save_result", "append_leaderboard", "print_leaderboard",
    "whole_doc", "fixed_chunks", "article_chunks",
    "build_provenance", "__version__",
]
