"""Ingestion orchestrator — populates Qdrant with Belgian tax documents."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

import httpx

from storage.chunker import chunk_document
from crawling.content_extractor import document_from_crawl_result, load_sitemap_metadata
from storage.embedder import embed_chunks
from fisconet.client import fetch_document, search_documents
from models import Document
from storage.qdrant_store import ensure_collection, get_client, search_similar, upsert_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Drupal ingestion (fin.belgium.be / finances.belgium.be)
# ---------------------------------------------------------------------------

async def ingest_drupal_url(url: str, sitemap_meta: dict | None = None) -> Document | None:
    """Ingest a single Drupal page using the existing crawl results."""
    # Use pre-fetched results if available
    results_path = Path("out/fetch_sitemap_results.json")
    if results_path.exists():
        data = json.loads(results_path.read_text(encoding="utf-8"))
        for row in data.get("results", []):
            if row.get("url") == url and row.get("success"):
                md = row.get("markdown_excerpt", "")
                return document_from_crawl_result(
                    url=url,
                    markdown_content=md,
                    sitemap_meta=sitemap_meta,
                )
    logger.warning("No cached result for %s — skipping (run fetch_all_sitemap_urls first)", url)
    return None


async def ingest_drupal_sites() -> list[Document]:
    """Ingest all 123 Drupal pages from cached crawl results."""
    sitemap = load_sitemap_metadata()
    docs = []
    for url, meta in sitemap.items():
        doc = await ingest_drupal_url(url, sitemap_meta=meta)
        if doc and doc.content_text:
            docs.append(doc)
    logger.info("Loaded %d Drupal documents", len(docs))
    return docs


# ---------------------------------------------------------------------------
# Fisconet ingestion
# ---------------------------------------------------------------------------

async def ingest_fisconet_document(guid: str, client: httpx.AsyncClient) -> Document | None:
    """Ingest a single Fisconet document by GUID."""
    return await fetch_document(guid, client=client)


async def ingest_fisconet_page(
    page: int = 0,
    page_size: int = 10,
    language: str = "fr",
    client: httpx.AsyncClient | None = None,
) -> list[Document]:
    """Ingest a page of Fisconet search results."""
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=30.0)

    try:
        result = await search_documents(
            language=language,
            page=page,
            page_size=page_size,
            client=client,
        )
        items = (
            result.get("pageContents")
            or result.get("results")
            or result.get("items")
            or []
        )
        if not items:
            logger.warning("No results in search response for page %d", page)
            return []

        docs = []
        for item in items:
            guid = item.get("guid")
            if not guid:
                continue
            doc = await ingest_fisconet_document(guid, client=client)
            if doc and doc.content_text:
                docs.append(doc)

        logger.info("Fetched %d documents from Fisconet page %d", len(docs), page)
        return docs
    finally:
        if own_client:
            await client.aclose()


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

async def ingest_and_store(
    docs: list[Document],
    qdrant_client=None,
) -> int:
    """Chunk, embed, and store documents in Qdrant. Returns point count."""
    if not docs:
        return 0

    # Chunk
    all_chunks = []
    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    logger.info("Created %d chunks from %d documents", len(all_chunks), len(docs))

    if not all_chunks:
        return 0

    # Embed
    embedded = embed_chunks(all_chunks)
    logger.info("Generated %d embeddings", len(embedded))

    # Store
    qclient = qdrant_client or get_client()
    ensure_collection(qclient)
    count = upsert_chunks(qclient, embedded)
    logger.info("Stored %d points in Qdrant", count)
    return count


async def ingest_single_drupal(url: str) -> int:
    """Ingest a single Drupal URL end-to-end. For testing."""
    sitemap = load_sitemap_metadata()
    meta = sitemap.get(url)
    doc = await ingest_drupal_url(url, sitemap_meta=meta)
    if not doc:
        logger.error("Failed to load document for %s", url)
        return 0
    return await ingest_and_store([doc])


async def ingest_single_fisconet(guid: str) -> int:
    """Ingest a single Fisconet document end-to-end. For testing."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        doc = await ingest_fisconet_document(guid, client=client)
    if not doc:
        logger.error("Failed to load Fisconet document %s", guid)
        return 0
    return await ingest_and_store([doc])


async def main():
    parser = argparse.ArgumentParser(description="Belgian tax document ingestion")
    parser.add_argument(
        "--source",
        choices=["drupal", "fisconet", "all"],
        default="all",
        help="Which source to ingest",
    )
    parser.add_argument(
        "--test-url",
        type=str,
        help="Ingest a single Drupal URL (for testing)",
    )
    parser.add_argument(
        "--test-guid",
        type=str,
        help="Ingest a single Fisconet GUID (for testing)",
    )
    parser.add_argument(
        "--fisconet-pages",
        type=int,
        default=1,
        help="Number of Fisconet search pages to ingest (default: 1)",
    )
    args = parser.parse_args()

    if args.test_url:
        count = await ingest_single_drupal(args.test_url)
        logger.info("Test ingestion complete: %d points stored", count)
        return

    if args.test_guid:
        count = await ingest_single_fisconet(args.test_guid)
        logger.info("Test ingestion complete: %d points stored", count)
        return

    total = 0
    if args.source in ("drupal", "all"):
        docs = await ingest_drupal_sites()
        count = await ingest_and_store(docs)
        total += count

    if args.source in ("fisconet", "all"):
        async with httpx.AsyncClient(timeout=30.0) as client:
            for page in range(args.fisconet_pages):
                docs = await ingest_fisconet_page(page=page, client=client)
                count = await ingest_and_store(docs)
                total += count

    logger.info("Ingestion complete: %d total points stored", total)


if __name__ == "__main__":
    asyncio.run(main())
