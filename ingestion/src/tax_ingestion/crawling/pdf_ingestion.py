"""PDF ingestion for Belgian tax documents.

Downloads PDFs from:
  1. Fisconet+ REST API  (GET /pdf?id={guid}&language={lang})
  2. Drupal pages on fin.belgium.be / finances.belgium.be (embedded PDF links)

Converts each PDF to Markdown using pymupdf4llm, and optionally keeps the
raw PDF on disk for archival.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import pymupdf
import pymupdf4llm
from bs4 import BeautifulSoup

from tax_search.models import Document, SourceType

logger = logging.getLogger(__name__)

FISCONET_BASE = "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public"
DEFAULT_PDF_DIR = Path("out/pdfs")
DEFAULT_MD_DIR = Path("out/pdfs_md")
TIMEOUT = 60.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_dirs(*dirs: Path) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str, max_len: int = 120) -> str:
    """Sanitize a string for use as a filename."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = re.sub(r"_+", "_", name).strip("_. ")
    return name[:max_len] if name else "unnamed"


# ---------------------------------------------------------------------------
# PDF download
# ---------------------------------------------------------------------------

async def download_fisconet_pdf(
    guid: str,
    language: str = "fr",
    *,
    out_dir: Path = DEFAULT_PDF_DIR,
    client: httpx.AsyncClient | None = None,
) -> Path | None:
    """Download a PDF from the Fisconet+ API and save to *out_dir*.

    Returns the local file path on success, ``None`` on failure.
    """
    _ensure_dirs(out_dir)
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=TIMEOUT)

    try:
        resp = await client.get(
            f"{FISCONET_BASE}/pdf",
            params={"id": guid, "language": language},
        )
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if "pdf" not in content_type and len(resp.content) < 256:
            logger.warning("Fisconet PDF response for %s is not a PDF (content-type: %s)", guid, content_type)
            return None

        filename = f"fisconet_{language}_{guid}.pdf"
        dest = out_dir / filename
        dest.write_bytes(resp.content)
        logger.info("Downloaded Fisconet PDF: %s (%d bytes)", dest, len(resp.content))
        return dest
    except httpx.HTTPStatusError as exc:
        logger.error("HTTP %s downloading Fisconet PDF %s: %s", exc.response.status_code, guid, exc)
        return None
    except Exception as exc:
        logger.error("Error downloading Fisconet PDF %s: %s", guid, exc)
        return None
    finally:
        if own_client:
            await client.aclose()


async def download_pdf_from_url(
    url: str,
    *,
    out_dir: Path = DEFAULT_PDF_DIR,
    client: httpx.AsyncClient | None = None,
) -> Path | None:
    """Download a PDF from a direct URL and save to *out_dir*.

    Returns the local file path on success, ``None`` on failure.
    """
    _ensure_dirs(out_dir)
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True)

    try:
        resp = await client.get(url)
        resp.raise_for_status()

        # Derive filename from URL path or content-disposition
        parsed = urlparse(url)
        url_filename = Path(parsed.path).name
        if not url_filename.lower().endswith(".pdf"):
            url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
            url_filename = f"drupal_{url_hash}.pdf"

        dest = out_dir / _safe_filename(url_filename)
        dest.write_bytes(resp.content)
        logger.info("Downloaded PDF: %s (%d bytes) from %s", dest, len(resp.content), url)
        return dest
    except Exception as exc:
        logger.error("Error downloading PDF from %s: %s", url, exc)
        return None
    finally:
        if own_client:
            await client.aclose()


# ---------------------------------------------------------------------------
# PDF link discovery from Drupal HTML
# ---------------------------------------------------------------------------

def discover_pdf_links(html: str, base_url: str = "") -> list[str]:
    """Extract PDF download URLs from a Drupal page's HTML.

    Looks for ``<a>`` tags whose ``href`` ends in ``.pdf`` or contains
    ``/sites/default/files/`` (common Drupal file path).
    """
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    seen: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href: str = a_tag["href"]
        if not href:
            continue
        # Match .pdf links or Drupal file paths
        if href.lower().endswith(".pdf") or "/sites/default/files/" in href:
            full_url = urljoin(base_url, href) if base_url else href
            if full_url not in seen:
                seen.add(full_url)
                links.append(full_url)

    return links


# ---------------------------------------------------------------------------
# PDF → Markdown conversion
# ---------------------------------------------------------------------------

def pdf_to_markdown(
    pdf_path: str | Path,
    *,
    out_dir: Path = DEFAULT_MD_DIR,
    save_md: bool = True,
) -> str:
    """Convert a local PDF file to Markdown using pymupdf4llm.

    Returns the Markdown text. If *save_md* is True, also writes a ``.md``
    file next to the PDF (in *out_dir*).
    """
    pdf_path = Path(pdf_path)
    md_text: str = pymupdf4llm.to_markdown(str(pdf_path))

    if save_md:
        _ensure_dirs(out_dir)
        md_filename = pdf_path.stem + ".md"
        md_dest = out_dir / md_filename
        md_dest.write_text(md_text, encoding="utf-8")
        logger.info("Wrote Markdown: %s (%d chars)", md_dest, len(md_text))

    return md_text


def pdf_bytes_to_markdown(pdf_bytes: bytes, name: str = "document") -> str:
    """Convert in-memory PDF bytes to Markdown without saving to disk first."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    md_text: str = pymupdf4llm.to_markdown(doc)
    doc.close()
    return md_text


# ---------------------------------------------------------------------------
# High-level ingestion functions
# ---------------------------------------------------------------------------

async def ingest_fisconet_pdf(
    guid: str,
    language: str = "fr",
    *,
    out_dir: Path = DEFAULT_PDF_DIR,
    md_dir: Path = DEFAULT_MD_DIR,
    client: httpx.AsyncClient | None = None,
) -> Document | None:
    """Download a Fisconet PDF, convert to Markdown, and return a Document.

    The raw PDF is kept on disk at *out_dir*; the Markdown is saved to *md_dir*.
    """
    pdf_path = await download_fisconet_pdf(
        guid, language, out_dir=out_dir, client=client,
    )
    if pdf_path is None:
        return None

    md_text = pdf_to_markdown(pdf_path, out_dir=md_dir)
    if not md_text.strip():
        logger.warning("Empty Markdown from Fisconet PDF %s", guid)
        return None

    return Document(
        source_url=f"{FISCONET_BASE}/pdf?id={guid}&language={language}",
        source_domain="minfin.fgov.be",
        source_type=SourceType.PDF,
        document_id=f"fisconet-pdf-{guid}",
        title=f"Fisconet PDF {guid}",
        language=language,
        content_text=md_text,
    )


async def ingest_drupal_pdfs(
    page_url: str,
    page_html: str,
    *,
    out_dir: Path = DEFAULT_PDF_DIR,
    md_dir: Path = DEFAULT_MD_DIR,
    client: httpx.AsyncClient | None = None,
) -> list[Document]:
    """Discover PDF links on a Drupal page, download each, and return Documents.

    The raw PDFs are kept on disk.
    """
    pdf_links = discover_pdf_links(page_html, base_url=page_url)
    if not pdf_links:
        return []

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True)

    docs: list[Document] = []
    try:
        for pdf_url in pdf_links:
            pdf_path = await download_pdf_from_url(
                pdf_url, out_dir=out_dir, client=client,
            )
            if pdf_path is None:
                continue

            md_text = pdf_to_markdown(pdf_path, out_dir=md_dir)
            if not md_text.strip():
                logger.warning("Empty Markdown from %s", pdf_url)
                continue

            docs.append(Document(
                source_url=pdf_url,
                source_domain=urlparse(page_url).netloc,
                source_type=SourceType.PDF,
                document_id=pdf_url,
                title=Path(urlparse(pdf_url).path).stem,
                language="fr",
                content_text=md_text,
            ))
    finally:
        if own_client:
            await client.aclose()

    logger.info("Ingested %d PDFs from %s", len(docs), page_url)
    return docs


async def fetch_library_pdf_guids(
    language: str = "fr",
    *,
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    """Fetch the curated library publications list from Fisconet+.

    Returns a list of dicts with ``id`` (guid) and ``title``.
    """
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=TIMEOUT)

    try:
        resp = await client.get(
            f"{FISCONET_BASE}/library/documents",
            params={"language": language},
        )
        resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("data", data)
        if isinstance(items, list):
            return [{"id": item.get("id"), "title": item.get("title", "")} for item in items if item.get("id")]
        return []
    except Exception as exc:
        logger.error("Error fetching library documents: %s", exc)
        return []
    finally:
        if own_client:
            await client.aclose()
