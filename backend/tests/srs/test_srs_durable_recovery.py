import os
import pytest
import datetime
import models
from worker import worker_queue
from main import run_investigation_task
from graph import build_graph
from checkpointing import DurableSqliteSaver

def test_durable_worker_queue_enqueue_and_processing(db_session):
    """Test enqueuing job into durable worker queue and executing graph task."""
    cust = models.Customer(customer_id="c_dur_1", name="Durable Customer", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_dur_1", customer_id="c_dur_1")
    merch = models.Merchant(merchant_id="m_dur_1", name="Durable Merchant", risk_score=0.01)
    txn = models.Transaction(txn_id="T-DURABLE-TEST", account_id="a_dur_1", merchant_id="m_dur_1", amount=100.0, currency="USD", status="PENDING")
    inv = models.Investigation(investigation_id="inv_durable_1", txn_id="T-DURABLE-TEST", status="QUEUED")

    db_session.add_all([cust, acct, merch, txn, inv])
    db_session.commit()

    worker_queue.enqueue("inv_durable_1", "T-DURABLE-TEST", db=db_session)

    # Process job synchronously
    processed = worker_queue.process_next_job(db=db_session)
    assert processed is True

    # Verify audit log recorded enqueuing
    logs = db_session.query(models.AuditLog).filter(models.AuditLog.investigation_id == "inv_durable_1").all()
    actions = [l.action for l in logs]
    assert "WORKER_STATE_TRANSITION" in actions

def test_sqlite_saver_persistent_checkpoint_creation():
    """Test that SqliteSaver checkpointer is active and compiles graph."""
    graph_app = build_graph()
    assert graph_app is not None
    config = {"configurable": {"thread_id": "test_thread_checkpoint"}}
    state = graph_app.get_state(config)
    assert state is not None

def test_durable_checkpoint_persistence_across_instances(tmp_path):
    """Task 16 Test: Verify DurableSqliteSaver persists and restores checkpoints across process restarts."""
    db_file = str(tmp_path / "test_checkpoints.db")
    config = {
        "configurable": {
            "thread_id": "inv_persist_99",
            "checkpoint_ns": "",
            "checkpoint_id": "1"
        }
    }

    checkpoint = {
        "v": 1,
        "id": "1",
        "ts": "2026-08-25T17:00:00Z",
        "channel_values": {"risk_score": 0.88},
        "channel_versions": {},
        "versions_seen": {},
        "pending_sends": []
    }
    metadata = {
        "source": "loop",
        "writes": {},
        "step": 1,
        "parents": {}
    }

    # Instance A saves checkpoint to SQLite disk
    saver_a = DurableSqliteSaver(db_path=db_file)
    saver_a.put(config, checkpoint, metadata, {})

    # Instance B simulates process restart and reloads checkpoint from SQLite disk
    saver_b = DurableSqliteSaver(db_path=db_file)
    tuple_res = saver_b.get_tuple(config)
    print("RESTORED TUPLE:", tuple_res)
    assert tuple_res is not None
    assert tuple_res.checkpoint is not None

def test_worker_state_machine_valid_and_invalid_transitions(db_session):
    """Task 18 Test: Worker state machine enforces valid state transitions and writes audit logs."""
    inv = models.Investigation(investigation_id="inv_sm_1", txn_id="T-SM-1", status="QUEUED")
    db_session.add(inv)
    db_session.commit()

    # Valid transition QUEUED -> RUNNING
    success = worker_queue.transition_job_state("inv_sm_1", "RUNNING", db=db_session)
    assert success is True
    assert inv.status == "RUNNING"

    # Invalid transition RUNNING -> INVALID_STATE raises ValueError
    with pytest.raises(ValueError, match="Invalid state"):
        worker_queue.transition_job_state("inv_sm_1", "INVALID_STATE", db=db_session)

    # Invalid transition COMPLETED -> RUNNING raises ValueError
    inv.status = "COMPLETED"
    db_session.commit()
    with pytest.raises(ValueError, match="Invalid state transition"):
        worker_queue.transition_job_state("inv_sm_1", "RUNNING", db=db_session)

def test_worker_crash_recovery_recovers_stale_running_jobs(db_session):
    """Task 17 Test: Worker crash recovery identifies stale RUNNING jobs and resets status to RETRYING."""
    old_time = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=600)
    inv_stale = models.Investigation(investigation_id="inv_stale_1", txn_id="T-STALE-1", status="RUNNING", updated_at=old_time)
    db_session.add(inv_stale)
    db_session.commit()

    recovered_count = worker_queue.recover_stale_or_abandoned_jobs(db=db_session, max_age_seconds=300)
    assert recovered_count == 1
    assert inv_stale.status == "RETRYING"

def test_worker_dead_letter_queue_after_max_retries(db_session, monkeypatch):
    """Task 19 Test: Worker sends job to dead-letter queue when exceeding max retries."""
    def mock_failing_task(inv_id, txn_id, db=None):
        raise RuntimeError("Worker task execution fatal crash")

    monkeypatch.setattr("worker.run_investigation_task", mock_failing_task)

    inv_failed = models.Investigation(investigation_id="inv_dlq_1", txn_id="NON_EXISTENT_TXN", status="QUEUED")
    db_session.add(inv_failed)
    db_session.commit()

    job = {
        "investigation_id": "inv_dlq_1",
        "transaction_id": "NON_EXISTENT_TXN",
        "retry_count": 2
    }
    worker_queue._queue.put(job)

    # Processing failing job with retry_count=2 triggers max retries (3) transition to FAILED
    processed = worker_queue.process_next_job(db=db_session)
    assert processed is True
    assert inv_failed.status == "FAILED"

    logs = db_session.query(models.AuditLog).filter(models.AuditLog.investigation_id == "inv_dlq_1").all()
    actions = [l.action for l in logs]
    assert "DEAD_LETTER_QUEUE" in actions

def test_task23_redis_worker_queue_broker_support():
    """Task 23 Test: Verify DurableWorkerQueue backend resolution and Redis broker fallback mechanism."""
    from worker import DurableWorkerQueue
    queue_default = DurableWorkerQueue()
    assert queue_default.get_broker_backend() in ["redis", "in_memory"]

    # When given an invalid/unreachable Redis URL, verify graceful fallback to in_memory backend
    queue_invalid = DurableWorkerQueue(redis_url="redis://non_existent_host:6379/0")
    assert queue_invalid.get_broker_backend() == "in_memory"

def test_task24_postgresql_checkpointer_factory(monkeypatch):
    """Task 24 Test: Verify get_durable_checkpointer selects DurablePostgresSaver when PostgreSQL URL is configured."""
    from checkpointing import get_durable_checkpointer, DurablePostgresSaver, DurableSqliteSaver

    # SQLite default fallback
    saver_sqlite = get_durable_checkpointer(db_path="test_checkpoints.db")
    assert isinstance(saver_sqlite, DurableSqliteSaver)

    # PostgreSQL resolution
    monkeypatch.setenv("CHECKPOINT_DB_URL", "postgresql://user:pass@localhost:5432/ffre_db")
    saver_pg = get_durable_checkpointer()
    assert isinstance(saver_pg, DurablePostgresSaver)
    assert saver_pg.db_url == "postgresql://user:pass@localhost:5432/ffre_db"
