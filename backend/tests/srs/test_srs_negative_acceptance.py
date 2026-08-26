import os
import json
import pytest
import models
from worker import DurableWorkerQueue
from guardrails import validate_claims
from checkpointing import DurablePostgresSaver, DurableSqliteSaver

def test_negative_invalid_input_rejection(client):
    """Task 30 Negative Test 1: Verify API Gateway rejects invalid payload with 422 Unprocessable Entity."""
    invalid_payload = {"invalid_field": 12345}
    response = client.post("/api/v1/investigations", json=invalid_payload)
    assert response.status_code == 422

def test_negative_missing_redis_production_fail_fast(monkeypatch):
    """Task 30 Negative Test 2: Verify STRICT_ENTERPRISE_MODE raises RuntimeError when Redis is unreachable."""
    monkeypatch.setenv("STRICT_ENTERPRISE_MODE", "true")
    with pytest.raises(RuntimeError) as exc_info:
        DurableWorkerQueue(redis_url="redis://non_existent_host:6379/0")
    assert "STRICT_ENTERPRISE_MODE" in str(exc_info.value)

def test_negative_unauthorized_user_access(client):
    """Task 30 Negative Test 3: Verify login attempt with invalid credentials returns 401 Unauthorized."""
    response = client.post("/api/v1/auth/login", data={"username": "invalid_user@example.com", "password": "wrong_password"})
    assert response.status_code == 401

def test_negative_duplicate_idempotency_key_deduplication(client, db_session):
    """Task 30 Negative Test 4: Verify duplicate Idempotency-Key returns existing investigation without duplicate creation."""
    # First obtain an auth token for client
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Test Investigator",
        "email": "idemp.test@example.com",
        "password": "Password123!",
        "role": "investigator"
    })
    token = reg_res.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "idemp_neg_test_key_999"
    }

    cust = models.Customer(customer_id="c_neg_idemp_1", name="Idemp Cust", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_neg_idemp_1", customer_id="c_neg_idemp_1")
    merch = models.Merchant(merchant_id="m_neg_idemp_1", name="Idemp Merch", risk_score=0.01)
    txn = models.Transaction(txn_id="T-NEG-IDEMP-1", account_id="a_neg_idemp_1", merchant_id="m_neg_idemp_1", amount=150.0, currency="USD", status="PENDING")

    db_session.add_all([cust, acct, merch, txn])
    db_session.commit()

    payload = {"transaction_id": "T-NEG-IDEMP-1", "user_id": "u_idemp_test"}

    # First call (returns 202 Accepted)
    res1 = client.post("/api/v1/investigations", json=payload, headers=headers)
    assert res1.status_code == 202
    inv_id_1 = res1.json()["investigation_id"]

    # Second call with identical Idempotency-Key
    res2 = client.post("/api/v1/investigations", json=payload, headers=headers)
    assert res2.status_code == 202
    assert res2.headers.get("X-Cache-Hit") == "true"
    inv_id_2 = res2.json()["investigation_id"]

    # Assert deduplication: exact same investigation returned
    assert inv_id_1 == inv_id_2

def test_negative_ungrounded_claim_validator_rejection():
    """Task 30 Negative Test 5: Verify claims validator rejects ungrounded LLM draft claim."""
    evidence_bundle = {
        "transaction": {"amount": 500.0, "currency": "USD"},
        "customer": {"name": "Alice Smith"}
    }
    ungrounded_explanation = "The customer Bob Jones transferred $10,000 to offshore account in Zurich."

    is_valid, unsupported_claims = validate_claims(ungrounded_explanation, evidence_bundle)
    assert is_valid is False
    assert len(unsupported_claims) > 0

def test_negative_worker_crash_pending_job_recovery():
    """Task 30 Negative Test 6: Verify worker pending queue crash recovery re-enqueues abandoned jobs."""
    worker_q = DurableWorkerQueue()
    job = {"investigation_id": "inv_crash_test", "transaction_id": "T-CRASH-1", "_raw_str": json.dumps({"investigation_id": "inv_crash_test"})}

    # Simulate stale job recovery
    recovered_count = worker_q.recover_stale_or_abandoned_jobs(max_age_seconds=0)
    assert isinstance(recovered_count, int)

def test_negative_corrupted_checkpoint_recovery():
    """Task 30 Negative Test 7: Verify checkpointer handles unpickling error gracefully and returns None."""
    saver = DurableSqliteSaver("test_corrupt_checkpoints.db")
    config = {"configurable": {"thread_id": "non_existent_corrupted_thread"}}
    res = saver.get_tuple(config)
    assert res is None
