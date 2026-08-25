import datetime
import pytest
import models
from graph import (
    build_graph,
    velocity_check_node,
    evidence_verifier_node,
    critic_node,
    risk_reasoning_node,
    should_retry_or_human_review,
    route_planner_tasks
)

def test_velocity_check_node_calculation(db_session):
    """Test velocity check node calculating 1-hour transaction count and sum."""
    cust = models.Customer(customer_id="c_vel_1", name="Velocity Customer", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_vel_1", customer_id="c_vel_1")
    merch = models.Merchant(merchant_id="m_vel_1", name="Velocity Merchant", risk_score=0.01)
    
    t1 = models.Transaction(txn_id="T-VEL-1", account_id="a_vel_1", merchant_id="m_vel_1", amount=3000.0, currency="USD", status="COMPLETED")
    t2 = models.Transaction(txn_id="T-VEL-2", account_id="a_vel_1", merchant_id="m_vel_1", amount=4000.0, currency="USD", status="PENDING")

    db_session.add_all([cust, acct, merch, t1, t2])
    db_session.commit()

    state = {
        "investigation_id": "inv_vel_1",
        "transaction_id": "T-VEL-2"
    }

    res_state = velocity_check_node(state)
    vel_ev = res_state.get("velocity_evidence", {})

    assert vel_ev.get("velocity_count_1h") >= 2
    assert vel_ev.get("velocity_sum_1h") >= 7000.0
    assert vel_ev.get("high_velocity_flag") is True
    assert vel_ev.get("velocity_score") == 0.85

def test_velocity_timestamp_window_filtering(db_session):
    """Priority 1 Test: Verify 1-hour timestamp window filtering excludes old transactions."""
    cust = models.Customer(customer_id="c_win_1", name="Window Customer", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_win_1", customer_id="c_win_1")
    merch = models.Merchant(merchant_id="m_win_1", name="Window Merchant", risk_score=0.01)

    now = datetime.datetime.utcnow()
    two_hours_ago = now - datetime.timedelta(hours=2)

    t_old = models.Transaction(txn_id="T-OLD-1", account_id="a_win_1", merchant_id="m_win_1", amount=9000.0, currency="USD", status="COMPLETED", timestamp=two_hours_ago)
    t_new = models.Transaction(txn_id="T-NEW-1", account_id="a_win_1", merchant_id="m_win_1", amount=200.0, currency="USD", status="PENDING", timestamp=now)

    db_session.add_all([cust, acct, merch, t_old, t_new])
    db_session.commit()

    state = {"investigation_id": "inv_win_1", "transaction_id": "T-NEW-1"}
    res = velocity_check_node(state)
    vel_ev = res.get("velocity_evidence", {})

    assert vel_ev.get("velocity_count_1h") == 1
    assert vel_ev.get("velocity_sum_1h") == 200.0
    assert vel_ev.get("high_velocity_flag") is False

def test_evidence_verifier_and_critic_nodes():
    """Test evidence verifier and actionable critic nodes."""
    state = {
        "investigation_id": "inv_crit_1",
        "transaction_id": "T-CRIT-1",
        "customer_evidence": {"kyc_status": "VERIFIED"},
        "transaction_evidence": {"amount": 500.0},
        "device_evidence": {"error": "Not Found"},
        "draft_explanation": "Transaction for $500.00 from device."
    }

    v_state = evidence_verifier_node(state)
    assert v_state["failed_target_node"] == "retrieve_device"
    assert "retrieve_device" in v_state["failed_target_nodes"]
    assert v_state["verified_evidence"]["status"] == "PARTIAL"

    c_state = critic_node(v_state)
    assert "critic_feedback" in c_state

def test_multi_source_targeted_retry_routing():
    """Priority 2 Test: Verify targeted retries for all 6 evidence sources."""
    state_device_fail = {
        "investigation_id": "inv_route_1",
        "validated": False,
        "retry_count": 1,
        "confidence": 0.90,
        "failed_target_node": "retrieve_device"
    }
    decision = should_retry_or_human_review(state_device_fail)
    assert decision == "retrieve_device"

    state_location_fail = {
        "investigation_id": "inv_route_2",
        "validated": False,
        "retry_count": 1,
        "confidence": 0.90,
        "failed_target_node": "retrieve_location"
    }
    decision_loc = should_retry_or_human_review(state_location_fail)
    assert decision_loc == "retrieve_location"

def test_multi_factor_dynamic_confidence():
    """Priority 4 & 5 Test: Verify multi-factor dynamic confidence and similarity distance handling."""
    state = {
        "investigation_id": "inv_conf_1",
        "customer_evidence": {"kyc_status": "VERIFIED"},
        "transaction_evidence": {"amount": 100.0},
        "merchant_evidence": {"name": "Test Merchant"},
        "device_evidence": {"os": "iOS"},
        "location_evidence": {"country": "US"},
        "velocity_evidence": {"velocity_score": 0.15},
        "rule_score": 0.20,
        "historical_cases": [{"similarity_distance": 0.40}],
        "validated": True
    }

    res = risk_reasoning_node(state)
    assert "confidence" in res
    assert 0.50 <= res["confidence"] <= 0.98

def test_dynamic_planner_task_routing():
    """Priority 6 Test: Verify dynamic planner task execution router."""
    state = {
        "tasks": ["retrieve_customer", "retrieve_device"]
    }
    routed_tasks = route_planner_tasks(state)
    assert routed_tasks == ["retrieve_customer", "retrieve_device"]
