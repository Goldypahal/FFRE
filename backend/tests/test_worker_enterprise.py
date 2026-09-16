import pytest
import datetime
from fastapi.testclient import TestClient
import models
from worker import DurableWorkerQueue, worker_queue
from auth import get_current_user

def test_worker_health_status_structure(db_session):
    """Verify DurableWorkerQueue get_health_status returns structured metrics."""
    health = worker_queue.get_health_status(db=db_session)
    assert "status" in health
    assert health["status"] in ["healthy", "degraded"]
    assert "broker" in health
    assert "queue_depth" in health
    assert "processing_depth" in health
    assert "dead_letter_count" in health
    assert "processed_count" in health
    assert "failed_count" in health
    assert "max_retries" in health
    assert health["max_retries"] == 3

def test_worker_drain_queue(db_session):
    """Verify drain_queue synchronously processes queued items."""
    # Seed items
    cust = models.Customer(customer_id="c_drain_1", name="Drain Customer", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_drain_1", customer_id="c_drain_1")
    merch = models.Merchant(merchant_id="m_drain_1", name="Drain Merchant", risk_score=0.1)
    txn = models.Transaction(txn_id="T-DRAIN-1", account_id="a_drain_1", merchant_id="m_drain_1", amount=150.0, currency="USD", status="PENDING")
    inv = models.Investigation(investigation_id="inv_drain_1", txn_id="T-DRAIN-1", status="QUEUED")

    db_session.add_all([cust, acct, merch, txn, inv])
    db_session.commit()

    worker_queue.enqueue("inv_drain_1", "T-DRAIN-1", db=db_session)
    drained = worker_queue.drain_queue(max_jobs=10, db=db_session)
    assert drained >= 1

    inv_after = db_session.query(models.Investigation).filter(models.Investigation.investigation_id == "inv_drain_1").first()
    assert inv_after.status in ["COMPLETED", "ESCALATED"]

def test_api_worker_health_endpoint(client):
    """Verify GET /api/v1/worker/health returns operational metrics."""
    res = client.get("/api/v1/worker/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["broker"] in ["redis", "redis_streams", "in_memory"]
    assert "queue_depth" in data

def test_api_worker_recovery_and_drain_endpoints(client, db_session):
    """Verify POST /api/v1/worker/recover and POST /api/v1/worker/drain as admin."""
    # Override admin user for permissions
    def override_admin():
        return models.User(
            user_id="admin_1",
            name="Admin User",
            email="admin@example.com",
            role="admin",
            tenant_id="default_tenant"
        )
    from main import app
    app.dependency_overrides[get_current_user] = override_admin

    try:
        # 1. Trigger recovery
        res_rec = client.post("/api/v1/worker/recover")
        assert res_rec.status_code == 200
        assert "recovered_jobs" in res_rec.json()

        # 2. Trigger drain
        res_drain = client.post("/api/v1/worker/drain?max_jobs=5")
        assert res_drain.status_code == 200
        assert "drained_jobs" in res_drain.json()
    finally:
        from tests.conftest import override_get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user

def test_admin_health_metrics_incorporates_worker_data(client):
    """Verify /api/v1/admin/health-metrics incorporates live worker telemetry."""
    res = client.get("/api/v1/admin/health-metrics")
    assert res.status_code == 200
    data = res.json()
    assert "cache_worker" in data
    cw = data["cache_worker"]
    assert cw["status"] in ["operational", "degraded"]
    assert "broker" in cw
    assert "pending_jobs" in cw
    assert "dead_letter_count" in cw
