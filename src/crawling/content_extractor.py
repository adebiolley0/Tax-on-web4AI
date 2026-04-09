"""Content extraction for Drupal pages (fin.belgium.be / finances.belgium.be)."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

from models import Document, SourceType

logger = logging.getLogger(__name__)

# Fiscal code patterns commonly found in Belgian tax text
FISCAL_CODE_PATTERNS = [
    re.compile(r"art\.?\s*(\d+[\w/]*)\s+CIR\s*92", re.IGNORECASE),
    re.compile(r"art\.?\s*(\d+[\w/]*)\s+C\.?TVA", re.IGNORECASE),
    re.compile(r"art\.?\s*(\d+[\w/]*)\s+C\.?Enr\.?", re.IGNORECASE),
    re.compile(r"art\.?\s*(\d+[\w/]*)\s+C\.?Succ\.?", re.IGNORECASE),
    re.compile(r"art\.?\s*(\d+[\w/]*)\s+AR/?CIR\s*92", re.IGNORECASE),
    re.compile(r"art\.?\s*(\d+[\w/]*)\s+C\.?Div\.?", re.IGNORECASE),
]


def extract_fiscal_codes(text: str) -> list[str]:
    """Extract fiscal code references (e.g., 'art. 7 CIR 92') from text."""
    codes = set()
    for pattern in FISCAL_CODE_PATTERNS:
        for match in pattern.finditer(text):
            codes.add(match.group(0).strip())
    return sorted(codes)


def detect_language(url: str) -> str:
    """Detect language from URL path."""
    if "/nl/" in url:
        return "nl"
    if "/de/" in url:
        return "de"
    if "/en/" in url:
        return "en"
    return "fr"


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    from urllib.parse import urlparse
    return urlparse(url).netloc


def document_from_crawl_result(
    url: str,
    markdown_content: str,
    html_content: str = "",
    sitemap_meta: dict | None = None,
) -> Document:
    """Build a Document from a crawl4ai result and optional sitemap metadata."""
    meta = sitemap_meta or {}

    title = meta.get("title", "")
    if not title and html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

    # Clean up markdown content
    content_text = markdown_content.strip() if markdown_content else ""

    # Extract fiscal codes from the content
    fiscal_codes = extract_fiscal_codes(content_text)

    return Document(
        source_url=url,
        source_domain=_extract_domain(url),
        source_type=SourceType.DRUPAL_PAGE,
        document_id=url,
        title=title,
        language=detect_language(url),
        content_text=content_text,
        content_html=html_content,
        audience=meta.get("audience"),
        tax_category=meta.get("category"),
        document_type="page_info",
        fiscal_codes=fiscal_codes,
        last_crawled=datetime.utcnow(),
    )


def load_sitemap_metadata(
    json_path: str | Path = "extracted_sitemap.json",
) -> dict[str, dict]:
    """Load URL→metadata mapping from the sitemap JSON."""
    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("endpoints", {})
