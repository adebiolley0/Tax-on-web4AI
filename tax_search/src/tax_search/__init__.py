"""Belgian tax semantic search: Qdrant + embeddings + retrieval strategies."""

from tax_search.models import Chunk, Document, EmbeddedChunk, SourceType
from tax_search.qdrant_store import (
    COLLECTION_NAME,
    VECTOR_SIZE,
    ensure_collection,
    get_client,
    search_similar,
    upsert_chunks,
)

__all__ = [
    "COLLECTION_NAME",
    "VECTOR_SIZE",
    "Chunk",
    "Document",
    "EmbeddedChunk",
    "SourceType",
    "ensure_collection",
    "get_client",
    "search_similar",
    "upsert_chunks",
]
