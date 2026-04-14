"""Qdrant search strategies with a unified interface.

Each strategy provides:
- setup_collection(): create the Qdrant collection with appropriate vector config
- index_chunks(): store documents with strategy-specific vectors
- search(): execute the search and return ranked results

Strategies:
1. DenseSearchStrategy     – Baseline cosine similarity (single dense vector)
2. HybridSearchStrategy    – Dense + BM25 sparse with RRF/DBSF fusion
3. ColBERTRerankStrategy   – Two-stage: dense prefetch → ColBERT multi-vector rerank
4. GroupedSearchStrategy   – Dense search grouped by document_id for diversity
"""

from __future__ import annotations

import logging
import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from qdrant_client import QdrantClient, models

from models import Chunk, EmbeddedChunk
from storage.embedder import embed_texts, get_model

logger = logging.getLogger(__name__)

DENSE_VECTOR_SIZE = 384  # paraphrase-multilingual-MiniLM-L12-v2


# ============================================================================
# Common types
# ============================================================================


@dataclass
class SearchResult:
    """Unified search result across all strategies."""

    score: float
    payload: dict


# ============================================================================
# BM25 Sparse Encoder
# ============================================================================

# French stopwords (articles, prepositions, conjunctions, pronouns)
_FR_STOPWORDS = frozenset(
    {
        "le", "la", "les", "de", "des", "du", "un", "une",
        "et", "en", "à", "au", "aux", "ce", "ces", "cette",
        "qui", "que", "qu", "est", "sont", "dans", "par",
        "pour", "sur", "avec", "il", "elle", "ils", "elles",
        "ne", "pas", "se", "son", "sa", "ses", "ou", "mais",
        "on", "nous", "vous", "je", "tu", "leur", "leurs",
        "être", "avoir", "faire", "dit", "été", "tout", "tous",
        "aussi", "plus", "comme", "peut", "même", "dont", "si",
        "d", "l", "n", "s", "y", "c", "j", "m", "t",
    }
)


def _tokenize_fr(text: str) -> list[str]:
    """Simple French-aware tokenizer: lowercase, split on non-alpha, filter stopwords."""
    tokens = re.findall(r"[a-zàâäéèêëïîôùûüÿçœæ]+", text.lower())
    return [t for t in tokens if t not in _FR_STOPWORDS and len(t) > 1]


class BM25Encoder:
    """BM25 sparse vector encoder for French text.

    Call fit() on the corpus before encode(). Uses k1=1.5, b=0.75.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.avg_dl: float = 0.0
        self.n_docs: int = 0
        self._fitted = False

    def fit(self, texts: Sequence[str]) -> BM25Encoder:
        """Build vocabulary and IDF from corpus."""
        self.n_docs = len(texts)
        doc_freq: Counter[str] = Counter()
        total_len = 0
        next_id = 0

        for text in texts:
            tokens = _tokenize_fr(text)
            total_len += len(tokens)
            for tok in set(tokens):
                doc_freq[tok] += 1
                if tok not in self.vocab:
                    self.vocab[tok] = next_id
                    next_id += 1

        self.avg_dl = total_len / max(self.n_docs, 1)

        for tok, df in doc_freq.items():
            self.idf[tok] = math.log(
                (self.n_docs - df + 0.5) / (df + 0.5) + 1.0
            )

        self._fitted = True
        logger.info(
            "BM25 fitted: %d docs, %d vocab terms, avg_dl=%.1f",
            self.n_docs,
            len(self.vocab),
            self.avg_dl,
        )
        return self

    def encode(self, text: str) -> models.SparseVector:
        """Encode a single text as a BM25 sparse vector."""
        tokens = _tokenize_fr(text)
        if not tokens:
            return models.SparseVector(indices=[0], values=[0.0])

        tf = Counter(tokens)
        dl = len(tokens)

        indices: list[int] = []
        values: list[float] = []

        for tok, count in tf.items():
            if tok not in self.vocab:
                continue
            idf_val = self.idf.get(tok, 0.0)
            tf_norm = (count * (self.k1 + 1)) / (
                count
                + self.k1 * (1 - self.b + self.b * dl / max(self.avg_dl, 1))
            )
            score = idf_val * tf_norm
            if score > 0:
                indices.append(self.vocab[tok])
                values.append(score)

        if not indices:
            return models.SparseVector(indices=[0], values=[0.0])
        return models.SparseVector(indices=indices, values=values)

    def encode_batch(self, texts: Sequence[str]) -> list[models.SparseVector]:
        """Encode multiple texts as BM25 sparse vectors."""
        return [self.encode(t) for t in texts]


# ============================================================================
# Helpers
# ============================================================================

_PAYLOAD_INDEXES = [
    ("source_domain", models.PayloadSchemaType.KEYWORD),
    ("source_type", models.PayloadSchemaType.KEYWORD),
    ("tax_category", models.PayloadSchemaType.KEYWORD),
    ("audience", models.PayloadSchemaType.KEYWORD),
    ("document_type", models.PayloadSchemaType.KEYWORD),
    ("language", models.PayloadSchemaType.KEYWORD),
    ("fiscal_codes", models.PayloadSchemaType.KEYWORD),
    ("document_id", models.PayloadSchemaType.KEYWORD),
    ("content_hash", models.PayloadSchemaType.KEYWORD),
]


def _create_payload_indexes(client: QdrantClient, collection_name: str) -> None:
    """Create standard payload indexes for filtering."""
    for field_name, schema in _PAYLOAD_INDEXES:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=schema,
        )


def _chunk_to_payload(chunk: Chunk) -> dict:
    """Convert a Chunk to a Qdrant payload dict."""
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "chunk_index": chunk.chunk_index,
        "section_heading": chunk.section_heading,
        "chunk_text": chunk.chunk_text,
        "content_hash": chunk.content_hash,
        "source_url": chunk.source_url,
        "source_domain": chunk.source_domain,
        "source_type": chunk.source_type.value,
        "title": chunk.title,
        "language": chunk.language,
        "document_date": (
            chunk.document_date.isoformat() if chunk.document_date else None
        ),
        "publication_date": (
            chunk.publication_date.isoformat()
            if chunk.publication_date
            else None
        ),
        "last_crawled": (
            chunk.last_crawled.isoformat() if chunk.last_crawled else None
        ),
        "audience": chunk.audience,
        "tax_category": chunk.tax_category,
        "document_type": chunk.document_type,
        "fiscal_codes": chunk.fiscal_codes,
        "taxonomies": chunk.taxonomies,
        "keywords": chunk.keywords,
        "fisconet_guid": chunk.fisconet_guid,
        "regionalisation": chunk.regionalisation,
    }


def _build_filter(filters: dict | None) -> models.Filter | None:
    """Build a Qdrant filter from a simple key/value dict."""
    if not filters:
        return None
    return models.Filter(
        must=[
            models.FieldCondition(key=k, match=models.MatchValue(value=v))
            for k, v in filters.items()
        ]
    )


def _encode_token_embeddings(texts: list[str]) -> list[list[list[float]]]:
    """Encode texts as token-level embeddings for ColBERT-style multi-vectors.

    Uses the same MiniLM model as the dense embedder. Returns a list of
    variable-length token-vector sequences (one per input text).
    """
    model = get_model()
    token_embs = model.encode(
        texts,
        output_value="token_embeddings",
        batch_size=64,
        show_progress_bar=False,
    )
    # sentence-transformers returns a list of numpy arrays,
    # each of shape (n_active_tokens, dim) with padding stripped.
    return [emb.tolist() for emb in token_embs]


# ============================================================================
# Strategy interface
# ============================================================================


class SearchStrategy(ABC):
    """Abstract interface for a Qdrant search strategy."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier (used as collection-name suffix and metrics key)."""
        ...

    @abstractmethod
    def setup_collection(
        self, client: QdrantClient, collection_name: str
    ) -> None:
        """Create the Qdrant collection with appropriate vector config."""
        ...

    @abstractmethod
    def index_chunks(
        self,
        client: QdrantClient,
        collection_name: str,
        chunks: Sequence[Chunk],
        embedded_chunks: Sequence[EmbeddedChunk],
    ) -> int:
        """Store chunks. Returns number of points upserted."""
        ...

    @abstractmethod
    def search(
        self,
        client: QdrantClient,
        collection_name: str,
        query_text: str,
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        """Execute search and return ranked results."""
        ...


# ============================================================================
# 1. Dense (baseline)
# ============================================================================


class DenseSearchStrategy(SearchStrategy):
    """Baseline: single dense-vector cosine similarity.

    Tests the raw semantic understanding of the embedding model
    (paraphrase-multilingual-MiniLM-L12-v2, 384-dim).
    """

    @property
    def name(self) -> str:
        return "dense"

    def setup_collection(self, client, collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=DENSE_VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )
        _create_payload_indexes(client, collection_name)

    def index_chunks(self, client, collection_name, chunks, embedded_chunks):
        points = [
            models.PointStruct(
                id=i,
                vector=ec.vector,
                payload=_chunk_to_payload(ec.chunk),
            )
            for i, ec in enumerate(embedded_chunks)
        ]
        client.upsert(collection_name=collection_name, points=points)
        return len(points)

    def search(self, client, collection_name, query_text, limit=10, filters=None):
        vec = embed_texts([query_text])[0]
        resp = client.query_points(
            collection_name=collection_name,
            query=vec,
            limit=limit,
            query_filter=_build_filter(filters),
            with_payload=True,
        )
        return [
            SearchResult(score=p.score, payload=p.payload)
            for p in resp.points
        ]


# ============================================================================
# 2. Hybrid (Dense + Sparse BM25)
# ============================================================================


class HybridSearchStrategy(SearchStrategy):
    """Dense + sparse BM25 search fused with RRF or DBSF.

    The BM25 encoder is fit automatically on the corpus during index_chunks().

    Args:
        fusion: "rrf" (Reciprocal Rank Fusion) or "dbsf" (Distribution-Based
                Score Fusion).
        prefetch_limit: candidates retrieved per branch before fusion.
    """

    def __init__(self, fusion: str = "rrf", prefetch_limit: int = 20):
        self._fusion = fusion
        self._prefetch_limit = prefetch_limit
        self.bm25 = BM25Encoder()

    @property
    def name(self) -> str:
        return f"hybrid_{self._fusion}"

    def setup_collection(self, client, collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=DENSE_VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                ),
            },
        )
        _create_payload_indexes(client, collection_name)

    def index_chunks(self, client, collection_name, chunks, embedded_chunks):
        if not self.bm25._fitted:
            self.bm25.fit([c.chunk_text for c in chunks])

        sparse_vecs = self.bm25.encode_batch([c.chunk_text for c in chunks])

        points = [
            models.PointStruct(
                id=i,
                vector={
                    "dense": ec.vector,
                    "sparse": sparse_vecs[i],
                },
                payload=_chunk_to_payload(ec.chunk),
            )
            for i, ec in enumerate(embedded_chunks)
        ]
        client.upsert(collection_name=collection_name, points=points)
        return len(points)

    def search(self, client, collection_name, query_text, limit=10, filters=None):
        dense_vec = embed_texts([query_text])[0]
        sparse_vec = self.bm25.encode(query_text)
        qf = _build_filter(filters)
        fusion = (
            models.Fusion.RRF if self._fusion == "rrf" else models.Fusion.DBSF
        )

        resp = client.query_points(
            collection_name=collection_name,
            prefetch=[
                models.Prefetch(
                    query=sparse_vec,
                    using="sparse",
                    limit=self._prefetch_limit,
                ),
                models.Prefetch(
                    query=dense_vec,
                    using="dense",
                    limit=self._prefetch_limit,
                ),
            ],
            query=models.FusionQuery(fusion=fusion),
            limit=limit,
            query_filter=qf,
            with_payload=True,
        )
        return [
            SearchResult(score=p.score, payload=p.payload)
            for p in resp.points
        ]


# ============================================================================
# 3. ColBERT Rerank (two-stage)
# ============================================================================


class ColBERTRerankStrategy(SearchStrategy):
    """Two-stage retrieval: fast dense prefetch → ColBERT multi-vector rerank.

    Uses token-level embeddings from the same MiniLM model as lightweight
    multi-vectors with MaxSim late-interaction scoring.  HNSW is disabled
    (m=0) on the multivector field to save memory — it is only used for
    rescoring prefetched candidates, not for initial search.

    Args:
        prefetch_limit: number of dense candidates to retrieve before reranking.
    """

    def __init__(self, prefetch_limit: int = 50):
        self._prefetch_limit = prefetch_limit

    @property
    def name(self) -> str:
        return "colbert_rerank"

    def setup_collection(self, client, collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=DENSE_VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
                "colbert": models.VectorParams(
                    size=DENSE_VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM,
                    ),
                    hnsw_config=models.HnswConfigDiff(m=0),
                ),
            },
        )
        _create_payload_indexes(client, collection_name)

    def index_chunks(self, client, collection_name, chunks, embedded_chunks):
        texts = [c.chunk_text for c in chunks]
        token_vecs = _encode_token_embeddings(texts)

        points = [
            models.PointStruct(
                id=i,
                vector={
                    "dense": ec.vector,
                    "colbert": token_vecs[i],
                },
                payload=_chunk_to_payload(ec.chunk),
            )
            for i, ec in enumerate(embedded_chunks)
        ]
        client.upsert(collection_name=collection_name, points=points)
        return len(points)

    def search(self, client, collection_name, query_text, limit=10, filters=None):
        dense_vec = embed_texts([query_text])[0]
        query_tokens = _encode_token_embeddings([query_text])[0]
        qf = _build_filter(filters)

        resp = client.query_points(
            collection_name=collection_name,
            prefetch=models.Prefetch(
                query=dense_vec,
                using="dense",
                limit=self._prefetch_limit,
            ),
            query=query_tokens,
            using="colbert",
            limit=limit,
            query_filter=qf,
            with_payload=True,
        )
        return [
            SearchResult(score=p.score, payload=p.payload)
            for p in resp.points
        ]


# ============================================================================
# 4. Grouped search (document-level diversity)
# ============================================================================


class GroupedSearchStrategy(SearchStrategy):
    """Dense search grouped by document_id for result diversity.

    Forces the database to return the best chunks across distinct documents,
    preventing a single highly-relevant document from monopolising all result
    slots.

    Args:
        group_size: max chunks returned per document.
    """

    def __init__(self, group_size: int = 3):
        self._group_size = group_size

    @property
    def name(self) -> str:
        return "grouped"

    def setup_collection(self, client, collection_name):
        # Same collection config as baseline dense
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=DENSE_VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )
        _create_payload_indexes(client, collection_name)

    def index_chunks(self, client, collection_name, chunks, embedded_chunks):
        points = [
            models.PointStruct(
                id=i,
                vector=ec.vector,
                payload=_chunk_to_payload(ec.chunk),
            )
            for i, ec in enumerate(embedded_chunks)
        ]
        client.upsert(collection_name=collection_name, points=points)
        return len(points)

    def search(self, client, collection_name, query_text, limit=10, filters=None):
        vec = embed_texts([query_text])[0]

        resp = client.query_points_groups(
            collection_name=collection_name,
            query=vec,
            group_by="document_id",
            limit=limit,
            group_size=self._group_size,
            query_filter=_build_filter(filters),
            with_payload=True,
        )

        # Flatten: interleave hits across groups for a fair ranked list.
        # Round 0: best hit from each group, round 1: second-best, etc.
        results: list[SearchResult] = []
        for round_idx in range(self._group_size):
            for group in resp.groups:
                if round_idx < len(group.hits):
                    hit = group.hits[round_idx]
                    results.append(
                        SearchResult(score=hit.score, payload=hit.payload)
                    )
        return results
