"""SPF Finances site search via crawl4ai: ``/fr/search?keywords=...`` (+ ``page``)."""

import asyncio
import re
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    UndetectedAdapter,
)
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from pydantic import BaseModel, Field

BASE_URL = "https://finances.belgium.be"
SEARCH_PATH = "/fr/search"


class SearchHit(BaseModel):
    """One row from the SPF Finances site search results."""

    title: str
    url: str
    breadcrumbs: list[str] = Field(default_factory=list)
    excerpt: str | None = None


class SearchResponse(BaseModel):
    """Structured search outcome for a single requested page."""

    query: str
    page: int
    search_url: str
    total_hits: int | None = None
    result_range_label: str | None = None
    results: list[SearchHit] = Field(default_factory=list)


def _build_search_url(query: str, page: int) -> str:
    q = quote(query, safe="")
    if page <= 0:
        return f"{BASE_URL}{SEARCH_PATH}?keywords={q}"
    return f"{BASE_URL}{SEARCH_PATH}?keywords={q}&page={page}"


def _absolute_url(href: str) -> str:
    return urljoin(BASE_URL + "/", href.lstrip("/"))


def parse_search_html(html: str, *, query: str, page: int, search_url: str) -> SearchResponse:
    soup = BeautifulSoup(html, "lxml")
    section = soup.select_one("section.view-id-search")
    if section is None:
        return SearchResponse(
            query=query,
            page=page,
            search_url=search_url,
            results=[],
        )

    total_hits: int | None = None
    header_h2 = section.find("header")
    if header_h2:
        h2 = header_h2.find("h2")
        if h2 and h2.string:
            m = re.search(r"(\d+)\s+résultat", h2.string)
            if m:
                total_hits = int(m.group(1))
        span = header_h2.find("span", class_="result")
        range_label = span.get_text(strip=True) if span else None
    else:
        range_label = None

    hits: list[SearchHit] = []
    for row in section.select("div[class^='count-']"):
        title_a = row.select_one(".views-field-title a")
        if not title_a or not title_a.get("href"):
            continue
        title = title_a.get_text(strip=True)
        url = _absolute_url(title_a["href"])
        crumbs = [
            li.get_text(strip=True)
            for li in row.select(".views-field-field-section-parents-all li")
        ]
        excerpt_el = row.select_one(".views-field-search-api-excerpt .field-content")
        excerpt = excerpt_el.get_text(strip=True) if excerpt_el else None
        if excerpt == "":
            excerpt = None
        hits.append(
            SearchHit(title=title, url=url, breadcrumbs=crumbs, excerpt=excerpt)
        )

    return SearchResponse(
        query=query,
        page=page,
        search_url=search_url,
        total_hits=total_hits,
        result_range_label=range_label,
        results=hits,
    )


async def search(query: str, page: int = 0) -> SearchResponse:
    """Run a keyword search on the French SPF Finances search page using crawl4ai.

    Uses the same browser stack as ``main.py`` (UndetectedAdapter, non-headless,
    locale fr-BE). Pagination follows the site's ``page`` query parameter
    (0 = first page, 1 = second, ...).
    """
    search_url = _build_search_url(query, page)
    browser_config = BrowserConfig(headless=False, verbose=False)
    undetected_adapter = UndetectedAdapter()
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=undetected_adapter,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=120_000,
        wait_until="networkidle",
        delay_before_return_html=12.0,
        locale="fr-BE",
        timezone_id="Europe/Brussels",
    )
    async with AsyncWebCrawler(
        crawler_strategy=crawler_strategy,
        config=browser_config,
    ) as crawler:
        result = await crawler.arun(url=search_url, config=run_config)
        if not result.success:
            raise RuntimeError(result.error_message or "Crawl failed")
        return parse_search_html(
            result.html,
            query=query,
            page=page,
            search_url=search_url,
        )
