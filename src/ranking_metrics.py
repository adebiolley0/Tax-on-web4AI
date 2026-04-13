"""Ranking metrics for semantic search evaluation.

Includes:
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (nDCG)
- Recall@K
"""

from __future__ import annotations

import math
from typing import Sequence


def reciprocal_rank(ranks: Sequence[int]) -> float:
    """Calculate reciprocal rank from a list of result ranks.

    Returns the reciprocal of the rank of the first relevant result.
    If no relevant result, returns 0.
    """
    for rank in ranks:
        if rank > 0:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(all_ranks: Sequence[Sequence[int]]) -> float:
    """Calculate Mean Reciprocal Rank (MRR) across multiple queries.

    Args:
        all_ranks: List of rank lists, one per query. Each list contains
                   the rank(s) of relevant results (1-indexed), or empty if none found.

    Returns:
        MRR score between 0 and 1.
    """
    if not all_ranks:
        return 0.0
    rrs = [reciprocal_rank(ranks) for ranks in all_ranks]
    return sum(rrs) / len(rrs)


def dcg_at_k(relevances: Sequence[float], k: int = 5) -> float:
    """Calculate Discounted Cumulative Gain @ k.

    Args:
        relevances: Sequence of relevance scores (0 or 1 for binary relevance)
        k: Cutoff rank

    Returns:
        DCG@k score
    """
    dcg = 0.0
    for i, rel in enumerate(relevances[:k], start=1):
        dcg += rel / math.log2(i + 1)
    return dcg


def ndcg_at_k(
    relevances: Sequence[float],
    k: int = 5,
    ideal_relevances: Sequence[float] | None = None,
) -> float:
    """Calculate Normalized Discounted Cumulative Gain @ k.

    Args:
        relevances: Sequence of relevance scores for retrieved results
        k: Cutoff rank
        ideal_relevances: Sequence of ideal relevance scores (for IDCG calculation).
                         If None, uses perfect ranking (all 1.0) up to k or
                         sorted relevances, whichever is appropriate.

    Returns:
        nDCG@k score between 0 and 1.
    """
    dcg = dcg_at_k(relevances, k)

    if ideal_relevances is None:
        # IDCG = DCG of ideal ranking (all 1.0 for top-k)
        # This assumes we have at least one relevant document
        num_relevant = sum(1 for r in relevances if r > 0)
        if num_relevant > 0:
            ideal_relevances = [1.0] * min(num_relevant, k)
        else:
            ideal_relevances = [1.0] * k

    idcg = dcg_at_k(ideal_relevances, k)

    if idcg == 0:
        return 0.0

    return dcg / idcg


def recall_at_k(
    relevant_found: int,
    total_relevant: int,
    k: int = 10,
) -> float:
    """Calculate Recall @ k.

    Args:
        relevant_found: Number of relevant documents found in top-k
        total_relevant: Total number of relevant documents
        k: Cutoff rank

    Returns:
        Recall@k between 0 and 1.
    """
    if total_relevant == 0:
        return 0.0
    return min(relevant_found / total_relevant, 1.0)


def mean_average_precision_at_k(
    all_precisions: Sequence[Sequence[float]],
    k: int = 10,
) -> float:
    """Calculate Mean Average Precision @ k.

    Args:
        all_precisions: List of precision@i sequences, one per query
        k: Cutoff rank

    Returns:
        MAP@k score between 0 and 1.
    """
    if not all_precisions:
        return 0.0

    aps = []
    for precisions in all_precisions:
        if not precisions:
            ap = 0.0
        else:
            ap = sum(precisions[:k]) / min(len(precisions), k)
        aps.append(ap)

    return sum(aps) / len(aps)
