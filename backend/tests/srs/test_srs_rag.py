import pytest
from unittest.mock import MagicMock
from graph import knowledge_lookup_node, AgentState

def test_rag_knowledge_lookup_node_retrieves_cases():
    state: AgentState = {
        "investigation_id": "inv_rag_node",
        "transaction_id": "txn_rag_1",
        "tasks": [],
        "customer_evidence": {"kyc_status": "VERIFIED"},
        "transaction_evidence": {"amount": 5000.0, "country": "RU"},
        "merchant_evidence": {"fraud_rate": 0.15},
        "device_evidence": {"os": "unknown"},
        "location_evidence": {"country": "RU"},
        "historical_cases": [],
        "risk_score": None,
        "confidence": None,
        "validated": False,
        "retry_count": 0,
        "report": None,
        "draft_explanation": None,
        "rule_score": 0.6,
        "rule_reasons": ["High merchant fraud rate"]
    }

    updated_state = knowledge_lookup_node(state)
    assert "historical_cases" in updated_state
    assert isinstance(updated_state["historical_cases"], list)
