import pytest
from unittest.mock import patch, MagicMock
from graph import build_graph, AgentState
import json

def test_planner_node():
    """Test the planner node function"""
    from graph import planner_node

    state: AgentState = {
        "transaction_id": "T-123",
        "tasks": [],
        "customer_evidence": {},
        "transaction_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "historical_cases": [],
        "risk_score": None,
        "confidence": None,
        "validated": False,
        "retry_count": 0,
        "report": None,
        "draft_explanation": None,
        "rule_score": None,
        "rule_reasons": []
    }

    # Mock the LLM to avoid actual API calls
    with patch('graph.llm') as mock_llm:
        mock_llm.invoke.return_value = MagicMock()
        result = planner_node(state)

    # Check that tasks were set
    assert "tasks" in result
    assert isinstance(result["tasks"], list)
    assert len(result["tasks"]) > 0
    # Should contain the expected task types
    expected_tasks = ["retrieve_customer", "retrieve_transaction", "retrieve_merchant",
                     "retrieve_device", "retrieve_location"]
    for task in expected_tasks:
        assert task in result["tasks"]

def test_retrieve_customer_node():
    """Test the retrieve_customer node function"""
    from graph import retrieve_customer_node

    state: AgentState = {
        "transaction_id": "T-123",
        "tasks": [],
        "customer_evidence": {},
        "transaction_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "historical_cases": [],
        "risk_score": None,
        "confidence": None,
        "validated": False,
        "retry_count": 0,
        "report": None,
        "draft_explanation": None,
        "rule_score": None,
        "rule_reasons": []
    }

    with patch('graph.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        mock_txn = MagicMock(account_id="A-123")
        mock_acct = MagicMock(customer_id="C-123")
        mock_cust = MagicMock(kyc_status="VERIFIED", risk_tier="LOW")
        mock_cust.name = "Alex Johnson"
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_txn,
            mock_acct,
            mock_cust
        ]

        result = retrieve_customer_node(state)

    # Check that customer_evidence was populated
    assert result["customer_evidence"]["kyc_status"] == "VERIFIED"
    assert result["customer_evidence"]["risk_tier"] == "LOW"
    assert result["customer_evidence"]["name"] == "Alex Johnson"

def test_build_graph():
    """Test that the graph can be built without errors"""
    # This test ensures the graph structure is correct
    graph_app = build_graph()
    assert graph_app is not None
    # The graph should have the expected nodes
    # We can't easily inspect the internal structure without importing LangGraph internals,
    # but we can at least verify it compiles

def test_should_retry_or_human_review():
    """Test the conditional routing logic"""
    from graph import should_retry_or_human_review

    # Test case 1: Not validated and retries < 3 -> should retry
    state1 = {
        "validated": False,
        "retry_count": 0,
        "confidence": 0.9
    }
    assert should_retry_or_human_review(state1) in ["risk_reasoning", "retry"]

    # Test case 2: Not validated and retries >= 3 -> should go to human review
    state2 = {
        "validated": False,
        "retry_count": 3,
        "confidence": 0.9
    }
    assert should_retry_or_human_review(state2) == "human_review"

    # Test case 3: Validated and confidence >= threshold -> should go to report generator
    state3 = {
        "validated": True,
        "retry_count": 0,
        "confidence": 0.9
    }
    assert should_retry_or_human_review(state3) == "report_generator"

    # Test case 4: Validated but confidence < threshold -> should go to human review
    state4 = {
        "validated": True,
        "retry_count": 0,
        "confidence": 0.8
    }
    assert should_retry_or_human_review(state4) == "human_review"

def test_risk_reasoning_node_with_mock_llm():
    """Test the risk reasoning node with mocked LLM"""
    from graph import risk_reasoning_node

    state: AgentState = {
        "transaction_id": "T-123",
        "tasks": [],
        "customer_evidence": {"kyc_status": "VERIFIED"},
        "transaction_evidence": {"amount": 100.0},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "historical_cases": [],
        "risk_score": None,
        "confidence": None,
        "validated": False,
        "retry_count": 0,
        "report": None,
        "draft_explanation": None,
        "rule_score": None,
        "rule_reasons": []
    }

    # Mock the LLM
    with patch('graph.llm') as mock_llm:
        mock_response = MagicMock()
        mock_response.content = "The transaction shows normal activity."
        mock_llm.invoke.return_value = mock_response

        # Also mock the rule_engine node output by setting rule_score
        state_with_rule_score = state.copy()
        state_with_rule_score["rule_score"] = 0.3
        state_with_rule_score["rule_reasons"] = ["Normal transaction amount"]

        result = risk_reasoning_node(state_with_rule_score)

    # Check that the reasoning node produced output
    assert "draft_explanation" in result
    assert result["draft_explanation"] == "The transaction shows normal activity."
    assert "risk_score" in result
    assert "confidence" in result
    # Risk score should be a combination of rule score and LLM estimate
    assert 0 <= result["risk_score"] <= 1.0