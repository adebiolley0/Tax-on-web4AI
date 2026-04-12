"""Semantic document chunking for tax documents."""

from __future__ import annotations

import hashlib
import re

from models import Chunk, Document
from storage.content_cleaner import clean_for_indexing


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _find_heading(text: str) -> str | None:
    """Extract the first markdown heading from a text block."""
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            return re.sub(r"^#+\s*", "", line).strip()
    return None


def chunk_document(
    doc: Document,
    max_chunk_size: int = 1500,
    overlap: int = 200,
) -> list[Chunk]:
    """Split a document into overlapping chunks.

    Strategy:
    1. Split on markdown headings (## or ###) first
    2. If a section is still too large, split on double newlines (paragraphs)
    3. If still too large, split on single newlines
    4. Apply overlap between consecutive chunks
    """
    text = clean_for_indexing(doc.content_text)
    if not text:
        return []

    # Split on markdown headings
    sections = re.split(r"(?=\n#{1,3}\s)", text)
    sections = [s.strip() for s in sections if s.strip()]

    # Further split oversized sections on paragraphs
    refined: list[str] = []
    for section in sections:
        if len(section) <= max_chunk_size:
            refined.append(section)
        else:
            paragraphs = re.split(r"\n\n+", section)
            refined.extend(p.strip() for p in paragraphs if p.strip())

    # Merge small consecutive pieces, split oversized ones
    final_chunks: list[str] = []
    buffer = ""
    for piece in refined:
        if len(piece) > max_chunk_size:
            # Flush buffer first
            if buffer:
                final_chunks.append(buffer)
                buffer = ""
            # Hard split on newlines, then on character boundary
            lines = piece.split("\n")
            sub_buf = ""
            for line in lines:
                if len(sub_buf) + len(line) + 1 > max_chunk_size:
                    if sub_buf:
                        final_chunks.append(sub_buf)
                    sub_buf = line
                else:
                    sub_buf = f"{sub_buf}\n{line}" if sub_buf else line
            if sub_buf:
                final_chunks.append(sub_buf)
        elif len(buffer) + len(piece) + 2 > max_chunk_size:
            if buffer:
                final_chunks.append(buffer)
            buffer = piece
        else:
            buffer = f"{buffer}\n\n{piece}" if buffer else piece

    if buffer:
        final_chunks.append(buffer)

    # Apply overlap: prepend tail of previous chunk to current
    overlapped: list[str] = []
    for i, chunk_text in enumerate(final_chunks):
        if i > 0 and overlap > 0:
            prev = final_chunks[i - 1]
            tail = prev[-overlap:] if len(prev) > overlap else prev
            # Find a word boundary in the tail
            space_idx = tail.find(" ")
            if space_idx > 0:
                tail = tail[space_idx + 1 :]
            chunk_text = tail + "\n" + chunk_text
        overlapped.append(chunk_text)

    # Build Chunk objects
    chunks: list[Chunk] = []
    for i, chunk_text in enumerate(overlapped):
        heading = _find_heading(chunk_text)
        chunks.append(
            Chunk(
                chunk_id=f"{doc.document_id}#chunk{i}",
                document_id=doc.document_id,
                chunk_index=i,
                section_heading=heading,
                chunk_text=chunk_text,
                content_hash=_sha256(chunk_text),
                source_url=doc.source_url,
                source_domain=doc.source_domain,
                source_type=doc.source_type,
                title=doc.title,
                language=doc.language,
                document_date=doc.document_date,
                publication_date=doc.publication_date,
                last_crawled=doc.last_crawled,
                audience=doc.audience,
                tax_category=doc.tax_category,
                document_type=doc.document_type,
                fiscal_codes=doc.fiscal_codes,
                taxonomies=doc.taxonomies,
                keywords=doc.keywords,
                fisconet_guid=doc.fisconet_guid,
                regionalisation=doc.regionalisation,
            )
        )

    return chunks
