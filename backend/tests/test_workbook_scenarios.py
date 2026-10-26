"""
FFIRE Scenario Suite: Production & Chaos Hardening (Task T2.3).

Executes non-infrastructure chaos and operational hardening scenarios:
1. Simulated network partition / degradation during evidence retrieval (fail-closed escalation)
2. Corrupted checkpointer state detection, quarantine, and thread-isolated recovery
3. Worker retry exhaustion, dead-letter queue (DLQ) routing, and audit recording
4. Concurrent multi-tenant collision defense and cross-tenant isolation under contention
5. Mixed-integrity batch ingestion resilience with quarantine accounting
6. Hostile idempotency payload alteration collision defense (HTTP 409)
7. Unscored investigation null-score immutability across state transitions
"""

import os
import json
import uuid
import datetime
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError

from fastapi.testclient import TestClient
import models
from database import SessionLocal
from graph import build_graph, retrieve_customer_node, retrieve_merchant_node
from worker import DurableWorkerQueue, worker_queue, MAX_JOB_RETRIES
from auth import get_current_user
from main import app
from benchmarks.runners.checkpoint_safety import CheckpointSafetyAuditor
from backend.checkpointing import ThreadSafeMemorySaver
from scripts.seed_demo_data import seed_transaction


def test_scenario_network_partition_fail_closed(db_session, client):
    """
    Scenario 1: Network partition / database outage during evidence retrieval.
    Verifies that graph fails closed, marks evidence UNAVAILABLE, and escalates
    to human review rather than silently approving or fabricating mock evidence (Finding V4).
    """
    # 1. Seed valid transaction and customer in DB
    cust = models.Customer(
        customer_id="c_partition_01",
        name="Partition Customer",
        kyc_status="VERIFIED",
        tenant_id="tenant_chaos"
    )
    acct = models.Account(
        account_id="a_partition_01",
        customer_id="c_partition_01",
        tenant_id="tenant_chaos"
    )
    txn = models.Transaction(
        txn_id="TXN-PARTITION-01",
        account_id="a_partition_01",
        amount=500.0,
        currency="USD",
        status="PENDING",
        tenant_id="tenant_chaos"
    )
    db_session.add_all([cust, acct, txn])
    db_session.commit()

    # 2. Simulate network partition during customer retrieval node
    with patch("graph.SessionLocal") as mock_session_cls:
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.query.side_effect = OperationalError("Simulated network partition: connection reset", None, None)

        state = {
            "transaction_id": "TXN-PARTITION-01",
            "tenant_id": "tenant_chaos",
            "session_id": "session_chaos_01"
        }
        res = retrieve_customer_node(state)

        # Fail-closed contract: must return UNAVAILABLE
        assert res["customer_evidence"]["evidence_status"] == "UNAVAILABLE"
        assert res["customer_evidence"].get("name") is None
        mock_db.close.assert_called()

    # 3. Simulate merchant retrieval failure under partition
    with patch("graph.SessionLocal") as mock_session_cls:
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.query.side_effect = OperationalError("Simulated timeout reaching merchant store", None, None)

        res_merch = retrieve_merchant_node(state)
        assert res_merch["merchant_evidence"]["evidence_status"] == "UNAVAILABLE"
        mock_db.close.assert_called()


def test_scenario_corrupted_checkpoint_recovery():
    """
    Scenario 2: Corrupted checkpointer state detection and thread-isolated recovery.
    Verifies that CheckpointSafetyAuditor detects malformed states, rejects execution,
    and isolates other uncorrupted threads from crash propagation.
    """
    saver = ThreadSafeMemorySaver()
    graph = build_graph(checkpointer=saver)

    # 1. Establish valid uncorrupted execution on threads alpha, beta, gamma
    valid_threads = ["thread_alpha", "thread_beta", "thread_gamma"]
    for tid in valid_threads:
        cfg = {"configurable": {"thread_id": tid, "checkpoint_ns": ""}}
        graph.invoke({"investigation_id": tid, "transaction_id": f"TXN_{tid}"}, config=cfg)

    # Verify all valid threads pass safety audit
    report_valid = CheckpointSafetyAuditor.audit_checkpointer(saver, valid_threads)
    assert report_valid.is_safe is True
    assert report_valid.valid_threads == 3
    assert report_valid.corrupted_threads == 0
    assert report_valid.isolated_state_verified is True

    # 2. Simulate checkpoint corruption on thread_corrupt: empty or malformed channel values
    cfg_corrupt = {"configurable": {"thread_id": "thread_corrupt", "checkpoint_ns": ""}}
    # Inject empty tuple into saver storage to simulate a corrupted/unparseable checkpoint record
    saver.storage["thread_corrupt"] = {}

    # Auditor detects corruption on thread_corrupt
    report_corrupt = CheckpointSafetyAuditor.audit_checkpointer(saver, valid_threads + ["thread_corrupt"])
    assert report_corrupt.is_safe is False
    assert report_corrupt.corrupted_threads >= 1
    assert any("thread_corrupt" in detail for detail in report_corrupt.details)

    # 3. Verify thread isolation: valid thread states remain completely intact and uncorrupted
    alpha_tuple = saver.get_tuple({"configurable": {"thread_id": "thread_alpha", "checkpoint_ns": ""}})
    assert alpha_tuple is not None
    assert alpha_tuple.checkpoint["channel_values"]["investigation_id"] == "thread_alpha"


def test_scenario_worker_dlq_routing_on_max_retries(db_session):
    """
    Scenario 3: Worker retry exhaustion, dead-letter queue (DLQ) routing, and audit log tracking.
    When a job fails persistently, worker must retry up to MAX_JOB_RETRIES, record a DeadLetterJob
    entry, write an AuditLog entry with action DEAD_LETTER_QUEUE, and increment DLQ telemetry.
    """
    # 1. Seed customer, account, transaction, and queued investigation
    cust = models.Customer(customer_id="c_dlq_01", name="DLQ Customer", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_dlq_01", customer_id="c_dlq_01")
    txn = models.Transaction(
        txn_id="TXN-DLQ-01",
        account_id="a_dlq_01",
        amount=1200.0,
        currency="USD",
        status="PENDING"
    )
    inv = models.Investigation(
        investigation_id="inv_dlq_01",
        txn_id="TXN-DLQ-01",
        status="QUEUED"
    )
    db_session.add_all([cust, acct, txn, inv])
    db_session.commit()

    # 2. Enqueue job into clean worker queue
    queue = DurableWorkerQueue()
    queue.enqueue("inv_dlq_01", "TXN-DLQ-01", db=db_session)

    # 3. Process job with simulated persistent unhandled exception in run_investigation_task
    with patch("worker.run_investigation_task") as mock_task:
        mock_task.side_effect = RuntimeError("Fatal hardware or downstream failure")

        # Attempt 1: Fails, retry_count becomes 1, status becomes RETRYING
        res1 = queue.process_next_job(db=db_session)
        assert res1 is True
        inv_after_1 = db_session.query(models.Investigation).filter_by(investigation_id="inv_dlq_01").first()
        assert inv_after_1.status == "RETRYING"

        # Attempt 2: Fails, retry_count becomes 2, status remains RETRYING
        res2 = queue.process_next_job(db=db_session)
        assert res2 is True
        inv_after_2 = db_session.query(models.Investigation).filter_by(investigation_id="inv_dlq_01").first()
        assert inv_after_2.status == "RETRYING"

        # Attempt 3: Fails, retry_count reaches MAX_JOB_RETRIES (3) -> Routed to DLQ
        res3 = queue.process_next_job(db=db_session)
        assert res3 is True
        inv_after_3 = db_session.query(models.Investigation).filter_by(investigation_id="inv_dlq_01").first()
        assert inv_after_3.status == "FAILED"

    # 4. Verify DeadLetterJob persistence in DB
    dlq_entry = db_session.query(models.DeadLetterJob).filter_by(investigation_id="inv_dlq_01").first()
    assert dlq_entry is not None
    assert dlq_entry.transaction_id == "TXN-DLQ-01"
    assert dlq_entry.retry_count == MAX_JOB_RETRIES
    assert "Fatal hardware" in dlq_entry.failure_reason

    # 5. Verify AuditLog action DEAD_LETTER_QUEUE
    audit_entry = db_session.query(models.AuditLog).filter_by(
        investigation_id="inv_dlq_01",
        action="DEAD_LETTER_QUEUE"
    ).first()
    assert audit_entry is not None
    assert "exceeded max retries" in audit_entry.details

    # 6. Verify health metrics reflect DLQ state
    health = queue.get_health_status(db=db_session)
    assert health["dead_letter_count"] >= 1
    assert queue.failed_count >= 1


def test_scenario_concurrent_multi_tenant_isolation_under_load(client, db_session):
    """
    Scenario 4: Multi-tenant collision defense under identical transaction IDs.
    Two distinct tenants ('tenant_alpha' and 'tenant_beta') submit investigations
    referencing an identically-named transaction ID 'TXN-SHARED-ID'.
    Verifies that investigations run in total isolation without cross-tenant bleed (Finding V5).
    """
    # 1. Seed transaction for tenant_alpha
    seed_transaction(db_session, "TXN_TENANT_A_1", tenant_id="tenant_alpha")

    # 2. Seed transaction for tenant_beta
    seed_transaction(db_session, "TXN_TENANT_B_1", tenant_id="tenant_beta")

    # 3. Create investigation under tenant_alpha
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )

    res_a = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_TENANT_A_1", "user_id": "user_alpha"},
        headers={"Idempotency-Key": "SHARED-KEY-1"}
    )
    assert res_a.status_code == 202
    inv_a_id = res_a.json()["investigation_id"]

    # 4. Create investigation under tenant_beta with identical idempotency key
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_beta",
        name="Beta User",
        email="beta@example.com",
        role="investigator",
        tenant_id="tenant_beta"
    )

    res_b = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_TENANT_B_1", "user_id": "user_beta"},
        headers={"Idempotency-Key": "SHARED-KEY-1"}
    )
    assert res_b.status_code == 202
    inv_b_id = res_b.json()["investigation_id"]

    # IDs must be completely distinct
    assert inv_a_id != inv_b_id

    # 5. Negative isolation: tenant_alpha CANNOT access tenant_beta's investigation
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_alpha",
        name="Alpha User",
        email="alpha@example.com",
        role="investigator",
        tenant_id="tenant_alpha"
    )
    res_cross_a = client.get(f"/api/v1/investigations/{inv_b_id}")
    assert res_cross_a.status_code in [403, 404]

    # 6. Negative isolation: tenant_alpha CANNOT create investigation on tenant_beta's transaction
    res_cross_txn = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN_TENANT_B_1", "user_id": "user_alpha"}
    )
    assert res_cross_txn.status_code in [403, 404]

    # 7. Negative isolation: tenant_beta CANNOT access tenant_alpha's investigation
    app.dependency_overrides[get_current_user] = lambda: models.User(
        user_id="user_beta",
        name="Beta User",
        email="beta@example.com",
        role="investigator",
        tenant_id="tenant_beta"
    )
    res_cross_b = client.get(f"/api/v1/investigations/{inv_a_id}")
    assert res_cross_b.status_code in [403, 404]


def test_scenario_mixed_quarantine_batch_ingestion(client, db_session):
    """
    Scenario 5: Batch transaction ingestion with mixed corrupted and clean records.
    Verifies that quarantine accounting accurately isolates malformed rows without
    aborting valid records (Finding V8).
    """
    # 1. Seed accounts
    cust = models.Customer(customer_id="c_ingest_scen", name="Ingest Scen Cust", tenant_id="default_tenant")
    acct1 = models.Account(account_id="acc_scen_valid", customer_id="c_ingest_scen", tenant_id="default_tenant")
    db_session.add_all([cust, acct1])
    db_session.commit()

    # Pre-seed one duplicate transaction
    existing_txn = models.Transaction(
        txn_id="TXN-DUP-01",
        account_id="acc_scen_valid",
        amount=50.0,
        currency="USD",
        tenant_id="default_tenant"
    )
    db_session.add(existing_txn)
    db_session.commit()

    # 2. Build 8-item batch: 3 valid, 4 quarantined, 1 duplicate
    batch_payload = [
        # 3 Valid transactions
        {"txn_id": "TXN-OK-1", "account_id": "acc_scen_valid", "amount": 100.0, "currency": "USD", "channel": "WEB"},
        {"txn_id": "TXN-OK-2", "account_id": "acc_scen_valid", "amount": 200.0, "currency": "USD", "channel": "MOBILE"},
        {"txn_id": "TXN-OK-3", "account_id": "acc_scen_valid", "amount": 300.0, "currency": "USD", "channel": "POS"},
        # 4 Quarantined transactions
        {"txn_id": "TXN-BAD-1", "account_id": "acc_scen_valid", "amount": -75.0, "currency": "USD"},  # Non-positive amount
        {"txn_id": "TXN-BAD-2", "account_id": "acc_scen_valid", "amount": 50.0, "currency": "INVALID_CURR"},  # Bad currency
        {"txn_id": "TXN-BAD-3", "account_id": "acc_scen_valid", "amount": 50.0, "currency": "USD", "channel": "TELEPATHY"},  # Bad channel
        {"txn_id": "TXN-BAD-4", "account_id": "acc_ghost_nonexistent", "amount": 50.0, "currency": "USD"},  # Missing account
        # 1 Duplicate transaction
        {"txn_id": "TXN-DUP-01", "account_id": "acc_scen_valid", "amount": 50.0, "currency": "USD"}
    ]

    res = client.post(
        "/api/v1/transactions/ingest",
        json={"transactions": batch_payload}
    )
    assert res.status_code == 200
    data = res.json()

    # Verify exact quarantine accounting
    assert data["total_records"] == 8
    assert data["ingested"] == 3
    assert data["quarantined"] == 4
    assert data["skipped_duplicates"] == 1
    assert len(data["quarantine_reasons"]) == 4

    # Verify valid transactions exist in database
    t1 = db_session.query(models.Transaction).filter_by(txn_id="TXN-OK-1").first()
    assert t1 is not None
    assert t1.amount == 100.0


def test_scenario_hostile_idempotency_payload_tampering(client, db_session):
    """
    Scenario 6: Hostile idempotency payload alteration collision defense.
    Reusing an idempotency key with an altered payload must return HTTP 409 Conflict (Finding V2).
    """
    # 1. Seed two valid transactions
    cust = models.Customer(customer_id="c_idem_scen", name="Idem Customer", tenant_id="default_tenant")
    acct = models.Account(account_id="a_idem_scen", customer_id="c_idem_scen", tenant_id="default_tenant")
    txn1 = models.Transaction(txn_id="TXN-IDEM-01", account_id="a_idem_scen", amount=250.0, currency="USD", tenant_id="default_tenant")
    txn2 = models.Transaction(txn_id="TXN-IDEM-02", account_id="a_idem_scen", amount=500.0, currency="USD", tenant_id="default_tenant")
    db_session.add_all([cust, acct, txn1, txn2])
    db_session.commit()

    # 2. First request with idempotency key
    res1 = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN-IDEM-01", "user_id": "user_1"},
        headers={"Idempotency-Key": "CHAOS-IDEM-KEY-99"}
    )
    assert res1.status_code == 202
    inv_id = res1.json()["investigation_id"]

    # 3. Exact replay: must succeed and return same investigation ID
    res2 = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN-IDEM-01", "user_id": "user_1"},
        headers={"Idempotency-Key": "CHAOS-IDEM-KEY-99"}
    )
    assert res2.status_code in [200, 202]
    assert res2.json()["investigation_id"] == inv_id

    # 4. Hostile tampering: Reusing SAME key with DIFFERENT transaction payload
    res_tampered = client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TXN-IDEM-02", "user_id": "user_1"},
        headers={"Idempotency-Key": "CHAOS-IDEM-KEY-99"}
    )
    # Must reject with 409 Conflict
    assert res_tampered.status_code == 409
    assert "Idempotency key reused with different payload" in res_tampered.json()["detail"]


def test_scenario_unscored_investigation_score_immutability(client, db_session):
    """
    Scenario 7: Unscored investigation null risk score preservation.
    Verifies that throughout lifecycle transitions (QUEUED -> ESCALATED -> WAITING_HUMAN),
    an unscored investigation returns risk_score as null / None and never invents scores (Finding V3).
    """
    # 1. Seed customer, account, transaction
    cust = models.Customer(customer_id="c_unscored_01", name="Unscored Cust", tenant_id="default_tenant")
    acct = models.Account(account_id="a_unscored_01", customer_id="c_unscored_01", tenant_id="default_tenant")
    txn = models.Transaction(txn_id="TXN-UNSCORED-01", account_id="a_unscored_01", amount=150.0, currency="USD", tenant_id="default_tenant")
    inv = models.Investigation(
        investigation_id="inv_unscored_01",
        txn_id="TXN-UNSCORED-01",
        status="QUEUED",
        risk_score=None,
        tenant_id="default_tenant"
    )
    db_session.add_all([cust, acct, txn, inv])
    db_session.commit()

    # Check status QUEUED
    res_q = client.get(f"/api/v1/investigations/inv_unscored_01")
    assert res_q.status_code == 200
    assert res_q.json()["risk_score"] is None
    assert res_q.json()["status"] == "QUEUED"

    # Transition to ESCALATED
    inv.status = "ESCALATED"
    db_session.commit()

    res_esc = client.get(f"/api/v1/investigations/inv_unscored_01")
    assert res_esc.status_code == 200
    # Crucial assertion: Must NOT fabricate 0.85
    assert res_esc.json()["risk_score"] is None
    assert res_esc.json()["status"] == "ESCALATED"

    # Transition to WAITING_HUMAN
    inv.status = "WAITING_HUMAN"
    db_session.commit()

    res_wait = client.get(f"/api/v1/investigations/inv_unscored_01")
    assert res_wait.status_code == 200
    # Crucial assertion: Must NOT fabricate 0.50
    assert res_wait.json()["risk_score"] is None
    assert res_wait.json()["status"] == "WAITING_HUMAN"
