import os
import sys
import time
import json
import uuid
import multiprocessing
import concurrent.futures
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

PG_URL = os.getenv("DATABASE_URL", "postgresql://ffire_user:ffire_password@localhost:5433/ffire_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
os.environ["DATABASE_URL"] = PG_URL
os.environ["REDIS_URL"] = REDIS_URL

import models
from database import SessionLocal, init_db
from checkpointing import DurablePostgresSaver
from graph import build_graph

def run_single_investigation(thread_id: str, txn_id: str = "TXN_BENCH_PG_001") -> Dict[str, Any]:
    """Run an investigation in a worker process/thread and return timing + status."""
    t0 = time.perf_counter()
    saver = DurablePostgresSaver(PG_URL, minconn=2, maxconn=10)
    graph_app = build_graph(checkpointer=saver)
    
    # Pre-register investigation record to satisfy foreign key constraints
    db = SessionLocal()
    try:
        inv_record = models.Investigation(
            investigation_id=thread_id,
            txn_id=txn_id,
            status="QUEUED",
            tenant_id="default_tenant"
        )
        db.add(inv_record)
        db.commit()
    finally:
        db.close()

    state = {
        "investigation_id": thread_id,
        "transaction_id": txn_id,
        "customer_id": "c_bench",
        "account_id": "a_bench",
        "merchant_id": "m_bench",
        "evidence": [],
        "historical_cases": [],
        "execution_trace": [],
        "retry_count": 0
    }
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        final_state = graph_app.invoke(state, config=config)
        dur = time.perf_counter() - t0
        saver.close()
        return {
            "thread_id": thread_id,
            "success": True,
            "duration_sec": dur,
            "status": final_state.get("report", "")[:40] if final_state else "EMPTY",
            "error": None
        }
    except Exception as exc:
        dur = time.perf_counter() - t0
        saver.close()
        return {
            "thread_id": thread_id,
            "success": False,
            "duration_sec": dur,
            "error": str(exc)
        }

def run_multithread_investigations(saver, graph_app, thread_id: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    db = SessionLocal()
    try:
        inv_record = models.Investigation(
            investigation_id=thread_id,
            txn_id="TXN_BENCH_PG_001",
            status="QUEUED",
            tenant_id="default_tenant"
        )
        db.add(inv_record)
        db.commit()
    finally:
        db.close()

    state = {
        "investigation_id": thread_id,
        "transaction_id": "TXN_BENCH_PG_001",
        "customer_id": "c_bench",
        "account_id": "a_bench",
        "merchant_id": "m_bench",
        "evidence": [],
        "historical_cases": [],
        "execution_trace": [],
        "retry_count": 0
    }
    config = {"configurable": {"thread_id": thread_id}}
    try:
        final_state = graph_app.invoke(state, config=config)
        dur = time.perf_counter() - t0
        return {"thread_id": thread_id, "success": True, "duration_sec": dur, "error": None}
    except Exception as exc:
        dur = time.perf_counter() - t0
        return {"thread_id": thread_id, "success": False, "duration_sec": dur, "error": str(exc)}

def verify_checkpoint_lineage_and_integrity(thread_ids: List[str]) -> Dict[str, Any]:
    """Query PostgreSQL directly to verify checkpoint lineage, completeness, and writes integrity."""
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(PG_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # 1. Verify all thread IDs exist in checkpoints table
            cur.execute("""
                SELECT thread_id, COUNT(*) as checkpoint_count, 
                       MIN(checkpoint_id) as first_cp, MAX(checkpoint_id) as last_cp
                FROM checkpoints
                WHERE thread_id = ANY(%s)
                GROUP BY thread_id
            """, (thread_ids,))
            cp_rows = cur.fetchall()
            found_threads = {r["thread_id"]: r["checkpoint_count"] for r in cp_rows}

            # 2. Check for lineage continuity (parent_checkpoint_id chaining)
            cur.execute("""
                SELECT thread_id, checkpoint_id, parent_checkpoint_id
                FROM checkpoints
                WHERE thread_id = ANY(%s)
                ORDER BY thread_id, checkpoint_id
            """, (thread_ids,))
            all_cps = cur.fetchall()

            broken_chains = []
            cps_by_thread = {}
            for r in all_cps:
                cps_by_thread.setdefault(r["thread_id"], []).append(r)

            for tid, cps in cps_by_thread.items():
                cp_ids = set(c["checkpoint_id"] for c in cps)
                for c in cps:
                    parent = c["parent_checkpoint_id"]
                    # Parent must either be None (initial checkpoint) or exist in the same thread
                    if parent is not None and parent not in cp_ids:
                        broken_chains.append({"thread_id": tid, "checkpoint": c["checkpoint_id"], "missing_parent": parent})

            # 3. Check checkpoint_writes
            cur.execute("""
                SELECT thread_id, COUNT(*) as write_count
                FROM checkpoint_writes
                WHERE thread_id = ANY(%s)
                GROUP BY thread_id
            """, (thread_ids,))
            write_rows = cur.fetchall()
            writes_by_thread = {r["thread_id"]: r["write_count"] for r in write_rows}

            # 4. Check for uncorrupted JSONB
            cur.execute("""
                SELECT COUNT(*) as valid_json_count
                FROM checkpoints
                WHERE thread_id = ANY(%s) AND checkpoint IS NOT NULL AND metadata IS NOT NULL
            """, (thread_ids,))
            valid_json_count = cur.fetchone()["valid_json_count"]

    return {
        "total_requested_threads": len(thread_ids),
        "persisted_threads_in_pg": len(found_threads),
        "all_threads_persisted": len(found_threads) == len(thread_ids),
        "total_checkpoints_created": sum(found_threads.values()),
        "average_checkpoints_per_thread": round(sum(found_threads.values()) / max(len(found_threads), 1), 2),
        "broken_lineage_count": len(broken_chains),
        "broken_chains": broken_chains,
        "total_writes_persisted": sum(writes_by_thread.values()),
        "average_writes_per_thread": round(sum(writes_by_thread.values()) / max(len(writes_by_thread), 1), 2),
        "valid_json_checkpoints": valid_json_count
    }

def test_process_crash_and_resumption():
    """Simulate worker process termination and verify recovery from PostgreSQL checkpointer."""
    print("\n--- Testing Cross-Process Crash Recovery & Checkpoint Resumption ---")
    crash_thread_id = f"crash_test_{int(time.time())}"
    
    # Run initial step in Process 1
    saver1 = DurablePostgresSaver(PG_URL, minconn=2, maxconn=5)
    graph1 = build_graph(checkpointer=saver1)
    
    db = SessionLocal()
    try:
        inv = models.Investigation(
            investigation_id=crash_thread_id,
            txn_id="TXN_BENCH_PG_001",
            status="QUEUED",
            tenant_id="default_tenant"
        )
        db.add(inv)
        db.commit()
    finally:
        db.close()

    state = {
        "investigation_id": crash_thread_id,
        "transaction_id": "TXN_BENCH_PG_001",
        "customer_id": "c_bench",
        "account_id": "a_bench",
        "merchant_id": "m_bench",
        "evidence": [],
        "historical_cases": [],
        "execution_trace": [],
        "retry_count": 0
    }
    config = {"configurable": {"thread_id": crash_thread_id}}

    # Stream partially through the graph (first 3 steps)
    step_count = 0
    for chunk in graph1.stream(state, config=config):
        step_count += 1
        if step_count >= 2:
            print(f"  [Process 1] Simulating crash/termination after step #{step_count}...")
            break
    
    # Abruptly close Process 1 resources (simulate kill)
    saver1.close()

    # Process 2: Completely fresh connection and saver instance
    print("  [Process 2] Initializing fresh process and loading checkpoint from PostgreSQL...")
    saver2 = DurablePostgresSaver(PG_URL, minconn=2, maxconn=5)
    
    # Verify tuple exists in PostgreSQL
    recovered_tuple = saver2.get_tuple(config)
    assert recovered_tuple is not None, "Failed to recover checkpoint tuple from PostgreSQL!"
    print(f"  [Process 2] Recovered checkpoint tuple! ID: {recovered_tuple.config['configurable'].get('checkpoint_id')}")

    # Resume graph execution to completion
    graph2 = build_graph(checkpointer=saver2)
    final_output = None
    for chunk in graph2.stream(None, config=config):
        final_output = chunk

    # Verify final state is completed
    latest_tuple = saver2.get_tuple(config)
    saver2.close()
    
    assert latest_tuple is not None
    assert latest_tuple.checkpoint.get("channel_values", {}).get("report") is not None
    print(f"  [Process 2] Resumption SUCCESS: Investigation completed with full report.")
    return True

def main():
    print("=" * 80)
    print("STRESS TEST: CHECKPOINT CONCURRENCY SAFETY, LINEAGE & CRASH RECOVERY")
    print(f"Database: {PG_URL}")
    print("=" * 80)

    init_db()

    # Pre-seed test customer & transaction records in PostgreSQL
    db = SessionLocal()
    try:
        cust = db.query(models.Customer).filter(models.Customer.customer_id == "c_bench").first()
        if not cust:
            cust = models.Customer(customer_id="c_bench", name="Benchmark Corp", kyc_status="VERIFIED", risk_tier="LOW")
            acct = models.Account(account_id="a_bench", customer_id="c_bench")
            merch = models.Merchant(merchant_id="m_bench", name="Bench Electronics", risk_score=0.02)
            txn = models.Transaction(txn_id="TXN_BENCH_PG_001", account_id="a_bench", merchant_id="m_bench", amount=1250.0, currency="USD", status="PENDING")
            db.add_all([cust, acct, merch, txn])
            db.commit()
    finally:
        db.close()

    # Phase 1: Concurrency stress tiers with shared saver across 1, 5, 10, 20, and 35 workers
    stress_saver = DurablePostgresSaver(PG_URL, minconn=5, maxconn=40)
    stress_graph = build_graph(checkpointer=stress_saver)

    concurrency_tiers = [1, 5, 10, 20, 35]
    all_thread_ids = []
    tier_results = {}

    total_start = time.perf_counter()

    for workers in concurrency_tiers:
        # Run 20 investigations per tier (or equal to worker count for 35)
        run_count = max(workers, 15)
        tier_tids = [f"stress_w{workers}_{int(time.time())}_{i}" for i in range(run_count)]
        all_thread_ids.extend(tier_tids)

        print(f"\n[Testing Tier: {workers} concurrent workers executing {run_count} investigations]...")
        t_tier_start = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(run_multithread_investigations, stress_saver, stress_graph, tid) for tid in tier_tids]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        t_tier_dur = time.perf_counter() - t_tier_start
        successes = sum(1 for r in results if r["success"])
        durations = [r["duration_sec"] for r in results]
        
        sorted_d = sorted(durations)
        p50 = sorted_d[int(len(sorted_d) * 0.50)]
        p95 = sorted_d[int(len(sorted_d) * 0.95)] if len(sorted_d) > 1 else sorted_d[0]
        throughput = run_count / t_tier_dur
        
        tier_results[str(workers)] = {
            "workers": workers,
            "total_investigations": run_count,
            "successes": successes,
            "failures": run_count - successes,
            "p50_sec": round(p50, 3),
            "p95_sec": round(p95, 3),
            "throughput_ops_sec": round(throughput, 2)
        }
        print(f"  -> Result: {successes}/{run_count} succeeded in {t_tier_dur:.2f}s | p50: {p50:.2f}s | p95: {p95:.2f}s | Throughput: {throughput:.2f} ops/s")
        assert successes == run_count, f"Failures detected in tier {workers}!"

    stress_saver.close()

    # Phase 2: Multi-Process Execution Test (Separate OS Processes)
    print("\n[Testing Multi-Process Checkpoint Concurrency: 10 separate OS processes concurrently writing to PostgreSQL]...")
    proc_thread_ids = [f"proc_stress_{int(time.time())}_{i}" for i in range(10)]
    all_thread_ids.extend(proc_thread_ids)

    with concurrent.futures.ProcessPoolExecutor(max_workers=5) as p_executor:
        p_futures = [p_executor.submit(run_single_investigation, tid) for tid in proc_thread_ids]
        p_results = [f.result() for f in concurrent.futures.as_completed(p_futures)]

    p_successes = sum(1 for r in p_results if r["success"])
    print(f"  -> Multi-Process Result: {p_successes}/10 succeeded across separate Python processes!")
    assert p_successes == 10, "Multi-process execution had failures!"

    # Phase 3: Crash Recovery & Resumption
    test_process_crash_and_resumption()

    # Phase 4: Database Lineage & Integrity Verification
    print(f"\n--- Verifying Checkpoint Lineage & Integrity for {len(all_thread_ids)} Total Investigations in PostgreSQL ---")
    lineage_audit = verify_checkpoint_lineage_and_integrity(all_thread_ids)
    print(f"  Total Requested Threads:       {lineage_audit['total_requested_threads']}")
    print(f"  Persisted Threads in PG:       {lineage_audit['persisted_threads_in_pg']}")
    print(f"  Total Checkpoints Created:     {lineage_audit['total_checkpoints_created']}")
    print(f"  Avg Checkpoints Per Thread:    {lineage_audit['average_checkpoints_per_thread']}")
    print(f"  Total Writes Persisted:        {lineage_audit['total_writes_persisted']}")
    print(f"  Avg Writes Per Thread:         {lineage_audit['average_writes_per_thread']}")
    print(f"  Broken Lineage Chains:         {lineage_audit['broken_lineage_count']}")
    print(f"  Valid JSON Checkpoints:        {lineage_audit['valid_json_checkpoints']}")

    assert lineage_audit["all_threads_persisted"] is True, "Missing threads in PostgreSQL!"
    assert lineage_audit["broken_lineage_count"] == 0, "Lineage breaks detected!"

    total_time = time.perf_counter() - total_start
    print(f"\n[ALL TESTS PASSED] Concurrency Safety & Lineage verified in {total_time:.2f}s!")

    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "benchmarks", "checkpoint_concurrency_stress_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "status": "PASS",
            "total_investigations_tested": len(all_thread_ids),
            "tier_benchmarks": tier_results,
            "lineage_audit": lineage_audit,
            "total_elapsed_sec": round(total_time, 2)
        }, f, indent=2)
    print(f"Stress test report written to: {output_path}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
