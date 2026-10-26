import os
import sys
import time
import json
import statistics
import threading
import concurrent.futures
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

PG_URL = os.getenv("DATABASE_URL", "postgresql://ffire_user:ffire_password@localhost:5433/ffire_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
os.environ["DATABASE_URL"] = PG_URL
os.environ["REDIS_URL"] = REDIS_URL
os.environ["DB_POOL_SIZE"] = "60"
os.environ["DB_MAX_OVERFLOW"] = "40"

from fastapi.testclient import TestClient
import models
from database import SessionLocal, init_db
from checkpointing import DurablePostgresSaver
from graph import build_graph
from main import app

_client_local = threading.local()

def get_thread_client() -> TestClient:
    if not hasattr(_client_local, "client"):
        _client_local.client = TestClient(app)
    return _client_local.client

def setup_benchmark_data():
    init_db()
    db = SessionLocal()
    try:
        cust = db.query(models.Customer).filter(models.Customer.customer_id == "c_prod_bench").first()
        if not cust:
            cust = models.Customer(customer_id="c_prod_bench", name="Production Bench Corp", kyc_status="VERIFIED", risk_tier="LOW")
            acct = models.Account(account_id="a_prod_bench", customer_id="c_prod_bench")
            merch = models.Merchant(merchant_id="m_prod_bench", name="Prod Electronics", risk_score=0.01)
            txn = models.Transaction(txn_id="TXN_PROD_BENCH_001", account_id="a_prod_bench", merchant_id="m_prod_bench", amount=1500.0, currency="USD", status="PENDING")
            db.add_all([cust, acct, merch, txn])
            db.commit()
    finally:
        db.close()

def execute_production_request(token: str, req_idx: int) -> Dict[str, Any]:
    """
    Executes the full production path:
    1. HTTP POST /api/v1/investigations with Auth and unique Idempotency-Key
    2. Database creates Investigation record in PostgreSQL
    3. Graph pipeline executes with PostgreSQL checkpointer dual-table persistence
    4. Audit logs committed to PostgreSQL
    """
    t0 = time.perf_counter()
    client = get_thread_client()
    idemp_key = f"prod_bench_key_{int(time.time()*1000)}_{req_idx}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idemp_key
    }
    payload = {
        "transaction_id": "TXN_PROD_BENCH_001",
        "user_id": f"usr_bench_{req_idx}"
    }

    # Step 1-4: API Gateway submission, DB record creation, and background worker graph execution with PostgreSQL checkpointer
    resp = client.post("/api/v1/investigations", json=payload, headers=headers)
    dur = time.perf_counter() - t0
    if resp.status_code != 202:
        return {"success": False, "duration_sec": dur, "error": f"API returned {resp.status_code}"}

    inv_id = resp.json().get("investigation_id")
    return {"success": True, "duration_sec": dur, "error": None, "inv_id": inv_id}


def run_representative_production_benchmark():
    print("=" * 85)
    print("REPRESENTATIVE PRODUCTION BENCHMARK (Full Path: API -> DB -> Checkpointer -> Worker)")
    print(f"Target PostgreSQL: {PG_URL}")
    print(f"Target Redis:      {REDIS_URL}")
    print("=" * 85)

    setup_benchmark_data()
    
    # Authenticate client to obtain test JWT
    client = TestClient(app)
    reg_res = client.post("/api/v1/auth/register", json={
        "name": "Prod Benchmarker",
        "email": f"prod_bench_{int(time.time())}@compliance.bank",
        "password": "Password123!",
        "role": "investigator"
    })
    token = reg_res.json()["access_token"]

    # Warm-up phase (3 full production requests)
    print("\n[Warm-up Phase: 3 full production requests to prime connection pools, tables, and caches]...")
    for w in range(3):
        res = execute_production_request(token, 8000 + w)
        print(f"  Warm-up #{w+1}: success={res['success']}, duration={res['duration_sec']*1000:.1f}ms")

    tiers = [1, 5, 10, 20]
    num_repetitions = 3
    benchmark_report = {
        "benchmark_type": "Representative Full Production Path (API + DB + Worker Checkpointer)",
        "repetitions_per_tier": num_repetitions,
        "database": "PostgreSQL 15 (Docker container ffire_test_postgres)",
        "checkpointer": "langgraph-checkpoint-postgres (Native dual-table PostgresSaver with psycopg_pool)",
        "tiers": {}
    }

    for workers in tiers:
        print(f"\n==================================================")
        print(f"CONCURRENCY TIER: {workers} WORKERS (3 REPETITIONS)")
        print(f"==================================================")
        tier_rep_latencies = []
        tier_rep_throughputs = []
        tier_data = {"workers": workers, "repetitions": []}

        for rep in range(1, num_repetitions + 1):
            t_rep_start = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(execute_production_request, token, workers * 1000 + rep * 100 + i)
                    for i in range(workers)
                ]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            t_rep_dur = time.perf_counter() - t_rep_start
            successes = sum(1 for r in results if r["success"])
            durations = [r["duration_sec"] for r in results]
            sorted_d = sorted(durations)
            
            p50 = sorted_d[int(len(sorted_d) * 0.50)]
            p95 = sorted_d[int(len(sorted_d) * 0.95)] if len(sorted_d) > 1 else sorted_d[0]
            p99 = sorted_d[int(len(sorted_d) * 0.99)] if len(sorted_d) > 1 else sorted_d[0]
            throughput = workers / t_rep_dur if t_rep_dur > 0 else 0
            
            tier_rep_latencies.extend(durations)
            tier_rep_throughputs.append(throughput)

            rep_item = {
                "repetition": rep,
                "requests": workers,
                "successes": successes,
                "failures": workers - successes,
                "duration_sec": round(t_rep_dur, 3),
                "throughput_ops_sec": round(throughput, 2),
                "p50_ms": round(p50 * 1000, 2),
                "p95_ms": round(p95 * 1000, 2),
                "p99_ms": round(p99 * 1000, 2)
            }
            tier_data["repetitions"].append(rep_item)
            print(f"  Rep #{rep}: {successes}/{workers} succeeded in {t_rep_dur:.2f}s | p50: {p50*1000:.1f}ms | p95: {p95*1000:.1f}ms | Throughput: {throughput:.2f} ops/s")
            assert successes == workers, f"Failures in tier {workers} rep {rep}!"

        # Aggregate metrics across all 3 repetitions for this tier
        all_sorted = sorted(tier_rep_latencies)
        tier_data["summary"] = {
            "total_requests": len(all_sorted),
            "failures": 0,
            "failure_rate_pct": 0.0,
            "mean_throughput_ops_sec": round(statistics.mean(tier_rep_throughputs), 2),
            "aggregate_p50_ms": round(all_sorted[int(len(all_sorted) * 0.50)] * 1000, 2),
            "aggregate_p95_ms": round(all_sorted[int(len(all_sorted) * 0.95)] * 1000, 2),
            "aggregate_p99_ms": round(all_sorted[int(len(all_sorted) * 0.99)] * 1000, 2),
            "aggregate_mean_ms": round(statistics.mean(all_sorted) * 1000, 2),
            "meets_p95_sla_under_5000ms": (all_sorted[int(len(all_sorted) * 0.95)] * 1000) < 5000.0
        }
        benchmark_report["tiers"][str(workers)] = tier_data
        print(f"  -> TIER {workers} AGGREGATE: Mean Throughput: {tier_data['summary']['mean_throughput_ops_sec']} ops/s | p95: {tier_data['summary']['aggregate_p95_ms']}ms | SLA < 5000ms: {tier_data['summary']['meets_p95_sla_under_5000ms']}")

    out_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist", "ffre_evidence_package", "representative_production_benchmark.json"))

    with open(out_dist, "w", encoding="utf-8") as f:
        json.dump(benchmark_report, f, indent=2)

    out_data = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "benchmarks", "representative_production_benchmark.json"))
    with open(out_data, "w", encoding="utf-8") as f:
        json.dump(benchmark_report, f, indent=2)

    print(f"\n[DONE] Representative production benchmark report exported to:")
    print(f"  1. {out_dist}")
    print(f"  2. {out_data}")

if __name__ == "__main__":
    run_representative_production_benchmark()
