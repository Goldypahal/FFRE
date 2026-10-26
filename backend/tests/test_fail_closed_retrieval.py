"""
Tests for Task T0.5: Fail-Closed Evidence Retrieval & Clean Sessions (Finding V4)
Verifies:
1. Absent device/location returns NOT_FOUND rather than synthetic literals (no "dev_bench" or "37.7749,-122.4194").
2. DB/infrastructure outage during retrieval yields UNAVAILABLE status and routes to human_review with ESCALATED status.
3. Database sessions are cleanly closed in finally blocks even when exceptions are raised.
4. new_device is derived from customer transaction and device evidence history rather than hardcoded logic.
"""

import pytest
from unittest.mock import patch, MagicMock
import models
from graph import (
    retrieve_customer_node,
    retrieve_transaction_node,
    retrieve_merchant_node,
    retrieve_device_node,
    retrieve_location_node,
    velocity_check_node,
    should_retry_or_human_review,
    human_review_node
)
from scripts.seed_demo_data import seed_transaction


def test_absent_device_returns_not_found_without_fabrication(db_session):
    """Verify that a customer without a device returns NOT_FOUND, never a fabricated fallback."""
    seed_transaction(db_session, "TXN_NO_DEV_1", tenant_id="tenant_alpha", include_device=False)

    res = retrieve_device_node({"transaction_id": "TXN_NO_DEV_1"})
    assert "device_evidence" in res
    dev_ev = res["device_evidence"]
    assert dev_ev.get("evidence_status") == "NOT_FOUND"
    assert "error" in dev_ev
    assert dev_ev.get("device_id") != "dev_bench"
    assert dev_ev.get("os") != "Linux"


def test_absent_location_returns_not_found_without_fabrication(db_session):
    """Verify that a transaction without location returns NOT_FOUND, never dummy coordinates."""
    seed_transaction(db_session, "TXN_NO_LOC_1", tenant_id="tenant_alpha", include_location=False)

    res = retrieve_location_node({"transaction_id": "TXN_NO_LOC_1"})
    assert "location_evidence" in res
    loc_ev = res["location_evidence"]
    assert loc_ev.get("evidence_status") == "NOT_FOUND"
    assert "error" in loc_ev
    assert loc_ev.get("geo_coord") != "37.7749,-122.4194"


def test_unavailable_evidence_source_escalates_to_human_review():
    """Verify that an UNAVAILABLE evidence source forces immediate escalation to human review."""
    state = {
        "investigation_id": "INV_FAIL_CLOSED_1",
        "transaction_id": "TXN_FC_1",
        "validated": True,
        "retry_count": 0,
        "confidence": 0.95,
        "failed_target_node": None,
        "critic_issues": False,
        "critic_cycle_count": 0,
        "customer_evidence": {
            "evidence_status": "UNAVAILABLE",
            "error": "Database error: OperationalError connection lost"
        },
        "transaction_evidence": {"evidence_status": "OK", "amount": 100.0},
        "merchant_evidence": {"evidence_status": "OK"},
        "device_evidence": {"evidence_status": "OK"},
        "location_evidence": {"evidence_status": "OK"},
        "velocity_evidence": {"evidence_status": "OK"}
    }

    decision = should_retry_or_human_review(state)
    assert decision == "human_review"

    # Human review report generation must explicitly cite the UNAVAILABLE source
    hr_state = human_review_node(state)
    report = hr_state.get("report", "")
    assert "HUMAN REVIEW ESCALATION REPORT" in report
    assert "UNAVAILABLE" in report
    assert "customer_evidence" in report


def test_db_exception_returns_unavailable_and_closes_session():
    """Verify that database errors yield UNAVAILABLE status and sessions are guaranteed closed."""
    mock_session = MagicMock()
    mock_session.query.side_effect = RuntimeError("Database connection timed out")

    with patch("graph.SessionLocal", return_value=mock_session):
        res_cust = retrieve_customer_node({"transaction_id": "TXN_ERR_1"})
        assert res_cust["customer_evidence"]["evidence_status"] == "UNAVAILABLE"
        assert "Database error" in res_cust["customer_evidence"]["error"]
        assert mock_session.close.called

    mock_session.reset_mock()
    with patch("graph.SessionLocal", return_value=mock_session):
        res_txn = retrieve_transaction_node({"transaction_id": "TXN_ERR_1"})
        assert res_txn["transaction_evidence"]["evidence_status"] == "UNAVAILABLE"
        assert mock_session.close.called

    mock_session.reset_mock()
    with patch("graph.SessionLocal", return_value=mock_session):
        res_merch = retrieve_merchant_node({"transaction_id": "TXN_ERR_1"})
        assert res_merch["merchant_evidence"]["evidence_status"] == "UNAVAILABLE"
        assert mock_session.close.called

    mock_session.reset_mock()
    with patch("graph.SessionLocal", return_value=mock_session):
        res_dev = retrieve_device_node({"transaction_id": "TXN_ERR_1"})
        assert res_dev["device_evidence"]["evidence_status"] == "UNAVAILABLE"
        assert mock_session.close.called

    mock_session.reset_mock()
    with patch("graph.SessionLocal", return_value=mock_session):
        res_loc = retrieve_location_node({"transaction_id": "TXN_ERR_1"})
        assert res_loc["location_evidence"]["evidence_status"] == "UNAVAILABLE"
        assert mock_session.close.called


def test_new_device_computation_from_history(db_session):
    """Verify that new_device is derived from prior customer transaction & evidence records."""
    # Create customer, account, device, and transaction 1
    cust = models.Customer(customer_id="cust_hist_1", name="History User", tenant_id="tenant_alpha")
    acct = models.Account(account_id="acct_hist_1", customer_id="cust_hist_1", tenant_id="tenant_alpha")
    dev = models.Device(device_id="dev_hist_1", customer_id="cust_hist_1", os="macOS", fingerprint="fp_known_device_77", tenant_id="tenant_alpha")
    t1 = models.Transaction(txn_id="TXN_HIST_1", account_id="acct_hist_1", amount=100.0, tenant_id="tenant_alpha")

    db_session.add_all([cust, acct, dev, t1])
    db_session.commit()

    # First transaction for this customer with no prior records -> new_device must be True
    res1 = retrieve_device_node({"transaction_id": "TXN_HIST_1"})
    assert res1["device_evidence"]["new_device"] is True

    # Record investigation evidence for transaction 1 linking fp_known_device_77
    inv1 = models.Investigation(
        investigation_id="INV_HIST_1",
        txn_id="TXN_HIST_1",
        status="COMPLETED",
        tenant_id="tenant_alpha"
    )
    ev1 = models.Evidence(
        investigation_id="INV_HIST_1",
        source="device_evidence",
        snippet="Device fingerprint: fp_known_device_77, OS: macOS",
        tenant_id="tenant_alpha"
    )
    t2 = models.Transaction(txn_id="TXN_HIST_2", account_id="acct_hist_1", amount=200.0, tenant_id="tenant_alpha")
    db_session.add_all([inv1, ev1, t2])
    db_session.commit()

    # Second transaction for the same customer using the same device -> new_device must be False
    res2 = retrieve_device_node({"transaction_id": "TXN_HIST_2"})
    assert res2["device_evidence"]["new_device"] is False
