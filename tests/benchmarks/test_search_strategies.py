"""Benchmark comparing Qdrant search strategies.

Uses the same validation dataset (21 documents, 21 questions) as the semantic
search tests.  Measures MRR, nDCG@5, Recall@10, MAP@10, and average top-score
for each strategy side-by-side.

Run:
    PYTHONPATH=src uv run python -m pytest tests/benchmarks/test_search_strategies.py -v -s
"""

from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from models import Document, SourceType
from ranking_metrics import mean_reciprocal_rank, ndcg_at_k
from storage.chunker import chunk_document
from storage.embedder import embed_chunks, embed_texts
from storage.qdrant_store import get_client
from storage.search import (
    ColBERTRerankStrategy,
    DenseSearchStrategy,
    GroupedSearchStrategy,
    HybridSearchStrategy,
    SearchResult,
    SearchStrategy,
)

logger = logging.getLogger(__name__)

VALIDATION_DIR = (
    Path(__file__).resolve().parent.parent.parent / "validation_dataset"
)
MD_DIR = VALIDATION_DIR / "md"
QUESTIONS_PATH = VALIDATION_DIR / "questions.json"


# ============================================================================
# Data loading helpers (mirrors test_semantic_search_validation.py)
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
# Metrics aggregation
# ============================================================================


@dataclass
class StrategyMetrics:
    """Aggregated quality metrics for one search strategy."""

    strategy_name: str = ""
    mrr: float = 0.0
    ndcg_at_5: float = 0.0
    recall_at_10: float = 0.0
    map_at_10: float = 0.0
    avg_top_score: float = 0.0
    index_time_s: float = 0.0
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

        # --- MRR ---
        rank_list: list[int] = []
        for i, doc_id in enumerate(doc_ids[:20]):
            if doc_id in expected:
                rank_list.append(i + 1)
                break
        if not rank_list:
            rank_list.append(0)
        all_ranks.append(rank_list)

        # --- nDCG@5 (deduplicate by document_id: only first chunk per doc counts) ---
        seen_docs: set[str] = set()
        relevances: list[float] = []
        for did in doc_ids[:5]:
            if did in expected and did not in seen_docs:
                relevances.append(1.0)
                seen_docs.add(did)
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

        # --- AP@10 (deduplicate by document_id: only first chunk per doc counts) ---
        seen_docs_ap: set[str] = set()
        relevant_count = 0
        precision_sum = 0.0
        for i, doc_id in enumerate(doc_ids[:10]):
            if doc_id in expected and doc_id not in seen_docs_ap:
                relevant_count += 1
                precision_sum += relevant_count / (i + 1)
                seen_docs_ap.add(doc_id)
        ap = precision_sum / max(relevant_count, 1) if relevant_count else 0.0
        ap_per_query.append(ap)

        # Per-question detail
        metrics.per_question[qid] = {
            "rank_of_expected": rank_list[0] if rank_list[0] > 0 else None,
            "top_score": hits[0].score if hits else 0.0,
            "expected_found_in_top10": bool(expected & set(doc_ids[:10])),
        }

    # Aggregate
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
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def validation_data():
    """Load docs, chunk, and embed once — shared by all strategies."""
    md_files = sorted(MD_DIR.glob("*.md"))
    assert md_files, f"No markdown documents found in {MD_DIR}"

    with ThreadPoolExecutor(max_workers=8) as pool:
        docs = list(pool.map(_load_md_document, md_files))

    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))

    embedded = embed_chunks(all_chunks)
    questions = _load_questions()

    logger.info(
        "Prepared %d docs → %d chunks → %d embedded",
        len(docs),
        len(all_chunks),
        len(embedded),
    )
    return all_chunks, embedded, questions


def _run_strategy(
    strategy: SearchStrategy,
    chunks,
    embedded,
    questions,
) -> StrategyMetrics:
    """Set up, index, search, and compute metrics for a single strategy."""
    client = get_client(in_memory=True)
    coll = f"bench_{strategy.name}"

    # Index
    t0 = time.perf_counter()
    strategy.setup_collection(client, coll)
    n = strategy.index_chunks(client, coll, chunks, embedded)
    index_time = time.perf_counter() - t0
    logger.info("[%s] indexed %d points in %.2fs", strategy.name, n, index_time)

    # Search all questions
    t0 = time.perf_counter()
    search_results: dict[str, list[SearchResult]] = {}
    for q in questions:
        hits = strategy.search(client, coll, q["question"], limit=20)
        search_results[q["id"]] = hits
    search_time = time.perf_counter() - t0
    logger.info(
        "[%s] searched %d questions in %.2fs",
        strategy.name,
        len(questions),
        search_time,
    )

    metrics = _compute_metrics(search_results, questions)
    metrics.strategy_name = strategy.name
    metrics.index_time_s = index_time
    metrics.search_time_s = search_time
    return metrics


@pytest.fixture(scope="module")
def all_strategy_metrics(validation_data):
    """Run every strategy and return dict[strategy_name → StrategyMetrics]."""
    chunks, embedded, questions = validation_data

    strategies: list[SearchStrategy] = [
        DenseSearchStrategy(),
        HybridSearchStrategy(fusion="rrf"),
        HybridSearchStrategy(fusion="dbsf"),
        ColBERTRerankStrategy(prefetch_limit=50),
        GroupedSearchStrategy(group_size=3),
    ]

    results: dict[str, StrategyMetrics] = {}
    for strategy in strategies:
        logger.info("=== Benchmarking: %s ===", strategy.name)
        try:
            metrics = _run_strategy(strategy, chunks, embedded, questions)
            results[strategy.name] = metrics
        except Exception:
            logger.exception("Strategy %s failed", strategy.name)
            pytest.fail(f"Strategy {strategy.name} raised an exception")

    return results


# ============================================================================
# Tests
# ============================================================================


class TestStrategyBenchmarks:
    """Compare search strategy quality and performance."""

    def test_all_strategies_produce_results(self, all_strategy_metrics):
        """Every strategy returns non-zero MRR and Recall."""
        for name, m in all_strategy_metrics.items():
            assert m.mrr > 0, f"{name}: MRR is zero"
            assert m.recall_at_10 > 0, f"{name}: Recall@10 is zero"

    def test_dense_baseline_minimum_quality(self, all_strategy_metrics):
        """Dense baseline meets minimum quality thresholds."""
        m = all_strategy_metrics["dense"]
        assert m.mrr >= 0.3, f"Dense MRR {m.mrr:.4f} < 0.3"
        assert m.ndcg_at_5 >= 0.3, f"Dense nDCG@5 {m.ndcg_at_5:.4f} < 0.3"
        assert m.recall_at_10 >= 0.5, f"Dense Recall@10 {m.recall_at_10:.4f} < 0.5"

    def test_hybrid_rrf_quality(self, all_strategy_metrics):
        """Hybrid RRF produces meaningful results."""
        m = all_strategy_metrics["hybrid_rrf"]
        assert m.mrr > 0, f"Hybrid RRF MRR is zero"
        assert m.recall_at_10 > 0, f"Hybrid RRF Recall@10 is zero"

    def test_hybrid_dbsf_quality(self, all_strategy_metrics):
        """Hybrid DBSF produces meaningful results."""
        m = all_strategy_metrics["hybrid_dbsf"]
        assert m.mrr > 0, f"Hybrid DBSF MRR is zero"
        assert m.recall_at_10 > 0, f"Hybrid DBSF Recall@10 is zero"

    def test_colbert_rerank_quality(self, all_strategy_metrics):
        """ColBERT rerank produces meaningful results."""
        m = all_strategy_metrics["colbert_rerank"]
        assert m.mrr > 0, f"ColBERT MRR is zero"
        assert m.recall_at_10 > 0, f"ColBERT Recall@10 is zero"

    def test_grouped_quality(self, all_strategy_metrics):
        """Grouped search produces meaningful results."""
        m = all_strategy_metrics["grouped"]
        assert m.mrr > 0, f"Grouped MRR is zero"
        assert m.recall_at_10 > 0, f"Grouped Recall@10 is zero"

    def test_print_comparison_table(self, all_strategy_metrics):
        """Print a formatted comparison table and save JSON report (always passes)."""
        header = (
            f"{'Strategy':<20} {'MRR':>8} {'nDCG@5':>8} {'R@10':>8} "
            f"{'MAP@10':>8} {'AvgScore':>8} {'Index(s)':>9} {'Search(s)':>10}"
        )
        sep = "=" * len(header)

        print(f"\n{sep}")
        print("SEARCH STRATEGY BENCHMARK RESULTS")
        print(sep)
        print(header)
        print("-" * len(header))

        for name, m in all_strategy_metrics.items():
            print(
                f"{name:<20} {m.mrr:>8.4f} {m.ndcg_at_5:>8.4f} "
                f"{m.recall_at_10:>8.4f} {m.map_at_10:>8.4f} "
                f"{m.avg_top_score:>8.4f} {m.index_time_s:>8.2f}s "
                f"{m.search_time_s:>9.2f}s"
            )

        print(sep)

        # Per-question breakdown
        print("\nPER-QUESTION DETAIL (rank of first expected doc, '—' = not found)")
        print("-" * len(header))
        q_ids = sorted(
            next(iter(all_strategy_metrics.values())).per_question.keys(),
            key=lambda x: int(x[1:]),
        )
        strat_names = list(all_strategy_metrics.keys())
        col_w = max(len(n) for n in strat_names)
        print(f"{'QID':<6}", end="")
        for sn in strat_names:
            print(f"  {sn:>{col_w}}", end="")
        print()

        for qid in q_ids:
            print(f"{qid:<6}", end="")
            for sn in strat_names:
                rank = all_strategy_metrics[sn].per_question[qid][
                    "rank_of_expected"
                ]
                val = str(rank) if rank is not None else "—"
                print(f"  {val:>{col_w}}", end="")
            print()

        print(sep)

        # Save JSON report
        report = {
            name: {
                "mrr": round(m.mrr, 4),
                "ndcg_at_5": round(m.ndcg_at_5, 4),
                "recall_at_10": round(m.recall_at_10, 4),
                "map_at_10": round(m.map_at_10, 4),
                "avg_top_score": round(m.avg_top_score, 4),
                "index_time_s": round(m.index_time_s, 3),
                "search_time_s": round(m.search_time_s, 3),
                "per_question": m.per_question,
            }
            for name, m in all_strategy_metrics.items()
        }
        report_path = VALIDATION_DIR / "benchmark_results.json"
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Wrote benchmark results to %s", report_path)
