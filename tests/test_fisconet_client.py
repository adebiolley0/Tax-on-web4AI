"""Tests for the Fisconet client — uses canned fixture data (no network)."""

from datetime import date

from models import SourceType


class TestParseFisconetDocs:
    """Test parsing of canned Fisconet API responses."""

    def test_all_docs_parsed(self, parsed_documents):
        assert len(parsed_documents) == 5

    def test_documents_have_titles(self, parsed_documents):
        for doc in parsed_documents:
            assert doc.title, f"Document {doc.document_id} has no title"

    def test_documents_have_content(self, parsed_documents):
        for doc in parsed_documents:
            assert len(doc.content_text) > 0, f"Document {doc.document_id} has no content"

    def test_documents_are_fisconet_type(self, parsed_documents):
        for doc in parsed_documents:
            assert doc.source_type == SourceType.FISCONET_DOCUMENT

    def test_documents_have_guids(self, parsed_documents):
        for doc in parsed_documents:
            assert doc.fisconet_guid is not None
            assert len(doc.fisconet_guid) > 10  # UUIDs are 36 chars

    def test_documents_have_document_type(self, parsed_documents):
        for doc in parsed_documents:
            assert doc.document_type, f"Document {doc.document_id} has no document_type"

    def test_documents_have_language(self, parsed_documents):
        for doc in parsed_documents:
            assert doc.language == "fr"

    def test_unique_guids(self, parsed_documents):
        guids = [d.fisconet_guid for d in parsed_documents]
        assert len(set(guids)) == len(guids), "Duplicate GUIDs found"

    def test_dates_are_parsed(self, parsed_documents):
        """At least some documents should have a document_date."""
        dates = [d.document_date for d in parsed_documents if d.document_date is not None]
        assert len(dates) > 0
        for d in dates:
            assert isinstance(d, date)

    def test_diverse_document_types(self, parsed_documents):
        """The 5-doc fixture should contain multiple document types."""
        types = {d.document_type for d in parsed_documents}
        assert len(types) >= 2, f"Expected diverse types, got: {types}"
