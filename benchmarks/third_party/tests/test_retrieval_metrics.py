import pytest
import math
from benchmarks.third_party.evaluation.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    mean_reciprocal_rank,
    dcg_at_k,
    ndcg_at_k,
    evaluate_query_retrieval,
)


def test_precision_at_k_hand_calculated():
    """Verify precision@k matches manual calculation: |Retrieved[:k] ∩ Relevant| / k."""
    relevant = {"doc_1", "doc_3"}
    retrieved = ["doc_1", "doc_2", "doc_3", "doc_4"]

    # k=1: retrieved=["doc_1"] -> hits=1 -> 1/1 = 1.0
    assert precision_at_k(retrieved, relevant, k=1) == 1.0

    # k=2: retrieved=["doc_1", "doc_2"] -> hits=1 -> 1/2 = 0.5
    assert precision_at_k(retrieved, relevant, k=2) == 0.5

    # k=3: retrieved=["doc_1", "doc_2", "doc_3"] -> hits=2 -> 2/3 = 0.6667
    assert precision_at_k(retrieved, relevant, k=3) == 0.6667

    # k=4: retrieved=["doc_1", "doc_2", "doc_3", "doc_4"] -> hits=2 -> 2/4 = 0.5
    assert precision_at_k(retrieved, relevant, k=4) == 0.5


def test_recall_at_k_hand_calculated():
    """Verify recall@k matches manual calculation: |Retrieved[:k] ∩ Relevant| / |Relevant|."""
    relevant = {"doc_1", "doc_3"}  # total = 2
    retrieved = ["doc_1", "doc_2", "doc_3", "doc_4"]

    # k=1: hits=1 -> 1/2 = 0.5
    assert recall_at_k(retrieved, relevant, k=1) == 0.5

    # k=2: hits=1 -> 1/2 = 0.5
    assert recall_at_k(retrieved, relevant, k=2) == 0.5

    # k=3: hits=2 -> 2/2 = 1.0
    assert recall_at_k(retrieved, relevant, k=3) == 1.0


def test_mrr_hand_calculated():
    """Verify MRR reciprocal rank for first relevant item."""
    relevant = {"doc_target"}

    # Hit at rank 1: 1/1 = 1.0
    assert mean_reciprocal_rank(["doc_target", "doc_other"], relevant) == 1.0

    # Hit at rank 2: 1/2 = 0.5
    assert mean_reciprocal_rank(["doc_other", "doc_target"], relevant) == 0.5

    # Hit at rank 4: 1/4 = 0.25
    assert mean_reciprocal_rank(["doc_a", "doc_b", "doc_c", "doc_target"], relevant) == 0.25

    # No hits: 0.0
    assert mean_reciprocal_rank(["doc_a", "doc_b"], relevant) == 0.0


def test_ndcg_at_k_hand_calculated():
    """
    Verify nDCG@k:
    Relevant = {E1, E2}
    Retrieved = [E1, E3, E2, E4]
    DCG@3 = 1/log2(2) + 0/log2(3) + 1/log2(4) = 1.0 + 0.5 = 1.5
    IDCG@3 = 1/log2(2) + 1/log2(3) = 1.0 + 0.63092975 = 1.63092975
    nDCG@3 = 1.5 / 1.63092975 = 0.9197
    """
    relevant = {"E1", "E2"}
    retrieved = ["E1", "E3", "E2", "E4"]

    manual_dcg3 = 1.0 / math.log2(2) + 0.0 + 1.0 / math.log2(4)
    manual_idcg3 = 1.0 / math.log2(2) + 1.0 / math.log2(3)
    expected_ndcg3 = round(manual_dcg3 / manual_idcg3, 4)

    assert ndcg_at_k(retrieved, relevant, k=3) == expected_ndcg3
    assert ndcg_at_k(retrieved, relevant, k=3) == 0.9197


def test_edge_cases():
    """Verify correct handling of empty retrieved, empty relevant, and k=0."""
    # Empty relevant: precision=0, recall=1 if empty retrieved else 0
    assert precision_at_k(["a", "b"], set(), k=2) == 0.0
    assert recall_at_k([], set(), k=2) == 1.0
    assert recall_at_k(["a"], set(), k=2) == 0.0

    # Empty retrieved
    assert precision_at_k([], {"a"}, k=1) == 0.0
    assert recall_at_k([], {"a"}, k=1) == 0.0
    assert mean_reciprocal_rank([], {"a"}) == 0.0
    assert ndcg_at_k([], {"a"}, k=1) == 0.0

    # k=0 or negative
    assert precision_at_k(["a"], {"a"}, k=0) == 0.0
    assert recall_at_k(["a"], {"a"}, k=-1) == 0.0


def test_evaluate_query_retrieval_bundle():
    """Verify bundled evaluation dictionary."""
    relevant = {"a", "b"}
    retrieved = ["a", "c", "b"]
    bundle = evaluate_query_retrieval(retrieved, relevant, k_values=[1, 3])

    assert "mrr" in bundle
    assert "precision@1" in bundle
    assert "recall@3" in bundle
    assert "ndcg@3" in bundle
    assert bundle["mrr"] == 1.0
    assert bundle["recall@3"] == 1.0
