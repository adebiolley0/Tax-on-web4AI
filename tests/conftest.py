"""Shared pytest fixtures for the Belgian tax ingestion pipeline."""

from __future__ import annotations

import base64
import json
from datetime import date, datetime
from pathlib import Path

import pytest

from chunker import chunk_document
from embedder import embed_chunks
from models import Document, EmbeddedChunk, SourceType
from qdrant_store import COLLECTION_NAME, ensure_collection, get_client, upsert_chunks

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixture: raw Fisconet API responses loaded from JSON
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def raw_fisconet_docs() -> list[dict]:
    """Load the 5 canned Fisconet API document responses."""
    path = FIXTURES_DIR / "fisconet_5docs.json"
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixture: parsed Document models from the canned data
# ---------------------------------------------------------------------------

def _parse_fisconet_doc(raw: dict) -> Document:
    """Convert a raw Fisconet API response dict into a Document model."""
    from fisconet_client import _html_to_text, _parse_date, _parse_datetime

    meta = raw.get("metadata") or raw
    content_block = raw.get("content") or {}
    raw_content = content_block.get("content", "")

    content_html = ""
    content_text = ""
    if raw_content:
        content_html = base64.b64decode(raw_content).decode("utf-8")
        content_text = _html_to_text(content_html)

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

    guid = meta.get("guid", "unknown")
    language = meta.get("language", "fr").lower()

    return Document(
        source_url=f"https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public/document/{guid}",
        source_domain="minfin.fgov.be",
        source_type=SourceType.FISCONET_DOCUMENT,
        document_id=guid,
        title=meta.get("title", ""),
        language=language,
        content_text=content_text,
        content_html=content_html,
        document_date=_parse_date(meta.get("documentDate")),
        publication_date=_parse_date(meta.get("publicationDate")),
        last_modified=_parse_datetime(meta.get("lastModified")),
        document_type=doc_type_label,
        taxonomies=taxonomies,
        keywords=keywords,
        fisconet_guid=guid,
    )


@pytest.fixture(scope="session")
def parsed_documents(raw_fisconet_docs) -> list[Document]:
    """Parse the 5 canned API responses into Document models."""
    docs = [_parse_fisconet_doc(raw) for raw in raw_fisconet_docs]
    # Filter out any docs with empty content
    return [d for d in docs if d.content_text.strip()]


# ---------------------------------------------------------------------------
# Fixture: in-memory Qdrant with the 5-doc dataset ingested
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def qdrant_with_docs(parsed_documents):
    """Return (qdrant_client, embedded_chunks) with 5 docs chunked, embedded, and stored."""
    all_chunks = []
    for doc in parsed_documents:
        all_chunks.extend(chunk_document(doc))

    embedded = embed_chunks(all_chunks)

    client = get_client(in_memory=True)
    ensure_collection(client)
    upsert_chunks(client, embedded)

    return client, embedded
