"""MCP server exposing Belgian SPF Finances search and URL fetch tools."""

import asyncio
import json

from fastmcp import FastMCP

from search import SearchResponse, fetch_urls, search as site_search

mcp = FastMCP("Belgian Tax SPF")

_fetch_cache: dict[str, dict] = {}
_fetch_lock = asyncio.Lock()


@mcp.tool(name="search")
async def search_tool(query: str) -> str:
    """Search the Belgian SPF Finances website (keyword search on finances.belgium.be)."""
    result: SearchResponse = await site_search(query)
    return json.dumps(result.model_dump(), ensure_ascii=False)


@mcp.tool(name="fetch")
async def fetch_tool(urls: list[str]) -> str:
    """Fetch pages from the Belgian tax / SPF Finances site by URL (crawl4ai)."""
    async with _fetch_lock:
        to_fetch: list[str] = []
        seen: set[str] = set()
        for u in urls:
            if u in _fetch_cache:
                continue
            if u not in seen:
                seen.add(u)
                to_fetch.append(u)

    fetched_map: dict[str, dict] = {}
    if to_fetch:
        rows = await fetch_urls(to_fetch)
        for r in rows:
            fetched_map[r.url] = r.model_dump()
        async with _fetch_lock:
            for r in rows:
                if r.success:
                    _fetch_cache[r.url] = r.model_dump()

    async with _fetch_lock:
        payload = [
            _fetch_cache[u] if u in _fetch_cache else fetched_map[u] for u in urls
        ]
    return json.dumps(payload, ensure_ascii=False)
