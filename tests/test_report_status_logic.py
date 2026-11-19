"""
Unit tests for benchmark status evaluation logic.

Ensures that benchmark pass/fail verdicts are strictly computed from defined target thresholds
and that no metrics are hard-coded to 'PASS'.
"""

import sys
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.evaluate_held_out_100_cases import (
    evaluate_metric_status,
    evaluate_all_metrics,
    load_evaluation_targets
)


def test_evaluate_metric_status_operators():
    """Verify operator logic in metric threshold evaluation."""
    rule_ge = {"threshold": 85.0, "operator": ">=", "label": ">= 85.0% target"}
    assert evaluate_metric_status(85.0, rule_ge)[0] == "PASS"
    assert evaluate_metric_status(87.5, rule_ge)[0] == "PASS"
    assert evaluate_metric_status(84.99, rule_ge)[0] == "FAIL"

    rule_le = {"threshold": 5.0, "operator": "<=", "label": "<= 5.0% target"}
    assert evaluate_metric_status(4.9, rule_le)[0] == "PASS"
    assert evaluate_metric_status(5.0, rule_le)[0] == "PASS"
    assert evaluate_metric_status(5.01, rule_le)[0] == "FAIL"


def test_hard_coded_pass_prevention_on_failing_metrics():
    """
    Critical regression test: ensure that historical violations
    (FPR 17.78%, FNR 9.09%, Brier 0.1589, KYC 0.0%) evaluate to FAIL.
    """
    targets = load_evaluation_targets()
    
    # Historical held-out metrics from October 2026 report
    historical_metrics = {
        "accuracy_pct": 87.00,
        "precision_pct": 86.21,
        "recall_pct": 90.91,
        "specificity_pct": 82.22,
        "f1_score": 0.8850,
        "false_positive_rate_pct": 17.78,    # Target < 5.0% -> MUST FAIL
        "false_negative_rate_pct": 9.09,     # Target < 2.0% -> MUST FAIL
        "brier_score": 0.1589,               # Target < 0.10 -> MUST FAIL
        "evidence_grounding_accuracy_pct": 100.0, # Target 100% -> PASS
        "insufficient_kyc_escalation_pct": 0.0     # Target 100% -> MUST FAIL
    }

    evaluations = evaluate_all_metrics(historical_metrics, targets)

    # Verify that failing metrics strictly evaluate to FAIL
    assert evaluations["false_positive_rate"]["status"] == "FAIL", "FPR 17.78% must FAIL threshold of 5.0%"
    assert evaluations["false_negative_rate"]["status"] == "FAIL", "FNR 9.09% must FAIL threshold of 2.0%"
    assert evaluations["brier_score"]["status"] == "FAIL", "Brier score 0.1589 must FAIL threshold of 0.10"
    assert evaluations["kyc_escalation_rate"]["status"] == "FAIL", "KYC escalation 0.0% must FAIL threshold of 100%"

    # Verify that passing metrics evaluate to PASS
    assert evaluations["accuracy"]["status"] == "PASS"
    assert evaluations["precision"]["status"] == "PASS"
    assert evaluations["recall"]["status"] == "PASS"
    assert evaluations["evidence_grounding"]["status"] == "PASS"

    # Overall verdict MUST be FAIL
    passed_count = sum(1 for e in evaluations.values() if e["status"] == "PASS")
    assert passed_count == 6
    assert len(evaluations) == 10
    overall_status = "PASS" if passed_count == len(evaluations) else "FAIL"
    assert overall_status == "FAIL"


def test_perfect_metrics_evaluate_to_pass():
    """Verify that when all criteria meet configured targets, overall status is PASS."""
    targets = load_evaluation_targets()
    
    perfect_metrics = {
        "accuracy_pct": 98.0,
        "precision_pct": 97.0,
        "recall_pct": 99.0,
        "specificity_pct": 97.0,
        "f1_score": 0.9800,
        "false_positive_rate_pct": 3.0,
        "false_negative_rate_pct": 1.0,
        "brier_score": 0.0450,
        "evidence_grounding_accuracy_pct": 100.0,
        "insufficient_kyc_escalation_pct": 100.0
    }

    evaluations = evaluate_all_metrics(perfect_metrics, targets)
    for key, ev in evaluations.items():
        assert ev["status"] == "PASS", f"Expected {key} to pass with value {ev['value']}"

    passed_count = sum(1 for e in evaluations.values() if e["status"] == "PASS")
    assert passed_count == len(evaluations)
