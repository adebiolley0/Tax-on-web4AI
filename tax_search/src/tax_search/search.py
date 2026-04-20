"""Qdrant search strategies with a unified interface.

Part 1 – Individual strategy classes (SearchStrategy ABC):
    DenseSearchStrategy, HybridSearchStrategy, ColBERTRerankStrategy,
    GroupedSearchStrategy.  Each owns its collection layout.

Part 2 – Composable grid-search infrastructure:
    PipelineConfig   – declarative description of a multi-stage pipeline.
    FullVectorStore  – single collection holding dense + sparse + ColBERT vectors.
    execute_pipeline – builds the nested Qdrant query tree from a PipelineConfig.
    generate_grid_configs – enumerates all valid config combinations.
"""

from __future__ import annotations

import logging
import math
import re
import sys
import time
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from typing import Sequence

from qdrant_client import QdrantClient, models

from tax_search.models import Chunk, EmbeddedChunk
from sentence_transformers import SentenceTransformer

from tax_search.embedder import embed_texts, get_model

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


def _print_progress(msg: str) -> None:
    """Write a timestamped progress line directly to stderr (visible even under pytest capture)."""
    ts = time.strftime("%H:%M:%S")
    sys.stderr.write(f"[{ts}] {msg}\n")
    sys.stderr.flush()


class SpladeSparseEncoder:
    """SPLADE++ sparse vector encoder using fastembed.

    Uses ``prithivida/Splade_PP_en_v1`` — a neural sparse model that performs
    term expansion and learns importance weights from a transformer.  The model
    is lazy-loaded on the first :meth:`encode` call so importing this module
    does not trigger a download.

    A **class-level** model cache ensures the 532 MB model is downloaded and
    loaded only once per process, regardless of how many ``SpladeSparseEncoder``
    instances are created.

    Requires ``fastembed`` (``uv add fastembed``).
    """

    MODEL_NAME = "prithivida/Splade_PP_en_v1"

    # Class-level cache: shared across all instances in the same process.
    _shared_model = None

    def __init__(self) -> None:
        pass  # no per-instance state; model lives on the class

    def _get_model(self):
        if SpladeSparseEncoder._shared_model is None:
            try:
                from fastembed import SparseTextEmbedding  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "fastembed is required for SPLADE: uv add fastembed"
                ) from exc
            _print_progress(
                f"SPLADE: loading model '{self.MODEL_NAME}' "
                "(first run downloads ~532 MB — this may take a few minutes) …"
            )
            t0 = time.perf_counter()
            SpladeSparseEncoder._shared_model = SparseTextEmbedding(
                model_name=self.MODEL_NAME,
                # fastembed prints a tqdm bar to stderr during download
            )
            _print_progress(
                f"SPLADE: model loaded in {time.perf_counter() - t0:.1f}s"
            )
        return SpladeSparseEncoder._shared_model

    def encode(self, text: str) -> models.SparseVector:
        """Encode a single text as a SPLADE sparse vector."""
        result = next(self._get_model().embed([text]))
        return models.SparseVector(
            indices=result.indices.tolist(),
            values=result.values.tolist(),
        )

    def encode_batch(
        self, texts: Sequence[str], batch_size: int = 64
    ) -> list[models.SparseVector]:
        """Encode texts in mini-batches with per-batch progress reporting."""
        model = self._get_model()
        texts = list(texts)
        total = len(texts)
        results: list[models.SparseVector] = []
        t0 = time.perf_counter()

        for start in range(0, total, batch_size):
            batch = texts[start : start + batch_size]
            for r in model.embed(batch):
                results.append(
                    models.SparseVector(
                        indices=r.indices.tolist(),
                        values=r.values.tolist(),
                    )
                )
            done = min(start + batch_size, total)
            elapsed = time.perf_counter() - t0
            _print_progress(
                f"SPLADE encode_batch: {done}/{total} texts "
                f"({elapsed:.1f}s elapsed)"
            )

        _print_progress(
            f"SPLADE encode_batch: done — {total} texts in "
            f"{time.perf_counter() - t0:.1f}s"
        )
        return results


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


def _encode_token_embeddings(
    texts: list[str],
    model: SentenceTransformer | None = None,
) -> list[list[list[float]]]:
    """Encode texts as token-level embeddings for ColBERT-style multi-vectors.

    Uses *model* if provided, otherwise falls back to the default singleton.
    Returns a list of variable-length token-vector sequences (one per input text).
    """
    if model is None:
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


# ############################################################################
#  Part 2 – Composable grid-search infrastructure
# ############################################################################


@dataclass
class PipelineConfig:
    """Declarative description of a multi-stage Qdrant search pipeline.

    Any combination of the flags below is valid.  ``execute_pipeline``
    translates the config into the right nested-prefetch query tree.
    """

    name: str = "dense"

    # Stage 1 – retrieval branches
    use_dense: bool = True
    use_sparse: bool = False

    # Which sparse encoder to use when use_sparse=True
    sparse_encoder: str = "bm25"  # "bm25" | "splade"

    # Fusion (only when both dense and sparse are active)
    fusion: str | None = None  # "rrf" | "dbsf"

    # Per-branch prefetch limit (hybrid) or dense-only prefetch
    prefetch_limit: int = 20

    # Stage 2 – ColBERT multi-vector reranking
    use_colbert_rerank: bool = False
    colbert_candidates: int = 50  # how many to feed into ColBERT

    # Result grouping (document-level diversity)
    use_grouping: bool = False
    group_size: int = 3
    group_limit: int = 10  # max distinct documents


# ---------------------------------------------------------------------------
# Full-vector collection (dense + sparse + colbert in one collection)
# ---------------------------------------------------------------------------


class FullVectorStore:
    """Collection with dense + BM25 sparse + SPLADE sparse + ColBERT vectors.

    One indexing pass; many search configurations.  Sparse fields:
    - ``sparse_bm25``   – custom BM25 encoder (French-aware)
    - ``sparse_splade`` – SPLADE++ neural sparse encoder (fastembed)
    """

    def __init__(self) -> None:
        self.bm25 = BM25Encoder()
        self.splade = SpladeSparseEncoder()

    def setup_collection(
        self,
        client: QdrantClient,
        collection_name: str,
        vector_size: int = DENSE_VECTOR_SIZE,
    ) -> None:
        """Create the Qdrant collection with dense + sparse + ColBERT vectors.

        *vector_size* must match the embedding dimension of the model that
        will be used to index and query this collection.
        """
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
                "colbert": models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM,
                    ),
                    hnsw_config=models.HnswConfigDiff(m=0),
                ),
            },
            sparse_vectors_config={
                # BM25: custom French-aware encoder; IDF applied at query time
                "sparse_bm25": models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                ),
                # SPLADE++: neural sparse encoder; weights are pre-computed
                "sparse_splade": models.SparseVectorParams(),
            },
        )
        _create_payload_indexes(client, collection_name)

    def index_chunks(
        self,
        client: QdrantClient,
        collection_name: str,
        chunks: Sequence[Chunk],
        embedded_chunks: Sequence[EmbeddedChunk],
        model: SentenceTransformer | None = None,
    ) -> int:
        """Index chunks into Qdrant with dense, sparse, and ColBERT vectors.

        *model* is used for ColBERT token-level embeddings.  When omitted the
        default singleton model is used (must match the model that produced
        *embedded_chunks*).
        """
        texts = [c.chunk_text for c in chunks]
        _print_progress(
            f"FullVectorStore.index_chunks: {len(texts)} chunks, "
            f"collection='{collection_name}'"
        )

        t_bm25 = time.perf_counter()
        if not self.bm25._fitted:
            self.bm25.fit(texts)
        bm25_vecs = self.bm25.encode_batch(texts)
        _print_progress(
            f"BM25 encoding done in {time.perf_counter() - t_bm25:.1f}s"
        )

        t_splade = time.perf_counter()
        _print_progress(f"Starting SPLADE encoding for {len(texts)} chunks …")
        splade_vecs = self.splade.encode_batch(texts)
        _print_progress(
            f"SPLADE encoding done in {time.perf_counter() - t_splade:.1f}s"
        )

        t_colbert = time.perf_counter()
        _print_progress(f"Starting ColBERT token encoding for {len(texts)} chunks …")
        token_vecs = _encode_token_embeddings(texts, model=model)
        _print_progress(
            f"ColBERT encoding done in {time.perf_counter() - t_colbert:.1f}s"
        )

        points = [
            models.PointStruct(
                id=i,
                vector={
                    "dense": ec.vector,
                    "sparse_bm25": bm25_vecs[i],
                    "sparse_splade": splade_vecs[i],
                    "colbert": token_vecs[i],
                },
                payload=_chunk_to_payload(ec.chunk),
            )
            for i, ec in enumerate(embedded_chunks)
        ]
        client.upsert(collection_name=collection_name, points=points)
        logger.info("Full-vector store: indexed %d points", len(points))
        return len(points)


# ---------------------------------------------------------------------------
# Pipeline executor
# ---------------------------------------------------------------------------


def execute_pipeline(
    config: PipelineConfig,
    client: QdrantClient,
    collection_name: str,
    dense_vec: list[float],
    sparse_vecs: dict[str, models.SparseVector],
    colbert_tokens: list[list[float]],
    limit: int = 10,
    filters: dict | None = None,
) -> list[SearchResult]:
    """Execute a search pipeline described by *config*.

    Builds the appropriate nested-prefetch / fusion / rerank / group query
    and runs it against a :class:`FullVectorStore` collection.

    *sparse_vecs* is a mapping from encoder name to pre-computed sparse vector,
    e.g. ``{"bm25": <SparseVector>, "splade": <SparseVector>}``.
    ``config.sparse_encoder`` selects which entry (and which collection field)
    to use for the sparse retrieval branch.
    """
    qf = _build_filter(filters)

    # Select the sparse vector and collection field for this config
    sparse_vec = sparse_vecs.get(config.sparse_encoder, next(iter(sparse_vecs.values())))
    sparse_field = f"sparse_{config.sparse_encoder}"

    # -- Stage 1: build retrieval query/prefetch --------------------------
    if config.use_dense and config.use_sparse and config.fusion:
        # Hybrid: two prefetch branches → fusion
        retrieval_prefetch: list[models.Prefetch] | models.Prefetch | None = [
            models.Prefetch(
                query=sparse_vec,
                using=sparse_field,
                limit=config.prefetch_limit,
            ),
            models.Prefetch(
                query=dense_vec,
                using="dense",
                limit=config.prefetch_limit,
            ),
        ]
        fusion_enum = (
            models.Fusion.RRF
            if config.fusion == "rrf"
            else models.Fusion.DBSF
        )
        retrieval_query = models.FusionQuery(fusion=fusion_enum)
        retrieval_using = None
    elif config.use_sparse and not config.use_dense:
        retrieval_prefetch = None
        retrieval_query = sparse_vec
        retrieval_using = sparse_field
    else:
        # Dense only (default)
        retrieval_prefetch = None
        retrieval_query = dense_vec
        retrieval_using = "dense"

    # -- Stage 2: optional ColBERT reranking ------------------------------
    if config.use_colbert_rerank:
        if retrieval_prefetch is not None:
            # Wrap hybrid fusion inside a single Prefetch so ColBERT
            # rescores the fused candidates.
            stage1 = models.Prefetch(
                prefetch=retrieval_prefetch,
                query=retrieval_query,
                limit=config.colbert_candidates,
            )
        else:
            stage1 = models.Prefetch(
                query=retrieval_query,
                using=retrieval_using,
                limit=config.colbert_candidates,
            )
        final_prefetch: list[models.Prefetch] | models.Prefetch | None = (
            stage1
        )
        final_query = colbert_tokens
        final_using: str | None = "colbert"
    else:
        final_prefetch = retrieval_prefetch
        final_query = retrieval_query
        final_using = retrieval_using

    # -- Stage 3: execute (flat or grouped) --------------------------------
    if config.use_grouping:
        kwargs_g: dict = dict(
            collection_name=collection_name,
            query=final_query,
            group_by="document_id",
            limit=config.group_limit,
            group_size=config.group_size,
            with_payload=True,
        )
        if final_prefetch is not None:
            kwargs_g["prefetch"] = final_prefetch
        if final_using is not None:
            kwargs_g["using"] = final_using
        if qf is not None:
            kwargs_g["query_filter"] = qf

        resp_g = client.query_points_groups(**kwargs_g)

        results: list[SearchResult] = []
        for round_idx in range(config.group_size):
            for group in resp_g.groups:
                if round_idx < len(group.hits):
                    h = group.hits[round_idx]
                    results.append(
                        SearchResult(score=h.score, payload=h.payload)
                    )
        return results

    # Flat (non-grouped) search
    kwargs_q: dict = dict(
        collection_name=collection_name,
        query=final_query,
        limit=limit,
        with_payload=True,
    )
    if final_prefetch is not None:
        kwargs_q["prefetch"] = final_prefetch
    if final_using is not None:
        kwargs_q["using"] = final_using
    if qf is not None:
        kwargs_q["query_filter"] = qf

    resp = client.query_points(**kwargs_q)
    return [
        SearchResult(score=p.score, payload=p.payload) for p in resp.points
    ]


# ---------------------------------------------------------------------------
# Grid configuration generator
# ---------------------------------------------------------------------------


def generate_grid_configs() -> list[PipelineConfig]:
    """Enumerate all search-pipeline configurations for grid search.

    Returns ~45 configs covering:
    - retrieval method  (dense / sparse-bm25 / sparse-splade / hybrid)
    - sparse encoder    (bm25 | splade)
    - fusion method     (rrf | dbsf)
    - prefetch depth    (20 / 50 / 100)
    - ColBERT reranking (off / on with 20–100 candidates)
    - document grouping (off / group_size 1–5)
    - full combo        (hybrid → ColBERT → grouped)
    """
    cfgs: list[PipelineConfig] = []

    # ---- 1. Baselines ---------------------------------------------------
    cfgs.append(PipelineConfig(name="dense"))
    # BM25 sparse-only
    cfgs.append(
        PipelineConfig(name="sparse_bm25_only", use_dense=False, use_sparse=True,
                       sparse_encoder="bm25")
    )
    # SPLADE sparse-only
    cfgs.append(
        PipelineConfig(name="sparse_splade_only", use_dense=False, use_sparse=True,
                       sparse_encoder="splade")
    )

    # ---- 2. Hybrid fusion variants (BM25) --------------------------------
    for fusion in ("rrf", "dbsf"):
        for pf in (20, 50, 100):
            cfgs.append(
                PipelineConfig(
                    name=f"hybrid_bm25_{fusion}_pf{pf}",
                    use_sparse=True,
                    sparse_encoder="bm25",
                    fusion=fusion,
                    prefetch_limit=pf,
                )
            )

    # ---- 3. Hybrid fusion variants (SPLADE) -----------------------------
    for fusion in ("rrf", "dbsf"):
        for pf in (20, 50, 100):
            cfgs.append(
                PipelineConfig(
                    name=f"hybrid_splade_{fusion}_pf{pf}",
                    use_sparse=True,
                    sparse_encoder="splade",
                    fusion=fusion,
                    prefetch_limit=pf,
                )
            )

    # ---- 4. Dense → ColBERT rerank (vary candidate pool) ----------------
    for cc in (20, 50, 100):
        cfgs.append(
            PipelineConfig(
                name=f"dense_colbert_cc{cc}",
                use_colbert_rerank=True,
                colbert_candidates=cc,
            )
        )

    # ---- 5. Sparse-only → ColBERT rerank --------------------------------
    cfgs.append(
        PipelineConfig(
            name="sparse_bm25_colbert",
            use_dense=False,
            use_sparse=True,
            sparse_encoder="bm25",
            use_colbert_rerank=True,
            colbert_candidates=50,
        )
    )
    cfgs.append(
        PipelineConfig(
            name="sparse_splade_colbert",
            use_dense=False,
            use_sparse=True,
            sparse_encoder="splade",
            use_colbert_rerank=True,
            colbert_candidates=50,
        )
    )

    # ---- 6. Hybrid → ColBERT (3-stage, BM25) ----------------------------
    for fusion in ("rrf", "dbsf"):
        for pf in (50, 100):
            cfgs.append(
                PipelineConfig(
                    name=f"hybrid_bm25_{fusion}_pf{pf}_colbert",
                    use_sparse=True,
                    sparse_encoder="bm25",
                    fusion=fusion,
                    prefetch_limit=pf,
                    use_colbert_rerank=True,
                    colbert_candidates=50,
                )
            )

    # ---- 7. Hybrid → ColBERT (3-stage, SPLADE) --------------------------
    for fusion in ("rrf", "dbsf"):
        for pf in (50, 100):
            cfgs.append(
                PipelineConfig(
                    name=f"hybrid_splade_{fusion}_pf{pf}_colbert",
                    use_sparse=True,
                    sparse_encoder="splade",
                    fusion=fusion,
                    prefetch_limit=pf,
                    use_colbert_rerank=True,
                    colbert_candidates=50,
                )
            )

    # ---- 8. Grouped variants (dense retrieval) --------------------------
    for gs in (1, 2, 3, 5):
        cfgs.append(
            PipelineConfig(
                name=f"grouped_gs{gs}",
                use_grouping=True,
                group_size=gs,
            )
        )

    # ---- 9. Hybrid + grouped (BM25 and SPLADE) --------------------------
    for sparse_enc in ("bm25", "splade"):
        for fusion in ("rrf", "dbsf"):
            cfgs.append(
                PipelineConfig(
                    name=f"hybrid_{sparse_enc}_{fusion}_grouped",
                    use_sparse=True,
                    sparse_encoder=sparse_enc,
                    fusion=fusion,
                    prefetch_limit=50,
                    use_grouping=True,
                    group_size=3,
                )
            )

    # ---- 10. ColBERT + grouped ------------------------------------------
    cfgs.append(
        PipelineConfig(
            name="colbert_grouped",
            use_colbert_rerank=True,
            colbert_candidates=50,
            use_grouping=True,
            group_size=3,
        )
    )

    # ---- 11. Hybrid → ColBERT + grouped (full pipeline, both encoders) --
    for sparse_enc in ("bm25", "splade"):
        for fusion in ("rrf", "dbsf"):
            cfgs.append(
                PipelineConfig(
                    name=f"hybrid_{sparse_enc}_{fusion}_colbert_grouped",
                    use_sparse=True,
                    sparse_encoder=sparse_enc,
                    fusion=fusion,
                    prefetch_limit=50,
                    use_colbert_rerank=True,
                    colbert_candidates=50,
                    use_grouping=True,
                    group_size=3,
                )
            )

    return cfgs
