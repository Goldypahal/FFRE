import os
import pytest
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
    inv = models.Investigation(investigation_id="inv_durable_1", txn_id="T-DURABLE-TEST", status="RUNNING")

    db_session.add_all([cust, acct, merch, txn, inv])
    db_session.commit()

    worker_queue.enqueue("inv_durable_1", "T-DURABLE-TEST", db=db_session)

    # Process job synchronously
    processed = worker_queue.process_next_job(db=db_session)
    assert processed is True

    # Verify audit log recorded enqueuing
    logs = db_session.query(models.AuditLog).filter(models.AuditLog.investigation_id == "inv_durable_1").all()
    actions = [l.action for l in logs]
    assert "WORKER_JOB_ENQUEUED" in actions

def test_sqlite_saver_persistent_checkpoint_creation():
    """Test that SqliteSaver checkpointer is active and compiles graph."""
    graph_app = build_graph()
    assert graph_app is not None
    config = {"configurable": {"thread_id": "test_thread_checkpoint"}}
    state = graph_app.get_state(config)
    assert state is not None

def test_durable_checkpoint_persistence_across_instances(tmp_path):
    """Task 16 Test: Durable checkpointer persists state to disk across saver restarts."""
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

    assert tuple_res is not None
    assert tuple_res.checkpoint is not None
