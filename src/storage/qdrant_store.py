"""Qdrant vector store management for Belgian tax documents."""

from __future__ import annotations

import logging
from typing import Sequence

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from models import Chunk, EmbeddedChunk

logger = logging.getLogger(__name__)

COLLECTION_NAME = "belgian_tax_docs"
VECTOR_SIZE = 384  # paraphrase-multilingual-MiniLM-L12-v2
QDRANT_URL = "http://localhost:6333"


def get_client(url: str = QDRANT_URL, in_memory: bool = False) -> QdrantClient:
    """Get a Qdrant client. Use in_memory=True for testing without a server."""
    if in_memory:
        return QdrantClient(location=":memory:")
    return QdrantClient(url=url)


def ensure_collection(client: QdrantClient) -> None:
    """Create the collection if it doesn't exist."""
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in collections:
        logger.info("Collection %r already exists", COLLECTION_NAME)
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )
    logger.info("Created collection %r", COLLECTION_NAME)

    # Create payload indexes for filtered search
    for field, schema in [
        ("source_domain", PayloadSchemaType.KEYWORD),
        ("source_type", PayloadSchemaType.KEYWORD),
        ("tax_category", PayloadSchemaType.KEYWORD),
        ("audience", PayloadSchemaType.KEYWORD),
        ("document_type", PayloadSchemaType.KEYWORD),
        ("language", PayloadSchemaType.KEYWORD),
        ("fiscal_codes", PayloadSchemaType.KEYWORD),
        ("document_id", PayloadSchemaType.KEYWORD),
        ("content_hash", PayloadSchemaType.KEYWORD),
    ]:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field,
            field_schema=schema,
        )
    logger.info("Created payload indexes")


def _chunk_to_payload(chunk: Chunk) -> dict:
    """Convert a Chunk to a Qdrant payload dict."""
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "chunk_index": chunk.chunk_index,
        "section_heading": chunk.section_heading,
        "chunk_text": chunk.chunk_text,
        "content_hash": chunk.content_hash,
        "source_url": chunk.source_url,
        "source_domain": chunk.source_domain,
        "source_type": chunk.source_type.value,
        "title": chunk.title,
        "language": chunk.language,
        "document_date": chunk.document_date.isoformat() if chunk.document_date else None,
        "publication_date": chunk.publication_date.isoformat() if chunk.publication_date else None,
        "last_crawled": chunk.last_crawled.isoformat() if chunk.last_crawled else None,
        "audience": chunk.audience,
        "tax_category": chunk.tax_category,
        "document_type": chunk.document_type,
        "fiscal_codes": chunk.fiscal_codes,
        "taxonomies": chunk.taxonomies,
        "keywords": chunk.keywords,
        "fisconet_guid": chunk.fisconet_guid,
        "regionalisation": chunk.regionalisation,
    }


def upsert_chunks(
    client: QdrantClient,
    embedded_chunks: Sequence[EmbeddedChunk],
    batch_size: int = 100,
) -> int:
    """Upsert embedded chunks into Qdrant. Returns count of upserted points."""
    if not embedded_chunks:
        return 0

    points = []
    for i, ec in enumerate(embedded_chunks):
        points.append(
            PointStruct(
                id=i,  # Will be overridden below with proper IDs
                vector=ec.vector,
                payload=_chunk_to_payload(ec.chunk),
            )
        )

    # Use content_hash-based IDs via scroll+check or just upsert (idempotent by chunk_id)
    # For simplicity, use sequential IDs offset by existing count
    info = client.get_collection(COLLECTION_NAME)
    offset = info.points_count or 0

    total = 0
    for batch_start in range(0, len(points), batch_size):
        batch = points[batch_start : batch_start + batch_size]
        for j, p in enumerate(batch):
            p.id = offset + batch_start + j
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        total += len(batch)
        logger.info("Upserted batch: %d/%d points", total, len(points))

    return total


def delete_by_document_id(client: QdrantClient, document_id: str) -> None:
    """Delete all chunks for a given document (before re-ingestion)."""
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
    )
    logger.info("Deleted chunks for document_id=%s", document_id)


def search_similar(
    client: QdrantClient,
    query_vector: list[float],
    limit: int = 10,
    filters: dict | None = None,
) -> list[dict]:
    """Search for similar chunks. Returns list of {score, payload} dicts."""
    qdrant_filter = None
    if filters:
        conditions = []
        for key, value in filters.items():
            conditions.append(
                FieldCondition(key=key, match=MatchValue(value=value))
            )
        qdrant_filter = Filter(must=conditions)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        query_filter=qdrant_filter,
        with_payload=True,
    )
    return [
        {"score": hit.score, "payload": hit.payload}
        for hit in results.points
    ]
