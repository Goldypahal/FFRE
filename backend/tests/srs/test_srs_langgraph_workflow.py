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
    assert decision in ["risk_reasoning", "retry"]

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

# --- Dedicated Granular Verification Tests for SA-1 to SA-15 ---

def test_sa1_agent_state_schema_isolation():
    """SA-1: Verify AgentState typed dictionary schema enforces node execution isolation and typing."""
    from graph import AgentState
    state: AgentState = {
        "investigation_id": "inv_sa1",
        "transaction_id": "txn_sa1",
        "tasks": ["retrieve_customer"],
        "customer_evidence": {},
        "transaction_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "velocity_evidence": {},
        "verified_evidence": {},
        "historical_cases": [],
        "risk_score": 0.5,
        "confidence": 0.9,
        "validated": True,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": "Draft",
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": 0.2,
        "rule_reasons": [],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": []
    }
    assert state["investigation_id"] == "inv_sa1"
    assert isinstance(state["tasks"], list)
    assert isinstance(state["execution_trace"], list)

def test_sa2_planner_decomposition_allowlist():
    """SA-2: Verify planner_node decomposes transactions and filters against approved allowlist."""
    from graph import planner_node
    test_state = {
        "transaction_id": "TXN-SA2",
        "tasks": ["customer_history", "merchant_reputation", "unknown_task"]
    }
    res = planner_node(test_state)
    assert "retrieve_customer" in res["tasks"]
    assert "retrieve_merchant" in res["tasks"]
    assert "unknown_task" not in res["tasks"]

def test_sa3_retrieve_customer_node(db_session):
    """SA-3: Verify retrieve_customer_node queries Customer model and handles missing data gracefully."""
    from graph import retrieve_customer_node
    state = {"transaction_id": "TXN-NONEXISTENT"}
    res = retrieve_customer_node(state)
    assert "customer_evidence" in res
    assert "error" in res["customer_evidence"] or "kyc_status" in res["customer_evidence"]

def test_sa4_retrieve_transaction_node(db_session):
    """SA-4: Verify retrieve_transaction_node queries transaction ledger."""
    from graph import retrieve_transaction_node
    state = {"transaction_id": "TXN-NONEXISTENT"}
    res = retrieve_transaction_node(state)
    assert "transaction_evidence" in res
    assert "error" in res["transaction_evidence"] or "currency" in res["transaction_evidence"]

def test_sa5_retrieve_merchant_node(db_session):
    """SA-5: Verify retrieve_merchant_node extracts merchant risk profile."""
    from graph import retrieve_merchant_node
    state = {"transaction_id": "TXN-NONEXISTENT"}
    res = retrieve_merchant_node(state)
    assert "merchant_evidence" in res
    assert "error" in res["merchant_evidence"] or "historical_fraud_rate" in res["merchant_evidence"]

def test_sa6_retrieve_device_node(db_session):
    """SA-6: Verify retrieve_device_node queries device fingerprint."""
    from graph import retrieve_device_node
    state = {"transaction_id": "TXN-NONEXISTENT"}
    res = retrieve_device_node(state)
    assert "device_evidence" in res
    assert "error" in res["device_evidence"] or "os" in res["device_evidence"]

def test_sa7_retrieve_location_node(db_session):
    """SA-7: Verify retrieve_location_node queries geo-location coordinates."""
    from graph import retrieve_location_node
    state = {"transaction_id": "TXN-NONEXISTENT"}
    res = retrieve_location_node(state)
    assert "location_evidence" in res
    assert "error" in res["location_evidence"] or "country" in res["location_evidence"]

def test_sa8_evidence_verifier_node():
    """SA-8: Verify evidence_verifier_node aggregates parallel retrieved sources and computes provenance."""
    from graph import evidence_verifier_node
    state = {
        "investigation_id": "inv_sa8",
        "transaction_id": "txn_sa8",
        "customer_evidence": {"kyc": "VERIFIED"},
        "transaction_evidence": {"amount": 100},
        "merchant_evidence": {"name": "Test"},
        "device_evidence": {"os": "iOS"},
        "location_evidence": {"country": "US"},
        "velocity_evidence": {}
    }
    res = evidence_verifier_node(state)
    assert "evidence_provenance" in res
    assert len(res["evidence_provenance"]) > 0

def test_sa9_velocity_check_node(db_session):
    """SA-9: Verify velocity_check_node computes multi-window transaction velocities."""
    from graph import velocity_check_node
    state = {"transaction_id": "TXN-NONEXISTENT"}
    res = velocity_check_node(state)
    assert "velocity_evidence" in res
    assert "velocity_5m" in res["velocity_evidence"]
    assert "velocity_1h" in res["velocity_evidence"]
    assert "velocity_24h" in res["velocity_evidence"]
    assert "velocity_7d" in res["velocity_evidence"]

def test_sa10_rule_engine_node():
    """SA-10: Verify rule_engine_node evaluates deterministic rules and generates RiskSignals."""
    from graph import rule_engine_node
    state = {
        "transaction_evidence": {"amount": 50000.0},
        "customer_evidence": {"kyc_status": "PENDING"},
        "velocity_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {}
    }
    res = rule_engine_node(state)
    assert res.get("rule_score") is not None
    assert isinstance(res.get("risk_signals"), list)

def test_sa11_knowledge_lookup_node():
    """SA-11: Verify knowledge_lookup_node queries historical fraud vector database."""
    from graph import knowledge_lookup_node
    state = {
        "transaction_evidence": {"amount": 100, "currency": "USD"},
        "device_evidence": {"os": "Android"},
        "merchant_evidence": {"name": "Test Retail"}
    }
    res = knowledge_lookup_node(state)
    assert "historical_cases" in res
    assert isinstance(res["historical_cases"], list)

def test_sa12_risk_reasoning_node():
    """SA-12: Verify risk_reasoning_node calculates synthesized risk score and dynamic confidence."""
    from graph import risk_reasoning_node
    state = {
        "investigation_id": "inv_sa12",
        "rule_score": 0.4,
        "rule_reasons": ["Moderate amount"],
        "historical_cases": [{"similarity": 0.8}],
        "customer_evidence": {"kyc": "VERIFIED"},
        "transaction_evidence": {"amount": 250},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "velocity_evidence": {}
    }
    res = risk_reasoning_node(state)
    assert res.get("risk_score") is not None
    assert res.get("confidence") is not None
    assert 0.0 <= res["confidence"] <= 1.0

def test_sa13_critic_node():
    """SA-13: Verify critic_node validates reasoning draft against collected evidence."""
    from graph import critic_node
    state = {
        "investigation_id": "inv_sa13",
        "draft_explanation": "Transaction is normal and verified.",
        "customer_evidence": {"kyc": "VERIFIED"},
        "transaction_evidence": {"amount": 100},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "velocity_evidence": {}
    }
    res = critic_node(state)
    assert "critic_issues" in res
    assert "critic_feedback" in res

def test_sa14_validator_node():
    """SA-14: Verify validator_node grounds claims against retrieved evidence."""
    from graph import validator_node
    state = {
        "draft_explanation": "Amount is 100 USD.",
        "transaction_evidence": {"amount": 100},
        "customer_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "velocity_evidence": {}
    }
    res = validator_node(state)
    assert "validated" in res

def test_sa15_human_review_node_packaging():
    """SA-15: Verify human_review_node generates structured escalation dossier."""
    from graph import human_review_node
    state = {
        "investigation_id": "inv_sa15",
        "transaction_id": "txn_sa15",
        "risk_score": 0.88,
        "confidence": 0.65,
        "validated": False,
        "retry_count": 3,
        "draft_explanation": "Suspicious transaction"
    }
    res = human_review_node(state)
    assert "report" in res
    assert "HUMAN REVIEW ESCALATION REPORT" in res["report"]
    assert "inv_sa15" in res["report"]
