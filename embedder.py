"""Embedding generation using sentence-transformers."""

from __future__ import annotations

import logging
from typing import Sequence

from sentence_transformers import SentenceTransformer

from models import Chunk, EmbeddedChunk

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load the embedding model (cached singleton)."""
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
        dim = _model.get_embedding_dimension()
        logger.info("Model loaded, dimension=%d", dim)
    return _model


def embed_texts(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """Embed a list of texts, returning float vectors."""
    model = get_model()
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
    return [vec.tolist() for vec in embeddings]


def embed_chunks(chunks: Sequence[Chunk], batch_size: int = 64) -> list[EmbeddedChunk]:
    """Embed a sequence of chunks, returning EmbeddedChunks with vectors."""
    if not chunks:
        return []

    texts = [c.chunk_text for c in chunks]
    vectors = embed_texts(texts, batch_size=batch_size)

    result = []
    for chunk, vector in zip(chunks, vectors):
        result.append(EmbeddedChunk(chunk=chunk, vector=vector))

    logger.info("Embedded %d chunks", len(result))
    return result
