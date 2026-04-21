"""Embedding generation using sentence-transformers."""

from __future__ import annotations

import logging
import os
from typing import Sequence

from sentence_transformers import SentenceTransformer

from tax_search.models import Chunk, EmbeddedChunk

logger = logging.getLogger(__name__)

MODEL_NAME = os.environ.get(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

# Module-level caches
_model: SentenceTransformer | None = None
_model_cache: dict[str, SentenceTransformer] = {}


def get_model() -> SentenceTransformer:
    """Load the default embedding model (cached singleton)."""
    global _model
    if _model is None:
        _model = get_model_by_name(MODEL_NAME)
    return _model


def get_model_by_name(model_name: str) -> SentenceTransformer:
    """Load or retrieve a cached SentenceTransformer by HuggingFace model ID.

    The model is cached per *model_name* so subsequent calls with the same
    identifier are free.  Raises ``OSError`` / ``EnvironmentError`` if the
    model weights are not available locally and no internet connection is
    present — callers that want optional models should catch those errors.
    """
    if model_name not in _model_cache:
        logger.info("Loading embedding model: %s", model_name)
        _model_cache[model_name] = SentenceTransformer(model_name)
        dim = _model_cache[model_name].get_embedding_dimension()
        logger.info("Model loaded, dimension=%d", dim)
    return _model_cache[model_name]


def embed_texts(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """Embed texts using the default model, returning float vectors."""
    return embed_texts_with(get_model(), texts, batch_size=batch_size)


def embed_texts_with(
    model: SentenceTransformer,
    texts: list[str],
    batch_size: int = 64,
    prompt_name: str | None = None,
) -> list[list[float]]:
    """Embed texts using the provided model instance.

    If *prompt_name* is given and the model defines that prompt, it is passed
    to ``encode()`` for query-side instruction prefixing (e.g. BGE-M3).
    Falls back to raw encode if the prompt is not found.
    """
    kwargs: dict = {"batch_size": batch_size, "show_progress_bar": False}
    if prompt_name:
        try:
            embeddings = model.encode(texts, prompt_name=prompt_name, **kwargs)
        except (ValueError, KeyError):
            logger.warning(
                "prompt_name=%r not found in model config, using raw encode",
                prompt_name,
            )
            embeddings = model.encode(texts, **kwargs)
    else:
        embeddings = model.encode(texts, **kwargs)
    return [vec.tolist() for vec in embeddings]


def embed_chunks(chunks: Sequence[Chunk], batch_size: int = 64) -> list[EmbeddedChunk]:
    """Embed chunks using the default model."""
    return embed_chunks_with(get_model(), chunks, batch_size=batch_size)


def embed_chunks_with(
    model: SentenceTransformer,
    chunks: Sequence[Chunk],
    batch_size: int = 64,
) -> list[EmbeddedChunk]:
    """Embed a sequence of chunks using the provided model instance."""
    if not chunks:
        return []

    texts = [c.chunk_text for c in chunks]
    vectors = embed_texts_with(model, texts, batch_size=batch_size)

    result = [EmbeddedChunk(chunk=chunk, vector=vector) for chunk, vector in zip(chunks, vectors)]
    logger.info("Embedded %d chunks", len(result))
    return result
