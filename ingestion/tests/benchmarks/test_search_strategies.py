"""Benchmark comparing Qdrant search strategies via grid search.

Uses the same validation dataset (21 documents, 21 questions) as the semantic
search tests.  For each model in EMBEDDING_MODELS the benchmark:

  1. Indexes all validation documents into a fresh in-memory Qdrant collection
     (dense + sparse + ColBERT vectors sized to that model's dimension).
  2. Runs every pipeline configuration produced by ``generate_grid_configs``
     (~30 configurations).
  3. Computes MRR, nDCG@5, Recall@10, MAP@10, and wall-clock time.
  4. Emits a per-model leaderboard and a cross-model summary.

Adding a new model
------------------
Append an ``EmbeddingModelSpec`` entry to the ``EMBEDDING_MODELS`` list at the
top of this file.  Models whose weights are not locally cached are skipped
automatically at runtime — there is no need to comment them out.

Run:
    PYTHONPATH=src uv run python -m pytest tests/benchmarks/test_search_strategies.py -v -s
"""

from __future__ import annotations

import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from sentence_transformers import SentenceTransformer

from tax_search.models import Document, SourceType
from tax_ingestion.ranking_metrics import mean_reciprocal_rank, ndcg_at_k
from tax_ingestion.storage.chunker import chunk_document
from tax_search.embedder import embed_chunks_with, embed_texts_with, get_model_by_name
from tax_search.qdrant_store import get_client
from tax_search.search import (
    FullVectorStore,
    PipelineConfig,
    SearchResult,
    SpladeSparseEncoder,
    _encode_token_embeddings,
    execute_pipeline,
    generate_grid_configs,
)

logger = logging.getLogger(__name__)


def _step(msg: str) -> None:
    """Write a timestamped step marker to stderr — visible even under pytest capture."""
    ts = time.strftime("%H:%M:%S")
    sys.stderr.write(f"[{ts}] BENCH: {msg}\n")
    sys.stderr.flush()

VALIDATION_DIR = (
    Path(__file__).resolve().parent.parent.parent / "validation_dataset"
)
MD_DIR = VALIDATION_DIR / "md"
QUESTIONS_PATH = VALIDATION_DIR / "questions.json"


# ============================================================================
# Embedding model registry
# ============================================================================


@dataclass
class EmbeddingModelSpec:
    """Configuration for one embedding model in the benchmark.

    Add entries to ``EMBEDDING_MODELS`` to include additional models.
    Models whose weights are not locally cached are skipped automatically.
    """

    key: str
    """Short identifier used in collection names and report keys."""

    hf_id: str
    """HuggingFace model ID passed to ``SentenceTransformer``."""

    label: str
    """Human-readable label for reports."""

    query_prompt: str | None = None
    """Optional query-side prompt name (e.g. ``"query"`` for BGE-M3 models)."""


#: All models to evaluate.  Order determines the "baseline" (first entry).
#: Models that are not downloaded locally are skipped with a warning.
EMBEDDING_MODELS: list[EmbeddingModelSpec] = [
    EmbeddingModelSpec(
        key="minilm",
        hf_id="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        label="MiniLM-L12 v2 (baseline, 384D)",
    ),
    # Commented out for local runs — too large to download in CI/testing:
    # EmbeddingModelSpec(
    #     key="bge_m3",
    #     hf_id="BAAI/bge-m3",
    #     label="BGE-M3 (1024D)",
    #     query_prompt="query",
    # ),
    # EmbeddingModelSpec(
    #     key="modernbert_be",
    #     hf_id="Parallia/Fairly-Multilingual-ModernBERT-Embed-BE",
    #     label="Fairly-Multilingual-ModernBERT-BE (768D)",
    # ),
]


# ============================================================================
# Data loading helpers
# ============================================================================


def _load_md_document(md_path: Path) -> Document:
    text = md_path.read_text(encoding="utf-8")
    short_name = md_path.stem
    return Document(
        source_url=f"fisconet://{short_name}",
        source_domain="minfin.fgov.be",
        source_type=SourceType.FISCONET_DOCUMENT,
        document_id=short_name,
        title=short_name,
        language="fr",
        content_text=text,
    )


def _load_questions() -> list[dict]:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


# ============================================================================
# Metrics
# ============================================================================


@dataclass
class StrategyMetrics:
    """Aggregated quality metrics for one search pipeline configuration."""

    strategy_name: str = ""
    mrr: float = 0.0
    ndcg_at_5: float = 0.0
    recall_at_10: float = 0.0
    map_at_10: float = 0.0
    avg_top_score: float = 0.0
    search_time_s: float = 0.0
    per_question: dict = field(default_factory=dict)


def _compute_metrics(
    search_results: dict[str, list[SearchResult]],
    questions: list[dict],
) -> StrategyMetrics:
    """Compute ranking metrics from search results against ground truth."""
    metrics = StrategyMetrics()

    all_ranks: list[list[int]] = []
    ndcg_scores: list[float] = []
    recall_hits = 0
    recall_scorable = 0
    top_scores: list[float] = []
    ap_per_query: list[float] = []

    for q in questions:
        qid = q["id"]
        expected = set(q["expected_docs"])
        secondary = set(q.get("secondary_docs", []))
        all_relevant = expected | secondary

        hits = search_results.get(qid, [])
        doc_ids = [h.payload.get("document_id", "") for h in hits]

        # --- MRR (first expected doc found) ---
        rank_list: list[int] = []
        for i, doc_id in enumerate(doc_ids[:20]):
            if doc_id in expected:
                rank_list.append(i + 1)
                break
        if not rank_list:
            rank_list.append(0)
        all_ranks.append(rank_list)

        # --- nDCG@5 (deduplicate by document_id) ---
        seen: set[str] = set()
        relevances: list[float] = []
        for did in doc_ids[:5]:
            if did in expected and did not in seen:
                relevances.append(1.0)
                seen.add(did)
            else:
                relevances.append(0.0)
        while len(relevances) < 5:
            relevances.append(0.0)
        num_rel = min(len(expected), 5)
        ideal = [1.0] * num_rel
        ndcg_scores.append(ndcg_at_k(relevances, k=5, ideal_relevances=ideal))

        # --- Recall@10 ---
        if expected:
            recall_scorable += 1
            if expected & set(doc_ids[:10]):
                recall_hits += 1

        # --- Best-match score ---
        for h in hits[:20]:
            if h.payload.get("document_id", "") in all_relevant:
                top_scores.append(h.score)
                break

        # --- AP@10 (deduplicate by document_id) ---
        seen_ap: set[str] = set()
        relevant_count = 0
        precision_sum = 0.0
        for i, doc_id in enumerate(doc_ids[:10]):
            if doc_id in expected and doc_id not in seen_ap:
                relevant_count += 1
                precision_sum += relevant_count / (i + 1)
                seen_ap.add(doc_id)
        ap = (
            precision_sum / max(relevant_count, 1) if relevant_count else 0.0
        )
        ap_per_query.append(ap)

        metrics.per_question[qid] = {
            "rank_of_expected": rank_list[0] if rank_list[0] > 0 else None,
            "top_score": hits[0].score if hits else 0.0,
            "expected_found_in_top10": bool(expected & set(doc_ids[:10])),
        }

    metrics.mrr = mean_reciprocal_rank(all_ranks)
    metrics.ndcg_at_5 = (
        sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
    )
    metrics.recall_at_10 = (
        recall_hits / recall_scorable if recall_scorable else 0.0
    )
    metrics.map_at_10 = (
        sum(ap_per_query) / len(ap_per_query) if ap_per_query else 0.0
    )
    metrics.avg_top_score = (
        sum(top_scores) / len(top_scores) if top_scores else 0.0
    )
    return metrics


# ============================================================================
# Core benchmark runner (model-agnostic)
# ============================================================================


def _run_model_benchmark(
    spec: EmbeddingModelSpec,
    model: SentenceTransformer,
    docs: list[Document],
    questions: list[dict],
) -> dict[str, StrategyMetrics]:
    """Run the full grid benchmark for one embedding model.

    Creates a fresh in-memory Qdrant collection sized to *model*'s output
    dimension, indexes all *docs*, pre-computes query vectors, then evaluates
    every configuration returned by ``generate_grid_configs``.

    Returns ``dict[config_name → StrategyMetrics]``, sorted by MRR descending.
    Models that are not downloaded will raise before this function is called;
    errors inside individual pipeline configurations are caught and logged so
    that one broken config does not abort the entire run.
    """
    # --- Chunk and embed documents -----------------------------------------
    _step(f"[{spec.key}] chunking {len(docs)} docs")
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    _step(f"[{spec.key}] {len(all_chunks)} chunks — embedding (dense)")

    t0 = time.perf_counter()
    embedded = embed_chunks_with(model, all_chunks)
    _step(f"[{spec.key}] dense embedding done in {time.perf_counter()-t0:.1f}s")

    # Infer vector dimension from the first embedded chunk
    vector_size = len(embedded[0].vector) if embedded else 384

    # --- Build in-memory Qdrant collection ---------------------------------
    collection_name = f"bench_{spec.key}"
    client = get_client(in_memory=True)
    store = FullVectorStore()
    store.setup_collection(client, collection_name, vector_size=vector_size)

    _step(f"[{spec.key}] index_chunks: BM25 + SPLADE + ColBERT for {len(all_chunks)} chunks")
    t0 = time.perf_counter()
    n = store.index_chunks(
        client, collection_name, all_chunks, embedded, model=model
    )
    _step(f"[{spec.key}] index_chunks done — {n} points in {time.perf_counter()-t0:.1f}s")
    logger.info(
        "[%s] Indexed %d points (dim=%d) into %s",
        spec.key, n, vector_size, collection_name,
    )

    # --- Pre-compute query representations ---------------------------------
    q_texts = [q["question"] for q in questions]
    _step(f"[{spec.key}] encoding {len(q_texts)} query vectors")
    dense_vecs = embed_texts_with(model, q_texts, prompt_name=spec.query_prompt)
    bm25_sparse_vecs = [store.bm25.encode(t) for t in q_texts]
    _step(f"[{spec.key}] SPLADE query encoding")
    splade_sparse_vecs = [store.splade.encode(t) for t in q_texts]
    sparse_vecs_list = [
        {"bm25": b, "splade": s}
        for b, s in zip(bm25_sparse_vecs, splade_sparse_vecs)
    ]
    colbert_vecs = _encode_token_embeddings(q_texts, model=model)
    _step(f"[{spec.key}] all query vectors ready")
    precomputed = list(zip(questions, dense_vecs, sparse_vecs_list, colbert_vecs))

    # --- Run every pipeline configuration ----------------------------------
    configs = generate_grid_configs()
    results: dict[str, StrategyMetrics] = {}
    _step(f"[{spec.key}] running {len(configs)} pipeline configs")

    for i, cfg in enumerate(configs, 1):
        _step(f"[{spec.key}] [{i}/{len(configs)}] {cfg.name}")
        t0 = time.perf_counter()
        search_results: dict[str, list[SearchResult]] = {}

        for q, dense_v, sparse_v_dict, colbert_v in precomputed:
            try:
                hits = execute_pipeline(
                    cfg,
                    client,
                    collection_name,
                    dense_vec=dense_v,
                    sparse_vecs=sparse_v_dict,
                    colbert_tokens=colbert_v,
                    limit=20,
                )
            except Exception as exc:
                logger.error(
                    "[%s][%s] Q%s failed: %s", spec.key, cfg.name, q["id"], exc
                )
                hits = []
            search_results[q["id"]] = hits

        elapsed = time.perf_counter() - t0
        metrics = _compute_metrics(search_results, questions)
        metrics.strategy_name = cfg.name
        metrics.search_time_s = elapsed
        results[cfg.name] = metrics

    # Sort by MRR descending
    return dict(sorted(results.items(), key=lambda kv: kv[1].mrr, reverse=True))


# ============================================================================
# Shared document / question fixture (module scope)
# ============================================================================


@pytest.fixture(scope="module")
def docs_and_questions():
    """Load all validation documents and questions once per module."""
    md_files = sorted(MD_DIR.glob("*.md"))
    assert md_files, f"No markdown documents found in {MD_DIR}"
    with ThreadPoolExecutor(max_workers=8) as pool:
        docs = list(pool.map(_load_md_document, md_files))
    questions = _load_questions()
    return docs, questions


# ============================================================================
# Baseline model fixtures (module scope — fast, always available)
# ============================================================================

_BASELINE_SPEC = EMBEDDING_MODELS[0]


@pytest.fixture(scope="module")
def indexed_store(docs_and_questions):
    """Index all validation docs with the baseline model.

    Returns (client, store, chunks, embedded, questions).
    """
    docs, questions = docs_and_questions
    _step(f"indexed_store: loading model '{_BASELINE_SPEC.hf_id}'")
    model = get_model_by_name(_BASELINE_SPEC.hf_id)

    _step(f"indexed_store: chunking {len(docs)} docs")
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    _step(f"indexed_store: {len(all_chunks)} chunks produced")

    _step("indexed_store: embedding chunks (dense)")
    t0 = time.perf_counter()
    embedded = embed_chunks_with(model, all_chunks)
    _step(f"indexed_store: dense embedding done in {time.perf_counter()-t0:.1f}s")

    vector_size = len(embedded[0].vector) if embedded else 384

    _step("indexed_store: setting up Qdrant collection")
    client = get_client(in_memory=True)
    store = FullVectorStore()
    store.setup_collection(client, f"bench_{_BASELINE_SPEC.key}", vector_size=vector_size)

    _step("indexed_store: calling index_chunks (BM25 + SPLADE + ColBERT)")
    t0 = time.perf_counter()
    n = store.index_chunks(
        client, f"bench_{_BASELINE_SPEC.key}", all_chunks, embedded, model=model
    )
    _step(
        f"indexed_store: index_chunks done — {n} points in "
        f"{time.perf_counter()-t0:.1f}s"
    )
    logger.info(
        "Baseline: indexed %d points (%d docs, %d chunks)",
        n, len(docs), len(all_chunks),
    )
    return client, store, all_chunks, embedded, questions


@pytest.fixture(scope="module")
def precomputed_queries(indexed_store):
    """Pre-compute all query representations (dense, sparse BM25+SPLADE, ColBERT) once."""
    _, store, _, _, questions = indexed_store
    model = get_model_by_name(_BASELINE_SPEC.hf_id)
    q_texts = [q["question"] for q in questions]
    _step(f"precomputed_queries: encoding {len(q_texts)} queries")

    _step("precomputed_queries: dense encoding")
    dense_vecs = embed_texts_with(model, q_texts, prompt_name=_BASELINE_SPEC.query_prompt)

    _step("precomputed_queries: BM25 encoding")
    bm25_sparse_vecs = [store.bm25.encode(t) for t in q_texts]

    _step("precomputed_queries: SPLADE encoding (reuses cached model)")
    t0 = time.perf_counter()
    splade_sparse_vecs = [store.splade.encode(t) for t in q_texts]
    _step(f"precomputed_queries: SPLADE done in {time.perf_counter()-t0:.1f}s")

    _step("precomputed_queries: ColBERT encoding")
    colbert_vecs = _encode_token_embeddings(q_texts, model=model)
    _step("precomputed_queries: all query vectors ready")

    # Each entry: (question, dense_vec, {"bm25": ..., "splade": ...}, colbert_vec)
    return list(zip(
        questions,
        dense_vecs,
        [{"bm25": b, "splade": s} for b, s in zip(bm25_sparse_vecs, splade_sparse_vecs)],
        colbert_vecs,
    ))


@pytest.fixture(scope="module")
def grid_results(indexed_store, precomputed_queries):
    """Run every pipeline config against the baseline model.

    Returns ``dict[config_name → StrategyMetrics]``, sorted by MRR descending.
    """
    client, store, chunks, embedded, questions = indexed_store
    collection_name = f"bench_{_BASELINE_SPEC.key}"
    configs = generate_grid_configs()
    _step(f"grid_results: running {len(configs)} pipeline configs")

    results: dict[str, StrategyMetrics] = {}

    for i, cfg in enumerate(configs, 1):
        _step(f"grid_results: [{i}/{len(configs)}] {cfg.name}")
        t0 = time.perf_counter()
        search_results: dict[str, list[SearchResult]] = {}

        for q, dense_v, sparse_v_dict, colbert_v in precomputed_queries:
            try:
                hits = execute_pipeline(
                    cfg,
                    client,
                    collection_name,
                    dense_vec=dense_v,
                    sparse_vecs=sparse_v_dict,
                    colbert_tokens=colbert_v,
                    limit=20,
                )
            except Exception as exc:
                logger.error("[%s] Q%s failed: %s", cfg.name, q["id"], exc)
                hits = []
            search_results[q["id"]] = hits

        elapsed = time.perf_counter() - t0
        metrics = _compute_metrics(search_results, questions)
        metrics.strategy_name = cfg.name
        metrics.search_time_s = elapsed
        results[cfg.name] = metrics

    return dict(
        sorted(results.items(), key=lambda kv: kv[1].mrr, reverse=True)
    )


# ============================================================================
# Multi-model fixture (session scope — may load large models)
# ============================================================================


@pytest.fixture(scope="session")
def all_model_grid_results():
    """Run the full grid benchmark for every model in EMBEDDING_MODELS.

    Models whose weights are not locally cached are skipped with a warning
    rather than failing the session.  The fixture always returns at least the
    baseline result.

    Returns ``dict[model_key → dict[config_name → StrategyMetrics]]``.
    """
    md_files = sorted(MD_DIR.glob("*.md"))
    assert md_files, f"No markdown documents found in {MD_DIR}"
    with ThreadPoolExecutor(max_workers=8) as pool:
        docs = list(pool.map(_load_md_document, md_files))
    questions = _load_questions()

    all_results: dict[str, dict[str, StrategyMetrics]] = {}

    _step(f"all_model_grid_results: {len(EMBEDDING_MODELS)} model(s) to benchmark")
    for spec in EMBEDDING_MODELS:
        _step(f"all_model_grid_results: loading '{spec.hf_id}'")
        logger.info("=" * 60)
        logger.info("Benchmarking model: %s (%s)", spec.label, spec.hf_id)
        logger.info("=" * 60)
        try:
            model = get_model_by_name(spec.hf_id)
        except Exception as exc:
            logger.warning(
                "Skipping model %s — could not load (%s: %s). "
                "Download the model weights to include it in the benchmark.",
                spec.hf_id,
                type(exc).__name__,
                exc,
            )
            _step(f"all_model_grid_results: SKIPPED '{spec.hf_id}' — {exc}")
            continue

        try:
            _step(f"all_model_grid_results: running full benchmark for '{spec.key}'")
            model_results = _run_model_benchmark(spec, model, docs, questions)
            all_results[spec.key] = model_results
            best_name, best_m = next(iter(model_results.items()))
            _step(
                f"all_model_grid_results: '{spec.key}' done — "
                f"best={best_name} MRR={best_m.mrr:.4f}"
            )
            logger.info(
                "[%s] Best strategy: %s  MRR=%.4f  R@10=%.4f",
                spec.key, best_name, best_m.mrr, best_m.recall_at_10,
            )
        except Exception as exc:
            logger.error(
                "Benchmark run failed for model %s: %s", spec.hf_id, exc,
                exc_info=True,
            )
            _step(f"all_model_grid_results: ERROR for '{spec.key}' — {exc}")

    assert all_results, "No models could be benchmarked — check EMBEDDING_MODELS"
    return all_results


# ============================================================================
# Leaderboard helpers
# ============================================================================


def _print_strategy_leaderboard(
    model_label: str,
    results: dict[str, StrategyMetrics],
) -> None:
    """Print a ranked table of pipeline configurations for one model."""
    col_w = max(len(n) for n in results) + 2
    header = (
        f"{'#':<4}{'Strategy':<{col_w}} {'MRR':>7} {'nDCG@5':>7} "
        f"{'R@10':>7} {'MAP@10':>7} {'Time(s)':>8}"
    )
    sep = "=" * len(header)

    print(f"\n{sep}")
    print(f"GRID SEARCH LEADERBOARD — {model_label}")
    print(sep)
    print(header)
    print("-" * len(header))

    for rank, (name, m) in enumerate(results.items(), 1):
        print(
            f"{rank:<4}{name:<{col_w}} {m.mrr:>7.4f} {m.ndcg_at_5:>7.4f} "
            f"{m.recall_at_10:>7.4f} {m.map_at_10:>7.4f} "
            f"{m.search_time_s:>7.2f}s"
        )

    print(sep)

    top5 = list(results.items())[:5]
    print(f"\nTOP 5 STRATEGIES ({model_label}):")
    for rank, (name, m) in enumerate(top5, 1):
        print(
            f"  {rank}. {name}  "
            f"(MRR={m.mrr:.4f}, R@10={m.recall_at_10:.4f}, "
            f"nDCG@5={m.ndcg_at_5:.4f})"
        )

    # Per-question breakdown for top-5
    top5_names = [n for n, _ in top5]
    tw = max(len(n) for n in top5_names)
    print(f"\nPER-QUESTION RANKS (top-5 strategies, '—' = not found)")
    print("-" * len(header))
    print(f"{'QID':<6}", end="")
    for n in top5_names:
        print(f"  {n:>{tw}}", end="")
    print()

    q_ids = sorted(
        next(iter(results.values())).per_question.keys(),
        key=lambda x: int(x[1:]),
    )
    for qid in q_ids:
        print(f"{qid:<6}", end="")
        for n in top5_names:
            rank_val = results[n].per_question[qid]["rank_of_expected"]
            val = str(rank_val) if rank_val is not None else "—"
            print(f"  {val:>{tw}}", end="")
        print()

    print(sep)


# ============================================================================
# Tests — baseline grid search
# ============================================================================


class TestGridSearch:
    """Grid search over all pipeline configurations for the baseline model."""

    def test_all_configs_produce_results(self, grid_results):
        """Every config returns at least some non-zero metrics."""
        failed = [n for n, m in grid_results.items() if m.mrr == 0]
        assert not failed, f"Configs with zero MRR: {failed}"

    def test_dense_baseline_quality(self, grid_results):
        """Dense-only baseline meets minimum thresholds."""
        m = grid_results["dense"]
        assert m.mrr >= 0.3, f"Dense MRR {m.mrr:.4f} < 0.3"
        assert m.recall_at_10 >= 0.5, f"Dense R@10 {m.recall_at_10:.4f} < 0.5"

    def test_at_least_one_strategy_beats_dense(self, grid_results):
        """At least one non-dense config improves over the dense baseline."""
        dense_mrr = grid_results["dense"].mrr
        better = [
            n
            for n, m in grid_results.items()
            if n != "dense" and m.mrr > dense_mrr
        ]
        assert better, (
            f"No strategy beat dense baseline MRR={dense_mrr:.4f}"
        )

    def test_print_leaderboard(self, grid_results):
        """Print the full baseline leaderboard sorted by MRR (always passes)."""
        _print_strategy_leaderboard(_BASELINE_SPEC.label, grid_results)

        # Save full JSON report
        report = {
            name: {
                "mrr": round(m.mrr, 4),
                "ndcg_at_5": round(m.ndcg_at_5, 4),
                "recall_at_10": round(m.recall_at_10, 4),
                "map_at_10": round(m.map_at_10, 4),
                "avg_top_score": round(m.avg_top_score, 4),
                "search_time_s": round(m.search_time_s, 3),
                "per_question": m.per_question,
            }
            for name, m in grid_results.items()
        }
        report_path = VALIDATION_DIR / "benchmark_results.json"
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Wrote baseline benchmark results to %s", report_path)


# ============================================================================
# Tests — cross-model comparison
# ============================================================================


@pytest.mark.skipif(
    len(EMBEDDING_MODELS) < 2,
    reason="Cross-model comparison requires at least 2 models in EMBEDDING_MODELS",
)
class TestEmbeddingModelComparison:
    """Compare all available embedding models on the full grid benchmark.

    Models listed in EMBEDDING_MODELS that are not locally cached are skipped
    automatically — only the results for successfully loaded models are shown.
    Skipped entirely when only one model is configured (no comparison to make).
    """

    def test_all_available_models_produce_results(self, all_model_grid_results):
        """Every successfully loaded model returns non-zero MRR."""
        failures = []
        for model_key, strategies in all_model_grid_results.items():
            baseline_mrr = strategies.get("dense", StrategyMetrics()).mrr
            if baseline_mrr == 0:
                failures.append(model_key)
        assert not failures, (
            f"Dense baseline had zero MRR for models: {failures}"
        )

    def test_print_per_model_leaderboards(self, all_model_grid_results):
        """Print a strategy leaderboard for each available model (always passes)."""
        spec_by_key = {s.key: s for s in EMBEDDING_MODELS}
        for model_key, strategies in all_model_grid_results.items():
            label = spec_by_key.get(model_key, EmbeddingModelSpec(
                key=model_key, hf_id=model_key, label=model_key
            )).label
            _print_strategy_leaderboard(label, strategies)

    def test_print_cross_model_summary(self, all_model_grid_results):
        """Print a compact cross-model × best-strategy summary (always passes).

        For each model, shows the best-performing strategy and the dense
        baseline, making it easy to compare models at a glance.
        """
        spec_by_key = {s.key: s for s in EMBEDDING_MODELS}

        col_model = 42
        col_strat = 28
        header = (
            f"{'Model':<{col_model}} {'BestStrategy':<{col_strat}}"
            f" {'MRR':>7} {'nDCG@5':>7} {'R@10':>7} {'MAP@10':>7}"
            f"  │  {'Dense-MRR':>9} {'Dense-R@10':>10}"
        )
        sep = "=" * len(header)

        print(f"\n{sep}")
        print("CROSS-MODEL SUMMARY  (best strategy + dense baseline per model)")
        print(sep)
        print(header)
        print("-" * len(header))

        for model_key, strategies in all_model_grid_results.items():
            label = spec_by_key.get(model_key, EmbeddingModelSpec(
                key=model_key, hf_id=model_key, label=model_key
            )).label
            best_name, best_m = next(iter(strategies.items()))
            dense_m = strategies.get("dense", StrategyMetrics())
            print(
                f"{label:<{col_model}} {best_name:<{col_strat}}"
                f" {best_m.mrr:>7.4f} {best_m.ndcg_at_5:>7.4f}"
                f" {best_m.recall_at_10:>7.4f} {best_m.map_at_10:>7.4f}"
                f"  │  {dense_m.mrr:>9.4f} {dense_m.recall_at_10:>10.4f}"
            )

        print(sep)

        # Identify best overall (by MRR of their best strategy)
        best_model_key = max(
            all_model_grid_results,
            key=lambda k: next(iter(all_model_grid_results[k].values())).mrr,
        )
        best_strat, best_overall = next(
            iter(all_model_grid_results[best_model_key].items())
        )
        best_label = spec_by_key.get(best_model_key, EmbeddingModelSpec(
            key=best_model_key, hf_id=best_model_key, label=best_model_key
        )).label
        print(
            f"\nBEST OVERALL: {best_label} / {best_strat}"
            f"  MRR={best_overall.mrr:.4f}  R@10={best_overall.recall_at_10:.4f}"
        )
        print(sep)

        # Persist full comparison report
        report = {}
        for model_key, strategies in all_model_grid_results.items():
            report[model_key] = {
                name: {
                    "mrr": round(m.mrr, 4),
                    "ndcg_at_5": round(m.ndcg_at_5, 4),
                    "recall_at_10": round(m.recall_at_10, 4),
                    "map_at_10": round(m.map_at_10, 4),
                    "avg_top_score": round(m.avg_top_score, 4),
                    "search_time_s": round(m.search_time_s, 3),
                }
                for name, m in strategies.items()
            }
        report_path = VALIDATION_DIR / "embedding_model_comparison.json"
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Wrote cross-model comparison to %s", report_path)
