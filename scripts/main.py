import asyncio
import sys
from pathlib import Path

# Allow `uv run python scripts/main.py` without installing the package
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from crawling.search import (  # noqa: E402
    _EXCLUDED_SELECTOR,
    _doc_markdown_generator,
)

from crawl4ai import (  # noqa: E402
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    UndetectedAdapter,
)
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy  # noqa: E402

TAX_ON_WEB_URL = "https://finances.belgium.be/fr/E-services/Tax-on-web"


async def crawl_tax_on_web(url: str = TAX_ON_WEB_URL) -> str:
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
        markdown_generator=_doc_markdown_generator(),
        remove_consent_popups=True,
        remove_overlay_elements=True,
        excluded_selector=_EXCLUDED_SELECTOR,
        css_selector="main#content",
        exclude_external_links=True,
        exclude_internal_links=True,
    )
    async with AsyncWebCrawler(
        crawler_strategy=crawler_strategy,
        config=browser_config,
    ) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        if not result.success:
            raise RuntimeError(result.error_message or "Crawl failed")
        md = result.markdown
        if isinstance(md, str):
            return md
        if md.fit_markdown and str(md.fit_markdown).strip():
            return str(md.fit_markdown).strip()
        return md.raw_markdown or ""


def main() -> None:
    text = asyncio.run(crawl_tax_on_web())
    print(text[:3000])


if __name__ == "__main__":
    main()
