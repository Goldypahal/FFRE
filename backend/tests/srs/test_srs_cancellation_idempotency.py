import pytest
import models
from graph import with_audit_logger

def test_investigation_cancellation_endpoint_and_audit(client, db_session):
    """Task 14 Test: Endpoint cancels investigation and logs audit event."""
    cust = models.Customer(customer_id="c_can_1", name="Cancel Cust", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_can_1", customer_id="c_can_1")
    merch = models.Merchant(merchant_id="m_can_1", name="Cancel Merch", risk_score=0.01)
    txn = models.Transaction(txn_id="T-CANCEL-1", account_id="a_can_1", merchant_id="m_can_1", amount=100.0, currency="USD", status="PENDING")
    inv = models.Investigation(
        investigation_id="inv_cancel_1",
        txn_id="T-CANCEL-1",
        status="RUNNING"
    )

    db_session.add_all([cust, acct, merch, txn, inv])
    db_session.commit()

    resp = client.post(f"/api/v1/investigations/{inv.investigation_id}/cancel")
    assert resp.status_code == 200
    inv_data = resp.json()
    assert inv_data["status"] == "CANCELLED"

    audit_logs = db_session.query(models.AuditLog).filter(
        models.AuditLog.investigation_id == inv.investigation_id
    ).all()
    actions = [a.action for a in audit_logs]
    assert "INVESTIGATION_CANCELLED" in actions

def test_graph_execution_skips_cancelled_investigations(db_session):
    """Task 14 Test: LangGraph node execution wrapper skips node when investigation is CANCELLED."""
    inv = models.Investigation(
        investigation_id="inv_cancel_graph",
        txn_id="T-CANCEL-GRAPH",
        status="CANCELLED"
    )
    db_session.add(inv)
    db_session.commit()

    executed = False
    def dummy_node(state):
        nonlocal executed
        executed = True
        return {"result": "ok"}

    wrapped = with_audit_logger(dummy_node, "dummy_node")
    res = wrapped({"investigation_id": "inv_cancel_graph"})

    assert executed is False
    assert res.get("execution_trace") == ["dummy_node_CANCELLED"]

def test_request_idempotency_cache_hit(client, db_session):
    """Task 15 Test: Duplicate investigation requests return existing ID with X-Cache-Hit header."""
    cust = models.Customer(customer_id="c_idemp_1", name="Idempotent Cust", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_idemp_1", customer_id="c_idemp_1")
    merch = models.Merchant(merchant_id="m_idemp_1", name="Idempotent Merch", risk_score=0.01)
    txn = models.Transaction(txn_id="T-IDEMP-1", account_id="a_idemp_1", merchant_id="m_idemp_1", amount=150.0, currency="USD", status="PENDING")

    db_session.add_all([cust, acct, merch, txn])
    db_session.commit()

    payload = {"transaction_id": "T-IDEMP-1", "user_id": "usr_idemp_1"}

    # 1. First intake request -> creates new investigation (Cache-Hit: false)
    resp1 = client.post("/api/v1/investigations", json=payload)
    assert resp1.status_code == 202
    assert resp1.headers.get("X-Cache-Hit") == "false"
    inv_id_1 = resp1.json()["investigation_id"]

    # 2. Second intake request with identical payload -> returns existing investigation (Cache-Hit: true)
    resp2 = client.post("/api/v1/investigations", json=payload)
    assert resp2.status_code in (200, 202)
    assert resp2.headers.get("X-Cache-Hit") == "true"
    inv_id_2 = resp2.json()["investigation_id"]

    assert inv_id_1 == inv_id_2
