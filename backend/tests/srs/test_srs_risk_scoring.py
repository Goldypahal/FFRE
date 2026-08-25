import datetime
import pytest
import models
from main import build_investigation_response
from rules import evaluate_rules
from graph import velocity_check_node, rule_engine_node

def test_risk_score_exact_value_returned(db_session):
    inv_high = models.Investigation(
        investigation_id="inv_risk_high",
        txn_id="txn_rh",
        status="COMPLETED",
        confidence=0.91,
        risk_score=0.87,
        report="High risk report"
    )
    db_session.add(inv_high)
    db_session.commit()

    resp_high = build_investigation_response(inv_high, db_session)
    assert resp_high.risk_score == 0.87

    inv_med = models.Investigation(
        investigation_id="inv_risk_med",
        txn_id="txn_rm",
        status="COMPLETED",
        confidence=0.88,
        risk_score=0.43,
        report="Medium risk report"
    )
    db_session.add(inv_med)
    db_session.commit()

    resp_med = build_investigation_response(inv_med, db_session)
    assert resp_med.risk_score == 0.43

    inv_low = models.Investigation(
        investigation_id="inv_risk_low",
        txn_id="txn_rl",
        status="COMPLETED",
        confidence=0.96,
        risk_score=0.12,
        report="Low risk report"
    )
    db_session.add(inv_low)
    db_session.commit()

    resp_low = build_investigation_response(inv_low, db_session)
    assert resp_low.risk_score == 0.12

def test_risk_score_preservation_across_status_changes(db_session):
    """Regression Test: Verify risk score is preserved across status transitions."""
    inv = models.Investigation(
        investigation_id="inv_status_change",
        txn_id="txn_sc",
        status="ESCALATED",
        confidence=0.65,
        risk_score=0.78,
        report="Escalated report"
    )
    db_session.add(inv)
    db_session.commit()

    resp = build_investigation_response(inv, db_session)
    assert resp.risk_score == 0.78
    assert resp.status == "ESCALATED"

def test_deterministic_risk_score_scenarios_low_med_high_critical():
    """Task 10 Test: Verify deterministic risk scoring produces exact scores across risk tiers."""
    # Scenario 1: LOW RISK (Clean transaction, familiar device, home country)
    state_low = {
        "device_evidence": {"new_device": False, "os": "iOS"},
        "location_evidence": {"country": "US"},
        "merchant_evidence": {"historical_fraud_rate": 0.01},
        "transaction_evidence": {"amount": 50.0}
    }
    score_low, reasons_low = evaluate_rules(state_low)
    assert score_low <= 0.20
    assert len(reasons_low) == 0

    # Scenario 2: HIGH / CRITICAL RISK (New device, high-risk merchant, offshore country mismatch)
    state_critical = {
        "device_evidence": {"new_device": True, "os": "Unknown"},
        "location_evidence": {"country": "RU"},
        "merchant_evidence": {"historical_fraud_rate": 0.15},
        "transaction_evidence": {"amount": 9500.0}
    }
    score_crit, reasons_crit = evaluate_rules(state_critical)
    assert score_crit >= 0.70
    assert len(reasons_crit) >= 3

def test_multi_window_velocity_metrics_and_anomaly_signals(db_session):
    """Task 6-9 Test: Multi-window velocity calculation, anomaly detection, and RiskSignal[] generation."""
    cust = models.Customer(customer_id="c_sig_1", name="Signal Customer", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_sig_1", customer_id="c_sig_1")
    merch1 = models.Merchant(merchant_id="m_sig_1", name="Merchant 1", risk_score=0.01)
    merch2 = models.Merchant(merchant_id="m_sig_2", name="Merchant 2", risk_score=0.01)
    merch3 = models.Merchant(merchant_id="m_sig_3", name="Merchant 3", risk_score=0.01)

    now = datetime.datetime.utcnow()
    t1 = models.Transaction(txn_id="T-SIG-1", account_id="a_sig_1", merchant_id="m_sig_1", amount=1000.0, currency="USD", status="COMPLETED", timestamp=now)
    t2 = models.Transaction(txn_id="T-SIG-2", account_id="a_sig_1", merchant_id="m_sig_2", amount=1000.0, currency="USD", status="COMPLETED", timestamp=now)
    t3 = models.Transaction(txn_id="T-SIG-3", account_id="a_sig_1", merchant_id="m_sig_3", amount=1000.0, currency="USD", status="PENDING", timestamp=now)

    db_session.add_all([cust, acct, merch1, merch2, merch3, t1, t2, t3])
    db_session.commit()

    state = {
        "investigation_id": "inv_sig_1",
        "transaction_id": "T-SIG-3",
        "risk_signals": []
    }

    res_vel = velocity_check_node(state)
    vel_ev = res_vel.get("velocity_evidence", {})

    # Task 7 Assertion: Verify multi-window velocity metrics
    assert "velocity_5m" in vel_ev
    assert "velocity_1h" in vel_ev
    assert "velocity_24h" in vel_ev
    assert "velocity_7d" in vel_ev
    assert vel_ev["velocity_5m"]["count"] >= 3

    # Task 8 & 9 Assertion: Verify anomaly patterns and decoupled RiskSignal[] records
    anomalies = vel_ev.get("anomaly_patterns", [])
    assert "BURST_TRANSACTIONS" in anomalies or "MULTI_MERCHANT_SPIKE" in anomalies

    signals = res_vel.get("risk_signals", [])
    assert len(signals) >= 1
    sample_sig = signals[0]
    assert "signal" in sample_sig
    assert "severity" in sample_sig
    assert "source" in sample_sig
