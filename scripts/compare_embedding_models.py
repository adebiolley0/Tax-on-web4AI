#!/usr/bin/env python3
"""Embedding model comparison benchmark for Tax-on-web4AI.

Runs the full 10-question validation set against three candidate models and
reports Recall@10, MRR, average best-match score, per-question rank/score, and
whether the Q5 synonym gap (dons vs libéralités) is resolved.

Usage:
    PYTHONPATH=src uv run python scripts/compare_embedding_models.py

Models compared:
    - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2  (baseline, 384D)
    - BAAI/bge-m3                                                   (1024D)
    - Parallia/Fairly-Multilingual-ModernBERT-Embed-BE              (768D)
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# Ensure src/ is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import Document, SourceType  # noqa: E402  (after sys.path insert)
from storage.chunker import chunk_document  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATION_DIR = REPO_ROOT / "validation_dataset"
MD_DIR = VALIDATION_DIR / "md"
QUESTIONS_PATH = VALIDATION_DIR / "questions.json"
RESULTS_JSON = REPO_ROOT / "benchmark_results.json"

# ---------------------------------------------------------------------------
# Models to compare
# ---------------------------------------------------------------------------

MODELS: list[dict] = [
    {
        "key": "minilm",
        "hf_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "label": "MiniLM-L12 v2 (baseline, 384D)",
        # Standard symmetric encode — no special prompt needed
        "query_prompt": None,
    },
    {
        "key": "bge_m3",
        "hf_id": "BAAI/bge-m3",
        "label": "BGE-M3 (1024D)",
        # BGE models benefit from a query-side instruction prefix.
        # The sentence-transformers wrapper exposes prompt_name="query" if the
        # model's tokenizer_config.json defines it; fall back to a manual prefix.
        "query_prompt": "query",
    },
    {
        "key": "modernbert_be",
        "hf_id": "Parallia/Fairly-Multilingual-ModernBERT-Embed-BE",
        "label": "Fairly-Multilingual-ModernBERT-BE",
        "query_prompt": None,
    },
]

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class QuestionResult:
    qid: str
    question: str
    expected_docs: list[str]
    secondary_docs: list[str]
    hits: list[dict]  # [{"score": float, "document_id": str}]

    @property
    def top10_doc_ids(self) -> list[str]:
        return [h["document_id"] for h in self.hits[:10]]

    @property
    def primary_found_in_top10(self) -> bool:
        return bool(set(self.expected_docs) & set(self.top10_doc_ids))

    @property
    def primary_rank(self) -> int | None:
        """1-based rank of the first expected-doc hit in the top-20, or None."""
        for i, h in enumerate(self.hits[:20]):
            if h["document_id"] in self.expected_docs:
                return i + 1
        return None

    @property
    def best_expected_score(self) -> float:
        """Cosine score of the first expected-doc hit, or 0 if not found."""
        for h in self.hits[:20]:
            if h["document_id"] in self.expected_docs:
                return h["score"]
        return 0.0

    def to_dict(self) -> dict:
        return {
            "qid": self.qid,
            "found_in_top10": self.primary_found_in_top10,
            "rank": self.primary_rank,
            "best_score": round(self.best_expected_score, 4),
        }


@dataclass
class ModelResult:
    key: str
    label: str
    hf_id: str
    load_time: float = 0.0
    embed_time: float = 0.0
    vector_dim: int = 0
    n_chunks: int = 0
    question_results: list[QuestionResult] = field(default_factory=list)
    error: str = ""

    # ---- aggregate metrics -------------------------------------------------

    @property
    def recall_at_10(self) -> float:
        qs = [r for r in self.question_results if r.expected_docs]
        return sum(1 for r in qs if r.primary_found_in_top10) / len(qs) if qs else 0.0

    @property
    def mrr(self) -> float:
        qs = [r for r in self.question_results if r.expected_docs]
        if not qs:
            return 0.0
        rr_sum = sum(1.0 / r.primary_rank for r in qs if r.primary_rank)
        return rr_sum / len(qs)

    @property
    def avg_best_score(self) -> float:
        scores = [r.best_expected_score for r in self.question_results if r.expected_docs]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def q5_resolved(self) -> bool:
        """Whether the dons/libéralités synonym gap (Q5) is bridged."""
        for r in self.question_results:
            if r.qid == "Q5":
                return r.primary_found_in_top10
        return False

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "hf_id": self.hf_id,
            "vector_dim": self.vector_dim,
            "n_chunks": self.n_chunks,
            "load_time_s": round(self.load_time, 1),
            "embed_time_s": round(self.embed_time, 1),
            "recall_at_10": round(self.recall_at_10, 4),
            "mrr": round(self.mrr, 4),
            "avg_best_score": round(self.avg_best_score, 4),
            "q5_resolved": self.q5_resolved,
            "error": self.error,
            "question_results": [qr.to_dict() for qr in self.question_results],
        }


# ---------------------------------------------------------------------------
# Benchmark helpers
# ---------------------------------------------------------------------------


def _load_documents() -> list[Document]:
    md_files = sorted(MD_DIR.glob("*.md"))
    docs = []
    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        docs.append(
            Document(
                source_url=f"fisconet://{md_path.stem}",
                source_domain="minfin.fgov.be",
                source_type=SourceType.FISCONET_DOCUMENT,
                document_id=md_path.stem,
                title=md_path.stem,
                language="fr",
                content_text=text,
            )
        )
    return docs


def _build_index(
    model: SentenceTransformer,
    docs: list[Document],
    batch_size: int = 32,
) -> tuple[QdrantClient, int, float]:
    """Chunk docs, embed with *model*, store in in-memory Qdrant.

    Returns (client, vector_dim, embed_time_seconds).
    """
    all_chunks = []
    for doc in docs:
        # chunk_document calls clean_for_indexing internally
        all_chunks.extend(chunk_document(doc))
    logger.info("Chunked %d docs → %d chunks", len(docs), len(all_chunks))

    texts = [c.chunk_text for c in all_chunks]

    t0 = time.perf_counter()
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
    embed_time = time.perf_counter() - t0
    logger.info("Embedded %d chunks in %.1fs", len(texts), embed_time)

    vector_dim = int(embeddings.shape[1])

    client = QdrantClient(location=":memory:")
    client.create_collection(
        collection_name="bench",
        vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
    )
    points = [
        PointStruct(
            id=i,
            vector=embeddings[i].tolist(),
            payload={"document_id": all_chunks[i].document_id},
        )
        for i in range(len(all_chunks))
    ]
    client.upsert(collection_name="bench", points=points)
    logger.info("Upserted %d points (dim=%d)", len(points), vector_dim)

    return client, vector_dim, embed_time, len(all_chunks)


def _encode_queries(
    model: SentenceTransformer,
    texts: list[str],
    query_prompt: str | None,
) -> "np.ndarray":  # type: ignore[name-defined]
    """Encode queries, applying a prompt prefix if the model supports it."""
    if query_prompt:
        try:
            return model.encode(texts, prompt_name=query_prompt, show_progress_bar=False)
        except (ValueError, KeyError):
            # Model doesn't define this prompt_name — fall back to raw encode
            logger.warning("prompt_name=%r not found in model config, using raw encode", query_prompt)
    return model.encode(texts, show_progress_bar=False)


def _run_questions(
    model: SentenceTransformer,
    client: QdrantClient,
    questions: list[dict],
    query_prompt: str | None,
) -> list[QuestionResult]:
    q_texts = [q["question"] for q in questions]
    q_vectors = _encode_queries(model, q_texts, query_prompt)

    results = []
    for q, vec in zip(questions, q_vectors):
        hits = client.query_points(
            collection_name="bench",
            query=vec.tolist(),
            limit=20,
            with_payload=True,
        )
        results.append(
            QuestionResult(
                qid=q["id"],
                question=q["question"],
                expected_docs=q["expected_docs"],
                secondary_docs=q.get("secondary_docs", []),
                hits=[
                    {"score": h.score, "document_id": h.payload["document_id"]}
                    for h in hits.points
                ],
            )
        )
    return results


# ---------------------------------------------------------------------------
# Main benchmark runner
# ---------------------------------------------------------------------------


def run_benchmark(models: list[dict] | None = None) -> list[ModelResult]:
    docs = _load_documents()
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    logger.info("Loaded %d documents, %d questions", len(docs), len(questions))

    model_specs = models or MODELS
    all_results: list[ModelResult] = []

    for spec in model_specs:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Model: %s", spec["hf_id"])
        logger.info("=" * 60)

        mr = ModelResult(key=spec["key"], label=spec["label"], hf_id=spec["hf_id"])

        try:
            t0 = time.perf_counter()
            st_model = SentenceTransformer(spec["hf_id"])
            mr.load_time = time.perf_counter() - t0
            logger.info("Loaded in %.1fs", mr.load_time)

            client, vector_dim, embed_time, n_chunks = _build_index(st_model, docs)
            mr.vector_dim = vector_dim
            mr.embed_time = embed_time
            mr.n_chunks = n_chunks

            mr.question_results = _run_questions(
                st_model, client, questions, spec.get("query_prompt")
            )

            logger.info(
                "Results — Recall@10=%.2f  MRR=%.3f  AvgScore=%.3f  Q5=%s",
                mr.recall_at_10,
                mr.mrr,
                mr.avg_best_score,
                "RESOLVED" if mr.q5_resolved else "still-failing",
            )

        except Exception as exc:
            mr.error = str(exc)
            logger.error("Model %s failed: %s", spec["key"], exc, exc_info=True)

        all_results.append(mr)

    return all_results


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------

_COL_W = 38  # model label column width
_NUM_W = 7   # numeric column width


def _print_report(results: list[ModelResult]) -> None:
    header = f"{'Model':<{_COL_W}} {'Dim':>5} {'R@10':>{_NUM_W}} {'MRR':>{_NUM_W}} {'AvgS':>{_NUM_W}} {'Q5':>5} {'EmbT(s)':>8}"
    sep = "─" * len(header)

    print()
    print("=" * len(header))
    print("EMBEDDING MODEL COMPARISON — Belgian Tax Semantic Search (10-Q validation set)")
    print("=" * len(header))
    print(header)
    print(sep)

    for r in results:
        if r.error:
            print(f"{r.label:<{_COL_W}} ERROR: {r.error[:60]}")
            continue
        print(
            f"{r.label:<{_COL_W}} {r.vector_dim:>5} "
            f"{r.recall_at_10:>{_NUM_W}.1%} "
            f"{r.mrr:>{_NUM_W}.3f} "
            f"{r.avg_best_score:>{_NUM_W}.3f} "
            f"{'YES':>5} " if r.q5_resolved else f"{'no':>5} ",
            end="",
        )
        print(f"{r.embed_time:>8.1f}")

    print(sep)

    # Per-question breakdown
    print()
    print("Per-question breakdown  (rank / cosine-score for primary expected doc)")
    print()

    q_col_w = 41
    cell_w = 16
    row_header = f"{'Q':>3}  {'Primary expected doc':<{q_col_w}}"
    for r in results:
        row_header += f"  {r.key:>{cell_w}}"
    print(row_header)
    print("─" * len(row_header))

    if not results or results[0].error:
        print("(no results)")
        return

    ref = results[0].question_results
    for qr in ref:
        row = f"{qr.qid:>3}  {qr.expected_docs[0]:<{q_col_w}}"
        for mr in results:
            if mr.error:
                row += f"  {'ERROR':>{cell_w}}"
                continue
            match = next((r for r in mr.question_results if r.qid == qr.qid), None)
            if match is None:
                row += f"  {'N/A':>{cell_w}}"
            elif match.primary_rank:
                cell = f"#{match.primary_rank} ({match.best_expected_score:.3f})"
                row += f"  {cell:>{cell_w}}"
            else:
                cell = f"miss ({match.best_expected_score:.3f})"
                row += f"  {cell:>{cell_w}}"
        print(row)

    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = run_benchmark()
    _print_report(results)

    # Persist raw results for the findings document
    RESULTS_JSON.write_text(
        json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Saved raw results → %s", RESULTS_JSON)
