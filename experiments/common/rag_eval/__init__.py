"""Shared harness for RAG experiments: corpora, questions, metrics, result logging."""
from rag_eval.corpora import (
    Chunk,
    Doc,
    Question,
    load_corpus_a,
    load_corpus_b,
    load_questions_a,
    load_questions_b,
    load_corpus,
)
from rag_eval.metrics import evaluate_rankings, RunResult
from rag_eval.cache import EmbeddingCache
from rag_eval.results import save_result, append_leaderboard, print_leaderboard
from rag_eval.chunking import whole_doc, fixed_chunks, article_chunks

__all__ = [
    "Chunk", "Doc", "Question",
    "load_corpus_a", "load_corpus_b", "load_questions_a", "load_questions_b", "load_corpus",
    "evaluate_rankings", "RunResult", "EmbeddingCache", "save_result", "append_leaderboard", "print_leaderboard",
    "whole_doc", "fixed_chunks", "article_chunks",
]
