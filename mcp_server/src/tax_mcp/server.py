"""MCP server exposing Belgian tax semantic search (Qdrant) and SPF Finances scraping."""

import json

from fastmcp import FastMCP

from tax_search.embedder import embed_texts
from tax_search.qdrant_store import ensure_collection, get_client, search_similar

from tax_mcp.scraping import SearchResponse, fetch_urls, search as site_search

mcp = FastMCP("Belgian Tax SPF")


@mcp.tool(name="search")
async def search_tool(query: str) -> str:
    """Search the Belgian SPF Finances website (keyword search on finances.belgium.be)."""
    result: SearchResponse = await site_search(query)
    return json.dumps(result.model_dump(), ensure_ascii=False)


@mcp.tool(name="fetch")
async def fetch_tool(urls: list[str]) -> str:
    """Fetch pages from the Belgian tax / SPF Finances site by URL (crawl4ai)."""
    rows = await fetch_urls(urls)
    payload = [r.model_dump() for r in rows]
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool(name="semantic_search")
async def semantic_search_tool(
    query: str,
    tax_category: str | None = None,
    audience: str | None = None,
    document_type: str | None = None,
    language: str = "fr",
    limit: int = 10,
) -> str:
    """Semantic search over Belgian tax regulation documents stored in Qdrant.

    Args:
        query: Natural-language search query (e.g. "deduction frais professionnels").
        tax_category: Optional filter by tax category (declaration, revenus, tva, isoc, habitation, ...).
        audience: Optional filter by audience (particuliers, entreprises, independants, asbl, tous).
        document_type: Optional filter by document type (Circulaires, Code et legislation, ...).
        language: Language filter (default: "fr").
        limit: Max results to return (default: 10).

    Returns:
        JSON array of search hits, each with score, title, chunk_text, and metadata.
    """
    query_vector = embed_texts([query])[0]

    filters: dict[str, str] = {"language": language}
    if tax_category:
        filters["tax_category"] = tax_category
    if audience:
        filters["audience"] = audience
    if document_type:
        filters["document_type"] = document_type

    client = get_client()
    ensure_collection(client)
    hits = search_similar(client, query_vector, limit=limit, filters=filters)

    results = []
    for hit in hits:
        payload = hit["payload"]
        results.append({
            "score": round(hit["score"], 4),
            "title": payload.get("title"),
            "chunk_text": payload.get("chunk_text"),
            "source_url": payload.get("source_url"),
            "document_type": payload.get("document_type"),
            "document_date": payload.get("document_date"),
            "tax_category": payload.get("tax_category"),
            "audience": payload.get("audience"),
            "taxonomies": payload.get("taxonomies"),
            "keywords": payload.get("keywords"),
            "fiscal_codes": payload.get("fiscal_codes"),
        })

    return json.dumps(results, ensure_ascii=False)
