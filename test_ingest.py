"""End-to-end test: ingest a single Fisconet document into in-memory Qdrant."""

import asyncio
import logging

from embedder import embed_texts
from qdrant_store import COLLECTION_NAME, ensure_collection, get_client, search_similar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def test_fisconet_single_doc():
    """Fetch one Fisconet document, chunk, embed, store, and query."""
    import httpx
    from chunker import chunk_document
    from embedder import embed_chunks
    from fisconet_client import fetch_document
    from qdrant_store import upsert_chunks

    # -- Step 1: Fetch a document from Fisconet API --
    logger.info("=== Step 1: Fetching a Fisconet document ===")

    # First, search for a document to get a GUID
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/search",
            json={
                "searchCriteria": {
                    "language": "fr",
                    "searchTerms": "impot des personnes physiques",
                    "orderBy": "RELEVANCE",
                    "taxonomies": [],
                    "documentTypes": [],
                    "keywords": [],
                },
                "paginationParameters": {
                    "currentPageNumber": 0,
                    "pageSize": 3,
                },
            },
        )
        resp.raise_for_status()
        search_data = resp.json()

    # Extract first result GUID — API wraps in data.pageContents
    data_block = search_data.get("data") or search_data
    results = (
        data_block.get("pageContents")
        or data_block.get("results")
        or data_block.get("items")
        or []
    )
    if not results:
        logger.info("Search response keys: %s", list(search_data.keys()))
        logger.info("data keys: %s", list(data_block.keys()) if isinstance(data_block, dict) else "N/A")
        raise RuntimeError("No search results returned")

    first = results[0]
    guid = first.get("guid")
    logger.info("Found document: guid=%s, title=%s", guid, first.get("title", "?")[:80])

    # -- Step 2: Fetch full document --
    logger.info("=== Step 2: Fetching full document content ===")
    async with httpx.AsyncClient(timeout=30.0) as client:
        doc = await fetch_document(guid, client=client)

    if not doc:
        raise RuntimeError(f"Failed to fetch document {guid}")

    logger.info("Document loaded:")
    logger.info("  Title: %s", doc.title[:100])
    logger.info("  Type: %s", doc.document_type)
    logger.info("  Date: %s", doc.document_date)
    logger.info("  Language: %s", doc.language)
    logger.info("  Content length: %d chars", len(doc.content_text))
    logger.info("  Taxonomies: %s", doc.taxonomies[:5])
    logger.info("  Keywords: %s", doc.keywords[:5])

    # -- Step 3: Chunk --
    logger.info("=== Step 3: Chunking document ===")
    chunks = chunk_document(doc)
    logger.info("Created %d chunks", len(chunks))
    for i, c in enumerate(chunks[:3]):
        logger.info("  Chunk %d: %d chars, heading=%s", i, len(c.chunk_text), c.section_heading)

    # -- Step 4: Embed --
    logger.info("=== Step 4: Generating embeddings ===")
    embedded = embed_chunks(chunks)
    logger.info("Generated %d embeddings, dim=%d", len(embedded), len(embedded[0].vector))

    # -- Step 5: Store in Qdrant (in-memory) --
    logger.info("=== Step 5: Storing in Qdrant (in-memory) ===")
    qclient = get_client(in_memory=True)
    ensure_collection(qclient)
    count = upsert_chunks(qclient, embedded)
    logger.info("Stored %d points", count)

    # -- Step 6: Verify with a semantic search --
    logger.info("=== Step 6: Semantic search test ===")
    query = "impot sur le revenu des personnes physiques en Belgique"
    query_vec = embed_texts([query])[0]
    results = search_similar(qclient, query_vec, limit=3)

    logger.info("Search query: %r", query)
    for i, hit in enumerate(results):
        logger.info(
            "  Result %d: score=%.4f, title=%s",
            i,
            hit["score"],
            hit["payload"].get("title", "?")[:80],
        )
        logger.info(
            "    Text preview: %s...",
            hit["payload"].get("chunk_text", "")[:150],
        )

    # -- Summary --
    info = qclient.get_collection(COLLECTION_NAME)
    logger.info("=== Summary ===")
    logger.info("Collection: %s", COLLECTION_NAME)
    logger.info("Total points: %d", info.points_count)
    logger.info("Vector size: %d", info.config.params.vectors.size)
    logger.info("TEST PASSED")


if __name__ == "__main__":
    asyncio.run(test_fisconet_single_doc())
