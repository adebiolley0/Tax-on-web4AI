"""Tests for Qdrant store — uses the 5-doc fixture dataset."""

import pytest

from tax_search.embedder import embed_texts
from tax_search.qdrant_store import (
    COLLECTION_NAME,
    delete_by_document_id,
    ensure_collection,
    get_client,
    search_similar,
    upsert_chunks,
)


class TestQdrantWithFixtures:
    """Integration tests using the session-scoped 5-doc Qdrant fixture."""

    def test_collection_exists(self, qdrant_with_docs):
        client, _ = qdrant_with_docs
        collections = [c.name for c in client.get_collections().collections]
        assert COLLECTION_NAME in collections

    def test_points_were_ingested(self, qdrant_with_docs):
        client, embedded = qdrant_with_docs
        info = client.get_collection(COLLECTION_NAME)
        assert info.points_count > 0
        assert info.points_count == len(embedded)

    def test_vector_dimension(self, qdrant_with_docs):
        client, _ = qdrant_with_docs
        info = client.get_collection(COLLECTION_NAME)
        assert info.config.params.vectors.size == 384

    def test_semantic_search_returns_results(self, qdrant_with_docs):
        client, _ = qdrant_with_docs
        query_vec = embed_texts(["TVA taxe valeur ajoutee"])[0]
        results = search_similar(client, query_vec, limit=3)
        assert len(results) > 0
        assert results[0]["score"] > 0

    def test_semantic_search_relevance(self, qdrant_with_docs):
        """A TVA query should rank TVA documents higher than succession docs."""
        client, _ = qdrant_with_docs
        query_vec = embed_texts(["taxe sur la valeur ajoutee TVA"])[0]
        results = search_similar(client, query_vec, limit=5)
        # The top result should mention TVA in title or chunk_text
        top = results[0]["payload"]
        text = (top.get("title", "") + " " + top.get("chunk_text", "")).lower()
        assert "tva" in text

    def test_semantic_search_with_filter(self, qdrant_with_docs):
        client, _ = qdrant_with_docs
        query_vec = embed_texts(["impot"])[0]

        # Search with language filter — all our docs are French
        results_fr = search_similar(client, query_vec, limit=5, filters={"language": "fr"})
        assert len(results_fr) > 0

        # Search with non-existent language — should return nothing
        results_de = search_similar(client, query_vec, limit=5, filters={"language": "de"})
        assert len(results_de) == 0

    def test_payload_fields_present(self, qdrant_with_docs):
        client, _ = qdrant_with_docs
        query_vec = embed_texts(["impot"])[0]
        results = search_similar(client, query_vec, limit=1)
        payload = results[0]["payload"]

        # Check essential fields are in the payload
        assert "chunk_text" in payload
        assert "title" in payload
        assert "source_url" in payload
        assert "source_domain" in payload
        assert "source_type" in payload
        assert "document_id" in payload
        assert "language" in payload
        assert "chunk_id" in payload
        assert "content_hash" in payload

    def test_all_five_documents_represented(self, qdrant_with_docs, parsed_documents):
        """All 5 source documents should have at least one chunk in the DB."""
        client, _ = qdrant_with_docs
        query_vec = embed_texts(["impot belgique"])[0]
        # Fetch a large number to cover all documents
        results = search_similar(client, query_vec, limit=100)
        doc_ids_in_db = {r["payload"]["document_id"] for r in results}
        source_doc_ids = {d.document_id for d in parsed_documents}
        assert source_doc_ids.issubset(doc_ids_in_db)


class TestQdrantUnit:
    """Unit tests for Qdrant helpers (fresh in-memory client per test)."""

    def test_ensure_collection_idempotent(self):
        client = get_client(in_memory=True)
        ensure_collection(client)
        ensure_collection(client)  # should not raise
        collections = [c.name for c in client.get_collections().collections]
        assert COLLECTION_NAME in collections

    def test_delete_by_document_id(self, qdrant_with_docs, parsed_documents):
        """Test deleting chunks by document_id on a separate in-memory instance."""
        from storage.chunker import chunk_document
        from storage.embedder import embed_chunks

        client = get_client(in_memory=True)
        ensure_collection(client)

        # Ingest one doc
        doc = parsed_documents[0]
        chunks = chunk_document(doc)
        embedded = embed_chunks(chunks)
        upsert_chunks(client, embedded)

        info = client.get_collection(COLLECTION_NAME)
        assert info.points_count == len(embedded)

        # Delete by document_id
        delete_by_document_id(client, doc.document_id)
        info = client.get_collection(COLLECTION_NAME)
        assert info.points_count == 0
