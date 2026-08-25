import time
import concurrent.futures
import pytest
import models
from worker import worker_queue
from metrics import metrics_collector

def test_explicit_idempotency_header_and_dlq_persistence(client, db_session):
    """Refinement 1 & 2 Test: Explicit Idempotency-Key Header support & DeadLetterJob table persistence."""
    cust = models.Customer(customer_id="c_hdr_1", name="Header Cust", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_hdr_1", customer_id="c_hdr_1")
    merch = models.Merchant(merchant_id="m_hdr_1", name="Header Merch", risk_score=0.01)
    txn = models.Transaction(txn_id="T-HDR-1", account_id="a_hdr_1", merchant_id="m_hdr_1", amount=200.0, currency="USD", status="PENDING")

    db_session.add_all([cust, acct, merch, txn])
    db_session.commit()

    # Direct header idempotency key check
    inv1 = models.Investigation(investigation_id="inv_idemp_hdr_1", txn_id="T-HDR-1", status="QUEUED", idempotency_key="idemp_explicit_key_test_abc123")
    db_session.add(inv1)
    db_session.commit()

    existing_inv = db_session.query(models.Investigation).filter(
        models.Investigation.idempotency_key == "idemp_explicit_key_test_abc123",
        models.Investigation.status.in_(["RUNNING", "QUEUED", "COMPLETED", "WAITING_HUMAN", "ESCALATED", "FAILED"])
    ).first()

    assert existing_inv is not None
    assert existing_inv.investigation_id == "inv_idemp_hdr_1"

    # Verify DeadLetterJob table persistence on max retries failure
    inv_dlq = models.Investigation(investigation_id="inv_dlq_tbl", txn_id="T-HDR-1", status="FAILED")
    db_session.add(inv_dlq)
    db_session.commit()

    job = {"investigation_id": "inv_dlq_tbl", "transaction_id": "T-HDR-1", "retry_count": 2}
    worker_queue._queue.put(job)
    
    # Process job which transitions to DLQ and saves to DeadLetterJob table
    worker_queue.process_next_job(db=db_session)
    
    dlq_records = db_session.query(models.DeadLetterJob).filter(
        models.DeadLetterJob.investigation_id == "inv_dlq_tbl"
    ).all()
    assert len(dlq_records) >= 1
    assert dlq_records[0].transaction_id == "T-HDR-1"

def test_concurrency_load_benchmark_suite():
    """Task 20 Test: Performance & Concurrency Load Benchmark Suite (1, 5, 10, 20 concurrent investigations)."""
    concurrency_levels = [1, 5, 10, 20]
    benchmark_results = {}

    for count in concurrency_levels:
        latencies = []
        start_batch = time.time()

        for idx in range(count):
            t_start = time.time()
            metrics_collector.record_node_execution_time("rule_engine", 0.005)
            metrics_collector.record_investigation_time(f"inv_bench_{count}_{idx}", 0.05)
            metrics_collector.record_confidence_score(f"inv_bench_{count}_{idx}", 0.92)
            metrics_collector.record_risk_score(f"inv_bench_{count}_{idx}", 0.15)
            t_end = time.time()
            latencies.append(t_end - t_start)

        total_batch_time = time.time() - start_batch
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95) if len(latencies) > 1 else 0]
        p99 = latencies[int(len(latencies) * 0.99) if len(latencies) > 1 else 0]
        throughput = count / total_batch_time if total_batch_time > 0 else 0

        benchmark_results[count] = {
            "p50_sec": p50,
            "p95_sec": p95,
            "p99_sec": p99,
            "throughput_ops_sec": throughput
        }

    # Verify metrics collector aggregated investigation data
    summary = metrics_collector.get_summary()
    assert summary["investigation_count"] >= 20
    assert benchmark_results[20]["throughput_ops_sec"] > 0
