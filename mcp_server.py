"""MCP server exposing Belgian SPF Finances search and URL fetch tools."""

import json

from fastmcp import FastMCP

from search import SearchResponse, fetch_urls, search as site_search

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
