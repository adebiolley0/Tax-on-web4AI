"""SPF Finances site search via crawl4ai: ``/fr/search?keywords=...`` (+ ``page``)."""

import asyncio
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
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


class FetchUrlResult(BaseModel):
    """Outcome of crawling one documentation URL."""

    url: str
    success: bool
    status_code: int | None = None
    redirected_url: str | None = None
    error_message: str | None = None
    markdown_excerpt: str | None = None
    html_length: int = 0


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


def _doc_browser_config(*, user_data_dir: str) -> BrowserConfig:
    # Persistent profile + fin.belgium.be warm-up clears Akamai/TSPD for finances.belgium.be.
    os.environ.setdefault("DISPLAY", ":1")
    return BrowserConfig(
        headless=False,
        verbose=False,
        use_persistent_context=True,
        user_data_dir=user_data_dir,
    )


_WARM_FIN_URL = "https://fin.belgium.be/fr/particuliers"


async def _session_warmup(crawler: AsyncWebCrawler) -> None:
    warm_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=120_000,
        wait_until="networkidle",
        delay_before_return_html=8.0,
        locale="fr-BE",
        timezone_id="Europe/Brussels",
        max_retries=0,
        verbose=False,
    )
    await crawler.arun(url=_WARM_FIN_URL, config=warm_cfg)


def _doc_primary_fetch_config() -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=120_000,
        wait_until="networkidle",
        delay_before_return_html=8.0,
        locale="fr-BE",
        timezone_id="Europe/Brussels",
        max_retries=0,
        verbose=False,
    )


def _is_waf_interstitial_html(html: str) -> bool:
    """Akamai CAPTCHA shell vs real content (Drupal, MyMinfin redirect, etc.)."""
    if not html.strip():
        return True
    low = html.lower()
    if "testing whether you are a human visitor" in low:
        return True
    if "what code is in the image" in low and "human visitor" in low:
        return True
    if 'id="main-content"' in low or "id='main-content'" in low:
        return False
    if 'name="generator"' in low and "drupal" in low:
        return False
    if "myminfin" in low or "minfin.fgov.be" in low:
        return False
    if len(html) > 25_000 and "human visitor" not in low:
        return False
    return True


def _markdown_excerpt(result) -> str | None:
    md = result.markdown
    if md is None:
        return None
    text = md if isinstance(md, str) else (md.raw_markdown or "")
    text = text.strip()
    if not text:
        return None
    return text[:2000] if len(text) > 2000 else text


async def fetch_url(url: str, *, crawler: AsyncWebCrawler | None = None) -> FetchUrlResult:
    """Fetch one Belgian tax documentation URL with crawl4ai.

    Uses a persistent Chromium profile, ``DISPLAY`` (default ``:1``), a warm-up visit
    to fin.belgium.be, and retries when Akamai serves a CAPTCHA interstitial.

    When ``crawler`` is omitted, a short-lived browser session is opened and closed.
    For many URLs, use :func:`fetch_all_sitemap_urls` so one session is reused.
    """
    if crawler is not None:
        last_err: str | None = None
        last_status: int | None = None
        last_redirect: str | None = None
        last_html_len = 0
        cfg = _doc_primary_fetch_config()
        max_attempts = 22 if "finances.belgium.be" in url else 6
        for attempt in range(max_attempts):
            if "finances.belgium.be" in url and attempt > 0:
                await _session_warmup(crawler)
            result = await crawler.arun(url=url, config=cfg)
            html = result.html or ""
            last_html_len = len(html)
            last_status = result.status_code
            last_redirect = result.redirected_url
            if not result.success:
                last_err = result.error_message or "Crawl failed"
                await asyncio.sleep(2.0)
                continue
            if _is_waf_interstitial_html(html):
                last_err = "WAF interstitial (no Drupal content yet)"
                await asyncio.sleep(4.0)
                continue
            return FetchUrlResult(
                url=url,
                success=True,
                status_code=result.status_code,
                redirected_url=result.redirected_url,
                markdown_excerpt=_markdown_excerpt(result),
                html_length=len(html),
            )
        return FetchUrlResult(
            url=url,
            success=False,
            status_code=last_status,
            redirected_url=last_redirect,
            error_message=last_err or "Crawl failed",
            html_length=last_html_len,
        )

    user_data_dir = tempfile.mkdtemp(prefix="crawl4ai-tax-one-")
    try:
        browser_config = _doc_browser_config(user_data_dir=user_data_dir)
        crawler_strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_config)
        async with AsyncWebCrawler(
            crawler_strategy=crawler_strategy,
            config=browser_config,
        ) as owned:
            await _session_warmup(owned)
            return await fetch_url(url, crawler=owned)
    finally:
        shutil.rmtree(user_data_dir, ignore_errors=True)


async def fetch_all_sitemap_urls(
    json_path: str | Path = "extracted_sitemap.json",
) -> list[FetchUrlResult]:
    """Load endpoint URLs from ``extracted_sitemap.json`` and fetch each with one shared crawler."""
    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    endpoints = data.get("endpoints") or {}
    urls = sorted(endpoints.keys())

    user_data_dir = tempfile.mkdtemp(prefix="crawl4ai-tax-batch-")
    try:
        browser_config = _doc_browser_config(user_data_dir=user_data_dir)
        crawler_strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_config)
        results: list[FetchUrlResult] = []
        async with AsyncWebCrawler(
            crawler_strategy=crawler_strategy,
            config=browser_config,
        ) as crawler:
            await _session_warmup(crawler)
            for u in urls:
                results.append(await fetch_url(u, crawler=crawler))
            for i, row in enumerate(results):
                if row.success:
                    continue
                results[i] = await fetch_url(urls[i], crawler=crawler)
        return results
    finally:
        shutil.rmtree(user_data_dir, ignore_errors=True)


async def test_fetch_all_sitemap_urls(
    json_path: str | Path = "extracted_sitemap.json",
    out_dir: str | Path = "out",
    out_file: str = "fetch_sitemap_results.json",
) -> Path:
    """Run :func:`fetch_all_sitemap_urls`, write aggregated results to ``out/``."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    dest = out_path / out_file
    rows = await fetch_all_sitemap_urls(json_path=json_path)
    payload = {
        "source_json": str(Path(json_path).resolve()),
        "total": len(rows),
        "success_count": sum(1 for r in rows if r.success),
        "failure_count": sum(1 for r in rows if not r.success),
        "results": [r.model_dump() for r in rows],
    }
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


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
