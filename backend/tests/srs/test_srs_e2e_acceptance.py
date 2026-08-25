import datetime
import pytest
import models
from main import app
from graph import (
    build_graph,
    planner_node,
    velocity_check_node,
    evidence_verifier_node,
    critic_node,
    risk_reasoning_node,
    should_retry_or_human_review,
    route_planner_tasks
)

def test_acceptance_test_a_dynamic_planner_execution(db_session):
    """Task 1 & Task 2 Test: Dynamic Planner Selection & Node Execution Trace Assertions."""
    cust = models.Customer(customer_id="c_e2e_a", name="Dynamic Customer", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_e2e_a", customer_id="c_e2e_a")
    merch = models.Merchant(merchant_id="m_e2e_a", name="Dynamic Merchant", risk_score=0.01)
    txn = models.Transaction(txn_id="T-E2E-A", account_id="a_e2e_a", merchant_id="m_e2e_a", amount=150.0, currency="USD", status="PENDING")
    dev = models.Device(device_id="d_e2e_a", customer_id="c_e2e_a", os="Android")

    db_session.add_all([cust, acct, merch, txn, dev])
    db_session.commit()

    initial_state = {
        "investigation_id": "inv_e2e_a",
        "transaction_id": "T-E2E-A",
        "tasks": ["retrieve_customer", "retrieve_device"],
        "customer_evidence": {},
        "transaction_evidence": {},
        "merchant_evidence": {},
        "device_evidence": {},
        "location_evidence": {},
        "velocity_evidence": {},
        "verified_evidence": {},
        "historical_cases": [],
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
        "rule_score": None,
        "rule_reasons": [],
        "execution_trace": [],
        "critic_details": {}
    }

    config = {"configurable": {"thread_id": "inv_e2e_a"}}
    graph_app = build_graph()
    res = graph_app.invoke(initial_state, config=config)

    # Task 1 Assertion: Verify node execution trace contains requested nodes and excludes unrequested nodes
    trace = res.get("execution_trace", [])
    assert "retrieve_customer" in trace
    assert "retrieve_device" in trace
    assert "retrieve_merchant" not in trace
    assert "retrieve_location" not in trace

    # Verify requested customer and device evidence executed
    assert res.get("customer_evidence", {}).get("kyc_status") == "VERIFIED"
    assert res.get("device_evidence", {}).get("os") == "Android"
    assert res.get("merchant_evidence") == {}
    assert res.get("location_evidence") == {}

def test_planner_schema_validation_allowlist():
    """Task 2 Test: Planner filters out malformed or unknown tasks against strict allowlist."""
    state = {
        "transaction_id": "T-ALLOWLIST",
        "tasks": ["retrieve_customer", "malformed_unknown_task", "hacker_task"]
    }
    res = planner_node(state)
    assert res["tasks"] == ["retrieve_customer"]

def test_critic_strict_schema_validation():
    """Task 3 Test: Critic node parses and populates structured JSON critic_details schema."""
    state = {
        "draft_explanation": "Transaction of $500 from unknown device.",
        "customer_evidence": {"kyc_status": "VERIFIED"},
        "transaction_evidence": {"amount": 500.0},
        "velocity_evidence": {"velocity_score": 0.15}
    }
    res = critic_node(state)
    assert "critic_details" in res
    assert "affected_claims" in res["critic_details"]
    assert "severity" in res["critic_details"]

def test_acceptance_test_b_single_retrieval_failure_retry():
    """Test B: Single retrieval failure routes back to specific failed retrieval node."""
    state_txn_fail = {
        "investigation_id": "inv_e2e_b",
        "validated": False,
        "retry_count": 1,
        "confidence": 0.85,
        "failed_target_node": "retrieve_transaction"
    }
    decision = should_retry_or_human_review(state_txn_fail)
    assert decision == "retrieve_transaction"

def test_acceptance_test_c_multiple_failures_tracking():
    """Test C: Multiple evidence failures tracked across verifier node."""
    state = {
        "investigation_id": "inv_e2e_c",
        "transaction_id": "T-E2E-C",
        "customer_evidence": {"error": "Not Found"},
        "device_evidence": {"error": "Not Found"},
        "location_evidence": {"error": "Not Found"}
    }

    res_state = evidence_verifier_node(state)
    failed_nodes = res_state["failed_target_nodes"]

    assert "retrieve_customer" in failed_nodes
    assert "retrieve_device" in failed_nodes
    assert "retrieve_location" in failed_nodes
    assert res_state["verified_evidence"]["status"] == "PARTIAL"

def test_acceptance_test_d_critic_correction_loop():
    """Test D: Critic detects issues -> routes to reasoning node for correction."""
    state_critic_issue = {
        "investigation_id": "inv_e2e_d",
        "validated": False,
        "retry_count": 1,
        "confidence": 0.80,
        "critic_issues": True,
        "critic_feedback": "Ungrounded claim regarding offshore location."
    }

    decision = should_retry_or_human_review(state_critic_issue)
    assert decision == "risk_reasoning"

def test_acceptance_test_e_pure_one_hour_velocity_window(db_session):
    """Test E: Pure 1-Hour Velocity Window excludes transactions older than 1 hour."""
    cust = models.Customer(customer_id="c_e2e_e", name="Velocity E2E", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_e2e_e", customer_id="c_e2e_e")
    merch = models.Merchant(merchant_id="m_e2e_e", name="Merchant E2E", risk_score=0.01)

    now = datetime.datetime.utcnow()
    three_hours_ago = now - datetime.timedelta(hours=3)

    t_old = models.Transaction(txn_id="T-E2E-OLD", account_id="a_e2e_e", merchant_id="m_e2e_e", amount=9000.0, currency="USD", status="COMPLETED", timestamp=three_hours_ago)
    t_recent = models.Transaction(txn_id="T-E2E-RECENT", account_id="a_e2e_e", merchant_id="m_e2e_e", amount=350.0, currency="USD", status="PENDING", timestamp=now)

    db_session.add_all([cust, acct, merch, t_old, t_recent])
    db_session.commit()

    state = {"investigation_id": "inv_e2e_e", "transaction_id": "T-E2E-RECENT"}
    res = velocity_check_node(state)
    vel = res.get("velocity_evidence", {})

    # Excludes 3-hour-old transaction: count is 1, sum is 350.0
    assert vel.get("velocity_count_1h") == 1
    assert vel.get("velocity_sum_1h") == 350.0
    assert vel.get("high_velocity_flag") is False

def test_acceptance_test_f_full_investigation_pipeline_e2e(client, db_session):
    """Test F: Full end-to-end investigation pipeline from API intake to report export."""
    cust = models.Customer(customer_id="c_e2e_f", name="Full Pipeline Customer", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_e2e_f", customer_id="c_e2e_f")
    merch = models.Merchant(merchant_id="m_e2e_f", name="Full Pipeline Merchant", risk_score=0.02)
    txn = models.Transaction(txn_id="T-E2E-F", account_id="a_e2e_f", merchant_id="m_e2e_f", amount=1200.0, currency="USD", status="PENDING", timestamp=datetime.datetime.utcnow())
    dev = models.Device(device_id="d_e2e_f", customer_id="c_e2e_f", os="iOS")
    loc = models.Location(location_id="l_e2e_f", txn_id="T-E2E-F", geo_coord="37.7749,-122.4194", country="US")

    db_session.add_all([cust, acct, merch, txn, dev, loc])
    db_session.commit()

    # 1. POST Investigation Intake
    response = client.post("/api/v1/investigations", json={"transaction_id": "T-E2E-F", "user_id": "usr_e2e_f"})
    assert response.status_code == 202
    inv_data = response.json()
    inv_id = inv_data["investigation_id"]

    # 2. Verify Audit Logs recorded
    audit_logs = db_session.query(models.AuditLog).filter(models.AuditLog.investigation_id == inv_id).all()
    actions = [a.action for a in audit_logs]
    assert any("NODE_EXECUTION" in a or "WORKER_JOB_ENQUEUED" in a for a in actions)

    # 3. Export PDF Report
    pdf_resp = client.post(f"/api/v1/investigations/{inv_id}/export?format=pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.content.startswith(b"%PDF")
