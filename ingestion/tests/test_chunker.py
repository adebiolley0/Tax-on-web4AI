"""Tests for the document chunker."""

from tax_ingestion.storage.chunker import chunk_document
from tax_search.models import Document, SourceType


def _make_doc(text: str, title: str = "Test doc") -> Document:
    return Document(
        source_url="https://example.com/test",
        source_domain="example.com",
        source_type=SourceType.DRUPAL_PAGE,
        document_id="test-doc-1",
        title=title,
        content_text=text,
    )


class TestChunkDocument:
    def test_empty_content_returns_no_chunks(self):
        doc = _make_doc("")
        assert chunk_document(doc) == []

    def test_short_content_single_chunk(self):
        doc = _make_doc("This is a short document about Belgian taxes.")
        chunks = chunk_document(doc)
        assert len(chunks) == 1
        assert "Belgian taxes" in chunks[0].chunk_text

    def test_chunks_have_correct_metadata(self):
        doc = _make_doc("Some content about TVA.", title="TVA Guide")
        chunks = chunk_document(doc)
        assert chunks[0].title == "TVA Guide"
        assert chunks[0].source_type == SourceType.DRUPAL_PAGE
        assert chunks[0].document_id == "test-doc-1"
        assert chunks[0].chunk_index == 0
        assert chunks[0].chunk_id == "test-doc-1#chunk0"

    def test_long_content_produces_multiple_chunks(self):
        # Build a document that exceeds max_chunk_size
        text = "\n\n".join(f"Paragraph {i}: " + "x" * 200 for i in range(20))
        doc = _make_doc(text)
        chunks = chunk_document(doc, max_chunk_size=500, overlap=50)
        assert len(chunks) > 1
        # Check sequential chunk indices
        for i, c in enumerate(chunks):
            assert c.chunk_index == i

    def test_heading_splitting(self):
        text = (
            "Introduction to Belgian taxes.\n"
            "## TVA\n"
            "La TVA est un impot indirect.\n"
            "## IPP\n"
            "L'impot des personnes physiques.\n"
        )
        doc = _make_doc(text)
        chunks = chunk_document(doc, max_chunk_size=5000)
        # With a large max_chunk_size, headings should still be detected
        # At minimum one chunk should have a heading
        headings = [c.section_heading for c in chunks if c.section_heading]
        assert any("TVA" in h or "IPP" in h for h in headings)

    def test_content_hash_is_deterministic(self):
        doc = _make_doc("Deterministic content test.")
        chunks1 = chunk_document(doc)
        chunks2 = chunk_document(doc)
        assert chunks1[0].content_hash == chunks2[0].content_hash

    def test_content_hash_differs_for_different_content(self):
        doc1 = _make_doc("Content A")
        doc2 = _make_doc("Content B")
        c1 = chunk_document(doc1)
        c2 = chunk_document(doc2)
        assert c1[0].content_hash != c2[0].content_hash

    def test_real_fisconet_doc_chunks(self, parsed_documents):
        """Chunk one of the real downloaded documents."""
        doc = parsed_documents[0]
        chunks = chunk_document(doc)
        assert len(chunks) >= 1
        # Every chunk should have non-empty text
        for c in chunks:
            assert len(c.chunk_text.strip()) > 0
