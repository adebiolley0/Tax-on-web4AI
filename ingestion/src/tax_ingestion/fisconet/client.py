"""Fisconet+ REST API client — direct HTTP access to Belgian tax legislation DB."""

from __future__ import annotations

import base64
import logging
from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup

from tax_search.models import Document, SourceType

logger = logging.getLogger(__name__)

BASE_URL = "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public"
TIMEOUT = 30.0


def _parse_date(val: str | None) -> date | None:
    """Parse a date string from Fisconet API (various formats)."""
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(val.split("T")[0] if "T" in val else val, fmt.split("T")[0]).date()
        except ValueError:
            continue
    return None


def _parse_datetime(val: str | None) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _html_to_text(html: str) -> str:
    """Strip HTML tags and return plain text."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


async def fetch_document(guid: str, *, client: httpx.AsyncClient | None = None) -> Document | None:
    """Fetch a single Fisconet document by GUID and return a Document model."""
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=TIMEOUT)

    try:
        resp = await client.get(f"{BASE_URL}/document/{guid}")
        resp.raise_for_status()
        raw = resp.json()
        # API wraps in {data: {metadata: {...}, content: {...}}}
        envelope = raw.get("data", raw) if isinstance(raw, dict) else raw
        meta = envelope.get("metadata") or envelope

        # Decode base64 HTML content
        content_html = ""
        content_text = ""
        content_block = envelope.get("content") or {}
        raw_content = content_block.get("content", "")
        if raw_content:
            try:
                content_html = base64.b64decode(raw_content).decode("utf-8")
                content_text = _html_to_text(content_html)
            except Exception:
                logger.warning("Failed to decode content for %s", guid)

        # Extract metadata
        doc_type_obj = meta.get("documentType") or {}
        doc_type_label = ""
        if doc_type_obj.get("label"):
            labels = doc_type_obj["label"]
            doc_type_label = labels.get("fr") or labels.get("nl") or next(iter(labels.values()), "")

        taxonomies = []
        for tax in meta.get("taxonomies") or []:
            label = tax.get("label") or {}
            name = label.get("fr") or label.get("nl") or ""
            if name:
                taxonomies.append(name)

        keywords = []
        for kw in meta.get("keywords") or []:
            label = kw.get("label") or {}
            name = label.get("fr") or label.get("nl") or ""
            if name:
                keywords.append(name)

        related_guids = []
        for rel in meta.get("relatedDocuments") or []:
            if rel.get("guid"):
                related_guids.append(rel["guid"])

        language = meta.get("language", "fr").lower()
        title = meta.get("title", "")

        return Document(
            source_url=f"{BASE_URL}/document/{guid}",
            source_domain="minfin.fgov.be",
            source_type=SourceType.FISCONET_DOCUMENT,
            document_id=guid,
            title=title,
            language=language,
            content_text=content_text,
            content_html=content_html,
            document_date=_parse_date(meta.get("documentDate")),
            publication_date=_parse_date(meta.get("publicationDate")),
            effective_date=_parse_date(meta.get("effectiveDate")),
            last_modified=_parse_datetime(meta.get("lastModified")),
            document_type=doc_type_label,
            taxonomies=taxonomies,
            keywords=keywords,
            fisconet_guid=guid,
            related_document_guids=related_guids,
            regionalisation=str(meta.get("regionalisation")) if meta.get("regionalisation") else None,
        )
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching document %s: %s", guid, e)
        return None
    except Exception as e:
        logger.error("Error fetching document %s: %s", guid, e)
        return None
    finally:
        if own_client:
            await client.aclose()


async def search_documents(
    language: str = "fr",
    search_terms: str = "",
    page: int = 0,
    page_size: int = 100,
    document_types: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    *,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """Search Fisconet documents. Returns raw API response dict."""
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=TIMEOUT)

    try:
        body = {
            "searchCriteria": {
                "language": language,
                "searchTerms": search_terms,
                "orderBy": "RELEVANCE",
                "taxonomies": [],
                "documentTypes": document_types or [],
                "keywords": [],
            },
            "paginationParameters": {
                "currentPageNumber": page,
                "pageSize": page_size,
            },
        }
        if date_from or date_to:
            body["searchCriteria"]["documentDateRange"] = {
                "from": date_from or "",
                "to": date_to or "",
            }

        resp = await client.post(f"{BASE_URL}/search", json=body)
        resp.raise_for_status()
        raw = resp.json()
        # API wraps payload in a "data" envelope
        return raw.get("data", raw)
    finally:
        if own_client:
            await client.aclose()


async def get_navigation_tree(*, client: httpx.AsyncClient | None = None) -> dict:
    """Fetch the full Fisconet taxonomy navigation tree."""
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=TIMEOUT)

    try:
        resp = await client.get(f"{BASE_URL}/navigation/tree")
        resp.raise_for_status()
        return resp.json()
    finally:
        if own_client:
            await client.aclose()


async def get_monthly_changes(
    language: str = "fr",
    month: int = 1,
    year: int = 2026,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    """Fetch documents added/modified in a given month."""
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=TIMEOUT)

    try:
        resp = await client.get(
            f"{BASE_URL}/changes/searches",
            params={"language": language, "month": month, "year": year},
        )
        resp.raise_for_status()
        return resp.json()
    finally:
        if own_client:
            await client.aclose()
