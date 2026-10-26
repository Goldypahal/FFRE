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


def test_low_vector_similarity_cannot_suppress_mandatory_rule_alert():
    """
    Regression Test (P0):
    Verify that lack of historical precedent in vector store (cold-start or low similarity)
    cannot silently veto or suppress a mandatory deterministic compliance rule alert below threshold.
    Specifically tests that an $8,400 structuring alert (rule_score=0.65) retains an elevated risk score
    >= 0.65 even when historical case similarity is 0.0.
    """
    from graph import risk_reasoning_node

    state: AgentState = {
        "transaction_id": "TXN_AML_19_0029",
        "tenant_id": "test_tenant",
        "tasks": [],
        "customer_evidence": {"name": "Test Customer", "kyc_status": "VERIFIED"},
        "transaction_evidence": {"amount": 8400.0, "currency": "USD", "account_id": "ACC_STK_1", "counterparty": "ACC_STK_2"},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "velocity_evidence": {},
        "verified_evidence": {},
        "historical_cases": [
            {"case_id": "hist_unrelated_001", "similarity": 0.05, "similarity_distance": 1.9}
        ],
        "risk_score": None,
        "confidence": None,
        "validated": False,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": None,
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": 0.65,
        "rule_reasons": [
            "Structuring threshold pattern detected ($8,400.00 between $8,000 and $9,999; CTR avoidance heuristic proxy)."
        ],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": [],
        "pii_vault": None,
    }

    # Evaluate risk reasoning with zero / minimal vector similarity
    with patch('graph.llm') as mock_llm:
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "reasoning": "Account ACC_STK_1 transfer of 8400.00 USD was verified under compliance threshold.",
            "risk_score": 0.55
        })
        mock_llm.invoke.return_value = mock_response

        result = risk_reasoning_node(state)

    # Invariant: Rule alert must be preserved. Risk score must not be dampened below rule_score (0.65)
    assert result["risk_score"] is not None
    assert result["risk_score"] >= 0.65, (
        f"Rule finding suppressed! Expected risk_score >= 0.65, got {result['risk_score']}"
    )
    assert result["risk_score"] >= 0.50, "Verdict crossed below suspicious decision boundary!"
    assert result.get("has_typology_alert") is True
    assert result.get("predicted_verdict") == "SUSPICIOUS"


def test_benign_high_value_commercial_wire_preserves_compliance_alert_without_forcing_suspicious_verdict():
    """
    Regression Test (P1):
    Verify that a routine commercial high-value transaction ($48,500 payroll disbursement)
    triggers and preserves the mandatory statutory compliance reporting alert (CTR mandate / anomaly)
    in state["compliance_alerts"] without blindly forcing the final adjudicated laundering verdict
    to SUSPICIOUS when verified KYC and legitimate business context confirm benign activity.
    """
    from graph import risk_reasoning_node

    state: AgentState = {
        "transaction_id": "TXN_BENIGN_PAYROLL_01",
        "tenant_id": "commercial_tenant",
        "tasks": [],
        "customer_evidence": {
            "name": "Acme Industrial Logistics LLC",
            "kyc_status": "VERIFIED",
            "risk_tier": "LOW",
        },
        "transaction_evidence": {
            "amount": 48500.0,
            "currency": "USD",
            "account_id": "ACC_PAYROLL_CORP",
            "counterparty": "ACC_PAYROLL_CLEARING",
        },
        "merchant_evidence": {},
        "device_evidence": {"new_device": False, "os": "macOS"},
        "location_evidence": {"country": "US"},
        "velocity_evidence": {"high_velocity_flag": False},
        "verified_evidence": {},
        "historical_cases": [
            {"case_id": "hist_commercial_001", "similarity": 0.20, "similarity_distance": 1.6}
        ],
        "risk_score": None,
        "confidence": None,
        "validated": True,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": None,
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": 0.85,
        "rule_reasons": [
            "High-value transaction anomaly ($48,500.00 >= $20,000.00)."
        ],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": [],
        "pii_vault": None,
    }

    with patch('graph.llm') as mock_llm:
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "reasoning": "Commercial payroll wire of $48,500.00 for verified entity Acme Industrial Logistics verified under standard operations.",
            "risk_score": 0.15
        })
        mock_llm.invoke.return_value = mock_response

        result = risk_reasoning_node(state)

    # 1. Compliance mandate alert is preserved in state
    assert "compliance_alerts" in result
    assert len(result["compliance_alerts"]) > 0
    assert any("High-value transaction anomaly" in a for a in result["compliance_alerts"])

    # 2. No typology alert is present
    assert result.get("has_typology_alert") is False

    # 3. Adjudication: Amount alone does NOT force a SUSPICIOUS money laundering conviction
    # base_combined = 0.35*0.85 + 0.40*0.15 + 0.25*0.20 = 0.2975 + 0.06 + 0.05 = 0.4075 < 0.50
    assert result["risk_score"] < 0.50
    assert result.get("predicted_verdict") == "BENIGN"



def test_low_vector_similarity_cannot_suppress_mandatory_rule_alert():
    """
    Regression Test (P0):
    Verify that lack of historical precedent in vector store (cold-start or low similarity)
    cannot silently veto or suppress a mandatory deterministic compliance rule alert below threshold.
    Specifically tests that an $8,400 structuring alert (rule_score=0.65) retains an elevated risk score
    >= 0.65 even when historical case similarity is 0.0.
    """
    from graph import risk_reasoning_node

    state: AgentState = {
        "transaction_id": "TXN_AML_19_0029",
        "tenant_id": "test_tenant",
        "tasks": [],
        "customer_evidence": {"name": "Test Customer", "kyc_status": "VERIFIED"},
        "transaction_evidence": {"amount": 8400.0, "currency": "USD", "account_id": "ACC_STK_1", "counterparty": "ACC_STK_2"},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "velocity_evidence": {},
        "verified_evidence": {},
        "historical_cases": [
            {"case_id": "hist_unrelated_001", "similarity": 0.05, "similarity_distance": 1.9}
        ],
        "risk_score": None,
        "confidence": None,
        "validated": False,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": None,
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": 0.65,
        "rule_reasons": [
            "Structuring threshold pattern detected ($8,400.00 between $8,000 and $9,999; CTR avoidance heuristic proxy)."
        ],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": [],
        "pii_vault": None,
    }

    # Evaluate risk reasoning with zero / minimal vector similarity
    with patch('graph.llm') as mock_llm:
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "reasoning": "Account ACC_STK_1 transfer of 8400.00 USD was verified under compliance threshold.",
            "risk_score": 0.55
        })
        mock_llm.invoke.return_value = mock_response

        result = risk_reasoning_node(state)

    # Invariant: Rule alert must be preserved. Risk score must not be dampened below rule_score (0.65)
    assert result["risk_score"] is not None
    assert result["risk_score"] >= 0.65, (
        f"Rule finding suppressed! Expected risk_score >= 0.65, got {result['risk_score']}"
    )
    assert result["risk_score"] >= 0.50, "Verdict crossed below suspicious decision boundary!"
    assert result.get("has_typology_alert") is True
    assert result.get("predicted_verdict") == "SUSPICIOUS"


def test_benign_high_value_commercial_wire_preserves_compliance_alert_without_forcing_suspicious_verdict():
    """
    Regression Test (P1):
    Verify that a routine commercial high-value transaction ($48,500 payroll disbursement)
    triggers and preserves the mandatory statutory compliance reporting alert (CTR mandate / anomaly)
    in state["compliance_alerts"] without blindly forcing the final adjudicated laundering verdict
    to SUSPICIOUS when verified KYC and legitimate business context confirm benign activity.
    """
    from graph import risk_reasoning_node

    state: AgentState = {
        "transaction_id": "TXN_BENIGN_PAYROLL_01",
        "tenant_id": "commercial_tenant",
        "tasks": [],
        "customer_evidence": {
            "name": "Acme Industrial Logistics LLC",
            "kyc_status": "VERIFIED",
            "risk_tier": "LOW",
        },
        "transaction_evidence": {
            "amount": 48500.0,
            "currency": "USD",
            "account_id": "ACC_PAYROLL_CORP",
            "counterparty": "ACC_PAYROLL_CLEARING",
        },
        "merchant_evidence": {},
        "device_evidence": {"new_device": False, "os": "macOS"},
        "location_evidence": {"country": "US"},
        "velocity_evidence": {"high_velocity_flag": False},
        "verified_evidence": {},
        "historical_cases": [
            {"case_id": "hist_commercial_001", "similarity": 0.20, "similarity_distance": 1.6}
        ],
        "risk_score": None,
        "confidence": None,
        "validated": True,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": None,
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": 0.85,
        "rule_reasons": [
            "High-value transaction anomaly ($48,500.00 >= $20,000.00)."
        ],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": [],
        "pii_vault": None,
    }

    with patch('graph.llm') as mock_llm:
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "reasoning": "Commercial payroll wire of $48,500.00 for verified entity Acme Industrial Logistics verified under standard operations.",
            "risk_score": 0.15
        })
        mock_llm.invoke.return_value = mock_response

        result = risk_reasoning_node(state)

    # 1. Compliance mandate alert is preserved in state
    assert "compliance_alerts" in result
    assert len(result["compliance_alerts"]) > 0
    assert any("High-value transaction anomaly" in a for a in result["compliance_alerts"])

    # 2. No typology alert is present
    assert result.get("has_typology_alert") is False

    # 3. Adjudication: Amount alone does NOT force a SUSPICIOUS money laundering conviction
    # base_combined = 0.35*0.85 + 0.40*0.15 + 0.25*0.20 = 0.2975 + 0.06 + 0.05 = 0.4075 < 0.50
    assert result["risk_score"] < 0.50
    assert result.get("predicted_verdict") == "BENIGN"


def test_low_vector_similarity_cannot_suppress_mandatory_rule_alert():
    """
    Regression Test (P0):
    Verify that lack of historical precedent in vector store (cold-start or low similarity)
    cannot silently veto or suppress a mandatory deterministic compliance rule alert below threshold.
    Specifically tests that an $8,400 structuring alert (rule_score=0.65) retains an elevated risk score
    >= 0.65 even when historical case similarity is 0.0.
    """
    from graph import risk_reasoning_node

    state: AgentState = {
        "transaction_id": "TXN_AML_19_0029",
        "tenant_id": "test_tenant",
        "tasks": [],
        "customer_evidence": {"name": "Test Customer", "kyc_status": "VERIFIED"},
        "transaction_evidence": {"amount": 8400.0, "currency": "USD", "account_id": "ACC_STK_1", "counterparty": "ACC_STK_2"},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "velocity_evidence": {},
        "verified_evidence": {},
        "historical_cases": [
            {"case_id": "hist_unrelated_001", "similarity": 0.05, "similarity_distance": 1.9}
        ],
        "risk_score": None,
        "confidence": None,
        "validated": False,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": None,
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": 0.65,
        "rule_reasons": [
            "Structuring threshold pattern detected ($8,400.00 between $8,000 and $9,999; CTR avoidance heuristic proxy)."
        ],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": [],
        "pii_vault": None,
    }

    # Evaluate risk reasoning with zero / minimal vector similarity
    with patch('graph.llm') as mock_llm:
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "reasoning": "Account ACC_STK_1 transfer of 8400.00 USD was verified under compliance threshold.",
            "risk_score": 0.55
        })
        mock_llm.invoke.return_value = mock_response

        result = risk_reasoning_node(state)

    # Invariant: Rule alert must be preserved. Risk score must not be dampened below rule_score (0.65)
    assert result["risk_score"] is not None
    assert result["risk_score"] >= 0.65, (
        f"Rule finding suppressed! Expected risk_score >= 0.65, got {result['risk_score']}"
    )
    assert result["risk_score"] >= 0.50, "Verdict crossed below suspicious decision boundary!"
    assert result.get("has_typology_alert") is True
    assert result.get("predicted_verdict") == "SUSPICIOUS"


def test_benign_high_value_commercial_wire_preserves_compliance_alert_without_forcing_suspicious_verdict():
    """
    Regression Test (P1):
    Verify that a routine commercial high-value transaction ($48,500 payroll disbursement)
    triggers and preserves the mandatory statutory compliance reporting alert (CTR mandate / anomaly)
    in state["compliance_alerts"] without blindly forcing the final adjudicated laundering verdict
    to SUSPICIOUS when verified KYC and legitimate business context confirm benign activity.
    """
    from graph import risk_reasoning_node

    state: AgentState = {
        "transaction_id": "TXN_BENIGN_PAYROLL_01",
        "tenant_id": "commercial_tenant",
        "tasks": [],
        "customer_evidence": {
            "name": "Acme Industrial Logistics LLC",
            "kyc_status": "VERIFIED",
            "risk_tier": "LOW",
        },
        "transaction_evidence": {
            "amount": 48500.0,
            "currency": "USD",
            "account_id": "ACC_PAYROLL_CORP",
            "counterparty": "ACC_PAYROLL_CLEARING",
        },
        "merchant_evidence": {},
        "device_evidence": {"new_device": False, "os": "macOS"},
        "location_evidence": {"country": "US"},
        "velocity_evidence": {"high_velocity_flag": False},
        "verified_evidence": {},
        "historical_cases": [
            {"case_id": "hist_commercial_001", "similarity": 0.20, "similarity_distance": 1.6}
        ],
        "risk_score": None,
        "confidence": None,
        "validated": True,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": None,
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": 0.85,
        "rule_reasons": [
            "High-value transaction anomaly ($48,500.00 >= $20,000.00)."
        ],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": [],
        "pii_vault": None,
    }

    with patch('graph.llm') as mock_llm:
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "reasoning": "Commercial payroll wire of $48,500.00 for verified entity Acme Industrial Logistics verified under standard operations.",
            "risk_score": 0.15
        })
        mock_llm.invoke.return_value = mock_response

        result = risk_reasoning_node(state)

    # 1. Compliance mandate alert is preserved in state
    assert "compliance_alerts" in result
    assert len(result["compliance_alerts"]) > 0
    assert any("High-value transaction anomaly" in a for a in result["compliance_alerts"])

    # 2. No typology alert is present
    assert result.get("has_typology_alert") is False

    # 3. Adjudication: Amount alone does NOT force a SUSPICIOUS money laundering conviction
    # base_combined = 0.35*0.85 + 0.40*0.15 + 0.25*0.20 = 0.2975 + 0.06 + 0.05 = 0.4075 < 0.50
    assert result["risk_score"] < 0.50
    assert result.get("predicted_verdict") == "BENIGN"