"""
Deterministic Retrieval Metrics for FFIRE Evidence Ranking Evaluation.

Computes mathematically rigorous ranking metrics:
- Precision@k
- Recall@k
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (nDCG@k)
"""

import math
from typing import Sequence, Set, Any, Union, List


def precision_at_k(retrieved: Sequence[str], relevant: Union[Set[str], Sequence[str]], k: int) -> float:
    """
    Computes Precision@k: fraction of top-k retrieved items that are relevant.
    Formula: |Retrieved[:k] ∩ Relevant| / k
    """
    if k <= 0:
        return 0.0
    rel_set = set(relevant)
    if not rel_set:
        return 0.0

    retrieved_k = list(retrieved)[:k]
    hits = sum(1 for item in retrieved_k if item in rel_set)
    return round(hits / k, 4)


def recall_at_k(retrieved: Sequence[str], relevant: Union[Set[str], Sequence[str]], k: int) -> float:
    """
    Computes Recall@k: fraction of all relevant items retrieved in top-k.
    Formula: |Retrieved[:k] ∩ Relevant| / |Relevant|
    """
    if k <= 0:
        return 0.0
    rel_set = set(relevant)
    if not rel_set:
        # If no relevant items exist, empty retrieval is considered 1.0 (correct abstention)
        return 1.0 if len(retrieved) == 0 else 0.0

    retrieved_k = list(retrieved)[:k]
    hits = sum(1 for item in retrieved_k if item in rel_set)
    return round(hits / len(rel_set), 4)


def mean_reciprocal_rank(retrieved: Sequence[str], relevant: Union[Set[str], Sequence[str]]) -> float:
    """
    Computes Reciprocal Rank for a single query (MRR is the average across queries).
    Formula: 1 / rank_of_first_relevant_item (1-indexed). Returns 0.0 if no hits.
    """
    rel_set = set(relevant)
    if not rel_set:
        return 0.0

    for idx, item in enumerate(retrieved, start=1):
        if item in rel_set:
            return round(1.0 / idx, 4)
    return 0.0


def dcg_at_k(retrieved: Sequence[str], relevant: Union[Set[str], Sequence[str]], k: int) -> float:
    """Computes Discounted Cumulative Gain at k using binary relevance."""
    if k <= 0:
        return 0.0
    rel_set = set(relevant)
    dcg = 0.0
    for idx, item in enumerate(list(retrieved)[:k], start=1):
        if item in rel_set:
            dcg += 1.0 / math.log2(idx + 1)
    return dcg


def ndcg_at_k(retrieved: Sequence[str], relevant: Union[Set[str], Sequence[str]], k: int) -> float:
    """
    Computes Normalized Discounted Cumulative Gain at k.
    Formula: DCG@k / IDCG@k
    """
    if k <= 0:
        return 0.0
    rel_set = set(relevant)
    if not rel_set:
        return 1.0 if len(retrieved) == 0 else 0.0

    actual_dcg = dcg_at_k(retrieved, rel_set, k)

    # Compute Ideal DCG (all relevant items ranked at the top)
    ideal_hits = min(k, len(rel_set))
    idcg = sum(1.0 / math.log2(idx + 1) for idx in range(1, ideal_hits + 1))

    if idcg == 0.0:
        return 0.0

    return round(actual_dcg / idcg, 4)


def evaluate_query_retrieval(
    retrieved: Sequence[str],
    relevant: Union[Set[str], Sequence[str]],
    k_values: List[int] = [1, 3, 5]
) -> dict:
    """Evaluates all retrieval metrics across specified k values."""
    results = {
        "mrr": mean_reciprocal_rank(retrieved, relevant),
    }
    for k in k_values:
        results[f"precision@{k}"] = precision_at_k(retrieved, relevant, k)
        results[f"recall@{k}"] = recall_at_k(retrieved, relevant, k)
        results[f"ndcg@{k}"] = ndcg_at_k(retrieved, relevant, k)
    return results
