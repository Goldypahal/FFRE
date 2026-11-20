"""
Property and statistical unit tests for FFIRE-Bench scoring engines.
"""

import pytest
from ffire_bench.scoring.metrics import (
    compute_t1_claim_metrics,
    compute_t2_error_detection_metrics,
    compute_t3_disposition_metrics
)
from ffire_bench.scoring.bootstrap import (
    wilson_score_interval,
    cluster_bootstrap_ci,
    paired_bootstrap_test
)


def test_t1_perfect_predictions():
    """Property test: identical gold and predicted labels yield macro-F1 = 1.0."""
    pairs = [
        {"gold_label": "SUPPORTED", "pred_label": "SUPPORTED", "gold_evidence_ids": ["EV-1"], "pred_evidence_ids": ["EV-1"]},
        {"gold_label": "CONTRADICTED", "pred_label": "CONTRADICTED", "gold_evidence_ids": ["EV-2"], "pred_evidence_ids": ["EV-2"]},
        {"gold_label": "UNSUPPORTED", "pred_label": "UNSUPPORTED", "gold_evidence_ids": [], "pred_evidence_ids": []},
        {"gold_label": "NOT_CHECKABLE", "pred_label": "NOT_CHECKABLE", "gold_evidence_ids": [], "pred_evidence_ids": []}
    ]

    res = compute_t1_claim_metrics(pairs)
    assert res["macro_f1"] == 1.0
    assert res["micro_accuracy"] == 1.0
    assert res["citation_metrics"]["citation_f1"] == 1.0


def test_t1_zero_correct_predictions():
    """Property test: completely mismatched predictions yield macro-F1 = 0.0."""
    pairs = [
        {"gold_label": "SUPPORTED", "pred_label": "CONTRADICTED", "gold_evidence_ids": ["EV-1"], "pred_evidence_ids": ["EV-9"]},
        {"gold_label": "CONTRADICTED", "pred_label": "UNSUPPORTED", "gold_evidence_ids": ["EV-2"], "pred_evidence_ids": ["EV-8"]},
    ]

    res = compute_t1_claim_metrics(pairs)
    assert res["macro_f1"] == 0.0
    assert res["micro_accuracy"] == 0.0
    assert res["citation_metrics"]["citation_f1"] == 0.0


def test_t2_error_detection_metrics():
    """Verify safe_to_file accuracy and critical error recall."""
    cases = [
        {"gold_safe_to_file": True, "pred_safe_to_file": True, "has_critical_error": False},
        {"gold_safe_to_file": False, "pred_safe_to_file": False, "has_critical_error": True, "critical_error_detected": True},
        {"gold_safe_to_file": False, "pred_safe_to_file": True, "has_critical_error": True, "critical_error_detected": False},
        {"gold_safe_to_file": True, "pred_safe_to_file": True, "has_critical_error": False}
    ]

    res = compute_t2_error_detection_metrics(cases)
    assert res["safe_to_file_accuracy"] == 75.0
    assert res["critical_error_recall"] == 50.0
    assert res["confusion_matrix"]["true_unsafe"] == 1
    assert res["confusion_matrix"]["false_safe"] == 1


def test_t3_cost_weighted_accuracy():
    """Verify 10x cost penalty for false negatives on fraud."""
    # Case 1: FN on fraud (missed fraud) -> cost 10.0
    # Case 2: Correct on legitimate -> cost 0.0
    cases = [
        {"gold_disposition": "ESCALATE", "pred_disposition": "ALLOW", "gold_is_fraud": True, "pred_confidence": 0.1, "expected_abstention": False},
        {"gold_disposition": "ALLOW", "pred_disposition": "ALLOW", "gold_is_fraud": False, "pred_confidence": 0.9, "expected_abstention": False}
    ]

    res = compute_t3_disposition_metrics(cases, fn_cost_multiplier=10.0)
    assert res["raw_accuracy"] == 50.0
    # Total cost = 10.0 out of max possible cost (10.0 + 1.0 = 11.0)
    assert res["cost_weighted_accuracy"] < 50.0
    assert res["total_penalty_cost"] == 10.0


def test_cluster_bootstrap_confidence_interval():
    """Verify that cluster bootstrap returns lower <= point <= upper."""
    items = [
        {"cluster_id": "C-1", "score": 1.0},
        {"cluster_id": "C-1", "score": 0.8},
        {"cluster_id": "C-2", "score": 0.6},
        {"cluster_id": "C-2", "score": 0.9},
        {"cluster_id": "C-3", "score": 0.7},
    ]

    def avg_score(sample):
        return sum(s["score"] for s in sample) / len(sample)

    pt, low, high = cluster_bootstrap_ci(items, avg_score, cluster_key="cluster_id", num_resamples=100)
    assert low <= pt <= high
    assert 0.5 <= low <= 1.0
    assert 0.5 <= high <= 1.0


def test_macro_f1_ignores_labels_that_never_occur():
    """A perfect system scores 1.0 even if only two of the four labels appear."""
    from ffire_bench.scoring.metrics import compute_t1_claim_metrics
    pairs = [
        {"gold_label": "SUPPORTED", "pred_label": "SUPPORTED"},
        {"gold_label": "CONTRADICTED", "pred_label": "CONTRADICTED"},
    ]
    m = compute_t1_claim_metrics(pairs)
    assert m["macro_f1"] == 1.0
    assert m["macro_f1_labels"] == ["SUPPORTED", "CONTRADICTED"]


def test_macro_f1_counts_wrongly_predicted_labels():
    """Predicting a label absent from gold still counts that label (as F1 = 0)."""
    from ffire_bench.scoring.metrics import compute_t1_claim_metrics
    pairs = [
        {"gold_label": "SUPPORTED", "pred_label": "SUPPORTED"},
        {"gold_label": "SUPPORTED", "pred_label": "UNSUPPORTED"},
    ]
    m = compute_t1_claim_metrics(pairs)
    assert set(m["macro_f1_labels"]) == {"SUPPORTED", "UNSUPPORTED"}
    assert m["macro_f1"] < 0.5
