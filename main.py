import asyncio

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    UndetectedAdapter,
)
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

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
        return md.raw_markdown or ""


def main() -> None:
    text = asyncio.run(crawl_tax_on_web())
    print(text[:3000])


if __name__ == "__main__":
    main()
