"""Tests for the embedding pipeline."""

from storage.embedder import embed_chunks, embed_texts, get_model
from models import Chunk, SourceType


class TestEmbedTexts:
    def test_single_text(self):
        vecs = embed_texts(["Impot des personnes physiques en Belgique"])
        assert len(vecs) == 1
        assert len(vecs[0]) == 384  # MiniLM-L12-v2 dimension

    def test_multiple_texts(self):
        texts = ["TVA", "Impot sur les societes", "Droits de succession"]
        vecs = embed_texts(texts)
        assert len(vecs) == 3
        for v in vecs:
            assert len(v) == 384

    def test_similar_texts_have_higher_similarity(self):
        """Semantically similar texts should have higher cosine similarity."""
        import math
        vecs = embed_texts([
            "La taxe sur la valeur ajoutée est un impôt indirect sur la consommation",
            "La TVA est un impôt indirect prélevé sur les biens et services",
            "Le python est un serpent non venimeux qui vit dans les forêts tropicales",
        ])

        def cosine(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a))
            nb = math.sqrt(sum(x * x for x in b))
            return dot / (na * nb)

        sim_related = cosine(vecs[0], vecs[1])
        sim_unrelated = cosine(vecs[0], vecs[2])
        assert sim_related > sim_unrelated


class TestEmbedChunks:
    def test_embed_chunks_returns_embedded_chunks(self):
        chunk = Chunk(
            chunk_id="test#chunk0",
            document_id="test",
            chunk_index=0,
            chunk_text="Article 7 CIR 92 concerne les revenus immobiliers.",
            content_hash="abc123",
            source_url="https://example.com",
            source_domain="example.com",
            source_type=SourceType.FISCONET_DOCUMENT,
            title="Test",
        )
        embedded = embed_chunks([chunk])
        assert len(embedded) == 1
        assert embedded[0].chunk.chunk_id == "test#chunk0"
        assert len(embedded[0].vector) == 384

    def test_embed_empty_list(self):
        assert embed_chunks([]) == []


class TestGetModel:
    def test_model_loads_and_is_cached(self):
        m1 = get_model()
        m2 = get_model()
        assert m1 is m2
        assert m1.get_embedding_dimension() == 384
