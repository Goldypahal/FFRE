import pytest
import models
from graph import build_graph, velocity_check_node, evidence_verifier_node, critic_node

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

def test_evidence_verifier_and_critic_nodes():
    """Test evidence verifier and critic nodes."""
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
    assert v_state["verified_evidence"]["status"] == "PARTIAL"

    c_state = critic_node(v_state)
    assert "critic_feedback" in c_state
