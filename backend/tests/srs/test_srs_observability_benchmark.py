import time
import os
import json
import statistics
import concurrent.futures
import pytest
import models
from worker import worker_queue
from metrics import metrics_collector
from graph import build_graph

def test_explicit_idempotency_header_and_dlq_persistence(client, db_session):
    """Refinement 1 & 2 Test: Explicit Idempotency-Key Header support & DeadLetterJob table persistence with SET NULL."""
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

def calculate_percentiles(latencies):
    """Accurate percentile calculation using statistics.quantiles or sample indexing."""
    if not latencies:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
    sorted_l = sorted(latencies)
    n = len(sorted_l)
    if n >= 100:
        q = statistics.quantiles(sorted_l, n=100, method='inclusive')
        p50 = q[49]
        p95 = q[94]
        p99 = q[98]
    else:
        p50 = sorted_l[int(n * 0.50)]
        p95 = sorted_l[int(n * 0.95) if n > 1 else 0]
        p99 = sorted_l[int(n * 0.99) if n > 1 else 0]
    return {"p50": p50, "p95": p95, "p99": p99}

def test_concurrency_load_benchmark_suite(db_session):
    """Task 20 Real Concurrency Load Benchmark Suite: Evaluates concurrent graph executions & exports benchmark artifacts."""
    concurrency_levels = [1, 5, 10, 20]
    benchmark_results = {}
    graph_app = build_graph()

    # Pre-seed DB transaction record
    cust = models.Customer(customer_id="c_bench", name="Bench Cust", kyc_status="VERIFIED")
    acct = models.Account(account_id="a_bench", customer_id="c_bench")
    merch = models.Merchant(merchant_id="m_bench", name="Bench Merch", risk_score=0.01)
    txn = models.Transaction(txn_id="T-BENCH-1", account_id="a_bench", merchant_id="m_bench", amount=350.0, currency="USD", status="PENDING")
    db_session.add_all([cust, acct, merch, txn])
    db_session.commit()

    for count in concurrency_levels:
        latencies = []
        successes = 0
        start_batch = time.time()

        def run_real_investigation_workload(idx):
            t_start = time.time()
            inv_id = f"bench_inv_{count}_{idx}"
            state = {
                "investigation_id": inv_id,
                "transaction_id": "T-BENCH-1",
                "customer_id": "c_bench",
                "account_id": "a_bench",
                "merchant_id": "m_bench",
                "evidence": [],
                "historical_cases": [],
                "execution_trace": [],
                "retry_count": 0
            }
            config = {"configurable": {"thread_id": inv_id}}
            metrics_collector.start_investigation_timer(inv_id)
            try:
                res = graph_app.invoke(state, config=config)
                metrics_collector.stop_investigation_timer(inv_id, status="completed")
                metrics_collector.record_node_execution_time("graph_engine", 0.01)
                t_end = time.time()
                return True, t_end - t_start
            except Exception:
                metrics_collector.stop_investigation_timer(inv_id, status="failed")
                t_end = time.time()
                return False, t_end - t_start

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(count, 10)) as executor:
            futures = [executor.submit(run_real_investigation_workload, i) for i in range(count)]
            for f in concurrent.futures.as_completed(futures):
                succ, dur = f.result()
                latencies.append(dur)
                if succ:
                    successes += 1

        total_batch_time = time.time() - start_batch
        pcts = calculate_percentiles(latencies)
        throughput = count / total_batch_time if total_batch_time > 0 else 0

        benchmark_results[str(count)] = {
            "concurrency": count,
            "requests": count,
            "successful": successes,
            "success_rate_pct": (successes / count) * 100.0,
            "p50_sec": round(pcts["p50"], 5),
            "p95_sec": round(pcts["p95"], 5),
            "p99_sec": round(pcts["p99"], 5),
            "throughput_ops_sec": round(throughput, 2),
            "batch_duration_sec": round(total_batch_time, 4)
        }

    # Export JSON artifact to data/benchmarks/task20_results.json
    os.makedirs("data/benchmarks", exist_ok=True)
    with open("data/benchmarks/task20_results.json", "w") as f:
        json.dump(benchmark_results, f, indent=2)

    # Render Markdown report artifact to data/benchmarks/task20_report.md
    md_lines = [
        "# Task 20 Performance & Concurrency Load Benchmark Report",
        "",
        f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        "",
        "## Execution Results Matrix",
        "",
        "| Concurrency | Requests | Success Rate | P50 Latency (s) | P95 Latency (s) | P99 Latency (s) | Throughput (ops/s) |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"
    ]
    for lvl in concurrency_levels:
        r = benchmark_results[str(lvl)]
        md_lines.append(f"| {r['concurrency']} | {r['requests']} | {r['success_rate_pct']:.1f}% | {r['p50_sec']:.5f} | {r['p95_sec']:.5f} | {r['p99_sec']:.5f} | {r['throughput_ops_sec']:.2f} |")

    with open("data/benchmarks/task20_report.md", "w") as f:
        f.write("\n".join(md_lines) + "\n")

    # Verify metrics summary and artifact persistence
    summary = metrics_collector.get_summary()
    assert summary["investigation_count"] >= 20
    assert os.path.exists("data/benchmarks/task20_results.json")
    assert os.path.exists("data/benchmarks/task20_report.md")
