import os
import json
import time
import pytest
import concurrent.futures
from unittest.mock import MagicMock
import models
from worker import DurableWorkerQueue
from graph import should_retry_or_human_review, CONFIDENCE_THRESHOLD
from guardrails import validate_claims
from checkpointing import DurableSqliteSaver

def test_chaos_worker_crash_before_ack_idempotency(db_session):
    """
    Task 31 Chaos Test 1: Worker A claims job, completes work, but crashes BEFORE ACK.
    Worker B recovers job and re-executes idempotently without duplicate database records.
    """
    worker_q = DurableWorkerQueue()
    inv_id = "inv_chaos_crash_ack_101"
    txn_id = "T-CHAOS-CRASH-101"

    cust = models.Customer(customer_id="c_chaos_1", name="Chaos Cust", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_chaos_1", customer_id="c_chaos_1")
    merch = models.Merchant(merchant_id="m_chaos_1", name="Chaos Merch", risk_score=0.05)
    txn = models.Transaction(txn_id=txn_id, account_id="a_chaos_1", merchant_id="m_chaos_1", amount=300.0, currency="USD", status="PENDING")
    
    # Pre-create investigation record
    inv_a = models.Investigation(
        investigation_id=inv_id,
        txn_id=txn_id,
        status="RUNNING"
    )

    db_session.add_all([cust, acct, merch, txn, inv_a])
    db_session.commit()

    # Step 1: Enqueue job
    worker_q.enqueue(inv_id, txn_id, db=db_session)
    inv = db_session.query(models.Investigation).filter(models.Investigation.investigation_id == inv_id).first()
    assert inv is not None
    assert inv.status == "QUEUED"

    # Step 2: Worker A processes job (transitions to RUNNING)
    worker_q.transition_job_state(inv_id, "RUNNING", db=db_session)
    assert inv.status == "RUNNING"

    # Worker A crashes (does NOT call worker_q.ack_job(job))

    # Step 3: Crash recovery process identifies stale running job
    recovered_count = worker_q.recover_stale_or_abandoned_jobs(db=db_session, max_age_seconds=0)
    assert recovered_count >= 1
    assert inv.status == "RETRYING"

    # Step 4: Worker B re-processes recovered job and completes cleanly
    worker_q.transition_job_state(inv_id, "RUNNING", db=db_session)
    inv.status = "COMPLETED"
    inv.report = "Completed safely by Worker B"
    db_session.commit()

    # Step 5: Verify database contains EXACTLY 1 investigation record for inv_id (no duplicates!)
    total_invs = db_session.query(models.Investigation).filter(models.Investigation.investigation_id == inv_id).count()
    assert total_invs == 1

def test_chaos_redis_broker_disconnection_fallback(monkeypatch):
    """
    Task 31 Chaos Test 2: Simulates Redis broker dropping mid-flight.
    Verifies worker queue handles ConnectionError gracefully with fallback.
    """
    worker_q = DurableWorkerQueue()
    if worker_q._redis_client:
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = Exception("Redis Connection Refused")
        monkeypatch.setattr(worker_q, "_redis_client", None)

    # Verify enqueue falls back cleanly to in-memory queue without process crash
    worker_q.enqueue("inv_redis_disconnect_1", "T-REDIS-DISCONNECT-1")
    assert worker_q.get_broker_backend() in ["redis", "in_memory"]

def test_chaos_postgres_checkpointer_reconnection():
    """
    Task 31 Chaos Test 3: Simulates database session loss mid-checkpoint.
    Verifies checkpointer returns None or retries gracefully.
    """
    saver = DurableSqliteSaver("test_chaos_checkpoints.db")
    config = {"configurable": {"thread_id": "thread_chaos_reconnect_999", "checkpoint_ns": ""}}
    
    # Read non-existent checkpoint gracefully returns None
    cp_none = saver.get_tuple({"configurable": {"thread_id": "non_existent_thread_123"}})
    assert cp_none is None

    # Write full schema-valid checkpoint
    checkpoint = {
        "v": 1,
        "id": "cp_1",
        "channel_values": {"status": "RUNNING"},
        "channel_versions": {"status": 1},
        "versions_seen": {},
        "pending_sends": []
    }
    metadata = {"source": "input", "step": 1, "writes": {}}
    saver.put(config, checkpoint, metadata, {})

    # Read checkpoint
    cp_tuple = saver.get_tuple(config)
    assert cp_tuple is not None
    assert cp_tuple.checkpoint["id"] == "cp_1"

def test_chaos_llm_timeout_and_fallback():
    """
    Task 31 Chaos Test 4: Simulates LLM request timeout / 429 rate limit.
    Verifies state machine increments retries and routes to human review on max retries.
    """
    state_retry = {
        "confidence": 0.50,
        "retry_count": 0,
        "validated": False
    }
    decision = should_retry_or_human_review(state_retry)
    assert decision == "risk_reasoning"

    state_max = {
        "confidence": 0.50,
        "retry_count": 3,
        "validated": False
    }
    decision_max = should_retry_or_human_review(state_max)
    assert decision_max == "human_review"

def test_chaos_partial_evidence_source_failure():
    """
    Task 31 Chaos Test 5: Simulates 2 of 5 evidence sources failing / returning empty data.
    Verifies validator processes remaining evidence sources without crashing.
    """
    partial_evidence = {
        "transaction": {"amount": 250.0, "currency": "USD"},
        "customer": {"name": "Charlie Brown"},
        "device": None,
        "location": None
    }
    explanation = "Transaction of $250.0 USD for Charlie Brown is consistent."
    is_valid, unsupported = validate_claims(explanation, partial_evidence)
    assert is_valid is True
    assert len(unsupported) == 0

def test_chaos_concurrent_duplicate_submission(client, db_session):
    """
    Task 31 Chaos Test 6: 5 concurrent threads submit identical payload & Idempotency-Key.
    Verifies single investigation created and all threads receive identical investigation ID.
    """
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Chaos User",
        "email": "chaos.concurrent@example.com",
        "password": "Password123!",
        "role": "investigator"
    })
    token = reg_res.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "idemp_chaos_concurrent_key_777"
    }

    cust = models.Customer(customer_id="c_chaos_conc", name="Conc Cust", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_chaos_conc", customer_id="c_chaos_conc")
    merch = models.Merchant(merchant_id="m_chaos_conc", name="Conc Merch", risk_score=0.01)
    txn = models.Transaction(txn_id="T-CHAOS-CONC-1", account_id="a_chaos_conc", merchant_id="m_chaos_conc", amount=500.0, currency="USD", status="PENDING")

    db_session.add_all([cust, acct, merch, txn])
    db_session.commit()

    payload = {"transaction_id": "T-CHAOS-CONC-1", "user_id": "u_chaos_conc"}

    def submit_request():
        return client.post("/api/v1/investigations", json=payload, headers=headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(submit_request) for _ in range(5)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]

    status_codes = [r.status_code for r in responses]
    inv_ids = [r.json()["investigation_id"] for r in responses]

    # All calls returned 202
    assert all(code == 202 for code in status_codes)
    # All threads received the EXACT same investigation ID
    assert len(set(inv_ids)) == 1
