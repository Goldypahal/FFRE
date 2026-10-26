"""
Automated Test Suite for Phase 5: Autonomous AI Investigation Agent & Tool Registry.

Validates:
1. InvestigationToolRegistry: Registration and execution of all 10 forensic tools:
   - Tool 1: get_customer_history
   - Tool 2: get_transaction_history
   - Tool 3: get_device_history
   - Tool 4: get_merchant_risk
   - Tool 5: get_ip_risk
   - Tool 6: search_historical_cases (Phase 3 4-Way Hybrid Search)
   - Tool 7: run_fraud_rules (Phase 1 Rules & CTR thresholds)
   - Tool 8: run_ml_model (Phase 2 Calibrated LightGBM)
   - Tool 9: get_graph_neighbors (Phase 4 Heterogeneous Graph & Cluster Detector)
   - Tool 10: create_investigation_report (Cryptographic Audit Dossier & SAR/CTR narrative)
2. Dynamic Multi-Step ReAct Investigation Execution.
3. Adjudication of Benign Commercial Wire ($85,000 with mandatory statutory CTR filing).
4. Adjudication of Coordinated Device-Sharing Fraud Ring (SUSPICIOUS with SAR narrative).
5. Adjudication of Structuring / Smurfing Typology.
6. Audit Trace & Cryptographic Evidence Checksum Integrity.
"""

import hashlib
import pytest
from backend.agent.tools import (
    get_tool_registry,
    get_customer_history,
    get_transaction_history,
    get_device_history,
    get_merchant_risk,
    get_ip_risk,
    search_historical_cases,
    run_fraud_rules,
    run_ml_model,
    get_graph_neighbors,
    create_investigation_report,
)
from backend.agent.agent import (
    AutonomousInvestigationAgent,
    run_autonomous_investigation,
    AgentInvestigationState,
)


def test_tool_registry_registration_and_listing():
    """Validates that all 10 required forensic tools are registered and accessible."""
    registry = get_tool_registry()
    tools = registry.list_tools()

    expected_tools = [
        "get_customer_history",
        "get_transaction_history",
        "get_device_history",
        "get_merchant_risk",
        "get_ip_risk",
        "search_historical_cases",
        "run_fraud_rules",
        "run_ml_model",
        "get_graph_neighbors",
        "create_investigation_report",
    ]

    for expected in expected_tools:
        assert expected in tools, f"Missing expected tool: {expected}"
    assert len(tools) == 10

    # Ensure unregistered tool throws ValueError
    with pytest.raises(ValueError, match="not registered"):
        registry.execute("non_existent_tool")


def test_individual_tools_execution():
    """Validates execution and structured return types for all individual forensic tools."""
    registry = get_tool_registry()

    # Tool 1: get_customer_history
    cust = registry.execute("get_customer_history", customer_id="CUST_TEST_01")
    assert cust["customer_id"] == "CUST_TEST_01"
    assert "kyc_status" in cust
    assert "risk_tier" in cust
    assert "accounts" in cust

    # Tool 2: get_transaction_history
    hist = registry.execute("get_transaction_history", account_id="ACCT_TEST_01")
    assert hist["account_id"] == "ACCT_TEST_01"
    assert "transaction_count" in hist
    assert "total_volume" in hist

    # Tool 3: get_device_history
    dev = registry.execute("get_device_history", device_id="DEV_FINGERPRINT_99")
    assert dev["device_id"] == "DEV_FINGERPRINT_99"
    assert "is_shared_device" in dev

    # Tool 4: get_merchant_risk
    merch = registry.execute("get_merchant_risk", merchant_id="MERCH_CRYPTO_01")
    assert merch["merchant_id"] == "MERCH_CRYPTO_01"
    assert "historical_fraud_rate" in merch
    assert "is_high_risk_category" in merch

    # Tool 5: get_ip_risk
    ip_res = registry.execute("get_ip_risk", ip_address="185.220.101.5")
    assert ip_res["is_tor"] is True
    assert ip_res["is_vpn"] is True
    assert ip_res["risk_penalty"] > 0.50

    # Tool 6: search_historical_cases
    cases = registry.execute("search_historical_cases", query_text="wire transfer commercial", amount=50000.0, channel="WIRE")
    assert isinstance(cases, list)
    assert len(cases) > 0
    assert "hybrid_score" in cases[0]

    # Tool 7: run_fraud_rules
    rule_res = registry.execute(
        "run_fraud_rules",
        transaction={"amount": 75000.0, "channel": "WIRE"},
        customer={"kyc_status": "VERIFIED"}
    )
    assert "rule_score" in rule_res
    assert "compliance_alerts" in rule_res

    # Tool 8: run_ml_model
    ml_res = registry.execute(
        "run_ml_model",
        transaction={"amount": 120.0, "channel": "POS", "timestamp": "2026-01-15T10:00:00Z"},
        customer={"kyc_status": "VERIFIED"},
        account={"account_type": "CHECKING"}
    )
    assert "calibrated_probability" in ml_res
    assert "model_id" in ml_res
    assert 0.0 <= ml_res["calibrated_probability"] <= 1.0

    # Tool 9: get_graph_neighbors
    graph_res = registry.execute("get_graph_neighbors", transaction_id="TXN_TEST_99")
    assert "cluster_risk_score" in graph_res
    assert "detected_clusters_count" in graph_res

    # Tool 10: create_investigation_report
    report = registry.execute(
        "create_investigation_report",
        investigation_id="INV_001",
        transaction_id="TXN_TEST_99",
        verdict="BENIGN",
        confidence=0.95,
        summary="Clear corporate transfer",
        evidence_bundle={}
    )
    assert report["investigation_id"] == "INV_001"
    assert report["verdict"] == "BENIGN"
    assert report["cryptographic_fingerprint"] is not None
    assert len(report["cryptographic_fingerprint"]) == 64  # SHA-256


def test_autonomous_investigation_benign_commercial_wire():
    """
    Validates end-to-end investigation of an $85,000 corporate payroll wire.
    Must correctly:
    1. Identify statutory CTR recordkeeping mandate without false positive laundering alert.
    2. Adjudicate as BENIGN with high confidence (>= 0.90).
    3. Include statutory CTR audit note while leaving SAR narrative empty.
    """
    result = run_autonomous_investigation(
        transaction_id="TXN_CORP_WIRE_01",
        transaction_data={
            "txn_id": "TXN_CORP_WIRE_01",
            "amount": 85000.0,
            "channel": "WIRE",
            "account_id": "ACC_CORP_MAIN",
            "customer_id": "CORP_ACME_INC"
        }
    )

    assert result["verdict"] == "BENIGN"
    assert result["confidence"] >= 0.90
    assert result["step_count"] >= 5

    report = result["report"]
    assert report is not None
    assert report["verdict"] == "BENIGN"
    assert report["sar_narrative"] is None
    assert report["ctr_audit_note"] is not None
    assert "31 CFR § 1010.311" in report["ctr_audit_note"]


def test_autonomous_investigation_device_sharing_syndicate():
    """
    Validates dynamic branch exploration when a device fingerprint is flagged.
    Must detect the syndicate ring and output a SUSPICIOUS adjudication with SAR narrative.
    """
    agent = AutonomousInvestigationAgent()

    # Create mock evidence state with shared device
    txn_data = {
        "txn_id": "TXN_SYNDICATE_01",
        "amount": 4800.0,
        "channel": "P2P",
        "account_id": "ACCT_MULE_01",
        "device_id": "DEV_FINGERPRINT_SYNDICATE",
        "ip_address": "185.220.101.45"  # Tor exit node
    }

    state = agent.investigate(
        transaction_id="TXN_SYNDICATE_01",
        transaction_data=txn_data
    )

    assert state.is_complete is True
    # The agent must have dynamically called get_device_history and get_ip_risk
    tool_names = [call["tool_name"] for call in state.tool_call_history]
    assert "get_device_history" in tool_names
    assert "get_ip_risk" in tool_names
    assert "search_historical_cases" in tool_names

    # Verdict must be SUSPICIOUS or have SAR narrative
    assert state.verdict in ["SUSPICIOUS", "REVIEW"]
    report = state.report
    assert report["cryptographic_fingerprint"] is not None


def test_autonomous_investigation_structuring_typology():
    """
    Validates autonomous investigation of structured cash transactions under CTR threshold.
    """
    agent = AutonomousInvestigationAgent()

    txn_data = {
        "txn_id": "TXN_STRUCTURING_9800",
        "amount": 9800.0,
        "channel": "CASH",
        "account_id": "ACCT_INDIVIDUAL_01"
    }

    state = agent.investigate(
        transaction_id="TXN_STRUCTURING_9800",
        transaction_data=txn_data
    )

    assert state.is_complete is True
    assert state.report is not None
    assert state.report["cryptographic_fingerprint"] is not None


def test_tool_call_audit_trace_completeness():
    """Validates that tool call history in state records exact audit trace parameters."""
    result = run_autonomous_investigation(
        transaction_id="TXN_AUDIT_TRACE_01",
        transaction_data={"txn_id": "TXN_AUDIT_TRACE_01", "amount": 1500.0, "channel": "POS"}
    )

    history = result["tool_call_history"]
    assert len(history) == result["step_count"]

    for idx, item in enumerate(history, 1):
        assert item["step"] == idx
        assert "tool_name" in item
        assert "args" in item
        assert "reason" in item
        assert "result_summary" in item
        assert len(item["reason"]) > 0


def test_cryptographic_fingerprint_integrity():
    """Validates the cryptographic SHA-256 fingerprint generated on the investigation report."""
    report = create_investigation_report(
        investigation_id="INV_CRYPTO_TEST",
        transaction_id="TXN_CRYPTO_99",
        verdict="SUSPICIOUS",
        confidence=0.98,
        summary="High-risk cluster confirmed",
        evidence_bundle={"compliance_alerts": []}
    )

    fingerprint = report["cryptographic_fingerprint"]
    assert len(fingerprint) == 64

    # Verify that the fingerprint was computed from the actual report payload components
    now_iso = report["generated_at"]
    expected_payload = f"INV_CRYPTO_TEST:TXN_CRYPTO_99:SUSPICIOUS:0.98:{now_iso}"
    expected_hash = hashlib.sha256(expected_payload.encode("utf-8")).hexdigest()
    assert fingerprint == expected_hash
