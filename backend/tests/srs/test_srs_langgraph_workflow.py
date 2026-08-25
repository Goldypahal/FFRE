import pytest
from unittest.mock import MagicMock, patch
from graph import (
    build_graph,
    AgentState,
    should_retry_or_human_review,
    human_review_node,
    CONFIDENCE_THRESHOLD,
    MAX_RETRIES
)

def test_workflow_decision_validation_pass_high_confidence():
    state: AgentState = {
        "investigation_id": "inv_test_1",
        "transaction_id": "txn_test_1",
        "tasks": [],
        "customer_evidence": {"kyc": "VERIFIED"},
        "transaction_evidence": {"amount": 100},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "historical_cases": [],
        "risk_score": 0.20,
        "confidence": 0.95,
        "validated": True,
        "retry_count": 0,
        "report": None,
        "draft_explanation": "Valid transaction",
        "rule_score": 0.1,
        "rule_reasons": []
    }
    decision = should_retry_or_human_review(state)
    assert decision == "report_generator"

def test_workflow_decision_validation_fail_retry():
    state: AgentState = {
        "investigation_id": "inv_test_2",
        "transaction_id": "txn_test_2",
        "tasks": [],
        "customer_evidence": {},
        "transaction_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "historical_cases": [],
        "risk_score": 0.80,
        "confidence": 0.70,
        "validated": False,
        "retry_count": 1,
        "report": None,
        "draft_explanation": "Hallucinated draft",
        "rule_score": 0.5,
        "rule_reasons": []
    }
    decision = should_retry_or_human_review(state)
    assert decision == "retry"

def test_workflow_decision_max_retries_escalates_to_human_review():
    state: AgentState = {
        "investigation_id": "inv_test_3",
        "transaction_id": "txn_test_3",
        "tasks": [],
        "customer_evidence": {},
        "transaction_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "historical_cases": [],
        "risk_score": 0.85,
        "confidence": 0.75,
        "validated": False,
        "retry_count": MAX_RETRIES,
        "report": None,
        "draft_explanation": "Repeated hallucinated draft",
        "rule_score": 0.7,
        "rule_reasons": []
    }
    decision = should_retry_or_human_review(state)
    assert decision == "human_review"

def test_workflow_decision_low_confidence_escalates_to_human_review():
    state: AgentState = {
        "investigation_id": "inv_test_4",
        "transaction_id": "txn_test_4",
        "tasks": [],
        "customer_evidence": {},
        "transaction_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "historical_cases": [],
        "risk_score": 0.60,
        "confidence": 0.55,  # Below threshold (0.85)
        "validated": True,
        "retry_count": 0,
        "report": None,
        "draft_explanation": "Valid claims but low overall confidence",
        "rule_score": 0.4,
        "rule_reasons": []
    }
    decision = should_retry_or_human_review(state)
    assert decision == "human_review"

def test_human_review_node_report_generation():
    state: AgentState = {
        "investigation_id": "inv_test_hr",
        "transaction_id": "txn_test_hr",
        "tasks": [],
        "customer_evidence": {},
        "transaction_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "historical_cases": [],
        "risk_score": 0.70,
        "confidence": 0.60,
        "validated": True,
        "retry_count": 0,
        "report": None,
        "draft_explanation": "Low confidence reasoning draft",
        "rule_score": 0.5,
        "rule_reasons": []
    }
    updated_state = human_review_node(state)
    assert updated_state.get("report") is not None
    assert "HUMAN REVIEW ESCALATION REPORT" in updated_state["report"]
    assert "inv_test_hr" in updated_state["report"]
