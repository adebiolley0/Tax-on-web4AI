"""Shared pieces for the corpus-C scripts: chunking + cache key + tokenizer."""
from __future__ import annotations

import sys
from pathlib import Path

from rag_eval import load_corpus_c, fixed_chunks
from rag_eval.corpora import DATA_DIR

sys.path.insert(0, str((DATA_DIR.parent / "02_dense_sweep").resolve()))
sys.path.insert(0, str((DATA_DIR.parent / "03_hybrid_rerank").resolve()))
from models import MODELS  # noqa: E402
from run_sweep import Encoder  # noqa: E402

CHUNKERS = {
    "fixed1200_title": lambda docs: fixed_chunks(docs, 1200, 100, prefix_title=True),
    "fixed1500_title": lambda docs: fixed_chunks(docs, 1500, 200, prefix_title=True),
}


def chunk_corpus_c(chunker: str = "fixed1200_title", max_chars: int | None = 200_000):
    docs = load_corpus_c(max_chars=max_chars)
    return docs, CHUNKERS[chunker](docs)


def cache_extra(spec, chunker: str) -> str:
    return f"seq{spec.max_seq}|d_prefix={spec.d_prefix!r}|C/{chunker}"
