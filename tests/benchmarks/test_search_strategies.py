"""Benchmark comparing Qdrant search strategies via grid search.

Uses the same validation dataset (21 documents, 21 questions) as the semantic
search tests.  Indexes once into a single full-vector collection (dense +
sparse + ColBERT), then runs ~30 pipeline configurations and compares
MRR, nDCG@5, Recall@10, MAP@10, and timing.

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
    FullVectorStore,
    PipelineConfig,
    SearchResult,
    execute_pipeline,
    generate_grid_configs,
    _encode_token_embeddings,
)

logger = logging.getLogger(__name__)

VALIDATION_DIR = (
    Path(__file__).resolve().parent.parent.parent / "validation_dataset"
)
MD_DIR = VALIDATION_DIR / "md"
QUESTIONS_PATH = VALIDATION_DIR / "questions.json"

COLLECTION_NAME = "bench_grid"


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
        ndcg_scores.append(
            ndcg_at_k(relevances, k=5, ideal_relevances=ideal)
        )

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
            precision_sum / max(relevant_count, 1)
            if relevant_count
            else 0.0
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
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def indexed_store():
    """Create one full-vector collection and index all validation documents.

    Returns (client, store, chunks, embedded, questions).
    """
    md_files = sorted(MD_DIR.glob("*.md"))
    assert md_files, f"No markdown documents found in {MD_DIR}"

    with ThreadPoolExecutor(max_workers=8) as pool:
        docs = list(pool.map(_load_md_document, md_files))

    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))

    embedded = embed_chunks(all_chunks)
    questions = _load_questions()

    client = get_client(in_memory=True)
    store = FullVectorStore()
    store.setup_collection(client, COLLECTION_NAME)
    n = store.index_chunks(client, COLLECTION_NAME, all_chunks, embedded)
    logger.info(
        "Indexed %d points (%d docs, %d chunks) into %s",
        n,
        len(docs),
        len(all_chunks),
        COLLECTION_NAME,
    )
    return client, store, all_chunks, embedded, questions


@pytest.fixture(scope="module")
def precomputed_queries(indexed_store):
    """Pre-compute all query representations (dense, sparse, ColBERT) once."""
    _, store, _, _, questions = indexed_store
    q_texts = [q["question"] for q in questions]

    dense_vecs = embed_texts(q_texts)
    sparse_vecs = [store.bm25.encode(t) for t in q_texts]
    colbert_vecs = _encode_token_embeddings(q_texts)

    return list(zip(questions, dense_vecs, sparse_vecs, colbert_vecs))


@pytest.fixture(scope="module")
def grid_results(indexed_store, precomputed_queries):
    """Run every pipeline configuration and collect metrics.

    Returns dict[config_name → StrategyMetrics], ordered by MRR descending.
    """
    client, store, chunks, embedded, questions = indexed_store
    configs = generate_grid_configs()

    results: dict[str, StrategyMetrics] = {}

    for cfg in configs:
        t0 = time.perf_counter()
        search_results: dict[str, list[SearchResult]] = {}

        for q, dense_v, sparse_v, colbert_v in precomputed_queries:
            try:
                hits = execute_pipeline(
                    cfg,
                    client,
                    COLLECTION_NAME,
                    dense_vec=dense_v,
                    sparse_vec=sparse_v,
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

    # Sort by MRR descending
    results = dict(
        sorted(results.items(), key=lambda kv: kv[1].mrr, reverse=True)
    )
    return results


# ============================================================================
# Tests
# ============================================================================


class TestGridSearch:
    """Grid search over all pipeline configurations."""

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
        """Print the full leaderboard sorted by MRR (always passes)."""
        col_w = max(len(n) for n in grid_results) + 2
        header = (
            f"{'#':<4}{'Strategy':<{col_w}} {'MRR':>7} {'nDCG@5':>7} "
            f"{'R@10':>7} {'MAP@10':>7} {'Time(s)':>8}"
        )
        sep = "=" * len(header)

        print(f"\n{sep}")
        print("GRID SEARCH LEADERBOARD (sorted by MRR)")
        print(sep)
        print(header)
        print("-" * len(header))

        for rank, (name, m) in enumerate(grid_results.items(), 1):
            print(
                f"{rank:<4}{name:<{col_w}} {m.mrr:>7.4f} {m.ndcg_at_5:>7.4f} "
                f"{m.recall_at_10:>7.4f} {m.map_at_10:>7.4f} "
                f"{m.search_time_s:>7.2f}s"
            )

        print(sep)

        # Top-5 summary
        top5 = list(grid_results.items())[:5]
        print("\nTOP 5 STRATEGIES:")
        for rank, (name, m) in enumerate(top5, 1):
            print(
                f"  {rank}. {name}  "
                f"(MRR={m.mrr:.4f}, R@10={m.recall_at_10:.4f}, "
                f"nDCG@5={m.ndcg_at_5:.4f})"
            )

        # Per-question breakdown for top-5
        print(f"\nPER-QUESTION RANKS (top-5 strategies, '—' = not found)")
        print("-" * len(header))
        top5_names = [n for n, _ in top5]
        tw = max(len(n) for n in top5_names)
        print(f"{'QID':<6}", end="")
        for n in top5_names:
            print(f"  {n:>{tw}}", end="")
        print()

        q_ids = sorted(
            next(iter(grid_results.values())).per_question.keys(),
            key=lambda x: int(x[1:]),
        )
        for qid in q_ids:
            print(f"{qid:<6}", end="")
            for n in top5_names:
                rank = grid_results[n].per_question[qid]["rank_of_expected"]
                val = str(rank) if rank is not None else "—"
                print(f"  {val:>{tw}}", end="")
            print()
        print(sep)

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
        logger.info("Wrote benchmark results to %s", report_path)
