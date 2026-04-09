"""Shared Pydantic models for the ingestion pipeline."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    DRUPAL_PAGE = "drupal_page"
    FISCONET_DOCUMENT = "fisconet_document"
    PDF = "pdf"


class Document(BaseModel):
    """A single ingested document (before chunking)."""

    source_url: str
    source_domain: str  # "fin.belgium.be" | "finances.belgium.be" | "minfin.fgov.be"
    source_type: SourceType
    document_id: str  # URL for Drupal, GUID for Fisconet
    title: str
    language: str = "fr"
    content_text: str  # full plain-text content for embedding
    content_html: str = ""  # raw HTML (kept for reference)

    # Dates
    document_date: date | None = None
    publication_date: date | None = None
    effective_date: date | None = None
    last_modified: datetime | None = None
    last_crawled: datetime = Field(default_factory=datetime.utcnow)

    # Classification
    audience: str | None = None  # particuliers, entreprises, independants, asbl, tous
    tax_category: str | None = None  # declaration, revenus, tva, isoc, habitation ...
    document_type: str | None = None  # loi, circulaire, ruling, commentaire, page_info ...
    fiscal_codes: list[str] = Field(default_factory=list)  # ["art. 7 CIR 92", ...]
    taxonomies: list[str] = Field(default_factory=list)  # taxonomy labels
    keywords: list[str] = Field(default_factory=list)  # subject keywords

    # Fisconet-specific
    fisconet_guid: str | None = None
    related_document_guids: list[str] = Field(default_factory=list)
    regionalisation: str | None = None


class Chunk(BaseModel):
    """A chunk of a document, ready for embedding."""

    chunk_id: str  # "{document_id}#chunk{chunk_index}"
    document_id: str  # parent document ID
    chunk_index: int
    section_heading: str | None = None
    chunk_text: str
    content_hash: str  # SHA-256 of chunk_text

    # Inherited from parent document
    source_url: str
    source_domain: str
    source_type: SourceType
    title: str
    language: str = "fr"
    document_date: date | None = None
    publication_date: date | None = None
    last_crawled: datetime = Field(default_factory=datetime.utcnow)
    audience: str | None = None
    tax_category: str | None = None
    document_type: str | None = None
    fiscal_codes: list[str] = Field(default_factory=list)
    taxonomies: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    fisconet_guid: str | None = None
    regionalisation: str | None = None


class EmbeddedChunk(BaseModel):
    """A chunk with its embedding vector, ready for Qdrant upsert."""

    chunk: Chunk
    vector: list[float]
